"""
Customer Agent.

Autonomous agent for customer management and support.
"""

import logging
from typing import Any, Dict

from ..base import Agent, AgentAction, AgentCapability


logger = logging.getLogger(__name__)


class CustomerAgent(Agent):
    """
    Customer agent.
    
    Handles customer onboarding, support, and relationship management.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="customer_agent",
            name="Customer Agent",
            capabilities=[
                AgentCapability.CUSTOMER_SUPPORT,
                AgentCapability.DATA_ANALYSIS,
                AgentCapability.PATTERN_RECOGNITION,
            ]
        )
    
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perceive customer state.
        
        Args:
            context: Customer context
            
        Returns:
            Perceived customer state
        """
        customer_id = context.get("customer_id")
        
        # Analyze customer data
        perceived_state = {
            "customer_id": customer_id,
            "customer_data": context.get("customer_data", {}),
            "interaction_history": context.get("interaction_history", []),
            "sentiment": self._analyze_sentiment(context),
            "needs": self._identify_needs(context),
        }
        
        # Store in memory
        self.memory.remember(f"customer_{customer_id}", perceived_state, "working")
        
        return perceived_state
    
    async def decide(self, perceived_state: Dict[str, Any]) -> AgentAction:
        """
        Decide on customer action.
        
        Args:
            perceived_state: Perceived customer state
            
        Returns:
            Decided action
        """
        # Analyze customer needs
        needs = perceived_state.get("needs", [])
        sentiment = perceived_state.get("sentiment")
        
        # Decide action based on needs and sentiment
        if "support" in needs:
            action_type = "provide_support"
        elif "onboarding" in needs:
            action_type = "assist_onboarding"
        elif sentiment == "negative":
            action_type = "escalate_to_human"
        else:
            action_type = "provide_information"
        
        return AgentAction(
            action_type=action_type,
            parameters=perceived_state
        )
    
    async def act(self, action: AgentAction) -> Any:
        """
        Execute customer action.
        
        Args:
            action: Action to execute
            
        Returns:
            Action result
        """
        action_type = action.action_type
        
        logger.info(f"Customer agent executing action: {action_type}")
        
        if action_type == "provide_support":
            return await self._provide_support(action.parameters)
        elif action_type == "assist_onboarding":
            return await self._assist_onboarding(action.parameters)
        elif action_type == "escalate_to_human":
            return await self._escalate_to_human(action.parameters)
        else:
            return await self._provide_information(action.parameters)
    
    def _analyze_sentiment(self, context: Dict[str, Any]) -> str:
        """Analyze customer sentiment."""
        # Simplified sentiment analysis
        # In production, use NLP model
        interaction_history = context.get("interaction_history", [])
        
        if not interaction_history:
            return "neutral"
        
        # Check for negative keywords
        negative_keywords = ["problem", "issue", "complaint", "frustrated"]
        last_interaction = interaction_history[-1].get("message", "").lower()
        
        if any(keyword in last_interaction for keyword in negative_keywords):
            return "negative"
        
        return "positive"
    
    def _identify_needs(self, context: Dict[str, Any]) -> list[str]:
        """Identify customer needs."""
        needs = []
        
        customer_data = context.get("customer_data", {})
        
        # Check onboarding status
        if customer_data.get("kyc_status") == "pending":
            needs.append("onboarding")
        
        # Check for support requests
        if context.get("support_request"):
            needs.append("support")
        
        # Check for product interests
        if context.get("product_inquiry"):
            needs.append("product_information")
        
        return needs
    
    async def _provide_support(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Provide customer support."""
        return {
            "action": "support_provided",
            "message": "I'm here to help you. How can I assist you today?",
            "next_steps": ["gather_details", "resolve_issue"]
        }
    
    async def _assist_onboarding(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assist with customer onboarding."""
        return {
            "action": "onboarding_assistance",
            "message": "Let me help you complete your onboarding process.",
            "next_steps": ["verify_identity", "complete_kyc", "setup_account"]
        }
    
    async def _escalate_to_human(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate to human agent."""
        return {
            "action": "escalated",
            "message": "I'm connecting you with a human agent who can better assist you.",
            "escalation_reason": "negative_sentiment"
        }
    
    async def _provide_information(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general information."""
        return {
            "action": "information_provided",
            "message": "Here's the information you requested.",
            "resources": ["faq", "product_guide", "contact_support"]
        }
