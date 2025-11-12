"""Compliance Service - SMSF Regulatory Compliance"""
from typing import Dict, List
from decimal import Decimal
from datetime import date


class ComplianceService:
    """
    SMSF compliance and regulatory service.
    
    Features:
    - Sole purpose test monitoring
    - Arm's length transactions
    - In-house asset limits (5%)
    - Investment restrictions
    - ATO annual return preparation
    - Audit preparation
    """
    
    async def check_compliance(
        self,
        smsf_id: str
    ) -> Dict:
        """
        Comprehensive compliance check.
        
        Returns compliance status and issues.
        """
        
        issues = []
        warnings = []
        
        # Mock compliance checks
        
        # 1. Sole purpose test
        sole_purpose_compliant = True
        if not sole_purpose_compliant:
            issues.append("Sole purpose test: Fund not providing retirement benefits")
        
        # 2. In-house assets (max 5%)
        in_house_assets_percentage = Decimal("3.2")
        if in_house_assets_percentage > Decimal("5.0"):
            issues.append(f"In-house assets exceed 5% limit: {float(in_house_assets_percentage):.1f}%")
        
        # 3. Arm's length transactions
        arm_length_compliant = True
        if not arm_length_compliant:
            issues.append("Non-arm's length transactions detected")
        
        # 4. Investment restrictions
        has_collectibles = False
        has_personal_use_assets = False
        
        if has_collectibles:
            issues.append("Collectibles held (not permitted)")
        
        if has_personal_use_assets:
            issues.append("Personal use assets detected (not permitted)")
        
        # 5. Contribution caps
        caps_exceeded = False
        if caps_exceeded:
            warnings.append("Contribution caps exceeded - ATO determination expected")
        
        # 6. Minimum pension payments
        pension_minimum_met = True
        if not pension_minimum_met:
            issues.append("Minimum pension payments not met - pension status at risk")
        
        # 7. Annual return
        annual_return_lodged = False
        if not annual_return_lodged:
            warnings.append("Annual return not yet lodged (due October 31)")
        
        # 8. Audit requirement
        audit_completed = False
        if not audit_completed:
            warnings.append("Annual audit not completed (required before lodging return)")
        
        compliance_status = "compliant" if len(issues) == 0 else "non_compliant"
        
        return {
            "smsf_id": smsf_id,
            "compliance_status": compliance_status,
            "issues_count": len(issues),
            "warnings_count": len(warnings),
            "issues": issues,
            "warnings": warnings,
            "checks_performed": {
                "sole_purpose_test": "? Passed" if sole_purpose_compliant else "? Failed",
                "in_house_assets": f"? {float(in_house_assets_percentage):.1f}% (limit 5%)",
                "arms_length": "? Compliant" if arm_length_compliant else "? Non-compliant",
                "investment_restrictions": "? Compliant",
                "contribution_caps": "? Within limits" if not caps_exceeded else "?? Exceeded",
                "minimum_pensions": "? Met" if pension_minimum_met else "? Not met",
                "annual_return": "? Lodged" if annual_return_lodged else "? Pending",
                "audit": "? Complete" if audit_completed else "? Required"
            },
            "next_actions": self._get_compliance_actions(issues, warnings),
            "important_dates": {
                "annual_return_due": "October 31 each year",
                "audit_required": "Before lodging annual return",
                "financial_year_end": "June 30"
            }
        }
    
    def _get_compliance_actions(
        self,
        issues: List[str],
        warnings: List[str]
    ) -> List[str]:
        """Get recommended compliance actions."""
        
        actions = []
        
        if len(issues) > 0:
            actions.append("?? URGENT: Address compliance issues immediately")
            actions.append("Contact SMSF specialist accountant")
            actions.append("May require voluntary disclosure to ATO")
        
        if len(warnings) > 0:
            actions.append("?? Review warnings and take action")
        
        if len(issues) == 0 and len(warnings) == 0:
            actions.append("? SMSF is compliant - well done!")
            actions.append("Maintain good record keeping")
            actions.append("Review investment strategy annually")
        
        return actions
    
    async def prepare_annual_return(
        self,
        smsf_id: str,
        financial_year: str
    ) -> Dict:
        """
        Prepare ATO annual return.
        
        SAR (Self-Managed Superannuation Fund Annual Return):
        - Member details
        - Contribution details
        - Pension payments
        - Investment income
        - Expenses
        - Tax calculations
        - Compliance declaration
        """
        
        return {
            "smsf_id": smsf_id,
            "financial_year": financial_year,
            "annual_return": {
                "members": 2,
                "total_contributions": 65000.00,
                "total_pensions": 32000.00,
                "investment_income": 45000.00,
                "expenses": 5000.00,
                "tax_payable": 6000.00
            },
            "status": "ready_for_lodgment",
            "lodgment_method": "Online (ATO portal)",
            "due_date": "October 31",
            "message": "Annual return prepared - ready for auditor review"
        }
