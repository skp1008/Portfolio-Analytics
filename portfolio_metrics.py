"""
Portfolio Metrics: Calculate portfolio analytics and generate visualizations
This module calculates various portfolio metrics and creates tables/figures.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import pyodbc
from config import AZURE_SERVER, AZURE_DATABASE, AZURE_USERNAME, AZURE_PASSWORD


def get_azure_connection():
    """Create and return a connection to Azure SQL Database."""
    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={AZURE_SERVER};"
        f"Database={AZURE_DATABASE};"
        f"Uid={AZURE_USERNAME};"
        f"Pwd={AZURE_PASSWORD};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error connecting to Azure SQL Database: {str(e)}")
        raise


def load_portfolio_data(conn, ticker_list, start_date="2020-01-01", end_date=None):
    """
    Load stock data from Azure SQL Database for portfolio analysis.
    Assumes portfolio was purchased on start_date.
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    placeholders = ','.join(['?' for _ in ticker_list])
    query = f"""
    SELECT Ticker, Date, Close, Volume
    FROM stock_data
    WHERE Ticker IN ({placeholders})
    AND Date >= ? AND Date <= ?
    ORDER BY Ticker, Date
    """
    
    params = ticker_list + [start_date, end_date]
    df = pd.read_sql(query, conn, params=params)
    
    # Pivot to have tickers as columns
    prices_df = df.pivot(index='Date', columns='Ticker', values='Close')
    prices_df.index = pd.to_datetime(prices_df.index)
    
    return prices_df


def calculate_returns(prices_df):
    """Calculate daily returns from price data."""
    returns_df = prices_df.pct_change().dropna()
    return returns_df


def calculate_total_return(prices_df, start_date, end_date):
    """Calculate absolute gain/loss over a period."""
    start_prices = prices_df.loc[start_date]
    end_prices = prices_df.loc[end_date]
    total_returns = (end_prices / start_prices - 1) * 100
    return total_returns


def calculate_annualized_return(returns_df):
    """Calculate annualized return (normalized to yearly basis)."""
    mean_daily_return = returns_df.mean()
    trading_days = 252
    annualized_return = mean_daily_return * trading_days * 100
    return annualized_return


def calculate_volatility(returns_df):
    """Calculate annualized standard deviation (volatility)."""
    daily_std = returns_df.std()
    trading_days = 252
    annualized_volatility = daily_std * np.sqrt(trading_days) * 100
    return annualized_volatility


def calculate_beta(returns_df, market_returns=None):
    """
    Calculate Beta: Sensitivity to market movements.
    If market_returns not provided, uses equal-weighted portfolio as benchmark.
    """
    if market_returns is None:
        # Use equal-weighted portfolio as market proxy
        market_returns = returns_df.mean(axis=1)
    
    betas = {}
    for ticker in returns_df.columns:
        covariance = returns_df[ticker].cov(market_returns)
        market_variance = market_returns.var()
        if market_variance > 0:
            betas[ticker] = covariance / market_variance
        else:
            betas[ticker] = 1.0
    
    return pd.Series(betas)


def calculate_var(returns_df, confidence_level=0.95):
    """Calculate Value at Risk (VaR) at given confidence level."""
    var_values = returns_df.quantile(1 - confidence_level) * 100
    return var_values


def calculate_sharpe_ratio(returns_df, risk_free_rate=0.02):
    """
    Calculate Sharpe Ratio: (Return - Risk-free rate) / Standard deviation
    risk_free_rate is annual (default 2%)
    """
    annualized_returns = calculate_annualized_return(returns_df)
    annualized_vol = calculate_volatility(returns_df)
    
    # Convert risk-free rate to daily
    daily_rf = risk_free_rate / 252
    
    sharpe_ratios = {}
    for ticker in returns_df.columns:
        if annualized_vol[ticker] > 0:
            excess_return = (returns_df[ticker].mean() - daily_rf) * 252 * 100
            sharpe_ratios[ticker] = excess_return / annualized_vol[ticker]
        else:
            sharpe_ratios[ticker] = 0
    
    return pd.Series(sharpe_ratios)


