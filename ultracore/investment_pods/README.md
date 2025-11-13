# Investment Pods System

**AI-Powered Goal-Based Investment Platform for UltraWealth Automated Investment Service**

## Overview

Investment Pods is a comprehensive goal-based investment system that combines:
- 🎯 **AI-Powered Portfolio Optimization** (Modern Portfolio Theory + Black-Litterman)
- 🛤️ **Smart Glide Paths** (automatic risk reduction as goals approach)
- 🛡️ **Downside Protection** (15% circuit breaker for capital preservation)
- 🇦🇺 **Australian Tax Optimization** (franking credits, CGT discount, FHSS)
- 💬 **Anya AI Assistant** (conversational interface, 24/7 support)
- 📊 **Real-Time Market Data** (Yahoo Finance integration)

## Architecture

### Event-Driven Design

```
┌─────────────────────────────────────────────────────────┐
│                    Investment Pods                       │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │   Kafka      │───▶│     Pod      │───▶│  Domain   │ │
│  │   Events     │    │  Aggregate   │    │  Services │ │
│  └──────────────┘    └──────────────┘    └───────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Core Services                        │  │
│  │  • Portfolio Optimizer (MPT + Black-Litterman)   │  │
│  │  • Glide Path Engine (automatic transitions)     │  │
│  │  • Downside Protection (circuit breakers)        │  │
│  │  • Tax Optimizer (franking, CGT, FHSS)           │  │
│  │  • ETF Universe Manager (ASX ETFs)               │  │
│  │  • Market Data Service (Yahoo Finance)           │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Anya AI Layer                        │  │
│  │  • Conversational Pod creation                    │  │
│  │  • Proactive notifications                        │  │
│  │  • 24/7 Q&A support                               │  │
│  │  • Educational content                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Pod Aggregate (`aggregates/pod_aggregate.py`)
Event-sourced aggregate managing Pod lifecycle:
- Pod creation and activation
- Portfolio optimization
- Glide path transitions
- Circuit breaker triggers
- Rebalancing events
- Contributions and withdrawals

#### 2. Portfolio Optimizer (`services/portfolio_optimizer.py`)
AI-powered optimization using:
- **Modern Portfolio Theory** (Markowitz mean-variance)
- **Black-Litterman Model** (market views + investor beliefs)
- **Risk Parity** (equal risk contribution)
- **Constraints**: Max 6 ETFs, 5-40% per ETF, max 60% single provider

#### 3. Glide Path Engine (`services/glide_path_engine.py`)
Automatic risk reduction based on timeline:
- **10 years out**: 80-90% equity
- **5 years out**: 60-70% equity
- **2 years out**: 30-50% equity
- **1 year out**: 10-30% equity

Different glide paths for different goals (first home vs retirement).

#### 4. Downside Protection (`services/downside_protection.py`)
Circuit breaker system:
- **15% drawdown limit** (automatic defensive shift)
- **Warning at 10%** (monitoring intensifies)
- **Recovery threshold 5%** (resume normal allocation)
- **Defensive allocation**: 70% defensive, 30% equity

#### 5. Tax Optimizer (`services/tax_optimizer.py`)
Australian tax benefits:
- **Franking Credits**: 30% company tax credit
- **CGT Discount**: 50% discount for >12 month holdings
- **FHSS**: First Home Super Saver integration
- **Tax Loss Harvesting**: Automatic opportunity identification

#### 6. ETF Universe Manager (`services/etf_universe_manager.py`)
Manages ASX-listed ETF universe:
- **Business Rules**: AUM >$50M, Volume >$500K, Expense <1.0%
- **12 Core ETFs**: VAS, IOZ, A200, VGS, IVV, NDQ, VAF, BOND, etc.
- **Diversification Validation**: Max 6 ETFs, max 40% single provider

#### 7. Market Data Service (`services/market_data_service.py`)
Real-time Yahoo Finance integration:
- **Historical data**: 5 years of daily prices
- **Returns calculation**: 1Y, 3Y, 5Y annualized
- **Volatility**: Annualized standard deviation
- **Correlation matrix**: For optimization
- **Real Australian ETF data**: VAS 10.28% 3Y return, 12.61% volatility

#### 8. Anya AI Service (`anya/anya_service.py`)
Conversational AI assistant:
- **Pod Creation**: Guided conversational flow
- **Progress Updates**: Monthly personalized messages
- **Notifications**: Glide path, circuit breaker, rebalancing
- **24/7 Q&A**: 10+ FAQ topics with detailed explanations
- **Educational**: Explains complex concepts simply

## Business Rules

### Portfolio Construction
- **Max ETFs**: 6 per Pod
- **Min ETF Weight**: 5%
- **Max ETF Weight**: 40%
- **Max Single Provider**: 60%
- **Rebalancing Threshold**: 5% drift

### ETF Selection
- **Min AUM**: $50M
- **Min Daily Volume**: $500K
- **Max Expense Ratio**: 1.0%
- **Min Track Record**: 12 months

### Risk Management
- **Circuit Breaker**: 15% drawdown
- **Warning Threshold**: 10% drawdown
- **Recovery Threshold**: 5% drawdown
- **Max Drawdown Target**: 20% (portfolio construction)

### Glide Path
- **Transition Frequency**: Quarterly reviews
- **Min Equity**: 10% (1 year from goal)
- **Max Equity**: 90% (10+ years from goal)
- **Defensive Shift**: 10% per year (last 5 years)

## Goal Types

1. **First Home** (FHSS eligible)
   - Typical timeline: 3-7 years
   - Glide path: Aggressive early, conservative late
   - Tax optimization: FHSS contributions

2. **Retirement**
   - Typical timeline: 10-40 years
   - Glide path: Gradual transition over decades
   - Tax optimization: Franking credits, CGT discount

3. **Wealth Accumulation**
   - Flexible timeline
   - Glide path: Based on client timeline
   - Tax optimization: Full suite

4. **Emergency Fund**
   - Short timeline: 1-2 years
   - Glide path: Conservative throughout
   - Tax optimization: Minimal (focus on liquidity)

5. **Education**
   - Typical timeline: 5-18 years
   - Glide path: Moderate early, conservative late
   - Tax optimization: CGT discount

## API Integration

### MCP Tools (6 Functions)

```python
from ultracore.investment_pods.mcp.pod_mcp_tools import PodMCPTools

