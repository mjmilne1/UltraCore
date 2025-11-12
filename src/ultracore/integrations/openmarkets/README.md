# OpenMarkets Integration for UltraCore

Enterprise-grade integration with OpenMarkets Australian trading infrastructure.

## Features

### ?? Core Capabilities
- **Event-Sourced Trading**: Complete audit trail with temporal queries
- **Multi-Exchange Access**: ASX, Chi-X, NSX execution
- **Real-time Market Data**: WebSocket streaming
- **Account Opening**: White-label KYC/AML onboarding

### ?? Agentic AI (Anya)
- **Natural Language Trading**: "Buy 1000 BHP at market price"
- **Portfolio Analysis**: "What's my tech sector exposure?"
- **Risk Monitoring**: "Alert me if portfolio volatility exceeds 15%"
- **Market Insights**: "Summarize today's market movements"

### ?? Machine Learning
- **Price Prediction**: LSTM-based time series forecasting
- **Portfolio Optimization**: ML-enhanced Modern Portfolio Theory
- **Risk Scoring**: Ensemble models for trade risk assessment
- **Sentiment Analysis**: FinBERT for market sentiment

### ?? Reinforcement Learning
- **Adaptive Strategies**: PPO and A2C trading agents
- **Dynamic Position Sizing**: RL-based risk management
- **Continuous Learning**: Learn from market feedback

### ?? MCP Framework
- **AI Tool Integration**: Expose trading as MCP tools
- **Claude Integration**: Native support for Claude AI
- **Natural Workflows**: AI agents can trade autonomously

### ?? Data Mesh
- **Domain-Oriented Products**: Trades, Positions, Market Data
- **Self-Serve Infrastructure**: Easy data access
- **Federated Governance**: Distributed ownership

### ? Australian Compliance
- **ASIC Reporting**: Market Integrity Rules compliance
- **Best Execution**: RG 254 monitoring
- **AML/CTF**: Transaction monitoring and reporting
- **Audit Trails**: Complete event-sourced history

## Quick Start

\\\python
from ultracore.integrations.openmarkets import OpenMarketsClient
from ultracore.integrations.openmarkets.agents import AnyaTradingAgent
from ultracore.integrations.openmarkets.config import OpenMarketsConfig

# Initialize client
config = OpenMarketsConfig(
    api_key="your-api-key",
    api_secret="your-api-secret",
    environment="sandbox"
)
client = OpenMarketsClient(config)

# Use Anya for natural language trading
agent = AnyaTradingAgent(
    client=client,
    anthropic_client=anthropic_client,
    account_id="your-account-id"
)

# Execute natural language trade
result = await agent.execute("Buy 1000 BHP shares at market price")
print(f"Order placed: {result['order_id']}")

# Get positions
positions = await client.get_positions(account_id="your-account-id")

# Stream market data
async for data in client.stream_market_data(["BHP", "CBA", "WES"]):
    print(f"{data.symbol}: ")
\\\

## Architecture

\\\
+-------------------------------------------------+
¦ OpenMarkets Integration                         ¦
¦                                                 ¦
¦ +---------------------------------------------+ ¦
¦ ¦ Agentic AI Layer (Anya)                     ¦ ¦
¦ ¦  • Natural language trading                 ¦ ¦
¦ ¦  • Portfolio management                     ¦ ¦
¦ ¦  • Risk monitoring                          ¦ ¦
¦ +---------------------------------------------+ ¦
¦              ¦                                   ¦
¦ +------------?-------------------------------+ ¦
¦ ¦ ML Layer              ¦ RL Layer           ¦ ¦
¦ ¦  • Price prediction   ¦  • PPO/A2C agents  ¦ ¦
¦ ¦  • Portfolio opt      ¦  • Adaptive        ¦ ¦
¦ ¦  • Risk scoring       ¦  • strategies      ¦ ¦
¦ +--------------------------------------------+ ¦
¦              ¦                  ¦               ¦
¦ +------------?------------------?------------+ ¦
¦ ¦ Trading Engine                             ¦ ¦
¦ ¦  • Order management                        ¦ ¦
¦ ¦  • Execution                               ¦ ¦
¦ ¦  • Position tracking                       ¦ ¦
¦ +-------------------------------------------+ ¦
¦              ¦                                 ¦
¦ +------------?--------------------------------+¦
¦ ¦ Event Store (UltraPlatform)                 ¦¦
¦ ¦  • OrderPlacedEvent                         ¦¦
¦ ¦  • OrderExecutedEvent                       ¦¦
¦ ¦  • PositionUpdatedEvent                     ¦¦
¦ ¦  • MarketDataReceivedEvent                  ¦¦
¦ +---------------------------------------------+¦
¦              ¦                                  ¦
¦ +------------?---------------------------------¦
¦ ¦ Data Mesh Products                           ¦
¦ ¦  • Trades Product                            ¦
¦ ¦  • Positions Product                         ¦
¦ ¦  • Market Data Product                       ¦
¦ +----------------------------------------------+
+-------------------------------------------------+
         ¦
         ?
