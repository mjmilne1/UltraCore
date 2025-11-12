# Fiscal.ai Integration for UltraWealth

## Overview

Fiscal.ai provides institutional-grade financial data for portfolio management and wealth advisory services within UltraCore platform.

## Features

- **Portfolio Analytics**: Comprehensive portfolio metrics, health scoring, and performance tracking
- **Diversification Analysis**: Sector allocation and concentration risk assessment  
- **Financial Data**: Real-time stock prices, fundamentals, ratios, and SEC filings
- **Company Intelligence**: Deep company profiles, segment data, and financial statements

## Architecture
```
UltraWealth Portfolio
    ↓
FiscalAIService (Business Logic)
    ↓
FiscalAIClient (API Communication)
    ↓
Fiscal.ai API
```

## API Endpoints

### Company Data
- **GET** `/api/v1/fiscal-ai/company/{ticker}/profile` - Company profile
- **GET** `/api/v1/fiscal-ai/company/{ticker}/financials` - Financial statements
- **GET** `/api/v1/fiscal-ai/company/{ticker}/price` - Stock prices
- **GET** `/api/v1/fiscal-ai/search` - Search companies

### Portfolio Management
- **POST** `/api/v1/fiscal-ai/portfolio/analyze` - Full portfolio analysis
- **POST** `/api/v1/fiscal-ai/portfolio/holdings/enrich` - Enrich holdings with data

## Usage Examples

### Analyze Portfolio
```python
from ultracore.services.fiscal_ai import FiscalAIService, PortfolioAnalyzer

service = FiscalAIService()
analyzer = PortfolioAnalyzer(service)

holdings = [
    {"ticker": "AAPL", "quantity": 100, "cost_basis": 150.00},
    {"ticker": "MSFT", "quantity": 50, "cost_basis": 280.00},
    {"ticker": "GOOGL", "quantity": 25, "cost_basis": 120.00}
]

# Get portfolio metrics
metrics = await service.calculate_portfolio_metrics(holdings)

# Health analysis
health = await analyzer.analyze_portfolio_health(holdings)
print(f"Portfolio Health Score: {health['health_score']}/100")

# Diversification
diversification = await analyzer.get_diversification_analysis(holdings)
print(f"Diversification Score: {diversification['diversification_score']}/100")
```

### Get Company Data
```python
from ultracore.services.fiscal_ai import FiscalAIService

service = FiscalAIService()

# Get company profile
async with service.client as client:
    profile = await client.get_company_profile("AAPL")
    
    # Get financial ratios
    ratios = await client.get_company_ratios("AAPL", "annual", 5)
    
    # Get stock prices
    prices = await client.get_stock_prices("AAPL", "2024-01-01", "2024-12-31")
```

### Via REST API
```bash
# Analyze portfolio
curl -X POST http://localhost:8000/api/v1/fiscal-ai/portfolio/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "holdings": [
      {"ticker": "AAPL", "quantity": 100, "cost_basis": 150},
      {"ticker": "MSFT", "quantity": 50, "cost_basis": 280}
    ]
  }'

# Get company financials
curl http://localhost:8000/api/v1/fiscal-ai/company/AAPL/financials?period=annual

# Search companies
curl "http://localhost:8000/api/v1/fiscal-ai/search?query=Apple&limit=10"
```

## Integration with UltraWealth Domains

### Account Domain
Enrich customer portfolios with real-time market data and analytics.

### Wealth Advisory
Provide AI-powered portfolio recommendations based on fundamental analysis.

### Risk Management
Monitor portfolio health scores and concentration risks.

### Reporting
Generate comprehensive wealth reports with institutional-grade financial data.

## Configuration

Set in `.env`:
```
FISCAL_AI_API_KEY=e831080d-1b88-4473-82e8-33ee11f59f2a
```

## Testing
```bash
# Run integration tests
pytest tests/integration/test_fiscal_ai.py

# Test API endpoints
pytest tests/api/test_fiscal_ai_routes.py
```

## Support

- Fiscal.ai Docs: https://docs.fiscal.ai
- UltraCore Support: dev@turingdynamics.com.au
