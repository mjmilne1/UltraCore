"""
Shadow Ledger Reconciliation System
Nubank-inspired: Nightly Kafka replay into shadow ledger with drift detection

Architecture:
1. Primary Ledger: Real-time transaction processing
2. Shadow Ledger: Nightly rebuild from Kafka events (full replay)
3. Reconciliation: Compare primary vs shadow, detect drift
4. Alerting: Block releases if drift > threshold

This ensures:
- Event sourcing integrity
- No data corruption
- Ability to rebuild from events
- Audit trail completeness
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import json

from ultracore.modules.accounting.general_ledger.ledger import GeneralLedger
from ultracore.modules.accounting.general_ledger.journal import JournalService, JournalEntry
from ultracore.modules.accounting.general_ledger.chart_of_accounts import ChartOfAccounts
from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.data_mesh.integration import DataMeshPublisher


class ReconciliationStatus(str, Enum):
    PASS = 'PASS'
    DRIFT_DETECTED = 'DRIFT_DETECTED'
    CRITICAL_DRIFT = 'CRITICAL_DRIFT'
    FAILED = 'FAILED'


class DriftSeverity(str, Enum):
    NONE = 'NONE'
    LOW = 'LOW'  # < 0.01% difference
    MEDIUM = 'MEDIUM'  # 0.01% - 0.1%
    HIGH = 'HIGH'  # 0.1% - 1%
    CRITICAL = 'CRITICAL'  # > 1%


class AccountDrift:
    """Represents drift in a single account"""
    
    def __init__(
        self,
        account_code: str,
        account_name: str,
        primary_balance: Decimal,
        shadow_balance: Decimal
    ):
        self.account_code = account_code
        self.account_name = account_name
        self.primary_balance = primary_balance
        self.shadow_balance = shadow_balance
        self.difference = shadow_balance - primary_balance
        self.difference_percentage = self._calculate_percentage()
        self.severity = self._calculate_severity()
    
    def _calculate_percentage(self) -> Decimal:
        """Calculate percentage difference"""
        if self.primary_balance == 0:
            if self.shadow_balance == 0:
                return Decimal('0')
            else:
                return Decimal('100')  # Complete difference
        
        return abs(self.difference / self.primary_balance * Decimal('100'))
    
    def _calculate_severity(self) -> DriftSeverity:
        """Calculate drift severity"""
        pct = self.difference_percentage
        
        if pct == 0:
            return DriftSeverity.NONE
        elif pct < Decimal('0.01'):
            return DriftSeverity.LOW
        elif pct < Decimal('0.1'):
            return DriftSeverity.MEDIUM
        elif pct < Decimal('1.0'):
            return DriftSeverity.HIGH
        else:
            return DriftSeverity.CRITICAL
    
    def to_dict(self) -> Dict:
        return {
            'account_code': self.account_code,
            'account_name': self.account_name,
            'primary_balance': str(self.primary_balance),
            'shadow_balance': str(self.shadow_balance),
            'difference': str(self.difference),
            'difference_percentage': str(self.difference_percentage),
            'severity': self.severity.value
        }


class ReconciliationReport:
    """Complete reconciliation report"""
    
    def __init__(
        self,
        run_id: str,
        started_at: datetime,
        completed_at: datetime
    ):
        self.run_id = run_id
        self.started_at = started_at
        self.completed_at = completed_at
        self.duration_seconds = (completed_at - started_at).total_seconds()
        
        self.status = ReconciliationStatus.PASS
        self.events_replayed = 0
        self.accounts_checked = 0
        self.accounts_with_drift: List[AccountDrift] = []
        
        self.primary_total_assets = Decimal('0')
        self.shadow_total_assets = Decimal('0')
        self.primary_total_liabilities = Decimal('0')
        self.shadow_total_liabilities = Decimal('0')
        self.primary_total_equity = Decimal('0')
        self.shadow_total_equity = Decimal('0')
        
        self.max_drift_severity = DriftSeverity.NONE
        self.critical_drift_accounts: List[str] = []
    
    def add_drift(self, drift: AccountDrift):
        """Add account drift to report"""
        self.accounts_with_drift.append(drift)
        
        # Update max severity
        severity_order = [
            DriftSeverity.NONE,
            DriftSeverity.LOW,
            DriftSeverity.MEDIUM,
            DriftSeverity.HIGH,
            DriftSeverity.CRITICAL
        ]
        
        if severity_order.index(drift.severity) > severity_order.index(self.max_drift_severity):
            self.max_drift_severity = drift.severity
        
        # Track critical drift accounts
        if drift.severity == DriftSeverity.CRITICAL:
            self.critical_drift_accounts.append(drift.account_code)
            self.status = ReconciliationStatus.CRITICAL_DRIFT
        elif self.status == ReconciliationStatus.PASS and drift.severity != DriftSeverity.NONE:
            self.status = ReconciliationStatus.DRIFT_DETECTED
    
    def should_block_deployment(self) -> bool:
        """
        Determine if deployment should be blocked
        
        Block if:
        - Critical drift detected
        - High drift in > 5 accounts
        - Accounting equation violated
        """
        if self.status == ReconciliationStatus.CRITICAL_DRIFT:
            return True
        
        high_drift_count = sum(
            1 for drift in self.accounts_with_drift
            if drift.severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]
        )
        
        if high_drift_count > 5:
            return True
        
        # Check accounting equation
        primary_equation_balanced = abs(
            self.primary_total_assets - (self.primary_total_liabilities + self.primary_total_equity)
        ) < Decimal('0.01')
        
        shadow_equation_balanced = abs(
            self.shadow_total_assets - (self.shadow_total_liabilities + self.shadow_total_equity)
        ) < Decimal('0.01')
        
        if not (primary_equation_balanced and shadow_equation_balanced):
            return True
        
        return False
    
    def to_dict(self) -> Dict:
        return {
            'run_id': self.run_id,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat(),
            'duration_seconds': self.duration_seconds,
            'status': self.status.value,
            'events_replayed': self.events_replayed,
            'accounts_checked': self.accounts_checked,
            'accounts_with_drift': len(self.accounts_with_drift),
            'max_drift_severity': self.max_drift_severity.value,
            'critical_drift_accounts': self.critical_drift_accounts,
            'should_block_deployment': self.should_block_deployment(),
            'primary_ledger': {
                'total_assets': str(self.primary_total_assets),
                'total_liabilities': str(self.primary_total_liabilities),
                'total_equity': str(self.primary_total_equity)
            },
            'shadow_ledger': {
                'total_assets': str(self.shadow_total_assets),
                'total_liabilities': str(self.shadow_total_liabilities),
                'total_equity': str(self.shadow_total_equity)
            },
            'drift_details': [drift.to_dict() for drift in self.accounts_with_drift]
        }


class ShadowLedger:
    """
    Shadow ledger built from Kafka event replay
    
    This is a complete rebuild from events to verify data integrity
    """
    
    def __init__(self):
        self.ledger = GeneralLedger()
        self.journal = JournalService()
        self.events_processed = 0
        self.last_event_timestamp: Optional[datetime] = None
    
    async def rebuild_from_events(
        self,
        start_date: datetime,
        end_date: datetime,
        progress_callback: Optional[callable] = None
    ) -> int:
        """
        Rebuild ledger from Kafka events
        
        Returns: Number of events processed
        """
        kafka_store = get_production_kafka_store()
        
        # Fetch all journal entry events from Kafka
        events = await kafka_store.get_events_by_type(
            entity='general_ledger',
            event_type='journal_entry_posted',
            start_time=start_date,
            end_time=end_date
        )
        
        # Replay events in order
        for i, event in enumerate(events):
            await self._process_event(event)
            
            if progress_callback and i % 100 == 0:
                progress_callback(i, len(events))
        
        return len(events)
    
    async def _process_event(self, event: Dict):
        """Process a single event"""
        event_data = event['event_data']
        
        # Recreate journal entry
        await self.journal.create_entry(
            description=event_data['description'],
            entries=event_data['entries']
        )
        
        self.events_processed += 1
        self.last_event_timestamp = datetime.fromisoformat(event['timestamp'])
    
    async def get_account_balance(self, account_code: str) -> Decimal:
        """Get balance from shadow ledger"""
        return await self.ledger.get_account_balance(account_code)


class ShadowLedgerReconciliation:
    """
    Shadow ledger reconciliation service
    
    Runs nightly to verify ledger integrity
    """
    
    def __init__(self):
        self.primary_ledger = GeneralLedger()
        self.shadow_ledger: Optional[ShadowLedger] = None
        self.coa = ChartOfAccounts()
    
    async def run_reconciliation(
        self,
        date: Optional[datetime] = None
    ) -> ReconciliationReport:
        """
        Run complete reconciliation
        
        Steps:
        1. Build shadow ledger from Kafka events
        2. Compare all account balances
        3. Generate drift report
        4. Publish results
        5. Alert if deployment should be blocked
        """
        import uuid
        
        if date is None:
            date = datetime.now(timezone.utc)
        
        # Create report
        run_id = f"RECON-{date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        started_at = datetime.now(timezone.utc)
        
        print(f"\n🔍 Starting Shadow Ledger Reconciliation: {run_id}")
        print(f"   Date: {date.strftime('%Y-%m-%d')}")
        
        # Step 1: Rebuild shadow ledger
        print("   📼 Rebuilding shadow ledger from Kafka events...")
        self.shadow_ledger = ShadowLedger()
        
        # Replay events from start of day to now
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        events_replayed = await self.shadow_ledger.rebuild_from_events(
            start_date=start_of_day,
            end_date=end_of_day,
            progress_callback=self._progress_callback
        )
        
        print(f"   ✅ Replayed {events_replayed} events")
        
        # Step 2: Compare balances
        print("   📊 Comparing account balances...")
        account_drifts = await self._compare_all_accounts()
        
        completed_at = datetime.now(timezone.utc)
        
        # Step 3: Build report
        report = ReconciliationReport(
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at
        )
        
        report.events_replayed = events_replayed
        report.accounts_checked = len(self.coa.accounts)
        
        # Add drifts
        for drift in account_drifts:
            if drift.difference != 0:
                report.add_drift(drift)
        
        # Calculate totals
        await self._calculate_totals(report)
        
        # Step 4: Publish results
        await self._publish_report(report)
        
        # Step 5: Alert if needed
        if report.should_block_deployment():
            await self._send_critical_alert(report)
        
        print(f"\n   📋 Reconciliation Complete:")
        print(f"      Status: {report.status.value}")
        print(f"      Accounts with drift: {len(report.accounts_with_drift)}")
        print(f"      Max severity: {report.max_drift_severity.value}")
        print(f"      🚨 Block deployment: {report.should_block_deployment()}")
        
        return report
    
    async def _compare_all_accounts(self) -> List[AccountDrift]:
        """Compare all account balances"""
        drifts = []
        
        for account in self.coa.accounts.values():
            # Get balances from both ledgers
            primary_balance = await self.primary_ledger.get_account_balance(account.code)
            shadow_balance = await self.shadow_ledger.get_account_balance(account.code)
            
            # Create drift object
            drift = AccountDrift(
                account_code=account.code,
                account_name=account.name,
                primary_balance=primary_balance,
                shadow_balance=shadow_balance
            )
            
            drifts.append(drift)
        
        return drifts
    
    async def _calculate_totals(self, report: ReconciliationReport):
        """Calculate totals by account type"""
        from ultracore.modules.accounting.general_ledger.chart_of_accounts import AccountType
        
        for account in self.coa.accounts.values():
            primary_balance = await self.primary_ledger.get_account_balance(account.code)
            shadow_balance = await self.shadow_ledger.get_account_balance(account.code)
            
            if account.account_type == AccountType.ASSET:
                report.primary_total_assets += primary_balance
                report.shadow_total_assets += shadow_balance
            elif account.account_type == AccountType.LIABILITY:
                report.primary_total_liabilities += primary_balance
                report.shadow_total_liabilities += shadow_balance
            elif account.account_type == AccountType.EQUITY:
                report.primary_total_equity += primary_balance
                report.shadow_total_equity += shadow_balance
    
    async def _publish_report(self, report: ReconciliationReport):
        """Publish report to Kafka and Data Mesh"""
        kafka_store = get_production_kafka_store()
        
        # Publish to Kafka
        await kafka_store.append_event(
            entity='reconciliation',
            event_type='shadow_ledger_reconciliation_completed',
            event_data=report.to_dict(),
            aggregate_id=report.run_id
        )
        
        # Publish to Data Mesh
        await DataMeshPublisher.publish_transaction_data(
            report.run_id,
            {
                'data_product': 'reconciliation_reports',
                'report': report.to_dict()
            }
        )
    
    async def _send_critical_alert(self, report: ReconciliationReport):
        """Send critical alert for deployment blocking"""
        kafka_store = get_production_kafka_store()
        
        # Send to notification system
        await kafka_store.append_event(
            entity='notifications',
            event_type='send_critical_alert',
            event_data={
                'alert_type': 'SHADOW_LEDGER_DRIFT',
                'severity': 'CRITICAL',
                'message': f'Shadow ledger drift detected. Deployment BLOCKED.',
                'details': {
                    'run_id': report.run_id,
                    'accounts_with_critical_drift': report.critical_drift_accounts,
                    'max_severity': report.max_drift_severity.value
                },
                'recipients': ['ops-team@ultracore.com', 'cto@ultracore.com']
            },
            aggregate_id=report.run_id
        )
        
        # Send to PagerDuty/Slack
        # In production: Integrate with alerting systems
    
    def _progress_callback(self, current: int, total: int):
        """Progress callback for event replay"""
        if current % 1000 == 0:
            pct = (current / total * 100) if total > 0 else 0
            print(f"      Progress: {current}/{total} ({pct:.1f}%)")


class ReconciliationScheduler:
    """
    Scheduler for nightly reconciliation runs
    
    Runs automatically every night at 2 AM
    """
    
    def __init__(self):
        self.reconciliation = ShadowLedgerReconciliation()
        self.is_running = False
    
    async def schedule_nightly_run(self):
        """Schedule nightly reconciliation"""
        while True:
            # Calculate next 2 AM
            now = datetime.now(timezone.utc)
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            
            if next_run <= now:
                next_run += timedelta(days=1)
            
            # Wait until next run
            wait_seconds = (next_run - now).total_seconds()
            print(f"⏰ Next reconciliation in {wait_seconds/3600:.1f} hours")
            
            await asyncio.sleep(wait_seconds)
            
            # Run reconciliation
            await self.run()
    
    async def run(self):
        """Run reconciliation"""
        if self.is_running:
            print("⚠️  Reconciliation already running, skipping")
            return
        
        self.is_running = True
        
        try:
            report = await self.reconciliation.run_reconciliation()
            
            # Check if deployment should be blocked
            if report.should_block_deployment():
                # Set deployment block flag
                await self._set_deployment_block()
            else:
                # Clear deployment block flag
                await self._clear_deployment_block()
        
        except Exception as e:
            print(f"❌ Reconciliation failed: {e}")
            # Send alert
        
        finally:
            self.is_running = False
    
    async def _set_deployment_block(self):
        """Set deployment block flag in CI/CD"""
        # Write flag file for CI/CD to check
        # In production: Update feature flag, CI/CD variable, etc.
        
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='deployment',
            event_type='deployment_blocked',
            event_data={
                'reason': 'Shadow ledger drift detected',
                'blocked_at': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id='deployment_block'
        )
    
    async def _clear_deployment_block(self):
        """Clear deployment block flag"""
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='deployment',
            event_type='deployment_unblocked',
            event_data={
                'unblocked_at': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id='deployment_block'
        )


# CLI tool for manual reconciliation
async def run_manual_reconciliation():
    """
    Run reconciliation manually
    
    Usage: python -m tests.shadow_ledger.reconciliation
    """
    reconciliation = ShadowLedgerReconciliation()
    report = await reconciliation.run_reconciliation()
    
    # Print detailed report
    print("\n" + "=" * 80)
    print("SHADOW LEDGER RECONCILIATION REPORT")
    print("=" * 80)
    print(f"Run ID: {report.run_id}")
    print(f"Status: {report.status.value}")
    print(f"Duration: {report.duration_seconds:.2f} seconds")
    print(f"Events Replayed: {report.events_replayed}")
    print(f"Accounts Checked: {report.accounts_checked}")
    print(f"Accounts with Drift: {len(report.accounts_with_drift)}")
    print(f"Max Drift Severity: {report.max_drift_severity.value}")
    print(f"\nDeployment Block: {'YES ⛔' if report.should_block_deployment() else 'NO ✅'}")
    
    if report.accounts_with_drift:
        print("\n" + "-" * 80)
        print("ACCOUNTS WITH DRIFT:")
        print("-" * 80)
        
        for drift in sorted(report.accounts_with_drift, key=lambda d: d.difference_percentage, reverse=True):
            print(f"\n{drift.account_code} - {drift.account_name}")
            print(f"  Primary:  ")
            print(f"  Shadow:   ")
            print(f"  Diff:      ({drift.difference_percentage:.4f}%)")
            print(f"  Severity: {drift.severity.value}")
    
    print("\n" + "=" * 80)
    
    return report


if __name__ == '__main__':
    # Run manual reconciliation
    asyncio.run(run_manual_reconciliation())
