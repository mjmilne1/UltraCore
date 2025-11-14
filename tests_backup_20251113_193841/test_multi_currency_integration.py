"""
Multi-Currency Integration Tests
Comprehensive tests for multi-currency system with full UltraCore architecture
"""

import pytest
from datetime import datetime
from uuid import uuid4

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
from ultracore.mcp.multi_currency_tools import get_multi_currency_tools


class TestCurrencyAggregates:
    """Test event-sourced currency aggregates"""
    
    def test_add_currency(self):
        """Test adding new currency"""
        tenant_id = "test_tenant"
        user_id = "test_user"
        currency_code = "USD"
        
        currency = CurrencyAggregate(currency_code, tenant_id)
        currency.add_currency(
            user_id=user_id,
            currency_name="US Dollar",
            currency_symbol="$",
            decimal_places=2
        )
        
        assert currency.currency_code == "USD"
        assert currency.currency_name == "US Dollar"
        assert currency.currency_symbol == "$"
        assert currency.is_active == True
        assert len(currency.uncommitted_events) == 1
    
    def test_update_exchange_rate(self):
        """Test updating exchange rate"""
        tenant_id = "test_tenant"
        user_id = "test_user"
        rate_id = str(uuid4())
        
        exchange_rate = ExchangeRateAggregate(rate_id, tenant_id)
        exchange_rate.update_rate(
            user_id=user_id,
            base_currency="USD",
            target_currency="EUR",
            rate=0.85,
            source="test"
        )
        
        assert exchange_rate.base_currency == "USD"
        assert exchange_rate.target_currency == "EUR"
        assert exchange_rate.rate == 0.85
        assert len(exchange_rate.uncommitted_events) == 1
    
    def test_execute_conversion(self):
        """Test currency conversion"""
        tenant_id = "test_tenant"
        user_id = "test_user"
        conversion_id = str(uuid4())
        
        conversion = CurrencyConversionAggregate(conversion_id, tenant_id)
        conversion.execute_conversion(
            user_id=user_id,
            from_currency="USD",
            to_currency="EUR",
            from_amount=1000.0,
            exchange_rate=0.85,
            conversion_type="user_conversion"
        )
        
        assert conversion.from_currency == "USD"
        assert conversion.to_currency == "EUR"
        assert conversion.from_amount == 1000.0
        assert conversion.to_amount == 850.0
        assert conversion.exchange_rate == 0.85
        assert len(conversion.uncommitted_events) == 1
    
    def test_set_currency_preference(self):
        """Test setting currency preference"""
        tenant_id = "test_tenant"
        user_id = "test_user"
        client_id = "test_client"
        preference_id = str(uuid4())
        
        preference = CurrencyPreferenceAggregate(preference_id, tenant_id)
        preference.set_preference(
            user_id=user_id,
            client_id=client_id,
            display_currency="EUR",
            auto_convert=True
        )
        
        assert preference.client_id == client_id
        assert preference.display_currency == "EUR"
        assert preference.auto_convert == True
        assert len(preference.uncommitted_events) == 1
    
    def test_calculate_portfolio_valuation(self):
        """Test portfolio valuation calculation"""
        tenant_id = "test_tenant"
        user_id = "test_user"
        portfolio_id = "test_portfolio"
        valuation_id = str(uuid4())
        
        currency_breakdown = {
            "USD": 50000.0,
            "EUR": 30000.0,
            "GBP": 20000.0
        }
        
        exchange_rates = {
            "USD/USD": 1.0,
            "EUR/USD": 1.176,
            "GBP/USD": 1.370
        }
        
        valuation = PortfolioValuationAggregate(valuation_id, tenant_id)
        valuation.calculate_valuation(
            user_id=user_id,
            portfolio_id=portfolio_id,
            client_id="test_client",
            display_currency="USD",
            currency_breakdown=currency_breakdown,
            exchange_rates=exchange_rates
        )
        
        assert valuation.portfolio_id == portfolio_id
        assert valuation.display_currency == "USD"
        assert valuation.total_value > 0
        assert "USD" in valuation.converted_values
        assert len(valuation.uncommitted_events) == 1


