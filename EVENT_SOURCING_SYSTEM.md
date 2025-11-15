# UltraCore ETF Event Sourcing System

## Overview

The UltraCore ETF system now supports **full event sourcing** with Kafka-based event tracking, while maintaining backward compatibility with direct Parquet file loading.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ETF Data Provider                         │
│  (Hybrid: Event Sourcing + Direct Parquet Loading)          │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼──────┐        ┌──────▼──────┐
        │ Event        │        │  Direct     │
        │ Sourcing     │        │  Parquet    │
        │ System       │        │  Loading    │
        │ (Kafka)      │        │  (Fallback) │
        └──────────────┘        └─────────────┘
                │                       │
                │                       │
        ┌───────▼──────┐        ┌──────▼──────┐
        │ Event Store  │        │  Parquet    │
        │ (Kafka)      │        │  Files      │
        └──────────────┘        └─────────────┘
```

## Features

### Event Sourcing Mode (Kafka Available)

✅ **Event Tracking** - All operations tracked as events  
✅ **Audit Trail** - Complete history of all data operations  
✅ **Event Replay** - Rebuild system state from events  
✅ **Distributed Coordination** - Multi-instance coordination  
✅ **Time Travel** - Query historical states  
✅ **CQRS Support** - Separate read/write models  

### Direct Mode (No Kafka)

✅ **Simple Deployment** - No external dependencies  
✅ **Fast Startup** - Direct file access  
✅ **All Features** - Full optimization capabilities  
✅ **Easy Testing** - No infrastructure setup  

## Installation

### Full System (with Event Sourcing)

```bash
# Install all dependencies including Kafka client
pip install -r requirements_etf_system.txt

# Install and configure Kafka (if using event sourcing)
# See Kafka documentation for setup
```

### Minimal System (Parquet only)

```bash
# Install only core dependencies
pip install pandas numpy pyarrow scipy yfinance
```

## Usage

### Initialize the System

```python
from ultracore.domains.wealth.integration.etf_data_provider import ETFDataProvider

# Initialize (auto-detects event sourcing availability)
data_provider = ETFDataProvider(data_dir="data/etf")

# Check mode
if data_provider.use_event_sourcing:
    print("Event Sourcing: ENABLED")
else:
    print("Direct Parquet Mode: ENABLED")
```

### Portfolio Optimization

```python
# Works the same in both modes!
result = data_provider.optimize_portfolio_mean_variance(
    tickers=['VAS', 'VGS', 'VTS', 'VAF'],
    risk_budget=0.20,  # 20% volatility target
    lookback_years=5
)

print(f"Expected Return: {result['expected_return']*100:.2f}%")
print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")

for ticker, weight in result['optimal_weights'].items():
    print(f"{ticker}: {weight*100:.1f}%")
```

### Risk Metrics

```python
# Calculate comprehensive risk metrics
metrics = data_provider.calculate_risk_metrics('VAS', lookback_years=3)

print(f"Expected Return: {metrics['mean_return']*100:.2f}% p.a.")
print(f"Volatility: {metrics['volatility']*100:.2f}%")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
```

### Correlation Analysis

```python
# Analyze correlations for diversification
tickers = ['VAS', 'VGS', 'VTS', 'VAF']
corr_matrix = data_provider.calculate_correlation_matrix(tickers, lookback_years=3)

print(corr_matrix.round(2))
```

## Event Sourcing Details

### Event Types

When event sourcing is enabled, the system tracks:

1. **ETFDataCollected** - New ETF data downloaded
2. **ETFDataUpdated** - Existing ETF data updated
3. **PortfolioOptimized** - Portfolio optimization performed
4. **RiskMetricsCalculated** - Risk metrics computed
5. **PriceDataQueried** - Price data accessed

### Event Store

Events are stored in Kafka topics:
- `etf-data-events` - Data collection events
- `portfolio-events` - Portfolio optimization events
- `query-events` - Data query events

### Event Replay

Rebuild system state from events:

```python
from ultracore.market_data.etf.etf_data_system import get_etf_system

system = get_etf_system()

# Replay events to rebuild state
await system.replay_events(from_timestamp=datetime(2025, 1, 1))
```

## Configuration

### Event Sourcing Configuration

Set environment variables:

```bash
# Kafka Configuration
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export KAFKA_TOPIC_PREFIX=ultracore

