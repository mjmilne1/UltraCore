"""
OpenAI Integration Service

Integrates OpenAI models for AI-powered wealth management features
"""

import os
from typing import Dict, List, Optional
from openai import OpenAI
import json


class OpenAIService:
    """
    OpenAI integration for UltraWealth
    
    Provides:
    - Anya AI assistant (GPT-4)
    - Investment analysis and recommendations
    - Natural language portfolio queries
    - Document analysis (SOA, financial statements)
    - Market insights and commentary
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
        self.anya_system_prompt = self._get_anya_system_prompt()
    
    def _get_anya_system_prompt(self) -> str:
        """Get Anya AI system prompt"""
        return """You are Anya, an expert AI financial advisor for UltraWealth, 
an Australian automated investment platform. You provide professional, 
compliant investment advice following ASIC RG 179 guidelines.

Your capabilities:
- Analyze client portfolios and provide recommendations
- Explain investment strategies in clear, accessible language
- Answer questions about Australian ETFs and market conditions
- Generate insights from financial data
- Ensure all advice includes appropriate disclaimers

Important compliance notes:
- Always include: "This is general advice only and does not consider your personal circumstances"
- For performance discussions: "Past performance is not indicative of future results"
- Be professional, empathetic, and Australian-context aware
- Use AUD currency and Australian financial terminology
"""
    
    async def chat_with_anya(
        self,
        user_message: str,
        context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Chat with Anya AI assistant
        
        Args:
            user_message: User's question or message
            context: Optional context (portfolio data, client profile, etc.)
            conversation_history: Previous conversation messages
            
        Returns:
            Dict: Anya's response with compliance notes
        """
        
        # Build messages
        messages = [
            {"role": "system", "content": self.anya_system_prompt}
        ]
        
        # Add context if provided
        if context:
            context_message = f"Client context: {json.dumps(context, indent=2)}"
            messages.append({"role": "system", "content": context_message})
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        anya_response = response.choices[0].message.content
        
        return {
            "response": anya_response,
            "model": self.model,
            "tokens_used": response.usage.total_tokens,
            "compliance_notes": [
                "This is general advice only and does not consider your personal circumstances.",
                "Past performance is not indicative of future results."
            ]
        }
    
    async def analyze_portfolio(
        self,
        portfolio_data: Dict,
        risk_profile: str
    ) -> Dict:
        """
        Analyze portfolio using GPT-4
        
        Args:
            portfolio_data: Portfolio holdings and performance
            risk_profile: Client risk profile
            
        Returns:
            Dict: AI-powered portfolio analysis
        """
        
        prompt = f"""Analyze this Australian investment portfolio:

Portfolio Data:
{json.dumps(portfolio_data, indent=2)}

Client Risk Profile: {risk_profile}

Please provide:
1. Portfolio health assessment
2. Diversification analysis
3. Risk-adjusted performance evaluation
4. Specific recommendations for improvement
5. Alignment with {risk_profile} risk profile

Format as structured JSON with sections: health_score (0-100), 
diversification_score (0-100), recommendations (list), risks (list), 
opportunities (list)."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.anya_system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for analysis
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        return {
            "analysis": analysis,
            "model": self.model,
            "tokens_used": response.usage.total_tokens
        }
    
    async def generate_market_insights(
        self,
        etf_data: List[Dict],
        market_conditions: Optional[Dict] = None
    ) -> Dict:
        """
        Generate market insights using GPT-4
        
        Args:
            etf_data: ETF performance and prediction data
            market_conditions: Optional current market conditions
            
        Returns:
            Dict: AI-generated market insights
        """
        
        prompt = f"""Analyze these Australian ETF market conditions:

ETF Data:
{json.dumps(etf_data, indent=2)}

{f"Market Conditions: {json.dumps(market_conditions, indent=2)}" if market_conditions else ""}

Provide:
1. Market outlook summary
2. Sector trends and opportunities
3. Risk factors to watch
4. Strategic recommendations

Keep it concise and actionable for Australian investors."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.anya_system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        insights = response.choices[0].message.content
        
        return {
            "insights": insights,
            "model": self.model,
            "tokens_used": response.usage.total_tokens
        }
    
    async def explain_investment_strategy(
        self,
        strategy_type: str,
        target_allocation: Dict,
        client_goals: List[Dict]
    ) -> str:
        """
        Generate plain-language explanation of investment strategy
        
        Args:
            strategy_type: Type of strategy (MDA, SMA, etc.)
            target_allocation: Target asset allocation
            client_goals: Client investment goals
            
        Returns:
            str: Plain-language explanation
        """
        
        prompt = f"""Explain this investment strategy in simple, clear language 
for an Australian client:

Strategy Type: {strategy_type}
Target Allocation: {json.dumps(target_allocation, indent=2)}
Client Goals: {json.dumps(client_goals, indent=2)}

Write 2-3 paragraphs explaining:
- Why this strategy suits their goals
- How the allocation works
- What to expect in terms of returns and risks

Use simple language, avoid jargon."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.anya_system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        explanation = response.choices[0].message.content
        
        return explanation
    
    async def generate_soa_content(
        self,
        client_data: Dict,
        portfolio_recommendation: Dict
    ) -> Dict:
        """
        Generate Statement of Advice content using GPT-4
        
        Args:
            client_data: Client profile and goals
            portfolio_recommendation: Recommended portfolio
            
        Returns:
            Dict: SOA content sections
        """
        
        prompt = f"""Generate a professional Statement of Advice (SOA) for this 
Australian client following ASIC RG 179 requirements:

Client Data:
{json.dumps(client_data, indent=2)}

Portfolio Recommendation:
{json.dumps(portfolio_recommendation, indent=2)}

Generate these sections:
1. Executive Summary
2. Client Situation Analysis
3. Investment Recommendation Rationale
4. Risk Disclosure
5. Fee Summary

Format as JSON with these keys: executive_summary, situation_analysis, 
recommendation_rationale, risk_disclosure, fee_summary"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.anya_system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        soa_content = json.loads(response.choices[0].message.content)
        
        return soa_content
    
    async def analyze_document(
        self,
        document_text: str,
        document_type: str = "financial_statement"
    ) -> Dict:
        """
        Analyze financial documents using GPT-4
        
        Args:
            document_text: Extracted document text
            document_type: Type of document
            
        Returns:
            Dict: Document analysis
        """
        
        prompt = f"""Analyze this {document_type}:

{document_text}

Extract and summarize:
1. Key financial figures
2. Important dates
3. Account details
4. Any red flags or notable items

Format as JSON."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a financial document analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        return analysis


# Global OpenAI service instance
_openai_service: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """Get OpenAI service singleton"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