def calculate_alpha(returns_df, beta_series, market_returns=None, risk_free_rate=0.02):
    """
    Calculate Alpha: Excess return beyond what beta predicts.
    """
    if market_returns is None:
        market_returns = returns_df.mean(axis=1)
    
    daily_rf = risk_free_rate / 252
    annualized_returns = calculate_annualized_return(returns_df)
    market_annualized = market_returns.mean() * 252 * 100
    
    alphas = {}
    for ticker in returns_df.columns:
        expected_return = risk_free_rate * 100 + beta_series[ticker] * (market_annualized - risk_free_rate * 100)
        alphas[ticker] = annualized_returns[ticker] - expected_return
    
    return pd.Series(alphas)


def calculate_turnover_rate(returns_df, rebalance_frequency='M'):
    """
    Calculate Turnover Rate: How frequently holdings change.
    Simplified version - measures variance in weights over time.
    """
    # For equal-weighted portfolio, turnover is based on rebalancing frequency
    # This is a simplified calculation
    if rebalance_frequency == 'M':
        turnover = 1 / 12  # Monthly rebalancing
    elif rebalance_frequency == 'Q':
        turnover = 1 / 4   # Quarterly rebalancing
    else:
        turnover = 0.1  # Default
    
    return turnover


def calculate_performance_summary(prices_df, returns_df, start_date="2020-01-01"):
    """
    Performance summary table: Returns across multiple periods.
    """
    end_date = prices_df.index[-1]
    
    periods = {
        '1M': 30,
        '3M': 90,
        'YTD': None,  # Year to date
        '1Y': 252,
        '3Y': 756,
        '5Y': 1260,
        'Inception': None
    }
    
    summary_data = []
    
    for period_name, days in periods.items():
        if period_name == 'YTD':
            period_start = datetime(end_date.year, 1, 1)
            if period_start < prices_df.index[0]:
                period_start = prices_df.index[0]
        elif period_name == 'Inception':
            period_start = pd.to_datetime(start_date)
        else:
            period_start = end_date - timedelta(days=days)
            if period_start < prices_df.index[0]:
                period_start = prices_df.index[0]
        
        period_start = prices_df.index[prices_df.index >= period_start][0]
        period_end = end_date
        
        period_prices = prices_df.loc[period_start:period_end]
        if len(period_prices) > 1:
            period_returns = (period_prices.iloc[-1] / period_prices.iloc[0] - 1) * 100
            summary_data.append({
                'Period': period_name,
                **{ticker: round(period_returns[ticker], 2) for ticker in period_returns.index}
            })
    
    summary_df = pd.DataFrame(summary_data)
    return summary_df


def calculate_drawdown(prices_df):
    """Calculate drawdown: decline from peak."""
    cumulative = (1 + prices_df.pct_change()).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max * 100
    return drawdown


def calculate_correlation_matrix(returns_df):
    """Calculate correlation matrix between holdings."""
    return returns_df.corr()


def calculate_portfolio_metrics(conn, ticker_list, start_date="2020-01-01", end_date=None):
    """
    Main function to calculate all portfolio metrics.
    Returns a dictionary with all calculated metrics.
    """
    print("Loading portfolio data from Azure...")
    prices_df = load_portfolio_data(conn, ticker_list, start_date, end_date)
    
    print("Calculating returns...")
    returns_df = calculate_returns(prices_df)
    
    print("Calculating portfolio metrics...")
    
    metrics = {
        'prices': prices_df,
        'returns': returns_df,
        'total_return': calculate_total_return(prices_df, prices_df.index[0], prices_df.index[-1]),
        'annualized_return': calculate_annualized_return(returns_df),
        'volatility': calculate_volatility(returns_df),
        'beta': calculate_beta(returns_df),
        'var_95': calculate_var(returns_df, 0.95),
        'sharpe_ratio': calculate_sharpe_ratio(returns_df),
        'alpha': calculate_alpha(returns_df, calculate_beta(returns_df)),
        'turnover_rate': calculate_turnover_rate(returns_df),
        'performance_summary': calculate_performance_summary(prices_df, returns_df, start_date),
        'drawdown': calculate_drawdown(prices_df),
        'correlation_matrix': calculate_correlation_matrix(returns_df)
    }
    
    return metrics


