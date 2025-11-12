# OpenMarkets Integration - Quick Start Guide

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- kubectl (for Kubernetes deployment)
- OpenMarkets API credentials

## Installation

### Option 1: Local Development (Fastest)
```powershell
cd integrations/openmarkets
.\setup.ps1 -Environment local
```

This will:
- Create Python virtual environment
- Install dependencies
- Create `.env` configuration file

Then update `.env` with your credentials:
```env
OPENMARKETS_API_KEY=your-actual-api-key
OPENMARKETS_API_SECRET=your-actual-api-secret
```

### Option 2: Docker (Recommended for Testing)
```powershell
cd integrations/openmarkets
.\setup.ps1 -Environment docker
```

This will start:
- OpenMarkets Integration Service (port 8100)
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- Kafka event streaming (port 9092)

### Option 3: Kubernetes (Production)
```powershell
cd integrations/openmarkets
.\setup.ps1 -Environment kubernetes
```

This will:
- Create `ultracore` namespace
- Deploy all services with auto-scaling
- Set up monitoring and health checks

## Quick Examples

### 1. Natural Language Trading with Anya
```python
from ultracore.integrations.openmarkets import OpenMarketsClient
from ultracore.integrations.openmarkets.agents import AnyaTradingAgent
from anthropic import Anthropic

# Initialize
client = OpenMarketsClient()
anthropic = Anthropic(api_key="your-anthropic-key")
agent = AnyaTradingAgent(client, anthropic, account_id="your-account")

# Trade with natural language
result = await agent.execute("Buy 1000 BHP shares at market price")
print(f"Order placed: {result['order_id']}")

# Check position
result = await agent.execute("What's my current position in BHP?")
print(result)
```

### 2. ML Price Prediction
```python
from ultracore.integrations.openmarkets.ml import PricePredictionModel

model = PricePredictionModel("BHP", model_registry)

# Train on historical data
await model.train(historical_events, epochs=100)

# Predict future price
prediction = await model.predict(recent_data)
print(f"Predicted price: ${prediction['predicted_price']:.2f}")
```

### 3. RL Adaptive Trading
```python
from ultracore.integrations.openmarkets.rl import TradingEnvironment, PPOTradingStrategy

# Create environment
env = TradingEnvironment(client, account_id, symbols=["BHP", "CBA", "WES"])

# Train RL agent
strategy = PPOTradingStrategy(env)
await strategy.train(total_timesteps=100000)

# Use trained strategy
observation = env.reset()
action = await strategy.predict(observation)
```

### 4. Market Regime Detection
```python
from ultracore.integrations.openmarkets.ml import MarketRegimeDetector

detector = MarketRegimeDetector(n_regimes=5)

# Train on historical data
await detector.train(market_data_events)

# Detect current regime
regime = await detector.detect_current_regime(recent_data)
print(f"Current market regime: {regime['current_regime']}")
print(f"Trading recommendation: {regime['trading_recommendation']}")
```

### 5. Anomaly Detection
```python
from ultracore.integrations.openmarkets.ml import TradingAnomalyDetector

detector = TradingAnomalyDetector()

# Train on normal trades
await detector.train(normal_trades)

# Check if trade is anomalous
result = await detector.detect_anomaly(trade_event)
if result['is_anomaly']:
    print(f"ALERT: Anomalous trade detected!")
    print(f"Risk score: {result['anomaly_score']}")
    print(f"Reasons: {result['anomaly_reasons']}")
```

### 6. MCP Server (AI Tool Integration)
```python
from ultracore.integrations.openmarkets.mcp import OpenMarketsMCPServer

# Start MCP server
server = OpenMarketsMCPServer(client, account_id)
await server.start(port=8100)

# Now Claude (or other AI) can use trading tools:
# - place_trade(symbol="BHP", action="buy", quantity=1000)
# - get_position(symbol="BHP")
# - get_portfolio()
# - analyze_market(symbol="BHP")
# - optimize_portfolio()
```

### 7. Data Mesh Products
```python
from ultracore.integrations.openmarkets.datamesh import TradesDataProduct

trades_product = TradesDataProduct(event_store)

# Get trades as DataFrame
trades_df = await trades_product.get_trades(
    account_id="your-account",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31)
)

# Get analytics
analytics = await trades_product.get_trade_analytics(account_id)
print(f"Total trades: {analytics['total_trades']}")
print(f"Total volume: ${analytics['total_volume']:,.2f}")
```

## Testing
```powershell
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/integrations/openmarkets/

# Run with coverage
pytest tests/ --cov=ultracore.integrations.openmarkets --cov-report=html

# View coverage report
start htmlcov/index.html
```

## Monitoring

### Local Development
- Health check: http://localhost:8100/health
- API docs: http://localhost:8100/docs
- Metrics: http://localhost:8100/metrics

### Docker
```powershell
# View logs
docker-compose logs -f openmarkets-integration

# Check service status
docker-compose ps

# Restart services
docker-compose restart
```

### Kubernetes
```powershell
# View pods
kubectl get pods -n ultracore

# View logs
kubectl logs -f deployment/openmarkets-integration -n ultracore

# Port forward
kubectl port-forward svc/openmarkets-service 8100:8100 -n ultracore
```

## Configuration

All configuration via environment variables in `.env`:
```env
# API Configuration
OPENMARKETS_API_KEY=your-key
OPENMARKETS_API_SECRET=your-secret
OPENMARKETS_ENVIRONMENT=sandbox  # or production

# Feature Flags
OPENMARKETS_EVENT_STORE_ENABLED=true
OPENMARKETS_DATA_MESH_ENABLED=true
OPENMARKETS_ML_ENABLED=true
OPENMARKETS_RL_ENABLED=true
OPENMARKETS_MCP_ENABLED=true

# Infrastructure
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
POSTGRES_HOST=localhost
REDIS_HOST=localhost
```

## Troubleshooting

### "Connection refused" errors
- Ensure all services are running: `docker-compose ps`
- Check service health: `curl http://localhost:8100/health`

### "Authentication failed"
- Verify API credentials in `.env`
- Check OpenMarkets environment (sandbox vs production)

### ML models not loading
- Ensure models are trained: Run training scripts first
- Check model directory: `ls models/`

### Kafka connection issues
- Verify Kafka is running: `docker-compose ps kafka`
- Check Kafka logs: `docker-compose logs kafka`

## Support

- Documentation: See README.md
- Issues: GitHub Issues
- Email: dev@turingdynamics.com.au

## Next Steps

1. ? Complete this Quick Start
2. ?? Read full documentation in README.md
3. ?? Explore examples in `examples/`
4. ?? Deploy to production
5. ?? Set up monitoring dashboards
6. ?? Train custom ML models
