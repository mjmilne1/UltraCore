"""
Delinquency Service
Business logic for delinquency management
"""

from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID
import logging

from ultracore.domains.delinquency.models.delinquency_status import (
    DelinquencyStatus,
    DelinquencyBucket,
    RiskLevel,
    BucketConfiguration,
    DEFAULT_BUCKET_CONFIGS,
    PortfolioAtRisk,
)

logger = logging.getLogger(__name__)


class DelinquencyService:
    """
    Delinquency Service
    
    Handles delinquency calculation, bucket classification,
    and automated actions
    """
    
    def __init__(self, bucket_configs: List[BucketConfiguration] = None):
        self.bucket_configs = bucket_configs or DEFAULT_BUCKET_CONFIGS
    
    def calculate_days_past_due(
        self,
        next_due_date: date,
        current_date: date = None
    ) -> int:
        """
        Calculate days past due
        
        Args:
            next_due_date: Next payment due date
            current_date: Current date (defaults to today)
        
        Returns:
            Days past due (0 if not overdue)
        """
        if current_date is None:
            current_date = date.today()
        
        if current_date <= next_due_date:
            return 0
        
        return (current_date - next_due_date).days
    
    def update_delinquency_status(
        self,
        status: DelinquencyStatus,
        payment_received: Decimal = None,
        current_date: date = None
    ) -> Dict[str, any]:
        """
        Update delinquency status
        
        Args:
            status: Current delinquency status
            payment_received: Payment amount (if any)
            current_date: Current date
        
        Returns:
            Update summary with changes and actions
        """
        if current_date is None:
            current_date = date.today()
        
        changes = {
            "bucket_changed": False,
            "became_delinquent": False,
            "became_current": False,
            "actions_required": [],
        }
        
        # Calculate days past due
        if status.next_due_date:
            old_dpd = status.days_past_due
            status.days_past_due = self.calculate_days_past_due(
                status.next_due_date,
                current_date
            )
            
            # Check if payment received
            if payment_received and payment_received > 0:
                status.last_payment_date = current_date
                status.amount_overdue = max(
                    Decimal("0.00"),
                    status.amount_overdue - payment_received
                )
                
                # If fully paid, mark as current
                if status.amount_overdue == 0:
                    status.mark_current()
                    changes["became_current"] = True
                    logger.info(f"Loan {status.loan_id} delinquency cured")
        
        # Update bucket
        old_bucket = status.current_bucket
        new_bucket = status.update_bucket()
        
        if new_bucket:
            changes["bucket_changed"] = True
            changes["old_bucket"] = old_bucket
            changes["new_bucket"] = new_bucket
            logger.info(
                f"Loan {status.loan_id} moved from {old_bucket} to {new_bucket}"
            )
            
            # Get automated actions for new bucket
            actions = self.get_automated_actions(new_bucket)
            changes["actions_required"] = actions
        
        # Check if became delinquent
        if status.days_past_due > 0 and not status.is_delinquent:
            status.mark_delinquent()
            changes["became_delinquent"] = True
            logger.warning(f"Loan {status.loan_id} became delinquent")
        
        # Update timestamp
        status.updated_at = datetime.utcnow()
        
        return changes
    
    def get_automated_actions(
        self,
        bucket: DelinquencyBucket
    ) -> List[Dict[str, any]]:
        """
        Get automated actions for a bucket
        
        Args:
            bucket: Delinquency bucket
        
        Returns:
            List of actions to execute
        """
        actions = []
        
        # Find bucket config
        config = next(
            (c for c in self.bucket_configs if c.bucket == bucket),
            None
        )
        
        if not config:
            return actions
        
        # Build action list
        if config.send_reminder:
            actions.append({
                "type": "send_reminder",
                "description": "Send payment reminder to customer",
            })
        
        if config.apply_late_fee:
            actions.append({
                "type": "apply_late_fee",
                "amount": config.late_fee_amount,
                "description": f"Apply late fee of ${config.late_fee_amount}",
            })
        
        if config.send_collection_notice:
            actions.append({
                "type": "send_collection_notice",
                "description": "Send formal collection notice",
            })
        
        if config.escalate_to_collections:
            actions.append({
                "type": "escalate_to_collections",
                "description": "Escalate to collections team",
            })
        
        if config.provision_percentage > 0:
            actions.append({
                "type": "update_provisioning",
                "percentage": config.provision_percentage,
                "description": f"Update provisioning to {config.provision_percentage}%",
            })
        
        return actions
    
    def calculate_portfolio_at_risk(
        self,
        delinquency_statuses: List[DelinquencyStatus],
        tenant_id: UUID
    ) -> PortfolioAtRisk:
        """
        Calculate Portfolio at Risk (PAR) metrics
        
        Args:
            delinquency_statuses: List of all delinquency statuses
            tenant_id: Tenant ID
        
        Returns:
            Portfolio at Risk metrics
        """
        par = PortfolioAtRisk(tenant_id=tenant_id)
        
        # Calculate totals
        par.total_loans = len(delinquency_statuses)
        
        total_balance = Decimal("0.00")
        amount_1_plus = Decimal("0.00")
        amount_30_plus = Decimal("0.00")
        amount_60_plus = Decimal("0.00")
        amount_90_plus = Decimal("0.00")
        
        for status in delinquency_statuses:
            # Assuming we have outstanding_balance in the status
            # (In production, this would come from loan data)
            outstanding = status.amount_overdue
            total_balance += outstanding
            
            # Count by bucket
            if status.current_bucket == DelinquencyBucket.CURRENT:
                par.loans_current += 1
            elif status.current_bucket == DelinquencyBucket.BUCKET_1:
                par.loans_bucket_1 += 1
                amount_1_plus += outstanding
            elif status.current_bucket == DelinquencyBucket.BUCKET_2:
                par.loans_bucket_2 += 1
                amount_1_plus += outstanding
                amount_30_plus += outstanding
            elif status.current_bucket == DelinquencyBucket.BUCKET_3:
                par.loans_bucket_3 += 1
                amount_1_plus += outstanding
                amount_30_plus += outstanding
                amount_60_plus += outstanding
            elif status.current_bucket == DelinquencyBucket.BUCKET_4:
                par.loans_bucket_4 += 1
                amount_1_plus += outstanding
                amount_30_plus += outstanding
                amount_60_plus += outstanding
                amount_90_plus += outstanding
            elif status.current_bucket == DelinquencyBucket.DEFAULTED:
                par.loans_defaulted += 1
                amount_1_plus += outstanding
                amount_30_plus += outstanding
                amount_60_plus += outstanding
                amount_90_plus += outstanding
        
        # Set totals
        par.total_outstanding_balance = total_balance
        par.amount_at_risk_1 = amount_1_plus
        par.amount_at_risk_30 = amount_30_plus
        par.amount_at_risk_60 = amount_60_plus
        par.amount_at_risk_90 = amount_90_plus
        
        # Calculate PAR percentages
        par.par_1 = par.calculate_par(total_balance, amount_1_plus)
        par.par_30 = par.calculate_par(total_balance, amount_30_plus)
        par.par_60 = par.calculate_par(total_balance, amount_60_plus)
        par.par_90 = par.calculate_par(total_balance, amount_90_plus)
        
        # Calculate provisioning
        par.total_provisioning_required = self.calculate_provisioning(
            delinquency_statuses
        )
        
        logger.info(
            f"PAR calculated: PAR30={par.par_30}%, PAR60={par.par_60}%, "
            f"PAR90={par.par_90}%"
        )
        
        return par
    
    def calculate_provisioning(
        self,
        delinquency_statuses: List[DelinquencyStatus]
    ) -> Decimal:
        """
        Calculate total provisioning required
        
        Args:
            delinquency_statuses: List of delinquency statuses
        
        Returns:
            Total provisioning amount
        """
        total_provisioning = Decimal("0.00")
        
        for status in delinquency_statuses:
            # Find bucket config
            config = next(
                (c for c in self.bucket_configs if c.bucket == status.current_bucket),
                None
            )
            
            if config and config.provision_percentage > 0:
                # Calculate provisioning for this loan
                provisioning = (
                    status.amount_overdue * config.provision_percentage / 100
                )
                total_provisioning += provisioning
        
        return total_provisioning
    
    def get_delinquency_trend(
        self,
        historical_par: List[PortfolioAtRisk]
    ) -> Dict[str, any]:
        """
        Analyze delinquency trend
        
        Args:
            historical_par: Historical PAR data
        
        Returns:
            Trend analysis
        """
        if len(historical_par) < 2:
            return {"trend": "insufficient_data"}
        
        # Sort by date
        sorted_par = sorted(historical_par, key=lambda x: x.calculation_date)
        
        # Compare latest vs previous
        latest = sorted_par[-1]
        previous = sorted_par[-2]
        
        # Calculate changes
        par_30_change = latest.par_30 - previous.par_30
        par_60_change = latest.par_60 - previous.par_60
        par_90_change = latest.par_90 - previous.par_90
        
        # Determine trend
        if par_30_change > 1:
            trend = "deteriorating"
        elif par_30_change < -1:
            trend = "improving"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "par_30_change": float(par_30_change),
            "par_60_change": float(par_60_change),
            "par_90_change": float(par_90_change),
            "latest_par_30": float(latest.par_30),
            "latest_par_60": float(latest.par_60),
            "latest_par_90": float(latest.par_90),
        }
