# Australian ETF Historical Data

## Overview

This directory contains comprehensive historical data for **72 Australian ETFs** downloaded from Yahoo Finance, prepared for machine learning applications in UltraWealth.

## Dataset Statistics

- **Total Records**: 213,820 rows (raw data)
- **ML-Ready Records**: 177,914 rows (after feature engineering and cleaning)
- **Unique ETFs**: 72
- **Date Range**: January 2, 2008 to November 12, 2025
- **Total Size**: ~258 MB (all files)

## Files

### Raw Historical Data

Individual CSV files for each ETF (e.g., `VAS_history.csv`, `A200_history.csv`):
- Date, Open, High, Low, Close, Volume
- Dividends, Stock Splits, Capital Gains
- Ticker, Name, Category, Currency

### Consolidated Datasets

1. **`all_australian_etfs_combined.csv`** (35.47 MB)
   - All ETF data combined into a single file
   - Raw OHLCV data with metadata

2. **`ml_dataset_full.csv`** (79.94 MB)
   - Complete dataset with 24 ML features
   - Includes technical indicators, returns, volatility
   - Ready for training ML models

3. **`ml_dataset_train.csv`** (80% of data)
   - Training set: 142,305 rows
   - Data before August 3, 2023

4. **`ml_dataset_test.csv`** (20% of data)
   - Test set: 35,609 rows
   - Data from August 3, 2023 onwards

5. **`ml_dataset_compact.csv`** (26.87 MB)
   - Compact version with 10 key features
   - Faster loading for quick experiments

6. **`dataset_summary.txt`**
   - Summary statistics and metadata

7. **`ml_dataset_info.txt`**
   - Detailed ML dataset information
   - Feature descriptions and statistics

## ML Features (24 total)

### Price Data
1. Open
2. High
3. Low
4. Close
5. Volume

### Corporate Actions
6. Dividends
7. Stock Splits
8. Capital Gains

### Returns
9. Daily_Return
10. Weekly_Return
11. Monthly_Return

### Volatility
12. Volatility_7d (7-day rolling standard deviation)
13. Volatility_30d (30-day rolling standard deviation)

### Moving Averages
14. SMA_7 (7-day simple moving average)
15. SMA_30 (30-day simple moving average)
16. SMA_90 (90-day simple moving average)

### Momentum
17. Momentum_7d (7-day price momentum)
18. Momentum_30d (30-day price momentum)

### Volume Indicators
19. Volume_MA_7 (7-day volume moving average)
20. Volume_Ratio (current volume / 7-day average)

### Technical Indicators
21. Daily_Range (high-low range as % of open)
22. RSI_14 (14-day Relative Strength Index)

### Target Variables
23. Target_Next_Day_Return (next day's return - for regression)
24. Target_Direction (1 if next day up, 0 if down - for classification)

## ETF Categories

### Broad Market (5)
- VAS, A200, IOZ, STW, OZR

### International Equities (7)
- VGS, VGAD, IVV, IWLD, VEU, VTS, ESTW

### Emerging Markets (3)
- VGE, IEM, EMKT

### Asia Pacific (3)
- VAP, ASIA, IAA

### Europe (2)
- VEQ, IEU

### US Equities (4)
- VTS, IVV, NDQ, FANG

### Small Cap (3)
- VSO, IJR, SMLL

### Growth (2)
- GGUS

### Dividend/Income (6)
- VHY, IHD, EINC, ZYAU, YMAX

### Property/REITs (5)
- VAP, DJRE, MVA, SLF, REIT

### Fixed Income/Bonds (6)
- VAF, VGB, GOVT, IAF, BILL, PLUS

### Inflation-Linked (1)
- ILB

### Commodities (4)
- QAU, GOLD, PMGOLD, ETPMAG

### Sector-Specific (5)
- VGE (Energy), VHT (Healthcare), VIT (Technology), VFG (Financials), VCF (Consumer)

### ESG/Sustainable (4)
- VETH, FAIR, ETHI, ESGI

### Active/Smart Beta (5)
- AQLT, QUAL, MVOL, DHHF, VDHG

### Currency Hedged (2)
- VGAD, HETH

### Additional Popular ETFs (12)
- HACK, DRUG, ATEC, BNKS, MVB, MVE, MVS, MVW, IOO, IXI, IKO, IJH, IJP

## Usage Examples

### Load Full ML Dataset

```python
import pandas as pd

# Load full ML dataset
df = pd.read_csv('data/etf_historical/ml_dataset_full.csv')
df['Date'] = pd.to_datetime(df['Date'])

# Filter by ticker
vas_data = df[df['Ticker'] == 'VAS.AX']

# Get features and target
features = df[['Daily_Return', 'Volatility_30d', 'SMA_30', 'RSI_14']]
target = df['Target_Direction']
```

### Load Train/Test Split

```python
# Load pre-split data
train = pd.read_csv('data/etf_historical/ml_dataset_train.csv')
test = pd.read_csv('data/etf_historical/ml_dataset_test.csv')

# Prepare for ML
feature_cols = ['Daily_Return', 'Volatility_30d', 'SMA_30', 'RSI_14', 
                'Momentum_30d', 'Volume_Ratio']

X_train = train[feature_cols]
y_train = train['Target_Direction']

X_test = test[feature_cols]
y_test = test['Target_Direction']
```

### Load Compact Dataset

```python
# Quick loading for experiments
df_compact = pd.read_csv('data/etf_historical/ml_dataset_compact.csv')

# Columns: Date, Ticker, Close, Volume, Daily_Return, Volatility_30d, 
#          SMA_30, RSI_14, Target_Next_Day_Return, Target_Direction
```

## ML Use Cases

### 1. Price Prediction (Regression)
- **Target**: `Target_Next_Day_Return`
- **Features**: All technical indicators
- **Models**: Linear Regression, Random Forest, XGBoost, LSTM

### 2. Direction Prediction (Classification)
- **Target**: `Target_Direction`
- **Features**: Returns, volatility, momentum, RSI
- **Models**: Logistic Regression, Random Forest, Neural Networks

### 3. Portfolio Optimization
- **Use**: Calculate correlation matrix across ETFs
- **Features**: Returns, volatility
- **Methods**: Mean-variance optimization, risk parity

### 4. Risk Assessment
- **Use**: Predict volatility and drawdowns
- **Features**: Historical volatility, volume, price ranges
- **Models**: GARCH, Random Forest

### 5. Anomaly Detection
- **Use**: Detect unusual market behavior
- **Features**: Volume ratio, daily range, returns
- **Models**: Isolation Forest, Autoencoders

## Data Quality Notes

- **Missing Data**: Rows with NaN values (from rolling calculations) have been removed
- **Delisted ETFs**: 6 ETFs failed to download (possibly delisted or renamed)
- **Time Zones**: Mixed time zones in original data (converted to UTC recommended)
- **Lookback Period**: First 90 days of each ETF may have incomplete features due to rolling windows

## Update Instructions

To refresh the dataset with latest data:

```bash
cd /home/ubuntu
python3 download_australian_etf_data.py
python3 prepare_ml_dataset.py
```

## Integration with UltraWealth

This dataset is automatically available to UltraWealth's ML modules:

- **Credit Scoring**: Use volatility and returns for risk assessment
- **Portfolio Optimization**: Use correlation and returns for asset allocation
- **AI Advisory**: Use all features for recommendation engine
- **Fraud Detection**: Use volume and price anomalies

## License

Data sourced from Yahoo Finance under their terms of service. For educational and research purposes only.

## Last Updated

November 13, 2025

## Contact

For questions or issues with this dataset, contact: support@turingdynamics.ai
