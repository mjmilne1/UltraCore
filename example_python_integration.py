"""
Example: Using UltraWealth from Python
Programmatic access to all components
"""

import asyncio
import sys
sys.path.insert(0, r'C:\Users\mjmil\UltraCore')

from ultracore.services.ultrawealth import (
    mcp_tools,
    ml_engine,
    rl_optimizer,
    agentic_ai,
    ultrawealth_datamesh
)

async def main():
    print("\n🤖 Using UltraWealth from Python...\n")
    
    # 1. Get ETF price via MCP
    print("[1/4] Getting ETF price via MCP...")
    price = await mcp_tools.get_etf_price("VAS.AX")
    print(f"✅ VAS.AX: ${price['price']}")
    
    # 2. Get ML prediction via MCP
    print("\n[2/4] Getting ML prediction via MCP...")
    prediction = await mcp_tools.predict_etf_price("VAS.AX")
    print(f"✅ Predicted: ${prediction['ensemble_prediction']:.2f} ({prediction['predicted_change_pct']:.2f}%)")
    
    # 3. Optimize portfolio via MCP
    print("\n[3/4] Optimizing portfolio via MCP...")
    portfolio = await mcp_tools.optimize_portfolio(
        tickers=["VAS.AX", "VGS.AX", "VAF.AX"],
        balance=100000,
        risk="moderate"
    )
    print(f"✅ Portfolio optimized!")
    print(f"   Sharpe Ratio: {portfolio['portfolio_metrics']['sharpe_ratio']:.2f}")
    print(f"   Expected Return: {portfolio['portfolio_metrics']['expected_return_annual']:.1f}%")
    print("\n   Allocation:")
    for ticker, alloc in portfolio['allocation'].items():
        print(f"      • {ticker}: {alloc['weight_pct']:.1f}% (${alloc['amount']:.0f})")
    
    # 4. Get AI recommendations
    print("\n[4/4] Getting AI recommendations...")
    recommendations = await mcp_tools.get_ai_recommendation(
        tickers=["VAS.AX", "VGS.AX", "VAF.AX"],
        current_allocation={
            "VAS.AX": {"weight": 0.33},
            "VGS.AX": {"weight": 0.33},
            "VAF.AX": {"weight": 0.34}
        }
    )
    print(f"✅ Market Sentiment: {recommendations['market_analysis']['sentiment']}")
    for rec in recommendations['recommendations']:
        print(f"   • {rec['ticker']}: {rec['action'].upper()} - {rec['reason']}")
    
    print("\n✅ Complete! All UltraWealth components accessible from Python\n")

if __name__ == "__main__":
    asyncio.run(main())
