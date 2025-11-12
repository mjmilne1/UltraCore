"""Customer Onboarding Workflow"""
from ultracore.workflows.base import Workflow
from .kyc import KYCService


class OnboardingWorkflow(Workflow):
    """
    Complete customer onboarding workflow.
    
    Steps:
    1. Collect customer information
    2. KYC/AML verification
    3. Account creation
    4. HIN allocation
    5. Bank account linking
    """
    
    def __init__(self, kyc_service: KYCService):
        super().__init__(workflow_name="openmarkets_onboarding")
        self.kyc_service = kyc_service
    
    async def execute(self, customer_data: dict) -> dict:
        """Execute onboarding workflow."""
        # Step 1: KYC verification
        kyc_response = await self.kyc_service.verify_customer(customer_data)
        
        if kyc_response.status == "approved":
            return {
                "success": True,
                "account_id": kyc_response.account_id,
                "hin": kyc_response.hin,
                "status": "active"
            }
        
        return {
            "success": False,
            "status": kyc_response.status,
            "reason": kyc_response.rejection_reason
        }
