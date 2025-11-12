"""KYC/AML Service Integration"""
from ..client import OpenMarketsClient
from ..models import KYCRequest, KYCResponse
from ultracore.kyc.base import KYCService as BaseKYCService


class KYCService(BaseKYCService):
    """
    KYC/AML verification service integrated with OpenMarkets.
    
    Features:
    - Identity verification
    - AML screening
    - Document verification
    - Risk assessment
    """
    
    def __init__(self, client: OpenMarketsClient):
        super().__init__(service_name="openmarkets_kyc")
        self.client = client
    
    async def verify_customer(self, kyc_request: KYCRequest) -> KYCResponse:
        """Submit KYC verification request."""
        return await self.client.submit_kyc(kyc_request)
    
    async def check_status(self, verification_id: str) -> KYCResponse:
        """Check KYC verification status."""
        return await self.client.get_kyc_status(verification_id)
