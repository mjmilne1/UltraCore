"""
Anya - AI Banking Assistant
OpenAI GPT-4 powered intelligent loan advisor
"""
from typing import Dict, Optional
from openai import OpenAI
import os
from decimal import Decimal

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'sk-dummy')) if os.getenv('OPENAI_API_KEY') else None


class AnyaAgent:
    """
    Anya - Your AI Banking Assistant
    
    Powered by GPT-4
    Specializes in loan analysis and customer service
    """
    
    def __init__(self):
        self.name = 'Anya'
        self.role = 'Senior Loan Advisor'
        self.model = 'gpt-4-turbo-preview'
    
    async def analyze_loan_application(
        self,
        customer_id: str,
        amount: Decimal,
        term_months: int,
        purpose: str,
        customer_data: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze a loan application using AI
        
        Returns:
            - recommendation: 'APPROVE' or 'REJECT'
            - confidence: 0.0 to 1.0
            - reasoning: Detailed explanation
            - risk_factors: List of identified risks
            - suggested_terms: Alternative terms if applicable
        """
        
        # Build analysis prompt
        prompt = f"""You are Anya, a senior loan advisor at TuringDynamics Bank. 
Analyze this loan application with Australian banking regulations in mind.

LOAN APPLICATION:
- Customer ID: {customer_id}
- Requested Amount: ${amount:,.2f} AUD
- Term: {term_months} months
- Purpose: {purpose}

CUSTOMER DATA:
{self._format_customer_data(customer_data)}

AUSTRALIAN REGULATORY CONTEXT:
- Must comply with ASIC responsible lending obligations
- Consider NCCP Act requirements
- Assess genuine hardship indicators
- Verify affordability and suitability

Provide your analysis in this EXACT JSON format:
{{
    "recommendation": "APPROVE or REJECT",
    "confidence": 0.85,
    "credit_score": 750,
    "reasoning": "Detailed explanation of your decision",
    "risk_factors": ["factor1", "factor2"],
    "strengths": ["strength1", "strength2"],
    "suggested_interest_rate": 8.5,
    "conditions": ["condition1", "condition2"],
    "compliance_notes": "ASIC/NCCP compliance notes"
}}

Respond ONLY with valid JSON. No other text."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Anya, a senior loan advisor. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse AI response
            import json
            analysis_text = response.choices[0].message.content
            
            # Clean response (remove markdown if present)
            analysis_text = analysis_text.replace('`json', '').replace('`', '').strip()
            analysis = json.loads(analysis_text)
            
            return {
                'agent': 'Anya',
                'model': self.model,
                'analysis': analysis,
                'raw_response': response.choices[0].message.content
            }
            
        except Exception as e:
            # Fallback to conservative decision
            return {
                'agent': 'Anya',
                'model': self.model,
                'error': str(e),
                'analysis': {
                    'recommendation': 'MANUAL_REVIEW',
                    'confidence': 0.0,
                    'credit_score': 650,
                    'reasoning': f'AI analysis failed: {str(e)}. Requires manual review.',
                    'risk_factors': ['AI_ANALYSIS_ERROR'],
                    'strengths': [],
                    'suggested_interest_rate': 10.0,
                    'conditions': ['Manual review required'],
                    'compliance_notes': 'Escalate to human underwriter'
                }
            }
    
    async def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Chat with Anya about loans or banking
        """
        system_prompt = f"""You are Anya, a friendly and professional AI banking assistant at TuringDynamics Bank in Australia.

Your responsibilities:
- Help customers understand loan products
- Answer questions about applications
- Provide financial guidance
- Explain terms and conditions
- Always comply with Australian banking regulations

Be warm, professional, and helpful. Use Australian terminology and references."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}"
    
    def _format_customer_data(self, data: Optional[Dict]) -> str:
        """Format customer data for analysis"""
        if not data:
            return "- No additional customer data provided"
        
        formatted = []
        if 'credit_score' in data:
            formatted.append(f"- Credit Score: {data['credit_score']}")
        if 'annual_income' in data:
            formatted.append(f"- Annual Income: ${data['annual_income']:,.2f}")
        if 'employment_status' in data:
            formatted.append(f"- Employment: {data['employment_status']}")
        if 'existing_loans' in data:
            formatted.append(f"- Existing Loans: {data['existing_loans']}")
        if 'debt_to_income_ratio' in data:
            formatted.append(f"- Debt-to-Income: {data['debt_to_income_ratio']:.1%}")
        
        return '\n'.join(formatted) if formatted else "- Limited customer data"


# Global Anya instance
anya = AnyaAgent()

