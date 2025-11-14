"""
Payment Validation Service.

Validates payment requests, limits, and compliance.
"""

from decimal import Decimal
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ..models.payment import Payment
from ..models.payment_method import PaymentMethod


class PaymentValidationService:
    """Service for validating payments."""
    
    def __init__(self):
        """Initialize payment validation service."""
        self.daily_limit_default = Decimal("50000")
        self.transaction_limit_default = Decimal("10000")
        self.high_value_threshold = Decimal("10000")
    
    async def validate_payment(
        self,
        payment: Payment,
        payment_method: PaymentMethod,
        account_balance: Decimal
    ) -> Dict[str, Any]:
        """
        Validate a payment request.
        
        Args:
            payment: Payment to validate
            payment_method: Payment method being used
            account_balance: Current account balance
            
        Returns:
            Validation result with errors if any
        """
        errors = []
        warnings = []
        
        # Validate amount
        amount_validation = self._validate_amount(payment.amount)
        if not amount_validation["valid"]:
            errors.extend(amount_validation["errors"])
        warnings.extend(amount_validation.get("warnings", []))
        
        # Validate balance
        if payment.amount > account_balance:
            errors.append({
                "code": "insufficient_funds",
                "message": f"Insufficient funds. Available: {account_balance}, Required: {payment.amount}"
            })
        
        # Validate payment method
        method_validation = self._validate_payment_method(payment_method)
        if not method_validation["valid"]:
            errors.extend(method_validation["errors"])
        
        # Validate limits
        limit_validation = await self._validate_limits(
            payment.amount,
            payment.from_customer_id,
            payment_method
        )
        if not limit_validation["valid"]:
            errors.extend(limit_validation["errors"])
        warnings.extend(limit_validation.get("warnings", []))
        
        # Validate compliance
        compliance_validation = self._validate_compliance(payment)
        if not compliance_validation["valid"]:
            errors.extend(compliance_validation["errors"])
        warnings.extend(compliance_validation.get("warnings", []))
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "requires_approval": payment.amount >= self.high_value_threshold
        }
    
    def _validate_amount(self, amount: Decimal) -> Dict[str, Any]:
        """Validate payment amount."""
        errors = []
        warnings = []
        
        if amount <= 0:
            errors.append({
                "code": "invalid_amount",
                "message": "Payment amount must be greater than zero"
            })
        
        if amount > Decimal("1000000"):
            warnings.append({
                "code": "high_value",
                "message": "High value payment - additional approval required"
            })
        
        # Check for suspicious round amounts
        if amount % 1000 == 0 and amount >= 5000:
            warnings.append({
                "code": "round_amount",
                "message": "Round amount payment - may require additional verification"
            })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_payment_method(self, payment_method: PaymentMethod) -> Dict[str, Any]:
        """Validate payment method."""
        errors = []
        
        if not payment_method.is_verified:
            errors.append({
                "code": "unverified_method",
                "message": "Payment method is not verified"
            })
        
        if payment_method.status != "active":
            errors.append({
                "code": "inactive_method",
                "message": f"Payment method is {payment_method.status}"
            })
        
        # Check expiry for cards
        if payment_method.card and payment_method.expires_at:
            if payment_method.expires_at < datetime.utcnow():
                errors.append({
                    "code": "expired_method",
                    "message": "Payment method has expired"
                })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _validate_limits(
        self,
        amount: Decimal,
        customer_id: str,
        payment_method: PaymentMethod
    ) -> Dict[str, Any]:
        """Validate payment limits."""
        errors = []
        warnings = []
        
        # Check transaction limit
        transaction_limit = payment_method.transaction_limit or self.transaction_limit_default
        if amount > transaction_limit:
            errors.append({
                "code": "exceeds_transaction_limit",
                "message": f"Amount exceeds transaction limit of {transaction_limit}"
            })
        
        # Check daily limit
        # TODO: Query database for today's transactions
        daily_total = Decimal("0")  # Placeholder
        daily_limit = payment_method.daily_limit or self.daily_limit_default
        
        if daily_total + amount > daily_limit:
            errors.append({
                "code": "exceeds_daily_limit",
                "message": f"Amount would exceed daily limit of {daily_limit}"
            })
        
        # Warn if approaching limit
        if daily_total + amount > daily_limit * Decimal("0.8"):
            warnings.append({
                "code": "approaching_daily_limit",
                "message": f"Approaching daily limit ({daily_total + amount}/{daily_limit})"
            })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_compliance(self, payment: Payment) -> Dict[str, Any]:
        """Validate compliance requirements."""
        errors = []
        warnings = []
        
        # Check for high-value reporting threshold (AUD 10,000)
        if payment.amount >= Decimal("10000"):
            warnings.append({
                "code": "reporting_threshold",
                "message": "Payment exceeds reporting threshold - will be reported to AUSTRAC"
            })
        
        # Check for international payments
        if payment.currency != "AUD":
            warnings.append({
                "code": "international_payment",
                "message": "International payment - additional compliance checks required"
            })
        
        # Validate required fields for compliance
        if not payment.description or len(payment.description) < 3:
            errors.append({
                "code": "missing_description",
                "message": "Payment description is required for compliance"
            })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def validate_batch(
        self,
        items: List[Dict[str, Any]],
        from_account_id: str,
        account_balance: Decimal
    ) -> Dict[str, Any]:
        """
        Validate a batch of payments.
        
        Args:
            items: List of payment items
            from_account_id: Source account ID
            account_balance: Current account balance
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        # Validate batch size
        if len(items) == 0:
            errors.append({
                "code": "empty_batch",
                "message": "Batch contains no items"
            })
        
        if len(items) > 1000:
            errors.append({
                "code": "batch_too_large",
                "message": "Batch exceeds maximum size of 1000 items"
            })
        
        # Calculate total
        total_amount = sum(Decimal(str(item.get("amount", 0))) for item in items)
        
        # Validate total against balance
        if total_amount > account_balance:
            errors.append({
                "code": "insufficient_funds",
                "message": f"Insufficient funds for batch. Available: {account_balance}, Required: {total_amount}"
            })
        
        # Validate individual items
        item_errors = []
        for idx, item in enumerate(items):
            item_validation = self._validate_batch_item(item, idx)
            if not item_validation["valid"]:
                item_errors.extend(item_validation["errors"])
        
        if item_errors:
            errors.extend(item_errors)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_amount": total_amount,
            "item_count": len(items)
        }
    
    def _validate_batch_item(self, item: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Validate a single batch item."""
        errors = []
        
        # Validate amount
        amount = item.get("amount")
        if not amount or Decimal(str(amount)) <= 0:
            errors.append({
                "code": "invalid_amount",
                "message": f"Item {index}: Invalid amount",
                "item_index": index
            })
        
        # Validate recipient
        has_account = item.get("to_account_id") or (item.get("to_bsb") and item.get("to_account_number"))
        has_payid = item.get("to_payid")
        
        if not (has_account or has_payid):
            errors.append({
                "code": "missing_recipient",
                "message": f"Item {index}: Missing recipient details",
                "item_index": index
            })
        
        # Validate description
        if not item.get("description"):
            errors.append({
                "code": "missing_description",
                "message": f"Item {index}: Description is required",
                "item_index": index
            })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
