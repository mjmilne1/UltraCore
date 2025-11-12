"""
MCP Tools for Cash Management
AI Assistant integration for cash operations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

from ultracore.modules.cash.cash_accounts import cash_account_service, PaymentMethod, AccountType
from ultracore.modules.cash.agentic_fraud import fraud_detector_agent
from ultracore.modules.cash.rl_optimizer import cash_optimizer_rl

class CashManagementMCPTools:
    """
    MCP Tools for Cash Management
    
    Enables AI assistants to:
    - Create cash accounts
    - Process deposits/withdrawals
    - Check balances
    - Analyze fraud risk
    - Optimize cash allocation
    - Get transaction history
    """
    
    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        """Get all MCP tool definitions"""
        
        return [
            {
                "name": "create_cash_account",
                "description": "Create a new cash management account for a client",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_id": {
                            "type": "string",
                            "description": "Client ID"
                        },
                        "account_type": {
                            "type": "string",
                            "enum": ["operating", "settlement", "custody", "trust", "interest_bearing"],
                            "description": "Type of cash account"
                        },
                        "currency": {
                            "type": "string",
                            "default": "AUD",
                            "description": "Account currency"
                        },
                        "interest_rate": {
                            "type": "number",
                            "default": 0.0,
                            "description": "Annual interest rate (%)"
                        }
                    },
                    "required": ["client_id", "account_type"]
                }
            },
            {
                "name": "initiate_deposit",
                "description": "Initiate a deposit to a cash account",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Cash account ID"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Deposit amount"
                        },
                        "payment_method": {
                            "type": "string",
                            "enum": ["npp", "bpay", "direct_credit", "direct_debit", "internal_transfer", "card"],
                            "description": "Payment method"
                        },
                        "reference": {
                            "type": "string",
                            "description": "Transaction reference"
                        }
                    },
                    "required": ["account_id", "amount", "payment_method", "reference"]
                }
            },
            {
                "name": "initiate_withdrawal",
                "description": "Initiate a withdrawal from a cash account",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Cash account ID"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Withdrawal amount"
                        },
                        "payment_method": {
                            "type": "string",
                            "enum": ["npp", "bpay", "direct_credit"],
                            "description": "Payment method"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination account/BSB"
                        }
                    },
                    "required": ["account_id", "amount", "payment_method", "destination"]
                }
            },
            {
                "name": "get_account_balance",
                "description": "Get current balance for a cash account",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Cash account ID"
                        }
                    },
                    "required": ["account_id"]
                }
            },
            {
                "name": "analyze_fraud_risk",
                "description": "Analyze fraud risk for a transaction using AI agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction": {
                            "type": "object",
                            "description": "Transaction details"
                        },
                        "account_history": {
                            "type": "array",
                            "description": "Account transaction history"
                        },
                        "client_profile": {
                            "type": "object",
                            "description": "Client risk profile"
                        }
                    },
                    "required": ["transaction"]
                }
            },
            {
                "name": "optimize_cash_allocation",
                "description": "Get RL-optimized cash allocation recommendation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_balances": {
                            "type": "object",
                            "description": "Current account balances"
                        },
                        "expected_outflows": {
                            "type": "number",
                            "description": "Expected outflows in next 24 hours"
                        },
                        "interest_rate": {
                            "type": "number",
                            "description": "Current interest rate (%)"
                        }
                    },
                    "required": ["account_balances", "expected_outflows", "interest_rate"]
                }
            },
            {
                "name": "reserve_balance",
                "description": "Reserve balance for pending operation (e.g., trade settlement)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Cash account ID"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Amount to reserve"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for reservation"
                        }
                    },
                    "required": ["account_id", "amount", "reason"]
                }
            },
            {
                "name": "get_transaction_history",
                "description": "Get complete event history for an account",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Cash account ID"
                        }
                    },
                    "required": ["account_id"]
                }
            },
            {
                "name": "credit_interest",
                "description": "Credit interest to an account",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Cash account ID"
                        },
                        "period_start": {
                            "type": "string",
                            "description": "Period start date (ISO format)"
                        },
                        "period_end": {
                            "type": "string",
                            "description": "Period end date (ISO format)"
                        }
                    },
                    "required": ["account_id", "period_start", "period_end"]
                }
            },
            {
                "name": "get_agent_performance",
                "description": "Get fraud detection agent performance metrics",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    @staticmethod
    def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        
        try:
            if tool_name == "create_cash_account":
                account = cash_account_service.create_account(
                    client_id=parameters["client_id"],
                    account_type=AccountType(parameters["account_type"]),
                    currency=parameters.get("currency", "AUD"),
                    interest_rate=parameters.get("interest_rate", 0.0)
                )
                
                return {
                    "success": True,
                    "account_id": account.account_id,
                    "account_type": account.account_type.value,
                    "currency": account.currency,
                    "created_at": account.created_at.isoformat()
                }
            
            elif tool_name == "initiate_deposit":
                transaction_id = cash_account_service.initiate_deposit(
                    account_id=parameters["account_id"],
                    amount=Decimal(str(parameters["amount"])),
                    payment_method=PaymentMethod(parameters["payment_method"]),
                    reference=parameters["reference"]
                )
                
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "status": "pending"
                }
            
            elif tool_name == "initiate_withdrawal":
                transaction_id = cash_account_service.initiate_withdrawal(
                    account_id=parameters["account_id"],
                    amount=Decimal(str(parameters["amount"])),
                    payment_method=PaymentMethod(parameters["payment_method"]),
                    destination=parameters["destination"]
                )
                
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "status": "pending"
                }
            
            elif tool_name == "get_account_balance":
                account = cash_account_service.get_account(parameters["account_id"])
                
                if not account:
                    return {
                        "success": False,
                        "error": "Account not found"
                    }
                
                return {
                    "success": True,
                    "balance": account.get_balance_snapshot()
                }
            
            elif tool_name == "analyze_fraud_risk":
                analysis = fraud_detector_agent.analyze_transaction(
                    transaction=parameters["transaction"],
                    account_history=parameters.get("account_history", []),
                    client_profile=parameters.get("client_profile", {})
                )
                
                return {
                    "success": True,
                    "fraud_analysis": analysis
                }
            
            elif tool_name == "optimize_cash_allocation":
                recommendation = cash_optimizer_rl.optimize_cash_allocation(
                    account_balances=parameters["account_balances"],
                    expected_outflows=parameters["expected_outflows"],
                    interest_rate=parameters["interest_rate"]
                )
                
                return {
                    "success": True,
                    "optimization": recommendation
                }
            
            elif tool_name == "reserve_balance":
                reservation_id = cash_account_service.reserve_balance(
                    account_id=parameters["account_id"],
                    amount=Decimal(str(parameters["amount"])),
                    reason=parameters["reason"]
                )
                
                return {
                    "success": True,
                    "reservation_id": reservation_id
                }
            
            elif tool_name == "get_transaction_history":
                history = cash_account_service.get_account_history(parameters["account_id"])
                
                return {
                    "success": True,
                    "event_count": len(history),
                    "events": [
                        {
                            "event_id": e.event_id,
                            "event_type": e.event_type,
                            "timestamp": e.timestamp.isoformat()
                        }
                        for e in history
                    ]
                }
            
            elif tool_name == "credit_interest":
                cash_account_service.credit_interest(
                    account_id=parameters["account_id"],
                    period_start=datetime.fromisoformat(parameters["period_start"]),
                    period_end=datetime.fromisoformat(parameters["period_end"])
                )
                
                return {
                    "success": True,
                    "message": "Interest credited"
                }
            
            elif tool_name == "get_agent_performance":
                performance = fraud_detector_agent.get_agent_performance()
                
                return {
                    "success": True,
                    "performance": performance
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Global MCP tools instance
cash_mcp_tools = CashManagementMCPTools()
