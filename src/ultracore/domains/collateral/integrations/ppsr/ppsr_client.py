"""
PPSR API Client - Real Integration with Australian PPSR
https://www.ppsr.gov.au/

PPSR is Australia's national online register for security interests
in personal property.

API Documentation: https://api.ppsr.gov.au/
"""
import httpx
from typing import Dict, Optional, List
from datetime import datetime, date
from decimal import Decimal
import asyncio

from ultracore.integrations.base import BaseAPIClient


class PPSRClient(BaseAPIClient):
    """
    Client for Australian PPSR API.
    
    Capabilities:
    - Register security interests
    - Search for existing registrations
    - Amend registrations
    - Discharge registrations
    - Subordination agreements
    
    Authentication:
    - API Key based
    - mTLS certificates for production
    
    Rate Limits:
    - 100 requests per minute
    - 10,000 requests per day
    """
    
    def __init__(
        self,
        api_key: str,
        environment: str = "production",
        timeout: int = 30
    ):
        base_urls = {
            "production": "https://api.ppsr.gov.au/v1",
            "sandbox": "https://sandbox-api.ppsr.gov.au/v1"
        }
        
        super().__init__(
            base_url=base_urls[environment],
            api_key=api_key,
            timeout=timeout
        )
        
        self.environment = environment
    
    async def search_by_grantor(
        self,
        grantor_name: str,
        grantor_abn: Optional[str] = None,
        grantor_acn: Optional[str] = None,
        grantor_type: str = "individual"
    ) -> Dict:
        """
        Search PPSR by grantor (borrower) details.
        
        Returns all security interests registered against the grantor.
        
        Critical for due diligence before taking security!
        """
        
        search_data = {
            "searchType": "grantor",
            "grantor": {
                "name": grantor_name,
                "type": grantor_type
            }
        }
        
        if grantor_abn:
            search_data["grantor"]["abn"] = grantor_abn
        if grantor_acn:
            search_data["grantor"]["acn"] = grantor_acn
        
        response = await self._post("/searches", json=search_data)
        
        return {
            "search_id": response.get("searchId"),
            "search_date": datetime.now(timezone.utc),
            "registrations_found": len(response.get("registrations", [])),
            "registrations": response.get("registrations", []),
            "grantor_clear": len(response.get("registrations", [])) == 0
        }
    
    async def search_by_serial_number(
        self,
        serial_number: str,
        collateral_class: str = "motor_vehicle"
    ) -> Dict:
        """
        Search PPSR by serial number (VIN for vehicles).
        
        Returns all security interests against the specific asset.
        """
        
        search_data = {
            "searchType": "serialNumber",
            "serialNumber": serial_number,
            "collateralClass": collateral_class
        }
        
        response = await self._post("/searches", json=search_data)
        
        return {
            "search_id": response.get("searchId"),
            "search_date": datetime.now(timezone.utc),
            "registrations_found": len(response.get("registrations", [])),
            "registrations": response.get("registrations", []),
            "serial_number_clear": len(response.get("registrations", [])) == 0
        }
    
    async def register_security_interest(
        self,
        secured_party_name: str,
        secured_party_abn: str,
        grantor_name: str,
        grantor_identifier: str,  # ABN or individual ID
        collateral_class: str,
        collateral_description: str,
        security_agreement_date: date,
        secured_amount: Optional[Decimal] = None,
        serial_number: Optional[str] = None,
        registration_end_date: Optional[date] = None
    ) -> Dict:
        """
        Register a security interest on PPSR.
        
        Returns registration number and timestamp (establishes priority!).
        
        CRITICAL: Registration time determines priority.
        Earlier registration = superior security interest.
        """
        
        registration_data = {
            "securedParty": {
                "name": secured_party_name,
                "abn": secured_party_abn
            },
            "grantor": {
                "name": grantor_name,
                "identifier": grantor_identifier
            },
            "collateral": {
                "class": collateral_class,
                "description": collateral_description
            },
            "securityAgreementDate": security_agreement_date.isoformat()
        }
        
        if secured_amount:
            registration_data["securedAmount"] = float(secured_amount)
        
        if serial_number:
            registration_data["collateral"]["serialNumber"] = serial_number
        
        if registration_end_date:
            registration_data["registrationEndDate"] = registration_end_date.isoformat()
        
        response = await self._post("/registrations", json=registration_data)
        
        # Extract critical registration details
        return {
            "registration_number": response.get("registrationNumber"),
            "registration_time": datetime.fromisoformat(response.get("registrationTime")),
            "priority_established": True,
            "status": response.get("status"),
            "registration_confirmation": response.get("confirmationNumber")
        }
    
    async def discharge_registration(
        self,
        registration_number: str,
        discharge_reason: str = "obligations_satisfied"
    ) -> Dict:
        """
        Discharge (remove) a PPSR registration.
        
        PPSA Section 178: Must discharge within 5 business days
        of request by debtor, or face ,000 penalty!
        """
        
        discharge_data = {
            "registrationNumber": registration_number,
            "dischargeReason": discharge_reason,
            "dischargeDate": datetime.now(timezone.utc).isoformat()
        }
        
        response = await self._post(
            f"/registrations/{registration_number}/discharge",
            json=discharge_data
        )
        
        return {
            "registration_number": registration_number,
            "discharge_time": datetime.now(timezone.utc),
            "discharge_confirmation": response.get("confirmationNumber"),
            "status": "discharged"
        }
    
    async def amend_registration(
        self,
        registration_number: str,
        amendments: Dict
    ) -> Dict:
        """
        Amend an existing PPSR registration.
        
        Can update:
        - Collateral description
        - Secured amount
        - Registration end date
        
        Cannot change: Grantor, Secured Party, Security Agreement Date
        """
        
        response = await self._patch(
            f"/registrations/{registration_number}",
            json=amendments
        )
        
        return {
            "registration_number": registration_number,
            "amendment_time": datetime.now(timezone.utc),
            "amendments_applied": amendments,
            "status": response.get("status")
        }
    
    async def get_registration_details(
        self,
        registration_number: str
    ) -> Dict:
        """
        Get detailed information about a specific registration.
        """
        
        response = await self._get(f"/registrations/{registration_number}")
        
        return response
    
    async def verify_priority(
        self,
        registration_number: str
    ) -> Dict:
        """
        Verify priority position of a registration.
        
        Checks for:
        - Earlier registrations
        - Subordination agreements
        - Priority disputes
        """
        
        response = await self._get(
            f"/registrations/{registration_number}/priority"
        )
        
        return {
            "registration_number": registration_number,
            "priority_position": response.get("priorityPosition"),
            "prior_interests": response.get("priorInterests", []),
            "is_first_priority": response.get("priorityPosition") == "first"
        }
    
    # Private methods
    
    async def _post(self, endpoint: str, **kwargs) -> Dict:
        """POST request with authentication."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
    
    async def _get(self, endpoint: str, **kwargs) -> Dict:
        """GET request with authentication."""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
    
    async def _patch(self, endpoint: str, **kwargs) -> Dict:
        """PATCH request with authentication."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
