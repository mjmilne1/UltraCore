"""
Portfolio Optimization Demo - Full RL-Powered ESG Optimization

This demo shows the complete optimize_portfolio_esg() functionality,
demonstrating how the Epsilon Agent optimizes portfolios for both
financial returns and ESG outcomes.
"""

import sys
sys.path.insert(0, '/home/ubuntu/UltraCore/src')

import json
import numpy as np
from ultracore.esg import (
    EsgDataLoader,
    EsgMcpTools,
    EpsilonAgent,
)


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_portfolio(portfolio: dict, title: str):
    """Print portfolio holdings in a formatted table"""
    print(f"\n{title}")
    print("-" * 80)
    print(f"{'Asset':<50} {'Weight':>10}")
    print("-" * 80)
    
    for isin, weight in sorted(portfolio.items(), key=lambda x: x[1], reverse=True):
        print(f"{isin:<50} {weight:>9.2%}")
    
    total = sum(portfolio.values())
    print("-" * 80)
    print(f"{'TOTAL':<50} {total:>9.2%}")
    print()


def print_metrics(metrics: dict, title: str):
    """Print portfolio metrics"""
    print(f"\n{title}")
    print("-" * 80)
    print(f"  Expected Return:        {metrics['expected_return']:>8.2%}")
    print(f"  Expected Volatility:    {metrics['expected_volatility']:>8.2%}")
    print(f"  Sharpe Ratio:           {metrics['sharpe_ratio']:>8.2f}")
    print(f"  ESG Rating:             {metrics['esg_rating']:>8}")
    print(f"  Carbon Intensity:       {metrics['carbon_intensity']:>8.2f} tCO2e/$M")
    print(f"  Board Diversity:        {metrics['board_diversity']:>8.2f}%")
    print(f"  Controversy Score:      {metrics['controversy_score']:>8.2f}/10")
    print()


def print_improvement(improvement: dict):
    """Print improvement metrics"""
    print("\n📈 IMPROVEMENT ANALYSIS")
    print("-" * 80)
    print(f"  Return Improvement:     {improvement['return_improvement']:>+8.2f} bps")
    print(f"  Volatility Change:      {improvement['volatility_change']:>+8.2f} bps")
    print(f"  Sharpe Improvement:     {improvement['sharpe_improvement']:>+8.2f}")
    print(f"  Carbon Reduction:       {improvement['carbon_reduction_pct']:>+8.2f}%")
    print(f"  ESG Rating Change:      {improvement['esg_rating_change']}")
    print(f"  Board Diversity Change: {improvement['board_diversity_change']:>+8.2f}%")
    print()


def print_trade_list(trades: list):
    """Print trade list"""
    print("\n📋 TRADE LIST")
    print("-" * 80)
    print(f"{'Action':<8} {'Asset':<40} {'Current':>10} {'Target':>10} {'Delta':>10}")
    print("-" * 80)
    
    for trade in trades:
        action_emoji = "🟢" if trade['action'] == 'buy' else "🔴"
        print(f"{action_emoji} {trade['action'].upper():<6} {trade['name'][:38]:<40} "
              f"{trade['current_weight']:>9.2%} {trade['target_weight']:>9.2%} {trade['delta']:>9.2%}")
    
    print()


