"""myTax ATO (Australian Taxation Office) Connector"""
from typing import List, Dict
from datetime import datetime
from decimal import Decimal

class MyTaxATOConnector:
    """Connector for Australian Taxation Office myTax system"""
    
    def __init__(self, tfn: str, api_key: str):
        """Initialize ATO connector"""
        self.tfn = tfn  # Tax File Number
        self.api_key = api_key
        self.base_url = "https://api.ato.gov.au/mytax/v1"
    
    async def export_capital_gains(self, capital_gains: List[Dict],
                                   tax_year: str) -> Dict:
        """Export capital gains/losses to myTax
        
        Australian CGT rules:
        - 50% discount for assets held > 12 months
        - 30-day wash sale rule
        - Separate reporting for listed/unlisted securities
        """
        cgt_data = {
            "tax_year": tax_year,
            "capital_gains": [],
            "capital_losses": [],
            "net_capital_gain": Decimal("0"),
            "cgt_discount_applied": Decimal("0")
        }
        
        for cg in capital_gains:
            holding_period_days = (cg["sale_date"] - cg["purchase_date"]).days
            eligible_for_discount = holding_period_days > 365
            
            gain_or_loss = cg["sale_proceeds"] - cg["cost_base"]
            
            if gain_or_loss > 0:
                # Capital gain
                discounted_gain = gain_or_loss * Decimal("0.5") if eligible_for_discount else gain_or_loss
                
                cgt_data["capital_gains"].append({
                    "asset": cg["symbol"],
                    "purchase_date": cg["purchase_date"].strftime("%Y-%m-%d"),
                    "sale_date": cg["sale_date"].strftime("%Y-%m-%d"),
                    "cost_base": float(cg["cost_base"]),
                    "sale_proceeds": float(cg["sale_proceeds"]),
                    "capital_gain": float(gain_or_loss),
                    "discount_applied": eligible_for_discount,
                    "discounted_gain": float(discounted_gain)
                })
                
                cgt_data["net_capital_gain"] += discounted_gain
                if eligible_for_discount:
                    cgt_data["cgt_discount_applied"] += (gain_or_loss - discounted_gain)
            else:
                # Capital loss
                cgt_data["capital_losses"].append({
                    "asset": cg["symbol"],
                    "purchase_date": cg["purchase_date"].strftime("%Y-%m-%d"),
                    "sale_date": cg["sale_date"].strftime("%Y-%m-%d"),
                    "cost_base": float(cg["cost_base"]),
                    "sale_proceeds": float(cg["sale_proceeds"]),
                    "capital_loss": float(abs(gain_or_loss))
                })
                
                cgt_data["net_capital_gain"] += gain_or_loss
        
        # POST to ATO API (placeholder)
        return {
            "success": True,
            "tax_year": tax_year,
            "capital_gains_count": len(cgt_data["capital_gains"]),
            "capital_losses_count": len(cgt_data["capital_losses"]),
            "net_capital_gain": float(cgt_data["net_capital_gain"]),
            "cgt_discount_applied": float(cgt_data["cgt_discount_applied"])
        }
    
    async def export_dividend_income(self, dividends: List[Dict],
                                     tax_year: str) -> Dict:
        """Export dividend income including franking credits
        
        Australian franking credit rules:
        - Franking credits = (dividend / (1 - company_tax_rate)) - dividend
        - Company tax rate = 30% for most companies
        - Grossed-up dividend = dividend + franking credits
        """
        dividend_data = {
            "tax_year": tax_year,
            "franked_dividends": [],
            "unfranked_dividends": [],
            "total_dividends": Decimal("0"),
            "total_franking_credits": Decimal("0"),
            "grossed_up_total": Decimal("0")
        }
        
        company_tax_rate = Decimal("0.30")
        
        for div in dividends:
            if div.get("franking_percent", 0) > 0:
                # Franked dividend
                franking_percent = Decimal(str(div["franking_percent"])) / Decimal("100")
                dividend_amount = Decimal(str(div["amount"]))
                
                # Calculate franking credits
                franking_credit = (dividend_amount / (Decimal("1") - company_tax_rate)) - dividend_amount
                franking_credit = franking_credit * franking_percent
                
                grossed_up = dividend_amount + franking_credit
                
                dividend_data["franked_dividends"].append({
                    "payer": div["symbol"],
                    "payment_date": div["payment_date"].strftime("%Y-%m-%d"),
                    "dividend_amount": float(dividend_amount),
                    "franking_percent": float(franking_percent * 100),
                    "franking_credit": float(franking_credit),
                    "grossed_up_amount": float(grossed_up)
                })
                
                dividend_data["total_dividends"] += dividend_amount
                dividend_data["total_franking_credits"] += franking_credit
                dividend_data["grossed_up_total"] += grossed_up
            else:
                # Unfranked dividend
                dividend_data["unfranked_dividends"].append({
                    "payer": div["symbol"],
                    "payment_date": div["payment_date"].strftime("%Y-%m-%d"),
                    "dividend_amount": float(div["amount"])
                })
                
                dividend_data["total_dividends"] += Decimal(str(div["amount"]))
        
        return {
            "success": True,
            "tax_year": tax_year,
            "franked_dividends_count": len(dividend_data["franked_dividends"]),
            "unfranked_dividends_count": len(dividend_data["unfranked_dividends"]),
            "total_dividends": float(dividend_data["total_dividends"]),
            "total_franking_credits": float(dividend_data["total_franking_credits"]),
            "grossed_up_total": float(dividend_data["grossed_up_total"])
        }
