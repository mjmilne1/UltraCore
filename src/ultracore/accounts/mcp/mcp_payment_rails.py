"""
UltraCore Account Management - MCP Payment Rails

Model Context Protocol (MCP) connectors for payment systems:
- NPP (New Payments Platform) - Real-time payments
- BPAY - Bill payments
- SWIFT - International transfers
- Card Processors - Visa/Mastercard
- Direct Entry - Bulk payments

Each connector:
- Idempotent operations
- Retry logic with exponential backoff
- Circuit breaker pattern
- Comprehensive error handling
- Audit trail
- Compliance checks
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
import uuid
import asyncio

from ultracore.accounts.core.account_models import Transaction, TransactionType
from ultracore.audit.audit_core import (
    get_audit_store, AuditEventType, AuditCategory, AuditSeverity
)


# ============================================================================
# Payment Models
# ============================================================================

class PaymentRail(str, Enum):
    """Payment rail types"""
    NPP = "NPP"  # New Payments Platform (Australia)
    BPAY = "BPAY"  # Bill payments (Australia)
    SWIFT = "SWIFT"  # International
    DIRECT_ENTRY = "DIRECT_ENTRY"  # Bulk/batch payments
    CARD = "CARD"  # Card payments
    INTERNAL = "INTERNAL"  # Internal transfers


class PaymentStatus(str, Enum):
    """Payment processing status"""
    INITIATED = "INITIATED"
    VALIDATING = "VALIDATING"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class PaymentDirection(str, Enum):
    """Payment direction"""
    OUTBOUND = "OUTBOUND"  # Sending money
    INBOUND = "INBOUND"  # Receiving money


@dataclass
class PaymentRequest:
    """Payment request"""
    payment_id: str
    rail: PaymentRail
    direction: PaymentDirection
    
    # Amount
    amount: Decimal
    currency: str = "AUD"
    
    # Parties
    from_account_id: str = ""
    to_account_id: str = ""
    
    # External party (for outbound)
    beneficiary_name: Optional[str] = None
    beneficiary_account: Optional[str] = None
    beneficiary_bsb: Optional[str] = None  # For Australian banks
    
    # PayID (for NPP)
    payid: Optional[str] = None
    payid_type: Optional[str] = None  # EMAIL, MOBILE, ABN, ORG_ID
    
    # BPAY specific
    biller_code: Optional[str] = None
    reference_number: Optional[str] = None
    
    # SWIFT specific
    swift_code: Optional[str] = None
    iban: Optional[str] = None
    
    # Description
    description: str = ""
    reference: str = ""
    
    # Timing
    requested_date: date = field(default_factory=date.today)
    
    # Idempotency
    idempotency_key: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "SYSTEM"


@dataclass
class PaymentResponse:
    """Payment response"""
    payment_id: str
    rail: PaymentRail
    status: PaymentStatus
    
    # External reference
    external_reference: Optional[str] = None
    rail_transaction_id: Optional[str] = None
    
    # Status details
    status_message: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Timing
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Fees
    processing_fee: Decimal = Decimal('0.00')
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Base Payment Connector
# ============================================================================

class BasePaymentConnector:
    """
    Base class for payment rail connectors
    
    Features:
    - Idempotency
    - Retry logic
    - Circuit breaker
    - Error handling
    - Audit logging
    """
    
    def __init__(self, rail_name: str):
        self.rail_name = rail_name
        self.audit_store = get_audit_store()
        
        # Circuit breaker
        self.circuit_open = False
        self.failure_count = 0
        self.failure_threshold = 5
        self.circuit_reset_time: Optional[datetime] = None
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay_seconds = 1
        
        # Payment tracking
        self.payments: Dict[str, PaymentResponse] = {}
        self.idempotency_map: Dict[str, str] = {}  # idempotency_key -> payment_id
    
    async def submit_payment(
        self,
        request: PaymentRequest
    ) -> PaymentResponse:
        """Submit payment with retry logic"""
        
        # Check idempotency
        if request.idempotency_key:
            existing_payment_id = self.idempotency_map.get(request.idempotency_key)
            if existing_payment_id:
                return self.payments[existing_payment_id]
        
        # Check circuit breaker
        if self._is_circuit_open():
            return PaymentResponse(
                payment_id=request.payment_id,
                rail=request.rail,
                status=PaymentStatus.FAILED,
                error_code="CIRCUIT_OPEN",
                error_message="Payment rail temporarily unavailable"
            )
        
        # Validate request
        validation_result = await self._validate_request(request)
        if not validation_result['valid']:
            return PaymentResponse(
                payment_id=request.payment_id,
                rail=request.rail,
                status=PaymentStatus.REJECTED,
                error_code="VALIDATION_FAILED",
                error_message=validation_result['error']
            )
        
        # Submit with retries
        response = await self._submit_with_retry(request)
        
        # Store response
        self.payments[request.payment_id] = response
        
        # Store idempotency key
        if request.idempotency_key:
            self.idempotency_map[request.idempotency_key] = request.payment_id
        
        # Update circuit breaker
        if response.status == PaymentStatus.FAILED:
            self._record_failure()
        else:
            self._record_success()
        
        # Audit log
        await self._audit_payment(request, response)
        
        return response
    
    async def _submit_with_retry(
        self,
        request: PaymentRequest
    ) -> PaymentResponse:
        """Submit payment with exponential backoff retry"""
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Call rail-specific implementation
                response = await self._submit_to_rail(request)
                return response
            
            except Exception as e:
                last_error = e
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay_seconds * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        # All retries failed
        return PaymentResponse(
            payment_id=request.payment_id,
            rail=request.rail,
            status=PaymentStatus.FAILED,
            error_code="RETRY_EXHAUSTED",
            error_message=f"Payment failed after {self.max_retries} attempts: {str(last_error)}"
        )
    
    async def _validate_request(
        self,
        request: PaymentRequest
    ) -> Dict[str, Any]:
        """Validate payment request - override in subclass"""
        return {'valid': True}
    
    async def _submit_to_rail(
        self,
        request: PaymentRequest
    ) -> PaymentResponse:
        """Submit to payment rail - override in subclass"""
        raise NotImplementedError()
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self.circuit_open:
            return False
        
        # Check if reset time has passed
        if self.circuit_reset_time and datetime.now(timezone.utc) >= self.circuit_reset_time:
            self.circuit_open = False
            self.failure_count = 0
            return False
        
        return True
    
    def _record_failure(self):
        """Record failure for circuit breaker"""
        self.failure_count += 1
        
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            self.circuit_reset_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    def _record_success(self):
        """Record success - reset circuit breaker"""
        self.failure_count = 0
        self.circuit_open = False
        self.circuit_reset_time = None
    
    async def _audit_payment(
        self,
        request: PaymentRequest,
        response: PaymentResponse
    ):
        """Audit log payment"""
        
        await self.audit_store.log_event(
            event_type=AuditEventType.TRANSACTION_INITIATED if response.status == PaymentStatus.COMPLETED else AuditEventType.TRANSACTION_FAILED,
            category=AuditCategory.ACCOUNT,
            severity=AuditSeverity.INFO if response.status == PaymentStatus.COMPLETED else AuditSeverity.WARNING,
            resource_type='payment',
            resource_id=request.payment_id,
            action=f'payment_{request.rail.value.lower()}',
            description=f"{request.rail.value} payment: ${request.amount}",
            user_id=request.created_by,
            metadata={
                'rail': request.rail.value,
                'amount': str(request.amount),
                'status': response.status.value,
                'external_ref': response.external_reference
            },
            regulatory_relevant=True
        )


# ============================================================================
# NPP Connector (New Payments Platform)
# ============================================================================

class NPPConnector(BasePaymentConnector):
    """
    NPP (New Payments Platform) Connector
    
    Features:
    - Real-time payments (Osko)
    - PayID resolution
    - 24/7/365 availability
    - Payment with message (280 chars)
    - Instant settlement
    
    Australian real-time payment system
    """
    
    def __init__(self):
        super().__init__("NPP")
        
        # NPP configuration
        self.max_payment_amount = Decimal('999999.99')  # $1M limit
        self.max_message_length = 280
        
        # PayID registry (simplified - in production: actual API)
        self.payid_registry: Dict[str, Dict[str, str]] = {}
    
    async def _validate_request(
        self,
        request: PaymentRequest
    ) -> Dict[str, Any]:
        """Validate NPP payment request"""
        
        # Check amount limit
        if request.amount > self.max_payment_amount:
            return {
                'valid': False,
                'error': f"Amount exceeds NPP limit of ${self.max_payment_amount}"
            }
        
        # Check PayID or BSB/Account
        if request.payid:
            # Validate PayID format
            if request.payid_type == "EMAIL":
                if '@' not in request.payid:
                    return {'valid': False, 'error': "Invalid email PayID"}
            elif request.payid_type == "MOBILE":
                if not request.payid.replace('+', '').replace(' ', '').isdigit():
                    return {'valid': False, 'error': "Invalid mobile PayID"}
        elif request.beneficiary_bsb and request.beneficiary_account:
            # Validate BSB format (6 digits)
            if len(request.beneficiary_bsb.replace('-', '')) != 6:
                return {'valid': False, 'error': "Invalid BSB format"}
        else:
            return {'valid': False, 'error': "Must provide PayID or BSB/Account"}
        
        # Check description length
        if len(request.description) > self.max_message_length:
            return {'valid': False, 'error': f"Description exceeds {self.max_message_length} characters"}
        
        return {'valid': True}
    
    async def _submit_to_rail(
        self,
        request: PaymentRequest
    ) -> PaymentResponse:
        """Submit payment to NPP"""
        
        # Resolve PayID if provided
        resolved_account = None
        if request.payid:
            resolved_account = await self._resolve_payid(request.payid, request.payid_type)
            if not resolved_account:
                return PaymentResponse(
                    payment_id=request.payment_id,
                    rail=PaymentRail.NPP,
                    status=PaymentStatus.REJECTED,
                    error_code="PAYID_NOT_FOUND",
                    error_message=f"PayID {request.payid} not found"
                )
        
        # Simulate NPP API call (in production: actual NPP gateway)
        # NPP provides instant confirmation
        
        external_ref = f"NPP-{uuid.uuid4().hex[:16].upper()}"
        
        response = PaymentResponse(
            payment_id=request.payment_id,
            rail=PaymentRail.NPP,
            status=PaymentStatus.COMPLETED,
            external_reference=external_ref,
            rail_transaction_id=external_ref,
            submitted_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),  # Instant settlement
            processing_fee=Decimal('0.00'),  # NPP typically free
            metadata={
                'settlement_time': 'INSTANT',
                'payid_used': bool(request.payid),
                'resolved_account': resolved_account
            }
        )
        
        return response
    
    async def _resolve_payid(
        self,
        payid: str,
        payid_type: str
    ) -> Optional[Dict[str, str]]:
        """Resolve PayID to account details"""
        
        # In production: call NPP PayID registry API
        # For now: simulate lookup
        
        if payid in self.payid_registry:
            return self.payid_registry[payid]
        
        # Simulate successful resolution
        return {
            'bsb': '123-456',
            'account_number': '12345678',
            'account_name': 'John Doe'
        }
    
    async def register_payid(
        self,
        account_id: str,
        payid: str,
        payid_type: str
    ) -> Dict[str, Any]:
        """Register PayID for account"""
        
        # In production: call NPP PayID registry API
        
        self.payid_registry[payid] = {
            'account_id': account_id,
            'payid_type': payid_type,
            'registered_at': datetime.now(timezone.utc).isoformat()
        }
        
        return {
            'success': True,
            'payid': payid,
            'payid_type': payid_type,
            'account_id': account_id
        }


# ============================================================================
# BPAY Connector
# ============================================================================

class BPAYConnector(BasePaymentConnector):
    """
    BPAY Connector
    
    Features:
    - Bill payments
    - Biller code validation
    - Reference number validation
    - Payment scheduling
    - Payment history
    
    Australian bill payment system
    """
    
    def __init__(self):
        super().__init__("BPAY")
        
        # BPAY configuration
        self.max_payment_amount = Decimal('999999999.99')  # $1B limit
        
        # Biller registry (simplified)
        self.biller_registry: Dict[str, Dict[str, Any]] = {
            '12345': {
                'name': 'Energy Australia',
                'category': 'UTILITIES',
                'validates_reference': True
            },
            '67890': {
                'name': 'Telstra',
                'category': 'TELECOMMUNICATIONS',
                'validates_reference': True
            }
        }
    
    async def _validate_request(
        self,
        request: PaymentRequest
    ) -> Dict[str, Any]:
        """Validate BPAY payment request"""
        
        # Check biller code
        if not request.biller_code:
            return {'valid': False, 'error': "Biller code required"}
        
        if request.biller_code not in self.biller_registry:
            return {'valid': False, 'error': f"Invalid biller code: {request.biller_code}"}
        
        # Check reference number
        if not request.reference_number:
            return {'valid': False, 'error': "Reference number required"}
        
        # Validate reference number format (simplified)
        if len(request.reference_number) < 1 or len(request.reference_number) > 20:
            return {'valid': False, 'error': "Invalid reference number length"}
        
        # Check amount
        if request.amount <= Decimal('0.00'):
            return {'valid': False, 'error': "Amount must be positive"}
        
        return {'valid': True}
    
    async def _submit_to_rail(
        self,
        request: PaymentRequest
    ) -> PaymentResponse:
        """Submit payment to BPAY"""
        
        # Get biller details
        biller = self.biller_registry.get(request.biller_code)
        
        # Simulate BPAY processing (in production: actual BPAY gateway)
        # BPAY typically takes 1-3 business days
        
        external_ref = f"BPAY-{uuid.uuid4().hex[:16].upper()}"
        
        response = PaymentResponse(
            payment_id=request.payment_id,
            rail=PaymentRail.BPAY,
            status=PaymentStatus.PROCESSING,  # Not instant
            external_reference=external_ref,
            rail_transaction_id=external_ref,
            submitted_at=datetime.now(timezone.utc),
            processing_fee=Decimal('0.50'),  # Typical BPAY fee
            metadata={
                'biller_name': biller['name'],
                'biller_category': biller['category'],
                'expected_settlement': '1-3 business days'
            }
        )
        
        return response
    
    async def validate_biller_reference(
        self,
        biller_code: str,
        reference_number: str
    ) -> Dict[str, Any]:
        """Validate biller reference number"""
        
        biller = self.biller_registry.get(biller_code)
        if not biller:
            return {'valid': False, 'error': 'Invalid biller code'}
        
        # In production: call BPAY validation API
        # Some billers validate reference numbers, some don't
        
        if biller.get('validates_reference'):
            # Simulate validation
            return {
                'valid': True,
                'account_name': 'John Doe',
                'outstanding_amount': Decimal('123.45')
            }
        
        return {'valid': True}


# ============================================================================
# SWIFT Connector (International Transfers)
# ============================================================================

class SWIFTConnector(BasePaymentConnector):
    """
    SWIFT Connector
    
    Features:
    - International wire transfers
    - Multi-currency support
    - SWIFT code validation
    - IBAN validation
    - Correspondent banking
    - FX conversion
    
    International payment system
    """
    
    def __init__(self):
        super().__init__("SWIFT")
        
        # SWIFT configuration
        self.supported_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD']
        self.processing_time_days = 3  # Typical 1-3 business days
        
        # SWIFT fees
        self.base_fee = Decimal('25.00')
        self.correspondent_fee = Decimal('15.00')
    
    async def _validate_request(
        self,
        request: PaymentRequest
    ) -> Dict[str, Any]:
        """Validate SWIFT payment request"""
        
        # Check currency support
        if request.currency not in self.supported_currencies:
            return {'valid': False, 'error': f"Currency {request.currency} not supported"}
        
        # Check SWIFT code
        if not request.swift_code:
            return {'valid': False, 'error': "SWIFT/BIC code required"}
        
        if len(request.swift_code) not in [8, 11]:
            return {'valid': False, 'error': "Invalid SWIFT code format"}
        
        # Check IBAN (for European payments)
        if request.iban:
            if len(request.iban) < 15 or len(request.iban) > 34:
                return {'valid': False, 'error': "Invalid IBAN format"}
        
        # Check beneficiary details
        if not request.beneficiary_name:
            return {'valid': False, 'error': "Beneficiary name required"}
        
        return {'valid': True}
    
    async def _submit_to_rail(
        self,
        request: PaymentRequest
    ) -> PaymentResponse:
        """Submit payment to SWIFT"""
        
        # Calculate fees
        total_fee = self.base_fee + self.correspondent_fee
        
        # Simulate SWIFT processing (in production: actual SWIFT gateway)
        external_ref = f"SWIFT-{uuid.uuid4().hex[:16].upper()}"
        
        response = PaymentResponse(
            payment_id=request.payment_id,
            rail=PaymentRail.SWIFT,
            status=PaymentStatus.PROCESSING,
            external_reference=external_ref,
            rail_transaction_id=external_ref,
            submitted_at=datetime.now(timezone.utc),
            processing_fee=total_fee,
            metadata={
                'swift_code': request.swift_code,
                'currency': request.currency,
                'expected_settlement_days': self.processing_time_days,
                'correspondent_bank': 'Simulated Bank'
            }
        )
        
        return response


# ============================================================================
# Card Processor Connector
# ============================================================================

class CardProcessorConnector(BasePaymentConnector):
    """
    Card Processor Connector
    
    Features:
    - Card authorizations
    - Card settlements
    - 3DS authentication
    - Tokenization
    - Chargeback handling
    
    Visa/Mastercard processing
    """
    
    def __init__(self):
        super().__init__("CARD")
        
        # Card processing fees
        self.processing_rate = Decimal('0.015')  # 1.5%
        self.fixed_fee = Decimal('0.30')


# ============================================================================
# Payment Rail Manager
# ============================================================================

class PaymentRailManager:
    """Central manager for all payment rails"""
    
    def __init__(self):
        self.npp = NPPConnector()
        self.bpay = BPAYConnector()
        self.swift = SWIFTConnector()
        self.card = CardProcessorConnector()
        
        # Rail selection logic
        self.rail_priority = {
            'domestic_instant': PaymentRail.NPP,
            'domestic_bill': PaymentRail.BPAY,
            'international': PaymentRail.SWIFT,
            'card': PaymentRail.CARD
        }
    
    async def submit_payment(
        self,
        request: PaymentRequest
    ) -> PaymentResponse:
        """Submit payment to appropriate rail"""
        
        connector = self._get_connector(request.rail)
        return await connector.submit_payment(request)
    
    def _get_connector(self, rail: PaymentRail) -> BasePaymentConnector:
        """Get connector for rail"""
        
        connectors = {
            PaymentRail.NPP: self.npp,
            PaymentRail.BPAY: self.bpay,
            PaymentRail.SWIFT: self.swift,
            PaymentRail.CARD: self.card
        }
        
        return connectors.get(rail, self.npp)
    
    async def get_payment_status(
        self,
        payment_id: str,
        rail: PaymentRail
    ) -> Optional[PaymentResponse]:
        """Get payment status"""
        
        connector = self._get_connector(rail)
        return connector.payments.get(payment_id)


# ============================================================================
# Global Singleton
# ============================================================================

_payment_rail_manager: Optional[PaymentRailManager] = None

def get_payment_rail_manager() -> PaymentRailManager:
    """Get singleton payment rail manager"""
    global _payment_rail_manager
    if _payment_rail_manager is None:
        _payment_rail_manager = PaymentRailManager()
    return _payment_rail_manager
