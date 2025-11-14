"""MCP Tools for Fee Management"""
from typing import Dict, List
from decimal import Decimal
from datetime import datetime

async def calculate_fee(fee_type: str, amount: Decimal,
                       parameters: Dict, tenant_id: str) -> Dict:
    """Calculate fee amount
    
    Args:
        fee_type: Type of fee (management, performance, transaction, tiered, subscription)
        amount: Base amount for fee calculation (AUM, gains, transaction value)
        parameters: Fee parameters (rate, tiers, hurdle_rate, etc.)
        tenant_id: Tenant ID
    
    Returns:
        Fee calculation details
    """
    if fee_type == "management":
        # Management fee: % of AUM annually
        annual_rate = parameters.get("annual_rate", 1.0) / 100
        billing_frequency = parameters.get("billing_frequency", "monthly")
        
        if billing_frequency == "monthly":
            fee_amount = amount * annual_rate / 12
        elif billing_frequency == "quarterly":
            fee_amount = amount * annual_rate / 4
        else:
            fee_amount = amount * annual_rate
        
        return {
            "fee_type": "management",
            "base_amount": float(amount),
            "annual_rate_percent": parameters.get("annual_rate"),
            "billing_frequency": billing_frequency,
            "fee_amount": float(fee_amount),
            "currency": "AUD"
        }
    
    elif fee_type == "performance":
        # Performance fee: % of gains above hurdle
        performance_rate = parameters.get("performance_rate", 20.0) / 100
        hurdle_rate = parameters.get("hurdle_rate", 0.0) / 100
        high_water_mark = Decimal(str(parameters.get("high_water_mark", 0)))
        
        # Only charge on gains above hurdle and high water mark
        hurdle_amount = amount * Decimal(str(hurdle_rate))
        gains_above_hurdle = max(Decimal("0"), amount - hurdle_amount - high_water_mark)
        fee_amount = gains_above_hurdle * Decimal(str(performance_rate))
        
        return {
            "fee_type": "performance",
            "total_gains": float(amount),
            "hurdle_rate_percent": parameters.get("hurdle_rate", 0.0),
            "hurdle_amount": float(hurdle_amount),
            "high_water_mark": float(high_water_mark),
            "gains_above_hurdle": float(gains_above_hurdle),
            "performance_rate_percent": parameters.get("performance_rate"),
            "fee_amount": float(fee_amount),
            "currency": "AUD"
        }
    
    elif fee_type == "tiered":
        # Tiered fee: Different rates for different brackets
        tiers = parameters.get("tiers", [])
        total_fee = Decimal("0")
        remaining_amount = amount
        breakdown = []
        
        for tier in tiers:
            threshold = Decimal(str(tier.get("threshold", 0))) if tier.get("threshold") else None
            rate = Decimal(str(tier.get("rate", 0))) / 100
            
            if threshold is None:
                # Last tier - all remaining amount
                tier_amount = remaining_amount
            else:
                # Calculate amount in this tier
                tier_amount = min(remaining_amount, threshold)
            
            tier_fee = tier_amount * rate
            total_fee += tier_fee
            
            breakdown.append({
                "tier_threshold": float(threshold) if threshold else None,
                "tier_rate_percent": tier.get("rate"),
                "tier_amount": float(tier_amount),
                "tier_fee": float(tier_fee)
            })
            
            remaining_amount -= tier_amount
            if remaining_amount <= 0:
                break
        
        return {
            "fee_type": "tiered",
            "total_amount": float(amount),
            "tier_breakdown": breakdown,
            "total_fee": float(total_fee),
            "currency": "AUD"
        }
    
    elif fee_type == "transaction":
        # Transaction fee: Fixed or percentage per trade
        if "fixed_fee" in parameters:
            fee_amount = Decimal(str(parameters["fixed_fee"]))
        else:
            percentage = Decimal(str(parameters.get("percentage", 0.1))) / 100
            fee_amount = amount * percentage
        
        # Apply min/max caps
        min_fee = Decimal(str(parameters.get("min_fee", 0)))
        max_fee = Decimal(str(parameters.get("max_fee", 999999)))
        fee_amount = max(min_fee, min(fee_amount, max_fee))
        
        return {
            "fee_type": "transaction",
            "transaction_value": float(amount),
            "fee_amount": float(fee_amount),
            "currency": "AUD"
        }
    
    else:
        return {
            "error": f"Unknown fee type: {fee_type}"
        }

