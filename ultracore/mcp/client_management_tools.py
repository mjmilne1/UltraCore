"""
MCP Tools for Client Management
Tools for AI agents to perform client management operations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from ultracore.client_management.aggregates import (
    ClientProfileAggregate,
    DocumentAggregate,
    RiskProfileAggregate,
    InvestmentGoalAggregate,
    BeneficiaryAggregate,
    FamilyPortfolioAggregate
)
from ultracore.agentic_ai.agents.client_management import (
    KYCVerificationAgent,
    RiskAssessmentAgent
)
from ultracore.ml.client_management import (
    RiskScoringModel,
    FinancialHealthModel
)


class ClientManagementTools:
    """MCP tools for client management operations"""
    
    def __init__(self):
        self.kyc_agent = KYCVerificationAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.risk_model = RiskScoringModel()
        self.health_model = FinancialHealthModel()
    
    # ========================================================================
    # CLIENT PROFILE TOOLS
    # ========================================================================
    
    def create_client_profile(
        self,
        user_id: str,
        tenant_id: str,
        full_name: str,
        email: str,
        phone: str,
        date_of_birth: str,
        address: str,
        **optional_fields
    ) -> Dict[str, Any]:
        """Create new client profile"""
        
        client_id = str(uuid4())
        client = ClientProfileAggregate(client_id, tenant_id)
        
        client.create_profile(
            user_id=user_id,
            full_name=full_name,
            email=email,
            phone=phone,
            date_of_birth=datetime.fromisoformat(date_of_birth),
            address=address,
            **optional_fields
        )
        
        success = client.commit()
        
        return {
            "client_id": client_id,
            "success": success,
            "profile_created": True
        }
    
    def update_client_profile(
        self,
        client_id: str,
        tenant_id: str,
        user_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update client profile"""
        
        client = ClientProfileAggregate(client_id, tenant_id)
        client.update_profile(user_id=user_id, **updates)
        success = client.commit()
        
        return {
            "client_id": client_id,
            "success": success,
            "updated_fields": list(updates.keys())
        }
    
    def calculate_financial_health(
        self,
        client_id: str,
        tenant_id: str,
        user_id: str,
        client_data: Dict[str, Any],
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate financial health score using ML"""
        
        # Predict financial health
        health_result = self.health_model.predict_financial_health(
            client_data=client_data,
            financial_data=financial_data
        )
        
        # Record in aggregate
        client = ClientProfileAggregate(client_id, tenant_id)
        client.score_financial_health(
            user_id=user_id,
            score=health_result["financial_health_score"],
            factors=health_result["component_scores"]
        )
        client.commit()
        
        return health_result
    
    # ========================================================================
    # DOCUMENT & KYC TOOLS
    # ========================================================================
    
    def upload_document(
        self,
        user_id: str,
        tenant_id: str,
        client_id: str,
        document_type: str,
        document_url: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        expiry_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload KYC document"""
        
        document_id = str(uuid4())
        document = DocumentAggregate(document_id, tenant_id)
        
        document.upload(
            user_id=user_id,
            client_id=client_id,
            document_type=document_type,
            document_url=document_url,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            expiry_date=datetime.fromisoformat(expiry_date) if expiry_date else None
        )
        
        success = document.commit()
        
        return {
            "document_id": document_id,
            "success": success,
            "verification_status": "pending"
        }
    
    def verify_document(
        self,
        document_id: str,
        tenant_id: str,
        user_id: str,
        document_type: str,
        document_url: str,
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify document using AI agent"""
        
        # AI verification
        verification_result = self.kyc_agent.verify_document(
            document_id=document_id,
            document_type=document_type,
            document_url=document_url,
            client_data=client_data
        )
        
        # Update aggregate
        document = DocumentAggregate(document_id, tenant_id)
        
        if verification_result["verification_status"] == "verified":
            document.verify(user_id=user_id, verification_method="ai_automated")
        elif verification_result["verification_status"] == "rejected":
            document.reject(
                user_id=user_id,
                rejection_reason=verification_result.get("rejection_reason", "Failed verification")
            )
        
        document.commit()
        
        return verification_result
    
    def assess_kyc_completeness(
        self,
        client_id: str,
        tenant_id: str,
        documents: List[Dict[str, Any]],
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess KYC completeness"""
        
        return self.kyc_agent.assess_kyc_completeness(
            client_id=client_id,
            documents=documents,
            client_data=client_data
        )
    
    # ========================================================================
    # RISK PROFILE TOOLS
    # ========================================================================
    
    def complete_risk_questionnaire(
        self,
        user_id: str,
        tenant_id: str,
        client_id: str,
        questionnaire_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Complete risk questionnaire"""
        
        profile_id = str(uuid4())
        risk_profile = RiskProfileAggregate(profile_id, tenant_id)
        
        risk_profile.complete_questionnaire(
            user_id=user_id,
            client_id=client_id,
            responses=questionnaire_responses
        )
        
        risk_profile.commit()
        
        return {
            "profile_id": profile_id,
            "success": True,
            "questionnaire_completed": True
        }
    
    def calculate_risk_score(
        self,
        profile_id: str,
        tenant_id: str,
        user_id: str,
        client_data: Dict[str, Any],
        questionnaire_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate risk score using ML"""
        
        # ML prediction
        risk_result = self.risk_model.predict_risk_score(
            client_data=client_data,
            questionnaire_responses=questionnaire_responses
        )
        
        # AI analysis
        analysis = self.risk_agent.analyze_questionnaire(
            client_id=client_data.get("client_id"),
            questionnaire_responses=questionnaire_responses
        )
        
        # Update aggregate
        risk_profile = RiskProfileAggregate(profile_id, tenant_id)
        risk_profile.calculate_score(
            user_id=user_id,
            score=risk_result["predicted_score"],
            risk_category=risk_result["risk_category"],
            risk_factors=risk_result["features_used"]
        )
        risk_profile.commit()
        
        return {
            **risk_result,
            "analysis": analysis
        }
    
    def assess_investment_suitability(
        self,
        client_id: str,
        risk_profile: Dict[str, Any],
        proposed_investment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess investment suitability"""
        
        return self.risk_agent.assess_suitability(
            client_id=client_id,
            risk_profile=risk_profile,
            proposed_investment=proposed_investment
        )
    
    def recommend_portfolio_allocation(
        self,
        client_id: str,
        risk_profile: Dict[str, Any],
        investment_goals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Recommend portfolio allocation"""
        
        return self.risk_agent.recommend_portfolio_allocation(
            client_id=client_id,
            risk_profile=risk_profile,
            investment_goals=investment_goals
        )
    
    # ========================================================================
    # INVESTMENT GOAL TOOLS
    # ========================================================================
    
    def create_investment_goal(
        self,
        user_id: str,
        tenant_id: str,
        client_id: str,
        goal_type: str,
        goal_name: str,
        target_amount: float,
        target_date: str,
        monthly_contribution: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create investment goal"""
        
        goal_id = str(uuid4())
        goal = InvestmentGoalAggregate(goal_id, tenant_id)
        
        goal.create_goal(
            user_id=user_id,
            client_id=client_id,
            goal_type=goal_type,
            goal_name=goal_name,
            target_amount=target_amount,
            target_date=datetime.fromisoformat(target_date),
            monthly_contribution=monthly_contribution
        )
        
        success = goal.commit()
        
        return {
            "goal_id": goal_id,
            "success": success,
            "goal_created": True
        }
    
    def update_goal_progress(
        self,
        goal_id: str,
        tenant_id: str,
        user_id: str,
        current_amount: float
    ) -> Dict[str, Any]:
        """Update investment goal progress"""
        
        goal = InvestmentGoalAggregate(goal_id, tenant_id)
        goal.update_progress(user_id=user_id, current_amount=current_amount)
        success = goal.commit()
        
        return {
            "goal_id": goal_id,
            "success": success,
            "current_amount": current_amount
        }
    
    # ========================================================================
    # BENEFICIARY TOOLS
    # ========================================================================
    
    def add_beneficiary(
        self,
        user_id: str,
        tenant_id: str,
        client_id: str,
        account_id: str,
        full_name: str,
        relationship: str,
        percentage: float,
        **contact_info
    ) -> Dict[str, Any]:
        """Add beneficiary to account"""
        
        beneficiary_id = str(uuid4())
        beneficiary = BeneficiaryAggregate(beneficiary_id, tenant_id)
        
        beneficiary.add_beneficiary(
            user_id=user_id,
            client_id=client_id,
            account_id=account_id,
            full_name=full_name,
            relationship=relationship,
            percentage=percentage,
            **contact_info
        )
        
        success = beneficiary.commit()
        
        return {
            "beneficiary_id": beneficiary_id,
            "success": success,
            "beneficiary_added": True
        }
    
    # ========================================================================
    # FAMILY PORTFOLIO TOOLS
    # ========================================================================
    
    def create_family_portfolio(
        self,
        user_id: str,
        tenant_id: str,
        portfolio_name: str,
        primary_client_id: str
    ) -> Dict[str, Any]:
        """Create family portfolio"""
        
        portfolio_id = str(uuid4())
        portfolio = FamilyPortfolioAggregate(portfolio_id, tenant_id)
        
        portfolio.create_portfolio(
            user_id=user_id,
            portfolio_name=portfolio_name,
            primary_client_id=primary_client_id
        )
        
        success = portfolio.commit()
        
        return {
            "portfolio_id": portfolio_id,
            "success": success,
            "portfolio_created": True
        }
    
    def add_family_member(
        self,
        portfolio_id: str,
        tenant_id: str,
        user_id: str,
        client_id: str,
        relationship: str,
        access_level: str = "view"
    ) -> Dict[str, Any]:
        """Add family member to portfolio"""
        
        portfolio = FamilyPortfolioAggregate(portfolio_id, tenant_id)
        portfolio.add_family_member(
            user_id=user_id,
            client_id=client_id,
            relationship=relationship,
            access_level=access_level
        )
        success = portfolio.commit()
        
        return {
            "portfolio_id": portfolio_id,
            "success": success,
            "member_added": True
        }


def get_client_management_tools() -> ClientManagementTools:
    """Get client management tools instance"""
    return ClientManagementTools()
