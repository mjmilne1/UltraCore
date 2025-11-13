"""
Multi-Currency MCP Tools
MCP tools for currency operations, exchange rates, and portfolio valuation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging
import requests

from ultracore.multi_currency.aggregates import (
    CurrencyAggregate,
    ExchangeRateAggregate,
    CurrencyConversionAggregate,
    CurrencyPreferenceAggregate,
    PortfolioValuationAggregate
)
from ultracore.agentic_ai.agents.forex import get_exchange_rate_prediction_agent
from ultracore.ml.forex import get_rate_forecasting_model
from ultracore.datamesh.multi_currency_mesh import get_multi_currency_data_product

logger = logging.getLogger(__name__)


class MultiCurrencyTools:
    """
    MCP Tools for multi-currency operations
    
    Tools:
    - Currency management
    - Exchange rate fetching
    - Currency conversion
    - Portfolio valuation
    - Rate prediction
    - Conversion timing optimization
    """
    
    def __init__(self):
        self.prediction_agent = get_exchange_rate_prediction_agent()
        self.forecasting_model = get_rate_forecasting_model()
        self.data_product = get_multi_currency_data_product()
        
        # Exchange rate API configuration
        self.exchange_rate_api_url = "https://api.exchangerate-api.com/v4/latest"
        # Alternative: "https://api.exchangeratesapi.io/latest"
        # Alternative: "https://openexchangerates.org/api/latest.json"
        
        logger.info("MultiCurrencyTools initialized")
    
    # ========================================================================
    # CURRENCY MANAGEMENT TOOLS
    # ========================================================================
    
    def add_currency(
        self,
        tenant_id: str,
        user_id: str,
        currency_code: str,
        currency_name: str,
        currency_symbol: str,
        decimal_places: int = 2
    ) -> Dict[str, Any]:
        """
        Add new currency to system
        
        Args:
            tenant_id: Tenant ID
            user_id: User performing action
            currency_code: ISO 4217 code (e.g., USD, EUR)
            currency_name: Full currency name
            currency_symbol: Currency symbol (e.g., $, €)
            decimal_places: Number of decimal places
        
        Returns:
            {
                "currency_code": str,
                "currency_added": bool,
                "message": str
            }
        """
        currency = CurrencyAggregate(currency_code, tenant_id)
        currency.add_currency(
            user_id=user_id,
            currency_name=currency_name,
            currency_symbol=currency_symbol,
            decimal_places=decimal_places
        )
        
        success = currency.commit()
        
        return {
            "currency_code": currency_code,
            "currency_added": success,
            "message": f"Currency {currency_code} added successfully" if success else "Failed to add currency"
        }
    
    def get_supported_currencies(
        self,
        tenant_id: str,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Get list of supported currencies
        
        Returns:
            {
                "currencies": [
                    {
                        "currency_code": "USD",
                        "currency_name": "US Dollar",
                        "currency_symbol": "$",
                        "decimal_places": 2
                    },
                    ...
                ]
            }
        """
        data = self.data_product.get_currencies_data(tenant_id, active_only)
        
        return {
            "currencies": data["data"]
        }
    
    # ========================================================================
    # EXCHANGE RATE TOOLS
    # ========================================================================
    
    def fetch_exchange_rates(
        self,
        tenant_id: str,
        user_id: str,
        base_currency: str = "USD",
        target_currencies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch current exchange rates from external API
        
        Args:
            tenant_id: Tenant ID
            user_id: User performing action
            base_currency: Base currency code
            target_currencies: List of target currencies (None = all)
        
        Returns:
            {
                "base_currency": str,
                "rates": {
                    "EUR": 0.85,
                    "GBP": 0.73,
                    ...
                },
                "last_updated": str,
                "source": str
            }
        """
        try:
            # Fetch from exchange rate API
            response = requests.get(
                f"{self.exchange_rate_api_url}/{base_currency}",
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            rates = data.get("rates", {})
            
            # Filter to target currencies if specified
            if target_currencies:
                rates = {k: v for k, v in rates.items() if k in target_currencies}
            
            # Store rates in event-sourced aggregate
            rate_id = str(uuid4())
            exchange_rate = ExchangeRateAggregate(rate_id, tenant_id)
            exchange_rate.fetch_batch_rates(
                user_id=user_id,
                base_currency=base_currency,
                rates=rates,
                source="exchangerate-api"
            )
            exchange_rate.commit()
            
            return {
                "base_currency": base_currency,
                "rates": rates,
                "last_updated": data.get("time_last_updated", datetime.utcnow().isoformat()),
                "source": "exchangerate-api"
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch exchange rates: {str(e)}")
            
            # Fallback to data mesh (cached rates)
            data = self.data_product.get_exchange_rates_data(tenant_id, base_currency, target_currencies)
            
            return {
                "base_currency": base_currency,
                "rates": {k: v["rate"] for k, v in data["data"].items()},
                "last_updated": data["metadata"]["last_updated"],
                "source": "cached"
            }
    
    def get_exchange_rate(
        self,
        tenant_id: str,
        base_currency: str,
        target_currency: str
    ) -> Dict[str, Any]:
        """
        Get exchange rate for specific currency pair
        
        Returns:
            {
                "currency_pair": "USD/EUR",
                "rate": 0.85,
                "inverse_rate": 1.176,
                "last_updated": str
            }
        """
        data = self.data_product.get_exchange_rates_data(tenant_id, base_currency, [target_currency])
        
        if target_currency in data["data"]:
            rate_data = data["data"][target_currency]
            return {
                "currency_pair": f"{base_currency}/{target_currency}",
                "rate": rate_data["rate"],
                "inverse_rate": rate_data["inverse_rate"],
                "last_updated": rate_data["last_updated"]
            }
        
        return {
            "currency_pair": f"{base_currency}/{target_currency}",
            "rate": None,
            "error": "Exchange rate not available"
        }
    
    # ========================================================================
    # CURRENCY CONVERSION TOOLS
    # ========================================================================
    
    def convert_currency(
        self,
        tenant_id: str,
        user_id: str,
        from_currency: str,
        to_currency: str,
        amount: float,
        client_id: Optional[str] = None,
        portfolio_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert currency amount
        
        Args:
            tenant_id: Tenant ID
            user_id: User performing action
            from_currency: Source currency
            to_currency: Target currency
            amount: Amount to convert
            client_id: Optional client ID
            portfolio_id: Optional portfolio ID
        
        Returns:
            {
                "conversion_id": str,
                "from_currency": str,
                "to_currency": str,
                "from_amount": float,
                "to_amount": float,
                "exchange_rate": float,
                "conversion_fee": float,
                "executed_at": str
            }
        """
        # Get current exchange rate
        rate_data = self.get_exchange_rate(tenant_id, from_currency, to_currency)
        
        if not rate_data.get("rate"):
            return {
                "error": "Exchange rate not available",
                "conversion_executed": False
            }
        
        exchange_rate = rate_data["rate"]
        conversion_fee = amount * 0.001  # 0.1% fee
        
        # Execute conversion
        conversion_id = str(uuid4())
        conversion = CurrencyConversionAggregate(conversion_id, tenant_id)
        conversion.execute_conversion(
            user_id=user_id,
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=amount,
            exchange_rate=exchange_rate,
            conversion_type="user_conversion",
            conversion_fee=conversion_fee,
            client_id=client_id,
            portfolio_id=portfolio_id
        )
        
        success = conversion.commit()
        
        if success:
            return {
                "conversion_id": conversion_id,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "from_amount": amount,
                "to_amount": conversion.to_amount,
                "exchange_rate": exchange_rate,
                "conversion_fee": conversion_fee,
                "executed_at": conversion.executed_at.isoformat() if conversion.executed_at else None
            }
        
        return {
            "error": "Conversion failed",
            "conversion_executed": False
        }
    
    # ========================================================================
    # PORTFOLIO VALUATION TOOLS
    # ========================================================================
    
    def calculate_portfolio_valuation(
        self,
        tenant_id: str,
        user_id: str,
        portfolio_id: str,
        client_id: str,
        currency_breakdown: Dict[str, float],  # {currency: amount}
        display_currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Calculate multi-currency portfolio valuation
        
        Args:
            tenant_id: Tenant ID
            user_id: User performing action
            portfolio_id: Portfolio ID
            client_id: Client ID
            currency_breakdown: Currency amounts in portfolio
            display_currency: Currency to display total in
        
        Returns:
            {
                "portfolio_id": str,
                "display_currency": str,
                "total_value": float,
                "currency_breakdown": Dict[str, float],
                "converted_values": Dict[str, float],
                "exchange_rates_used": Dict[str, float]
            }
        """
        # Fetch current exchange rates
        currencies = list(currency_breakdown.keys())
        rates_data = self.fetch_exchange_rates(
            tenant_id=tenant_id,
            user_id=user_id,
            base_currency=display_currency,
            target_currencies=currencies
        )
        
        # Build exchange rates dict
        exchange_rates = {}
        for currency in currencies:
            if currency == display_currency:
                exchange_rates[f"{currency}/{display_currency}"] = 1.0
            else:
                # Inverse rate (from target to base)
                rate = rates_data["rates"].get(currency)
                if rate:
                    exchange_rates[f"{currency}/{display_currency}"] = 1 / rate
        
        # Calculate valuation
        valuation_id = str(uuid4())
        valuation = PortfolioValuationAggregate(valuation_id, tenant_id)
        valuation.calculate_valuation(
            user_id=user_id,
            portfolio_id=portfolio_id,
            client_id=client_id,
            display_currency=display_currency,
            currency_breakdown=currency_breakdown,
            exchange_rates=exchange_rates
        )
        
        valuation.commit()
        
        return {
            "portfolio_id": portfolio_id,
            "display_currency": display_currency,
            "total_value": valuation.total_value,
            "currency_breakdown": valuation.currency_breakdown,
            "converted_values": valuation.converted_values,
            "exchange_rates_used": valuation.exchange_rates_used
        }
    
    def set_currency_preference(
        self,
        tenant_id: str,
        user_id: str,
        client_id: str,
        display_currency: str,
        auto_convert: bool = True
    ) -> Dict[str, Any]:
        """
        Set user currency preference
        
        Returns:
            {
                "preference_set": bool,
                "client_id": str,
                "display_currency": str,
                "auto_convert": bool
            }
        """
        preference_id = str(uuid4())
        preference = CurrencyPreferenceAggregate(preference_id, tenant_id)
        preference.set_preference(
            user_id=user_id,
            client_id=client_id,
            display_currency=display_currency,
            auto_convert=auto_convert
        )
        
        success = preference.commit()
        
        return {
            "preference_set": success,
            "client_id": client_id,
            "display_currency": display_currency,
            "auto_convert": auto_convert
        }
    
    # ========================================================================
    # AI-POWERED TOOLS
    # ========================================================================
    
    def predict_exchange_rate(
        self,
        base_currency: str,
        target_currency: str,
        forecast_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Predict future exchange rate using ML model
        
        Returns:
            {
                "currency_pair": str,
                "current_rate": float,
                "predicted_rate": float,
                "predicted_low": float,
                "predicted_high": float,
                "confidence": float,
                "forecast_timestamp": str
            }
        """
        # TODO: Fetch historical rates from data mesh
        historical_rates = []
        
        prediction = self.forecasting_model.predict_rate(
            currency_pair=f"{base_currency}/{target_currency}",
            historical_rates=historical_rates,
            forecast_hours=forecast_hours
        )
        
        return prediction
    
    def recommend_conversion_timing(
        self,
        from_currency: str,
        to_currency: str,
        amount: float,
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """
        Recommend optimal timing for currency conversion
        
        Returns:
            {
                "recommendation": "wait" | "convert_now",
                "optimal_timing": str,
                "expected_rate": float,
                "potential_savings": float,
                "reasoning": str
            }
        """
        recommendation = self.prediction_agent.recommend_conversion_timing(
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            urgency=urgency
        )
        
        return recommendation
    
    def optimize_portfolio_currencies(
        self,
        portfolio_currencies: Dict[str, float],
        target_currency: str,
        risk_tolerance: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Optimize multi-currency portfolio allocation
        
        Returns:
            {
                "current_allocation": Dict[str, float],
                "recommended_allocation": Dict[str, float],
                "rebalancing_actions": List[Dict],
                "expected_benefit": float
            }
        """
        optimization = self.prediction_agent.optimize_portfolio_currency_allocation(
            portfolio_currencies=portfolio_currencies,
            target_currency=target_currency,
            risk_tolerance=risk_tolerance
        )
        
        return optimization


def get_multi_currency_tools() -> MultiCurrencyTools:
    """Get multi-currency tools instance"""
    return MultiCurrencyTools()
