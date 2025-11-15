# UltraOptimiser ETF Data Integration

## Overview

UltraOptimiser can now use **real ASX ETF historical data** collected via the Manus Yahoo Finance API for portfolio optimization, risk analysis, and rebalancing recommendations.

## Features

✅ **137 ASX ETFs** with complete historical data  
✅ **Portfolio Optimization** using mean-variance optimization  
✅ **Risk Metrics** (Sharpe, Sortino, Max Drawdown, VaR, CVaR)  
✅ **Correlation Analysis** for diversification  
✅ **Expected Returns** calculation  
✅ **Latest Prices** for portfolio valuation  
✅ **Multiple Risk Profiles** (Conservative, Balanced, Growth)  

## Quick Start

### 1. Import the Data Provider

```python
from ultracore.domains.wealth.integration.etf_data_provider_manus import ETFDataProviderManus

# Initialize with data directory
data_provider = ETFDataProviderManus(data_dir="data/etf/historical")

# Check available ETFs
print(f"Available ETFs: {len(data_provider.available_etfs)}")
print(data_provider.available_etfs[:10])
```

### 2. Load ETF Data

```python
# Load single ETF
vas_data = data_provider.load_etf_data('VAS')
print(f"Rows: {len(vas_data)}")
print(f"Date range: {vas_data.index[0]} to {vas_data.index[-1]}")
print(f"Latest close: ${vas_data['Close'].iloc[-1]:.2f}")
```

### 3. Calculate Risk Metrics

```python
# Get comprehensive risk metrics
metrics = data_provider.calculate_risk_metrics('VAS', lookback_years=3)

print(f"Expected Return: {metrics['mean_return']*100:.2f}% p.a.")
print(f"Volatility: {metrics['volatility']*100:.2f}%")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
print(f"VaR (95%): {metrics['var_95']*100:.2f}%")
print(f"CVaR (95%): {metrics['cvar_95']*100:.2f}%")
```

### 4. Optimize Portfolio

```python
# Define portfolio
tickers = ['VAS', 'VGS', 'VTS', 'VAF', 'IOZ']

# Optimize for balanced risk profile
result = data_provider.optimize_portfolio_mean_variance(
    tickers=tickers,
    risk_budget=0.6,  # 60% risk tolerance
    lookback_years=3
)

# Display results
print("Optimal Weights:")
for ticker, weight in result['optimal_weights'].items():
    print(f"  {ticker}: {weight*100:.1f}%")

print(f"\nExpected Return: {result['expected_return']*100:.2f}% p.a.")
print(f"Volatility: {result['volatility']*100:.2f}%")
print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
```

### 5. Analyze Correlations

```python
# Calculate correlation matrix
corr_matrix = data_provider.calculate_correlation_matrix(tickers, lookback_years=3)
print(corr_matrix.round(2))
```

## Risk Profiles

The data provider supports three standard risk profiles:

### Conservative (30% risk budget)
- **Target Volatility**: 10-15%
- **Typical Allocation**: Higher fixed income, lower equities
- **Suitable For**: Risk-averse investors, near retirement

### Balanced (60% risk budget)
- **Target Volatility**: 15-20%
- **Typical Allocation**: Balanced equities and fixed income
- **Suitable For**: Moderate risk tolerance, medium-term goals

### Growth (90% risk budget)
- **Target Volatility**: 20-30%
- **Typical Allocation**: Higher equities, lower fixed income
- **Suitable For**: Risk-tolerant investors, long-term goals

## Example: Complete Portfolio Optimization

