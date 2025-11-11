"""
UltraCore Customer Management - KYC/AML Agent

Intelligent KYC/AML agent with:
- Document processing (OCR, data extraction)
- Identity verification (biometric matching)
- Sanctions screening (OFAC, UN, EU, DFAT)
- PEP screening (political exposure detection)
- Adverse media screening (NLP on news)
- Entity resolution (fuzzy matching)
- Risk scoring (ML-based)
- Explainable decisions (for compliance)
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
import uuid
import re

from ultracore.customers.agents.agent_base import (
    BaseAgent, AgentType, AgentTool, ToolType, AgentDecision,
    calculate_confidence, check_human_review_required
)
from ultracore.customers.core.customer_models import (
    Customer, KYCRecord, KYCStatus, DueDiligenceLevel, PEPStatus,
    Identification, IdentificationType
)
from ultracore.customers.core.customer_manager import get_customer_manager


# ============================================================================
# KYC/AML Specific Models
# ============================================================================

class ScreeningListType(str, Enum):
    """Types of screening lists"""
    SANCTIONS = "SANCTIONS"  # OFAC, UN, EU, DFAT
    PEP = "PEP"  # Politically Exposed Persons
    ADVERSE_MEDIA = "ADVERSE_MEDIA"  # Negative news
    WATCHLIST = "WATCHLIST"  # Internal watchlist
    DISQUALIFIED = "DISQUALIFIED"  # Disqualified persons (ASIC)


@dataclass
class ScreeningMatch:
    """Match from screening database"""
    match_id: str
    list_type: ScreeningListType
    list_name: str  # e.g., "OFAC SDN", "UN Sanctions", "DFAT Sanctions"
    
    # Matched entity
    entity_name: str
    entity_aliases: List[str] = field(default_factory=list)
    entity_dob: Optional[date] = None
    entity_nationality: Optional[str] = None
    entity_country: Optional[str] = None
    
    # Match details
    match_score: Decimal = Decimal('0.0')  # 0-100
    match_type: str = "EXACT"  # EXACT, FUZZY, PHONETIC
    matched_fields: List[str] = field(default_factory=list)
    
    # Additional info
    designation: Optional[str] = None  # Reason for listing
    designation_date: Optional[date] = None
    programs: List[str] = field(default_factory=list)  # Sanctions programs
    
    # Status
    false_positive: bool = False
    reviewed: bool = False
    review_notes: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DocumentAnalysis:
    """Result of document analysis"""
    document_id: str
    document_type: str  # PASSPORT, DRIVERS_LICENSE, etc.
    
    # Extracted data
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    
    # OCR confidence
    ocr_confidence: Decimal = Decimal('0.0')
    
    # Document verification
    genuine_score: Decimal = Decimal('0.0')  # 0-100
    tamper_detected: bool = False
    
    # Biometric matching (if applicable)
    face_match_score: Optional[Decimal] = None
    
    # Validation
    validation_checks: Dict[str, bool] = field(default_factory=dict)
    validation_errors: List[str] = field(default_factory=list)
    
    # Metadata
    processed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EntityResolutionResult:
    """Result of entity resolution"""
    query_entity: Dict[str, Any]
    
    # Matches found
    matches: List[Dict[str, Any]] = field(default_factory=list)
    
    # Best match
    best_match_id: Optional[str] = None
    best_match_score: Decimal = Decimal('0.0')
    
    # Duplicate detection
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    
    # Metadata
    resolution_method: str = "FUZZY_MATCHING"


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    assessment_id: str
    customer_id: str
    
    # Overall risk
    risk_score: Decimal  # 0-100
    risk_level: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    
    # Risk factors
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Scoring breakdown
    geography_score: Decimal = Decimal('0.0')
    business_score: Decimal = Decimal('0.0')
    transaction_score: Decimal = Decimal('0.0')
    relationship_score: Decimal = Decimal('0.0')
    screening_score: Decimal = Decimal('0.0')
    
    # Recommendations
    recommended_dd_level: DueDiligenceLevel = DueDiligenceLevel.STANDARD
    recommended_monitoring: str = "STANDARD"  # STANDARD, ENHANCED
    
    # Metadata
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    model_version: str = "v1.0"


# ============================================================================
# KYC/AML Agent
# ============================================================================

class KYCAMLAgent(BaseAgent):
    """
    Intelligent KYC/AML Agent
    
    Capabilities:
    1. Document processing & verification
    2. Identity verification
    3. Sanctions screening
    4. PEP screening
    5. Adverse media screening
    6. Entity resolution (duplicate detection)
    7. Risk scoring
    8. Decision making with explainability
    """
    
    def __init__(self):
        system_prompt = """You are an expert KYC/AML compliance agent.
