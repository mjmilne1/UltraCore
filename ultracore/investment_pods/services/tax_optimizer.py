"""
Australian Tax Optimizer
Franking credits, CGT discount, FHSS integration
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

from ..models import TaxOptimizationStrategy, BUSINESS_RULES

logger = logging.getLogger(__name__)


@dataclass
class FrankingCreditAnalysis:
    """Franking credit analysis"""
    total_franking_credits: Decimal
    franking_yield: Decimal
    tax_benefit: Decimal  # Actual tax benefit for client
    marginal_tax_rate: Decimal


@dataclass
class CGTAnalysis:
    """Capital gains tax analysis"""
    total_capital_gain: Decimal
    long_term_gain: Decimal  # >12 months, 50% discount
    short_term_gain: Decimal  # <12 months, no discount
    cgt_discount_benefit: Decimal
    estimated_cgt_liability: Decimal
    marginal_tax_rate: Decimal


@dataclass
class FHSSAnalysis:
    """First Home Super Saver analysis"""
    eligible: bool
    contributions_to_date: Decimal
    remaining_annual_limit: Decimal
    remaining_total_limit: Decimal
    estimated_tax_benefit: Decimal


class AustralianTaxOptimizer:
    """
    Australian tax optimizer for Investment Pods
    
    Key features:
    1. Franking credits optimization (30% company tax rate)
    2. CGT 50% discount for >12 month holdings
    3. First Home Super Saver (FHSS) scheme integration
    4. Tax loss harvesting
    """
    
    def __init__(self):
        self.company_tax_rate = Decimal("0.30")  # 30% Australian company tax
        self.cgt_discount = Decimal("0.50")  # 50% CGT discount for >12 months
        self.fhss_annual_limit = Decimal("15000")  # $15,000 annual FHSS limit
        self.fhss_total_limit = Decimal("50000")  # $50,000 total FHSS limit
    
    def calculate_franking_credits(
        self,
        holdings: List[Dict],
        marginal_tax_rate: Decimal
    ) -> FrankingCreditAnalysis:
        """
        Calculate franking credits benefit
        
        Franking credits represent tax already paid by companies
        Can be used to offset personal income tax
        """
        total_franking_credits = Decimal("0")
        total_dividends = Decimal("0")
        
        for holding in holdings:
            # Franked dividends
            franking_yield = holding.get("franking_yield", Decimal("0"))
            current_value = holding.get("current_value", Decimal("0"))
            
            # Annual franked dividends
            franked_dividends = current_value * franking_yield / Decimal("100")
            
            # Franking credits (30% company tax already paid)
            # Formula: Franking Credit = Dividend × (Company Tax Rate / (1 - Company Tax Rate))
            franking_credit = franked_dividends * (self.company_tax_rate / (Decimal("1") - self.company_tax_rate))
            
            total_franking_credits += franking_credit
            total_dividends += franked_dividends
        
        # Calculate tax benefit
        # If marginal tax rate < 30%, client gets refund
        # If marginal tax rate > 30%, credits reduce tax owed
        grossed_up_dividends = total_dividends + total_franking_credits
        tax_on_dividends = grossed_up_dividends * marginal_tax_rate
        tax_benefit = total_franking_credits - tax_on_dividends
        
        # Portfolio franking yield
        total_value = sum(h.get("current_value", Decimal("0")) for h in holdings)
        franking_yield = (total_dividends / total_value * Decimal("100")) if total_value > 0 else Decimal("0")
        
        logger.info(f"Franking credits: total={total_franking_credits}, benefit={tax_benefit}")
        
        return FrankingCreditAnalysis(
            total_franking_credits=total_franking_credits,
            franking_yield=franking_yield,
            tax_benefit=tax_benefit,
            marginal_tax_rate=marginal_tax_rate
        )
    
    def calculate_cgt_liability(
        self,
        holdings: List[Dict],
        marginal_tax_rate: Decimal,
        sell_trades: Optional[List[Dict]] = None
    ) -> CGTAnalysis:
        """
        Calculate capital gains tax liability
        
        50% discount for assets held >12 months
        """
        total_capital_gain = Decimal("0")
        long_term_gain = Decimal("0")
        short_term_gain = Decimal("0")
        
        # If sell trades provided, calculate CGT on those
        # Otherwise, calculate unrealized CGT on all holdings
        if sell_trades:
            for trade in sell_trades:
                etf_code = trade["etf_code"]
                units_sold = Decimal(str(trade["units"]))
                sell_price = Decimal(str(trade["price"]))
                
                # Find holding
                holding = next((h for h in holdings if h["etf_code"] == etf_code), None)
                if not holding:
                    continue
                
                # Calculate gain
                average_price = holding.get("average_price", sell_price)
                capital_gain = (sell_price - average_price) * units_sold
                
                # Check holding period
                purchase_date = holding.get("purchase_date")
                if purchase_date:
                    holding_days = (date.today() - purchase_date).days
                    if holding_days >= 365:
                        long_term_gain += capital_gain
                    else:
                        short_term_gain += capital_gain
                else:
                    # Unknown holding period - assume short term (conservative)
                    short_term_gain += capital_gain
                
                total_capital_gain += capital_gain
        else:
            # Calculate unrealized CGT on all holdings
            for holding in holdings:
                unrealized_gain = holding.get("unrealized_gain", Decimal("0"))
                
                # Check holding period
                purchase_date = holding.get("purchase_date")
                if purchase_date:
                    holding_days = (date.today() - purchase_date).days
                    if holding_days >= 365:
                        long_term_gain += unrealized_gain
                    else:
                        short_term_gain += unrealized_gain
                else:
                    short_term_gain += unrealized_gain
                
                total_capital_gain += unrealized_gain
        
        # Calculate CGT liability
        # Long-term: 50% discount
        taxable_long_term = long_term_gain * self.cgt_discount
        taxable_short_term = short_term_gain
        
        total_taxable_gain = taxable_long_term + taxable_short_term
        cgt_liability = total_taxable_gain * marginal_tax_rate
        
        # CGT discount benefit
        cgt_discount_benefit = long_term_gain * self.cgt_discount * marginal_tax_rate
        
        logger.info(f"CGT: total_gain={total_capital_gain}, liability={cgt_liability}, discount_benefit={cgt_discount_benefit}")
        
        return CGTAnalysis(
            total_capital_gain=total_capital_gain,
            long_term_gain=long_term_gain,
            short_term_gain=short_term_gain,
            cgt_discount_benefit=cgt_discount_benefit,
            estimated_cgt_liability=cgt_liability,
            marginal_tax_rate=marginal_tax_rate
        )
    
    def optimize_for_cgt_discount(
        self,
        holdings: List[Dict],
        proposed_trades: List[Dict]
    ) -> Tuple[List[Dict], Decimal]:
        """
        Optimize trades to maximize CGT discount
        
        Prefer selling holdings >12 months old
        """
        optimized_trades = []
        tax_savings = Decimal("0")
        
        for trade in proposed_trades:
            if trade["action"] != "SELL":
                optimized_trades.append(trade)
                continue
            
            etf_code = trade["etf_code"]
            units_to_sell = trade["units"]
            
            # Find all holdings for this ETF (may have multiple purchase dates)
            etf_holdings = [h for h in holdings if h["etf_code"] == etf_code]
            
            if not etf_holdings:
                optimized_trades.append(trade)
                continue
            
            # Sort by holding period (longest first for CGT discount)
            etf_holdings_sorted = sorted(
                etf_holdings,
                key=lambda h: h.get("purchase_date", date.today()),
                reverse=False  # Oldest first
            )
            
            # Select units from longest-held parcels first
            remaining_units = units_to_sell
            for holding in etf_holdings_sorted:
                if remaining_units <= 0:
                    break
                
                holding_units = holding.get("units", Decimal("0"))
                units_from_parcel = min(remaining_units, holding_units)
                
                # Check if eligible for CGT discount
                purchase_date = holding.get("purchase_date")
                if purchase_date and (date.today() - purchase_date).days >= 365:
                    # Eligible for 50% discount
                    capital_gain = (trade["price"] - holding.get("average_price", trade["price"])) * units_from_parcel
                    tax_saving = capital_gain * self.cgt_discount * Decimal("0.37")  # Assume 37% marginal rate
                    tax_savings += tax_saving
                
                remaining_units -= units_from_parcel
            
            optimized_trades.append(trade)
        
        logger.info(f"CGT optimization: tax_savings={tax_savings}")
        return optimized_trades, tax_savings
    
    def analyze_fhss_eligibility(
        self,
        client_age: int,
        is_first_home_buyer: bool,
        fhss_contributions_to_date: Decimal,
        current_financial_year_contributions: Decimal
    ) -> FHSSAnalysis:
        """
        Analyze First Home Super Saver (FHSS) scheme eligibility
        
        FHSS allows first home buyers to save inside super with tax benefits
        """
        eligible = is_first_home_buyer and client_age >= 18
        
        # Calculate remaining limits
        remaining_annual_limit = self.fhss_annual_limit - current_financial_year_contributions
        remaining_total_limit = self.fhss_total_limit - fhss_contributions_to_date
        
        # Estimate tax benefit
        # FHSS contributions taxed at 15% (super rate) vs marginal rate
        # Assume 37% marginal rate
        marginal_rate = Decimal("0.37")
        super_rate = Decimal("0.15")
        tax_benefit_rate = marginal_rate - super_rate  # 22% benefit
        
        estimated_tax_benefit = remaining_total_limit * tax_benefit_rate
        
        logger.info(f"FHSS analysis: eligible={eligible}, remaining_total={remaining_total_limit}")
        
        return FHSSAnalysis(
            eligible=eligible,
            contributions_to_date=fhss_contributions_to_date,
            remaining_annual_limit=max(Decimal("0"), remaining_annual_limit),
            remaining_total_limit=max(Decimal("0"), remaining_total_limit),
            estimated_tax_benefit=estimated_tax_benefit if eligible else Decimal("0")
        )
    
    def identify_tax_loss_harvesting_opportunities(
        self,
        holdings: List[Dict],
        marginal_tax_rate: Decimal
    ) -> List[Dict]:
        """
        Identify tax loss harvesting opportunities
        
        Sell holdings with losses to offset capital gains
        """
        opportunities = []
        
        for holding in holdings:
            unrealized_gain = holding.get("unrealized_gain", Decimal("0"))
            
            # Loss position
            if unrealized_gain < 0:
                loss_amount = abs(unrealized_gain)
                tax_benefit = loss_amount * marginal_tax_rate
                
                opportunities.append({
                    "etf_code": holding["etf_code"],
                    "etf_name": holding.get("etf_name", ""),
                    "loss_amount": loss_amount,
                    "tax_benefit": tax_benefit,
                    "current_value": holding.get("current_value", Decimal("0")),
                    "recommendation": "Sell to harvest tax loss"
                })
        
        # Sort by tax benefit (highest first)
        opportunities.sort(key=lambda x: x["tax_benefit"], reverse=True)
        
        logger.info(f"Tax loss harvesting: {len(opportunities)} opportunities identified")
        return opportunities
    
    def calculate_optimal_franking_allocation(
        self,
        etf_universe: List,
        target_franking_yield: Decimal,
        max_allocation: Decimal = Decimal("40.0")
    ) -> List[Dict]:
        """
        Calculate optimal allocation to maximize franking credits
        
        Subject to diversification constraints
        """
        # Filter Australian equity ETFs (only Australian companies pay franking credits)
        aus_equity_etfs = [
            etf for etf in etf_universe
            if etf.asset_class.value == "australian_equity" and etf.is_eligible
        ]
        
        # Sort by franking yield
        aus_equity_etfs.sort(key=lambda e: e.franking_yield, reverse=True)
        
        # Select top ETFs
        selected_etfs = []
        total_allocation = Decimal("0")
        
        for etf in aus_equity_etfs[:3]:  # Max 3 ETFs for franking optimization
            if total_allocation >= max_allocation:
                break
            
            allocation = min(Decimal("20.0"), max_allocation - total_allocation)  # Max 20% per ETF
            
            selected_etfs.append({
                "etf_code": etf.etf_code,
                "etf_name": etf.etf_name,
                "allocation": allocation,
                "franking_yield": etf.franking_yield,
                "expected_franking_credits": allocation / Decimal("100") * etf.franking_yield
            })
            
            total_allocation += allocation
        
        return selected_etfs
    
    def generate_tax_optimization_report(
        self,
        franking_analysis: FrankingCreditAnalysis,
        cgt_analysis: CGTAnalysis,
        fhss_analysis: Optional[FHSSAnalysis] = None
    ) -> str:
        """Generate tax optimization report for client"""
        report = f"""
