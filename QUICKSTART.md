# 🚀 UltraWealth Platform - Quick Start Guide

## 📋 What You Have

A complete AI-powered wealth management platform with:

### Core Components
1. **DataMesh** - Data governance with auto-update (daily at 6 PM AEST)
2. **ML Engine** - Random Forest + Gradient Boosting predictions
3. **RL Optimizer** - Portfolio optimization using Reinforcement Learning
4. **Agentic AI** - Autonomous decision-making system
5. **MCP Tools** - AI agent access layer
6. **Auto-Update** - Keeps 90+ Australian ETFs fresh

### Features
- ✅ 90+ Australian ETFs (ASX listed only)
- ✅ Real-time pricing from Yahoo Finance (FREE)
- ✅ ML price predictions (ensemble models)
- ✅ RL portfolio optimization
- ✅ Autonomous AI recommendations
- ✅ Data lineage tracking
- ✅ Automatic daily updates
- ✅ MCP-compatible for AI agents

## 🏃 Quick Start

### 1. Start Server
```powershell
cd C:\Users\mjmil\UltraCore
python server.py
```

### 2. Run Tests
```powershell
# In new window:
cd C:\Users\mjmil\UltraCore
.\test_complete.ps1
```

### 3. Access API
- **Server**: http://localhost:8888
- **Docs**: http://localhost:8888/docs
- **Health**: http://localhost:8888/health

## 📊 Example Usage

### Get ML Prediction
```powershell
Invoke-RestMethod -Uri "http://localhost:8888/api/v1/ml/predict/VAS.AX"
```

### Optimize Portfolio
```powershell
$body = @{
    tickers = @("VAS.AX", "VGS.AX", "VAF.AX")
    initial_balance = 100000
    risk_tolerance = "moderate"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8888/api/v1/portfolio/optimize" `
    -Method POST -Body $body -ContentType "application/json"
```

### Get AI Recommendations
```powershell
$body = @{
    tickers = @("VAS.AX", "VGS.AX", "NDQ.AX")
    current_allocation = @{
        "VAS.AX" = @{weight = 0.4}
        "VGS.AX" = @{weight = 0.4}
        "NDQ.AX" = @{weight = 0.2}
    }
    portfolio_value = 100000
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8888/api/v1/ai/recommend" `
    -Method POST -Body $body -ContentType "application/json"
```

## 🎯 Next Steps

1. **Integrate with your RL Engine**: Use MCP tools endpoints
2. **Connect to your agents**: Use `/api/v1/mcp/*` endpoints
3. **Deploy to production**: Set up on cloud server
4. **Add monitoring**: Set up logging and alerts
5. **Expand universe**: Add more ETFs if needed

## 📚 API Endpoints

### Universe
- `GET /api/v1/universe` - Get all ETFs
- `GET /api/v1/universe/provider/{provider}` - Filter by provider
- `GET /api/v1/universe/category/{category}` - Filter by category

### DataMesh
- `POST /api/v1/datamesh/ingest` - Ingest data
- `GET /api/v1/datamesh/status` - Get cache status
- `GET /api/v1/datamesh/lineage/{ticker}` - Get data lineage

### Machine Learning
- `POST /api/v1/ml/train/{ticker}` - Train model
- `GET /api/v1/ml/predict/{ticker}` - Get prediction
- `POST /api/v1/ml/batch-predict` - Batch predictions

### Portfolio Optimization
- `POST /api/v1/portfolio/optimize` - Optimize allocation

### Agentic AI
- `POST /api/v1/ai/analyze` - Market analysis
- `POST /api/v1/ai/recommend` - Get recommendations
- `GET /api/v1/ai/history` - Decision history

### MCP Tools
- `GET /api/v1/mcp/tools` - List tools
- `GET /api/v1/mcp/price/{ticker}` - Get price
- `GET /api/v1/mcp/predict/{ticker}` - Predict
- `POST /api/v1/mcp/optimize` - Optimize

## 🔧 Configuration

### Auto-Update Schedule
Edit `ultracore/services/ultrawealth/auto_update.py`:
```python
# Change update time (default: 6 PM AEST)
schedule.every().day.at("18:00").do(...)
```

### Risk Tolerance Levels
- **Conservative**: Low risk, bonds heavy
- **Moderate**: Balanced approach
- **Aggressive**: High growth focus

## 📞 Support

Check `/docs` endpoint for interactive API documentation!
