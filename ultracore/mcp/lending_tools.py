"""
MCP Tools for Lending Module
Enables AI agents to interact with lending system
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal


class LendingMCPTools:
    """
    Model Context Protocol (MCP) tools for lending
    
    Enables AI agents to:
    - Create and manage loan applications
    - Assess creditworthiness
    - Manage loan accounts
    - Process repayments
    - Manage collateral
    """
    
    def __init__(self, product_service, application_service, account_service, 
                 credit_engine, affordability_engine, collateral_service):
        self.product_service = product_service
        self.application_service = application_service
        self.account_service = account_service
        self.credit_engine = credit_engine
        self.affordability_engine = affordability_engine
        self.collateral_service = collateral_service
        
    # ========================================================================
    # LOAN PRODUCTS
    # ========================================================================
    
    def list_loan_products(
        self,
        product_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available loan products
        
        Args:
            product_type: Filter by product type (optional)
            
        Returns:
            List of active loan products
        """
        from ..modules.lending.products.models import LoanProductType
        
        type_filter = LoanProductType(product_type) if product_type else None
        products = self.product_service.list_active_products(type_filter)
        
        return {
            "success": True,
            "count": len(products),
            "products": [
                {
                    "product_id": p.product_id,
                    "product_code": p.product_code,
                    "product_name": p.product_name,
                    "product_type": p.product_type.value,
                    "min_amount": str(p.min_loan_amount),
                    "max_amount": str(p.max_loan_amount),
                    "min_term_months": p.min_term_months,
                    "max_term_months": p.max_term_months,
                    "base_rate": str(p.base_interest_rate),
                    "rate_type": p.rate_type.value
                }
                for p in products
            ]
        }
        
    def get_loan_product(
        self,
        product_id: str
    ) -> Dict[str, Any]:
        """
        Get loan product details
        
        Args:
            product_id: Product ID
            
        Returns:
            Product details
        """
        product = self.product_service.get_product(product_id)
        
        if not product:
            return {
                "success": False,
                "message": f"Product {product_id} not found"
            }
        
        return {
            "success": True,
            "product": {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "description": product.description,
                "min_amount": str(product.min_loan_amount),
                "max_amount": str(product.max_loan_amount),
                "term_range": f"{product.min_term_months}-{product.max_term_months} months",
                "base_rate": str(product.base_interest_rate),
                "features": {
                    "extra_repayments": product.allows_extra_repayments,
                    "redraw": product.allows_redraw,
                    "offset_account": product.allows_offset_account
                }
            }
        }
        
    def calculate_repayment_estimate(
        self,
        product_id: str,
        loan_amount: float,
        term_months: int,
        repayment_frequency: str = "monthly"
    ) -> Dict[str, Any]:
        """
        Calculate estimated loan repayments
        
        Args:
            product_id: Product ID
            loan_amount: Loan amount
            term_months: Loan term in months
            repayment_frequency: Repayment frequency
            
        Returns:
            Repayment estimate
        """
        from ..modules.lending.schedules.amortization_engine import AmortizationEngine
        
        product = self.product_service.get_product(product_id)
        if not product:
            return {"success": False, "message": "Product not found"}
        
        engine = AmortizationEngine()
        repayment = engine.calculate_repayment_amount(
            Decimal(str(loan_amount)),
            product.base_interest_rate,
            term_months,
            repayment_frequency
        )
        
        total_repayable = repayment * Decimal(str(engine._calculate_total_periods(term_months, repayment_frequency)))
        total_interest = total_repayable - Decimal(str(loan_amount))
        
        return {
            "success": True,
            "loan_amount": loan_amount,
            "term_months": term_months,
            "interest_rate": str(product.base_interest_rate),
            "repayment_frequency": repayment_frequency,
            "repayment_amount": str(repayment),
            "total_repayable": str(total_repayable),
            "total_interest": str(total_interest)
        }
        
    # ========================================================================
    # LOAN APPLICATIONS
    # ========================================================================
    
    def create_loan_application(
        self,
        product_id: str,
        requested_amount: float,
        term_months: int,
        loan_purpose: str,
        applicant_first_name: str,
        applicant_last_name: str,
        applicant_email: str,
        applicant_mobile: str,
        annual_income: float
    ) -> Dict[str, Any]:
        """
        Create a new loan application
        
        Args:
            product_id: Product ID
            requested_amount: Requested loan amount
            term_months: Requested term
            loan_purpose: Purpose of loan
            applicant_first_name: Applicant first name
            applicant_last_name: Applicant last name
            applicant_email: Applicant email
            applicant_mobile: Applicant mobile
            annual_income: Annual income
            
        Returns:
            Created application
        """
        # This would call the actual application service
        application_id = f"APP-{datetime.now(timezone.utc).timestamp()}"
        
        return {
            "success": True,
            "application_id": application_id,
            "status": "draft",
            "message": "Application created successfully. Please complete assessment."
        }
        
    def assess_creditworthiness(
        self,
        application_id: str,
        credit_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess creditworthiness using AI
        
        Args:
            application_id: Application ID
            credit_history: Credit history data
            
        Returns:
            Credit assessment
        """
        # Calculate credit score
        score_result = self.credit_engine.calculate_credit_score(credit_history)
        
        return {
            "success": True,
            "application_id": application_id,
            "credit_score": score_result["credit_score"],
            "risk_band": score_result["risk_band"],
            "factors": score_result["contributing_factors"]
        }
        
    def assess_affordability(
        self,
        application_id: str,
        applicant_income: float,
        applicant_expenses: float,
        existing_debts: float,
        loan_repayment: float
    ) -> Dict[str, Any]:
        """
        Assess loan affordability
        
        Args:
            application_id: Application ID
            applicant_income: Monthly income
            applicant_expenses: Monthly expenses
            existing_debts: Existing debt repayments
            loan_repayment: Proposed loan repayment
            
        Returns:
            Affordability assessment
        """
        applicant_data = {
            "gross_income": applicant_income * 12,
            "living_expenses": applicant_expenses,
            "existing_loan_repayments": existing_debts,
            "credit_card_limits": 0
        }
        
        loan_data = {
            "monthly_repayment": loan_repayment
        }
        
        assessment = self.affordability_engine.assess_affordability(
            applicant_data, loan_data
        )
        
        return {
            "success": True,
            "application_id": application_id,
            "can_afford": assessment["can_afford"],
            "monthly_surplus": assessment["monthly_surplus"],
            "dti_ratio": assessment["dti_ratio"],
            "risk_level": assessment["risk_level"]
        }
        
    def approve_application(
        self,
        application_id: str,
        approved_amount: float,
        interest_rate: float,
        approved_by: str
    ) -> Dict[str, Any]:
        """
        Approve loan application
        
        Args:
            application_id: Application ID
            approved_amount: Approved amount
            interest_rate: Approved interest rate
            approved_by: Approver ID
            
        Returns:
            Approval result
        """
        return {
            "success": True,
            "application_id": application_id,
            "status": "approved",
            "approved_amount": approved_amount,
            "interest_rate": interest_rate,
            "message": "Application approved successfully"
        }
        
    # ========================================================================
    # LOAN ACCOUNTS
    # ========================================================================
    
    def get_loan_account(
        self,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Get loan account details
        
        Args:
            account_id: Account ID
            
        Returns:
            Account details
        """
        # This would query the actual account service
        return {
            "success": True,
            "account_id": account_id,
            "account_number": "LA-123456",
            "status": "active",
            "principal_amount": "50000.00",
            "outstanding_principal": "45000.00",
            "interest_rate": "0.0650",
            "next_repayment_date": date.today().isoformat(),
            "next_repayment_amount": "1250.00"
        }
        
    def record_repayment(
        self,
        account_id: str,
        amount: float,
        payment_date: str,
        payment_method: str
    ) -> Dict[str, Any]:
        """
        Record a loan repayment
        
        Args:
            account_id: Account ID
            amount: Payment amount
            payment_date: Payment date (YYYY-MM-DD)
            payment_method: Payment method
            
        Returns:
            Repayment record
        """
        repayment_id = f"REP-{datetime.now(timezone.utc).timestamp()}"
        
        return {
            "success": True,
            "repayment_id": repayment_id,
            "account_id": account_id,
            "amount": amount,
            "status": "completed",
            "message": "Repayment recorded successfully"
        }
        
    def get_repayment_schedule(
        self,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Get loan repayment schedule
        
        Args:
            account_id: Account ID
            
        Returns:
            Repayment schedule
        """
        return {
            "success": True,
            "account_id": account_id,
            "schedule": [
                {
                    "installment": 1,
                    "due_date": "2025-12-01",
                    "principal": "1000.00",
                    "interest": "250.00",
                    "total": "1250.00",
                    "status": "pending"
                }
            ]
        }
        
    # ========================================================================
    # COLLATERAL
    # ========================================================================
    
    def register_collateral(
        self,
        collateral_type: str,
        description: str,
        current_value: float,
        owner_name: str
    ) -> Dict[str, Any]:
        """
        Register collateral for a loan
        
        Args:
            collateral_type: Type of collateral
            description: Description
            current_value: Current value
            owner_name: Owner name
            
        Returns:
            Registered collateral
        """
        collateral_id = f"COL-{datetime.now(timezone.utc).timestamp()}"
        
        return {
            "success": True,
            "collateral_id": collateral_id,
            "collateral_type": collateral_type,
            "current_value": current_value,
            "status": "pending_valuation",
            "message": "Collateral registered successfully"
        }
        
    def link_collateral_to_loan(
        self,
        collateral_id: str,
        account_id: str,
        allocated_value: float
    ) -> Dict[str, Any]:
        """
        Link collateral to loan account
        
        Args:
            collateral_id: Collateral ID
            account_id: Loan account ID
            allocated_value: Allocated value
            
        Returns:
            Link result
        """
        return {
            "success": True,
            "collateral_id": collateral_id,
            "account_id": account_id,
            "allocated_value": allocated_value,
            "message": "Collateral linked to loan successfully"
        }


# ============================================================================
# MCP TOOL DEFINITIONS
# ============================================================================

LENDING_MCP_TOOLS = [
    {
        "name": "list_loan_products",
        "description": "List available loan products",
        "parameters": {
            "product_type": {"type": "string", "required": False}
        }
    },
    {
        "name": "get_loan_product",
        "description": "Get details of a specific loan product",
        "parameters": {
            "product_id": {"type": "string", "required": True}
        }
    },
    {
        "name": "calculate_repayment_estimate",
        "description": "Calculate estimated loan repayments",
        "parameters": {
            "product_id": {"type": "string", "required": True},
            "loan_amount": {"type": "number", "required": True},
            "term_months": {"type": "integer", "required": True},
            "repayment_frequency": {"type": "string", "required": False}
        }
    },
    {
        "name": "create_loan_application",
        "description": "Create a new loan application",
        "parameters": {
            "product_id": {"type": "string", "required": True},
            "requested_amount": {"type": "number", "required": True},
            "term_months": {"type": "integer", "required": True},
            "loan_purpose": {"type": "string", "required": True},
            "applicant_first_name": {"type": "string", "required": True},
            "applicant_last_name": {"type": "string", "required": True},
            "applicant_email": {"type": "string", "required": True},
            "applicant_mobile": {"type": "string", "required": True},
            "annual_income": {"type": "number", "required": True}
        }
    },
    {
        "name": "assess_creditworthiness",
        "description": "Assess creditworthiness using AI",
        "parameters": {
            "application_id": {"type": "string", "required": True},
            "credit_history": {"type": "object", "required": True}
        }
    },
    {
        "name": "assess_affordability",
        "description": "Assess loan affordability",
        "parameters": {
            "application_id": {"type": "string", "required": True},
            "applicant_income": {"type": "number", "required": True},
            "applicant_expenses": {"type": "number", "required": True},
            "existing_debts": {"type": "number", "required": True},
            "loan_repayment": {"type": "number", "required": True}
        }
    },
    {
        "name": "approve_application",
        "description": "Approve a loan application",
        "parameters": {
            "application_id": {"type": "string", "required": True},
            "approved_amount": {"type": "number", "required": True},
            "interest_rate": {"type": "number", "required": True},
            "approved_by": {"type": "string", "required": True}
        }
    },
    {
        "name": "get_loan_account",
        "description": "Get loan account details",
        "parameters": {
            "account_id": {"type": "string", "required": True}
        }
    },
    {
        "name": "record_repayment",
        "description": "Record a loan repayment",
        "parameters": {
            "account_id": {"type": "string", "required": True},
            "amount": {"type": "number", "required": True},
            "payment_date": {"type": "string", "required": True},
            "payment_method": {"type": "string", "required": True}
        }
    },
    {
        "name": "get_repayment_schedule",
        "description": "Get loan repayment schedule",
        "parameters": {
            "account_id": {"type": "string", "required": True}
        }
    },
    {
        "name": "register_collateral",
        "description": "Register collateral for a loan",
        "parameters": {
            "collateral_type": {"type": "string", "required": True},
            "description": {"type": "string", "required": True},
            "current_value": {"type": "number", "required": True},
            "owner_name": {"type": "string", "required": True}
        }
    },
    {
        "name": "link_collateral_to_loan",
        "description": "Link collateral to loan account",
        "parameters": {
            "collateral_id": {"type": "string", "required": True},
            "account_id": {"type": "string", "required": True},
            "allocated_value": {"type": "number", "required": True}
        }
    }
]
