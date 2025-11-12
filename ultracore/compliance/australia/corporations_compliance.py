"""
Corporations Act 2001 Compliance Module
Company and Financial Services Regulation
"""

from typing import Dict, Any, List
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    """Company types"""
    PROPRIETARY = "proprietary"  # Pty Ltd
    PUBLIC = "public"  # Limited
    NO_LIABILITY = "no_liability"  # NL (mining)

class CorporationsActCompliance:
    """
    Corporations Act 2001 Compliance
    
    Key Requirements:
    1. Company registration (ACN)
    2. Director duties
    3. Financial reporting
    4. Disclosure requirements
    5. Related party transactions
    6. Insolvent trading prevention
    7. Record keeping
    """
    
    def __init__(self):
        self.acn = None
        self.entity_type = None
        
    def validate_acn(self, acn: str) -> Dict[str, Any]:
        """
        Validate Australian Company Number
        
        Format: XXX XXX XXX (9 digits)
        """
        
        acn_clean = acn.replace(" ", "")
        
        valid = (
            len(acn_clean) == 9 and
            acn_clean.isdigit()
        )
        
        return {
            "valid": valid,
            "acn": acn if valid else None,
            "format": "XXX XXX XXX"
        }
    
    def check_director_duties(
        self,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check compliance with director duties (s180-183)
        
        Directors must:
        1. Act with care and diligence (s180)
        2. Act in good faith in best interests (s181)
        3. Not improperly use position (s182)
        4. Not improperly use information (s183)
        """
        
        checks = {
            "care_and_diligence": True,  # Would assess based on action
            "good_faith": True,
            "no_improper_use_position": True,
            "no_improper_use_information": True
        }
        
        # Check for conflicts of interest
        if action.get("personal_benefit"):
            checks["good_faith"] = False
            checks["no_improper_use_position"] = False
        
        compliant = all(checks.values())
        
        return {
            "compliant": compliant,
            "duties_assessed": checks,
            "action": action.get("description")
        }
    
    def check_related_party_transaction(
        self,
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check related party transaction (Chapter 2E)
        
        Requires:
        - Member approval for material benefits
        - Disclosure of relationship
        - Arm's length terms
        """
        
        is_related_party = transaction.get("related_party", False)
        amount = transaction.get("amount", 0)
        
        if not is_related_party:
            return {
                "approval_required": False,
                "compliant": True
            }
        
        # Material if >$100k or >1% of assets
        material = amount > 100000
        
        approval_required = material
        approval_obtained = transaction.get("member_approval", False)
        
        return {
            "related_party_transaction": True,
            "material": material,
            "approval_required": approval_required,
            "approval_obtained": approval_obtained,
            "compliant": not approval_required or approval_obtained,
            "disclosure_required": True
        }
    
    def check_financial_reporting(
        self,
        entity_size: str
    ) -> Dict[str, Any]:
        """
        Check financial reporting requirements
        
        Depends on entity size:
        - Large proprietary: Must prepare and audit
        - Small proprietary: Generally exempt
        - Public: Must prepare, audit, lodge
        """
        
        if entity_size == "large_proprietary":
            return {
                "financial_report_required": True,
                "audit_required": True,
                "lodge_with_asic": True,
                "deadline": "Within 4 months of year end"
            }
        elif entity_size == "small_proprietary":
            return {
                "financial_report_required": False,
                "audit_required": False,
                "lodge_with_asic": False,
                "notes": "Unless directed by ASIC or shareholders"
            }
        else:  # public
            return {
                "financial_report_required": True,
                "audit_required": True,
                "lodge_with_asic": True,
                "annual_report_required": True,
                "deadline": "Within 4 months of year end"
            }
    
    def check_insolvent_trading(
        self,
        financial_position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check for insolvent trading (s588G)
        
        Director has defense if:
        - Reasonable grounds to believe solvent
        - Relied on competent person
        - Was sick
        - Took reasonable steps to prevent
        """
        
        assets = financial_position.get("total_assets", 0)
        liabilities = financial_position.get("total_liabilities", 0)
        
        net_position = assets - liabilities
        
        # Check liquidity
        current_assets = financial_position.get("current_assets", 0)
        current_liabilities = financial_position.get("current_liabilities", 0)
        current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
        
        # Indicators of insolvency
        insolvent_indicators = []
        
        if net_position < 0:
            insolvent_indicators.append("Liabilities exceed assets")
        
        if current_ratio < 1:
            insolvent_indicators.append("Cannot pay debts as they fall due")
        
        if financial_position.get("continuing_losses"):
            insolvent_indicators.append("Continuing trading losses")
        
        likely_insolvent = len(insolvent_indicators) >= 2
        
        return {
            "likely_insolvent": likely_insolvent,
            "indicators": insolvent_indicators,
            "net_assets": net_position,
            "current_ratio": current_ratio,
            "warning": "Director may be personally liable if trading while insolvent" if likely_insolvent else None,
            "recommended_action": "Seek professional advice immediately" if likely_insolvent else None
        }

# Global instance
corporations_compliance = CorporationsActCompliance()
