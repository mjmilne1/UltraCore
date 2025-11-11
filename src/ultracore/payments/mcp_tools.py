"""
UltraCore - MCP Payment Tools
Enabling Claude to process payments with natural language
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal
import json

class PaymentMCPTools:
    """MCP tools for Claude to handle payments"""
    
    def __init__(self, payment_facade):
        self.payments = payment_facade
        self.tools = self._register_tools()
    
    def _register_tools(self) -> List[Dict[str, Any]]:
        """Register payment tools for MCP"""
        return [
            {
                "name": "send_payment",
                "description": "Send money to someone via NPP, BPAY, or other rails",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "Amount to send in AUD"
                        },
                        "to": {
                            "type": "string",
                            "description": "Recipient (PayID, mobile, email, BSB-account, or description)"
                        },
                        "from_account": {
                            "type": "string",
                            "description": "Sender's account number"
                        },
                        "description": {
                            "type": "string",
                            "description": "Payment description"
                        }
                    },
                    "required": ["amount", "to", "from_account"]
                }
            },
            {
                "name": "pay_bill",
                "description": "Pay a bill using BPAY",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "biller": {
                            "type": "string",
                            "description": "Biller name or code"
                        },
                        "reference": {
                            "type": "string",
                            "description": "Customer reference number"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Bill amount in AUD"
                        },
                        "from_account": {
                            "type": "string",
                            "description": "Account to pay from"
                        }
                    },
                    "required": ["biller", "amount", "from_account"]
                }
            },
            {
                "name": "analyze_payment",
                "description": "Analyze a payment for fraud, optimal routing, and recommendations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "Payment amount"
                        },
                        "recipient": {
                            "type": "string",
                            "description": "Payment recipient"
                        },
                        "purpose": {
                            "type": "string",
                            "description": "Purpose of payment"
                        }
                    },
                    "required": ["amount", "recipient"]
                }
            },
            {
                "name": "schedule_payment",
                "description": "Schedule a future payment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "Payment amount"
                        },
                        "to": {
                            "type": "string",
                            "description": "Recipient"
                        },
                        "date": {
                            "type": "string",
                            "description": "Date to process payment (YYYY-MM-DD)"
                        },
                        "recurring": {
                            "type": "boolean",
                            "description": "Is this a recurring payment?"
                        }
                    },
                    "required": ["amount", "to", "date"]
                }
            }
        ]
    
    async def handle_natural_language(self, user_input: str) -> Dict[str, Any]:
        """
        Handle natural language payment requests
        Examples:
        - "Send $100 to John's mobile 0412345678"
        - "Pay my electricity bill"
        - "Transfer 500 dollars to sarah@email.com"
        """
        
        # Extract intent and entities (simplified - use real NLP in production)
        intent = self._extract_intent(user_input)
        entities = self._extract_entities(user_input)
        
        # Route to appropriate handler
        if intent == "send_money":
            return await self._handle_send_money(entities)
        elif intent == "pay_bill":
            return await self._handle_pay_bill(entities)
        elif intent == "check_payment":
            return await self._handle_check_payment(entities)
        else:
            return {
                "error": "Could not understand request",
                "suggestion": "Try: 'Send $100 to 0412345678' or 'Pay electricity bill'"
            }
    
    def _extract_intent(self, text: str) -> str:
        """Extract payment intent from natural language"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["send", "transfer", "pay"]):
            if "bill" in text_lower:
                return "pay_bill"
            else:
                return "send_money"
        elif any(word in text_lower for word in ["check", "status", "where"]):
            return "check_payment"
        
        return "unknown"
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from natural language"""
        import re
        
        entities = {}
        
        # Extract amount
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', text)
        if amount_match:
            entities["amount"] = Decimal(amount_match.group(1))
        
        # Extract mobile number
        mobile_match = re.search(r'04\d{8}', text)
        if mobile_match:
            entities["to"] = mobile_match.group(0)
        
        # Extract email
        email_match = re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)
        if email_match:
            entities["to"] = email_match.group(0)
        
        # Extract common billers
        billers = {
            "electricity": "12345",
            "gas": "23456",
            "water": "34567",
            "internet": "45678",
            "phone": "56789"
        }
        
        for biller_name, biller_code in billers.items():
            if biller_name in text.lower():
                entities["biller"] = biller_code
                entities["biller_name"] = biller_name
        
        return entities
    
    async def _handle_send_money(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send money request"""
        if "amount" not in entities or "to" not in entities:
            return {
                "error": "Missing required information",
                "needed": ["amount", "recipient"]
            }
        
        # Process payment
        result = await self.payments.pay(
            amount=entities["amount"],
            from_account="default",  # Use customer's default account
            to=entities["to"],
            description=entities.get("description", "Payment via Claude")
        )
        
        return {
            "success": True,
            "message": f"Payment of ${entities['amount']} sent successfully",
            "details": result
        }
    
    async def _handle_pay_bill(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle bill payment request"""
        if "biller" not in entities:
            return {
                "error": "Please specify which bill to pay",
                "suggestions": ["electricity", "gas", "water", "internet"]
            }
        
        # Get bill details (mock - integrate with real bill system)
        bill_amount = entities.get("amount", Decimal("150.00"))
        
        result = await self.payments.pay_bill(
            biller_code=entities["biller"],
            crn="1234567890123456",  # Get from bill system
            amount=bill_amount,
            from_account="default"
        )
        
        return {
            "success": True,
            "message": f"{entities.get('biller_name', 'Bill')} payment of ${bill_amount} processed",
            "details": result
        }
    
    async def _handle_check_payment(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Check payment status"""
        # Mock implementation - integrate with real payment tracking
        return {
            "status": "completed",
            "message": "Your last payment was completed successfully",
            "timestamp": datetime.now().isoformat()
        }


class ClaudePaymentAgent:
    """Claude-powered payment agent with ML insights"""
    
    def __init__(self, mcp_tools, data_mesh, ml_engine):
        self.mcp = mcp_tools
        self.mesh = data_mesh
        self.ml = ml_engine
    
    async def process_request(self, user_message: str) -> str:
        """
        Process user payment request with full AI/ML pipeline
        """
        
        # Step 1: Natural language understanding
        intent = await self.mcp.handle_natural_language(user_message)
        
        # Step 2: Get ML recommendations from data mesh
        if intent.get("success"):
            payment_data = intent.get("details", {})
            recommendations = await self.mesh.get_domain_recommendation(payment_data)
            
            # Step 3: Apply fraud detection
            fraud_info = recommendations.get("fraud", {})
            if fraud_info.get("should_block"):
                return self._format_fraud_block_response(fraud_info)
            
            # Step 4: Apply optimal routing
            routing = recommendations.get("routing", {})
            if routing.get("recommended"):
                payment_data["rail"] = routing["recommended"]["rail"]
            
            # Step 5: Process payment with ML insights
            result = await self._execute_with_ml_monitoring(payment_data)
            
            # Step 6: Generate natural language response
            return self._format_success_response(result, recommendations)
        
        return self._format_error_response(intent)
    
    def _format_fraud_block_response(self, fraud_info: Dict[str, Any]) -> str:
        """Format fraud blocking message"""
        return f"""
        ?? Payment blocked for security reasons
        
        Risk Score: {fraud_info['score']:.2f}
        Risk Level: {fraud_info['risk_level']}
        
        This payment has been flagged by our ML fraud detection system.
        Please verify your identity or contact support if you believe this is an error.
        """
    
    def _format_success_response(
        self,
        result: Dict[str, Any],
        recommendations: Dict[str, Any]
    ) -> str:
        """Format success message with ML insights"""
        routing = recommendations.get("routing", {}).get("recommended", {})
        
        return f"""
        ? Payment processed successfully!
        
        Amount: ${result.get('amount', 0)}
        Method: {routing.get('rail', 'Unknown').upper()}
        Time: {routing.get('estimated_time', 'Unknown')}
        Cost: ${routing.get('cost', 0):.2f}
        
        Transaction ID: {result.get('transaction_id', 'N/A')}
        
        ML Insights:
        - Fraud Score: {recommendations.get('fraud', {}).get('score', 0):.2f} (Low Risk)
        - Routing Confidence: {routing.get('ml_confidence', 0):.0%}
        - Success Probability: {routing.get('success_probability', 0):.1%}
        """
    
    def _format_error_response(self, error_data: Dict[str, Any]) -> str:
        """Format error message"""
        return f"""
        ? Unable to process payment
        
        Reason: {error_data.get('error', 'Unknown error')}
        Suggestion: {error_data.get('suggestion', 'Please try again')}
        """
    
    async def _execute_with_ml_monitoring(
        self,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute payment with ML monitoring"""
        # Add ML tracking
        payment_data["ml_tracking"] = {
            "start_time": datetime.now(),
            "model_versions": {
                "fraud": "v3.2.1",
                "routing": "v2.8.0",
                "optimization": "v1.5.3"
            }
        }
        
        # Process payment (mock)
        result = {
            "success": True,
            "amount": payment_data.get("amount", 0),
            "transaction_id": f"TXN{datetime.now().timestamp()}"
        }
        
        # Record ML performance
        payment_data["ml_tracking"]["end_time"] = datetime.now()
        payment_data["ml_tracking"]["latency_ms"] = 150
        
        return result
