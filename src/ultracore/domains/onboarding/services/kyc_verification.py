"""
KYC Verification Service.

Identity verification and Know Your Customer compliance.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from ..models import (
    IdentityVerificationMethod,
    KYCVerification,
    VerificationStatus,
)


class DocumentVerificationEngine:
    """Document verification engine."""
    
    def verify_passport(self, document_data: Dict) -> Tuple[bool, Decimal, Dict]:
        """
        Verify passport document.
        
        Returns:
            (is_valid, confidence_score, extracted_data) tuple
        """
        # Mock implementation - in production, integrate with OCR and document verification service
        extracted_data = {
            "document_number": document_data.get("document_number", ""),
            "full_name": document_data.get("full_name", ""),
            "date_of_birth": document_data.get("date_of_birth", ""),
            "nationality": document_data.get("nationality", ""),
            "expiry_date": document_data.get("expiry_date", ""),
            "issuing_country": document_data.get("issuing_country", "")
        }
        
        # Validation checks
        checks = []
        
        # Check if all required fields present
        required_fields = ["document_number", "full_name", "date_of_birth", "nationality"]
        all_fields_present = all(extracted_data.get(field) for field in required_fields)
        checks.append(("required_fields", all_fields_present))
        
        # Check document not expired
        expiry_date = extracted_data.get("expiry_date")
        not_expired = True
        if expiry_date:
            try:
                expiry = datetime.fromisoformat(expiry_date)
                not_expired = expiry > datetime.utcnow()
            except ValueError:
                not_expired = False
        checks.append(("not_expired", not_expired))
        
        # Check document authenticity (mock - in production, check security features)
        is_authentic = True  # Mock check
        checks.append(("authentic", is_authentic))
        
        # Calculate confidence score
        passed_checks = sum(1 for _, passed in checks if passed)
        confidence_score = Decimal(str(passed_checks / len(checks)))
        
        is_valid = all(passed for _, passed in checks)
        
        return is_valid, confidence_score, extracted_data
    
    def verify_drivers_license(self, document_data: Dict) -> Tuple[bool, Decimal, Dict]:
        """Verify driver's license."""
        extracted_data = {
            "license_number": document_data.get("license_number", ""),
            "full_name": document_data.get("full_name", ""),
            "date_of_birth": document_data.get("date_of_birth", ""),
            "address": document_data.get("address", ""),
            "expiry_date": document_data.get("expiry_date", ""),
            "issuing_state": document_data.get("issuing_state", "")
        }
        
        # Similar validation as passport
        required_fields = ["license_number", "full_name", "date_of_birth", "address"]
        all_fields_present = all(extracted_data.get(field) for field in required_fields)
        
        expiry_date = extracted_data.get("expiry_date")
        not_expired = True
        if expiry_date:
            try:
                expiry = datetime.fromisoformat(expiry_date)
                not_expired = expiry > datetime.utcnow()
            except ValueError:
                not_expired = False
        
        checks = [
            ("required_fields", all_fields_present),
            ("not_expired", not_expired),
            ("authentic", True)  # Mock
        ]
        
        passed_checks = sum(1 for _, passed in checks if passed)
        confidence_score = Decimal(str(passed_checks / len(checks)))
        is_valid = all(passed for _, passed in checks)
        
        return is_valid, confidence_score, extracted_data
    
    def verify_proof_of_address(self, document_data: Dict) -> Tuple[bool, Decimal, Dict]:
        """Verify proof of address document."""
        extracted_data = {
            "document_type": document_data.get("document_type", ""),  # utility_bill, bank_statement, etc.
            "full_name": document_data.get("full_name", ""),
            "address": document_data.get("address", ""),
            "document_date": document_data.get("document_date", ""),
            "issuer": document_data.get("issuer", "")
        }
        
        # Validation checks
        required_fields = ["full_name", "address", "document_date"]
        all_fields_present = all(extracted_data.get(field) for field in required_fields)
        
        # Check document is recent (within 3 months)
        document_date = extracted_data.get("document_date")
        is_recent = False
        if document_date:
            try:
                doc_date = datetime.fromisoformat(document_date)
                days_old = (datetime.utcnow() - doc_date).days
                is_recent = days_old <= 90  # 3 months
            except ValueError:
                is_recent = False
        
        checks = [
            ("required_fields", all_fields_present),
            ("recent", is_recent),
            ("authentic", True)  # Mock
        ]
        
        passed_checks = sum(1 for _, passed in checks if passed)
        confidence_score = Decimal(str(passed_checks / len(checks)))
        is_valid = all(passed for _, passed in checks)
        
        return is_valid, confidence_score, extracted_data


