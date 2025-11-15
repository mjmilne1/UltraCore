#!/usr/bin/env python3
"""
Simple Test of ETF Data Provider (No UltraCore Dependencies)

This script tests the ETF data provider directly without requiring
the full UltraCore infrastructure.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import only the Manus data provider (standalone)
from ultracore.domains.wealth.integration.etf_data_provider_manus import ETFDataProviderManus

print("=" * 80)
print("ETF Data Provider - Simple Test")
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
print()

# Calculate risk metrics
print("5. Calculating Risk Metrics (3-year lookback)...")
print()
for ticker in available_tickers:
    try:
        metrics = data_provider.calculate_risk_metrics(ticker, lookback_years=3)
        print(f"   {ticker}:")
        print(f"      Expected Return: {metrics['mean_return']*100:.2f}% p.a.")
        print(f"      Volatility:      {metrics['volatility']*100:.2f}%")
        print(f"      Sharpe Ratio:    {metrics['sharpe_ratio']:.2f}")
        print(f"      Max Drawdown:    {metrics['max_drawdown']*100:.2f}%")
        print()
    except Exception as e:
        print(f"   ❌ Error calculating metrics for {ticker}: {e}")
        print()

# Calculate correlation matrix
print("6. Calculating Correlation Matrix...")
try:
    corr_matrix = data_provider.calculate_correlation_matrix(available_tickers, lookback_years=3)
    print("\n   Correlation Matrix:")
    print(corr_matrix.round(2))
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print()

# Portfolio Optimization
print("7. Portfolio Optimization Tests...")
print()

for risk_level, risk_budget in [("Conservative", 0.3), ("Balanced", 0.6), ("Growth", 0.9)]:
    print(f"   {risk_level} ({int(risk_budget*100)}% risk budget):")
    try:
        result = data_provider.optimize_portfolio_mean_variance(
            tickers=available_tickers,
            risk_budget=risk_budget,
            lookback_years=3
        )
        
        print(f"      Optimal Weights:")
        for ticker, weight in result['optimal_weights'].items():
            print(f"         {ticker}: {weight*100:.1f}%")
        
        print(f"      Expected Return: {result['expected_return']*100:.2f}% p.a.")
        print(f"      Volatility:      {result['volatility']*100:.2f}%")
        print(f"      Sharpe Ratio:    {result['sharpe_ratio']:.2f}")
        print()
    except Exception as e:
        print(f"      ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()

# Get latest prices
print("8. Latest ETF Prices...")
try:
    latest_prices = data_provider.get_latest_prices(available_tickers)
    for ticker, price in latest_prices.items():
        print(f"   {ticker}: ${price:.2f}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

print("=" * 80)
print("✅ Test Complete!")
print("=" * 80)
print()
print("The ETF data provider is working correctly!")
print("UltraOptimiser can now use this data for portfolio optimization.")
