#!/usr/bin/env python3
"""
Test UltraOptimiser with Real ETF Data

This script demonstrates how UltraOptimiser can use the Manus-collected
ETF data for portfolio optimization.
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ultracore.domains.wealth.integration.etf_data_provider_manus import ETFDataProviderManus

print("=" * 80)
print("UltraOptimiser with Real ETF Data - Test")
print("=" * 80)
print()

# Initialize data provider
print("1. Initializing ETF Data Provider...")
try:
    data_provider = ETFDataProviderManus(data_dir="data/etf/historical")
    print(f"   ✅ Loaded data for {len(data_provider.available_etfs)} ETFs")
    print(f"   Sample ETFs: {', '.join(data_provider.available_etfs[:10])}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

print()

# Test portfolio: Diversified Australian ETF portfolio
test_portfolio = {
    'VAS': 'Vanguard Australian Shares',
    'VGS': 'Vanguard International Shares',
    'VTS': 'Vanguard US Total Market',
    'VAF': 'Vanguard Australian Fixed Interest',
    'IOZ': 'iShares Core S&P/ASX 200'
}

print("2. Testing Portfolio:")
for ticker, name in test_portfolio.items():
    print(f"   - {ticker}: {name}")
print()

# Check data availability
print("3. Checking Data Availability...")
availability = data_provider.check_data_availability(list(test_portfolio.keys()))
for ticker, available in availability.items():
    status = "✅" if available else "❌"
    print(f"   {status} {ticker}")

available_tickers = [t for t, a in availability.items() if a]
print(f"\n   Available: {len(available_tickers)}/{len(test_portfolio)} ETFs")
print()

if not available_tickers:
    print("❌ No data available for test portfolio")
    sys.exit(1)

# Calculate risk metrics for each ETF
print("4. Calculating Risk Metrics (3-year lookback)...")
print()
for ticker in available_tickers:
    metrics = data_provider.calculate_risk_metrics(ticker, lookback_years=3)
    print(f"   {ticker}:")
    print(f"      Expected Return: {metrics['mean_return']*100:.2f}% p.a.")
    print(f"      Volatility:      {metrics['volatility']*100:.2f}%")
    print(f"      Sharpe Ratio:    {metrics['sharpe_ratio']:.2f}")
    print(f"      Max Drawdown:    {metrics['max_drawdown']*100:.2f}%")
    print()

# Calculate correlation matrix
print("5. Calculating Correlation Matrix...")
corr_matrix = data_provider.calculate_correlation_matrix(available_tickers, lookback_years=3)
print("\n   Correlation Matrix:")
print(corr_matrix.round(2))
print()

# Portfolio Optimization - Conservative
print("6. Portfolio Optimization - Conservative (30% risk budget)...")
result_conservative = data_provider.optimize_portfolio_mean_variance(
    tickers=available_tickers,
    risk_budget=0.3,
    lookback_years=3
)

print("\n   Optimal Weights:")
for ticker, weight in result_conservative['optimal_weights'].items():
    print(f"      {ticker}: {weight*100:.1f}%")

print(f"\n   Expected Return: {result_conservative['expected_return']*100:.2f}% p.a.")
print(f"   Volatility:      {result_conservative['volatility']*100:.2f}%")
print(f"   Sharpe Ratio:    {result_conservative['sharpe_ratio']:.2f}")
print()

# Portfolio Optimization - Balanced
print("7. Portfolio Optimization - Balanced (60% risk budget)...")
result_balanced = data_provider.optimize_portfolio_mean_variance(
    tickers=available_tickers,
    risk_budget=0.6,
    lookback_years=3
)

print("\n   Optimal Weights:")
for ticker, weight in result_balanced['optimal_weights'].items():
    print(f"      {ticker}: {weight*100:.1f}%")

print(f"\n   Expected Return: {result_balanced['expected_return']*100:.2f}% p.a.")
print(f"   Volatility:      {result_balanced['volatility']*100:.2f}%")
print(f"   Sharpe Ratio:    {result_balanced['sharpe_ratio']:.2f}")
print()

# Portfolio Optimization - Growth
print("8. Portfolio Optimization - Growth (90% risk budget)...")
result_growth = data_provider.optimize_portfolio_mean_variance(
    tickers=available_tickers,
    risk_budget=0.9,
    lookback_years=3
)

print("\n   Optimal Weights:")
for ticker, weight in result_growth['optimal_weights'].items():
    print(f"      {ticker}: {weight*100:.1f}%")

print(f"\n   Expected Return: {result_growth['expected_return']*100:.2f}% p.a.")
print(f"   Volatility:      {result_growth['volatility']*100:.2f}%")
print(f"   Sharpe Ratio:    {result_growth['sharpe_ratio']:.2f}")
print()

# Summary comparison
print("=" * 80)
print("SUMMARY - Portfolio Comparison")
print("=" * 80)
print()
print(f"{'Strategy':<15} {'Return':<12} {'Volatility':<12} {'Sharpe':<10}")
print("-" * 80)
print(f"{'Conservative':<15} {result_conservative['expected_return']*100:>10.2f}% {result_conservative['volatility']*100:>10.2f}% {result_conservative['sharpe_ratio']:>10.2f}")
print(f"{'Balanced':<15} {result_balanced['expected_return']*100:>10.2f}% {result_balanced['volatility']*100:>10.2f}% {result_balanced['sharpe_ratio']:>10.2f}")
print(f"{'Growth':<15} {result_growth['expected_return']*100:>10.2f}% {result_growth['volatility']*100:>10.2f}% {result_growth['sharpe_ratio']:>10.2f}")
print()

# Get latest prices
print("9. Latest ETF Prices...")
latest_prices = data_provider.get_latest_prices(available_tickers)
for ticker, price in latest_prices.items():
    print(f"   {ticker}: ${price:.2f}")
print()

print("=" * 80)
print("✅ Test Complete!")
print("=" * 80)
print()
print("UltraOptimiser can now use real ETF data for portfolio optimization!")
print("The data is ready for:")
print("  - Portfolio construction")
print("  - Risk analysis")
print("  - Rebalancing recommendations")
print("  - ML/RL training")