class BiometricVerificationEngine:
    """Biometric verification engine."""
    
    def verify_face_match(
        self,
        document_photo: str,
        selfie_photo: str
    ) -> Tuple[bool, Decimal]:
        """
        Verify face match between document and selfie.
        
        Args:
            document_photo: Path/URL to document photo
            selfie_photo: Path/URL to selfie photo
        
        Returns:
            (is_match, confidence_score) tuple
        """
        # Mock implementation - in production, integrate with face recognition service
        # (e.g., AWS Rekognition, Azure Face API, or custom ML model)
        
        # Simulate face matching
        confidence_score = Decimal("0.95")  # Mock high confidence
        is_match = confidence_score >= Decimal("0.85")
        
        return is_match, confidence_score
    
    def verify_liveness(self, video_path: str) -> Tuple[bool, Decimal]:
        """
        Verify liveness (detect if real person, not photo/video).
        
        Args:
            video_path: Path/URL to liveness video
        
        Returns:
            (is_live, confidence_score) tuple
        """
        # Mock implementation - in production, integrate with liveness detection service
        confidence_score = Decimal("0.92")
        is_live = confidence_score >= Decimal("0.80")
        
        return is_live, confidence_score


class ThirdPartyVerificationService:
    """Third-party verification service integration."""
    
    def verify_with_provider(
        self,
        provider: str,
        customer_data: Dict
    ) -> Tuple[bool, Dict]:
        """
        Verify identity using third-party provider.
        
        Providers: Onfido, Jumio, Trulioo, etc.
        
        Args:
            provider: Provider name
            customer_data: Customer information
        
        Returns:
            (is_verified, response_data) tuple
        """
        # Mock implementation - in production, integrate with actual providers
        
        if provider == "onfido":
            return self._verify_onfido(customer_data)
        elif provider == "jumio":
            return self._verify_jumio(customer_data)
        elif provider == "trulioo":
            return self._verify_trulioo(customer_data)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _verify_onfido(self, customer_data: Dict) -> Tuple[bool, Dict]:
        """Mock Onfido verification."""
        response = {
            "provider": "onfido",
            "check_id": "onfido_check_123",
            "status": "complete",
            "result": "clear",
            "sub_results": {
                "document": "clear",
                "facial_similarity": "clear",
                "identity_report": "clear"
            },
            "confidence": 0.95
        }
        
        is_verified = response["result"] == "clear"
        return is_verified, response
    
    def _verify_jumio(self, customer_data: Dict) -> Tuple[bool, Dict]:
        """Mock Jumio verification."""
        response = {
            "provider": "jumio",
            "transaction_reference": "jumio_tx_456",
            "status": "APPROVED_VERIFIED",
            "identity_verification": {
                "similarity": "MATCH",
                "validity": True
            },
            "confidence": 0.93
        }
        
        is_verified = response["status"] == "APPROVED_VERIFIED"
        return is_verified, response
    
    def _verify_trulioo(self, customer_data: Dict) -> Tuple[bool, Dict]:
        """Mock Trulioo verification."""
        response = {
            "provider": "trulioo",
            "transaction_id": "trulioo_789",
            "record_status": "match",
            "datasource_results": [
                {
                    "datasource_name": "Australian Passport",
                    "datasource_fields": [
                        {"field_name": "FirstName", "status": "match"},
                        {"field_name": "LastName", "status": "match"},
                        {"field_name": "DateOfBirth", "status": "match"}
                    ]
                }
            ],
            "confidence": 0.91
        }
        
        is_verified = response["record_status"] == "match"
        return is_verified, response


