"""
Bank Integration Module
NPP, BPAY, Direct Debit/Credit integration
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal
import uuid

class PaymentStatus(str, Enum):
    """Payment status"""
    INITIATED = "initiated"
    PROCESSING = "processing"
    CLEARED = "cleared"
    SETTLED = "settled"
    FAILED = "failed"
    REVERSED = "reversed"

class BankIntegration:
    """
    Bank Integration for Australian Payments
    
    Supports:
    - NPP (New Payments Platform) - Instant payments
    - BPAY - Bill payments
    - Direct Credit - Standard transfers (1-2 days)
    - Direct Debit - Automated debits
    """
    
    def __init__(self):
        self.payment_queue = []
        self.processed_payments = []
        
    def process_npp_payment(
        self,
        from_account: str,
        to_account: str,
        bsb: str,
        amount: Decimal,
        reference: str,
        payment_id: str = None
    ) -> Dict[str, Any]:
        """
        Process NPP (New Payments Platform) payment
        
        NPP Features:
        - Real-time payments (seconds)
        - 24/7/365 availability
        - PayID support
        - Osko payments
        - Max $1M per transaction
        """
        
        payment_id = payment_id or f"NPP-{uuid.uuid4().hex[:12].upper()}"
        
        # Validate amount
        if amount > Decimal("1000000"):
            return {
                "success": False,
                "error": "Amount exceeds NPP limit ($1M)"
            }
        
        # Validate BSB format
        if not self._validate_bsb(bsb):
            return {
                "success": False,
                "error": "Invalid BSB format"
            }
        
        payment = {
            "payment_id": payment_id,
            "payment_method": "NPP",
            "from_account": from_account,
            "to_account": to_account,
            "bsb": bsb,
            "amount": float(amount),
            "reference": reference,
            "status": PaymentStatus.INITIATED,
            "initiated_at": datetime.now(timezone.utc).isoformat(),
            "cleared_at": None,
            "settlement_time": "Real-time (seconds)",
            "fee": 0.0  # NPP typically no fee for retail
        }
        
        # Simulate instant processing
        payment["status"] = PaymentStatus.PROCESSING
        
        # NPP is real-time - immediate clearing
        payment["status"] = PaymentStatus.CLEARED
        payment["cleared_at"] = datetime.now(timezone.utc).isoformat()
        
        # Immediate settlement
        payment["status"] = PaymentStatus.SETTLED
        payment["settled_at"] = datetime.now(timezone.utc).isoformat()
        
        self.processed_payments.append(payment)
        
        return {
            "success": True,
            "payment": payment
        }
    
    def process_bpay_payment(
        self,
        from_account: str,
        biller_code: str,
        reference_number: str,
        amount: Decimal,
        payment_id: str = None
    ) -> Dict[str, Any]:
        """
        Process BPAY payment
        
        BPAY Features:
        - Bill payments
        - Biller code + reference number
        - 1-3 business days
        - Max $99,999.99 per transaction
        """
        
        payment_id = payment_id or f"BPAY-{uuid.uuid4().hex[:12].upper()}"
        
        # Validate amount
        if amount > Decimal("99999.99"):
            return {
                "success": False,
                "error": "Amount exceeds BPAY limit ($99,999.99)"
            }
        
        # Validate biller code
        if not self._validate_biller_code(biller_code):
            return {
                "success": False,
                "error": "Invalid biller code format"
            }
        
        payment = {
            "payment_id": payment_id,
            "payment_method": "BPAY",
            "from_account": from_account,
            "biller_code": biller_code,
            "reference_number": reference_number,
            "amount": float(amount),
            "status": PaymentStatus.INITIATED,
            "initiated_at": datetime.now(timezone.utc).isoformat(),
            "expected_settlement": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "settlement_time": "1-3 business days",
            "fee": 0.0  # BPAY typically no fee
        }
        
        self.payment_queue.append(payment)
        
        return {
            "success": True,
            "payment": payment,
            "message": "BPAY payment queued for processing"
        }
    
    def process_direct_credit(
        self,
        from_account: str,
        to_account: str,
        to_name: str,
        bsb: str,
        amount: Decimal,
        description: str,
        payment_id: str = None
    ) -> Dict[str, Any]:
        """
        Process Direct Credit payment
        
        Direct Credit Features:
        - Standard bank transfer
        - 1-2 business days
        - Batch processing
        - No transaction limit (bank-dependent)
        """
        
        payment_id = payment_id or f"DC-{uuid.uuid4().hex[:12].upper()}"
        
        # Validate BSB
        if not self._validate_bsb(bsb):
            return {
                "success": False,
                "error": "Invalid BSB format"
            }
        
        payment = {
            "payment_id": payment_id,
            "payment_method": "DIRECT_CREDIT",
            "from_account": from_account,
            "to_account": to_account,
            "to_name": to_name,
            "bsb": bsb,
            "amount": float(amount),
            "description": description,
            "status": PaymentStatus.INITIATED,
            "initiated_at": datetime.now(timezone.utc).isoformat(),
            "expected_settlement": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "settlement_time": "1-2 business days",
            "fee": 0.0
        }
        
        self.payment_queue.append(payment)
        
        return {
            "success": True,
            "payment": payment,
            "message": "Direct credit queued for processing"
        }
    
    def process_direct_debit(
        self,
        from_account: str,
        from_name: str,
        bsb: str,
        to_account: str,
        amount: Decimal,
        mandate_id: str,
        reference: str,
        payment_id: str = None
    ) -> Dict[str, Any]:
        """
        Process Direct Debit
        
        Direct Debit Features:
        - Requires customer mandate
        - 3-5 business days processing
        - Used for recurring payments
        - Dispute period (7 days)
        """
        
        payment_id = payment_id or f"DD-{uuid.uuid4().hex[:12].upper()}"
        
        # Validate BSB
        if not self._validate_bsb(bsb):
            return {
                "success": False,
                "error": "Invalid BSB format"
            }
        
        # Validate mandate
        if not mandate_id:
            return {
                "success": False,
                "error": "Direct debit mandate required"
            }
        
        payment = {
            "payment_id": payment_id,
            "payment_method": "DIRECT_DEBIT",
            "from_account": from_account,
            "from_name": from_name,
            "bsb": bsb,
            "to_account": to_account,
            "amount": float(amount),
            "mandate_id": mandate_id,
            "reference": reference,
            "status": PaymentStatus.INITIATED,
            "initiated_at": datetime.now(timezone.utc).isoformat(),
            "expected_settlement": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "settlement_time": "3-5 business days",
            "dispute_period_ends": (datetime.now(timezone.utc) + timedelta(days=12)).isoformat(),
            "fee": 0.0
        }
        
        self.payment_queue.append(payment)
        
        return {
            "success": True,
            "payment": payment,
            "message": "Direct debit queued for processing"
        }
    
    def process_payment_queue(self):
        """Process pending payments in queue"""
        
        processed = []
        
        for payment in self.payment_queue:
            # Simulate processing based on payment method
            if payment["payment_method"] == "BPAY":
                # BPAY takes 1-3 days
                initiated = datetime.fromisoformat(payment["initiated_at"])
                if (datetime.now(timezone.utc) - initiated).days >= 1:
                    payment["status"] = PaymentStatus.SETTLED
                    payment["settled_at"] = datetime.now(timezone.utc).isoformat()
                    processed.append(payment)
            
            elif payment["payment_method"] == "DIRECT_CREDIT":
                # Direct credit takes 1-2 days
                initiated = datetime.fromisoformat(payment["initiated_at"])
                if (datetime.now(timezone.utc) - initiated).days >= 2:
                    payment["status"] = PaymentStatus.SETTLED
                    payment["settled_at"] = datetime.now(timezone.utc).isoformat()
                    processed.append(payment)
            
            elif payment["payment_method"] == "DIRECT_DEBIT":
                # Direct debit takes 3-5 days
                initiated = datetime.fromisoformat(payment["initiated_at"])
                if (datetime.now(timezone.utc) - initiated).days >= 5:
                    payment["status"] = PaymentStatus.SETTLED
                    payment["settled_at"] = datetime.now(timezone.utc).isoformat()
                    processed.append(payment)
        
        # Move processed payments
        for payment in processed:
            self.payment_queue.remove(payment)
            self.processed_payments.append(payment)
        
        return {
            "processed_count": len(processed),
            "remaining_in_queue": len(self.payment_queue)
        }
    
    def get_payment_status(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment status"""
        
        # Check processed payments
        payment = next(
            (p for p in self.processed_payments if p["payment_id"] == payment_id),
            None
        )
        
        if payment:
            return payment
        
        # Check queue
        payment = next(
            (p for p in self.payment_queue if p["payment_id"] == payment_id),
            None
        )
        
        return payment
    
    def _validate_bsb(self, bsb: str) -> bool:
        """Validate BSB format (XXX-XXX)"""
        
        # Remove spaces and hyphens
        bsb_clean = bsb.replace("-", "").replace(" ", "")
        
        return len(bsb_clean) == 6 and bsb_clean.isdigit()
    
    def _validate_biller_code(self, biller_code: str) -> bool:
        """Validate BPAY biller code"""
        
        # Biller codes are typically 4-6 digits
        return len(biller_code) >= 4 and len(biller_code) <= 6 and biller_code.isdigit()

# Global bank integration instance
bank_integration = BankIntegration()