def generate_rolling_returns_chart(returns_df, window=30, save_path='figures/rolling_returns.png'):
    """Generate rolling returns chart."""
    rolling_returns = returns_df.rolling(window=window).mean() * 100
    
    plt.figure(figsize=(14, 8))
    for ticker in rolling_returns.columns:
        plt.plot(rolling_returns.index, rolling_returns[ticker], label=ticker, linewidth=2)
    
    plt.title(f'{window}-Day Rolling Returns', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Return (%)', fontsize=12)
    plt.legend(loc='best', ncol=2)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    import os
    os.makedirs('figures', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved rolling returns chart to {save_path}")


def generate_drawdown_chart(drawdown_df, save_path='figures/drawdown.png'):
    """Generate drawdown chart."""
    plt.figure(figsize=(14, 8))
    for ticker in drawdown_df.columns:
        plt.fill_between(drawdown_df.index, 0, drawdown_df[ticker], alpha=0.3, label=ticker)
        plt.plot(drawdown_df.index, drawdown_df[ticker], linewidth=1.5)
    
    plt.title('Portfolio Drawdown', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Drawdown (%)', fontsize=12)
    plt.legend(loc='best', ncol=2)
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    plt.tight_layout()
    
    import os
    os.makedirs('figures', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved drawdown chart to {save_path}")


def generate_correlation_matrix_heatmap(corr_matrix, save_path='figures/correlation_matrix.png'):
    """Generate correlation matrix heatmap."""
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8}, vmin=-1, vmax=1)
    plt.title('Stock Correlation Matrix', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    
    import os
    os.makedirs('figures', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved correlation matrix to {save_path}")


def generate_efficient_frontier(returns_df, save_path='figures/efficient_frontier.png'):
    """Generate efficient frontier plot: Risk-return tradeoff."""
    annualized_returns = calculate_annualized_return(returns_df)
    annualized_vol = calculate_volatility(returns_df)
    
    plt.figure(figsize=(12, 8))
    plt.scatter(annualized_vol, annualized_returns, s=200, alpha=0.6, edgecolors='black', linewidth=2)
    
    for ticker in returns_df.columns:
        plt.annotate(ticker, (annualized_vol[ticker], annualized_returns[ticker]),
                    fontsize=10, ha='center', va='bottom')
    
    plt.xlabel('Volatility (Annualized %)', fontsize=12)
    plt.ylabel('Return (Annualized %)', fontsize=12)
    plt.title('Efficient Frontier: Risk-Return Tradeoff', fontsize=16, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    import os
    os.makedirs('figures', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved efficient frontier to {save_path}")


def generate_all_figures(metrics, save_dir='figures'):
    """Generate all portfolio visualization figures."""
    import os
    os.makedirs(save_dir, exist_ok=True)
    
    print("Generating visualizations...")
    generate_rolling_returns_chart(metrics['returns'], save_path=f'{save_dir}/rolling_returns.png')
    generate_drawdown_chart(metrics['drawdown'], save_path=f'{save_dir}/drawdown.png')
    generate_correlation_matrix_heatmap(metrics['correlation_matrix'], save_path=f'{save_dir}/correlation_matrix.png')
    generate_efficient_frontier(metrics['returns'], save_path=f'{save_dir}/efficient_frontier.png')
    
    print("All figures generated successfully!")


if __name__ == "__main__":
    # Example usage
    ticker_list = ["AMZN", "AAPL", "META", "NVDA", "GOOGL", "MSFT", "TSLA", "NFLX", "ADBE", "ORCL"]
    
    conn = get_azure_connection()
    metrics = calculate_portfolio_metrics(conn, ticker_list, start_date="2020-01-01")
    conn.close()
    
    # Generate all figures
    generate_all_figures(metrics)
    
    # Print summary
    print("\n=== Portfolio Metrics Summary ===")
    print("\nAnnualized Returns:")
    print(metrics['annualized_return'])
    print("\nVolatility:")
    print(metrics['volatility'])
    print("\nSharpe Ratios:")
    print(metrics['sharpe_ratio'])
    print("\nPerformance Summary:")
    print(metrics['performance_summary'])