# Event Store Configuration
export EVENT_STORE_TYPE=kafka
export EVENT_STORE_RETENTION_DAYS=90
```

### Direct Mode Configuration

No configuration needed! Just ensure Parquet files exist in:
```
data/etf/historical/*.parquet
```

## Testing

### Test Full System

```bash
python initialize_etf_system_with_event_sourcing.py
```

This will:
- ✅ Initialize event sourcing (if available)
- ✅ Test data loading
- ✅ Calculate risk metrics
- ✅ Optimize portfolios
- ✅ Analyze correlations
- ✅ Get latest prices

### Test Specific Features

```python
from ultracore.domains.wealth.integration.etf_data_provider import ETFDataProvider

data_provider = ETFDataProvider(data_dir="data/etf")

# Test data availability
availability = data_provider.check_data_availability(['VAS', 'VGS', 'VTS'])
print(availability)

# Test latest prices
prices = data_provider.get_latest_prices(['VAS', 'VGS', 'VTS'])
print(prices)
```

## Performance

### Event Sourcing Mode

- **Initialization**: ~2-3 seconds (Kafka connection)
- **Data Loading**: ~50ms per ETF (cached after first load)
- **Optimization**: ~1-2 seconds for 5-10 ETFs
- **Event Tracking**: ~5ms overhead per operation

### Direct Mode

- **Initialization**: <100ms (no external connections)
- **Data Loading**: ~20ms per ETF (Parquet read + cache)
- **Optimization**: ~1-2 seconds for 5-10 ETFs
- **No overhead**: Direct file access

## Advantages of Event Sourcing

### Audit & Compliance
- Complete audit trail of all operations
- Regulatory compliance support
- Forensic analysis capabilities

### Debugging & Testing
- Reproduce bugs by replaying events
- Test with historical states
- Time-travel debugging

### Scalability
- Distributed processing support
- Event-driven architecture
- Microservices ready

### Data Quality
- Track data lineage
- Validate data transformations
- Monitor data quality metrics

## When to Use Each Mode

### Use Event Sourcing When:
- ✅ You need audit trails
- ✅ You have multiple services
- ✅ You want event-driven architecture
- ✅ You need time-travel queries
- ✅ You have Kafka infrastructure

### Use Direct Mode When:
- ✅ You want simple deployment
- ✅ You're prototyping
- ✅ You don't need audit trails
- ✅ You want minimal dependencies
- ✅ You're running locally

## Migration

### From Direct Mode to Event Sourcing

1. Install Kafka and confluent-kafka
2. Configure Kafka connection
3. Restart the system
4. System auto-detects and enables event sourcing

### From Event Sourcing to Direct Mode

1. System automatically falls back if Kafka unavailable
2. No code changes needed
3. All features continue to work

## Troubleshooting

### Event Sourcing Not Enabling

**Symptom**: System uses direct mode even with Kafka installed

**Solutions**:
1. Check Kafka is running: `kafka-topics.sh --list --bootstrap-server localhost:9092`
2. Check environment variables: `echo $KAFKA_BOOTSTRAP_SERVERS`
3. Check logs for connection errors
4. Verify confluent-kafka installed: `pip show confluent-kafka`

### Optimization Not Converging

**Symptom**: `optimization_success: False`

**Solutions**:
1. Increase lookback period (more data)
2. Relax risk budget constraint
3. Remove highly correlated assets
4. Check for missing data

### High Memory Usage

**Symptom**: System uses lots of memory

**Solutions**:
1. Clear cache: `data_provider._cache.clear()`
2. Load fewer ETFs at once
3. Use shorter lookback periods
4. Disable event sourcing if not needed

## API Reference

### ETFDataProvider

#### `__init__(data_dir: str = "/data/etf")`
Initialize the data provider with automatic event sourcing detection.

#### `use_event_sourcing: bool`
Property indicating if event sourcing is enabled.

#### `available_etfs: List[str]`
List of all available ETF tickers.

#### `load_etf_data(ticker: str) -> pd.DataFrame`
Load ETF data (tries Parquet first, then event sourcing).

#### `optimize_portfolio_mean_variance(...) -> Dict`
Optimize portfolio using scipy.optimize (works in both modes).

#### `calculate_risk_metrics(ticker: str, ...) -> Dict`
Calculate comprehensive risk metrics (works in both modes).

## Dependencies

### Required (Both Modes)
- pandas >= 2.0.0
- numpy >= 1.24.0
- pyarrow >= 12.0.0
- scipy >= 1.10.0
- yfinance >= 0.2.28

### Optional (Event Sourcing Only)
- confluent-kafka >= 2.0.0

## Support

For issues:
1. Check system mode: `data_provider.use_event_sourcing`
2. Check logs for errors
3. Test with direct mode first
4. Verify Kafka if using event sourcing

---

**Last Updated**: November 2025  
**Version**: 2.0  
**Status**: Production Ready ✅