```python
from ultracore.domains.wealth.integration.etf_data_provider_manus import ETFDataProviderManus

# Initialize
data_provider = ETFDataProviderManus(data_dir="data/etf/historical")

# Define portfolio
portfolio_etfs = ['VAS', 'VGS', 'VTS', 'VAF', 'IOZ']

# Check availability
availability = data_provider.check_data_availability(portfolio_etfs)
available_etfs = [etf for etf, avail in availability.items() if avail]

print(f"Available: {len(available_etfs)}/{len(portfolio_etfs)} ETFs\n")

# Calculate individual risk metrics
print("Individual ETF Metrics:")
for etf in available_etfs:
    metrics = data_provider.calculate_risk_metrics(etf, lookback_years=3)
    print(f"{etf}: Return={metrics['mean_return']*100:.1f}%, "
          f"Vol={metrics['volatility']*100:.1f}%, "
          f"Sharpe={metrics['sharpe_ratio']:.2f}")

print()

# Optimize for three risk profiles
for risk_level, risk_budget in [("Conservative", 0.3), ("Balanced", 0.6), ("Growth", 0.9)]:
    result = data_provider.optimize_portfolio_mean_variance(
        tickers=available_etfs,
        risk_budget=risk_budget,
        lookback_years=3
    )
    
    print(f"{risk_level} Portfolio:")
    print(f"  Return: {result['expected_return']*100:.2f}% p.a.")
    print(f"  Volatility: {result['volatility']*100:.2f}%")
    print(f"  Sharpe: {result['sharpe_ratio']:.2f}")
    print(f"  Weights: {', '.join([f'{t}={w*100:.0f}%' for t, w in result['optimal_weights'].items()])}")
    print()
```

## Example: Portfolio Valuation

```python
# Get latest prices
latest_prices = data_provider.get_latest_prices(available_etfs)

# Calculate portfolio value
investment = 100000  # $100,000
result = data_provider.optimize_portfolio_mean_variance(
    tickers=available_etfs,
    risk_budget=0.6,
    lookback_years=3
)

print("Portfolio Allocation ($100,000):")
total_value = 0
for ticker, weight in result['optimal_weights'].items():
    allocation = investment * weight
    shares = allocation / latest_prices[ticker]
    value = shares * latest_prices[ticker]
    total_value += value
    print(f"  {ticker}: ${allocation:,.2f} ({shares:.2f} shares @ ${latest_prices[ticker]:.2f})")

print(f"Total: ${total_value:,.2f}")
```

## Available ETFs

The data provider includes 137 ASX ETFs across multiple categories:

### Australian Equities
- VAS, A200, IOZ, STW, VHY, FAIR, etc.

### International Equities
- VGS, VTS, NDQ, IVV, ASIA, etc.

### Fixed Income
- VAF, VGB, VBND, BILL, CRED, etc.

### Commodities
- GOLD, PMGOLD, QAU, etc.

### Sector-Specific
- ATEC, HACK, ROBO, DRUG, etc.

### Thematic
- ESGI, ETHI, FAIR, VESG, etc.

## API Reference

### ETFDataProviderManus

#### `__init__(data_dir: str = "data/etf/historical")`
Initialize the data provider with the directory containing Parquet files.

#### `load_etf_data(ticker: str) -> pd.DataFrame`
Load historical data for a single ETF.

**Returns**: DataFrame with columns: Date (index), Open, High, Low, Close, Adj Close, Volume

#### `get_returns(tickers: List[str], start_date: Optional[date] = None, end_date: Optional[date] = None, period: str = "daily") -> pd.DataFrame`
Get returns for multiple ETFs.

**Parameters**:
- `tickers`: List of ETF tickers
- `start_date`: Start date (default: 1 year ago)
- `end_date`: End date (default: today)
- `period`: 'daily', 'weekly', or 'monthly'

**Returns**: DataFrame with returns for each ticker

#### `calculate_expected_returns(tickers: List[str], method: str = "historical_mean", lookback_years: int = 3) -> Dict[str, float]`
Calculate expected annual returns for ETFs.

**Parameters**:
- `tickers`: List of ETF tickers
- `method`: 'historical_mean' or 'exponential'
- `lookback_years`: Years of historical data to use

**Returns**: Dictionary of ticker -> expected annual return

#### `calculate_covariance_matrix(tickers: List[str], lookback_years: int = 3) -> pd.DataFrame`
Calculate annualized covariance matrix for portfolio optimization.

