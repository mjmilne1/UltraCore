"""
Efficient Frontier Visualization
Visualize the efficient frontier for a portfolio of ETFs
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from ultracore.domains.wealth.integration.etf_data_provider import ETFDataProvider

def calculate_portfolio_metrics(weights, returns, cov_matrix):
    """Calculate portfolio return and volatility"""
    portfolio_return = np.sum(returns.mean() * weights) * 252
    portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
    return portfolio_return, portfolio_volatility

def generate_random_portfolios(returns, cov_matrix, num_portfolios=10000):
    """Generate random portfolio allocations"""
    num_assets = len(returns.columns)
    results = np.zeros((3, num_portfolios))
    weights_record = []
    
    for i in range(num_portfolios):
        # Random weights
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        weights_record.append(weights)
        
        # Calculate metrics
        portfolio_return, portfolio_volatility = calculate_portfolio_metrics(
            weights, returns, cov_matrix
        )
        
        # Calculate Sharpe ratio (assuming 4% risk-free rate)
        sharpe_ratio = (portfolio_return - 0.04) / portfolio_volatility
        
        # Store results
        results[0, i] = portfolio_volatility
        results[1, i] = portfolio_return
        results[2, i] = sharpe_ratio
    
    return results, weights_record

def find_efficient_frontier(returns, cov_matrix, num_points=100):
    """Calculate efficient frontier"""
    from scipy.optimize import minimize
    
    num_assets = len(returns.columns)
    
    # Target returns
    min_return = returns.mean().min() * 252
    max_return = returns.mean().max() * 252
    target_returns = np.linspace(min_return, max_return, num_points)
    
    efficient_portfolios = []
    
    for target_return in target_returns:
        # Minimize volatility for target return
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Weights sum to 1
            {'type': 'eq', 'fun': lambda w: np.sum(returns.mean() * w) * 252 - target_return}  # Target return
        ]
        
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_guess = np.array([1/num_assets] * num_assets)
        
        result = minimize(
            lambda w: np.sqrt(np.dot(w.T, np.dot(cov_matrix * 252, w))),
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            volatility = result.fun
            efficient_portfolios.append({
                'return': target_return,
                'volatility': volatility,
                'weights': result.x
            })
    
    return efficient_portfolios

def visualize_efficient_frontier(tickers, lookback_years=5):
    """
    Visualize efficient frontier for given tickers
    """
    
    print("="*80)
    print("Efficient Frontier Visualization")
    print("="*80)
    print(f"\nETFs: {', '.join(tickers)}")
    print(f"Lookback Period: {lookback_years} years\n")
    
    # Initialize data provider
    dp = ETFDataProvider(data_dir="data/etf")
    
    # Load data for all tickers
    print("Loading ETF data...")
    returns_list = []
    
    for ticker in tickers:
        data = dp.load_etf_data(ticker)
        if data is not None and not data.empty:
            # Calculate daily returns
            data['returns'] = data['Close'].pct_change()
            returns_list.append(data['returns'].dropna())
            print(f"  ✅ {ticker}: {len(data)} data points")
        else:
            print(f"  ❌ {ticker}: No data")
            return
    
    # Combine returns into DataFrame
    returns = pd.concat(returns_list, axis=1, keys=tickers)
    returns = returns.dropna()
    
    # Limit to lookback period
    if lookback_years:
        cutoff_date = returns.index[-1] - pd.Timedelta(days=lookback_years*365)
        returns = returns[returns.index >= cutoff_date]
    
    print(f"\nTotal observations: {len(returns)}")
    print(f"Date range: {returns.index[0].date()} to {returns.index[-1].date()}")
    
    # Calculate covariance matrix
    cov_matrix = returns.cov()
    
    print("\n" + "="*80)
    print("Generating Random Portfolios...")
    print("="*80)
    
    # Generate random portfolios
    random_results, weights_record = generate_random_portfolios(returns, cov_matrix, num_portfolios=10000)
    
    print(f"Generated 10,000 random portfolios")
    
    print("\n" + "="*80)
    print("Calculating Efficient Frontier...")
    print("="*80)
    
    # Calculate efficient frontier
    efficient_portfolios = find_efficient_frontier(returns, cov_matrix, num_points=100)
    
    print(f"Calculated {len(efficient_portfolios)} efficient portfolios")
    
    # Find maximum Sharpe ratio portfolio
    max_sharpe_idx = np.argmax(random_results[2])
    max_sharpe_return = random_results[1, max_sharpe_idx]
    max_sharpe_volatility = random_results[0, max_sharpe_idx]
    max_sharpe_weights = weights_record[max_sharpe_idx]
    
    # Find minimum volatility portfolio
    min_vol_idx = np.argmin(random_results[0])
    min_vol_return = random_results[1, min_vol_idx]
    min_vol_volatility = random_results[0, min_vol_idx]
    min_vol_weights = weights_record[min_vol_idx]
    
    print("\n" + "="*80)
    print("Optimal Portfolios")
    print("="*80)
    
    print("\n1. Maximum Sharpe Ratio Portfolio:")
    print(f"   Expected Return: {max_sharpe_return*100:.2f}%")
    print(f"   Volatility: {max_sharpe_volatility*100:.2f}%")
    print(f"   Sharpe Ratio: {random_results[2, max_sharpe_idx]:.2f}")
    print("   Allocation:")
    for ticker, weight in zip(tickers, max_sharpe_weights):
        if weight > 0.01:
            print(f"     {ticker}: {weight*100:.1f}%")
    
    print("\n2. Minimum Volatility Portfolio:")
    print(f"   Expected Return: {min_vol_return*100:.2f}%")
    print(f"   Volatility: {min_vol_volatility*100:.2f}%")
    print(f"   Sharpe Ratio: {(min_vol_return - 0.04) / min_vol_volatility:.2f}")
    print("   Allocation:")
    for ticker, weight in zip(tickers, min_vol_weights):
        if weight > 0.01:
            print(f"     {ticker}: {weight*100:.1f}%")
    
    # Create visualization
    print("\n" + "="*80)
    print("Creating Visualization...")
    print("="*80)
    
    plt.figure(figsize=(14, 10))
    
    # Plot random portfolios (colored by Sharpe ratio)
    scatter = plt.scatter(
        random_results[0, :],
        random_results[1, :],
        c=random_results[2, :],
        cmap='viridis',
        marker='o',
        s=10,
        alpha=0.3,
        label='Random Portfolios'
    )
    plt.colorbar(scatter, label='Sharpe Ratio')
    
    # Plot efficient frontier
    ef_volatility = [p['volatility'] for p in efficient_portfolios]
    ef_return = [p['return'] for p in efficient_portfolios]
    plt.plot(ef_volatility, ef_return, 'r-', linewidth=3, label='Efficient Frontier')
    
    # Plot maximum Sharpe ratio portfolio
    plt.scatter(
        max_sharpe_volatility,
        max_sharpe_return,
        marker='*',
        color='gold',
        s=500,
        edgecolors='black',
        linewidths=2,
        label='Max Sharpe Ratio',
        zorder=5
    )
    
    # Plot minimum volatility portfolio
    plt.scatter(
        min_vol_volatility,
        min_vol_return,
        marker='*',
        color='red',
        s=500,
        edgecolors='black',
        linewidths=2,
        label='Min Volatility',
        zorder=5
    )
    
    # Plot individual assets
    for i, ticker in enumerate(tickers):
        asset_return = returns[ticker].mean() * 252
        asset_volatility = returns[ticker].std() * np.sqrt(252)
        plt.scatter(
            asset_volatility,
            asset_return,
            marker='D',
            s=200,
            label=ticker,
            edgecolors='black',
            linewidths=1.5,
            zorder=4
        )
    
    plt.xlabel('Volatility (Standard Deviation)', fontsize=12)
    plt.ylabel('Expected Annual Return', fontsize=12)
    plt.title(f'Efficient Frontier - {", ".join(tickers)}\n({lookback_years} Year Lookback)', fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Format axes as percentages
    ax = plt.gca()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x*100:.0f}%'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y*100:.0f}%'))
    
    # Save figure
    output_file = "efficient_frontier.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualization saved to: {output_file}")
    
    # Show plot
    plt.show()
    
    print("\n" + "="*80)
    print("COMPLETE")
    print("="*80)

if __name__ == "__main__":
    # Portfolio tickers
    tickers = ['VAS', 'VGS', 'VTS', 'IOZ']
    
    # Visualize efficient frontier
    visualize_efficient_frontier(tickers, lookback_years=5)
