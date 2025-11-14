"""
UltraCore Loan Management - IFRS 9 Provisioning Engine

Complete IFRS 9 / AASB 9 provisioning system:
- Stage classification (1, 2, 3)
- ECL calculation
- Event sourcing integration
- GL posting
- Portfolio aggregation
- Regulatory reporting

ARCHITECTURE INTEGRATION:
- Event Store: All provision events
- General Ledger: Automatic journal entries
- Audit Core: Regulatory compliance logging
- Loan Accounts: Source data
- Delinquency Tracker: SICR indicators
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import uuid
import asyncio

from ultracore.lending.provisioning.ifrs9_models import (
    IFRS9Stage, SignificantIncreaseIndicator, CreditImpairedIndicator,
    ProvisionEventType, ProvisionMethod,
    PDLGDEADParameters, StageClassification, ECLCalculation,
    LoanProvision, ProvisionEvent, PortfolioProvision,
    ProvisionGLAccounts
)
from ultracore.lending.servicing.loan_account import (
    LoanAccount, LoanStatus
)
from ultracore.lending.collections.delinquency_tracker import (
    get_delinquency_tracker, DelinquencyBucket
)
from ultracore.lending.collections.collections_manager import (
    get_collections_manager
)
from ultracore.accounting.general_ledger import (
    get_general_ledger, JournalEntryType
)
from ultracore.audit.audit_core import (
    get_audit_store, AuditEventType, AuditCategory, AuditSeverity
)


# ============================================================================
# IFRS 9 Staging Engine
# ============================================================================

class IFRS9StagingEngine:
    """
    IFRS 9 Stage Classification Engine
    Determines Stage 1, 2, or 3 based on SICR and impairment
    
    ARCHITECTURE INTEGRATION:
    - Uses DelinquencyTracker for DPD data
    - Uses CollectionsManager for forbearance
    - Publishes events to event store
    - Logs to audit trail
    """
    
    def __init__(self):
        # Integration with existing modules
        self.delinquency_tracker = get_delinquency_tracker()
        self.collections_manager = get_collections_manager()
        self.audit_store = get_audit_store()
        
        # Storage
        self.classifications: Dict[str, StageClassification] = {}
        
        # Event store for provision events
        self.provision_events: List[ProvisionEvent] = []
        
        # Configuration
        self.sicr_dpd_threshold = 30  # 30+ DPD = SICR
        self.impaired_dpd_threshold = 90  # 90+ DPD = Impaired
    
    async def classify_loan_stage(
        self,
        loan_account: LoanAccount,
        assessment_date: Optional[date] = None
    ) -> StageClassification:
        """
        Classify loan into IFRS 9 stage
        
        Stage 1: 12-month ECL (no SICR)
        Stage 2: Lifetime ECL (SICR but not impaired)
        Stage 3: Lifetime ECL (credit impaired)
        """
        
        classification_id = f"STGCLS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        calc_date = assessment_date or date.today()
        
        # Get delinquency status
        delinquency = await self.delinquency_tracker.get_delinquency_status(
            loan_account.account_id
        )
        
        if not delinquency:
            delinquency = await self.delinquency_tracker.update_delinquency_status(
                loan_account,
                calc_date
            )
        
        dpd = delinquency.days_past_due
        
        # Get previous classification
        previous_classification = self.classifications.get(loan_account.account_id)
        previous_stage = previous_classification.current_stage if previous_classification else None
        
        # Check for credit impairment (Stage 3)
        impairment_indicators = await self._check_credit_impaired(
            loan_account,
            dpd
        )
        
        if impairment_indicators:
            current_stage = IFRS9Stage.STAGE_3
            sicr_indicators = []
        else:
            # Check for significant increase in credit risk (Stage 2)
            sicr_indicators = await self._check_sicr(
                loan_account,
                dpd
            )
            
            if sicr_indicators:
                current_stage = IFRS9Stage.STAGE_2
            else:
                current_stage = IFRS9Stage.STAGE_1
        
        # Calculate days in stage
        days_in_stage = 0
        stage_change_date = None
        
        if previous_stage and previous_stage != current_stage:
            stage_change_date = calc_date
            days_in_stage = 0
        elif previous_classification:
            days_in_stage = (calc_date - previous_classification.assessment_date).days
        
        # Create classification
        classification = StageClassification(
            classification_id=classification_id,
            loan_account_id=loan_account.account_id,
            current_stage=current_stage,
            previous_stage=previous_stage,
            stage_change_date=stage_change_date,
            days_in_stage=days_in_stage,
            sicr_indicators=sicr_indicators,
            impairment_indicators=impairment_indicators,
            days_past_due=dpd,
            assessment_date=calc_date
        )
        
        # Store classification
        self.classifications[loan_account.account_id] = classification
        
        # If stage changed, create event
        if previous_stage and previous_stage != current_stage:
            await self._publish_stage_change_event(
                loan_account,
                previous_stage,
                current_stage,
                classification
            )
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            category=AuditCategory.FINANCIAL,
            severity=AuditSeverity.INFO,
            resource_type='ifrs9_staging',
            resource_id=classification_id,
            action='stage_classified',
            description=f"IFRS 9 Stage {current_stage.value} classification",
            metadata={
                'loan_account_id': loan_account.account_id,
                'stage': current_stage.value,
                'previous_stage': previous_stage.value if previous_stage else None,
                'dpd': dpd,
                'sicr_indicators': [s.value for s in sicr_indicators],
                'impairment_indicators': [i.value for i in impairment_indicators]
            },
            regulatory_relevant=True
        )
        
        return classification
    
    async def _check_credit_impaired(
        self,
        loan_account: LoanAccount,
        dpd: int
    ) -> List[CreditImpairedIndicator]:
        """Check for credit impairment indicators (Stage 3)"""
        
        indicators = []
        
        # 90+ days past due (regulatory backstop)
        if dpd >= self.impaired_dpd_threshold:
            indicators.append(CreditImpairedIndicator.DPD_90_PLUS)
        
        # Check loan status
        if loan_account.status == LoanStatus.DEFAULT:
            indicators.append(CreditImpairedIndicator.DEFAULT)
        
        if loan_account.status == LoanStatus.WRITTEN_OFF:
            indicators.append(CreditImpairedIndicator.DEFAULT)
        
        # Check for restructuring/forbearance
        hardship_apps = [
            app for app in self.collections_manager.hardship_applications.values()
            if app.loan_account_id == loan_account.account_id and app.active
        ]
        
        if hardship_apps:
            indicators.append(CreditImpairedIndicator.RESTRUCTURING)
        
        return indicators
    
    async def _check_sicr(
        self,
        loan_account: LoanAccount,
        dpd: int
    ) -> List[SignificantIncreaseIndicator]:
        """Check for significant increase in credit risk indicators (Stage 2)"""
        
        indicators = []
        
        # 30+ days past due (regulatory backstop)
        if dpd >= self.sicr_dpd_threshold:
            indicators.append(SignificantIncreaseIndicator.DPD_30_PLUS)
        
        # Check for forbearance
        hardship_apps = [
            app for app in self.collections_manager.hardship_applications.values()
            if app.loan_account_id == loan_account.account_id and app.active
        ]
        
        if hardship_apps:
            indicators.append(SignificantIncreaseIndicator.FORBEARANCE)
        
        # Check for collections activity (watchlist)
        case = await self.collections_manager._get_case_by_account(
            loan_account.account_id
        )
        
        if case and case.active:
            indicators.append(SignificantIncreaseIndicator.WATCHLIST)
        
        return indicators
    
    async def _publish_stage_change_event(
        self,
        loan_account: LoanAccount,
        previous_stage: IFRS9Stage,
        new_stage: IFRS9Stage,
        classification: StageClassification
    ):
        """
        Publish stage change event to event store
        EVENT SOURCING PATTERN
        """
        
        event_id = f"EVT-{uuid.uuid4().hex[:16].upper()}"
        
        event = ProvisionEvent(
            event_id=event_id,
            event_type=ProvisionEventType.STAGE_CHANGED,
            event_timestamp=datetime.now(timezone.utc),
            loan_account_id=loan_account.account_id,
            previous_stage=previous_stage,
            new_stage=new_stage,
            caused_by="IFRS9StagingEngine",
            reason=f"Stage changed from {previous_stage.value} to {new_stage.value}",
            event_data={
                'classification_id': classification.classification_id,
                'dpd': classification.days_past_due,
                'sicr_indicators': [s.value for s in classification.sicr_indicators],
                'impairment_indicators': [i.value for i in classification.impairment_indicators]
            }
        )
        
        self.provision_events.append(event)
    
    async def get_classification(
        self,
        loan_account_id: str
    ) -> Optional[StageClassification]:
        """Get current stage classification"""
        return self.classifications.get(loan_account_id)


# ============================================================================
# ECL Calculator
# ============================================================================

class ECLCalculator:
    """
    Expected Credit Loss Calculator
    Calculates provisions based on PD, LGD, EAD
    
    ARCHITECTURE INTEGRATION:
    - Uses staging engine for stage determination
    - Publishes calculation events
    - Integrates with audit trail
    """
    
    def __init__(self):
        self.staging_engine = None  # Will be set by get function
        self.audit_store = get_audit_store()
        
        # Storage
        self.parameters: Dict[str, PDLGDEADParameters] = {}
        self.calculations: Dict[str, ECLCalculation] = {}
        
        # Default parameters (simplified)
        self.default_pd_stage_1 = Decimal('1.00')  # 1% 12-month PD
        self.default_pd_stage_2 = Decimal('15.00')  # 15% lifetime PD
        self.default_pd_stage_3 = Decimal('50.00')  # 50% lifetime PD
        self.default_lgd = Decimal('45.00')  # 45% loss given default
    
    async def calculate_pd_lgd_ead(
        self,
        loan_account: LoanAccount,
        stage: IFRS9Stage
    ) -> PDLGDEADParameters:
        """Calculate PD, LGD, EAD parameters for loan"""
        
        parameter_id = f"PARAM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        # EAD = Current outstanding balance
        ead = loan_account.current_balance.principal_outstanding
        
        # Calculate time to maturity
        if loan_account.maturity_date:
            days_to_maturity = (loan_account.maturity_date - date.today()).days
            time_to_maturity = Decimal(days_to_maturity) / Decimal('365')
        else:
            time_to_maturity = Decimal('1.0')
        
        # Get PD based on stage and risk factors
        if stage == IFRS9Stage.STAGE_1:
            pd_12m = self._calculate_pd(loan_account, "12_MONTH")
            pd_lifetime = self._calculate_pd(loan_account, "LIFETIME")
        else:
            pd_12m = Decimal('0.00')
            pd_lifetime = self._calculate_pd(loan_account, "LIFETIME")
        
        # Get LGD based on collateral
        lgd = self._calculate_lgd(loan_account)
        
        # Get EIR
        eir = loan_account.terms.interest_rate
        
        parameters = PDLGDEADParameters(
            parameter_id=parameter_id,
            loan_account_id=loan_account.account_id,
            stage=stage,
            pd_12_month=pd_12m,
            pd_lifetime=pd_lifetime,
            lgd=lgd,
            ead=ead,
            eir=eir,
            time_to_maturity_years=time_to_maturity,
            model_version="v1.0"
        )
        
        self.parameters[parameter_id] = parameters
        return parameters
    
    def _calculate_pd(self, loan_account: LoanAccount, horizon: str) -> Decimal:
        """Calculate probability of default"""
        
        base_pd = self.default_pd_stage_1 if horizon == "12_MONTH" else self.default_pd_stage_2
        
        # Adjust for DPD
        dpd = loan_account.days_past_due
        
        if dpd > 0:
            dpd_adjustment = Decimal(min(dpd, 180)) / Decimal('180') * Decimal('30.00')
            base_pd += dpd_adjustment
        
        return min(base_pd, Decimal('100.00'))
    
    def _calculate_lgd(self, loan_account: LoanAccount) -> Decimal:
        """Calculate loss given default"""
        return self.default_lgd
    
    async def calculate_ecl(
        self,
        loan_account: LoanAccount,
        stage: IFRS9Stage,
        parameters: Optional[PDLGDEADParameters] = None
    ) -> ECLCalculation:
        """Calculate Expected Credit Loss"""
        
        calculation_id = f"ECL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        if not parameters:
            parameters = await self.calculate_pd_lgd_ead(loan_account, stage)
        
        # Select PD based on stage
        if stage == IFRS9Stage.STAGE_1:
            pd = parameters.pd_12_month
            time_horizon = "12_MONTH"
        else:
            pd = parameters.pd_lifetime
            time_horizon = "LIFETIME"
        
        lgd = parameters.lgd
        ead = parameters.ead
        eir = parameters.eir
        
        # Calculate undiscounted ECL
        ecl_amount = (pd / Decimal('100')) * (lgd / Decimal('100')) * ead
        ecl_amount = ecl_amount.quantize(Decimal('0.01'))
        
        # Calculate discount factor
        if eir > 0 and parameters.time_to_maturity_years > 0:
            discount_rate = Decimal('1.0') + (eir / Decimal('100'))
            discount_factor = Decimal('1.0') / (discount_rate ** float(parameters.time_to_maturity_years))
        else:
            discount_factor = Decimal('1.0')
        
        # Discounted ECL
        discounted_ecl = ecl_amount * discount_factor
        discounted_ecl = discounted_ecl.quantize(Decimal('0.01'))
        
        calculation = ECLCalculation(
            calculation_id=calculation_id,
            loan_account_id=loan_account.account_id,
            stage=stage,
            pd=pd,
            lgd=lgd,
            ead=ead,
            eir=eir,
            ecl_amount=ecl_amount,
            ecl_principal=ecl_amount,
            discount_factor=discount_factor,
            discounted_ecl=discounted_ecl,
            time_horizon=time_horizon,
            calculation_method=ProvisionMethod.INDIVIDUAL,
            model_version="v1.0"
        )
        
        self.calculations[calculation_id] = calculation
        return calculation


# ============================================================================
# Provision Manager
# ============================================================================

class ProvisionManager:
    """
    Loan Provision Manager
    Manages provision lifecycle with full GL integration
    
    ARCHITECTURE INTEGRATION:
    - Event sourcing for all provision changes
    - Automatic GL posting
    - Audit trail logging
    - Integration with loan accounts
    """
    
    def __init__(self):
        # Integration points
        self.staging_engine = get_ifrs9_staging_engine()
        self.ecl_calculator = ECLCalculator()
        self.ecl_calculator.staging_engine = self.staging_engine
        self.general_ledger = get_general_ledger()
        self.audit_store = get_audit_store()
        
        # Storage
        self.provisions: Dict[str, LoanProvision] = {}
        self.provision_events: List[ProvisionEvent] = []
        
        # GL accounts
        self.gl_accounts = ProvisionGLAccounts()
    
    async def calculate_and_record_provision(
        self,
        loan_account: LoanAccount,
        calculation_date: Optional[date] = None,
        auto_post: bool = True
    ) -> Tuple[LoanProvision, List[ProvisionEvent]]:
        """
        Calculate provision for loan and record events
        
        FULL WORKFLOW:
        1. Classify stage
        2. Calculate ECL
        3. Calculate provision movement
        4. Create provision record
        5. Publish events
        6. Post to GL (if auto_post)
        7. Log audit trail
        """
        
        calc_date = calculation_date or date.today()
        events = []
        
        # Step 1: Classify stage
        classification = await self.staging_engine.classify_loan_stage(
            loan_account,
            calc_date
        )
        
        stage = classification.current_stage
        
        # Step 2: Calculate ECL
        ecl_calculation = await self.ecl_calculator.calculate_ecl(
            loan_account,
            stage
        )
        
        # Step 3: Get previous provision
        previous_provision = await self._get_latest_provision(loan_account.account_id)
        previous_amount = previous_provision.provision_amount if previous_provision else Decimal('0.00')
        
        # Step 4: Calculate new provision
        new_provision_amount = ecl_calculation.discounted_ecl
        
        # Step 5: Calculate movement
        provision_movement = new_provision_amount - previous_amount
        
        provision_increase = max(provision_movement, Decimal('0.00'))
        provision_decrease = abs(min(provision_movement, Decimal('0.00')))
        
        # Step 6: Create provision record
        provision_id = f"PROV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        provision = LoanProvision(
            provision_id=provision_id,
            loan_account_id=loan_account.account_id,
            stage=stage,
            provision_amount=new_provision_amount,
            cumulative_provision=new_provision_amount,
            provision_increase=provision_increase,
            provision_decrease=provision_decrease,
            provision_movement=provision_movement,
            specific_provision=new_provision_amount,
            effective_date=calc_date,
            created_by="SYSTEM"
        )
        
        self.provisions[provision_id] = provision
        
        # Step 7: Create calculation event
        calc_event = ProvisionEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:16].upper()}",
            event_type=ProvisionEventType.PROVISION_CALCULATED,
            event_timestamp=datetime.now(timezone.utc),
            loan_account_id=loan_account.account_id,
            provision_id=provision_id,
            previous_provision=previous_amount,
            new_provision=new_provision_amount,
            provision_movement=provision_movement,
            caused_by="ProvisionManager",
            reason="IFRS 9 ECL calculation",
            event_data={
                'stage': stage.value,
                'ecl_calculation_id': ecl_calculation.calculation_id,
                'pd': str(ecl_calculation.pd),
                'lgd': str(ecl_calculation.lgd),
                'ead': str(ecl_calculation.ead)
            }
        )
        
        self.provision_events.append(calc_event)
        events.append(calc_event)
        
        # Step 8: Post to GL if movement exists and auto_post
        if abs(provision_movement) > Decimal('0.01') and auto_post:
            journal_entry = await self._post_provision_to_gl(
                provision,
                provision_movement,
                stage
            )
            
            provision.posted = True
            provision.posting_date = calc_date
            provision.journal_entry_id = journal_entry.entry_id
            
            # Create posting event
            post_event = ProvisionEvent(
                event_id=f"EVT-{uuid.uuid4().hex[:16].upper()}",
                event_type=ProvisionEventType.PROVISION_POSTED,
                event_timestamp=datetime.now(timezone.utc),
                loan_account_id=loan_account.account_id,
                provision_id=provision_id,
                provision_movement=provision_movement,
                journal_entry_id=journal_entry.entry_id,
                caused_by="ProvisionManager",
                reason="Provision posted to GL"
            )
            
            self.provision_events.append(post_event)
            events.append(post_event)
        
        # Step 9: Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.TRANSACTION_SETTLED,
            category=AuditCategory.FINANCIAL,
            severity=AuditSeverity.INFO,
            resource_type='loan_provision',
            resource_id=provision_id,
            action='provision_calculated',
            description=f"IFRS 9 provision: ${new_provision_amount}",
            metadata={
                'loan_account_id': loan_account.account_id,
                'stage': stage.value,
                'provision_amount': str(new_provision_amount),
                'movement': str(provision_movement),
                'posted': provision.posted
            },
            regulatory_relevant=True
        )
        
        return provision, events
    
    async def _post_provision_to_gl(
        self,
        provision: LoanProvision,
        movement: Decimal,
        stage: IFRS9Stage
    ) -> Any:
        """
        Post provision to General Ledger
        GL INTEGRATION PATTERN
        """
        
        lines = []
        
        expense_account = self.gl_accounts.get_expense_account(stage)
        liability_account = self.gl_accounts.get_liability_account(stage)
        
        if movement > 0:
            # Increase provision
            lines.append({
                'account_code': expense_account,
                'debit': str(abs(movement)),
                'credit': '0.00',
                'description': f"Provision expense - Stage {stage.value[-1]}"
            })
            
            lines.append({
                'account_code': liability_account,
                'debit': '0.00',
                'credit': str(abs(movement)),
                'description': f"Provision liability - Stage {stage.value[-1]}"
            })
        
        elif movement < 0:
            # Decrease provision
            lines.append({
                'account_code': liability_account,
                'debit': str(abs(movement)),
                'credit': '0.00',
                'description': f"Provision release - Stage {stage.value[-1]}"
            })
            
            lines.append({
                'account_code': expense_account,
                'debit': '0.00',
                'credit': str(abs(movement)),
                'description': f"Provision expense reversal - Stage {stage.value[-1]}"
            })
        
        # Create journal entry
        entry = await self.general_ledger.create_entry(
            entry_type=JournalEntryType.ADJUSTING,
            entry_date=provision.effective_date,
            description=f"IFRS 9 Provision - {provision.loan_account_id}",
            lines=lines,
            created_by="IFRS9Engine",
            reference=provision.provision_id,
            auto_post=True
        )
        
        return entry
    
    async def _get_latest_provision(
        self,
        loan_account_id: str
    ) -> Optional[LoanProvision]:
        """Get most recent provision for loan"""
        
        provisions = [
            p for p in self.provisions.values()
            if p.loan_account_id == loan_account_id and not p.reversed
        ]
        
        if not provisions:
            return None
        
        return max(provisions, key=lambda x: x.effective_date)
    
    async def run_portfolio_provisioning(
        self,
        calculation_date: Optional[date] = None,
        auto_post: bool = True
    ) -> PortfolioProvision:
        """Run provisioning for entire loan portfolio"""
        
        calc_date = calculation_date or date.today()
        portfolio_id = f"PORT-{calc_date.isoformat()}"
        
        # Import here to avoid circular import
        from ultracore.lending.servicing.loan_account import get_loan_account_manager
        loan_manager = get_loan_account_manager()
        
        # Get all active loans
        active_accounts = await loan_manager.get_active_accounts()
        
        portfolio = PortfolioProvision(
            portfolio_id=portfolio_id,
            calculation_date=calc_date
        )
        
        # Process each loan
        for loan_account in active_accounts:
            provision, events = await self.calculate_and_record_provision(
                loan_account,
                calc_date,
                auto_post
            )
            
            # Aggregate by stage
            stage = provision.stage
            
            if stage == IFRS9Stage.STAGE_1:
                portfolio.stage_1_count += 1
                portfolio.stage_1_exposure += loan_account.current_balance.principal_outstanding
                portfolio.stage_1_provision += provision.provision_amount
            
            elif stage == IFRS9Stage.STAGE_2:
                portfolio.stage_2_count += 1
                portfolio.stage_2_exposure += loan_account.current_balance.principal_outstanding
                portfolio.stage_2_provision += provision.provision_amount
            
            elif stage == IFRS9Stage.STAGE_3:
                portfolio.stage_3_count += 1
                portfolio.stage_3_exposure += loan_account.current_balance.principal_outstanding
                portfolio.stage_3_provision += provision.provision_amount
        
        # Calculate totals
        portfolio.total_count = (
            portfolio.stage_1_count +
            portfolio.stage_2_count +
            portfolio.stage_3_count
        )
        
        portfolio.total_exposure = (
            portfolio.stage_1_exposure +
            portfolio.stage_2_exposure +
            portfolio.stage_3_exposure
        )
        
        portfolio.total_provision = (
            portfolio.stage_1_provision +
            portfolio.stage_2_provision +
            portfolio.stage_3_provision
        )
        
        # Calculate coverage ratios
        portfolio.calculate_coverage_ratios()
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            category=AuditCategory.FINANCIAL,
            severity=AuditSeverity.INFO,
            resource_type='portfolio_provision',
            resource_id=portfolio_id,
            action='portfolio_provisioned',
            description=f"Portfolio provisioning completed: ${portfolio.total_provision}",
            metadata={
                'calculation_date': calc_date.isoformat(),
                'total_loans': portfolio.total_count,
                'total_exposure': str(portfolio.total_exposure),
                'total_provision': str(portfolio.total_provision),
                'coverage_ratio': str(portfolio.total_coverage_ratio)
            },
            regulatory_relevant=True
        )
        
        return portfolio
    
    async def get_provision_events(
        self,
        loan_account_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ProvisionEvent]:
        """Get provision events from event store"""
        
        events = self.provision_events
        
        if loan_account_id:
            events = [e for e in events if e.loan_account_id == loan_account_id]
        
        if start_date:
            events = [e for e in events if e.event_timestamp.date() >= start_date]
        
        if end_date:
            events = [e for e in events if e.event_timestamp.date() <= end_date]
        
        return sorted(events, key=lambda x: x.event_timestamp)


# ============================================================================
# Global Singletons
# ============================================================================

_ifrs9_staging_engine: Optional[IFRS9StagingEngine] = None
_provision_manager: Optional[ProvisionManager] = None

def get_ifrs9_staging_engine() -> IFRS9StagingEngine:
    """Get the singleton IFRS 9 staging engine"""
    global _ifrs9_staging_engine
    if _ifrs9_staging_engine is None:
        _ifrs9_staging_engine = IFRS9StagingEngine()
    return _ifrs9_staging_engine

def get_provision_manager() -> ProvisionManager:
    """Get the singleton provision manager"""
    global _provision_manager
    if _provision_manager is None:
        _provision_manager = ProvisionManager()
    return _provision_manager
