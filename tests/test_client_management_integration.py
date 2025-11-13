"""
Integration Tests for Client Management System
Tests event sourcing, AI agents, ML models, and MCP tools
"""

import unittest
from datetime import datetime, timedelta
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
from ultracore.mcp.client_management_tools import ClientManagementTools
from ultracore.datamesh.client_management_mesh import get_client_management_data_product


class TestClientManagementIntegration(unittest.TestCase):
    """Integration tests for client management system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tenant_id = "test_tenant"
        self.user_id = "test_user"
        self.client_id = str(uuid4())
        self.tools = ClientManagementTools()
    
    # ========================================================================
    # EVENT SOURCING TESTS
    # ========================================================================
    
    def test_client_profile_event_sourcing(self):
        """Test client profile aggregate event sourcing"""
        client = ClientProfileAggregate(self.client_id, self.tenant_id)
        
        # Create profile
        client.create_profile(
            user_id=self.user_id,
            full_name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            date_of_birth=datetime(1990, 1, 1),
            address="123 Main St"
        )
        
        # Verify state
        self.assertEqual(client.full_name, "John Doe")
        self.assertEqual(client.email, "john@example.com")
        self.assertTrue(len(client.uncommitted_events) > 0)
        
        # Update profile
        client.update_profile(
            user_id=self.user_id,
            annual_income=100000,
            net_worth=500000
        )
        
        self.assertEqual(client.annual_income, 100000)
        self.assertEqual(client.net_worth, 500000)
    
    def test_document_verification_workflow(self):
        """Test document upload and verification workflow"""
        document_id = str(uuid4())
        document = DocumentAggregate(document_id, self.tenant_id)
        
        # Upload document
        document.upload(
            user_id=self.user_id,
            client_id=self.client_id,
            document_type="passport",
            document_url="https://example.com/passport.pdf",
            file_name="passport.pdf",
            file_size=1024000,
            mime_type="application/pdf"
        )
        
        self.assertEqual(document.verification_status, "pending")
        
        # Verify document
        document.verify(
            user_id=self.user_id,
            verification_method="ai_automated"
        )
        
        self.assertEqual(document.verification_status, "verified")
        self.assertIsNotNone(document.verified_at)
    
    def test_risk_profile_calculation(self):
        """Test risk profile questionnaire and score calculation"""
        profile_id = str(uuid4())
        risk_profile = RiskProfileAggregate(profile_id, self.tenant_id)
        
        questionnaire_responses = {
            "investment_objective": "growth",
            "time_horizon_years": 15,
            "risk_tolerance": "moderate",
            "annual_income": 100000,
            "net_worth": 500000,
            "investment_experience": "intermediate",
            "loss_tolerance_percentage": 20
        }
        
        # Complete questionnaire
        risk_profile.complete_questionnaire(
            user_id=self.user_id,
            client_id=self.client_id,
            responses=questionnaire_responses
        )
        
        self.assertEqual(risk_profile.questionnaire_responses, questionnaire_responses)
        
        # Calculate score
        risk_profile.calculate_score(
            user_id=self.user_id,
            score=65.5,
            risk_category="balanced",
            risk_factors={"time_horizon": 0.7, "financial_capacity": 0.6}
        )
        
        self.assertEqual(risk_profile.calculated_score, 65.5)
        self.assertEqual(risk_profile.risk_category, "balanced")
    
    def test_investment_goal_tracking(self):
        """Test investment goal creation and progress tracking"""
        goal_id = str(uuid4())
        goal = InvestmentGoalAggregate(goal_id, self.tenant_id)
        
        # Create goal
        goal.create_goal(
            user_id=self.user_id,
            client_id=self.client_id,
            goal_type="retirement",
            goal_name="Retirement Fund",
            target_amount=1000000,
            target_date=datetime.now() + timedelta(days=365*20),
            monthly_contribution=2000
        )
        
        self.assertEqual(goal.goal_type, "retirement")
        self.assertEqual(goal.target_amount, 1000000)
        
        # Update progress
        goal.update_progress(
            user_id=self.user_id,
            current_amount=150000
        )
        
        self.assertEqual(goal.current_amount, 150000)
        self.assertEqual(goal.progress_percentage, 15.0)
    
    def test_beneficiary_management(self):
        """Test beneficiary addition and updates"""
        beneficiary_id = str(uuid4())
        beneficiary = BeneficiaryAggregate(beneficiary_id, self.tenant_id)
        
        # Add beneficiary
        beneficiary.add_beneficiary(
            user_id=self.user_id,
            client_id=self.client_id,
            account_id="account_123",
            full_name="Jane Doe",
            relationship="spouse",
            percentage=50.0,
            contact_email="jane@example.com"
        )
        
        self.assertEqual(beneficiary.full_name, "Jane Doe")
        self.assertEqual(beneficiary.percentage, 50.0)
        self.assertTrue(beneficiary.is_active)
    
    def test_family_portfolio_creation(self):
        """Test family portfolio and joint account management"""
        portfolio_id = str(uuid4())
        portfolio = FamilyPortfolioAggregate(portfolio_id, self.tenant_id)
        
        # Create portfolio
        portfolio.create_portfolio(
            user_id=self.user_id,
            portfolio_name="Smith Family Portfolio",
            primary_client_id=self.client_id
        )
        
        self.assertEqual(portfolio.portfolio_name, "Smith Family Portfolio")
        
        # Add family member
        portfolio.add_family_member(
            user_id=self.user_id,
            client_id="client_456",
            relationship="spouse",
            access_level="admin"
        )
        
        self.assertEqual(len(portfolio.family_members), 1)
    
    # ========================================================================
    # AI AGENT TESTS
    # ========================================================================
    
    def test_kyc_verification_agent(self):
        """Test KYC verification AI agent"""
        agent = KYCVerificationAgent()
        
        client_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-01",
            "address": "123 Main St"
        }
        
        # Verify document
        result = agent.verify_document(
            document_id="doc_123",
            document_type="passport",
            document_url="https://example.com/passport.pdf",
            client_data=client_data
        )
        
        self.assertIn("verification_status", result)
        self.assertIn("confidence_score", result)
        self.assertIn("recommendation", result)
    
    def test_risk_assessment_agent(self):
        """Test risk assessment AI agent"""
        agent = RiskAssessmentAgent()
        
        questionnaire_responses = {
            "investment_objective": "growth",
            "time_horizon_years": 15,
            "risk_tolerance": "moderate",
            "annual_income": 100000,
            "net_worth": 500000,
            "investment_experience": "intermediate",
            "loss_tolerance_percentage": 20
        }
        
        # Analyze questionnaire
        analysis = agent.analyze_questionnaire(
            client_id=self.client_id,
            questionnaire_responses=questionnaire_responses
        )
        
        self.assertIn("risk_factors", analysis)
        
        # Calculate risk score
        client_data = {
            "date_of_birth": datetime(1990, 1, 1),
            "annual_income": 100000,
            "net_worth": 500000
        }
        
        score_result = agent.calculate_risk_score(
            client_id=self.client_id,
            questionnaire_analysis=analysis,
            client_data=client_data
        )
        
        self.assertIn("calculated_score", score_result)
        self.assertIn("risk_category", score_result)
    
    # ========================================================================
    # ML MODEL TESTS
    # ========================================================================
    
    def test_risk_scoring_model(self):
        """Test risk scoring ML model"""
        model = RiskScoringModel()
        
        client_data = {
            "date_of_birth": datetime(1990, 1, 1),
            "annual_income": 100000,
            "net_worth": 500000
        }
        
        questionnaire_responses = {
            "investment_experience": "intermediate",
            "time_horizon_years": 15,
            "loss_tolerance_percentage": 20,
            "investment_objective": "growth",
            "employment_stability_score": 8,
            "dependents_count": 2,
            "existing_investments_value": 200000
        }
        
        # Predict risk score
        prediction = model.predict_risk_score(
            client_data=client_data,
            questionnaire_responses=questionnaire_responses
        )
        
        self.assertIn("predicted_score", prediction)
        self.assertIn("risk_category", prediction)
        self.assertIn("confidence", prediction)
        self.assertGreaterEqual(prediction["predicted_score"], 0)
        self.assertLessEqual(prediction["predicted_score"], 100)
    
    def test_financial_health_model(self):
        """Test financial health scoring ML model"""
        model = FinancialHealthModel()
        
        client_data = {
            "annual_income": 100000
        }
        
        financial_data = {
            "total_debt": 50000,
            "monthly_savings": 2000,
            "emergency_fund": 30000,
            "monthly_expenses": 5000,
            "credit_limit": 20000,
            "credit_used": 5000,
            "investment_diversification_score": 70,
            "net_worth_growth_rate": 8,
            "cash_flow_stability_score": 75,
            "insurance_coverage_score": 65
        }
        
        # Predict financial health
        prediction = model.predict_financial_health(
            client_data=client_data,
            financial_data=financial_data
        )
        
        self.assertIn("financial_health_score", prediction)
        self.assertIn("health_category", prediction)
        self.assertIn("component_scores", prediction)
        self.assertIn("recommendations", prediction)
    
    # ========================================================================
    # MCP TOOLS TESTS
    # ========================================================================
    
    def test_mcp_create_client_profile(self):
        """Test MCP tool for creating client profile"""
        result = self.tools.create_client_profile(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            full_name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            date_of_birth="1990-01-01",
            address="123 Main St"
        )
        
        self.assertIn("client_id", result)
        self.assertTrue(result["profile_created"])
    
    def test_mcp_upload_and_verify_document(self):
        """Test MCP tools for document upload and verification"""
        # Upload
        upload_result = self.tools.upload_document(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            document_type="passport",
            document_url="https://example.com/passport.pdf",
            file_name="passport.pdf",
            file_size=1024000,
            mime_type="application/pdf"
        )
        
        self.assertIn("document_id", upload_result)
        
        # Verify
        verify_result = self.tools.verify_document(
            document_id=upload_result["document_id"],
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            document_type="passport",
            document_url="https://example.com/passport.pdf",
            client_data={"full_name": "John Doe"}
        )
        
        self.assertIn("verification_status", verify_result)
    
    def test_mcp_risk_assessment_workflow(self):
        """Test MCP tools for complete risk assessment workflow"""
        questionnaire_responses = {
            "investment_objective": "growth",
            "time_horizon_years": 15,
            "risk_tolerance": "moderate",
            "annual_income": 100000,
            "net_worth": 500000,
            "investment_experience": "intermediate",
            "loss_tolerance_percentage": 20,
            "employment_stability_score": 8,
            "dependents_count": 2,
            "existing_investments_value": 200000
        }
        
        # Complete questionnaire
        questionnaire_result = self.tools.complete_risk_questionnaire(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            questionnaire_responses=questionnaire_responses
        )
        
        self.assertTrue(questionnaire_result["questionnaire_completed"])
        
        # Calculate risk score
        client_data = {
            "client_id": self.client_id,
            "date_of_birth": datetime(1990, 1, 1),
            "annual_income": 100000,
            "net_worth": 500000
        }
        
        score_result = self.tools.calculate_risk_score(
            profile_id=questionnaire_result["profile_id"],
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            client_data=client_data,
            questionnaire_responses=questionnaire_responses
        )
        
        self.assertIn("predicted_score", score_result)
        self.assertIn("risk_category", score_result)
    
    # ========================================================================
    # DATA MESH TESTS
    # ========================================================================
    
    def test_data_mesh_client_profile_query(self):
        """Test data mesh client profile data product"""
        data_product = get_client_management_data_product()
        
        result = data_product.get_client_profile_data(
            tenant_id=self.tenant_id,
            client_id=self.client_id
        )
        
        self.assertEqual(result["domain"], "client_profiles")
        self.assertIn("metadata", result)
        self.assertIn("quality_score", result["metadata"])
    
    def test_data_mesh_dashboard(self):
        """Test data mesh comprehensive dashboard"""
        data_product = get_client_management_data_product()
        
        dashboard = data_product.get_client_management_dashboard(
            tenant_id=self.tenant_id
        )
        
        self.assertIn("dashboard", dashboard)
        self.assertIn("summary", dashboard)
        self.assertIn("client_profiles", dashboard["dashboard"])
        self.assertIn("documents", dashboard["dashboard"])
        self.assertIn("risk_profiles", dashboard["dashboard"])
    
    def test_data_quality_validation(self):
        """Test data product quality validation"""
        data_product = get_client_management_data_product()
        
        validation = data_product.validate_data_quality()
        
        self.assertIn("quality_checks", validation)
        self.assertIn("sla_compliance", validation)
        self.assertTrue(validation["quality_checks"]["completeness"]["passed"])


if __name__ == "__main__":
    unittest.main()
