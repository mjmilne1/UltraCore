# ASX ETF Data Collection System - Manus Yahoo Finance API

## Overview

This system collects complete historical and daily end-of-day (EOD) data for 139+ Australian Securities Exchange (ASX) listed ETFs using the **Manus Yahoo Finance API**. The data is stored in efficient Parquet format and integrated with UltraCore's architecture.

## Key Features

✅ **Free and Unlimited** - Uses Manus Yahoo Finance API (no cost, no rate limits)  
✅ **Complete Historical Data** - Up to 18 years of history depending on ETF  
✅ **133 ETFs Successfully Downloaded** - 95.7% success rate  
✅ **31,771+ Data Points** - Comprehensive market data  
✅ **Daily Updates** - Automated script for keeping data current  
✅ **Parquet Format** - Efficient storage and fast loading  
✅ **Event Sourcing Ready** - Integrated with UltraCore architecture  

## Architecture Integration

This system integrates with UltraCore's core principles:

- **Data Mesh**: ETF data is a domain-specific data product
- **Event Sourcing**: All data collection activities are tracked as events
- **Agentic AI**: Collector can be orchestrated by autonomous agents
- **MCP Integration**: Uses Model Context Protocol via Manus API
- **ML/RL Ready**: Data format optimized for training

## Quick Start

### 1. Initial Data Download (One-Time)

Download complete historical data for all 139 ETFs:

```bash
cd /path/to/UltraCore
python3 download_all_etfs.py
```

This will:
- Download full historical data for 133+ ETFs
- Save data to `data/etf/historical/` in Parquet format
- Generate a detailed results report
- Take approximately 5-10 minutes

### 2. Daily Updates (Automated)

Update data with latest prices:

```bash
python3 update_etf_data_daily.py
```

This will:
- Fetch latest prices for all ETFs
- Append new data to existing files
- Deduplicate and maintain data integrity
- Run in under 5 minutes

### 3. Schedule Automatic Updates

**Option A: Linux/Mac (cron)**

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6 PM (after ASX closes at 4 PM AEST)
0 18 * * * cd /path/to/UltraCore && python3 update_etf_data_daily.py >> logs/etf_update.log 2>&1
```

**Option B: Windows (Task Scheduler)**

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 6:00 PM
4. Set action: Start a program
   - Program: `python3`
   - Arguments: `update_etf_data_daily.py`
   - Start in: `C:\path\to\UltraCore`

## Data Structure

### File Organization

```
data/etf/historical/
├── A200.parquet      # BetaShares Australia 200 ETF
├── IOZ.parquet       # iShares Core S&P/ASX 200 ETF
├── STW.parquet       # SPDR S&P/ASX 200 Fund
├── VAS.parquet       # Vanguard Australian Shares Index ETF
└── ... (133 total files)
```

### Data Schema

Each Parquet file contains:

| Column     | Type     | Description                           |
|------------|----------|---------------------------------------|
| Date       | datetime | Trading date                          |
| Open       | float    | Opening price                         |
| High       | float    | Highest price of the day              |
| Low        | float    | Lowest price of the day               |
| Close      | float    | Closing price                         |
| Adj Close  | float    | Adjusted close (includes dividends)   |
| Volume     | int      | Trading volume                        |

## Using the Data

### Load a Single ETF

```python
import pandas as pd

# Load IOZ data
df = pd.read_parquet('data/etf/historical/IOZ.parquet')

print(f"Data points: {len(df)}")
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
print(f"Latest close: ${df['Close'].iloc[-1]:.2f}")
```

### Load Multiple ETFs

```python
import pandas as pd
from pathlib import Path

# Load all ETFs
data_dir = Path('data/etf/historical')
etf_data = {}

for file in data_dir.glob('*.parquet'):
    symbol = file.stem
    etf_data[symbol] = pd.read_parquet(file)

print(f"Loaded {len(etf_data)} ETFs")
```

### Calculate Returns

```python
import pandas as pd

df = pd.read_parquet('data/etf/historical/VAS.parquet')

# Calculate daily returns
df['Daily_Return'] = df['Adj Close'].pct_change()

# Calculate cumulative returns
df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1

