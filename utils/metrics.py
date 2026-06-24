import pandas as pd
import numpy as np

def calculate_benchmark_return(benchmark_df: pd.DataFrame) -> str:
    """Calculates the absolute total baseline buy-and-hold index returns."""
    try:
        # Handle potential Multi-Index columns safely
        if isinstance(benchmark_df.columns, pd.MultiIndex):
            benchmark_df.columns = benchmark_df.columns.get_level_values(0)
            
        close_prices = pd.to_numeric(benchmark_df['Close'], errors='coerce').dropna()
        if len(close_prices) < 2:
            return "N/A"
            
        initial_price = close_prices.iloc[0]
        final_price = close_prices.iloc[-1]
        
        bench_return = ((final_price / initial_price) - 1) * 100
        return f"{bench_return:.2f}%"
    except Exception:
        return "N/A"

def calculate_performance_metrics(equity_curve: pd.Series, risk_free_rate: float = 0.05) -> dict:
    """
    Module 310: Complete Institutional Portfolio Analytics Suite.
    Calculates CAGR, Volatility, Sharpe, Max Drawdown, and the required Sortino Ratio.
    """
    returns = equity_curve.pct_change().dropna()
    
    # 1. Total Return
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
    
    # 2. CAGR (Assuming standard 252 trading days per year over data window)
    total_days = len(equity_curve)
    years = total_days / 252.0
    cagr = (equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1 / years) - 1 if years > 0 else 0.0
    
    # 3. Annual Volatility
    annual_vol = returns.std() * np.sqrt(252)
    
    # 4. Sharpe Ratio
    sharpe = (cagr - risk_free_rate) / annual_vol if annual_vol > 0 else 0.0
    
    # 5. Max Drawdown Calculation
    rolling_max = equity_curve.cummax()
    drawdowns = (equity_curve - rolling_max) / rolling_max
    max_dd = drawdowns.min()
    
    # 6. FIX: Sortino Ratio (Targeting Downside-Only Volatility)
    downside_returns = returns[returns < 0]
    downside_vol = downside_returns.std() * np.sqrt(252)
    sortino = (cagr - risk_free_rate) / downside_vol if downside_vol > 0 else 0.0
    
    # 7. Calmar Ratio
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0.0
    
    return {
        "Total Return": f"{total_return * 100:.2f}%",
        "CAGR": f"{cagr * 100:.2f}%",
        "Annual Volatility": f"{annual_vol * 100:.2f}%",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Sortino Ratio": f"{sortino:.2f}",  # Newly added metric
        "Max Drawdown": f"{max_dd * 100:.2f}%",
        "Calmar Ratio": f"{calmar:.2f}"
    }