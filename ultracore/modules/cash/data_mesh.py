"""
Data Mesh for Cash Management
Data governance, quality, and lineage
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class DataQualityDimension(str, Enum):
    """Data quality dimensions"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"

class CashDataMesh:
    """
    Data Mesh for Cash Management
    
    Features:
    - Data quality monitoring
    - Data lineage tracking
    - Materialized views
    - Data governance
    - Version control
    """
    
    def __init__(self):
        self.quality_scores = {}
        self.lineage_records = []
        self.materialized_views = {}
        self.governance_policies = {}
        
    def assess_transaction_quality(
        self,
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess data quality of cash transaction
        
        Dimensions:
        - Completeness: All required fields present
        - Accuracy: Values within expected ranges
        - Consistency: Internal consistency checks
        - Timeliness: Not stale data
        - Validity: Valid formats and values
        """
        
        scores = {}
        issues = []
        
        # Completeness check
        required_fields = [
            "account_id", "transaction_id", "amount", 
            "timestamp", "transaction_type"
        ]
        
        missing_fields = [f for f in required_fields if f not in transaction]
        completeness = (len(required_fields) - len(missing_fields)) / len(required_fields) * 100
        
        scores[DataQualityDimension.COMPLETENESS] = completeness
        
        if missing_fields:
            issues.append(f"Missing fields: {', '.join(missing_fields)}")
        
        # Accuracy check
        amount = transaction.get("amount", 0)
        accuracy = 100.0
        
        if amount <= 0:
            accuracy -= 50
            issues.append("Amount must be positive")
        
        if amount > 10000000:  # $10M
            accuracy -= 25
            issues.append("Amount exceeds normal range")
        
        scores[DataQualityDimension.ACCURACY] = accuracy
        
        # Validity check
        validity = 100.0
        
        # Check account ID format
        account_id = transaction.get("account_id", "")
        if not account_id.startswith("CMA-"):
            validity -= 25
            issues.append("Invalid account ID format")
        
        # Check transaction ID format
        transaction_id = transaction.get("transaction_id", "")
        if not any(transaction_id.startswith(prefix) for prefix in ["DEP-", "WDR-", "TRF-"]):
            validity -= 25
            issues.append("Invalid transaction ID format")
        
        scores[DataQualityDimension.VALIDITY] = validity
        
        # Timeliness check
        timestamp = transaction.get("timestamp")
        if timestamp:
            try:
                tx_time = datetime.fromisoformat(timestamp)
                age_seconds = (datetime.now(timezone.utc) - tx_time).total_seconds()
                
                if age_seconds < 3600:  # < 1 hour
                    timeliness = 100.0
                elif age_seconds < 86400:  # < 1 day
                    timeliness = 75.0
                else:
                    timeliness = 50.0
                    issues.append("Stale data (>1 day old)")
                    
            except:
                timeliness = 0.0
                issues.append("Invalid timestamp format")
        else:
            timeliness = 0.0
            issues.append("Missing timestamp")
        
        scores[DataQualityDimension.TIMELINESS] = timeliness
        
        # Consistency check (would check against other data sources)
        consistency = 100.0
        scores[DataQualityDimension.CONSISTENCY] = consistency
        
        # Overall quality score
        overall_score = sum(scores.values()) / len(scores)
        
        quality_assessment = {
            "overall_score": overall_score,
            "dimension_scores": scores,
            "issues": issues,
            "grade": self._get_quality_grade(overall_score),
            "assessed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Store quality score
        self.quality_scores[transaction.get("transaction_id", "unknown")] = quality_assessment
        
        return quality_assessment
    
    def _get_quality_grade(self, score: float) -> str:
        """Get quality grade from score"""
        
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        else:
            return "D"
    
    def track_lineage(
        self,
        data_element: str,
        source: str,
        transformations: List[str],
        destination: str
    ):
        """Track data lineage"""
        
        lineage_record = {
            "lineage_id": f"LIN-{len(self.lineage_records) + 1:06d}",
            "data_element": data_element,
            "source": source,
            "transformations": transformations,
            "destination": destination,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.lineage_records.append(lineage_record)
        
        return lineage_record
    
    def create_materialized_view(
        self,
        view_name: str,
        source_data: List[Dict[str, Any]],
        aggregation: str
    ):
        """Create materialized view for performance"""
        
        if aggregation == "account_balances":
            # Create view of current account balances
            view_data = {}
            
            for item in source_data:
                account_id = item.get("account_id")
                if account_id not in view_data:
                    view_data[account_id] = {
                        "account_id": account_id,
                        "available_balance": 0.0,
                        "ledger_balance": 0.0,
                        "transaction_count": 0,
                        "last_updated": None
                    }
                
                view_data[account_id]["available_balance"] = item.get("available_balance", 0.0)
                view_data[account_id]["ledger_balance"] = item.get("ledger_balance", 0.0)
                view_data[account_id]["transaction_count"] += 1
                view_data[account_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        elif aggregation == "daily_transactions":
            # Create view of daily transaction totals
            view_data = {}
            
            for item in source_data:
                date = item.get("timestamp", "")[:10]
                
                if date not in view_data:
                    view_data[date] = {
                        "date": date,
                        "total_deposits": 0.0,
                        "total_withdrawals": 0.0,
                        "transaction_count": 0
                    }
                
                tx_type = item.get("transaction_type")
                amount = item.get("amount", 0.0)
                
                if tx_type == "deposit":
                    view_data[date]["total_deposits"] += amount
                elif tx_type == "withdrawal":
                    view_data[date]["total_withdrawals"] += amount
                
                view_data[date]["transaction_count"] += 1
        
        else:
            view_data = {}
        
        self.materialized_views[view_name] = {
            "data": view_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_count": len(source_data)
        }
        
        return view_data
    
    def apply_governance_policy(
        self,
        policy_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply data governance policy"""
        
        policies = {
            "pii_masking": self._mask_pii,
            "retention_policy": self._apply_retention,
            "access_control": self._check_access
        }
        
        policy_func = policies.get(policy_name)
        
        if policy_func:
            return policy_func(data)
        
        return {"compliant": True, "data": data}
    
    def _mask_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask personally identifiable information"""
        
        masked_data = data.copy()
        
        # Mask account numbers (show last 4 digits)
        if "account_id" in masked_data:
            account_id = masked_data["account_id"]
            if len(account_id) > 4:
                masked_data["account_id"] = "***" + account_id[-4:]
        
        # Mask destination accounts
        if "destination" in masked_data:
            dest = masked_data["destination"]
            if len(dest) > 4:
                masked_data["destination"] = "***" + dest[-4:]
        
        return {
            "compliant": True,
            "data": masked_data,
            "policy_applied": "pii_masking"
        }
    
    def _apply_retention(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply data retention policy"""
        
        # Check if data is past retention period
        timestamp = data.get("timestamp")
        
        if timestamp:
            data_age = (datetime.now(timezone.utc) - datetime.fromisoformat(timestamp)).days
            
            # 7-year retention for cash transactions (Australian requirement)
            retention_days = 7 * 365
            
            if data_age > retention_days:
                return {
                    "compliant": False,
                    "data": None,
                    "reason": "Past retention period",
                    "policy_applied": "retention_policy"
                }
        
        return {
            "compliant": True,
            "data": data,
            "policy_applied": "retention_policy"
        }
    
    def _check_access(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check access control"""
        
        # Would implement role-based access control
        return {
            "compliant": True,
            "data": data,
            "policy_applied": "access_control"
        }
    
    def generate_data_quality_report(self) -> Dict[str, Any]:
        """Generate data quality report"""
        
        if not self.quality_scores:
            return {
                "total_assessments": 0,
                "average_score": 0,
                "grade_distribution": {}
            }
        
        scores = [s["overall_score"] for s in self.quality_scores.values()]
        grades = [s["grade"] for s in self.quality_scores.values()]
        
        grade_distribution = {}
        for grade in grades:
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        return {
            "total_assessments": len(scores),
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "grade_distribution": grade_distribution,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

# Global data mesh instance
cash_data_mesh = CashDataMesh()