class KYCVerificationService:
    """
    KYC Verification Service.
    
    Manages identity verification process.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.document_engine = DocumentVerificationEngine()
        self.biometric_engine = BiometricVerificationEngine()
        self.third_party_service = ThirdPartyVerificationService()
    
    def create_verification(
        self,
        onboarding_id: str,
        customer_data: Dict,
        method: IdentityVerificationMethod = IdentityVerificationMethod.DOCUMENT_VERIFICATION
    ) -> KYCVerification:
        """Create KYC verification."""
        verification = KYCVerification(
            tenant_id=self.tenant_id,
            onboarding_id=onboarding_id,
            method=method,
            provided_name=customer_data.get("full_name", ""),
            provided_date_of_birth=customer_data.get("date_of_birth"),
            provided_address=customer_data.get("address", {}),
            provided_nationality=customer_data.get("nationality", "")
        )
        
        return verification
    
    def verify_with_documents(
        self,
        verification: KYCVerification,
        documents: List[Dict]
    ) -> KYCVerification:
        """
        Verify identity using documents.
        
        Args:
            verification: KYC verification instance
            documents: List of document data
        
        Returns:
            Updated verification
        """
        verification.start_verification()
        
        identity_confirmed = False
        address_confirmed = False
        date_of_birth_confirmed = False
        confidence_scores = []
        
        # Process each document
        for doc in documents:
            doc_type = doc.get("document_type")
            
            if doc_type == "passport":
                is_valid, confidence, extracted = self.document_engine.verify_passport(doc)
                confidence_scores.append(confidence)
                
                if is_valid:
                    # Check if extracted data matches provided data
                    if extracted.get("full_name", "").lower() == verification.provided_name.lower():
                        identity_confirmed = True
                    if extracted.get("date_of_birth") == verification.provided_date_of_birth:
                        date_of_birth_confirmed = True
            
            elif doc_type == "drivers_license":
                is_valid, confidence, extracted = self.document_engine.verify_drivers_license(doc)
                confidence_scores.append(confidence)
                
                if is_valid:
                    if extracted.get("full_name", "").lower() == verification.provided_name.lower():
                        identity_confirmed = True
                    if extracted.get("date_of_birth") == verification.provided_date_of_birth:
                        date_of_birth_confirmed = True
                    # Driver's license has address
                    address_confirmed = True
            
            elif doc_type in ["utility_bill", "bank_statement"]:
                is_valid, confidence, extracted = self.document_engine.verify_proof_of_address(doc)
                confidence_scores.append(confidence)
                
                if is_valid:
                    address_confirmed = True
        
        # Calculate overall confidence
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
        else:
            avg_confidence = Decimal("0")
        
        # Complete verification
        verification.verify(
            identity_confirmed=identity_confirmed,
            address_confirmed=address_confirmed,
            date_of_birth_confirmed=date_of_birth_confirmed,
            confidence_score=avg_confidence
        )
        
        return verification
    
    def verify_with_biometrics(
        self,
        verification: KYCVerification,
        document_photo: str,
        selfie_photo: str,
        liveness_video: Optional[str] = None
    ) -> KYCVerification:
        """
        Verify identity using biometrics.
        
        Args:
            verification: KYC verification instance
            document_photo: Path/URL to document photo
            selfie_photo: Path/URL to selfie photo
            liveness_video: Optional liveness video
        
        Returns:
            Updated verification
        """
        verification.start_verification()
        
        # Face matching
        is_match, face_confidence = self.biometric_engine.verify_face_match(
            document_photo=document_photo,
            selfie_photo=selfie_photo
        )
        
        # Liveness detection
        liveness_confidence = Decimal("1.0")
        if liveness_video:
            is_live, liveness_confidence = self.biometric_engine.verify_liveness(liveness_video)
            if not is_live:
                verification.fail("Liveness check failed")
                return verification
        
        # Calculate overall confidence
        confidence_score = (face_confidence + liveness_confidence) / Decimal("2")
        
        # Complete verification
        verification.verify(
            identity_confirmed=is_match,
            address_confirmed=False,  # Biometrics don't verify address
            date_of_birth_confirmed=False,  # Biometrics don't verify DOB
            confidence_score=confidence_score
        )
        
        return verification
    
    def verify_with_third_party(
        self,
        verification: KYCVerification,
        provider: str,
        customer_data: Dict
    ) -> KYCVerification:
        """
        Verify identity using third-party service.
        
        Args:
            verification: KYC verification instance
            provider: Provider name (onfido, jumio, trulioo)
            customer_data: Customer information
        
        Returns:
            Updated verification
        """
        verification.start_verification()
        verification.third_party_provider = provider
        
        try:
            is_verified, response = self.third_party_service.verify_with_provider(
                provider=provider,
                customer_data=customer_data
            )
            
            verification.third_party_response = response
            verification.third_party_reference = response.get("check_id") or response.get("transaction_reference") or response.get("transaction_id")
            
            if is_verified:
                confidence_score = Decimal(str(response.get("confidence", 0.9)))
                
                verification.verify(
                    identity_confirmed=True,
                    address_confirmed=True,  # Third-party services typically verify address
                    date_of_birth_confirmed=True,
                    confidence_score=confidence_score
                )
            else:
                verification.fail(
                    reason="Third-party verification failed",
                    details=response
                )
        
        except Exception as e:
            verification.fail(
                reason=f"Third-party verification error: {str(e)}",
                details={}
            )
        
        return verification
    
    def perform_manual_review(
        self,
        verification: KYCVerification,
        reviewer_id: str,
        approved: bool,
        notes: str
    ) -> KYCVerification:
        """Perform manual review of verification."""
        verification.complete_manual_review(
            reviewer_id=reviewer_id,
            approved=approved,
            notes=notes
        )
        
        return verification
    
    def get_verification_requirements(
        self,
        customer_type: str,
        risk_level: str
    ) -> Dict:
        """
        Get verification requirements based on customer type and risk level.
        
        Args:
            customer_type: individual or business
            risk_level: low, medium, high
        
        Returns:
            Verification requirements
        """
        requirements = {
            "documents_required": [],
            "verification_methods": [],
            "additional_checks": []
        }
        
        # Base requirements for individuals
        if customer_type == "individual":
            requirements["documents_required"].extend([
                "government_id",  # Passport or driver's license
                "proof_of_address"
            ])
            requirements["verification_methods"].append("document_verification")
        
        # Additional requirements based on risk level
        if risk_level in ["high", "very_high"]:
            requirements["verification_methods"].append("biometric_verification")
            requirements["additional_checks"].extend([
                "enhanced_due_diligence",
                "source_of_funds",
                "source_of_wealth"
            ])
        
        # Business requirements
        if customer_type == "business":
            requirements["documents_required"].extend([
                "business_registration",
                "beneficial_ownership",
                "financial_statements"
            ])
            requirements["additional_checks"].append("business_verification")
        
        return requirements
