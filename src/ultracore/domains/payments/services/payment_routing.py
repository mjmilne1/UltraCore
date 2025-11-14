"""
Payment Routing Service.

Routes payments to appropriate payment systems and processors.
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.payment import Payment
from ..models.enums import PaymentSystem


class PaymentRoutingService:
    """Service for routing payments to appropriate systems."""
    
    def __init__(self):
        """Initialize payment routing service."""
        self.npp_enabled = True
        self.bpay_enabled = True
        self.swift_enabled = True
        self.direct_entry_enabled = True
    
    async def determine_payment_system(
        self,
        amount: Decimal,
        currency: str,
        to_account: Optional[Dict[str, Any]] = None,
        to_payid: Optional[str] = None,
        to_biller: Optional[Dict[str, Any]] = None,
        to_international: Optional[Dict[str, Any]] = None,
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """
        Determine the best payment system for a payment.
        
        Args:
            amount: Payment amount
            currency: Currency code
            to_account: Domestic account details (BSB + account number)
            to_payid: PayID
            to_biller: BPAY biller details
            to_international: International beneficiary details
            urgency: Payment urgency (instant, normal, scheduled)
            
        Returns:
            Recommended payment system and routing details
        """
        # International payment
        if currency != "AUD" or to_international:
            if not self.swift_enabled:
                return {
                    "payment_system": None,
                    "error": "International payments not available"
                }
            return {
                "payment_system": PaymentSystem.SWIFT,
                "estimated_delivery": "1-3 business days",
                "fees": self._calculate_swift_fees(amount, currency)
            }
        
        # BPAY payment
        if to_biller:
            if not self.bpay_enabled:
                return {
                    "payment_system": None,
                    "error": "BPAY payments not available"
                }
            return {
                "payment_system": PaymentSystem.BPAY,
                "estimated_delivery": "1-2 business days",
                "fees": Decimal("0")
            }
        
        # NPP/Instant payment
        if urgency == "instant" or to_payid:
            if not self.npp_enabled:
                return {
                    "payment_system": PaymentSystem.DIRECT_ENTRY,
                    "estimated_delivery": "1-2 business days",
                    "fees": Decimal("0"),
                    "note": "NPP not available, using Direct Entry"
                }
            
            # Check NPP limits
            if amount > Decimal("1000000"):
                return {
                    "payment_system": PaymentSystem.DIRECT_ENTRY,
                    "estimated_delivery": "1-2 business days",
                    "fees": Decimal("0"),
                    "note": "Amount exceeds NPP limit, using Direct Entry"
                }
            
            return {
                "payment_system": PaymentSystem.NPP,
                "estimated_delivery": "< 60 seconds",
                "fees": Decimal("0")
            }
        
        # Default to Direct Entry for domestic payments
        if to_account:
            if not self.direct_entry_enabled:
                return {
                    "payment_system": None,
                    "error": "Direct Entry not available"
                }
            return {
                "payment_system": PaymentSystem.DIRECT_ENTRY,
                "estimated_delivery": "1-2 business days",
                "fees": Decimal("0")
            }
        
        return {
            "payment_system": None,
            "error": "Unable to determine payment system - insufficient recipient details"
        }
    
    def _calculate_swift_fees(self, amount: Decimal, currency: str) -> Decimal:
        """Calculate SWIFT payment fees."""
        # Base fee
        base_fee = Decimal("25")
        
        # Additional fee for high-value payments
        if amount > Decimal("50000"):
            base_fee += Decimal("15")
        
        # Currency conversion fee (if applicable)
        if currency != "AUD":
            base_fee += Decimal("10")
        
        return base_fee
    
    async def route_payment(self, payment: Payment) -> Dict[str, Any]:
        """
        Route a payment to the appropriate processor.
        
        Args:
            payment: Payment to route
            
        Returns:
            Routing result with processor details
        """
        if payment.payment_system == PaymentSystem.NPP:
            return await self._route_to_npp(payment)
        elif payment.payment_system == PaymentSystem.BPAY:
            return await self._route_to_bpay(payment)
        elif payment.payment_system == PaymentSystem.SWIFT:
            return await self._route_to_swift(payment)
        elif payment.payment_system == PaymentSystem.DIRECT_ENTRY:
            return await self._route_to_direct_entry(payment)
        else:
            return {
                "success": False,
                "error": f"Unsupported payment system: {payment.payment_system}"
            }
    
    async def _route_to_npp(self, payment: Payment) -> Dict[str, Any]:
        """Route payment to NPP."""
        # TODO: Integrate with NPP client
        return {
            "success": True,
            "processor": "npp",
            "endpoint": "npp.payments.com.au",
            "estimated_processing_time": "< 60 seconds"
        }
    
    async def _route_to_bpay(self, payment: Payment) -> Dict[str, Any]:
        """Route payment to BPAY."""
        # TODO: Integrate with BPAY client
        return {
            "success": True,
            "processor": "bpay",
            "endpoint": "bpay.com.au",
            "estimated_processing_time": "1-2 business days"
        }
    
    async def _route_to_swift(self, payment: Payment) -> Dict[str, Any]:
        """Route payment to SWIFT."""
        # TODO: Integrate with SWIFT client
        return {
            "success": True,
            "processor": "swift",
            "endpoint": "swift.com",
            "estimated_processing_time": "1-3 business days"
        }
    
    async def _route_to_direct_entry(self, payment: Payment) -> Dict[str, Any]:
        """Route payment to Direct Entry."""
        # TODO: Integrate with Direct Entry client
        return {
            "success": True,
            "processor": "direct_entry",
            "endpoint": "direct-entry.com.au",
            "estimated_processing_time": "1-2 business days"
        }
    
    async def get_available_systems(
        self,
        currency: str = "AUD",
        amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Get available payment systems for given criteria.
        
        Args:
            currency: Currency code
            amount: Optional payment amount
            
        Returns:
            Available payment systems with details
        """
        systems = []
        
        if currency == "AUD":
            if self.npp_enabled:
                systems.append({
                    "system": PaymentSystem.NPP,
                    "name": "New Payments Platform",
                    "speed": "Instant (< 60s)",
                    "limit": Decimal("1000000"),
                    "fees": Decimal("0"),
                    "available": amount is None or amount <= Decimal("1000000")
                })
            
            if self.direct_entry_enabled:
                systems.append({
                    "system": PaymentSystem.DIRECT_ENTRY,
                    "name": "Direct Entry",
                    "speed": "1-2 business days",
                    "limit": None,
                    "fees": Decimal("0"),
                    "available": True
                })
            
            if self.bpay_enabled:
                systems.append({
                    "system": PaymentSystem.BPAY,
                    "name": "BPAY",
                    "speed": "1-2 business days",
                    "limit": None,
                    "fees": Decimal("0"),
                    "available": True
                })
        
        if self.swift_enabled:
            systems.append({
                "system": PaymentSystem.SWIFT,
                "name": "SWIFT International",
                "speed": "1-3 business days",
                "limit": None,
                "fees": self._calculate_swift_fees(amount or Decimal("0"), currency),
                "available": True
            })
        
        return {
            "available_systems": systems,
            "count": len(systems)
        }
