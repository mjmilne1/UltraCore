"""
MCP Tools for Investor Management
Enables AI agents to interact with investor management system
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal

# Simulated imports - in production these would be actual MCP SDK imports
# from mcp import Tool, ToolResult


class InvestorMCPTools:
    """
    Model Context Protocol (MCP) tools for investor management
    
    Enables AI agents (like Claude, GPT-4, etc.) to:
    - Create and manage investors
    - Initiate loan transfers
    - Match investors to loans
    - Get pricing recommendations
    - Query investor portfolios
    """
    
    def __init__(self, investor_service, transfer_service, matching_engine, pricing_engine):
        self.investor_service = investor_service
        self.transfer_service = transfer_service
        self.matching_engine = matching_engine
        self.pricing_engine = pricing_engine
        
    # Tool 1: Create Investor
    def create_investor(
        self,
        investor_name: str,
        investor_type: str,
        email: str,
        phone: Optional[str] = None,
        country: str = "AU"
    ) -> Dict[str, Any]:
        """
        Create a new investor account
        
        Args:
            investor_name: Legal name of investor
            investor_type: Type (institutional, private_equity, hedge_fund, etc.)
            email: Contact email
            phone: Contact phone (optional)
            country: Country code (default: AU)
            
        Returns:
            Created investor details
        """
        
        from ..modules.investor_management.models import CreateInvestorRequest, InvestorType
        
        request = CreateInvestorRequest(
            external_id=f"EXT-{datetime.now(timezone.utc).timestamp()}",
            investor_name=investor_name,
            investor_type=InvestorType(investor_type),
            email=email,
            phone=phone,
            country=country,
            created_by="mcp_agent"
        )
        
        investor = self.investor_service.create_investor(request)
        
        return {
            "success": True,
            "investor_id": investor.investor_id,
            "investor_name": investor.investor_name,
            "status": investor.status.value,
            "message": f"Investor {investor.investor_name} created successfully. Status: {investor.status.value}"
        }
        
    # Tool 2: Get Investor Details
    def get_investor(
        self,
        investor_id: str
    ) -> Dict[str, Any]:
        """
        Get investor details
        
        Args:
            investor_id: Investor ID
            
        Returns:
            Investor details
        """
        
        investor = self.investor_service.get_investor(investor_id)
        
        if not investor:
            return {
                "success": False,
                "message": f"Investor {investor_id} not found"
            }
        
        return {
            "success": True,
            "investor": {
                "investor_id": investor.investor_id,
                "investor_name": investor.investor_name,
                "investor_type": investor.investor_type.value,
                "status": investor.status.value,
                "email": investor.email,
                "total_investments": str(investor.total_investments),
                "active_loans": investor.active_loans,
                "total_returns": str(investor.total_returns),
                "kyc_verified": investor.kyc_verified,
                "aml_verified": investor.aml_verified
            }
        }
        
    # Tool 3: Initiate Loan Transfer
    def initiate_loan_transfer(
        self,
        loan_id: str,
        to_investor_id: str,
        transfer_type: str,
        purchase_price_ratio: float,
        settlement_date: str,
        outstanding_principal: float
    ) -> Dict[str, Any]:
        """
        Initiate a loan transfer to an investor
        
        Args:
            loan_id: Loan ID to transfer
            to_investor_id: Investor receiving the loan
            transfer_type: Type (sale, buy_back, intermediary_sale)
            purchase_price_ratio: Price as % of principal (e.g., 0.95 for 95%)
            settlement_date: Settlement date (YYYY-MM-DD)
            outstanding_principal: Current principal balance
            
        Returns:
            Transfer details
        """
        
        from ..modules.investor_management.models import InitiateLoanTransferRequest, TransferType
        
        request = InitiateLoanTransferRequest(
            loan_id=loan_id,
            to_investor_id=to_investor_id,
            transfer_type=TransferType(transfer_type),
            purchase_price_ratio=Decimal(str(purchase_price_ratio)),
            settlement_date=date.fromisoformat(settlement_date),
            effective_date_from=date.fromisoformat(settlement_date),
            created_by="mcp_agent"
        )
        
        transfer = self.transfer_service.initiate_transfer(
            request,
            outstanding_principal=Decimal(str(outstanding_principal))
        )
        
        return {
            "success": True,
            "transfer_id": transfer.transfer_id,
            "loan_id": transfer.loan_id,
            "to_investor_id": transfer.to_investor_id,
            "purchase_price": str(transfer.purchase_price),
            "status": transfer.status.value,
            "settlement_date": transfer.settlement_date.isoformat(),
            "message": f"Transfer {transfer.transfer_id} initiated successfully"
        }
        
    # Tool 4: Match Investors to Loan
    def match_investors_to_loan(
        self,
        loan_id: str,
        principal_amount: float,
        loan_type: str,
        risk_rating: str,
        interest_rate: float,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Use AI to match investors to a loan
        
        Args:
            loan_id: Loan ID
            principal_amount: Loan amount
            loan_type: Type of loan
            risk_rating: Risk rating (AAA, AA, A, BBB, BB, B, CCC)
            interest_rate: Interest rate
            top_n: Number of top matches to return
            
        Returns:
            List of matched investors with scores
        """
        
        loan_data = {
            "loan_id": loan_id,
            "principal_amount": principal_amount,
            "loan_type": loan_type,
            "risk_rating": risk_rating,
            "interest_rate": interest_rate
        }
        
        # Get active investors
        from ..modules.investor_management.models import InvestorStatus
        active_investors = self.investor_service.list_investors(status=InvestorStatus.ACTIVE)
        
        # Match
        matches = self.matching_engine.match_investors_for_loan(
            loan_data,
            active_investors,
            top_n
        )
        
        return {
            "success": True,
            "loan_id": loan_id,
            "matches": matches,
            "message": f"Found {len(matches)} investor matches"
        }
        
    # Tool 5: Get Loan Pricing Recommendation
    def get_loan_pricing_recommendation(
        self,
        loan_id: str,
        principal_amount: float,
        interest_rate: float,
        remaining_term_months: int,
        risk_rating: str,
        days_past_due: int = 0
    ) -> Dict[str, Any]:
        """
        Get AI-powered pricing recommendation for a loan
        
        Args:
            loan_id: Loan ID
            principal_amount: Loan amount
            interest_rate: Interest rate
            remaining_term_months: Remaining term
            risk_rating: Risk rating
            days_past_due: Days past due (0 if current)
            
        Returns:
            Pricing recommendation
        """
        
        loan_data = {
            "loan_id": loan_id,
            "principal_amount": principal_amount,
            "interest_rate": interest_rate,
            "remaining_term_months": remaining_term_months,
            "risk_rating": risk_rating,
            "days_past_due": days_past_due
        }
        
        recommendation = self.pricing_engine.recommend_price(loan_data)
        
        return {
            "success": True,
            "loan_id": loan_id,
            "recommendation": recommendation,
            "message": f"Recommended price ratio: {recommendation['recommended_price_ratio']:.2%}"
        }
        
    # Tool 6: Get Investor Portfolio
    def get_investor_portfolio(
        self,
        investor_id: str
    ) -> Dict[str, Any]:
        """
        Get investor's loan portfolio
        
        Args:
            investor_id: Investor ID
            
        Returns:
            Portfolio details
        """
        
        investor = self.investor_service.get_investor(investor_id)
        if not investor:
            return {
                "success": False,
                "message": f"Investor {investor_id} not found"
            }
        
        # Get all transfers for this investor
        transfers = self.transfer_service.get_transfers_for_investor(investor_id)
        
        # Filter active transfers
        active_transfers = [t for t in transfers if t.status.value == "active"]
        
        return {
            "success": True,
            "investor_id": investor_id,
            "investor_name": investor.investor_name,
            "portfolio": {
                "total_investments": str(investor.total_investments),
                "active_loans": len(active_transfers),
                "total_returns": str(investor.total_returns),
                "loans": [
                    {
                        "loan_id": t.loan_id,
                        "transfer_id": t.transfer_id,
                        "purchase_price": str(t.purchase_price),
                        "outstanding_principal": str(t.outstanding_principal),
                        "effective_date": t.effective_date_from.isoformat()
                    }
                    for t in active_transfers
                ]
            }
        }
        
    # Tool 7: Approve Transfer
    def approve_transfer(
        self,
        transfer_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a pending loan transfer
        
        Args:
            transfer_id: Transfer ID
            notes: Approval notes (optional)
            
        Returns:
            Updated transfer status
        """
        
        from ..modules.investor_management.models import ApproveTransferRequest
        
        request = ApproveTransferRequest(
            transfer_id=transfer_id,
            approved_by="mcp_agent",
            notes=notes
        )
        
        transfer = self.transfer_service.approve_transfer(request)
        
        return {
            "success": True,
            "transfer_id": transfer.transfer_id,
            "status": transfer.status.value,
            "sub_status": transfer.sub_status.value if transfer.sub_status else None,
            "message": f"Transfer {transfer_id} approved successfully"
        }
        
    # Tool 8: Get Loan Owner
    def get_loan_owner(
        self,
        loan_id: str
    ) -> Dict[str, Any]:
        """
        Get current owner of a loan
        
        Args:
            loan_id: Loan ID
            
        Returns:
            Owner details
        """
        
        owner_id = self.transfer_service.get_loan_owner(loan_id)
        
        if not owner_id:
            return {
                "success": True,
                "loan_id": loan_id,
                "owner": "ORIGINATOR",
                "message": "Loan is owned by originating institution"
            }
        
        investor = self.investor_service.get_investor(owner_id)
        
        return {
            "success": True,
            "loan_id": loan_id,
            "owner": "INVESTOR",
            "investor_id": owner_id,
            "investor_name": investor.investor_name if investor else "Unknown",
            "message": f"Loan is owned by investor {owner_id}"
        }
        
    # Tool 9: List All Investors
    def list_investors(
        self,
        status: Optional[str] = None,
        investor_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all investors with optional filters
        
        Args:
            status: Filter by status (active, inactive, suspended, etc.)
            investor_type: Filter by type (institutional, private_equity, etc.)
            
        Returns:
            List of investors
        """
        
        from ..modules.investor_management.models import InvestorStatus, InvestorType
        
        status_filter = InvestorStatus(status) if status else None
        type_filter = InvestorType(investor_type) if investor_type else None
        
        investors = self.investor_service.list_investors(
            status=status_filter,
            investor_type=type_filter
        )
        
        return {
            "success": True,
            "count": len(investors),
            "investors": [
                {
                    "investor_id": inv.investor_id,
                    "investor_name": inv.investor_name,
                    "investor_type": inv.investor_type.value,
                    "status": inv.status.value,
                    "active_loans": inv.active_loans,
                    "total_investments": str(inv.total_investments)
                }
                for inv in investors
            ]
        }
        
    # Tool 10: Get Transfer Details
    def get_transfer(
        self,
        transfer_id: str
    ) -> Dict[str, Any]:
        """
        Get transfer details
        
        Args:
            transfer_id: Transfer ID
            
        Returns:
            Transfer details
        """
        
        transfer = self.transfer_service.get_transfer(transfer_id)
        
        if not transfer:
            return {
                "success": False,
                "message": f"Transfer {transfer_id} not found"
            }
        
        return {
            "success": True,
            "transfer": {
                "transfer_id": transfer.transfer_id,
                "loan_id": transfer.loan_id,
                "transfer_type": transfer.transfer_type.value,
                "status": transfer.status.value,
                "from_investor_id": transfer.from_investor_id,
                "to_investor_id": transfer.to_investor_id,
                "outstanding_principal": str(transfer.outstanding_principal),
                "purchase_price": str(transfer.purchase_price),
                "purchase_price_ratio": str(transfer.purchase_price_ratio),
                "settlement_date": transfer.settlement_date.isoformat(),
                "effective_date_from": transfer.effective_date_from.isoformat(),
                "created_at": transfer.created_at.isoformat()
            }
        }


# MCP Tool Definitions
# These would be registered with the MCP server

MCP_TOOL_DEFINITIONS = [
    {
        "name": "create_investor",
        "description": "Create a new investor account in the system",
        "parameters": {
            "investor_name": {"type": "string", "required": True},
            "investor_type": {"type": "string", "required": True},
            "email": {"type": "string", "required": True},
            "phone": {"type": "string", "required": False},
            "country": {"type": "string", "required": False, "default": "AU"}
        }
    },
    {
        "name": "get_investor",
        "description": "Get details of an investor",
        "parameters": {
            "investor_id": {"type": "string", "required": True}
        }
    },
    {
        "name": "initiate_loan_transfer",
        "description": "Initiate a loan transfer to an investor",
        "parameters": {
            "loan_id": {"type": "string", "required": True},
            "to_investor_id": {"type": "string", "required": True},
            "transfer_type": {"type": "string", "required": True},
            "purchase_price_ratio": {"type": "number", "required": True},
            "settlement_date": {"type": "string", "required": True},
            "outstanding_principal": {"type": "number", "required": True}
        }
    },
    {
        "name": "match_investors_to_loan",
        "description": "Use AI to find the best investors for a loan",
        "parameters": {
            "loan_id": {"type": "string", "required": True},
            "principal_amount": {"type": "number", "required": True},
            "loan_type": {"type": "string", "required": True},
            "risk_rating": {"type": "string", "required": True},
            "interest_rate": {"type": "number", "required": True},
            "top_n": {"type": "integer", "required": False, "default": 5}
        }
    },
    {
        "name": "get_loan_pricing_recommendation",
        "description": "Get AI-powered pricing recommendation for selling a loan",
        "parameters": {
            "loan_id": {"type": "string", "required": True},
            "principal_amount": {"type": "number", "required": True},
            "interest_rate": {"type": "number", "required": True},
            "remaining_term_months": {"type": "integer", "required": True},
            "risk_rating": {"type": "string", "required": True},
            "days_past_due": {"type": "integer", "required": False, "default": 0}
        }
    },
    {
        "name": "get_investor_portfolio",
        "description": "Get an investor's loan portfolio",
        "parameters": {
            "investor_id": {"type": "string", "required": True}
        }
    },
    {
        "name": "approve_transfer",
        "description": "Approve a pending loan transfer",
        "parameters": {
            "transfer_id": {"type": "string", "required": True},
            "notes": {"type": "string", "required": False}
        }
    },
    {
        "name": "get_loan_owner",
        "description": "Get the current owner of a loan",
        "parameters": {
            "loan_id": {"type": "string", "required": True}
        }
    },
    {
        "name": "list_investors",
        "description": "List all investors with optional filters",
        "parameters": {
            "status": {"type": "string", "required": False},
            "investor_type": {"type": "string", "required": False}
        }
    },
    {
        "name": "get_transfer",
        "description": "Get details of a loan transfer",
        "parameters": {
            "transfer_id": {"type": "string", "required": True}
        }
    }
]