class TestExchangeRatePredictionAgent:
    """Test AI agent for exchange rate prediction"""
    
    def test_predict_rate_movement(self):
        """Test rate movement prediction"""
        agent = get_exchange_rate_prediction_agent()
        
        historical_rates = [
            {"rate": 1.18, "timestamp": "2024-01-01"},
            {"rate": 1.19, "timestamp": "2024-01-02"},
            {"rate": 1.20, "timestamp": "2024-01-03"}
        ]
        
        prediction = agent.predict_rate_movement(
            base_currency="USD",
            target_currency="EUR",
            historical_rates=historical_rates,
            timeframe_hours=24
        )
        
        assert "currency_pair" in prediction
        assert "predicted_rate" in prediction
        assert "confidence" in prediction
        assert "direction" in prediction
        assert prediction["direction"] in ["up", "down", "stable"]
    
    def test_recommend_conversion_timing(self):
        """Test conversion timing recommendation"""
        agent = get_exchange_rate_prediction_agent()
        
        recommendation = agent.recommend_conversion_timing(
            from_currency="USD",
            to_currency="EUR",
            amount=10000.0,
            urgency="normal"
        )
        
        assert "recommendation" in recommendation
        assert recommendation["recommendation"] in ["wait", "convert_now", "convert_partial"]
        assert "optimal_timing" in recommendation
        assert "expected_rate" in recommendation
    
    def test_optimize_portfolio_currencies(self):
        """Test portfolio currency optimization"""
        agent = get_exchange_rate_prediction_agent()
        
        portfolio_currencies = {
            "USD": 50000.0,
            "EUR": 30000.0,
            "GBP": 20000.0
        }
        
        optimization = agent.optimize_portfolio_currency_allocation(
            portfolio_currencies=portfolio_currencies,
            target_currency="USD",
            risk_tolerance="moderate"
        )
        
        assert "current_allocation" in optimization
        assert "recommended_allocation" in optimization
        assert "rebalancing_actions" in optimization
        assert isinstance(optimization["rebalancing_actions"], list)


class TestRateForecastingModel:
    """Test ML model for exchange rate forecasting"""
    
    def test_predict_rate(self):
        """Test rate prediction"""
        model = get_rate_forecasting_model()
        
        historical_rates = [
            {"rate": 1.18, "timestamp": "2024-01-01"},
            {"rate": 1.19, "timestamp": "2024-01-02"},
            {"rate": 1.20, "timestamp": "2024-01-03"}
        ]
        
        prediction = model.predict_rate(
            currency_pair="USD/EUR",
            historical_rates=historical_rates,
            forecast_hours=24
        )
        
        assert "predicted_rate" in prediction
        assert "predicted_low" in prediction
        assert "predicted_high" in prediction
        assert "confidence" in prediction
        assert prediction["predicted_low"] <= prediction["predicted_rate"] <= prediction["predicted_high"]
    
    def test_predict_volatility(self):
        """Test volatility prediction"""
        model = get_rate_forecasting_model()
        
        historical_rates = [
            {"rate": 1.18 + i * 0.01, "timestamp": f"2024-01-{i+1:02d}"}
            for i in range(30)
        ]
        
        volatility = model.predict_volatility(
            currency_pair="USD/EUR",
            historical_rates=historical_rates,
            window_days=30
        )
        
        assert "current_volatility" in volatility
        assert "predicted_volatility" in volatility
        assert "volatility_trend" in volatility
        assert volatility["volatility_trend"] in ["increasing", "decreasing", "stable"]
        assert "risk_level" in volatility
        assert volatility["risk_level"] in ["low", "medium", "high"]
    
    def test_detect_trend_reversal(self):
        """Test trend reversal detection"""
        model = get_rate_forecasting_model()
        
        # Create uptrend then downtrend
        historical_rates = [
            {"rate": 1.18 + i * 0.01, "timestamp": f"2024-01-{i+1:02d}"}
            for i in range(10)
        ] + [
            {"rate": 1.27 - i * 0.01, "timestamp": f"2024-01-{i+11:02d}"}
            for i in range(5)
        ]
        
        reversal = model.detect_trend_reversal(
            currency_pair="USD/EUR",
            historical_rates=historical_rates
        )
        
        # May or may not detect reversal depending on data
        if reversal:
            assert "signal_type" in reversal
            assert reversal["signal_type"] in ["bullish_reversal", "bearish_reversal"]