Your role is to verify customer identity, screen against sanctions and PEP lists,
assess risk, and make compliance decisions.

You must:
- Thoroughly verify all identity documents
- Screen against all relevant lists (OFAC, UN, EU, DFAT)
- Detect potential duplicates or fraud
- Assess risk based on multiple factors
- Provide clear reasoning for all decisions
- Flag cases requiring human review

You follow Australian AML/CTF regulations (AUSTRAC) and international standards (FATF)."""

        super().__init__(
            agent_id=f"AGENT-KYC-{uuid.uuid4().hex[:8].upper()}",
            agent_type=AgentType.KYC_AML,
            agent_name="KYC/AML Compliance Agent",
            system_prompt=system_prompt
        )
        
        # Screening databases (in-memory for demo)
        self.sanctions_list: List[Dict[str, Any]] = []
        self.pep_list: List[Dict[str, Any]] = []
        self.adverse_media: List[Dict[str, Any]] = []
        
        # Screening matches
        self.screening_matches: Dict[str, List[ScreeningMatch]] = {}
        
        # Document analyses
        self.document_analyses: Dict[str, DocumentAnalysis] = {}
        
        # Risk assessments
        self.risk_assessments: Dict[str, RiskAssessment] = {}
        
        # Customer manager
        self.customer_manager = get_customer_manager()
        
        # Load screening data
        self._load_screening_data()
    
    def _register_tools(self):
        """Register KYC/AML specific tools"""
        
        # Document analysis tool
        self.register_tool(AgentTool(
            tool_id="doc_analysis",
            tool_name="analyze_document",
            tool_type=ToolType.DOCUMENT_ANALYSIS,
            description="Extract and verify data from identity documents using OCR and AI",
            parameters={
                'type': 'object',
                'properties': {
                    'document_id': {'type': 'string'},
                    'document_type': {'type': 'string', 'enum': ['PASSPORT', 'DRIVERS_LICENSE', 'NATIONAL_ID']}
                },
                'required': ['document_id', 'document_type']
            },
            function=self._analyze_document
        ))
        
        # Sanctions screening tool
        self.register_tool(AgentTool(
            tool_id="sanctions_screen",
            tool_name="screen_sanctions",
            tool_type=ToolType.API_CALL,
            description="Screen customer against sanctions lists (OFAC, UN, EU, DFAT)",
            parameters={
                'type': 'object',
                'properties': {
                    'full_name': {'type': 'string'},
                    'date_of_birth': {'type': 'string'},
                    'nationality': {'type': 'string'}
                },
                'required': ['full_name']
            },
            function=self._screen_sanctions
        ))
        
        # PEP screening tool
        self.register_tool(AgentTool(
            tool_id="pep_screen",
            tool_name="screen_pep",
            tool_type=ToolType.API_CALL,
            description="Screen for Politically Exposed Persons (PEP)",
            parameters={
                'type': 'object',
                'properties': {
                    'full_name': {'type': 'string'},
                    'country': {'type': 'string'},
                    'position': {'type': 'string'}
                },
                'required': ['full_name']
            },
            function=self._screen_pep
        ))
        
        # Adverse media screening
        self.register_tool(AgentTool(
            tool_id="adverse_media",
            tool_name="screen_adverse_media",
            tool_type=ToolType.TEXT_ANALYSIS,
            description="Screen for adverse media (negative news) using NLP",
            parameters={
                'type': 'object',
                'properties': {
                    'entity_name': {'type': 'string'},
                    'search_period_days': {'type': 'integer'}
                },
                'required': ['entity_name']
            },
            function=self._screen_adverse_media
        ))
        
        # Entity resolution
        self.register_tool(AgentTool(
            tool_id="entity_resolution",
            tool_name="resolve_entity",
            tool_type=ToolType.DATABASE_QUERY,
            description="Check for duplicate customers using fuzzy matching",
            parameters={
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'dob': {'type': 'string'},
                    'address': {'type': 'string'}
                },
                'required': ['name']
            },
            function=self._resolve_entity
        ))
        
        # Risk scoring
        self.register_tool(AgentTool(
            tool_id="risk_scoring",
            tool_name="calculate_risk_score",
            tool_type=ToolType.ML_MODEL,
            description="Calculate customer risk score using ML model",
            parameters={
                'type': 'object',
                'properties': {
                    'customer_id': {'type': 'string'}
                },
                'required': ['customer_id']
            },
            function=self._calculate_risk_score
        ))
    
    def _load_screening_data(self):
        """Load screening databases (simulated)"""
        
        # Sample sanctions list
        self.sanctions_list = [
            {
                'name': 'BLOCKED PERSON',
                'aliases': ['BP TEST'],
                'dob': '1970-01-01',
                'nationality': 'XX',
                'programs': ['OFAC SDN'],
                'designation': 'Terrorism'
            },
            # In production, load from actual databases
        ]
        
        # Sample PEP list
        self.pep_list = [
            {
                'name': 'POLITICAL FIGURE',
                'position': 'Minister',
                'country': 'TEST',
                'category': 'FOREIGN_PEP'
            },
        ]
    
    async def _make_decision(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AgentDecision:
        """
        Make KYC/AML decision
        
        Process:
        1. Analyze documents
        2. Verify identity
        3. Screen against lists
        4. Check for duplicates
        5. Assess risk
        6. Make decision
        """
        
        decision_id = f"DEC-{uuid.uuid4().hex[:12].upper()}"
        customer_id = context.get('customer_id')
        
        if not customer_id:
            raise ValueError("customer_id required in context")
        
        customer = await self.customer_manager.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Initialize reasoning
        reasoning_steps = []
        evidence = {}
        confidence_scores = []
        
        # Step 1: Analyze documents
        self.memory.add_reasoning_step("Analyzing identity documents...")
        reasoning_steps.append("Analyzing identity documents")
        
        if customer.identifications:
            doc = customer.get_primary_identification()
            if doc:
                doc_analysis = await self._analyze_document(
                    document_id=doc.identification_id,
                    document_type=doc.id_type.value
                )
                
                evidence['document_verification'] = {
                    'genuine_score': float(doc_analysis.genuine_score),
                    'ocr_confidence': float(doc_analysis.ocr_confidence)
                }
                
                confidence_scores.append(float(doc_analysis.genuine_score) / 100)
                
                if doc_analysis.genuine_score >= 80:
                    reasoning_steps.append(f"Document verification passed (score: {doc_analysis.genuine_score})")
                else:
                    reasoning_steps.append(f"Document verification concerning (score: {doc_analysis.genuine_score})")
        
        # Step 2: Screen sanctions
        self.memory.add_reasoning_step("Screening against sanctions lists...")
        reasoning_steps.append("Screening against sanctions lists (OFAC, UN, EU, DFAT)")
        
        sanctions_matches = await self._screen_sanctions(
            full_name=customer.get_full_name(),
            date_of_birth=customer.date_of_birth.isoformat() if customer.date_of_birth else None,
            nationality=customer.contact_details.email or "AU"  # Simplified
        )
        
        sanctions_hit = len(sanctions_matches) > 0
        evidence['sanctions_screening'] = {
            'matches': len(sanctions_matches),
            'hit': sanctions_hit
        }
        
        if sanctions_hit:
            reasoning_steps.append(f"⚠️ SANCTIONS HIT: {len(sanctions_matches)} match(es) found")
            confidence_scores.append(0.0)  # Zero confidence on sanctions hit
        else:
            reasoning_steps.append("✓ No sanctions matches found")
            confidence_scores.append(1.0)
        
        # Step 3: Screen PEP
        self.memory.add_reasoning_step("Screening for PEP status...")
        reasoning_steps.append("Screening for Politically Exposed Persons (PEP)")
        
        pep_matches = await self._screen_pep(
            full_name=customer.get_full_name(),
            country="AU"
        )
        
        pep_hit = len(pep_matches) > 0
        evidence['pep_screening'] = {
            'matches': len(pep_matches),
            'hit': pep_hit
        }
        
        if pep_hit:
            reasoning_steps.append(f"⚠️ PEP IDENTIFIED: {len(pep_matches)} match(es)")
            confidence_scores.append(0.5)  # Lower confidence for PEP
        else:
            reasoning_steps.append("✓ No PEP matches found")
            confidence_scores.append(1.0)
        
        # Step 4: Adverse media screening
        self.memory.add_reasoning_step("Screening adverse media...")
        reasoning_steps.append("Screening for adverse media (negative news)")
        
        adverse_media_matches = await self._screen_adverse_media(
            entity_name=customer.get_full_name(),
            search_period_days=365
        )
        
        adverse_media_hit = len(adverse_media_matches) > 0
        evidence['adverse_media'] = {
            'matches': len(adverse_media_matches),
            'hit': adverse_media_hit
        }
        
        if adverse_media_hit:
            reasoning_steps.append(f"⚠️ Adverse media found: {len(adverse_media_matches)} article(s)")
            confidence_scores.append(0.6)
        else:
            reasoning_steps.append("✓ No adverse media found")
            confidence_scores.append(1.0)
        
        # Step 5: Entity resolution (duplicate check)
        self.memory.add_reasoning_step("Checking for duplicates...")
        reasoning_steps.append("Checking for duplicate customers")
        
        entity_resolution = await self._resolve_entity(
            name=customer.get_full_name(),
            dob=customer.date_of_birth.isoformat() if customer.date_of_birth else None
        )
        
        is_duplicate = entity_resolution.is_duplicate
        evidence['duplicate_check'] = {
            'is_duplicate': is_duplicate,
            'matches': len(entity_resolution.matches)
        }
        
        if is_duplicate:
            reasoning_steps.append(f"⚠️ Potential duplicate detected (match score: {entity_resolution.best_match_score})")
            confidence_scores.append(0.7)
        else:
            reasoning_steps.append("✓ No duplicates found")
            confidence_scores.append(1.0)
        
        # Step 6: Risk assessment
        self.memory.add_reasoning_step("Calculating risk score...")
        reasoning_steps.append("Calculating overall risk score")
        
        risk_assessment = await self._calculate_risk_score(customer_id=customer_id)
        
        evidence['risk_assessment'] = {
            'risk_score': float(risk_assessment.risk_score),
            'risk_level': risk_assessment.risk_level,
            'risk_factors': len(risk_assessment.risk_factors)
        }
        
        reasoning_steps.append(f"Risk score calculated: {risk_assessment.risk_score}/100 ({risk_assessment.risk_level})")
        
        # Step 7: Make decision
        self.memory.add_reasoning_step("Making final decision...")
        
        # Calculate overall confidence
        overall_confidence = calculate_confidence(confidence_scores)
        
        # Determine decision
        if sanctions_hit:
            decision_type = "REJECT"
            decision_value = "REJECTED - Sanctions match"
            reasoning_steps.append("❌ DECISION: REJECT due to sanctions match")
        elif pep_hit and risk_assessment.risk_score > 70:
            decision_type = "ESCALATE"
            decision_value = "ESCALATE - PEP with high risk"
            reasoning_steps.append("⚠️ DECISION: ESCALATE for enhanced due diligence (PEP + High Risk)")
        elif risk_assessment.risk_score > 80:
            decision_type = "ESCALATE"
            decision_value = "ESCALATE - Very high risk"
            reasoning_steps.append("⚠️ DECISION: ESCALATE for enhanced due diligence (Very High Risk)")
        elif overall_confidence < 0.7:
            decision_type = "ESCALATE"
            decision_value = "ESCALATE - Low confidence"
            reasoning_steps.append("⚠️ DECISION: ESCALATE due to low confidence in verification")
        else:
            decision_type = "APPROVE"
            decision_value = "APPROVED - Standard due diligence"
            reasoning_steps.append("✓ DECISION: APPROVE with standard due diligence")
        
        # Check if human review required
        risk_flags = []
        if sanctions_hit:
            risk_flags.append('SANCTIONS')
        if pep_hit:
            risk_flags.append('PEP')
        if adverse_media_hit:
            risk_flags.append('ADVERSE_MEDIA')
        
        requires_review, review_reason = check_human_review_required(
            overall_confidence,
            risk_flags,
            threshold=0.8
        )
        
        # Create decision
        decision = AgentDecision(
            decision_id=decision_id,
            agent_id=self.agent_id,
            decision_type=decision_type,
            decision=decision_value,
            confidence=overall_confidence,
            reasoning=reasoning_steps,
            evidence=evidence,
            requires_human_review=requires_review,
            review_reason=review_reason,
            metadata={
                'customer_id': customer_id,
                'sanctions_hit': sanctions_hit,
                'pep_hit': pep_hit,
                'risk_score': float(risk_assessment.risk_score),
                'risk_level': risk_assessment.risk_level
            }
        )
        
        return decision
    
    async def _analyze_document(
        self,
        document_id: str,
        document_type: str
    ) -> DocumentAnalysis:
        """
        Analyze identity document using OCR and AI
        
        In production:
        - Use OCR (Tesseract, Google Vision, AWS Textract)
        - Computer vision for tamper detection
        - Biometric matching (face recognition)
        - MRZ parsing for passports
        """
        
        # Simulated analysis
        analysis = DocumentAnalysis(
            document_id=document_id,
            document_type=document_type,
            extracted_data={
                'document_number': 'N1234567',
                'name': 'JOHN DOE',
                'dob': '1990-01-01',
                'issue_date': '2020-01-01',
                'expiry_date': '2030-01-01'
            },
            ocr_confidence=Decimal('95.5'),
            genuine_score=Decimal('92.0'),
            tamper_detected=False,
            face_match_score=Decimal('88.5'),
            validation_checks={
                'format_valid': True,
                'checksum_valid': True,
                'dates_valid': True,
                'not_expired': True
            }
        )
        
        self.document_analyses[document_id] = analysis
        
        return analysis
    
    async def _screen_sanctions(
        self,
        full_name: str,
        date_of_birth: Optional[str] = None,
        nationality: Optional[str] = None
    ) -> List[ScreeningMatch]:
        """
        Screen against sanctions lists
        
        In production:
        - Query OFAC SDN list
        - Query UN Sanctions list
        - Query EU Sanctions list
        - Query DFAT (Australia) Sanctions list
        - Use fuzzy matching algorithms
        """
        
        matches = []
        
        # Fuzzy matching (simplified)
        for entry in self.sanctions_list:
            match_score = self._calculate_name_match_score(
                full_name,
                entry['name']
            )
            
            if match_score > 80:  # High threshold
                match = ScreeningMatch(
                    match_id=f"SANC-{uuid.uuid4().hex[:8].upper()}",
                    list_type=ScreeningListType.SANCTIONS,
                    list_name="OFAC SDN",
                    entity_name=entry['name'],
                    entity_aliases=entry.get('aliases', []),
                    entity_dob=date.fromisoformat(entry['dob']) if 'dob' in entry else None,
                    entity_nationality=entry.get('nationality'),
                    match_score=Decimal(str(match_score)),
                    match_type="FUZZY" if match_score < 100 else "EXACT",
                    matched_fields=['name'],
                    designation=entry.get('designation'),
                    programs=entry.get('programs', [])
                )
                matches.append(match)
        
        # Store matches
        if matches:
            if full_name not in self.screening_matches:
                self.screening_matches[full_name] = []
            self.screening_matches[full_name].extend(matches)
        
        return matches
    
    async def _screen_pep(
        self,
        full_name: str,
        country: Optional[str] = None,
        position: Optional[str] = None
    ) -> List[ScreeningMatch]:
        """
        Screen for PEP status
        
        In production:
        - Query PEP databases (Dow Jones, World-Check, etc.)
        - Check government official lists
        - Screen family members and associates
        """
        
        matches = []
        
        for entry in self.pep_list:
            match_score = self._calculate_name_match_score(
                full_name,
                entry['name']
            )
            
            if match_score > 85:
                match = ScreeningMatch(
                    match_id=f"PEP-{uuid.uuid4().hex[:8].upper()}",
                    list_type=ScreeningListType.PEP,
                    list_name="PEP Database",
                    entity_name=entry['name'],
                    entity_country=entry.get('country'),
                    match_score=Decimal(str(match_score)),
                    match_type="FUZZY" if match_score < 100 else "EXACT",
                    matched_fields=['name'],
                    designation=f"{entry.get('position', 'Official')} - {entry.get('category', 'PEP')}"
                )
                matches.append(match)
        
        return matches
    
    async def _screen_adverse_media(
        self,
        entity_name: str,
        search_period_days: int = 365
    ) -> List[ScreeningMatch]:
        """
        Screen for adverse media using NLP
        
        In production:
        - Search news databases
        - NLP sentiment analysis
        - Entity recognition
        - Category classification (fraud, corruption, etc.)
        """
        
        # Simulated adverse media screening
        matches = []
        
        # In production, query news APIs and use NLP
        # For now, return empty (no adverse media)
        
        return matches
    
    async def _resolve_entity(
        self,
        name: str,
        dob: Optional[str] = None,
        address: Optional[str] = None
    ) -> EntityResolutionResult:
        """
        Entity resolution - check for duplicates
        
        In production:
        - Fuzzy name matching (Levenshtein, Jaro-Winkler)
        - Phonetic matching (Soundex, Metaphone)
        - Address matching
        - Date of birth matching
        - ML-based entity resolution
        """
        
        # Get all customers
        all_customers = list(self.customer_manager.customers.values())
        
        matches = []
        for customer in all_customers:
            customer_name = customer.get_full_name()
            
            # Skip self
            if customer_name == name:
                continue
            
            # Calculate match score
            name_score = self._calculate_name_match_score(name, customer_name)
            
            if name_score > 70:  # Potential match
                matches.append({
                    'customer_id': customer.customer_id,
                    'name': customer_name,
                    'match_score': float(name_score),
                    'dob': customer.date_of_birth.isoformat() if customer.date_of_birth else None
                })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Determine if duplicate
        is_duplicate = False
        duplicate_of = None
        best_match_score = Decimal('0.0')
        
        if matches:
            best_match = matches[0]
            best_match_score = Decimal(str(best_match['match_score']))
            
            if best_match_score > 90:  # High confidence duplicate
                is_duplicate = True
                duplicate_of = best_match['customer_id']
        
        result = EntityResolutionResult(
            query_entity={'name': name, 'dob': dob},
            matches=matches,
            best_match_id=duplicate_of,
            best_match_score=best_match_score,
            is_duplicate=is_duplicate,
            duplicate_of=duplicate_of
        )
        
        return result
    
    async def _calculate_risk_score(
        self,
        customer_id: str
    ) -> RiskAssessment:
        """
        Calculate customer risk score using ML
        
        Factors:
        - Geography (high-risk countries)
        - Business type (high-risk industries)
        - Transaction patterns
        - Relationships
        - Screening results
        """
        
        assessment_id = f"RISK-{uuid.uuid4().hex[:12].upper()}"
        
        customer = await self.customer_manager.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        risk_factors = []
        
        # Geography risk (simplified)
        geography_score = Decimal('10.0')  # Low risk (Australia)
        
        # Business risk
        business_score = Decimal('10.0')  # Standard business
        
        # Transaction risk (placeholder)
        transaction_score = Decimal('20.0')
        
        # Relationship risk (from graph)
        relationship_score = Decimal('15.0')
        
        # Screening risk
        screening_score = Decimal('20.0')
        
        # Check for high-risk indicators
        if customer.pep_status != PEPStatus.NOT_PEP:
            risk_factors.append({
                'factor': 'PEP Status',
                'score': 30.0,
                'description': 'Customer is politically exposed'
            })
            screening_score += Decimal('30.0')
        
        if customer.sanctions_hit:
            risk_factors.append({
                'factor': 'Sanctions Hit',
                'score': 50.0,
                'description': 'Sanctions screening match'
            })
            screening_score += Decimal('50.0')
        
        # Calculate overall score (weighted average)
        total_score = (
            geography_score * Decimal('0.2') +
            business_score * Decimal('0.2') +
            transaction_score * Decimal('0.2') +
            relationship_score * Decimal('0.2') +
            screening_score * Decimal('0.2')
        )
        
        # Cap at 100
        total_score = min(total_score, Decimal('100.0'))
        
        # Determine risk level
        if total_score >= 80:
            risk_level = "VERY_HIGH"
            recommended_dd = DueDiligenceLevel.ENHANCED
        elif total_score >= 60:
            risk_level = "HIGH"
            recommended_dd = DueDiligenceLevel.ENHANCED
        elif total_score >= 40:
            risk_level = "MEDIUM"
            recommended_dd = DueDiligenceLevel.STANDARD
        else:
            risk_level = "LOW"
            recommended_dd = DueDiligenceLevel.SIMPLIFIED
        
        assessment = RiskAssessment(
            assessment_id=assessment_id,
            customer_id=customer_id,
            risk_score=total_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            geography_score=geography_score,
            business_score=business_score,
            transaction_score=transaction_score,
            relationship_score=relationship_score,
            screening_score=screening_score,
            recommended_dd_level=recommended_dd,
            recommended_monitoring="ENHANCED" if risk_level in ["HIGH", "VERY_HIGH"] else "STANDARD"
        )
        
        self.risk_assessments[assessment_id] = assessment
        
        return assessment
    
    def _calculate_name_match_score(
        self,
        name1: str,
        name2: str
    ) -> float:
        """
        Calculate name match score (0-100)
        
        In production:
        - Use Jaro-Winkler distance
        - Phonetic matching (Soundex, Metaphone)
        - Handle unicode/accents
        - Account for name variations
        """
        
        # Normalize
        name1 = name1.upper().strip()
        name2 = name2.upper().strip()
        
        # Exact match
        if name1 == name2:
            return 100.0
        
        # Simple Levenshtein-like scoring (simplified)
        if name1 in name2 or name2 in name1:
            return 90.0
        
        # Character overlap
        set1 = set(name1.replace(' ', ''))
        set2 = set(name2.replace(' ', ''))
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        return jaccard * 80.0  # Max 80 for partial match


# ============================================================================
# Global Singleton
# ============================================================================

_kyc_aml_agent: Optional[KYCAMLAgent] = None

def get_kyc_aml_agent() -> KYCAMLAgent:
    """Get singleton KYC/AML agent"""
    global _kyc_aml_agent
    if _kyc_aml_agent is None:
        _kyc_aml_agent = KYCAMLAgent()
    return _kyc_aml_agent