💰 Australian Tax Optimization Report

Franking Credits:
• Total Franking Credits: ${franking_analysis.total_franking_credits:,.2f}
• Portfolio Franking Yield: {franking_analysis.franking_yield:.2f}%
• Annual Tax Benefit: ${franking_analysis.tax_benefit:,.2f}

Capital Gains Tax:
• Total Capital Gains: ${cgt_analysis.total_capital_gain:,.2f}
• Long-term Gains (>12 months): ${cgt_analysis.long_term_gain:,.2f}
• Short-term Gains (<12 months): ${cgt_analysis.short_term_gain:,.2f}
• CGT Discount Benefit: ${cgt_analysis.cgt_discount_benefit:,.2f}
• Estimated CGT Liability: ${cgt_analysis.estimated_cgt_liability:,.2f}
"""
        
        if fhss_analysis and fhss_analysis.eligible:
            report += f"""
First Home Super Saver (FHSS):
• Eligible: Yes ✅
• Contributions to Date: ${fhss_analysis.contributions_to_date:,.2f}
• Remaining Annual Limit: ${fhss_analysis.remaining_annual_limit:,.2f}
• Remaining Total Limit: ${fhss_analysis.remaining_total_limit:,.2f}
• Estimated Tax Benefit: ${fhss_analysis.estimated_tax_benefit:,.2f}
"""
        
        return report.strip()
    
    def calculate_after_tax_return(
        self,
        gross_return: Decimal,
        franking_credits: Decimal,
        cgt_liability: Decimal,
        portfolio_value: Decimal
    ) -> Decimal:
        """Calculate after-tax return"""
        # Gross return
        gross_gain = portfolio_value * gross_return / Decimal("100")
        
        # Add franking credit benefit
        after_tax_gain = gross_gain + franking_credits - cgt_liability
        
        # After-tax return percentage
        after_tax_return = (after_tax_gain / portfolio_value) * Decimal("100")
        
        return after_tax_return