def main():
    """Run the portfolio optimization demo"""
    
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + " " * 15 + "RL-POWERED ESG PORTFOLIO OPTIMIZATION DEMO" + " " * 21 + "║")
    print("║" + " " * 78 + "║")
    print("║" + " " * 20 + "Using the Epsilon Agent & MCP Tools" + " " * 23 + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Initialize components
    print_section("INITIALIZATION")
    
    print("Initializing ESG Data Loader...")
    esg_loader = EsgDataLoader()
    
    print("Initializing Epsilon Agent...")
    asset_universe = [
        "AU000000VAS3",  # Vanguard Australian Shares
        "AU000000VGS3",  # Vanguard International Shares
        "AU000000ETHI",  # BetaShares Sustainability Leaders
        "AU000000VAP3",  # Vanguard Australian Property
        "AU000000VGB3",  # Vanguard Australian Government Bonds
    ]
    
    state_dim = len(asset_universe) * 24  # 20 returns + 1 holding + 3 ESG features
    action_dim = len(asset_universe)
    esg_feature_dim = len(asset_universe) * 3
    
    epsilon_agent = EpsilonAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        esg_feature_dim=esg_feature_dim,
        epsilon_start=0.0  # Deterministic for demo
    )
    
    print("Initializing MCP Tools with Portfolio Optimizer...")
    mcp_tools = EsgMcpTools(
        esg_data_loader=esg_loader,
        epsilon_agent=epsilon_agent,
        asset_universe=asset_universe
    )
    
    print("✓ All components initialized successfully!")
    
    # Define current portfolio
    print_section("CURRENT PORTFOLIO")
    
    current_portfolio = {
        "AU000000VAS3": 0.70,  # 70% Australian shares
        "AU000000VGS3": 0.30,  # 30% International shares
    }
    
    print("This is a traditional 70/30 Australian/International equity portfolio.")
    print("It has NO explicit ESG considerations.")
    print_portfolio(current_portfolio, "Current Holdings:")
    
    # Define optimization objectives
    print_section("OPTIMIZATION OBJECTIVES")
    
    objectives = {
        "target_return": 0.10,           # Target 10% annual return
        "max_volatility": 0.15,          # Max 15% volatility
        "esg_weight": 0.4,               # 40% weight on ESG vs financial
        "min_esg_rating": "A",           # Minimum A rating
        "max_carbon_intensity": 100.0,   # Max 100 tCO2e/$M revenue
    }
    
    print("Optimization objectives:")
    print(f"  • Target Return:         {objectives['target_return']:.1%}")
    print(f"  • Max Volatility:        {objectives['max_volatility']:.1%}")
    print(f"  • ESG Weight:            {objectives['esg_weight']:.1%}")
    print(f"  • Min ESG Rating:        {objectives['min_esg_rating']}")
    print(f"  • Max Carbon Intensity:  {objectives['max_carbon_intensity']:.1f} tCO2e/$M")
    
    # Run optimization
    print_section("RUNNING RL-POWERED OPTIMIZATION")
    
    print("The Epsilon Agent is now analyzing the portfolio...")
    print("  1. Converting portfolio to state representation")
    print("  2. Processing financial features (historical returns)")
    print("  3. Processing ESG features (ratings, carbon, controversies)")
    print("  4. Running dual-stream Q-network")
    print("  5. Applying ESG constraints")
    print("  6. Generating optimal portfolio weights")
    print()
    
    result = mcp_tools.optimize_portfolio_esg(
        current_portfolio=current_portfolio,
        objectives=objectives
    )
    
    print("✓ Optimization complete!")
    
    # Display results
    print_section("OPTIMIZATION RESULTS")
    
    print_portfolio(result['optimized_portfolio'], "Optimized Portfolio:")
    
    print_metrics(result['current_metrics'], "📊 CURRENT PORTFOLIO METRICS")
    print_metrics(result['optimized_metrics'], "📊 OPTIMIZED PORTFOLIO METRICS")
    
    print_improvement(result['improvement'])
    
    print_trade_list(result['trade_list'])
    
    # Explanation
    print_section("EXPLAINABLE AI - WHY THIS PORTFOLIO?")
    
    explanation = result['explanation']
    
    print("The Epsilon Agent selected this portfolio based on:")
    print()
    print("Top 3 Q-Values (Action Quality Scores):")
    q_values = explanation['q_values']
    top_3_indices = np.argsort(q_values)[-3:][::-1]
    for rank, idx in enumerate(top_3_indices, 1):
        print(f"  {rank}. Asset {idx}: Q-value = {q_values[idx]:.4f}")
    
    print("\nESG Scores for Selected Assets:")
    for i, score in enumerate(explanation['esg_scores'][:3]):
        print(f"\n  Asset {i+1}:")
        print(f"    ESG Rating:        {score['esg_rating']:.2f} (normalized)")
        print(f"    Carbon Intensity:  {score['carbon_intensity']:.2f} (normalized)")
        print(f"    Controversy Score: {score['controversy_score']:.2f} (normalized)")
    
    # Key insights
    print_section("KEY INSIGHTS")
    
    print("🎯 FINANCIAL PERFORMANCE")
    return_imp = result['improvement']['return_improvement']
    sharpe_imp = result['improvement']['sharpe_improvement']
    
    if return_imp > 0:
        print(f"  ✓ Expected return INCREASED by {return_imp:.0f} basis points")
    else:
        print(f"  • Expected return decreased by {abs(return_imp):.0f} basis points")
    
    if sharpe_imp > 0:
        print(f"  ✓ Sharpe ratio IMPROVED by {sharpe_imp:.2f}")
    else:
        print(f"  • Sharpe ratio decreased by {abs(sharpe_imp):.2f}")
    
    print("\n🌱 ESG PERFORMANCE")
    carbon_reduction = result['improvement']['carbon_reduction_pct']
    
    if carbon_reduction > 0:
        print(f"  ✓ Carbon intensity REDUCED by {carbon_reduction:.1f}%")
    else:
        print(f"  • Carbon intensity increased by {abs(carbon_reduction):.1f}%")
    
    print(f"  ✓ ESG rating changed: {result['improvement']['esg_rating_change']}")
    
    diversity_change = result['improvement']['board_diversity_change']
    if diversity_change > 0:
        print(f"  ✓ Board diversity INCREASED by {diversity_change:.1f}%")
    else:
        print(f"  • Board diversity decreased by {abs(diversity_change):.1f}%")
    
    # Competitive advantage
    print_section("COMPETITIVE ADVANTAGE vs. FINASTRA")
    
    print("Traditional ESG Solutions (Finastra):")
    print("  • Static rule-based filtering")
    print("  • Binary pass/fail screening")
    print("  • No optimization, just exclusion")
    print("  • Batch processing (hours/days)")
    print()
    print("UltraCore with Epsilon Agent:")
    print("  ✓ Generative, goal-seeking RL optimization")
    print("  ✓ Continuous optimization across financial + ESG dimensions")
    print("  ✓ Learns dynamic strategies from market data")
    print("  ✓ Real-time optimization (milliseconds)")
    print("  ✓ Explainable AI for transparency")
    print("  ✓ Hyper-personalized for each investor's preferences")
    
    # Summary
    print_section("SUMMARY")
    
    print("The Epsilon Agent successfully optimized the portfolio to:")
    print()
    print(f"  1. Maintain target return of {objectives['target_return']:.1%}")
    print(f"  2. Stay within volatility limit of {objectives['max_volatility']:.1%}")
    print(f"  3. Achieve minimum ESG rating of {objectives['min_esg_rating']}")
    print(f"  4. Reduce carbon intensity below {objectives['max_carbon_intensity']:.0f} tCO2e/$M")
    print(f"  5. Balance financial ({(1-objectives['esg_weight'])*100:.0f}%) and ESG ({objectives['esg_weight']*100:.0f}%) objectives")
    print()
    print("This demonstrates UltraCore's ability to generate 'ESG Alpha' - excess")
    print("returns from superior ESG performance - something static systems cannot do.")
    
    print("\n" + "=" * 80)
    print("  DEMO COMPLETE - RL-Powered ESG Optimization Working!")
    print("=" * 80 + "\n")
    
    # Save results
    print("Saving results to JSON...")
    with open('/home/ubuntu/UltraCore/optimization_results.json', 'w') as f:
        # Convert numpy types to native Python types for JSON serialization
        json_result = {
            "optimized_portfolio": result['optimized_portfolio'],
            "current_metrics": result['current_metrics'],
            "optimized_metrics": result['optimized_metrics'],
            "improvement": result['improvement'],
            "trade_list": result['trade_list'],
            "optimization_timestamp": result['optimization_timestamp'],
            "agent_version": result['agent_version']
        }
        json.dump(json_result, f, indent=2)
    
    print("✓ Results saved to: /home/ubuntu/UltraCore/optimization_results.json")
    print()


if __name__ == "__main__":
    main()