#### `calculate_correlation_matrix(tickers: List[str], lookback_years: int = 3) -> pd.DataFrame`
Calculate correlation matrix for diversification analysis.

#### `calculate_risk_metrics(ticker: str, lookback_years: int = 3) -> Dict[str, float]`
Calculate comprehensive risk metrics for an ETF.

**Returns**: Dictionary with:
- `volatility`: Annualized volatility
- `sharpe_ratio`: Sharpe ratio (3% risk-free rate)
- `sortino_ratio`: Sortino ratio
- `max_drawdown`: Maximum drawdown
- `var_95`: Value at Risk (95% confidence)
- `cvar_95`: Conditional VaR (95% confidence)
- `mean_return`: Expected annual return

#### `optimize_portfolio_mean_variance(tickers: List[str], risk_budget: float = 0.6, lookback_years: int = 3, target_return: Optional[float] = None) -> Dict[str, any]`
Optimize portfolio using mean-variance optimization.

**Parameters**:
- `tickers`: List of ETF tickers
- `risk_budget`: Risk tolerance (0-1, higher = more risk)
- `lookback_years`: Years of historical data
- `target_return`: Target annual return (None = maximize Sharpe)

**Returns**: Dictionary with:
- `optimal_weights`: Dictionary of ticker -> weight
- `expected_return`: Expected annual return
- `volatility`: Portfolio volatility
- `sharpe_ratio`: Portfolio Sharpe ratio
- `tickers`: List of tickers

#### `check_data_availability(tickers: List[str]) -> Dict[str, bool]`
Check which ETFs have data available.

#### `get_latest_prices(tickers: List[str]) -> Dict[str, float]`
Get latest closing prices for ETFs.

## Integration with UltraCore

The ETF data provider integrates seamlessly with UltraCore's architecture:

### Data Mesh
ETF data is treated as a first-class data product with ownership and quality guarantees.

### Event Sourcing
All data collection and optimization activities can be tracked as events.

### Agentic AI
The data provider can be used by autonomous agents for portfolio management.

### ML/RL Ready
Data format is optimized for machine learning and reinforcement learning training.

## Performance Considerations

- **Caching**: Loaded data is cached in memory for fast access
- **Lazy Loading**: Data is only loaded when requested
- **Efficient Storage**: Parquet format provides fast I/O and compression
- **Parallel Processing**: Multiple ETFs can be processed in parallel

## Limitations

1. **Historical Data Only**: No real-time or intraday data
2. **Simple Optimization**: Uses random portfolio generation (not scipy.optimize)
3. **No Transaction Costs**: Optimization doesn't account for trading costs
4. **No Constraints**: No support for custom constraints (e.g., sector limits)

## Future Enhancements

- [ ] Real-time data integration
- [ ] Advanced optimization (Black-Litterman, risk parity)
- [ ] Transaction cost modeling
- [ ] Tax-aware optimization
- [ ] Custom constraints support
- [ ] Backtesting framework
- [ ] Monte Carlo simulation
- [ ] Scenario analysis

## Testing

Run the standalone test to verify the integration:

```bash
cd /path/to/UltraCore
python3 test_etf_standalone.py
```

This will:
- Load all available ETFs
- Calculate risk metrics
- Optimize portfolios with three risk profiles
- Display correlation matrix
- Show portfolio valuations

## Troubleshooting

### Issue: "Data directory not found"

**Solution**: Ensure the ETF data has been downloaded:
```bash
python3 download_all_etfs.py
```

### Issue: "No data for ticker"

**Solution**: Check if the ETF is in the available list:
```python
print(data_provider.available_etfs)
```

### Issue: High/unrealistic returns

**Solution**: This can happen with short lookback periods during bull markets. Use longer periods (5-10 years) for more realistic estimates.

## Support

For issues or questions:
1. Check that ETF data is downloaded (`data/etf/historical/`)
2. Verify Python dependencies (pandas, numpy, pyarrow)
3. Review test output for specific errors
4. Check log files for detailed error messages

---

**Last Updated**: November 2025  
**Version**: 1.0  
**Status**: Production Ready ✅
