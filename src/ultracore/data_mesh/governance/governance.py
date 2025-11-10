"""
Data Mesh Governance
Federated governance model with central standards
"""
from typing import Dict, List
from enum import Enum


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class DataGovernance:
    """
    Federated governance for data mesh
    
    Enforces:
    - Data quality standards
    - Security policies
    - Compliance requirements
    - SLA monitoring
    """
    
    GLOBAL_POLICIES = {
        "data_retention": {
            "customer_data": 2555,  # 7 years (Australian requirement)
            "transaction_data": 2555,  # 7 years
            "audit_logs": 2555,  # 7 years
            "analytical_data": 365  # 1 year
        },
        "quality_standards": {
            "completeness_threshold": 0.95,
            "accuracy_threshold": 0.99,
            "timeliness_minutes": 5,
            "consistency_checks": True
        },
        "security": {
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "pii_masking": True,
            "access_logging": True
        }
    }
    
    def validate_data_product(self, product_metadata: Dict) -> Dict:
        """
        Validate that a data product meets governance standards
        
        Returns:
            Validation result with any issues
        """
        issues = []
        
        # Check required metadata
        required_fields = ["domain", "owner", "sla", "quality_checks"]
        for field in required_fields:
            if field not in product_metadata:
                issues.append(f"Missing required field: {field}")
        
        # Check SLA commitments
        if "sla" in product_metadata:
            sla = product_metadata["sla"]
            if sla.get("availability", 0) < 0.99:
                issues.append("SLA availability must be >= 99%")
        
        # Check quality checks
        if "quality_checks" in product_metadata:
            required_checks = ["completeness", "accuracy", "timeliness"]
            provided_checks = product_metadata["quality_checks"]
            missing = set(required_checks) - set(provided_checks)
            if missing:
                issues.append(f"Missing quality checks: {missing}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def check_compliance(self, domain: str, data_type: str) -> Dict:
        """Check compliance requirements for data type"""
        compliance = {
            "privacy_act_1988": True,  # All domains
            "aml_ctf_act_2006": domain in ["client", "payment", "loan"],
            "asic_reporting": domain in ["loan", "account"],
            "data_retention_days": self.GLOBAL_POLICIES["data_retention"].get(
                data_type, 365
            )
        }
        return compliance
    
    def get_access_policy(self, classification: DataClassification) -> Dict:
        """Get access control policy for data classification"""
        policies = {
            DataClassification.PUBLIC: {
                "authentication": False,
                "encryption": False,
                "audit_log": False
            },
            DataClassification.INTERNAL: {
                "authentication": True,
                "encryption": True,
                "audit_log": True,
                "mfa_required": False
            },
            DataClassification.CONFIDENTIAL: {
                "authentication": True,
                "encryption": True,
                "audit_log": True,
                "mfa_required": True,
                "pii_masking": True
            },
            DataClassification.RESTRICTED: {
                "authentication": True,
                "encryption": True,
                "audit_log": True,
                "mfa_required": True,
                "pii_masking": True,
                "approval_required": True
            }
        }
        return policies[classification]


governance = DataGovernance()
