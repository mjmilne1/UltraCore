"""
UltraCore Loan Management - Underwriting Engine

Comprehensive underwriting and credit decision system:
- Automated credit assessment
- Affordability calculations
- Risk scoring
- Policy rules engine
- Credit bureau integration
- Approval workflow
- Exception management
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import asyncio

from ultracore.lending.origination.loan_application import (
    get_application_manager, LoanApplication, ApplicationStatus,
    LoanProductType, EmploymentType
)
from ultracore.audit.audit_core import (
    get_audit_store, AuditEventType, AuditCategory, AuditSeverity
)


# ============================================================================
# Underwriting Enums
# ============================================================================

class CreditGrade(str, Enum):
    """Credit grade classification"""
    AAA = "AAA"  # Excellent
    AA = "AA"    # Very Good
    A = "A"      # Good
    BBB = "BBB"  # Fair
    BB = "BB"    # Below Average
    B = "B"      # Poor
    CCC = "CCC"  # Very Poor
    D = "D"      # Default


class RiskRating(str, Enum):
    """Risk rating classification"""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    UNACCEPTABLE = "UNACCEPTABLE"


class DecisionType(str, Enum):
    """Underwriting decision types"""
    AUTO_APPROVE = "AUTO_APPROVE"
    AUTO_DECLINE = "AUTO_DECLINE"
    REFER_TO_UNDERWRITER = "REFER_TO_UNDERWRITER"
    CONDITIONAL_APPROVE = "CONDITIONAL_APPROVE"


class PolicyRuleType(str, Enum):
    """Types of policy rules"""
    MANDATORY = "MANDATORY"  # Must pass
    DISCRETIONARY = "DISCRETIONARY"  # Can be overridden
    GUIDELINE = "GUIDELINE"  # Informational only


class AffordabilityMethod(str, Enum):
    """Affordability calculation methods"""
    NET_INCOME = "NET_INCOME"  # Based on net income
    GROSS_INCOME = "GROSS_INCOME"  # Based on gross income
    HEM = "HEM"  # Household Expenditure Measure (ASIC)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class CreditBureauResponse:
    """Credit bureau check response"""
    bureau_reference: str
    check_date: datetime
    
    # Credit score
    credit_score: Optional[int] = None  # 0-1200 (Equifax scale)
    credit_grade: Optional[CreditGrade] = None
    
    # Credit history
    number_of_enquiries_6m: int = 0
    number_of_enquiries_12m: int = 0
    number_of_defaults: int = 0
    total_default_amount: Decimal = Decimal('0.00')
    
    # Accounts
    number_of_accounts: int = 0
    total_credit_limit: Decimal = Decimal('0.00')
    total_outstanding: Decimal = Decimal('0.00')
    
    # Payment history
    number_of_late_payments: int = 0
    worst_payment_status: Optional[str] = None
    
    # Adverse events
    bankruptcies: int = 0
    court_judgements: int = 0
    part_ix_agreements: int = 0
    
    # Risk indicators
    high_risk_flags: List[str] = field(default_factory=list)
    
    # Raw response
    raw_response: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyRule:
    """Individual policy rule"""
    rule_id: str
    rule_name: str
    rule_type: PolicyRuleType
    
    # Rule definition
    description: str
    rule_logic: str  # Python expression or rule
    
    # Parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    active: bool = True
    
    # Applies to
    product_types: List[LoanProductType] = field(default_factory=list)
    
    # Created
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PolicyRuleResult:
    """Result of policy rule evaluation"""
    rule_id: str
    rule_name: str
    rule_type: PolicyRuleType
    
    # Result
    passed: bool
    actual_value: Any
    threshold_value: Any
    
    # Message
    message: str
    
    # Override
    can_override: bool = False
    overridden: bool = False
    override_reason: Optional[str] = None
    override_by: Optional[str] = None


@dataclass
class AffordabilityAssessment:
    """Affordability calculation result"""
    assessment_id: str
    application_id: str
    
    # Method
    method: AffordabilityMethod
    
    # Income
    gross_monthly_income: Decimal
    net_monthly_income: Decimal
    
    # Expenses
    living_expenses: Decimal
    existing_debt_repayments: Decimal
    proposed_loan_repayment: Decimal
    
    # Calculations
    total_expenses: Decimal
    surplus_income: Decimal
    net_disposable_income: Decimal
    
    # Ratios
    debt_service_ratio: Decimal  # (Total debt / Gross income) * 100
    net_surplus_ratio: Decimal  # (Surplus / Net income) * 100
    
    # Assessment
    affordable: bool
    maximum_affordable_amount: Optional[Decimal] = None
    
    # Buffer
    stress_test_rate: Decimal = Decimal('7.00')  # APRA buffer
    stressed_repayment: Decimal = Decimal('0.00')
    stressed_affordable: bool = False
    
    # Comments
    comments: List[str] = field(default_factory=list)
    
    # Metadata
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    assessed_by: Optional[str] = None


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    assessment_id: str
    application_id: str
    
    # Scores
    credit_score: Optional[int] = None
    behavior_score: Optional[int] = None
    application_score: Optional[int] = None
    combined_score: Decimal = Decimal('0.00')
    
    # Ratings
    credit_grade: Optional[CreditGrade] = None
    risk_rating: RiskRating = RiskRating.MODERATE
    
    # Key metrics
    ltv_ratio: Optional[Decimal] = None
    dti_ratio: Decimal = Decimal('0.00')
    dsr_ratio: Decimal = Decimal('0.00')
    
    # Risk factors
    positive_factors: List[str] = field(default_factory=list)
    negative_factors: List[str] = field(default_factory=list)
    
    # Probability
    probability_of_default: Optional[Decimal] = None  # %
    expected_loss: Optional[Decimal] = None
    
    # Decision
    risk_acceptable: bool = False
    
    # Metadata
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    assessed_by: Optional[str] = None


@dataclass
class UnderwritingDecision:
    """Complete underwriting decision"""
    decision_id: str
    application_id: str
    
    # Decision
    decision_type: DecisionType
    approved: bool = False
    
    # Approved terms (if approved)
    approved_amount: Optional[Decimal] = None
    approved_term_months: Optional[int] = None
    approved_rate: Optional[Decimal] = None
    
    # Decline reason (if declined)
    decline_reasons: List[str] = field(default_factory=list)
    
    # Conditions (if conditional)
    conditions: List[str] = field(default_factory=list)
    
    # Assessments
    affordability: Optional[AffordabilityAssessment] = None
    risk: Optional[RiskAssessment] = None
    credit_bureau: Optional[CreditBureauResponse] = None
    
    # Policy compliance
    policy_results: List[PolicyRuleResult] = field(default_factory=list)
    policy_compliant: bool = True
    
    # Referral
    refer_to_manager: bool = False
    referral_reasons: List[str] = field(default_factory=list)
    
    # Decision maker
    decided_by: str = "SYSTEM"
    decision_type_used: str = "AUTOMATED"  # AUTOMATED, MANUAL, HYBRID
    
    # Timestamps
    decision_date: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Credit Bureau Service
# ============================================================================

class CreditBureauService:
    """
    Credit bureau integration service
    Integrates with Equifax, Experian, etc.
    """
    
    def __init__(self):
        self.enabled = True
        self.cache: Dict[str, CreditBureauResponse] = {}
    
    async def check_credit(
        self,
        applicant_name: str,
        date_of_birth: date,
        address: str,
        consent_given: bool
    ) -> CreditBureauResponse:
        """
        Perform credit bureau check
        In production, would integrate with Equifax/Experian API
        """
        
        if not consent_given:
            raise ValueError("Credit check consent not provided")
        
        # Generate reference
        bureau_ref = f"CBR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        # In production, would call actual bureau API
        # For now, return simulated response
        
        # Simulate credit score (300-850 is common, but Equifax uses 0-1200)
        # Using 0-1200 scale
        simulated_score = 750  # Good score
        
        response = CreditBureauResponse(
            bureau_reference=bureau_ref,
            check_date=datetime.now(timezone.utc),
            credit_score=simulated_score,
            credit_grade=self._score_to_grade(simulated_score),
            number_of_enquiries_6m=2,
            number_of_enquiries_12m=4,
            number_of_defaults=0,
            total_default_amount=Decimal('0.00'),
            number_of_accounts=3,
            total_credit_limit=Decimal('25000.00'),
            total_outstanding=Decimal('5000.00'),
            number_of_late_payments=0,
            bankruptcies=0,
            court_judgements=0,
            part_ix_agreements=0
        )
        
        # Cache response
        cache_key = f"{applicant_name}_{date_of_birth.isoformat()}"
        self.cache[cache_key] = response
        
        return response
    
    def _score_to_grade(self, score: int) -> CreditGrade:
        """Convert credit score to grade"""
        if score >= 900:
            return CreditGrade.AAA
        elif score >= 800:
            return CreditGrade.AA
        elif score >= 700:
            return CreditGrade.A
        elif score >= 600:
            return CreditGrade.BBB
        elif score >= 500:
            return CreditGrade.BB
        elif score >= 400:
            return CreditGrade.B
        elif score >= 300:
            return CreditGrade.CCC
        else:
            return CreditGrade.D


# ============================================================================
# Policy Rules Engine
# ============================================================================

class PolicyRulesEngine:
    """
    Policy rules engine
    Evaluates lending policy rules
    """
    
    def __init__(self):
        self.rules: Dict[str, PolicyRule] = {}
        self._initialize_standard_rules()
    
    def _initialize_standard_rules(self):
        """Initialize standard lending policy rules"""
        
        # Age requirements
        self.add_rule(PolicyRule(
            rule_id="AGE_MIN",
            rule_name="Minimum Age",
            rule_type=PolicyRuleType.MANDATORY,
            description="Applicant must be at least 18 years old",
            rule_logic="age >= 18",
            parameters={'min_age': 18}
        ))
        
        # Income requirements
        self.add_rule(PolicyRule(
            rule_id="MIN_INCOME",
            rule_name="Minimum Income",
            rule_type=PolicyRuleType.MANDATORY,
            description="Minimum annual income requirement",
            rule_logic="income >= 30000",
            parameters={'min_income': 30000}
        ))
        
        # Credit score
        self.add_rule(PolicyRule(
            rule_id="MIN_CREDIT_SCORE",
            rule_name="Minimum Credit Score",
            rule_type=PolicyRuleType.DISCRETIONARY,
            description="Minimum credit score for approval",
            rule_logic="credit_score >= 600",
            parameters={'min_score': 600}
        ))
        
        # LTV limits
        self.add_rule(PolicyRule(
            rule_id="MAX_LTV",
            rule_name="Maximum LTV Ratio",
            rule_type=PolicyRuleType.MANDATORY,
            description="Maximum loan-to-value ratio",
            rule_logic="ltv <= 80",
            parameters={'max_ltv': 80},
            product_types=[LoanProductType.HOME_LOAN]
        ))
        
        # DTI limits
        self.add_rule(PolicyRule(
            rule_id="MAX_DTI",
            rule_name="Maximum Debt-to-Income",
            rule_type=PolicyRuleType.DISCRETIONARY,
            description="Maximum debt-to-income ratio",
            rule_logic="dti <= 40",
            parameters={'max_dti': 40}
        ))
        
        # Defaults
        self.add_rule(PolicyRule(
            rule_id="NO_DEFAULTS",
            rule_name="No Payment Defaults",
            rule_type=PolicyRuleType.MANDATORY,
            description="No payment defaults in last 5 years",
            rule_logic="defaults == 0",
            parameters={'max_defaults': 0}
        ))
        
        # Bankruptcy
        self.add_rule(PolicyRule(
            rule_id="NO_BANKRUPTCY",
            rule_name="No Recent Bankruptcy",
            rule_type=PolicyRuleType.MANDATORY,
            description="No bankruptcy or insolvency",
            rule_logic="bankruptcies == 0",
            parameters={'max_bankruptcies': 0}
        ))
        
        # Employment stability
        self.add_rule(PolicyRule(
            rule_id="EMPLOYMENT_STABILITY",
            rule_name="Employment Stability",
            rule_type=PolicyRuleType.GUIDELINE,
            description="Minimum employment duration",
            rule_logic="months_employed >= 6",
            parameters={'min_months': 6}
        ))
    
    def add_rule(self, rule: PolicyRule):
        """Add a policy rule"""
        self.rules[rule.rule_id] = rule
    
    async def evaluate_rules(
        self,
        application: LoanApplication,
        credit_bureau: Optional[CreditBureauResponse] = None
    ) -> List[PolicyRuleResult]:
        """Evaluate all applicable rules"""
        
        results = []
        
        # Calculate age
        if application.primary_applicant.date_of_birth:
            age = (date.today() - application.primary_applicant.date_of_birth).days // 365
        else:
            age = 0
        
        # Calculate income
        income = application.primary_employment.total_annual_income()
        
        # Calculate employment duration
        emp = application.primary_employment
        months_employed = (emp.years_employed or 0) * 12 + (emp.months_employed or 0)
        
        # LTV
        ltv = application.loan_to_value_ratio()
        
        # DTI
        dti = application.debt_to_income_ratio()
        
        # Credit bureau data
        credit_score = credit_bureau.credit_score if credit_bureau else None
        defaults = credit_bureau.number_of_defaults if credit_bureau else 0
        bankruptcies = credit_bureau.bankruptcies if credit_bureau else 0
        
        # Context for rule evaluation
        context = {
            'age': age,
            'income': float(income),
            'credit_score': credit_score,
            'ltv': float(ltv) if ltv else None,
            'dti': float(dti),
            'defaults': defaults,
            'bankruptcies': bankruptcies,
            'months_employed': months_employed
        }
        
        # Evaluate each rule
        for rule in self.rules.values():
            if not rule.active:
                continue
            
            # Check if rule applies to product type
            if rule.product_types and application.product_type not in rule.product_types:
                continue
            
            result = await self._evaluate_rule(rule, context)
            results.append(result)
        
        return results
    
    async def _evaluate_rule(
        self,
        rule: PolicyRule,
        context: Dict[str, Any]
    ) -> PolicyRuleResult:
        """Evaluate a single rule"""
        
        try:
            # Simple evaluation (in production, would use safe eval or rules engine)
            passed = eval(rule.rule_logic, {"__builtins__": {}}, context)
            
            # Get actual vs threshold
            # Extract variable name from rule_logic
            var_name = rule.rule_logic.split()[0]
            actual_value = context.get(var_name, "N/A")
            
            # Extract threshold from parameters
            threshold_key = list(rule.parameters.keys())[0] if rule.parameters else None
            threshold_value = rule.parameters.get(threshold_key, "N/A") if threshold_key else "N/A"
            
            message = f"{'PASS' if passed else 'FAIL'}: {rule.description}"
            
            return PolicyRuleResult(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                rule_type=rule.rule_type,
                passed=passed,
                actual_value=actual_value,
                threshold_value=threshold_value,
                message=message,
                can_override=(rule.rule_type == PolicyRuleType.DISCRETIONARY)
            )
        
        except Exception as e:
            return PolicyRuleResult(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                rule_type=rule.rule_type,
                passed=False,
                actual_value="ERROR",
                threshold_value="N/A",
                message=f"Error evaluating rule: {str(e)}",
                can_override=False
            )


# ============================================================================
# Affordability Calculator
# ============================================================================

class AffordabilityCalculator:
    """
    Affordability assessment calculator
    Implements various methods including ASIC HEM
    """
    
    def __init__(self):
        # APRA stress test buffer
        self.stress_test_buffer = Decimal('3.00')  # 3% above actual rate
        self.minimum_stress_rate = Decimal('7.00')  # Minimum 7%
        
        # HEM benchmarks (simplified - would use full ASIC HEM tables)
        self.hem_benchmarks = {
            1: Decimal('2500.00'),  # Single person
            2: Decimal('3500.00'),  # Couple
            3: Decimal('4200.00'),  # Family of 3
            4: Decimal('4800.00'),  # Family of 4
            5: Decimal('5400.00'),  # Family of 5+
        }
    
    async def assess_affordability(
        self,
        application: LoanApplication,
        proposed_rate: Decimal,
        method: AffordabilityMethod = AffordabilityMethod.HEM
    ) -> AffordabilityAssessment:
        """Perform affordability assessment"""
        
        assessment_id = f"AFF-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        # Calculate income
        gross_annual = application.total_household_income()
        gross_monthly = gross_annual / Decimal('12')
        
        # Estimate net income (simplified - 80% of gross after tax)
        net_monthly = gross_monthly * Decimal('0.80')
        
        # Calculate living expenses
        if method == AffordabilityMethod.HEM:
            living_expenses = self._calculate_hem_expenses(application)
        else:
            living_expenses = self._calculate_declared_expenses(application)
        
        # Existing debt repayments
        existing_debt = application.primary_financial.total_monthly_repayments()
        if application.joint_financial:
            existing_debt += application.joint_financial.total_monthly_repayments()
        
        # Proposed loan repayment
        proposed_repayment = self._calculate_monthly_repayment(
            application.requested_amount,
            proposed_rate,
            application.requested_term_months
        )
        
        # Total expenses
        total_expenses = living_expenses + existing_debt + proposed_repayment
        
        # Surplus
        surplus = net_monthly - total_expenses
        
        # Ratios
        dsr = ((existing_debt + proposed_repayment) / gross_monthly) * Decimal('100')
        surplus_ratio = (surplus / net_monthly) * Decimal('100')
        
        # Stress test
        stress_rate = max(
            proposed_rate + self.stress_test_buffer,
            self.minimum_stress_rate
        )
        stressed_repayment = self._calculate_monthly_repayment(
            application.requested_amount,
            stress_rate,
            application.requested_term_months
        )
        stressed_total = living_expenses + existing_debt + stressed_repayment
        stressed_surplus = net_monthly - stressed_total
        stressed_affordable = stressed_surplus >= 0
        
        # Determine affordability
        affordable = (
            surplus >= 0 and
            stressed_affordable and
            dsr <= Decimal('40.00')  # Max 40% DSR
        )
        
        # Calculate maximum affordable amount
        max_affordable = None
        if not affordable:
            # Calculate max amount that would be affordable
            max_monthly = net_monthly - living_expenses - existing_debt
            max_stressed_monthly = max_monthly * Decimal('0.80')  # 20% buffer
            max_affordable = self._calculate_max_loan_amount(
                max_stressed_monthly,
                stress_rate,
                application.requested_term_months
            )
        
        # Comments
        comments = []
        if surplus < 0:
            comments.append(f"Insufficient surplus:  shortfall")
        if not stressed_affordable:
            comments.append("Fails stress test at higher interest rate")
        if dsr > Decimal('40.00'):
            comments.append(f"DSR too high: {dsr:.1f}% (max 40%)")
        
        assessment = AffordabilityAssessment(
            assessment_id=assessment_id,
            application_id=application.application_id,
            method=method,
            gross_monthly_income=gross_monthly,
            net_monthly_income=net_monthly,
            living_expenses=living_expenses,
            existing_debt_repayments=existing_debt,
            proposed_loan_repayment=proposed_repayment,
            total_expenses=total_expenses,
            surplus_income=surplus,
            net_disposable_income=surplus,
            debt_service_ratio=dsr,
            net_surplus_ratio=surplus_ratio,
            affordable=affordable,
            maximum_affordable_amount=max_affordable,
            stress_test_rate=stress_rate,
            stressed_repayment=stressed_repayment,
            stressed_affordable=stressed_affordable,
            comments=comments
        )
        
        return assessment
    
    def _calculate_hem_expenses(self, application: LoanApplication) -> Decimal:
        """Calculate living expenses using HEM"""
        
        # Calculate household size
        household_size = 1  # Primary applicant
        if application.joint_applicant:
            household_size += 1
        household_size += application.primary_applicant.number_of_dependents
        
        # Get HEM benchmark
        if household_size > 5:
            household_size = 5
        
        hem = self.hem_benchmarks.get(household_size, Decimal('2500.00'))
        
        return hem
    
    def _calculate_declared_expenses(self, application: LoanApplication) -> Decimal:
        """Calculate living expenses from declared amounts"""
        
        expenses = application.primary_financial.total_monthly_expenses()
        if application.joint_financial:
            expenses += application.joint_financial.total_monthly_expenses()
        
        return expenses
    
    def _calculate_monthly_repayment(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        term_months: int
    ) -> Decimal:
        """Calculate monthly loan repayment"""
        
        if annual_rate == 0:
            return principal / Decimal(term_months)
        
        monthly_rate = annual_rate / Decimal('100') / Decimal('12')
        
        # PMT formula: P * [r(1+r)^n] / [(1+r)^n - 1]
        numerator = monthly_rate * ((1 + monthly_rate) ** term_months)
        denominator = ((1 + monthly_rate) ** term_months) - 1
        
        payment = principal * (numerator / denominator)
        
        return payment.quantize(Decimal('0.01'))
    
    def _calculate_max_loan_amount(
        self,
        max_monthly_payment: Decimal,
        annual_rate: Decimal,
        term_months: int
    ) -> Decimal:
        """Calculate maximum loan amount for given payment"""
        
        if annual_rate == 0:
            return max_monthly_payment * Decimal(term_months)
        
        monthly_rate = annual_rate / Decimal('100') / Decimal('12')
        
        # Reverse PMT formula
        numerator = max_monthly_payment * (((1 + monthly_rate) ** term_months) - 1)
        denominator = monthly_rate * ((1 + monthly_rate) ** term_months)
        
        max_amount = numerator / denominator
        
        return max_amount.quantize(Decimal('0.01'))


# ============================================================================
# Risk Assessment Engine
# ============================================================================

class RiskAssessmentEngine:
    """
    Risk assessment and scoring engine
    """
    
    async def assess_risk(
        self,
        application: LoanApplication,
        credit_bureau: Optional[CreditBureauResponse] = None,
        affordability: Optional[AffordabilityAssessment] = None
    ) -> RiskAssessment:
        """Perform comprehensive risk assessment"""
        
        assessment_id = f"RISK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        # Credit score
        credit_score = credit_bureau.credit_score if credit_bureau else None
        credit_grade = credit_bureau.credit_grade if credit_bureau else None
        
        # Calculate application score
        app_score = await self._calculate_application_score(application)
        
        # Combined score (weighted average)
        if credit_score:
            combined_score = (
                Decimal(credit_score) * Decimal('0.60') +  # 60% weight on credit score
                Decimal(app_score) * Decimal('0.40')  # 40% weight on application
            )
        else:
            combined_score = Decimal(app_score)
        
        # Calculate key ratios
        ltv = application.loan_to_value_ratio()
        dti = application.debt_to_income_ratio()
        dsr = affordability.debt_service_ratio if affordability else Decimal('0.00')
        
        # Identify risk factors
        positive_factors = []
        negative_factors = []
        
        # Positive factors
        if credit_score and credit_score >= 700:
            positive_factors.append("Good credit score")
        if ltv and ltv < Decimal('70.00'):
            positive_factors.append("Low LTV ratio")
        if dti < Decimal('30.00'):
            positive_factors.append("Low debt-to-income ratio")
        if application.primary_employment.employment_type == EmploymentType.FULL_TIME:
            positive_factors.append("Full-time employment")
        if affordability and affordability.surplus_income > Decimal('500.00'):
            positive_factors.append("Strong surplus income")
        
        # Negative factors
        if credit_score and credit_score < 600:
            negative_factors.append("Below average credit score")
        if credit_bureau and credit_bureau.number_of_defaults > 0:
            negative_factors.append("Payment defaults on record")
        if ltv and ltv > Decimal('80.00'):
            negative_factors.append("High LTV ratio")
        if dti > Decimal('40.00'):
            negative_factors.append("High debt-to-income ratio")
        if affordability and not affordability.stressed_affordable:
            negative_factors.append("Fails stress test")
        if credit_bureau and credit_bureau.number_of_enquiries_6m > 3:
            negative_factors.append("Multiple recent credit enquiries")
        
        # Determine risk rating
        risk_rating = self._determine_risk_rating(
            combined_score,
            ltv,
            dti,
            negative_factors
        )
        
        # Probability of default (simplified model)
        pd = self._estimate_probability_of_default(
            combined_score,
            ltv,
            dti
        )
        
        # Risk acceptable?
        risk_acceptable = (
            risk_rating not in [RiskRating.VERY_HIGH, RiskRating.UNACCEPTABLE] and
            len(negative_factors) < 3
        )
        
        assessment = RiskAssessment(
            assessment_id=assessment_id,
            application_id=application.application_id,
            credit_score=credit_score,
            application_score=app_score,
            combined_score=combined_score,
            credit_grade=credit_grade,
            risk_rating=risk_rating,
            ltv_ratio=ltv,
            dti_ratio=dti,
            dsr_ratio=dsr,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            probability_of_default=pd,
            risk_acceptable=risk_acceptable
        )
        
        return assessment
    
    async def _calculate_application_score(
        self,
        application: LoanApplication
    ) -> int:
        """Calculate application-based score"""
        
        score = 500  # Base score
        
        # Income
        income = application.total_household_income()
        if income >= Decimal('100000'):
            score += 100
        elif income >= Decimal('75000'):
            score += 75
        elif income >= Decimal('50000'):
            score += 50
        elif income >= Decimal('30000'):
            score += 25
        
        # Employment
        if application.primary_employment.employment_type == EmploymentType.FULL_TIME:
            score += 50
        
        emp_years = application.primary_employment.years_employed or 0
        if emp_years >= 5:
            score += 50
        elif emp_years >= 2:
            score += 25
        
        # Net worth
        net_worth = application.primary_financial.net_worth()
        if net_worth >= Decimal('200000'):
            score += 75
        elif net_worth >= Decimal('100000'):
            score += 50
        elif net_worth >= Decimal('50000'):
            score += 25
        
        # Residential stability
        if application.primary_applicant.residential_status == "OWNER_OCCUPIED":
            score += 25
        
        return min(score, 850)  # Cap at 850
    
    def _determine_risk_rating(
        self,
        score: Decimal,
        ltv: Optional[Decimal],
        dti: Decimal,
        negative_factors: List[str]
    ) -> RiskRating:
        """Determine overall risk rating"""
        
        if score >= Decimal('750') and dti < Decimal('30') and len(negative_factors) == 0:
            return RiskRating.VERY_LOW
        elif score >= Decimal('650') and dti < Decimal('35') and len(negative_factors) <= 1:
            return RiskRating.LOW
        elif score >= Decimal('550') and dti < Decimal('40') and len(negative_factors) <= 2:
            return RiskRating.MODERATE
        elif score >= Decimal('450') or len(negative_factors) <= 3:
            return RiskRating.HIGH
        elif score >= Decimal('350'):
            return RiskRating.VERY_HIGH
        else:
            return RiskRating.UNACCEPTABLE
    
    def _estimate_probability_of_default(
        self,
        score: Decimal,
        ltv: Optional[Decimal],
        dti: Decimal
    ) -> Decimal:
        """Estimate probability of default"""
        
        # Simplified PD model (in production, use statistical/ML model)
        base_pd = Decimal('5.00')  # 5% base
        
        # Adjust for score
        if score >= 700:
            base_pd -= Decimal('3.00')
        elif score < 600:
            base_pd += Decimal('5.00')
        
        # Adjust for LTV
        if ltv and ltv > Decimal('80'):
            base_pd += Decimal('2.00')
        
        # Adjust for DTI
        if dti > Decimal('40'):
            base_pd += Decimal('2.00')
        
        return max(Decimal('0.50'), base_pd)


# ============================================================================
# Underwriting Engine
# ============================================================================

class UnderwritingEngine:
    """
    Main underwriting engine
    Orchestrates credit decision process
    """
    
    def __init__(self):
        self.app_manager = get_application_manager()
        self.credit_bureau = CreditBureauService()
        self.policy_engine = PolicyRulesEngine()
        self.affordability_calc = AffordabilityCalculator()
        self.risk_engine = RiskAssessmentEngine()
        self.audit_store = get_audit_store()
        
        # Decisions
        self.decisions: Dict[str, UnderwritingDecision] = {}
    
    async def underwrite_application(
        self,
        application_id: str,
        proposed_rate: Decimal,
        underwriter: str = "SYSTEM"
    ) -> UnderwritingDecision:
        """
        Perform complete underwriting assessment
        """
        
        decision_id = f"DEC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        # Get application
        application = await self.app_manager.get_application(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        # Change status to underwriting
        application.change_status(
            ApplicationStatus.UNDERWRITING,
            underwriter,
            "Application under review"
        )
        
        # Step 1: Credit bureau check
        credit_bureau = await self.credit_bureau.check_credit(
            applicant_name=f"{application.primary_applicant.first_name} {application.primary_applicant.last_name}",
            date_of_birth=application.primary_applicant.date_of_birth,
            address=application.primary_applicant.address_line1,
            consent_given=application.primary_applicant.credit_check_consent
        )
        
        # Step 2: Policy rules evaluation
        policy_results = await self.policy_engine.evaluate_rules(application, credit_bureau)
        
        # Check policy compliance
        mandatory_failed = [
            r for r in policy_results
            if r.rule_type == PolicyRuleType.MANDATORY and not r.passed
        ]
        policy_compliant = len(mandatory_failed) == 0
        
        # Step 3: Affordability assessment
        affordability = await self.affordability_calc.assess_affordability(
            application,
            proposed_rate,
            AffordabilityMethod.HEM
        )
        
        # Step 4: Risk assessment
        risk = await self.risk_engine.assess_risk(
            application,
            credit_bureau,
            affordability
        )
        
        # Step 5: Make decision
        decision = await self._make_decision(
            decision_id,
            application,
            credit_bureau,
            policy_results,
            policy_compliant,
            affordability,
            risk,
            proposed_rate,
            underwriter
        )
        
        # Store decision
        self.decisions[decision_id] = decision
        
        # Update application status
        if decision.approved:
            application.change_status(
                ApplicationStatus.APPROVED if not decision.conditions else ApplicationStatus.CONDITIONALLY_APPROVED,
                underwriter,
                "Application approved"
            )
            application.approved_amount = decision.approved_amount
            application.approved_term_months = decision.approved_term_months
            application.approved_rate = decision.approved_rate
            application.conditions = decision.conditions
        elif decision.decision_type == DecisionType.REFER_TO_UNDERWRITER:
            # Keep in underwriting status
            pass
        else:
            application.change_status(
                ApplicationStatus.DECLINED,
                underwriter,
                "Application declined"
            )
            application.decline_reason = '; '.join(decision.decline_reasons)
        
        application.decision_date = datetime.now(timezone.utc)
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            category=AuditCategory.FINANCIAL,
            severity=AuditSeverity.INFO,
            resource_type='loan_decision',
            resource_id=decision_id,
            action='underwriting_completed',
            description=f"Loan decision: {'APPROVED' if decision.approved else 'DECLINED'}",
            user_id=underwriter,
            metadata={
                'application_id': application_id,
                'decision_type': decision.decision_type.value,
                'approved': decision.approved,
                'risk_rating': risk.risk_rating.value,
                'credit_score': credit_bureau.credit_score
            },
            regulatory_relevant=True
        )
        
        return decision
    
    async def _make_decision(
        self,
        decision_id: str,
        application: LoanApplication,
        credit_bureau: CreditBureauResponse,
        policy_results: List[PolicyRuleResult],
        policy_compliant: bool,
        affordability: AffordabilityAssessment,
        risk: RiskAssessment,
        proposed_rate: Decimal,
        underwriter: str
    ) -> UnderwritingDecision:
        """Make underwriting decision"""
        
        decline_reasons = []
        conditions = []
        referral_reasons = []
        
        # Check for auto-decline conditions
        if not policy_compliant:
            mandatory_failures = [
                r for r in policy_results
                if r.rule_type == PolicyRuleType.MANDATORY and not r.passed
            ]
            decline_reasons.extend([r.message for r in mandatory_failures])
        
        if not affordability.affordable:
            decline_reasons.append("Insufficient affordability")
        
        if risk.risk_rating == RiskRating.UNACCEPTABLE:
            decline_reasons.append("Unacceptable risk level")
        
        # Auto decline?
        if decline_reasons:
            return UnderwritingDecision(
                decision_id=decision_id,
                application_id=application.application_id,
                decision_type=DecisionType.AUTO_DECLINE,
                approved=False,
                decline_reasons=decline_reasons,
                affordability=affordability,
                risk=risk,
                credit_bureau=credit_bureau,
                policy_results=policy_results,
                policy_compliant=policy_compliant,
                decided_by=underwriter
            )
        
        # Check for referral conditions
        if risk.risk_rating in [RiskRating.HIGH, RiskRating.VERY_HIGH]:
            referral_reasons.append("High risk rating requires manual review")
        
        discretionary_failures = [
            r for r in policy_results
            if r.rule_type == PolicyRuleType.DISCRETIONARY and not r.passed
        ]
        if discretionary_failures:
            referral_reasons.append("Policy exceptions require approval")
        
        if credit_bureau.credit_score and credit_bureau.credit_score < 650:
            referral_reasons.append("Below standard credit score")
        
        if application.requested_amount > Decimal('500000'):
            referral_reasons.append("Large loan amount requires senior approval")
        
        # Refer to manual underwriter?
        if referral_reasons:
            return UnderwritingDecision(
                decision_id=decision_id,
                application_id=application.application_id,
                decision_type=DecisionType.REFER_TO_UNDERWRITER,
                approved=False,
                affordability=affordability,
                risk=risk,
                credit_bureau=credit_bureau,
                policy_results=policy_results,
                policy_compliant=True,
                refer_to_manager=True,
                referral_reasons=referral_reasons,
                decided_by=underwriter
            )
        
        # Auto approve with conditions?
        if risk.risk_rating == RiskRating.MODERATE:
            conditions.append("Provide additional income verification")
        
        ltv = application.loan_to_value_ratio()
        if ltv and ltv > Decimal('75'):
            conditions.append("Lenders Mortgage Insurance required")
        
        # Auto approve!
        return UnderwritingDecision(
            decision_id=decision_id,
            application_id=application.application_id,
            decision_type=DecisionType.AUTO_APPROVE if not conditions else DecisionType.CONDITIONAL_APPROVE,
            approved=True,
            approved_amount=application.requested_amount,
            approved_term_months=application.requested_term_months,
            approved_rate=proposed_rate,
            conditions=conditions,
            affordability=affordability,
            risk=risk,
            credit_bureau=credit_bureau,
            policy_results=policy_results,
            policy_compliant=True,
            decided_by=underwriter
        )
    
    async def get_decision(self, decision_id: str) -> Optional[UnderwritingDecision]:
        """Get underwriting decision"""
        return self.decisions.get(decision_id)
    
    async def override_decision(
        self,
        decision_id: str,
        approved: bool,
        override_by: str,
        override_reason: str
    ) -> UnderwritingDecision:
        """Override automated decision (manual underwriting)"""
        
        decision = self.decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        
        decision.approved = approved
        decision.decided_by = override_by
        decision.decision_type_used = "MANUAL"
        decision.metadata['override_reason'] = override_reason
        decision.metadata['original_decision'] = decision.decision_type.value
        
        return decision


# ============================================================================
# Global Underwriting Engine
# ============================================================================

_underwriting_engine: Optional[UnderwritingEngine] = None

def get_underwriting_engine() -> UnderwritingEngine:
    """Get the singleton underwriting engine"""
    global _underwriting_engine
    if _underwriting_engine is None:
        _underwriting_engine = UnderwritingEngine()
    return _underwriting_engine
