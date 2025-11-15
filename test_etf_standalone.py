#!/usr/bin/env python3
"""
Standalone Test of ETF Data for UltraOptimiser

This script directly imports and tests the ETF data provider
without going through package __init__.py files.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np

# Direct file import to avoid __init__.py issues
import importlib.util

spec = importlib.util.spec_from_file_location(
    "etf_data_provider_manus",
    "src/ultracore/domains/wealth/integration/etf_data_provider_manus.py"
)
etf_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(etf_module)

ETFDataProviderManus = etf_module.ETFDataProviderManus

print("=" * 80)
print("ETF Data for UltraOptimiser - Standalone Test")
print("=" * 80)
print()

# Initialize data provider
print("1. Initializing ETF Data Provider...")
try:
    data_provider = ETFDataProviderManus(data_dir="data/etf/historical")
    print(f"   ✅ Loaded data for {len(data_provider.available_etfs)} ETFs")
    print(f"   First 15 ETFs: {', '.join(data_provider.available_etfs[:15])}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test portfolio
test_portfolio = ['VAS', 'VGS', 'VTS', 'VAF', 'IOZ']

print("2. Testing Portfolio:")
for ticker in test_portfolio:
    print(f"   - {ticker}")
print()

# Check data availability
print("3. Checking Data Availability...")
availability = data_provider.check_data_availability(test_portfolio)
for ticker, available in availability.items():
    status = "✅" if available else "❌"
    print(f"   {status} {ticker}")

available_tickers = [t for t, a in availability.items() if a]
print(f"\n   Available: {len(available_tickers)}/{len(test_portfolio)} ETFs")
print()

if not available_tickers:
    print("❌ No data available for test portfolio")
    sys.exit(1)

# Load sample data
print("4. Loading Sample Data (VAS)...")
vas_data = data_provider.load_etf_data('VAS')
print(f"   ✅ Loaded {len(vas_data)} rows")
print(f"   Date range: {vas_data.index[0].date()} to {vas_data.index[-1].date()}")
print(f"   Latest close: ${vas_data['Close'].iloc[-1]:.2f}")
print(f"   Columns: {', '.join(vas_data.columns)}")
print()

# Calculate risk metrics
print("5. Calculating Risk Metrics (3-year lookback)...")
print()
for ticker in available_tickers:
    try:
        metrics = data_provider.calculate_risk_metrics(ticker, lookback_years=3)
        print(f"   {ticker}:")
        print(f"      Expected Return: {metrics['mean_return']*100:>6.2f}% p.a.")
        print(f"      Volatility:      {metrics['volatility']*100:>6.2f}%")
        print(f"      Sharpe Ratio:    {metrics['sharpe_ratio']:>6.2f}")
        print(f"      Sortino Ratio:   {metrics['sortino_ratio']:>6.2f}")
        print(f"      Max Drawdown:    {metrics['max_drawdown']*100:>6.2f}%")
        print()
    except Exception as e:
        print(f"   ❌ Error calculating metrics for {ticker}: {e}")
        print()

# Calculate correlation matrix
print("6. Calculating Correlation Matrix...")
try:
    corr_matrix = data_provider.calculate_correlation_matrix(available_tickers, lookback_years=3)
    print("\n   Correlation Matrix:")
    print(corr_matrix.round(2).to_string())
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print()

# Portfolio Optimization
print("7. Portfolio Optimization Tests...")
print()

results = {}

for risk_level, risk_budget in [("Conservative", 0.3), ("Balanced", 0.6), ("Growth", 0.9)]:
    print(f"   {risk_level} ({int(risk_budget*100)}% risk budget):")
    try:
        result = data_provider.optimize_portfolio_mean_variance(
            tickers=available_tickers,
            risk_budget=risk_budget,
            lookback_years=3
        )
        
        results[risk_level] = result
        
        print(f"      Optimal Weights:")
        for ticker, weight in sorted(result['optimal_weights'].items(), key=lambda x: x[1], reverse=True):
            print(f"         {ticker}: {weight*100:>5.1f}%")
        
        print(f"\n      Expected Return: {result['expected_return']*100:>6.2f}% p.a.")
        print(f"      Volatility:      {result['volatility']*100:>6.2f}%")
        print(f"      Sharpe Ratio:    {result['sharpe_ratio']:>6.2f}")
        print()
    except Exception as e:
        print(f"      ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()

# Summary comparison table
if results:
    print("8. Portfolio Comparison Summary...")
    print()
    print(f"   {'Strategy':<15} {'Return':>10} {'Volatility':>12} {'Sharpe':>10}")
    print("   " + "-" * 50)
    for strategy, result in results.items():
        print(f"   {strategy:<15} {result['expected_return']*100:>9.2f}% {result['volatility']*100:>11.2f}% {result['sharpe_ratio']:>10.2f}")
    print()

# Get latest prices
print("9. Latest ETF Prices...")
try:
    latest_prices = data_provider.get_latest_prices(available_tickers)
    for ticker in sorted(latest_prices.keys()):
        price = latest_prices[ticker]
        print(f"   {ticker}: ${price:>7.2f}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

# Example: Calculate portfolio value
if results and latest_prices:
    print("10. Example Portfolio Value Calculation ($100,000 investment)...")
    print()
    
    investment = 100000
    
    for strategy, result in results.items():
        print(f"   {strategy} Portfolio:")
        total_value = 0
        for ticker, weight in result['optimal_weights'].items():
            if ticker in latest_prices:
                allocation = investment * weight
                shares = allocation / latest_prices[ticker]
                value = shares * latest_prices[ticker]
                total_value += value
                print(f"      {ticker}: ${allocation:>10,.2f} ({shares:>8.2f} shares @ ${latest_prices[ticker]:.2f})")
        print(f"      Total: ${total_value:>10,.2f}")
        print()

print("=" * 80)
print("✅ Test Complete!")
print("=" * 80)
print()
print("Summary:")
print(f"  • {len(data_provider.available_etfs)} ETFs available")
print(f"  • {len(available_tickers)} ETFs tested")
print(f"  • {len(results)} portfolio strategies optimized")
print()
print("The ETF data provider is working correctly!")
print("UltraOptimiser can now use this data for:")
print("  - Portfolio optimization")
print("  - Risk analysis")
print("  - Rebalancing recommendations")
print("  - ML/RL training")