async def get_fee_schedule(client_id: str, tenant_id: str) -> Dict:
    """Get fee schedule for a client
    
    Args:
        client_id: Client ID
        tenant_id: Tenant ID
    
    Returns:
        Complete fee schedule for the client
    """
    return {
        "client_id": client_id,
        "tenant_id": tenant_id,
        "fee_schedule": {
            "management_fee": {
                "annual_rate_percent": 1.0,
                "billing_frequency": "monthly",
                "min_fee": 0,
                "max_fee": None
            },
            "performance_fee": {
                "performance_rate_percent": 20.0,
                "hurdle_rate_percent": 8.0,
                "high_water_mark": 1000000.00,
                "billing_frequency": "annual"
            },
            "transaction_fee": {
                "percentage": 0.1,
                "min_fee": 10.00,
                "max_fee": 100.00
            }
        },
        "subscription_tier": "PRO",
        "custom_pricing": False,
        "effective_date": "2024-01-01",
        "next_review_date": "2025-01-01"
    }

async def optimize_fee_structure(portfolio_value: Decimal,
                                client_tier: str,
                                tenant_id: str) -> Dict:
    """Optimize fee structure for a client
    
    Args:
        portfolio_value: Current portfolio value
        client_tier: Client tier (BASIC, PRO, PREMIUM, ENTERPRISE)
        tenant_id: Tenant ID
    
    Returns:
        Optimized fee structure recommendations
    """
    # Tiered pricing based on portfolio value
    if portfolio_value < Decimal("100000"):
        tier = "BASIC"
        management_fee = 1.5
        performance_fee = 20.0
    elif portfolio_value < Decimal("500000"):
        tier = "PRO"
        management_fee = 1.0
        performance_fee = 20.0
    elif portfolio_value < Decimal("2000000"):
        tier = "PREMIUM"
        management_fee = 0.75
        performance_fee = 15.0
    else:
        tier = "ENTERPRISE"
        management_fee = 0.5
        performance_fee = 10.0
    
    # Calculate annual fees
    annual_management_fee = float(portfolio_value) * (management_fee / 100)
    
    # Estimate performance fee (assume 10% annual return)
    estimated_gains = float(portfolio_value) * 0.10
    estimated_performance_fee = estimated_gains * (performance_fee / 100)
    
    total_estimated_fees = annual_management_fee + estimated_performance_fee
    effective_rate = (total_estimated_fees / float(portfolio_value)) * 100
    
    return {
        "portfolio_value": float(portfolio_value),
        "recommended_tier": tier,
        "current_tier": client_tier,
        "tier_upgrade_available": tier != client_tier,
        "recommended_fees": {
            "management_fee_percent": management_fee,
            "performance_fee_percent": performance_fee,
            "annual_management_fee": annual_management_fee,
            "estimated_performance_fee": estimated_performance_fee,
            "total_estimated_annual_fees": total_estimated_fees,
            "effective_rate_percent": effective_rate
        },
        "savings_vs_current": {
            "amount": 0,  # Would calculate based on current fees
            "percent": 0
        },
        "recommendation": f"Upgrade to {tier} tier for lower fees" if tier != client_tier else "Current tier is optimal"
    }

async def calculate_australian_gst(fee_amount: Decimal,
                                   gst_registered: bool) -> Dict:
    """Calculate Australian GST on fees
    
    Args:
        fee_amount: Fee amount before GST
        gst_registered: Whether the client is GST registered
    
    Returns:
        GST calculation details
    """
    gst_rate = Decimal("0.10")  # 10% GST in Australia
    
    if gst_registered:
        # GST registered - can claim input tax credit
        gst_amount = fee_amount * gst_rate
        total_amount = fee_amount + gst_amount
        
        return {
            "fee_amount_ex_gst": float(fee_amount),
            "gst_rate_percent": 10.0,
            "gst_amount": float(gst_amount),
            "total_amount_inc_gst": float(total_amount),
            "gst_registered": True,
            "input_tax_credit_available": True,
            "net_cost": float(fee_amount)  # Can claim GST back
        }
    else:
        # Not GST registered - cannot claim GST
        gst_amount = fee_amount * gst_rate
        total_amount = fee_amount + gst_amount
        
        return {
            "fee_amount_ex_gst": float(fee_amount),
            "gst_rate_percent": 10.0,
            "gst_amount": float(gst_amount),
            "total_amount_inc_gst": float(total_amount),
            "gst_registered": False,
            "input_tax_credit_available": False,
            "net_cost": float(total_amount)  # Full amount including GST
        }
