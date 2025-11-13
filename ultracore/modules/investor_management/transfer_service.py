"""
Loan Transfer Service
Handles loan sales, buybacks, and ownership transfers
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import uuid

from .models import (
    LoanTransfer, TransferType, TransferStatus, TransferSubStatus,
    PaymentRouting, PaymentRoutingStatus,
    InitiateLoanTransferRequest, ApproveTransferRequest, CancelTransferRequest
)
from .kafka_events import InvestorKafkaProducer
from .investor_service import InvestorService


class LoanTransferService:
    """
    Loan Transfer Service
    
    Handles:
    - Loan sales to investors
    - Intermediary sales (investor to investor)
    - Buybacks
    - Partial sales
    - Securitization transfers
    """
    
    def __init__(self, investor_service: InvestorService):
        self.transfers: Dict[str, LoanTransfer] = {}
        self.payment_routings: Dict[str, PaymentRouting] = {}
        self.loan_ownership: Dict[str, List[str]] = {}  # loan_id -> [investor_ids]
        self.kafka_producer = InvestorKafkaProducer()
        self.investor_service = investor_service
        
    def initiate_transfer(
        self,
        request: InitiateLoanTransferRequest,
        outstanding_principal: Decimal,
        outstanding_interest: Decimal = Decimal("0.00")
    ) -> LoanTransfer:
        """
        Initiate a loan transfer
        
        Args:
            request: Transfer request
            outstanding_principal: Current principal balance
            outstanding_interest: Current interest balance
            
        Returns:
            Created transfer
        """
        
        # Validate investor exists and is active
        investor = self.investor_service.get_investor(request.to_investor_id)
        if not investor:
            raise ValueError(f"Investor {request.to_investor_id} not found")
        if investor.status.value != "active":
            raise ValueError(f"Investor {request.to_investor_id} is not active")
        
        # Generate transfer ID
        transfer_id = f"TRF-{uuid.uuid4().hex[:12].upper()}"
        external_id = f"EXT-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate purchase price
        purchase_price = outstanding_principal * request.purchase_price_ratio
        
        # Determine from_investor_id
        from_investor_id = None
        current_owners = self.loan_ownership.get(request.loan_id, [])
        if current_owners:
            from_investor_id = current_owners[0]  # Assuming single owner for now
        
        # Create transfer
        transfer = LoanTransfer(
            transfer_id=transfer_id,
            external_id=external_id,
            loan_id=request.loan_id,
            transfer_type=request.transfer_type,
            from_investor_id=from_investor_id,
            to_investor_id=request.to_investor_id,
            outstanding_principal=outstanding_principal,
            outstanding_interest=outstanding_interest,
            purchase_price=purchase_price,
            purchase_price_ratio=request.purchase_price_ratio,
            transfer_percentage=request.transfer_percentage,
            settlement_date=request.settlement_date,
            effective_date_from=request.effective_date_from,
            created_by=request.created_by,
            status=TransferStatus.PENDING,
            sub_status=TransferSubStatus.AWAITING_APPROVAL,
            notes=request.notes
        )
        
        # Store transfer
        self.transfers[transfer_id] = transfer
        
        # Calculate gain/loss
        if from_investor_id is None:  # Sale from originator
            transfer.gain_loss_amount = purchase_price - outstanding_principal
        
        # Publish event
        self.kafka_producer.publish_transfer_initiated(
            transfer_id=transfer_id,
            loan_id=request.loan_id,
            from_investor_id=from_investor_id,
            to_investor_id=request.to_investor_id,
            transfer_type=request.transfer_type.value,
            outstanding_principal=outstanding_principal,
            purchase_price=purchase_price,
            purchase_price_ratio=request.purchase_price_ratio,
            settlement_date=request.settlement_date,
            created_by=request.created_by
        )
        
        return transfer
        
    def approve_transfer(
        self,
        request: ApproveTransferRequest
    ) -> LoanTransfer:
        """
        Approve a pending transfer
        
        Args:
            request: Approval request
            
        Returns:
            Updated transfer
        """
        
        transfer = self.transfers.get(request.transfer_id)
        if not transfer:
            raise ValueError(f"Transfer {request.transfer_id} not found")
        
        if transfer.status != TransferStatus.PENDING:
            raise ValueError(f"Transfer {request.transfer_id} is not pending")
        
        # Update transfer
        transfer.status = TransferStatus.APPROVED
        transfer.sub_status = TransferSubStatus.AWAITING_SETTLEMENT
        transfer.approval_date = datetime.now(timezone.utc)
        transfer.approved_by = request.approved_by
        transfer.updated_at = datetime.now(timezone.utc)
        
        if request.notes:
            transfer.notes = f"{transfer.notes}\n\nApproval: {request.notes}"
        
        # Publish event
        self.kafka_producer.publish_transfer_approved(
            transfer_id=transfer.transfer_id,
            loan_id=transfer.loan_id,
            to_investor_id=transfer.to_investor_id,
            approved_by=request.approved_by
        )
        
        return transfer
        
    def execute_settlement(
        self,
        transfer_id: str
    ) -> LoanTransfer:
        """
        Execute settlement on settlement date
        
        This would be called by a scheduled job on the settlement date
        
        Args:
            transfer_id: Transfer ID
            
        Returns:
            Updated transfer
        """
        
        transfer = self.transfers.get(transfer_id)
        if not transfer:
            raise ValueError(f"Transfer {transfer_id} not found")
        
        if transfer.status != TransferStatus.APPROVED:
            raise ValueError(f"Transfer {transfer_id} is not approved")
        
        # Check if settlement date has arrived
        if date.today() < transfer.settlement_date:
            raise ValueError(f"Settlement date {transfer.settlement_date} has not arrived")
        
        # Update transfer status
        transfer.status = TransferStatus.SETTLEMENT_IN_PROGRESS
        transfer.sub_status = TransferSubStatus.AWAITING_PAYMENT
        transfer.updated_at = datetime.now(timezone.utc)
        
        # In production, this would:
        # 1. Initiate payment from investor to originator
        # 2. Wait for payment confirmation
        # 3. Transfer ownership
        # 4. Create accounting entries
        
        # For now, simulate immediate settlement
        transfer.status = TransferStatus.ACTIVE
        transfer.sub_status = TransferSubStatus.PAYMENT_RECEIVED
        
        # Transfer ownership
        self._transfer_ownership(transfer)
        
        # Create payment routing
        self._create_payment_routing(transfer)
        
        # Publish events
        self.kafka_producer.publish_loan_ownership_transferred(
            loan_id=transfer.loan_id,
            transfer_id=transfer.transfer_id,
            from_owner=transfer.from_investor_id,
            to_owner=transfer.to_investor_id,
            transfer_percentage=transfer.transfer_percentage,
            effective_date=transfer.effective_date_from
        )
        
        return transfer
        
    def _transfer_ownership(
        self,
        transfer: LoanTransfer
    ):
        """
        Transfer loan ownership
        
        Args:
            transfer: Transfer record
        """
        
        loan_id = transfer.loan_id
        
        # Remove from previous owner
        if transfer.from_investor_id:
            current_owners = self.loan_ownership.get(loan_id, [])
            if transfer.from_investor_id in current_owners:
                current_owners.remove(transfer.from_investor_id)
                self.loan_ownership[loan_id] = current_owners
        
        # Add to new owner
        if loan_id not in self.loan_ownership:
            self.loan_ownership[loan_id] = []
        
        if transfer.to_investor_id not in self.loan_ownership[loan_id]:
            self.loan_ownership[loan_id].append(transfer.to_investor_id)
        
    def _create_payment_routing(
        self,
        transfer: LoanTransfer
    ):
        """
        Create payment routing for transferred loan
        
        Args:
            transfer: Transfer record
        """
        
        routing_id = f"RTE-{uuid.uuid4().hex[:12].upper()}"
        
        routing = PaymentRouting(
            routing_id=routing_id,
            loan_id=transfer.loan_id,
            investor_id=transfer.to_investor_id,
            transfer_id=transfer.transfer_id,
            route_principal=True,
            route_interest=True,
            route_fees=False,  # Fees retained by originator
            routing_percentage=transfer.transfer_percentage,
            status=PaymentRoutingStatus.ACTIVE,
            effective_from=transfer.effective_date_from,
            effective_to=transfer.effective_date_to
        )
        
        self.payment_routings[routing_id] = routing
        
        # Publish event
        self.kafka_producer.publish_payment_routing_activated(
            routing_id=routing_id,
            loan_id=transfer.loan_id,
            investor_id=transfer.to_investor_id,
            transfer_id=transfer.transfer_id,
            routing_percentage=transfer.transfer_percentage,
            effective_from=transfer.effective_date_from
        )
        
    def cancel_transfer(
        self,
        request: CancelTransferRequest
    ) -> LoanTransfer:
        """
        Cancel a pending or approved transfer
        
        Args:
            request: Cancellation request
            
        Returns:
            Updated transfer
        """
        
        transfer = self.transfers.get(request.transfer_id)
        if not transfer:
            raise ValueError(f"Transfer {request.transfer_id} not found")
        
        if transfer.status not in [TransferStatus.PENDING, TransferStatus.APPROVED]:
            raise ValueError(f"Transfer {request.transfer_id} cannot be cancelled")
        
        # Update transfer
        transfer.status = TransferStatus.CANCELLED
        transfer.updated_at = datetime.now(timezone.utc)
        transfer.notes = f"{transfer.notes}\n\nCancelled: {request.reason}"
        
        # Publish event
        self.kafka_producer._publish("transfer-events", {
            "event_type": "transfer.cancelled",
            "transfer_id": transfer.transfer_id,
            "loan_id": transfer.loan_id,
            "reason": request.reason,
            "cancelled_by": request.cancelled_by,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return transfer
        
    def get_transfer(
        self,
        transfer_id: str
    ) -> Optional[LoanTransfer]:
        """Get transfer by ID"""
        return self.transfers.get(transfer_id)
        
    def get_transfers_for_loan(
        self,
        loan_id: str
    ) -> List[LoanTransfer]:
        """Get all transfers for a loan"""
        return [t for t in self.transfers.values() if t.loan_id == loan_id]
        
    def get_active_transfer_for_loan(
        self,
        loan_id: str
    ) -> Optional[LoanTransfer]:
        """Get active transfer for a loan"""
        for transfer in self.transfers.values():
            if transfer.loan_id == loan_id and transfer.status == TransferStatus.ACTIVE:
                return transfer
        return None
        
    def get_transfers_for_investor(
        self,
        investor_id: str
    ) -> List[LoanTransfer]:
        """Get all transfers for an investor"""
        return [
            t for t in self.transfers.values()
            if t.to_investor_id == investor_id or t.from_investor_id == investor_id
        ]
        
    def get_loan_owner(
        self,
        loan_id: str
    ) -> Optional[str]:
        """Get current owner of a loan"""
        owners = self.loan_ownership.get(loan_id, [])
        return owners[0] if owners else None
        
    def get_payment_routing_for_loan(
        self,
        loan_id: str
    ) -> Optional[PaymentRouting]:
        """Get active payment routing for a loan"""
        for routing in self.payment_routings.values():
            if routing.loan_id == loan_id and routing.status == PaymentRoutingStatus.ACTIVE:
                return routing
        return None
        
    def route_payment_to_investor(
        self,
        loan_id: str,
        payment_id: str,
        amount: Decimal,
        payment_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Route a payment to the investor
        
        Args:
            loan_id: Loan ID
            payment_id: Payment ID
            amount: Payment amount
            payment_type: Type of payment (principal, interest, fee)
            
        Returns:
            Routing details if routed, None if retained by originator
        """
        
        routing = self.get_payment_routing_for_loan(loan_id)
        if not routing:
            return None  # No routing, payment goes to originator
        
        # Check if this payment type should be routed
        should_route = False
        if payment_type == "principal" and routing.route_principal:
            should_route = True
        elif payment_type == "interest" and routing.route_interest:
            should_route = True
        elif payment_type == "fee" and routing.route_fees:
            should_route = True
        
        if not should_route:
            return None
        
        # Calculate routed amount
        routed_amount = amount * (routing.routing_percentage / Decimal("100.00"))
        
        # Publish event
        self.kafka_producer.publish_payment_routed_to_investor(
            payment_id=payment_id,
            loan_id=loan_id,
            investor_id=routing.investor_id,
            amount=routed_amount,
            payment_type=payment_type,
            routing_percentage=routing.routing_percentage
        )
        
        return {
            "investor_id": routing.investor_id,
            "routed_amount": routed_amount,
            "routing_percentage": routing.routing_percentage,
            "retained_amount": amount - routed_amount
        }
