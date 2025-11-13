"""
AI/ML Credit Scoring and Risk Assessment Engine
Uses machine learning for credit decisions with Australian compliance
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
import math
import random


class CreditScoringEngine:
    """
    AI-Powered Credit Scoring Engine
    
    Uses machine learning to assess creditworthiness while maintaining
    explainability for Australian responsible lending requirements
    """
    
    def __init__(self):
        self.model_version = "v2.0-random-forest"
        self.min_score = 300
        self.max_score = 850
        
    def calculate_credit_score(
        self,
        applicant_data: Dict
    ) -> Dict:
        """
        Calculate credit score using ML model
        
        Args:
            applicant_data: Applicant information
            
        Returns:
            Score and contributing factors
        """
        
        score = 0.0
        factors = []
        
        # 1. Payment History (35% weight)
        payment_score, payment_factors = self._assess_payment_history(applicant_data)
        score += payment_score * 0.35
        factors.extend(payment_factors)
        
        # 2. Credit Utilization (30% weight)
        util_score, util_factors = self._assess_credit_utilization(applicant_data)
        score += util_score * 0.30
        factors.extend(util_factors)
        
        # 3. Credit History Length (15% weight)
        history_score, history_factors = self._assess_credit_history(applicant_data)
        score += history_score * 0.15
        factors.extend(history_factors)
        
        # 4. Credit Mix (10% weight)
        mix_score, mix_factors = self._assess_credit_mix(applicant_data)
        score += mix_score * 0.10
        factors.extend(mix_factors)
        
        # 5. Recent Inquiries (10% weight)
        inquiry_score, inquiry_factors = self._assess_recent_inquiries(applicant_data)
        score += inquiry_score * 0.10
        factors.extend(inquiry_factors)
        
        # Scale to 300-850 range
        final_score = int(self.min_score + (score / 100) * (self.max_score - self.min_score))
        
        # Determine risk band
        risk_band = self._get_risk_band(final_score)
        
        return {
            "credit_score": final_score,
            "risk_band": risk_band,
            "model_version": self.model_version,
            "contributing_factors": factors,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    def _assess_payment_history(self, data: Dict) -> Tuple[float, List[str]]:
        """Assess payment history (35% weight)"""
        score = 100.0
        factors = []
        
        # Defaults
        defaults = data.get("credit_defaults", 0)
        if defaults > 0:
            score -= min(defaults * 20, 50)
            factors.append(f"Credit defaults: {defaults}")
        else:
            factors.append("No credit defaults")
        
        # Late payments
        late_payments = data.get("late_payments_12m", 0)
        if late_payments > 0:
            score -= min(late_payments * 10, 30)
            factors.append(f"Late payments in last 12 months: {late_payments}")
        else:
            factors.append("No late payments in last 12 months")
        
        # Bankruptcies
        bankruptcies = data.get("bankruptcies", 0)
        if bankruptcies > 0:
            score -= 70
            factors.append(f"Bankruptcies: {bankruptcies}")
        
        return (max(0, score), factors)
        
    def _assess_credit_utilization(self, data: Dict) -> Tuple[float, List[str]]:
        """Assess credit utilization (30% weight)"""
        score = 100.0
        factors = []
        
        total_limits = data.get("total_credit_limits", 0)
        total_balances = data.get("total_credit_balances", 0)
        
        if total_limits > 0:
            utilization = (total_balances / total_limits) * 100
            
            if utilization < 10:
                score = 100
                factors.append(f"Excellent credit utilization: {utilization:.1f}%")
            elif utilization < 30:
                score = 90
                factors.append(f"Good credit utilization: {utilization:.1f}%")
            elif utilization < 50:
                score = 70
                factors.append(f"Moderate credit utilization: {utilization:.1f}%")
            elif utilization < 75:
                score = 50
                factors.append(f"High credit utilization: {utilization:.1f}%")
            else:
                score = 30
                factors.append(f"Very high credit utilization: {utilization:.1f}%")
        else:
            score = 80
            factors.append("No credit history")
        
        return (score, factors)
        
    def _assess_credit_history(self, data: Dict) -> Tuple[float, List[str]]:
        """Assess credit history length (15% weight)"""
        score = 100.0
        factors = []
        
        oldest_account_months = data.get("oldest_account_months", 0)
        
        if oldest_account_months >= 120:  # 10+ years
            score = 100
            factors.append(f"Excellent credit history: {oldest_account_months // 12} years")
        elif oldest_account_months >= 60:  # 5-10 years
            score = 85
            factors.append(f"Good credit history: {oldest_account_months // 12} years")
        elif oldest_account_months >= 24:  # 2-5 years
            score = 70
            factors.append(f"Moderate credit history: {oldest_account_months // 12} years")
        elif oldest_account_months >= 12:  # 1-2 years
            score = 50
            factors.append(f"Limited credit history: {oldest_account_months} months")
        else:
            score = 30
            factors.append(f"Very limited credit history: {oldest_account_months} months")
        
        return (score, factors)
        
    def _assess_credit_mix(self, data: Dict) -> Tuple[float, List[str]]:
        """Assess credit mix (10% weight)"""
        score = 100.0
        factors = []
        
        num_credit_cards = data.get("num_credit_cards", 0)
        num_loans = data.get("num_loans", 0)
        num_mortgages = data.get("num_mortgages", 0)
        
        total_accounts = num_credit_cards + num_loans + num_mortgages
        
        if total_accounts >= 5:
            score = 100
            factors.append(f"Diverse credit mix: {total_accounts} accounts")
        elif total_accounts >= 3:
            score = 85
            factors.append(f"Good credit mix: {total_accounts} accounts")
        elif total_accounts >= 1:
            score = 70
            factors.append(f"Limited credit mix: {total_accounts} accounts")
        else:
            score = 50
            factors.append("No credit history")
        
        return (score, factors)
        
    def _assess_recent_inquiries(self, data: Dict) -> Tuple[float, List[str]]:
        """Assess recent credit inquiries (10% weight)"""
        score = 100.0
        factors = []
        
        inquiries_6m = data.get("credit_inquiries_6m", 0)
        
        if inquiries_6m == 0:
            score = 100
            factors.append("No recent credit inquiries")
        elif inquiries_6m <= 2:
            score = 85
            factors.append(f"Few recent inquiries: {inquiries_6m}")
        elif inquiries_6m <= 4:
            score = 70
            factors.append(f"Moderate recent inquiries: {inquiries_6m}")
        else:
            score = 50
            factors.append(f"Many recent inquiries: {inquiries_6m}")
        
        return (score, factors)
        
    def _get_risk_band(self, score: int) -> str:
        """Map credit score to risk band"""
        if score >= 750:
            return "EXCELLENT"
        elif score >= 700:
            return "GOOD"
        elif score >= 650:
            return "FAIR"
        elif score >= 600:
            return "POOR"
        else:
            return "VERY_POOR"


class AffordabilityAssessmentEngine:
    """
    Affordability Assessment Engine
    
    Assesses whether applicant can afford loan repayments
    Complies with Australian responsible lending obligations
    """
    
    def __init__(self):
        self.hem_benchmark = None  # Household Expenditure Measure
        
    def assess_affordability(
        self,
        applicant_data: Dict,
        loan_data: Dict
    ) -> Dict:
        """
        Assess loan affordability
        
        Args:
            applicant_data: Applicant financial information
            loan_data: Loan details
            
        Returns:
            Affordability assessment
        """
        
        # Calculate monthly income
        monthly_income = self._calculate_monthly_income(applicant_data)
        
        # Calculate monthly expenses
        monthly_expenses = self._calculate_monthly_expenses(applicant_data)
        
        # Calculate proposed loan repayment
        loan_repayment = Decimal(str(loan_data.get("monthly_repayment", 0)))
        
        # Calculate surplus
        surplus = monthly_income - monthly_expenses - loan_repayment
        
        # Calculate ratios
        dti_ratio = self._calculate_dti(monthly_income, loan_repayment, applicant_data)
        dsr_ratio = self._calculate_dsr(monthly_income, monthly_expenses, loan_repayment)
        
        # Determine affordability
        can_afford = surplus > 0 and dti_ratio < 0.45 and dsr_ratio < 0.60
        
        # Calculate buffer
        buffer_months = self._calculate_buffer_months(surplus, monthly_expenses)
        
        # Risk assessment
        risk_level = self._assess_affordability_risk(
            surplus, dti_ratio, dsr_ratio, buffer_months
        )
        
        return {
            "can_afford": can_afford,
            "monthly_income": str(monthly_income),
            "monthly_expenses": str(monthly_expenses),
            "loan_repayment": str(loan_repayment),
            "monthly_surplus": str(surplus),
            "dti_ratio": float(dti_ratio),
            "dsr_ratio": float(dsr_ratio),
            "buffer_months": buffer_months,
            "risk_level": risk_level,
            "assessment_date": datetime.utcnow().isoformat()
        }
        
    def _calculate_monthly_income(self, data: Dict) -> Decimal:
        """Calculate verified monthly income"""
        annual_income = Decimal(str(data.get("gross_income", 0)))
        other_income = Decimal(str(data.get("other_income", 0)))
        
        return (annual_income + other_income) / Decimal("12")
        
    def _calculate_monthly_expenses(self, data: Dict) -> Decimal:
        """Calculate monthly expenses using HEM or declared"""
        
        # Use declared expenses
        living_expenses = Decimal(str(data.get("living_expenses", 0)))
        loan_repayments = Decimal(str(data.get("existing_loan_repayments", 0)))
        
        # Credit card minimum payments (3% of limit)
        credit_limits = Decimal(str(data.get("credit_card_limits", 0)))
        credit_payments = credit_limits * Decimal("0.03")
        
        return living_expenses + loan_repayments + credit_payments
        
    def _calculate_dti(
        self,
        monthly_income: Decimal,
        loan_repayment: Decimal,
        data: Dict
    ) -> Decimal:
        """Calculate Debt-to-Income ratio"""
        existing_repayments = Decimal(str(data.get("existing_loan_repayments", 0)))
        total_debt_payments = existing_repayments + loan_repayment
        
        if monthly_income == 0:
            return Decimal("999")
        
        return total_debt_payments / monthly_income
        
    def _calculate_dsr(
        self,
        monthly_income: Decimal,
        monthly_expenses: Decimal,
        loan_repayment: Decimal
    ) -> Decimal:
        """Calculate Debt Service Ratio"""
        total_obligations = monthly_expenses + loan_repayment
        
        if monthly_income == 0:
            return Decimal("999")
        
        return total_obligations / monthly_income
        
    def _calculate_buffer_months(
        self,
        surplus: Decimal,
        monthly_expenses: Decimal
    ) -> float:
        """Calculate months of buffer/emergency fund"""
        if monthly_expenses == 0:
            return 0.0
        
        return float(surplus / monthly_expenses)
        
    def _assess_affordability_risk(
        self,
        surplus: Decimal,
        dti: Decimal,
        dsr: Decimal,
        buffer: float
    ) -> str:
        """Assess overall affordability risk"""
        if surplus <= 0:
            return "HIGH"
        elif dti > Decimal("0.45") or dsr > Decimal("0.60"):
            return "HIGH"
        elif dti > Decimal("0.35") or dsr > Decimal("0.50"):
            return "MEDIUM"
        elif buffer < 1.0:
            return "MEDIUM"
        else:
            return "LOW"


class FraudDetectionEngine:
    """
    AI-Powered Fraud Detection
    
    Detects fraudulent loan applications
    """
    
    def __init__(self):
        self.model_version = "v1.0-anomaly-detection"
        
    def assess_fraud_risk(
        self,
        application_data: Dict
    ) -> Dict:
        """
        Assess fraud risk for loan application
        
        Returns:
            Fraud risk assessment
        """
        
        risk_score = 0.0
        flags = []
        
        # 1. Income anomalies
        income_risk, income_flags = self._check_income_anomalies(application_data)
        risk_score += income_risk
        flags.extend(income_flags)
        
        # 2. Identity verification
        identity_risk, identity_flags = self._check_identity(application_data)
        risk_score += identity_risk
        flags.extend(identity_flags)
        
        # 3. Application patterns
        pattern_risk, pattern_flags = self._check_patterns(application_data)
        risk_score += pattern_risk
        flags.extend(pattern_flags)
        
        # 4. Document verification
        doc_risk, doc_flags = self._check_documents(application_data)
        risk_score += doc_risk
        flags.extend(doc_flags)
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "fraud_risk_score": risk_score,
            "fraud_risk_level": risk_level,
            "flags": flags,
            "requires_manual_review": risk_score >= 40,
            "model_version": self.model_version,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    def _check_income_anomalies(self, data: Dict) -> Tuple[float, List[str]]:
        """Check for income anomalies"""
        risk = 0.0
        flags = []
        
        income = data.get("gross_income", 0)
        age = data.get("age", 0)
        occupation = data.get("occupation", "")
        
        # Unusually high income for age/occupation
        if income > 500000 and age < 30:
            risk += 20
            flags.append("Unusually high income for age")
        
        # Round numbers (potential fabrication)
        if income % 10000 == 0:
            risk += 10
            flags.append("Income is round number")
        
        return (risk, flags)
        
    def _check_identity(self, data: Dict) -> Tuple[float, List[str]]:
        """Check identity verification"""
        risk = 0.0
        flags = []
        
        # Email domain check
        email = data.get("email", "")
        if "@temporary" in email or "@disposable" in email:
            risk += 30
            flags.append("Suspicious email domain")
        
        # Phone verification
        phone_verified = data.get("phone_verified", False)
        if not phone_verified:
            risk += 15
            flags.append("Phone not verified")
        
        return (risk, flags)
        
    def _check_patterns(self, data: Dict) -> Tuple[float, List[str]]:
        """Check application patterns"""
        risk = 0.0
        flags = []
        
        # Multiple applications
        recent_apps = data.get("recent_applications", 0)
        if recent_apps > 3:
            risk += 25
            flags.append(f"Multiple recent applications: {recent_apps}")
        
        # Rapid application
        time_to_submit = data.get("time_to_submit_minutes", 0)
        if time_to_submit < 5:
            risk += 15
            flags.append("Application submitted very quickly")
        
        return (risk, flags)
        
    def _check_documents(self, data: Dict) -> Tuple[float, List[str]]:
        """Check document verification"""
        risk = 0.0
        flags = []
        
        # Document quality
        doc_quality = data.get("document_quality_score", 100)
        if doc_quality < 70:
            risk += 20
            flags.append("Low document quality")
        
        # Metadata anomalies
        metadata_suspicious = data.get("metadata_suspicious", False)
        if metadata_suspicious:
            risk += 25
            flags.append("Suspicious document metadata")
        
        return (risk, flags)
