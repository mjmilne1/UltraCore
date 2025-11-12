from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class LoanType(Enum):
    PERSONAL = "personal_loan"
    HOME = "home_loan"
    BUSINESS = "business_loan"
    BNPL = "buy_now_pay_later"
    CREDIT_LINE = "revolving_credit"

@dataclass
class LoanProduct:
    product_type: LoanType
    min_amount: Decimal
    max_amount: Decimal
    min_term_months: int
    max_term_months: int
    base_rate: float
    requirements: Dict

class LendingDomain:
    def __init__(self):
        self.domain_name = "lending"
        self.products = self._initialize_products()
    
    def _initialize_products(self):
        return {
            LoanType.PERSONAL: LoanProduct(
                product_type=LoanType.PERSONAL,
                min_amount=Decimal("1000"),
                max_amount=Decimal("75000"),
                min_term_months=6,
                max_term_months=84,
                base_rate=0.089,
                requirements={"min_income": 30000, "min_credit_score": 600}
            ),
            LoanType.HOME: LoanProduct(
                product_type=LoanType.HOME,
                min_amount=Decimal("50000"),
                max_amount=Decimal("2000000"),
                min_term_months=60,
                max_term_months=360,
                base_rate=0.059,
                requirements={"min_deposit": 0.1, "min_income": 60000}
            )
        }
    
    async def originate_loan(self, application: Dict) -> Dict:
        loan_type = LoanType(application["loan_type"])
        product = self.products[loan_type]
        
        credit_decision = await self.perform_credit_check(application)
        
        if credit_decision["approved"]:
            interest_rate = self.calculate_interest_rate(
                product.base_rate,
                credit_decision["risk_score"]
            )
            
            return {
                "status": "APPROVED",
                "loan_id": f"LOAN_{datetime.now().timestamp():.0f}",
                "amount": application["amount"],
                "interest_rate": interest_rate,
                "term_months": application["term_months"],
                "monthly_payment": self.calculate_monthly_payment(
                    application["amount"],
                    interest_rate,
                    application["term_months"]
                )
            }
        else:
            return {
                "status": "DECLINED",
                "reasons": credit_decision["reasons"]
            }
    
    async def perform_credit_check(self, application: Dict) -> Dict:
        risk_score = await self.calculate_risk_score(application)
        approved = risk_score > 0.6
        
        reasons = []
        if not approved:
            if application.get("credit_score", 0) < 600:
                reasons.append("Low credit score")
        
        return {
            "approved": approved,
            "risk_score": risk_score,
            "reasons": reasons
        }
    
    async def calculate_risk_score(self, application: Dict) -> float:
        score = 0.5
        
        credit_score = application.get("credit_score", 0)
        if credit_score > 750:
            score += 0.3
        elif credit_score > 650:
            score += 0.2
            
        income = application.get("annual_income", 0)
        if income > 100000:
            score += 0.2
        elif income > 60000:
            score += 0.1
        
        return min(score, 1.0)
    
    def calculate_interest_rate(self, base_rate: float, risk_score: float) -> float:
        risk_adjustment = (1 - risk_score) * 0.05
        return base_rate + risk_adjustment
    
    def calculate_monthly_payment(self, principal: Decimal, 
                                 annual_rate: float, 
                                 term_months: int) -> Decimal:
        if term_months == 0:
            return Decimal("0")
        
        monthly_rate = annual_rate / 12
        if monthly_rate == 0:
            return principal / term_months
        
        payment = principal * (monthly_rate * (1 + monthly_rate)**term_months) / \
                 ((1 + monthly_rate)**term_months - 1)
        
        return Decimal(str(round(payment, 2)))