+-----------------------------------------+
¦ OpenMarkets API                         ¦
¦  • ASX, Chi-X, NSX                      ¦
¦  • Real-time market data                ¦
¦  • Account opening                      ¦
+-----------------------------------------+
\\\

## Configuration

Set environment variables:

\\\ash
export OPENMARKETS_API_KEY=your-api-key
export OPENMARKETS_API_SECRET=your-api-secret
export OPENMARKETS_ENVIRONMENT=sandbox  # or production
export OPENMARKETS_EVENT_STORE_ENABLED=true
export OPENMARKETS_DATA_MESH_ENABLED=true
export OPENMARKETS_ML_ENABLED=true
export OPENMARKETS_RL_ENABLED=true
export OPENMARKETS_MCP_ENABLED=true
\\\

## Integration with UltraCore Domains

\\\python
from ultracore.domains.investment import InvestmentDomain
from ultracore.integrations.openmarkets import OpenMarketsClient

# Initialize investment domain with OpenMarkets
investment_domain = InvestmentDomain(
    trading_client=OpenMarketsClient(),
    event_store=event_store,
    data_mesh=data_mesh
)

# Execute trades through domain
await investment_domain.execute_trade(
    account_id="account-123",
    symbol="BHP",
    quantity=1000,
    side="BUY"
)
\\\

## Data Mesh Products

### Trades Product
\\\python
from ultracore.integrations.openmarkets.datamesh import TradesDataProduct

trades_product = TradesDataProduct(event_store)
trades_df = await trades_product.get_trades(
    account_id="account-123",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31)
)

analytics = await trades_product.get_trade_analytics(
    account_id="account-123"
)
\\\

### Positions Product
\\\python
from ultracore.integrations.openmarkets.datamesh import PositionsDataProduct

positions_product = PositionsDataProduct(client)
positions_df = await positions_product.get_positions(account_id="account-123")
\\\

## MCP Server

Start the MCP server to expose trading tools to AI agents:

\\\python
from ultracore.integrations.openmarkets.mcp import OpenMarketsMCPServer

server = OpenMarketsMCPServer(
    client=client,
    account_id="your-account-id"
)

await server.start(port=8100)
\\\

AI agents (Claude, etc.) can now use tools like:
- \place_trade(symbol="BHP", action="buy", quantity=1000)\
- \get_position(symbol="BHP")\
- \get_portfolio()\
- \nalyze_market(symbol="BHP")\
- \optimize_portfolio()\

## Testing

\\\ash
# Unit tests
pytest tests/unit/integrations/openmarkets/

# Integration tests (requires sandbox credentials)
pytest tests/integration/openmarkets/

# Load tests
pytest tests/load/openmarkets/
\\\

## Compliance

All trading activities are:
- ? Event-sourced for complete audit trail
- ? Monitored for best execution (ASIC RG 254)
- ? Reported to ASIC per Market Integrity Rules
- ? AML/CTF compliant with transaction monitoring
- ? Immutable and temporally queryable

## License

Copyright © 2025 Richelou Pty Ltd. All Rights Reserved.