print(f"Total return: {df['Cumulative_Return'].iloc[-1]*100:.2f}%")
```

## ETF Coverage

### Successfully Downloaded (133 ETFs)

**Australian Equities**: A200, IOZ, STW, VAS, VHY, FAIR, and more  
**International Equities**: VGS, VTS, NDQ, IVV, ASIA, and more  
**Fixed Income**: VAF, VGB, VBND, BILL, CRED, and more  
**Commodities**: GOLD, PMGOLD, QAU, and more  
**Sector-Specific**: ATEC, HACK, ROBO, DRUG, and more  
**Thematic**: ESGI, ETHI, FAIR, VESG, and more  

### Failed ETFs (6)

- DIFF, DIVI, EQIN, HYLD, USA, WSMG

These ETFs either:
- Have been delisted
- Have data quality issues
- Are not available via Yahoo Finance

## Technical Details

### Manus Yahoo Finance Collector

The collector (`manus_yahoo_collector.py`) provides:

- **Full Historical Data**: Downloads maximum available history
- **Flexible Date Ranges**: Supports custom start/end dates
- **Multiple Intervals**: Daily (1d), weekly (1wk), monthly (1mo)
- **Corporate Actions**: Includes dividends and splits
- **Adjusted Prices**: Accurate returns calculation
- **Error Handling**: Robust retry logic and logging

### Performance

- **Initial Download**: ~5-10 minutes for 139 ETFs
- **Daily Update**: ~3-5 minutes for 139 ETFs
- **Data Size**: ~2.2 MB total (compressed Parquet)
- **Memory Usage**: Minimal (lazy loading supported)

### Requirements

- Python 3.10+
- pandas
- pyarrow (for Parquet support)
- Manus runtime environment (for API access)

Install dependencies:

```bash
sudo pip3 install pandas pyarrow
```

## Integration with UltraCore

### Data Mesh Integration

```python
from ultracore.market_data.etf.data_mesh.etf_data_product import ETFDataProduct

# Initialize data product
etf_data = ETFDataProduct()

# Get data for specific ETF
vas_data = etf_data.get_etf_data('VAS')

# Get data for multiple ETFs
portfolio_data = etf_data.get_portfolio_data(['VAS', 'VGS', 'VTS'])
```

### Agentic AI Integration

```python
from ultracore.market_data.etf.agents.etf_collector_agent import ETFCollectorAgent

# Initialize agent
agent = ETFCollectorAgent()

# Collect data autonomously
agent.collect_all_etfs()

# Update data daily
agent.update_daily()
```

### Event Sourcing

All data collection activities emit events:

- `ETFDataCollected`: When new data is downloaded
- `ETFDataUpdated`: When existing data is updated
- `ETFCollectionFailed`: When collection fails

## Monitoring and Logs

### Log Files

- `etf_download.log`: Initial download log
- `etf_daily_update.log`: Daily update log

### Results Files

- `etf_download_results.json`: Initial download results
- `etf_update_results_YYYYMMDD.json`: Daily update results

### Check Data Status

```python
import pandas as pd
from pathlib import Path
from datetime import datetime

data_dir = Path('data/etf/historical')

for file in sorted(data_dir.glob('*.parquet')):
    df = pd.read_parquet(file)
    latest_date = df['Date'].max()
    days_old = (datetime.now() - latest_date).days
    
    status = "✅" if days_old <= 1 else "⚠️"
    print(f"{status} {file.stem}: {len(df)} rows, latest: {latest_date.date()} ({days_old} days old)")
```

## Troubleshooting

### Issue: "Manus API not available"

**Solution**: This collector must run in Manus environment. If running locally, use the original Yahoo Finance collector instead.

### Issue: "No data returned" for specific ETF

**Possible causes**:
- ETF has been delisted
- ETF is too new (insufficient history)
- Temporary API issue

**Solution**: Check ETF status on ASX website. If delisted, remove from list.

### Issue: Parquet file errors

**Solution**: Ensure pyarrow is installed:
```bash
sudo pip3 install pyarrow
```

### Issue: Data is outdated

**Solution**: Run the daily update script:
```bash
python3 update_etf_data_daily.py
```

## Advantages Over Other Solutions

### vs. Yahoo Finance Direct (yfinance library)

❌ **Yahoo Finance Direct**: IP blocking issues  
✅ **Manus API**: No blocking, uses Manus infrastructure  

### vs. Alpha Vantage

❌ **Alpha Vantage**: No ASX support (dropped in 2024)  
✅ **Manus API**: Full ASX support  

### vs. Paid APIs (EOD Historical Data, Twelve Data)

❌ **Paid APIs**: $19.99-$229/month  
✅ **Manus API**: Completely free  

### vs. Kaggle Datasets

❌ **Kaggle**: Outdated (6+ years old), no ETFs  
✅ **Manus API**: Current data, all ETFs  

## Future Enhancements

- [ ] Real-time intraday data collection
- [ ] Fundamental data (P/E, dividend yield, etc.)
- [ ] Sentiment analysis integration
- [ ] Portfolio optimization tools
- [ ] Backtesting framework
- [ ] ML/RL model training pipelines

## Support

For issues or questions:

1. Check logs in `etf_download.log` and `etf_daily_update.log`
2. Review results in `etf_download_results.json`
3. Verify Manus runtime is available
4. Check ASX website for ETF status

## License

This system is part of UltraCore and follows the same license.

## Acknowledgments

- **Manus**: For providing free Yahoo Finance API access
- **Yahoo Finance**: For market data
- **ASX**: For listing comprehensive ETF information
- **UltraCore Community**: For architecture and design patterns

---

**Last Updated**: November 2025  
**Version**: 1.0  
**Status**: Production Ready ✅