tools = PodMCPTools(pod_service)

# Create Pod
result = tools.create_goal_pod(
    client_id="client_123",
    goal_type="first_home",
    goal_name="First Home Deposit",
    target_amount=200000.0,
    target_date="2029-11-15",
    risk_tolerance=4,  # Balanced
    monthly_contribution=2000.0
)

# Monitor risk
risk = tools.monitor_downside_risk(pod_id="pod_123")

# Calculate glide path
glide_path = tools.calculate_glide_path(
    goal_type="first_home",
    target_date="2029-11-15"
)
```

### Data Mesh Product

```python
from ultracore.investment_pods.data_mesh.pod_data_product import PodDataProduct

data_product = PodDataProduct(pod_repository)

# Get Pod summary
summary = data_product.get_pod_summary("pod_123")

# Get portfolio composition
composition = data_product.get_portfolio_composition("pod_123")

# Get aggregate metrics
metrics = data_product.get_aggregate_metrics()
```

## Example Usage

### Create a First Home Pod

```python
from ultracore.investment_pods.anya.anya_service import AnyaService

anya = AnyaService()

# Conversational Pod creation
result = anya.create_pod_conversational(
    client_id="client_123",
    conversation_context={
        "goal_type": "first_home",
        "goal_name": "My First Home",
        "target_amount": 200000,
        "target_date": "2029-11-15",
        "risk_tolerance": "balanced",
        "current_value": 50000
    }
)

print(result["anya_response"])
# 🎯 Great! I've created your "My First Home" Pod!
# 
# **Your Goal:**
# • Target Amount: $200,000
# • Target Date: November 2029
# • Time Horizon: 5 years
# ...
```

### Monitor Pod Progress

```python
# Generate monthly update
update = anya.generate_progress_update(
    pod=pod,
    monthly_return=Decimal("1.2"),
    on_track=True
)

print(update)
# 📊 Monthly Update: My First Home
# 
# Great news! You're on track to reach your goal! 🎉
# ...
```

### Ask Anya Questions

```python
# 24/7 Q&A support
answer = anya.answer_question(
    client_id="client_123",
    question="How does the circuit breaker work?",
    pod=pod
)

print(answer)
# **Circuit Breaker - Your 15% Protection:**
# 
# A circuit breaker is like an emergency brake for your portfolio!
# ...
```

## Testing

Run comprehensive tests:

```bash
python3 ultracore/investment_pods/tests/test_pod_lifecycle.py
```

Tests cover:
- ✅ Pod creation (all goal types)
- ✅ Portfolio optimization
- ✅ Glide path transitions
- ✅ Circuit breaker activation
- ✅ Rebalancing
- ✅ Contributions and withdrawals

## Performance

### Real Australian ETF Data (Yahoo Finance)

| ETF | 3Y Return | Volatility | Max Drawdown |
|-----|-----------|------------|--------------|
| VAS | 10.28%    | 12.61%     | 15.18%       |
| VGS | 21.10%    | 16.50%     | 20.50%       |
| NDQ | 30.25%    | 22.50%     | 28.50%       |

### Optimization Results

Sample balanced portfolio (5-year first home goal):
- **Expected Return**: 11.5% p.a.
- **Volatility**: 13.2%
- **Sharpe Ratio**: 0.57
- **Total Fees**: 0.18% p.a.
- **Franking Yield**: 2.1% p.a.

## Deployment

### Prerequisites
- Python 3.11+
- Kafka cluster
- PostgreSQL (event store)
- Redis (caching)
- Yahoo Finance API access

### Environment Variables
```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
POSTGRES_CONNECTION_STRING=postgresql://...
REDIS_URL=redis://localhost:6379
```

### Docker Deployment
```bash
docker build -t investment-pods .
docker run -p 8000:8000 investment-pods
```

## Monitoring

Key metrics to monitor:
- **Pod Creation Rate**: Pods/day
- **Total AUM**: Aggregate value across all Pods
- **Average Return**: Portfolio performance
- **Circuit Breaker Triggers**: Frequency and recovery
- **Glide Path Transitions**: Automatic adjustments
- **Rebalancing Events**: Frequency and cost

## Roadmap

### Phase 2 (Q1 2026)
- [ ] Machine learning return predictions
- [ ] Dynamic glide paths (market-adaptive)
- [ ] Multi-currency support
- [ ] International tax optimization

### Phase 3 (Q2 2026)
- [ ] Options overlay strategies
- [ ] ESG/sustainable investing filters
- [ ] Social features (goal sharing)
- [ ] Advanced tax loss harvesting

## License

Proprietary - UltraWealth Automated Investment Service

## Contact

**Anya AI Assistant**: Available 24/7 in the app
**Support**: support@ultrawealth.com.au
**Documentation**: https://docs.ultrawealth.com.au/investment-pods

---

Built with ❤️ by the UltraWealth team
