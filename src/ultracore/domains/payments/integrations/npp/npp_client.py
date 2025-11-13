"""NPP (New Payments Platform) Client - Real API Integration"""
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime
import uuid
import httpx


class NPPClient:
    """
    NPP (New Payments Platform) API Client.
    
    NPP Infrastructure:
    - Operated by: NPPA (New Payments Platform Australia)
    - Fast Settlement Service (FSS): Real-time gross settlement
    - Addressing Service: PayID resolution
    - Overlay Services: Osko (consumer), BPAY (bills), Mandated Payments
    
    API Endpoints:
    - PayID Lookup: Resolve PayID to BSB+Account
    - Payment Initiation: Submit real-time payment
    - Payment Status: Track payment
    
    Authentication: ISO 20022 messaging, mutual TLS
    """
    
    def __init__(
        self,
        api_base_url: str = "https://api.npp.com.au/v1",
        participant_id: str = None,
        api_key: str = None,
        cert_path: str = None,
        environment: str = "production"
    ):
        self.api_base_url = api_base_url
        self.participant_id = participant_id  # Bank's NPP participant ID
        self.api_key = api_key
        self.cert_path = cert_path
        self.environment = environment
        
        self.client = httpx.AsyncClient(
            base_url=api_base_url,
            headers={
                "X-Participant-ID": participant_id,
                "X-API-Key": api_key
            },
            timeout=10.0
        )
    
    async def lookup_payid(
        self,
        payid: str,
        payid_type: str = "email"
    ) -> Dict:
        """
        Lookup PayID to resolve BSB + Account Number.
        
        PayID Types:
        - email: Email address
        - mobile: Mobile number (+61...)
        - abn: Australian Business Number
        - org_id: Organisation identifier
        
        Returns:
            {
                "payid": "john@example.com",
                "account_name": "John Smith",
                "bsb": "123-456",
                "account_number": "12345678",
                "participant_id": "ABCAUS2X"
            }
        """
        
        # Mock response for development
        if self.environment == "development":
            return {
                "payid": payid,
                "payid_type": payid_type,
                "account_name": "John Smith",
                "bsb": "123-456",
                "account_number": "12345678",
                "participant_id": "ABCAUS2X",
                "status": "active"
            }
        
        # Real API call
        response = await self.client.post(
            "/addressing/lookup",
            json={
                "payid": payid,
                "payid_type": payid_type
            }
        )
        
        response.raise_for_status()
        return response.json()
    
    async def send_payment(
        self,
        to_payid: Optional[str] = None,
        to_payid_type: Optional[str] = None,
        to_bsb: Optional[str] = None,
        to_account_number: Optional[str] = None,
        amount: Decimal = None,
        description: str = "",
        reference: Optional[str] = None
    ) -> Dict:
        """
        Send NPP instant payment.
        
        Payment Flow:
        1. Resolve PayID (if provided)
        2. Submit payment to FSS (Fast Settlement Service)
        3. Real-time settlement (seconds)
        4. Return transaction confirmation
        
        Returns:
            {
                "transaction_id": "NPP-...",
                "settlement_id": "FSS-...",
                "status": "completed",
                "completed_at": "2025-01-15T10:30:45Z",
                "processing_time_ms": 2341
            }
        """
        
        # Resolve PayID if provided
        if to_payid:
            payid_info = await self.lookup_payid(to_payid, to_payid_type)
            to_bsb = payid_info["bsb"]
            to_account_number = payid_info["account_number"]
            to_account_name = payid_info["account_name"]
        
        # Generate transaction ID
        transaction_id = f"NPP-{uuid.uuid4().hex[:16].upper()}"
        
        # Mock for development
        if self.environment == "development":
            return {
                "transaction_id": transaction_id,
                "settlement_id": f"FSS-{uuid.uuid4().hex[:12].upper()}",
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "processing_time_ms": 2341,
                "recipient_bsb": to_bsb,
                "recipient_account": to_account_number
            }
        
        # Real NPP payment submission (ISO 20022 format)
        payment_payload = {
            "message_type": "pacs.008",  # Customer credit transfer
            "transaction_id": transaction_id,
            "instructing_agent": self.participant_id,
            "instructed_agent": to_bsb[:3],  # First 3 digits = bank
            "debtor": {
                "account": {
                    "identification": "source_account"  # Populated by system
                }
            },
            "creditor": {
                "name": to_account_name if to_payid else "Beneficiary",
                "account": {
                    "identification": {
                        "bsb": to_bsb,
                        "account_number": to_account_number
                    }
                }
            },
            "amount": {
                "value": str(amount),
                "currency": "AUD"
            },
            "remittance_information": {
                "unstructured": description,
                "structured": reference
            }
        }
        
        response = await self.client.post(
            "/payments/initiate",
            json=payment_payload
        )
        
        response.raise_for_status()
        return response.json()
    
    async def register_payid(
        self,
        payid: str,
        payid_type: str,
        bsb: str,
        account_number: str,
        account_name: str
    ) -> Dict:
        """
        Register PayID for account.
        
        Steps:
        1. Validate PayID availability
        2. Send verification (email/SMS)
        3. Confirm verification
        4. Activate PayID
        """
        
        if self.environment == "development":
            return {
                "payid": payid,
                "status": "pending_verification",
                "verification_code_sent": True,
                "expires_at": (datetime.now(timezone.utc)).isoformat()
            }
        
        response = await self.client.post(
            "/addressing/register",
            json={
                "payid": payid,
                "payid_type": payid_type,
                "account": {
                    "bsb": bsb,
                    "account_number": account_number,
                    "account_name": account_name
                }
            }
        )
        
        response.raise_for_status()
        return response.json()
