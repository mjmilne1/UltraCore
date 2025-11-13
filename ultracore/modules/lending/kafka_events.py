"""
Kafka Events for Lending Module
Event sourcing and real-time streaming for all lending operations
"""

from typing import Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import json


class LendingKafkaProducer:
    """
    Kafka Producer for Lending Events
    
    Publishes all lending events to Kafka topics for:
    - Event sourcing
    - Real-time analytics
    - Downstream system integration
    - Audit trail
    """
    
    def __init__(self):
        # In production, initialize actual Kafka producer
        self.producer = None
        
    def _publish(self, topic: str, event: Dict[str, Any]):
        """Publish event to Kafka topic"""
        # In production, use actual Kafka producer
        print(f"[KAFKA] Topic: {topic}, Event: {json.dumps(event, default=str)}")
        
    # ========================================================================
    # LOAN APPLICATION EVENTS
    # ========================================================================
    
    def publish_application_created(
        self,
        application_id: str,
        product_id: str,
        requested_amount: Decimal,
        term_months: int,
        applicant_id: str
    ):
        """Loan application created"""
        self._publish("loan-application-events", {
            "event_type": "application.created",
            "application_id": application_id,
            "product_id": product_id,
            "requested_amount": str(requested_amount),
            "term_months": term_months,
            "applicant_id": applicant_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_application_submitted(
        self,
        application_id: str,
        applicant_id: str
    ):
        """Loan application submitted"""
        self._publish("loan-application-events", {
            "event_type": "application.submitted",
            "application_id": application_id,
            "applicant_id": applicant_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_credit_score_calculated(
        self,
        application_id: str,
        credit_score: int,
        risk_band: str,
        model_version: str
    ):
        """Credit score calculated"""
        self._publish("loan-assessment-events", {
            "event_type": "credit_score.calculated",
            "application_id": application_id,
            "credit_score": credit_score,
            "risk_band": risk_band,
            "model_version": model_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_affordability_assessed(
        self,
        application_id: str,
        can_afford: bool,
        monthly_surplus: Decimal,
        dti_ratio: Decimal,
        risk_level: str
    ):
        """Affordability assessed"""
        self._publish("loan-assessment-events", {
            "event_type": "affordability.assessed",
            "application_id": application_id,
            "can_afford": can_afford,
            "monthly_surplus": str(monthly_surplus),
            "dti_ratio": str(dti_ratio),
            "risk_level": risk_level,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_fraud_risk_assessed(
        self,
        application_id: str,
        fraud_risk_score: float,
        fraud_risk_level: str,
        flags: list
    ):
        """Fraud risk assessed"""
        self._publish("loan-fraud-events", {
            "event_type": "fraud_risk.assessed",
            "application_id": application_id,
            "fraud_risk_score": fraud_risk_score,
            "fraud_risk_level": fraud_risk_level,
            "flags": flags,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_application_approved(
        self,
        application_id: str,
        approved_amount: Decimal,
        interest_rate: Decimal,
        approved_by: str
    ):
        """Loan application approved"""
        self._publish("loan-application-events", {
            "event_type": "application.approved",
            "application_id": application_id,
            "approved_amount": str(approved_amount),
            "interest_rate": str(interest_rate),
            "approved_by": approved_by,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_application_declined(
        self,
        application_id: str,
        decline_reason: str,
        declined_by: str
    ):
        """Loan application declined"""
        self._publish("loan-application-events", {
            "event_type": "application.declined",
            "application_id": application_id,
            "decline_reason": decline_reason,
            "declined_by": declined_by,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    # ========================================================================
    # LOAN ACCOUNT EVENTS
    # ========================================================================
    
    def publish_account_created(
        self,
        account_id: str,
        account_number: str,
        application_id: str,
        client_id: str,
        principal_amount: Decimal,
        interest_rate: Decimal,
        term_months: int
    ):
        """Loan account created"""
        self._publish("loan-account-events", {
            "event_type": "account.created",
            "account_id": account_id,
            "account_number": account_number,
            "application_id": application_id,
            "client_id": client_id,
            "principal_amount": str(principal_amount),
            "interest_rate": str(interest_rate),
            "term_months": term_months,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_loan_disbursed(
        self,
        account_id: str,
        disbursement_id: str,
        amount: Decimal,
        disbursement_method: str,
        disbursement_date: date
    ):
        """Loan disbursed"""
        self._publish("loan-account-events", {
            "event_type": "loan.disbursed",
            "account_id": account_id,
            "disbursement_id": disbursement_id,
            "amount": str(amount),
            "disbursement_method": disbursement_method,
            "disbursement_date": disbursement_date.isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_repayment_received(
        self,
        account_id: str,
        repayment_id: str,
        amount: Decimal,
        principal_portion: Decimal,
        interest_portion: Decimal,
        repayment_date: date
    ):
        """Repayment received"""
        self._publish("loan-repayment-events", {
            "event_type": "repayment.received",
            "account_id": account_id,
            "repayment_id": repayment_id,
            "amount": str(amount),
            "principal_portion": str(principal_portion),
            "interest_portion": str(interest_portion),
            "repayment_date": repayment_date.isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_repayment_failed(
        self,
        account_id: str,
        repayment_id: str,
        amount: Decimal,
        failure_reason: str
    ):
        """Repayment failed"""
        self._publish("loan-repayment-events", {
            "event_type": "repayment.failed",
            "account_id": account_id,
            "repayment_id": repayment_id,
            "amount": str(amount),
            "failure_reason": failure_reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_account_in_arrears(
        self,
        account_id: str,
        days_in_arrears: int,
        arrears_amount: Decimal,
        repayment_status: str
    ):
        """Account in arrears"""
        self._publish("loan-arrears-events", {
            "event_type": "account.in_arrears",
            "account_id": account_id,
            "days_in_arrears": days_in_arrears,
            "arrears_amount": str(arrears_amount),
            "repayment_status": repayment_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_account_defaulted(
        self,
        account_id: str,
        outstanding_amount: Decimal,
        days_overdue: int
    ):
        """Account defaulted"""
        self._publish("loan-default-events", {
            "event_type": "account.defaulted",
            "account_id": account_id,
            "outstanding_amount": str(outstanding_amount),
            "days_overdue": days_overdue,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_hardship_arrangement_created(
        self,
        account_id: str,
        arrangement_id: str,
        arrangement_type: str,
        duration_months: int
    ):
        """Hardship arrangement created"""
        self._publish("loan-hardship-events", {
            "event_type": "hardship.arrangement_created",
            "account_id": account_id,
            "arrangement_id": arrangement_id,
            "arrangement_type": arrangement_type,
            "duration_months": duration_months,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_loan_paid_off(
        self,
        account_id: str,
        final_payment_amount: Decimal,
        total_interest_paid: Decimal,
        payoff_date: date
    ):
        """Loan paid off"""
        self._publish("loan-account-events", {
            "event_type": "loan.paid_off",
            "account_id": account_id,
            "final_payment_amount": str(final_payment_amount),
            "total_interest_paid": str(total_interest_paid),
            "payoff_date": payoff_date.isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    # ========================================================================
    # COLLATERAL EVENTS
    # ========================================================================
    
    def publish_collateral_registered(
        self,
        collateral_id: str,
        collateral_type: str,
        current_value: Decimal,
        owner_id: str
    ):
        """Collateral registered"""
        self._publish("collateral-events", {
            "event_type": "collateral.registered",
            "collateral_id": collateral_id,
            "collateral_type": collateral_type,
            "current_value": str(current_value),
            "owner_id": owner_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_collateral_valued(
        self,
        collateral_id: str,
        valuation_id: str,
        valued_amount: Decimal,
        valuation_method: str
    ):
        """Collateral valued"""
        self._publish("collateral-events", {
            "event_type": "collateral.valued",
            "collateral_id": collateral_id,
            "valuation_id": valuation_id,
            "valued_amount": str(valued_amount),
            "valuation_method": valuation_method,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_collateral_linked_to_loan(
        self,
        collateral_id: str,
        account_id: str,
        allocated_value: Decimal,
        lvr: Decimal
    ):
        """Collateral linked to loan"""
        self._publish("collateral-events", {
            "event_type": "collateral.linked_to_loan",
            "collateral_id": collateral_id,
            "account_id": account_id,
            "allocated_value": str(allocated_value),
            "lvr": str(lvr),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_ppsr_registered(
        self,
        collateral_id: str,
        ppsr_registration_number: str,
        registration_date: date
    ):
        """PPSR registered"""
        self._publish("collateral-ppsr-events", {
            "event_type": "ppsr.registered",
            "collateral_id": collateral_id,
            "ppsr_registration_number": ppsr_registration_number,
            "registration_date": registration_date.isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    # ========================================================================
    # PRODUCT EVENTS
    # ========================================================================
    
    def publish_product_created(
        self,
        product_id: str,
        product_code: str,
        product_name: str,
        product_type: str,
        base_interest_rate: Decimal
    ):
        """Loan product created"""
        self._publish("loan-product-events", {
            "event_type": "product.created",
            "product_id": product_id,
            "product_code": product_code,
            "product_name": product_name,
            "product_type": product_type,
            "base_interest_rate": str(base_interest_rate),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def publish_interest_rate_changed(
        self,
        product_id: str,
        old_rate: Decimal,
        new_rate: Decimal,
        effective_date: date
    ):
        """Interest rate changed"""
        self._publish("loan-product-events", {
            "event_type": "interest_rate.changed",
            "product_id": product_id,
            "old_rate": str(old_rate),
            "new_rate": str(new_rate),
            "effective_date": effective_date.isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })


# ============================================================================
# KAFKA TOPICS CONFIGURATION
# ============================================================================

LENDING_KAFKA_TOPICS = {
    "loan-application-events": {
        "partitions": 6,
        "retention_days": 365,
        "description": "Loan application lifecycle events"
    },
    "loan-account-events": {
        "partitions": 12,
        "retention_days": 2555,  # 7 years for compliance
        "description": "Loan account lifecycle events"
    },
    "loan-assessment-events": {
        "partitions": 6,
        "retention_days": 2555,  # 7 years for compliance
        "description": "Credit scoring and affordability assessments"
    },
    "loan-fraud-events": {
        "partitions": 3,
        "retention_days": 2555,  # 7 years for compliance
        "description": "Fraud detection events"
    },
    "loan-repayment-events": {
        "partitions": 12,
        "retention_days": 2555,  # 7 years for compliance
        "description": "Loan repayment events"
    },
    "loan-arrears-events": {
        "partitions": 6,
        "retention_days": 2555,  # 7 years for compliance
        "description": "Arrears and delinquency events"
    },
    "loan-default-events": {
        "partitions": 3,
        "retention_days": 2555,  # 7 years for compliance
        "description": "Default events"
    },
    "loan-hardship-events": {
        "partitions": 3,
        "retention_days": 2555,  # 7 years for compliance
        "description": "Hardship arrangement events"
    },
    "collateral-events": {
        "partitions": 6,
        "retention_days": 2555,  # 7 years for compliance
        "description": "Collateral lifecycle events"
    },
    "collateral-ppsr-events": {
        "partitions": 3,
        "retention_days": 2555,  # 7 years for compliance
        "description": "PPSR registration events"
    },
    "loan-product-events": {
        "partitions": 3,
        "retention_days": 365,
        "description": "Loan product configuration events"
    }
}