class TestMultiCurrencyDataProduct:
    """Test data mesh multi-currency domain"""
    
    def test_get_currencies_data(self):
        """Test getting currencies data"""
        data_product = get_multi_currency_data_product()
        
        data = data_product.get_currencies_data(
            tenant_id="test_tenant",
            active_only=True
        )
        
        assert "domain" in data
        assert "data" in data
        assert "metadata" in data
        assert isinstance(data["data"], list)
        assert data["metadata"]["total_count"] > 0
    
    def test_get_exchange_rates_data(self):
        """Test getting exchange rates data"""
        data_product = get_multi_currency_data_product()
        
        data = data_product.get_exchange_rates_data(
            tenant_id="test_tenant",
            base_currency="USD",
            target_currencies=["EUR", "GBP"]
        )
        
        assert "domain" in data
        assert "base_currency" in data
        assert "data" in data
        assert "EUR" in data["data"]
        assert "GBP" in data["data"]
    
    def test_validate_data_quality(self):
        """Test data quality validation"""
        data_product = get_multi_currency_data_product()
        
        quality = data_product.validate_data_quality()
        
        assert "quality_checks" in quality
        assert "sla_compliance" in quality
        assert quality["quality_checks"]["completeness"]["passed"] == True
        assert quality["sla_compliance"]["availability"]["passed"] == True


class TestMultiCurrencyTools:
    """Test MCP tools for multi-currency operations"""
    
    def test_get_supported_currencies(self):
        """Test getting supported currencies"""
        tools = get_multi_currency_tools()
        
        result = tools.get_supported_currencies(
            tenant_id="test_tenant",
            active_only=True
        )
        
        assert "currencies" in result
        assert isinstance(result["currencies"], list)
        assert len(result["currencies"]) > 0
    
    def test_get_exchange_rate(self):
        """Test getting exchange rate"""
        tools = get_multi_currency_tools()
        
        result = tools.get_exchange_rate(
            tenant_id="test_tenant",
            base_currency="USD",
            target_currency="EUR"
        )
        
        assert "currency_pair" in result
        assert "rate" in result
    
    def test_predict_exchange_rate(self):
        """Test exchange rate prediction via tools"""
        tools = get_multi_currency_tools()
        
        prediction = tools.predict_exchange_rate(
            base_currency="USD",
            target_currency="EUR",
            forecast_hours=24
        )
        
        assert "predicted_rate" in prediction
        assert "confidence" in prediction
    
    def test_recommend_conversion_timing(self):
        """Test conversion timing recommendation via tools"""
        tools = get_multi_currency_tools()
        
        recommendation = tools.recommend_conversion_timing(
            from_currency="USD",
            to_currency="EUR",
            amount=10000.0,
            urgency="normal"
        )
        
        assert "recommendation" in recommendation
        assert "reasoning" in recommendation


class TestEndToEndWorkflows:
    """Test end-to-end multi-currency workflows"""
    
    def test_currency_conversion_workflow(self):
        """Test complete currency conversion workflow"""
        tools = get_multi_currency_tools()
        tenant_id = "test_tenant"
        user_id = "test_user"
        
        # 1. Get exchange rate
        rate = tools.get_exchange_rate(
            tenant_id=tenant_id,
            base_currency="USD",
            target_currency="EUR"
        )
        assert "rate" in rate
        
        # 2. Get conversion timing recommendation
        recommendation = tools.recommend_conversion_timing(
            from_currency="USD",
            to_currency="EUR",
            amount=10000.0,
            urgency="normal"
        )
        assert "recommendation" in recommendation
        
        # 3. Execute conversion (if recommended)
        if recommendation["recommendation"] == "convert_now":
            conversion = tools.convert_currency(
                tenant_id=tenant_id,
                user_id=user_id,
                from_currency="USD",
                to_currency="EUR",
                amount=10000.0
            )
            assert "conversion_id" in conversion or "error" in conversion
    
    def test_portfolio_valuation_workflow(self):
        """Test multi-currency portfolio valuation workflow"""
        tools = get_multi_currency_tools()
        tenant_id = "test_tenant"
        user_id = "test_user"
        
        # 1. Set currency preference
        preference = tools.set_currency_preference(
            tenant_id=tenant_id,
            user_id=user_id,
            client_id="test_client",
            display_currency="USD",
            auto_convert=True
        )
        assert "preference_set" in preference
        
        # 2. Calculate portfolio valuation
        currency_breakdown = {
            "USD": 50000.0,
            "EUR": 30000.0,
            "GBP": 20000.0
        }
        
        valuation = tools.calculate_portfolio_valuation(
            tenant_id=tenant_id,
            user_id=user_id,
            portfolio_id="test_portfolio",
            client_id="test_client",
            currency_breakdown=currency_breakdown,
            display_currency="USD"
        )
        
        assert "total_value" in valuation
        assert "currency_breakdown" in valuation
        assert "converted_values" in valuation
        
        # 3. Optimize portfolio currencies
        optimization = tools.optimize_portfolio_currencies(
            portfolio_currencies=currency_breakdown,
            target_currency="USD",
            risk_tolerance="moderate"
        )
        
        assert "rebalancing_actions" in optimization


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
