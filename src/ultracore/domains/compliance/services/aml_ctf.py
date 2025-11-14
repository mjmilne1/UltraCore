"""
AML/CTF Compliance Service.

Customer risk assessment, sanctions screening, PEP checking,
and enhanced due diligence for Anti-Money Laundering and
Counter-Terrorism Financing compliance.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from ..models import (
    ComplianceCheck,
    ComplianceCheckStatus,
    CustomerRiskProfile,
    RiskLevel,
)


class SanctionsScreeningService:
    """Sanctions screening service."""
    
    # Simplified sanctions lists (in production, integrate with DFAT/UN lists)
    SANCTIONED_ENTITIES = {
        "individuals": [
            # Example entries
            {"name": "John Doe", "dob": "1970-01-01", "country": "XX"},
        ],
        "organizations": [
            # Example entries
            {"name": "Example Corp", "country": "XX"},
        ]
    }
    
    SANCTIONED_COUNTRIES = [
        "KP",  # North Korea
        "IR",  # Iran (partial sanctions)
        "SY",  # Syria
        # Add more as per Australian sanctions regime
    ]
    
    def screen_individual(
        self,
        name: str,
        date_of_birth: Optional[str] = None,
        country: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Screen individual against sanctions lists.
        
        Returns:
            (is_sanctioned, match_details) tuple
        """
        # Normalize name for comparison
        name_normalized = name.lower().strip()
        
        # Check against sanctioned individuals
        for entity in self.SANCTIONED_ENTITIES["individuals"]:
            entity_name = entity["name"].lower().strip()
            
            # Simple name matching (in production, use fuzzy matching)
            if name_normalized == entity_name:
                # Additional checks for DOB and country if provided
                if date_of_birth and entity.get("dob") != date_of_birth:
                    continue
                if country and entity.get("country") != country:
                    continue
                
                return True, {
                    "match_type": "individual",
                    "matched_entity": entity,
                    "confidence": "high"
                }
        
        return False, None
    
    def screen_organization(
        self,
        name: str,
        country: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Screen organization against sanctions lists.
        
        Returns:
            (is_sanctioned, match_details) tuple
        """
        name_normalized = name.lower().strip()
        
        # Check against sanctioned organizations
        for entity in self.SANCTIONED_ENTITIES["organizations"]:
            entity_name = entity["name"].lower().strip()
            
            if name_normalized == entity_name:
                if country and entity.get("country") != country:
                    continue
                
                return True, {
                    "match_type": "organization",
                    "matched_entity": entity,
                    "confidence": "high"
                }
        
        return False, None
    
    def check_country_sanctions(self, country_code: str) -> Tuple[bool, Optional[Dict]]:
        """Check if country is under sanctions."""
        if country_code in self.SANCTIONED_COUNTRIES:
            return True, {
                "country_code": country_code,
                "sanctions_type": "comprehensive"
            }
        
        return False, None


class PEPCheckingService:
    """Politically Exposed Person (PEP) checking service."""
    
    # Simplified PEP database (in production, integrate with commercial PEP databases)
    PEP_DATABASE = {
        # Example entries
        "John Smith": {
            "position": "Minister of Finance",
            "country": "AU",
            "start_date": "2020-01-01",
            "end_date": None,  # Current
            "risk_level": "high"
        }
    }
    
    def check_pep_status(
        self,
        name: str,
        country: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Check if individual is a Politically Exposed Person.
        
        Returns:
            (is_pep, pep_details) tuple
        """
        name_normalized = name.strip()
        
        if name_normalized in self.PEP_DATABASE:
            pep_data = self.PEP_DATABASE[name_normalized]
            
            # Check if country matches (if provided)
            if country and pep_data.get("country") != country:
                return False, None
            
            # Check if PEP status is current
            end_date = pep_data.get("end_date")
            if end_date and datetime.fromisoformat(end_date) < datetime.utcnow():
                # Former PEP (still requires monitoring for 12 months)
                return True, {
                    **pep_data,
                    "status": "former",
                    "monitoring_required": True
                }
            
            return True, {
                **pep_data,
                "status": "current",
                "monitoring_required": True
            }
        
        return False, None
    
    def is_family_member_of_pep(
        self,
        name: str,
        related_to: str
    ) -> Tuple[bool, Optional[Dict]]:
        """Check if individual is family member of PEP."""
        # Simplified check (in production, use comprehensive relationship database)
        is_pep, pep_details = self.check_pep_status(related_to)
        
        if is_pep:
            return True, {
                "relationship": "family_member",
                "pep_name": related_to,
                "pep_details": pep_details
            }
        
        return False, None


class RiskAssessmentEngine:
    """Customer risk assessment engine."""
    
    def __init__(self):
        self.sanctions_service = SanctionsScreeningService()
        self.pep_service = PEPCheckingService()
    
    def assess_customer_risk(
        self,
        customer_data: Dict,
        transaction_history: Optional[List[Dict]] = None
    ) -> Tuple[Decimal, RiskLevel, List[Dict]]:
        """
        Assess customer risk for AML/CTF compliance.
        
        Returns:
            (risk_score, risk_level, risk_factors) tuple
        """
        risk_score = Decimal("0")
        risk_factors = []
        
        # 1. Sanctions screening
        is_sanctioned, sanctions_details = self.sanctions_service.screen_individual(
            name=customer_data.get("name", ""),
            date_of_birth=customer_data.get("date_of_birth"),
            country=customer_data.get("country")
        )
        
        if is_sanctioned:
            risk_score += Decimal("100")  # Maximum risk
            risk_factors.append({
                "factor": "sanctions_match",
                "severity": "critical",
                "details": sanctions_details
            })
        
        # 2. PEP checking
        is_pep, pep_details = self.pep_service.check_pep_status(
            name=customer_data.get("name", ""),
            country=customer_data.get("country")
        )
        
        if is_pep:
            risk_score += Decimal("50")
            risk_factors.append({
                "factor": "pep_status",
                "severity": "high",
                "details": pep_details
            })
        
        # 3. Geographic risk
        country = customer_data.get("country", "")
        high_risk_countries = ["AF", "IQ", "SY", "YE", "SO"]  # Example
        
        if country in high_risk_countries:
            risk_score += Decimal("30")
            risk_factors.append({
                "factor": "high_risk_jurisdiction",
                "severity": "high",
                "details": {"country": country}
            })
        
        # 4. Transaction behavior analysis
        if transaction_history:
            tx_risk, tx_factors = self._analyze_transaction_behavior(transaction_history)
            risk_score += tx_risk
            risk_factors.extend(tx_factors)
        
        # 5. Customer profile factors
        profile_risk, profile_factors = self._analyze_customer_profile(customer_data)
        risk_score += profile_risk
        risk_factors.extend(profile_factors)
        
        # Cap risk score at 100
        risk_score = min(risk_score, Decimal("100"))
        
        # Determine risk level
        if risk_score >= 75:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 50:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return risk_score, risk_level, risk_factors
    
    def _analyze_transaction_behavior(
        self,
        transaction_history: List[Dict]
    ) -> Tuple[Decimal, List[Dict]]:
        """Analyze transaction behavior for risk indicators."""
        risk_score = Decimal("0")
        risk_factors = []
        
        if not transaction_history:
            return risk_score, risk_factors
        
        # Calculate transaction statistics
        amounts = [Decimal(str(tx.get("amount", 0))) for tx in transaction_history]
        avg_amount = sum(amounts) / len(amounts) if amounts else Decimal("0")
        max_amount = max(amounts) if amounts else Decimal("0")
        
        # High average transaction amount
        if avg_amount > Decimal("50000"):
            risk_score += Decimal("15")
            risk_factors.append({
                "factor": "high_average_amount",
                "severity": "medium",
                "details": {"average_amount": float(avg_amount)}
            })
        
        # Very large single transaction
        if max_amount > Decimal("100000"):
            risk_score += Decimal("20")
            risk_factors.append({
                "factor": "large_transaction",
                "severity": "high",
                "details": {"max_amount": float(max_amount)}
            })
        
        # High transaction frequency
        if len(transaction_history) > 100:
            risk_score += Decimal("10")
            risk_factors.append({
                "factor": "high_frequency",
                "severity": "low",
                "details": {"transaction_count": len(transaction_history)}
            })
        
        return risk_score, risk_factors
    
    def _analyze_customer_profile(self, customer_data: Dict) -> Tuple[Decimal, List[Dict]]:
        """Analyze customer profile for risk indicators."""
        risk_score = Decimal("0")
        risk_factors = []
        
        # Cash-intensive business
        business_type = customer_data.get("business_type", "")
        cash_intensive_businesses = [
            "money_service_business",
            "casino",
            "real_estate",
            "jewelry",
            "car_dealer"
        ]
        
        if business_type in cash_intensive_businesses:
            risk_score += Decimal("20")
            risk_factors.append({
                "factor": "cash_intensive_business",
                "severity": "medium",
                "details": {"business_type": business_type}
            })
        
        # Complex ownership structure
        if customer_data.get("complex_ownership", False):
            risk_score += Decimal("15")
            risk_factors.append({
                "factor": "complex_ownership",
                "severity": "medium",
                "details": {}
            })
        
        return risk_score, risk_factors


class AMLCTFService:
    """
    AML/CTF Compliance Service.
    
    Manages customer risk assessment, sanctions screening,
    and enhanced due diligence.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.risk_engine = RiskAssessmentEngine()
        self.sanctions_service = SanctionsScreeningService()
        self.pep_service = PEPCheckingService()
    
    def perform_customer_screening(
        self,
        customer_id: str,
        customer_data: Dict,
        transaction_history: Optional[List[Dict]] = None
    ) -> ComplianceCheck:
        """
        Perform comprehensive customer screening.
        
        Args:
            customer_id: Customer identifier
            customer_data: Customer information
            transaction_history: Optional transaction history
        
        Returns:
            ComplianceCheck result
        """
        # Create compliance check
        check = ComplianceCheck(
            tenant_id=self.tenant_id,
            subject_type="customer",
            subject_id=customer_id,
            check_type="aml_ctf_screening",
            performed_by="system"
        )
        
        check.start_check()
        
        # Perform risk assessment
        risk_score, risk_level, risk_factors = self.risk_engine.assess_customer_risk(
            customer_data=customer_data,
            transaction_history=transaction_history
        )
        
        # Determine if check passed
        passed = risk_level not in [RiskLevel.CRITICAL]
        
        # Complete check
        check.complete_check(
            passed=passed,
            risk_level=risk_level,
            risk_score=risk_score,
            findings=risk_factors
        )
        
        # Add recommendations
        if risk_level == RiskLevel.CRITICAL:
            check.recommendations.append("Block customer - Critical risk detected")
            check.recommendations.append("Escalate to compliance officer immediately")
        elif risk_level == RiskLevel.HIGH:
            check.recommendations.append("Enhanced due diligence required")
            check.recommendations.append("Ongoing monitoring required")
        elif risk_level == RiskLevel.MEDIUM:
            check.recommendations.append("Standard monitoring required")
        
        return check
    
    def create_customer_risk_profile(
        self,
        customer_id: str,
        customer_data: Dict,
        transaction_history: Optional[List[Dict]] = None
    ) -> CustomerRiskProfile:
        """Create or update customer risk profile."""
        # Perform risk assessment
        risk_score, risk_level, risk_factors = self.risk_engine.assess_customer_risk(
            customer_data=customer_data,
            transaction_history=transaction_history
        )
        
        # Create profile
        profile = CustomerRiskProfile(
            tenant_id=self.tenant_id,
            customer_id=customer_id,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            country_of_residence=customer_data.get("country", "")
        )
        
        # Check PEP status
        is_pep, pep_details = self.pep_service.check_pep_status(
            name=customer_data.get("name", ""),
            country=customer_data.get("country")
        )
        
        if is_pep:
            profile.mark_as_pep(pep_details)
        
        # Check sanctions
        is_sanctioned, sanctions_details = self.sanctions_service.screen_individual(
            name=customer_data.get("name", ""),
            date_of_birth=customer_data.get("date_of_birth"),
            country=customer_data.get("country")
        )
        
        if is_sanctioned:
            profile.mark_as_sanctioned(sanctions_details)
        
        # Calculate transaction statistics
        if transaction_history:
            amounts = [Decimal(str(tx.get("amount", 0))) for tx in transaction_history]
            profile.average_transaction_amount = (
                sum(amounts) / len(amounts) if amounts else Decimal("0")
            )
            profile.transaction_frequency = len(transaction_history)
        
        # Set review schedule
        if profile.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            # High risk: review every 3 months
            profile.next_review_due = datetime.utcnow() + timedelta(days=90)
        elif profile.risk_level == RiskLevel.MEDIUM:
            # Medium risk: review every 6 months
            profile.next_review_due = datetime.utcnow() + timedelta(days=180)
        else:
            # Low risk: review annually
            profile.next_review_due = datetime.utcnow() + timedelta(days=365)
        
        return profile
    
    def perform_enhanced_due_diligence(
        self,
        customer_id: str,
        customer_data: Dict,
        additional_info: Dict
    ) -> ComplianceCheck:
        """
        Perform enhanced due diligence for high-risk customers.
        
        Args:
            customer_id: Customer identifier
            customer_data: Customer information
            additional_info: Additional EDD information
        
        Returns:
            ComplianceCheck result
        """
        check = ComplianceCheck(
            tenant_id=self.tenant_id,
            subject_type="customer",
            subject_id=customer_id,
            check_type="enhanced_due_diligence",
            performed_by=additional_info.get("performed_by", "system")
        )
        
        check.start_check()
        
        findings = []
        
        # 1. Source of wealth verification
        if "source_of_wealth" in additional_info:
            findings.append({
                "check": "source_of_wealth",
                "verified": additional_info.get("source_of_wealth_verified", False),
                "details": additional_info.get("source_of_wealth")
            })
        
        # 2. Source of funds verification
        if "source_of_funds" in additional_info:
            findings.append({
                "check": "source_of_funds",
                "verified": additional_info.get("source_of_funds_verified", False),
                "details": additional_info.get("source_of_funds")
            })
        
        # 3. Purpose of account
        if "account_purpose" in additional_info:
            findings.append({
                "check": "account_purpose",
                "verified": True,
                "details": additional_info.get("account_purpose")
            })
        
        # 4. Expected transaction activity
        if "expected_activity" in additional_info:
            findings.append({
                "check": "expected_activity",
                "details": additional_info.get("expected_activity")
            })
        
        # Determine if EDD passed
        all_verified = all(
            finding.get("verified", True)
            for finding in findings
        )
        
        passed = all_verified and len(findings) >= 3  # Require at least 3 checks
        
        check.complete_check(
            passed=passed,
            risk_level=RiskLevel.HIGH if passed else RiskLevel.CRITICAL,
            risk_score=Decimal("50") if passed else Decimal("75"),
            findings=findings
        )
        
        if passed:
            check.recommendations.append("EDD completed successfully")
            check.recommendations.append("Ongoing enhanced monitoring required")
        else:
            check.recommendations.append("EDD incomplete - additional information required")
            check.recommendations.append("Consider account restrictions until EDD completed")
        
        return check
    
    def schedule_ongoing_monitoring(
        self,
        customer_id: str,
        risk_level: RiskLevel
    ) -> datetime:
        """Schedule next monitoring review based on risk level."""
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            # High risk: monitor every 3 months
            return datetime.utcnow() + timedelta(days=90)
        elif risk_level == RiskLevel.MEDIUM:
            # Medium risk: monitor every 6 months
            return datetime.utcnow() + timedelta(days=180)
        else:
            # Low risk: monitor annually
            return datetime.utcnow() + timedelta(days=365)
