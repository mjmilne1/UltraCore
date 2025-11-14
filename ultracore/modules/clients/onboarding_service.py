"""
Client Onboarding Service - End-to-End Automation
Features:
- Multi-step onboarding workflow
- AI-powered automation
- Integration with all services
- Progress tracking
- Notification system
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from ultracore.modules.clients.client_service import client_service
from ultracore.modules.clients.kyc_service import kyc_service, VerificationLevel
from ultracore.agents.client_agent import client_agent
from ultracore.datamesh.client_mesh import client_data_mesh, DataSource

class OnboardingStep(str, Enum):
    REGISTRATION = "registration"
    RISK_PROFILING = "risk_profiling"
    KYC_VERIFICATION = "kyc_verification"
    PORTFOLIO_SETUP = "portfolio_setup"
    AGREEMENT_SIGNING = "agreement_signing"
    ACCOUNT_ACTIVATION = "account_activation"
    COMPLETED = "completed"

class OnboardingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class OnboardingService:
    """
    Comprehensive onboarding service
    Orchestrates entire client onboarding journey
    """
    
    def __init__(self):
        self.onboarding_sessions = {}
        self.workflow_templates = self._load_workflow_templates()
    
    async def start_onboarding(
        self,
        email: str,
        client_type: str,
        workflow_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        Start new onboarding session
        """
        
        session_id = f"ONB-{int(datetime.now(timezone.utc).timestamp())}"
        
        session = {
            "session_id": session_id,
            "status": OnboardingStatus.IN_PROGRESS,
            "workflow_type": workflow_type,
            "current_step": OnboardingStep.REGISTRATION,
            "steps_completed": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "client_id": None,
            "kyc_id": None,
            "data": {
                "email": email,
                "client_type": client_type
            },
            "ai_insights": [],
            "notifications_sent": []
        }
        
        self.onboarding_sessions[session_id] = session
        
        # Record in Data Mesh
        client_data_mesh._record_event("ONBOARDING_STARTED", {
            "session_id": session_id,
            "email": email,
            "workflow_type": workflow_type
        })
        
        return {
            "session_id": session_id,
            "current_step": OnboardingStep.REGISTRATION,
            "message": "Onboarding started. Please complete registration.",
            "next_action": "submit_registration_data"
        }
    
    async def submit_registration(
        self,
        session_id: str,
        registration_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit registration data
        Creates client record
        """
        
        session = self.onboarding_sessions.get(session_id)
        if not session:
            return {"error": "Onboarding session not found"}
        
        # Validate current step
        if session["current_step"] != OnboardingStep.REGISTRATION:
            return {"error": f"Invalid step. Expected {OnboardingStep.REGISTRATION}"}
        
        # Create client
        client = await client_service.create_client(
            client_type=session["data"]["client_type"],
            email=session["data"]["email"],
            created_by="onboarding_system",
            **registration_data
        )
        
        # Update session
        session["client_id"] = client.id
        session["data"].update(registration_data)
        session["steps_completed"].append(OnboardingStep.REGISTRATION)
        session["current_step"] = OnboardingStep.RISK_PROFILING
        
        # Record in Data Mesh
        client_data_mesh._record_event("REGISTRATION_COMPLETED", {
            "session_id": session_id,
            "client_id": client.id
        })
        
        # Send welcome notification
        await self._send_notification(
            session_id,
            "welcome_email",
            {"client_name": registration_data.get("first_name", "Client")}
        )
        
        return {
            "session_id": session_id,
            "client_id": client.id,
            "current_step": OnboardingStep.RISK_PROFILING,
            "message": "Registration completed. Please complete risk profiling.",
            "next_action": "submit_risk_profile"
        }
    
    async def submit_risk_profile(
        self,
        session_id: str,
        risk_profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit risk profiling questionnaire
        AI analyzes and recommends risk level
        """
        
        session = self.onboarding_sessions.get(session_id)
        if not session:
            return {"error": "Onboarding session not found"}
        
        if session["current_step"] != OnboardingStep.RISK_PROFILING:
            return {"error": f"Invalid step. Expected {OnboardingStep.RISK_PROFILING}"}
        
        # Get AI risk assessment
        client = await client_service.get_client(session["client_id"])
        client_data = {**client.dict(), **risk_profile_data}
        
        risk_assessment = await client_agent.assess_client_risk(client_data)
        
        # Update client with risk profile
        await client_service.update_client(
            client_id=session["client_id"],
            updated_by="onboarding_system",
            risk_profile=risk_profile_data.get("risk_profile", "moderate"),
            investment_experience=risk_profile_data.get("investment_experience", "none"),
            annual_income=risk_profile_data.get("annual_income"),
            net_worth=risk_profile_data.get("net_worth")
        )
        
        # Update session
        session["data"]["risk_profile"] = risk_profile_data
        session["ai_insights"].append(risk_assessment)
        session["steps_completed"].append(OnboardingStep.RISK_PROFILING)
        session["current_step"] = OnboardingStep.KYC_VERIFICATION
        
        # Record in Data Mesh
        client_data_mesh._record_event("RISK_PROFILING_COMPLETED", {
            "session_id": session_id,
            "client_id": session["client_id"],
            "risk_level": risk_assessment["risk_level"]
        })
        
        return {
            "session_id": session_id,
            "risk_assessment": risk_assessment,
            "current_step": OnboardingStep.KYC_VERIFICATION,
            "message": "Risk profiling completed. Please start KYC verification.",
            "next_action": "start_kyc"
        }
    
    async def start_kyc_verification(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Start KYC verification process
        """
        
        session = self.onboarding_sessions.get(session_id)
        if not session:
            return {"error": "Onboarding session not found"}
        
        if session["current_step"] != OnboardingStep.KYC_VERIFICATION:
            return {"error": f"Invalid step. Expected {OnboardingStep.KYC_VERIFICATION}"}
        
        # Determine verification level based on risk
        risk_level = session["ai_insights"][-1]["risk_level"] if session["ai_insights"] else "medium"
        
        if risk_level == "high":
            verification_level = VerificationLevel.ENHANCED
        elif risk_level == "low":
            verification_level = VerificationLevel.BASIC
        else:
            verification_level = VerificationLevel.STANDARD
        
        # Initiate KYC
        kyc_result = await kyc_service.initiate_kyc(
            client_id=session["client_id"],
            verification_level=verification_level
        )
        
        session["kyc_id"] = kyc_result["kyc_id"]
        
        return {
            "session_id": session_id,
            "kyc_id": kyc_result["kyc_id"],
            "verification_level": verification_level,
            "required_documents": kyc_result["required_documents"],
            "message": "KYC verification initiated. Please submit required documents.",
            "next_action": "submit_kyc_documents"
        }
    
    async def complete_kyc_step(
        self,
        session_id: str,
        kyc_approved: bool
    ) -> Dict[str, Any]:
        """
        Complete KYC verification step
        """
        
        session = self.onboarding_sessions.get(session_id)
        if not session:
            return {"error": "Onboarding session not found"}
        
        if not kyc_approved:
            session["status"] = OnboardingStatus.PAUSED
            await self._send_notification(
                session_id,
                "kyc_additional_info_required",
                {}
            )
            return {
                "session_id": session_id,
                "message": "Additional information required for KYC verification."
            }
        
        # Mark KYC step complete
        session["steps_completed"].append(OnboardingStep.KYC_VERIFICATION)
        session["current_step"] = OnboardingStep.PORTFOLIO_SETUP
        
        # Record in Data Mesh
        client_data_mesh._record_event("KYC_STEP_COMPLETED", {
            "session_id": session_id,
            "client_id": session["client_id"]
        })
        
        return {
            "session_id": session_id,
            "current_step": OnboardingStep.PORTFOLIO_SETUP,
            "message": "KYC verification completed. Let's set up your portfolio.",
            "next_action": "setup_portfolio"
        }
    
    async def setup_portfolio(
        self,
        session_id: str,
        initial_investment: float,
        accept_recommendation: bool = True
    ) -> Dict[str, Any]:
        """
        Setup initial portfolio
        AI recommends allocation based on risk profile
        """
        
        session = self.onboarding_sessions.get(session_id)
        if not session:
            return {"error": "Onboarding session not found"}
        
        if session["current_step"] != OnboardingStep.PORTFOLIO_SETUP:
            return {"error": f"Invalid step. Expected {OnboardingStep.PORTFOLIO_SETUP}"}
        
        # Get AI portfolio recommendation
        client = await client_service.get_client(session["client_id"])
        
        portfolio_recommendation = await client_agent.recommend_portfolio(
            {**client.dict(), "investment_amount": initial_investment},
            client.risk_profile
        )
        
        # Store recommendation
        session["data"]["portfolio"] = {
            "initial_investment": initial_investment,
            "recommendation": portfolio_recommendation,
            "accepted": accept_recommendation
        }
        
        session["steps_completed"].append(OnboardingStep.PORTFOLIO_SETUP)
        session["current_step"] = OnboardingStep.AGREEMENT_SIGNING
        
        # Record in Data Mesh
        client_data_mesh._record_event("PORTFOLIO_SETUP_COMPLETED", {
            "session_id": session_id,
            "client_id": session["client_id"],
            "initial_investment": initial_investment
        })
        
        return {
            "session_id": session_id,
            "portfolio_recommendation": portfolio_recommendation,
            "current_step": OnboardingStep.AGREEMENT_SIGNING,
            "message": "Portfolio setup completed. Please review and sign agreements.",
            "next_action": "sign_agreements"
        }
    
    async def sign_agreements(
        self,
        session_id: str,
        agreements_signed: List[str],
        signature_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sign client agreements
        """
        
        session = self.onboarding_sessions.get(session_id)
        if not session:
            return {"error": "Onboarding session not found"}
        
        if session["current_step"] != OnboardingStep.AGREEMENT_SIGNING:
            return {"error": f"Invalid step. Expected {OnboardingStep.AGREEMENT_SIGNING}"}
        
        # Store agreements
        session["data"]["agreements"] = {
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "agreements": agreements_signed,
            "signature": signature_data
        }
        
        session["steps_completed"].append(OnboardingStep.AGREEMENT_SIGNING)
        session["current_step"] = OnboardingStep.ACCOUNT_ACTIVATION
        
        # Record in Data Mesh
        client_data_mesh._record_event("AGREEMENTS_SIGNED", {
            "session_id": session_id,
            "client_id": session["client_id"],
            "agreements": agreements_signed
        })
        
        return {
            "session_id": session_id,
            "current_step": OnboardingStep.ACCOUNT_ACTIVATION,
            "message": "Agreements signed. Activating your account...",
            "next_action": "activate_account"
        }
    
    async def activate_account(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Final step: Activate client account
        """
        
        session = self.onboarding_sessions.get(session_id)
        if not session:
            return {"error": "Onboarding session not found"}
        
        # Activate client account
        await client_service.update_client(
            client_id=session["client_id"],
            updated_by="onboarding_system",
            status="active"
        )
        
        # Complete onboarding
        session["status"] = OnboardingStatus.COMPLETED
        session["current_step"] = OnboardingStep.COMPLETED
        session["completed_at"] = datetime.now(timezone.utc).isoformat()
        session["steps_completed"].append(OnboardingStep.ACCOUNT_ACTIVATION)
        
        # Record in Data Mesh
        client_data_mesh._record_event("ONBOARDING_COMPLETED", {
            "session_id": session_id,
            "client_id": session["client_id"],
            "duration": self._calculate_duration(session)
        })
        
        # Send welcome notification
        await self._send_notification(
            session_id,
            "account_activated",
            {"client_id": session["client_id"]}
        )
        
        return {
            "session_id": session_id,
            "client_id": session["client_id"],
            "status": OnboardingStatus.COMPLETED,
            "message": "Congratulations! Your account is now active.",
            "next_action": "login_to_portal"
        }
    
    async def get_onboarding_progress(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get current onboarding progress
        """
        
        session = self.onboarding_sessions.get(session_id)
        if not session:
            return {"error": "Onboarding session not found"}
        
        all_steps = [
            OnboardingStep.REGISTRATION,
            OnboardingStep.RISK_PROFILING,
            OnboardingStep.KYC_VERIFICATION,
            OnboardingStep.PORTFOLIO_SETUP,
            OnboardingStep.AGREEMENT_SIGNING,
            OnboardingStep.ACCOUNT_ACTIVATION
        ]
        
        progress_percentage = (len(session["steps_completed"]) / len(all_steps)) * 100
        
        return {
            "session_id": session_id,
            "status": session["status"],
            "current_step": session["current_step"],
            "steps_completed": session["steps_completed"],
            "progress_percentage": round(progress_percentage, 1),
            "client_id": session.get("client_id"),
            "kyc_id": session.get("kyc_id"),
            "estimated_time_remaining": self._estimate_time_remaining(session)
        }
    
    async def abandon_onboarding(
        self,
        session_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Mark onboarding as abandoned
        """
        
        session = self.onboarding_sessions.get(session_id)
        if not session:
            return {"error": "Onboarding session not found"}
        
        session["status"] = OnboardingStatus.ABANDONED
        session["data"]["abandonment_reason"] = reason
        session["data"]["abandoned_at"] = datetime.now(timezone.utc).isoformat()
        
        # Record in Data Mesh
        client_data_mesh._record_event("ONBOARDING_ABANDONED", {
            "session_id": session_id,
            "reason": reason,
            "step": session["current_step"]
        })
        
        return {
            "session_id": session_id,
            "status": OnboardingStatus.ABANDONED,
            "message": "Onboarding session abandoned. You can resume anytime."
        }
    
    # Helper methods
    
    async def _send_notification(
        self,
        session_id: str,
        notification_type: str,
        data: Dict[str, Any]
    ):
        """Send notification to client"""
        
        session = self.onboarding_sessions.get(session_id)
        if not session:
            return
        
        notification = {
            "type": notification_type,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        
        session["notifications_sent"].append(notification)
        
        # In production, actually send email/SMS
        print(f"📧 Notification sent: {notification_type}")
    
    def _calculate_duration(self, session: Dict[str, Any]) -> str:
        """Calculate onboarding duration"""
        
        if not session.get("completed_at"):
            return "N/A"
        
        start = datetime.fromisoformat(session["started_at"])
        end = datetime.fromisoformat(session["completed_at"])
        duration = end - start
        
        days = duration.days
        hours = duration.seconds // 3600
        
        if days > 0:
            return f"{days} days, {hours} hours"
        else:
            return f"{hours} hours"
    
    def _estimate_time_remaining(self, session: Dict[str, Any]) -> str:
        """Estimate time remaining"""
        
        total_steps = 6
        completed_steps = len(session["steps_completed"])
        remaining_steps = total_steps - completed_steps
        
        # Assume 15 minutes per step
        minutes = remaining_steps * 15
        
        if minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            return f"{hours} hour{'s' if hours > 1 else ''}"
    
    def _load_workflow_templates(self) -> Dict[str, Any]:
        """Load onboarding workflow templates"""
        return {
            "standard": {
                "steps": ["registration", "risk_profiling", "kyc", "portfolio", "agreements", "activation"],
                "estimated_duration": "2-3 days"
            },
            "express": {
                "steps": ["registration", "risk_profiling", "portfolio", "activation"],
                "estimated_duration": "1 hour"
            }
        }

# Global instance
onboarding_service = OnboardingService()
