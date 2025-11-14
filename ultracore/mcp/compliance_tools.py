"""
MCP Compliance Tools
Model Context Protocol tools for AI agents to interact with compliance system
"""

from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4

from ultracore.compliance.aggregates.customer import CustomerAggregate
from ultracore.compliance.aggregates.complaint import ComplaintAggregate
from ultracore.agentic_ai.agents.compliance.aml_agent import AMLMonitoringAgent
from ultracore.ml.compliance.fraud_detection import FraudDetectionModel


class ComplianceMCPTools:
    """
    MCP tools for compliance operations
    Enables AI agents to perform compliance actions
    """
    
    def __init__(self):
        self.aml_agent = AMLMonitoringAgent()
        self.fraud_model = FraudDetectionModel()
    
    def check_aml_status(self, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """
        Check AML compliance status for user
        
        MCP Tool: check_aml_status
        """
        # In production, fetch from event store
        return {
            "user_id": user_id,
            "aml_status": "verified",
            "risk_level": "low",
            "last_reviewed": datetime.utcnow().isoformat(),
            "pep_check": "passed",
            "sanctions_check": "passed"
        }
    
    def monitor_transaction(
        self,
        transaction_id: str,
        user_id: str,
        tenant_id: str,
        transaction_type: str,
        amount: float,
        currency: str = "AUD"
    ) -> Dict[str, Any]:
        """
        Monitor transaction for AML compliance
        
        MCP Tool: monitor_transaction
        """
        # Fetch user history (from event store in production)
        user_history = []
        
        # Run AML monitoring
        result = self.aml_agent.monitor_transaction(
            transaction_id=transaction_id,
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            user_history=user_history
        )
        
        # Run ML fraud detection
        transaction_data = {
            "id": transaction_id,
            "type": transaction_type,
            "amount": amount,
            "currency": currency,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        fraud_result = self.fraud_model.predict_fraud_probability(
            transaction=transaction_data,
            user_history=user_history
        )
        
        return {
            "transaction_id": transaction_id,
            "aml_monitoring": result,
            "fraud_detection": fraud_result,
            "overall_risk": "high" if result["is_suspicious"] or fraud_result["fraud_probability"] > 0.7 else "low",
            "action_required": result["requires_smr"] or fraud_result["fraud_probability"] > 0.8
        }
    
    def file_smr(
        self,
        user_id: str,
        tenant_id: str,
        transaction_ids: List[str],
        reason: str,
        report_type: str = "suspicious"
    ) -> Dict[str, Any]:
        """
        File Suspicious Matter Report with AUSTRAC
        
        MCP Tool: file_smr
        """
        smr_reference = f"SMR-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
        
        # In production, create SMR aggregate and publish events
        return {
            "smr_reference": smr_reference,
            "report_type": report_type,
            "transaction_ids": transaction_ids,
            "filed_at": datetime.utcnow().isoformat(),
            "filed_with_austrac": True,
            "status": "filed"
        }
    
    def submit_complaint(
        self,
        user_id: str,
        tenant_id: str,
        category: str,
        subject: str,
        description: str,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Submit customer complaint
        
        MCP Tool: submit_complaint
        """
        complaint_id = str(uuid4())
        
        # Create complaint aggregate
        complaint = ComplaintAggregate(complaint_id, tenant_id)
        complaint.submit(
            user_id=user_id,
            category=category,
            subject=subject,
            description=description,
            priority=priority
        )
        
        # Publish events
        success = complaint.commit()
        
        return {
            "complaint_id": complaint_id,
            "complaint_reference": complaint.complaint_reference,
            "status": "submitted",
            "submitted_at": datetime.utcnow().isoformat(),
            "acknowledgment_due": (datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat(),
            "resolution_due": (datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat(),
            "success": success
        }
    
    def acknowledge_complaint(
        self,
        complaint_id: str,
        tenant_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Acknowledge complaint (24-hour requirement)
        
        MCP Tool: acknowledge_complaint
        """
        # Rebuild complaint from events
        complaint = ComplaintAggregate(complaint_id, tenant_id)
        complaint.acknowledge(user_id)
        success = complaint.commit()
        
        return {
            "complaint_id": complaint_id,
            "status": "acknowledged",
            "acknowledged_at": datetime.utcnow().isoformat(),
            "acknowledged_by": user_id,
            "success": success
        }
    
    def resolve_complaint(
        self,
        complaint_id: str,
        tenant_id: str,
        user_id: str,
        resolution: str,
        compensation_amount: float = None
    ) -> Dict[str, Any]:
        """
        Resolve complaint
        
        MCP Tool: resolve_complaint
        """
        complaint = ComplaintAggregate(complaint_id, tenant_id)
        complaint.resolve(
            user_id=user_id,
            resolution=resolution,
            compensation_amount=compensation_amount
        )
        success = complaint.commit()
        
        return {
            "complaint_id": complaint_id,
            "status": "resolved",
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution": resolution,
            "compensation_amount": compensation_amount,
            "success": success
        }
    
    def escalate_to_afca(
        self,
        complaint_id: str,
        tenant_id: str,
        user_id: str,
        escalation_reason: str
    ) -> Dict[str, Any]:
        """
        Escalate complaint to AFCA
        
        MCP Tool: escalate_to_afca
        """
        complaint = ComplaintAggregate(complaint_id, tenant_id)
        complaint.escalate_to_afca(user_id, escalation_reason)
        success = complaint.commit()
        
        return {
            "complaint_id": complaint_id,
            "status": "escalated_afca",
            "afca_reference": complaint.afca_reference,
            "escalated_at": datetime.utcnow().isoformat(),
            "escalation_reason": escalation_reason,
            "success": success
        }
    
    def perform_reconciliation(
        self,
        tenant_id: str,
        user_id: str,
        total_client_balance: float,
        bank_balance: float
    ) -> Dict[str, Any]:
        """
        Perform daily client money reconciliation
        
        MCP Tool: perform_reconciliation
        """
        variance = abs(total_client_balance - bank_balance)
        
        if variance < 0.01:
            status = "balanced"
            severity = None
        elif variance < 10.00:
            status = "minor_variance"
            severity = "minor"
        else:
            status = "major_variance"
            severity = "major"
        
        return {
            "reconciliation_date": datetime.utcnow().date().isoformat(),
            "total_client_balance": total_client_balance,
            "bank_balance": bank_balance,
            "variance": variance,
            "status": status,
            "severity": severity,
            "requires_investigation": variance >= 10.00,
            "performed_at": datetime.utcnow().isoformat(),
            "performed_by": user_id
        }
    
    def assess_risk(
        self,
        tenant_id: str,
        user_id: str,
        risk_category: str,
        risk_title: str,
        risk_description: str,
        likelihood: str,
        impact: str
    ) -> Dict[str, Any]:
        """
        Create risk assessment
        
        MCP Tool: assess_risk
        """
        # Calculate risk score
        likelihood_scores = {"rare": 1, "unlikely": 2, "possible": 3, "likely": 4, "almost_certain": 5}
        impact_scores = {"insignificant": 1, "minor": 2, "moderate": 3, "major": 4, "catastrophic": 5}
        
        risk_score = likelihood_scores[likelihood] * impact_scores[impact]
        
        if risk_score >= 16:
            risk_level = "very_high"
        elif risk_score >= 10:
            risk_level = "high"
        elif risk_score >= 5:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        risk_reference = f"RISK-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
        
        return {
            "risk_reference": risk_reference,
            "risk_category": risk_category,
            "risk_title": risk_title,
            "likelihood": likelihood,
            "impact": impact,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "assessed_at": datetime.utcnow().isoformat(),
            "assessed_by": user_id
        }


# Singleton instance
_compliance_tools: ComplianceMCPTools = None

def get_compliance_tools() -> ComplianceMCPTools:
    """Get singleton compliance tools instance"""
    global _compliance_tools
    if _compliance_tools is None:
        _compliance_tools = ComplianceMCPTools()
    return _compliance_tools
