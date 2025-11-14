"""
Fee Service
Business logic for charges and fees management
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import logging

from ultracore.domains.charges_fees.models.fee import (
    Fee,
    FeeType,
    FeeStatus,
    ChargingRule,
    TriggerType,
    FeeRevenue,
)

logger = logging.getLogger(__name__)


class FeeService:
    """
    Fee Service
    
    Handles fee calculation, application, waiver evaluation,
    and revenue tracking
    """
    
    def __init__(self):
        # In production, charging rules would be loaded from database
        self.charging_rules: List[ChargingRule] = []
    
    def add_charging_rule(self, rule: ChargingRule):
        """Add a charging rule"""
        self.charging_rules.append(rule)
        logger.info(f"Added charging rule: {rule.rule_name}")
    
    def evaluate_fee_for_event(
        self,
        event_type: str,
        context: Dict[str, Any],
        tenant_id: UUID,
        created_by: str
    ) -> List[Fee]:
        """
        Evaluate if fees should be applied for an event
        
        Args:
            event_type: Event type (e.g., "PaymentMissed")
            context: Event context data
            tenant_id: Tenant ID
            created_by: User who triggered the event
        
        Returns:
            List of fees to apply
        """
        fees_to_apply = []
        
        # Find matching rules
        matching_rules = [
            rule for rule in self.charging_rules
            if rule.is_active
            and rule.trigger_type == TriggerType.EVENT
            and rule.trigger_event == event_type
            and rule.tenant_id == tenant_id
        ]
        
        for rule in matching_rules:
            # Evaluate conditions
            if not rule.evaluate_conditions(context):
                logger.debug(f"Rule {rule.rule_name} conditions not met")
                continue
            
            # Check waiver conditions
            if rule.evaluate_waiver_conditions(context):
                logger.info(f"Fee waived by rule {rule.rule_name} waiver conditions")
                continue
            
            # Calculate fee amount
            base_amount = context.get("base_amount")
            tier_key = context.get("tier_key")
            
            try:
                amount = rule.calculate_fee_amount(
                    base_amount=base_amount,
                    tier_key=tier_key
                )
            except ValueError as e:
                logger.error(f"Error calculating fee amount: {e}")
                continue
            
            # Create fee
            fee = Fee(
                tenant_id=tenant_id,
                account_id=context.get("account_id"),
                loan_id=context.get("loan_id"),
                customer_id=context.get("customer_id"),
                fee_type=rule.fee_type,
                fee_name=rule.fee_name,
                description=rule.description,
                amount=amount,
                charging_rule_id=rule.rule_id,
                created_by=created_by,
            )
            
            fees_to_apply.append(fee)
            logger.info(
                f"Fee to apply: {fee.fee_name} ${amount} "
                f"(rule: {rule.rule_name})"
            )
        
        return fees_to_apply
    
    def apply_fee(
        self,
        fee: Fee,
        account_balance: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Apply a fee
        
        Args:
            fee: Fee to apply
            account_balance: Current account balance
        
        Returns:
            Application result
        """
        # Check if fee can be applied
        if fee.status != FeeStatus.PENDING:
            return {
                "success": False,
                "reason": f"Fee status is {fee.status}, not PENDING",
            }
        
        # Check if account has sufficient balance (optional)
        if account_balance is not None and account_balance < fee.amount:
            logger.warning(
                f"Insufficient balance to apply fee: "
                f"${account_balance} < ${fee.amount}"
            )
            # Fee can still be applied, creating negative balance
        
        # Apply the fee
        fee.apply()
        
        logger.info(f"Fee applied: {fee.fee_name} ${fee.amount}")
        
        return {
            "success": True,
            "fee_id": fee.fee_id,
            "amount": fee.amount,
            "applied_date": fee.applied_date,
        }
    
    def waive_fee(
        self,
        fee: Fee,
        reason: str,
        waived_by: str
    ) -> Dict[str, Any]:
        """
        Waive a fee
        
        Args:
            fee: Fee to waive
            reason: Waiver reason
            waived_by: User who waived the fee
        
        Returns:
            Waiver result
        """
        if fee.status == FeeStatus.WAIVED:
            return {
                "success": False,
                "reason": "Fee already waived",
            }
        
        if fee.status == FeeStatus.REFUNDED:
            return {
                "success": False,
                "reason": "Fee already refunded",
            }
        
        # Waive the fee
        fee.waive(reason=reason, waived_by=waived_by)
        
        logger.info(f"Fee waived: {fee.fee_name} ${fee.amount} - {reason}")
        
        return {
            "success": True,
            "fee_id": fee.fee_id,
            "amount": fee.amount,
            "waiver_reason": reason,
        }
    
    def refund_fee(
        self,
        fee: Fee,
        refund_amount: Decimal,
        reason: str,
        refunded_by: str
    ) -> Dict[str, Any]:
        """
        Refund a fee
        
        Args:
            fee: Fee to refund
            refund_amount: Amount to refund
            reason: Refund reason
            refunded_by: User who refunded the fee
        
        Returns:
            Refund result
        """
        if fee.status != FeeStatus.APPLIED:
            return {
                "success": False,
                "reason": f"Fee status is {fee.status}, not APPLIED",
            }
        
        if refund_amount > fee.amount:
            return {
                "success": False,
                "reason": f"Refund amount ${refund_amount} exceeds fee amount ${fee.amount}",
            }
        
        # Refund the fee
        fee.refund(
            amount=refund_amount,
            reason=reason,
            refunded_by=refunded_by
        )
        
        logger.info(f"Fee refunded: {fee.fee_name} ${refund_amount} - {reason}")
        
        return {
            "success": True,
            "fee_id": fee.fee_id,
            "refund_amount": refund_amount,
            "refund_reason": reason,
        }
    
    def calculate_fee_revenue(
        self,
        fees: List[Fee],
        period_start: date,
        period_end: date,
        tenant_id: UUID
    ) -> FeeRevenue:
        """
        Calculate fee revenue for a period
        
        Args:
            fees: List of fees
            period_start: Period start date
            period_end: Period end date
            tenant_id: Tenant ID
        
        Returns:
            Fee revenue metrics
        """
        revenue = FeeRevenue(
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
        )
        
        # Filter fees in period
        period_fees = [
            fee for fee in fees
            if fee.applied_date
            and period_start <= fee.applied_date <= period_end
        ]
        
        # Calculate totals
        for fee in period_fees:
            revenue.total_fees_count += 1
            
            if fee.status == FeeStatus.APPLIED:
                revenue.total_fees_applied += fee.amount
                
                # Breakdown by type
                fee_type_str = str(fee.fee_type)
                revenue.revenue_by_type[fee_type_str] = (
                    revenue.revenue_by_type.get(fee_type_str, Decimal("0.00")) +
                    fee.amount
                )
            
            elif fee.status == FeeStatus.WAIVED:
                revenue.total_fees_waived += fee.amount
                revenue.waived_fees_count += 1
            
            elif fee.status == FeeStatus.REFUNDED:
                revenue.total_fees_refunded += fee.refund_amount
                revenue.refunded_fees_count += 1
        
        # Calculate net revenue
        revenue.calculate_net_revenue()
        
        logger.info(
            f"Fee revenue calculated for {period_start} to {period_end}: "
            f"${revenue.net_fee_revenue}"
        )
        
        return revenue
    
    def get_fee_schedule(
        self,
        account_id: Optional[UUID] = None,
        loan_id: Optional[UUID] = None,
        product_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get applicable fee schedule
        
        Args:
            account_id: Account ID
            loan_id: Loan ID
            product_code: Product code
        
        Returns:
            List of applicable fees
        """
        schedule = []
        
        for rule in self.charging_rules:
            if not rule.is_active:
                continue
            
            # Check applicability
            if product_code and rule.applies_to_products:
                if product_code not in rule.applies_to_products:
                    continue
            
            if account_id and rule.applies_to_accounts:
                if account_id not in rule.applies_to_accounts:
                    continue
            
            schedule.append({
                "fee_type": rule.fee_type,
                "fee_name": rule.fee_name,
                "description": rule.description,
                "amount_type": rule.amount_type,
                "fixed_amount": rule.fixed_amount,
                "percentage": rule.percentage,
                "trigger_type": rule.trigger_type,
                "schedule": rule.schedule,
                "waiver_conditions": rule.waiver_conditions,
            })
        
        return schedule


# ============================================================================
# Default Charging Rules
# ============================================================================

def create_default_charging_rules(tenant_id: UUID) -> List[ChargingRule]:
    """Create default charging rules"""
    
    rules = [
        # Monthly maintenance fee
        ChargingRule(
            tenant_id=tenant_id,
            rule_name="Monthly Maintenance Fee",
            rule_code="MONTHLY_MAINT",
            fee_type=FeeType.MONTHLY_MAINTENANCE,
            fee_name="Monthly Maintenance Fee",
            description="Monthly account maintenance fee",
            trigger_type=TriggerType.SCHEDULE,
            schedule="0 0 1 * *",  # First day of month
            amount_type="fixed",
            fixed_amount=Decimal("10.00"),
            waiver_conditions={
                "minimum_balance": ">= 1000.00"
            },
            created_by="system",
        ),
        
        # Late payment fee
        ChargingRule(
            tenant_id=tenant_id,
            rule_name="Late Payment Fee",
            rule_code="LATE_PAYMENT",
            fee_type=FeeType.LATE_PAYMENT,
            fee_name="Late Payment Fee",
            description="Fee for missed loan payment",
            trigger_type=TriggerType.EVENT,
            trigger_event="PaymentMissed",
            amount_type="fixed",
            fixed_amount=Decimal("50.00"),
            conditions={
                "days_past_due": ">= 1"
            },
            max_fee_amount=Decimal("100.00"),
            created_by="system",
        ),
        
        # ATM withdrawal fee
        ChargingRule(
            tenant_id=tenant_id,
            rule_name="ATM Withdrawal Fee (Other Bank)",
            rule_code="ATM_WITHDRAWAL",
            fee_type=FeeType.ATM_WITHDRAWAL,
            fee_name="ATM Withdrawal Fee",
            description="Fee for ATM withdrawal at other bank",
            trigger_type=TriggerType.EVENT,
            trigger_event="ATMWithdrawal",
            amount_type="fixed",
            fixed_amount=Decimal("3.00"),
            conditions={
                "atm_network": "other_bank",
                "free_withdrawals_used": ">= 4"
            },
            created_by="system",
        ),
        
        # Overdraft fee
        ChargingRule(
            tenant_id=tenant_id,
            rule_name="Overdraft Fee",
            rule_code="OVERDRAFT",
            fee_type=FeeType.OVERDRAFT,
            fee_name="Overdraft Fee",
            description="Fee for overdrawing account",
            trigger_type=TriggerType.EVENT,
            trigger_event="AccountOverdrawn",
            amount_type="fixed",
            fixed_amount=Decimal("35.00"),
            created_by="system",
        ),
    ]
    
    return rules
