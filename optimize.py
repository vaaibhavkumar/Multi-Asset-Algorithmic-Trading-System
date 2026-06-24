import os
import pandas as pd
import numpy as np
from datetime import datetime
from utils.config_loader import load_market_config
from data.data_handler import DataHandler
from strategy.trend_follower import DualMovingAverageVolumeStrategy
from utils.metrics import calculate_performance_metrics

def run_parameter_optimization(config_file: str, split_ratio: float = 0.80):
    """
    Run a 3D grid search over Fast EMA, Slow EMA, and Macro SMA parameter combinations 
    on In-Sample (Train) data, and validate the optimal matrix out-of-sample.
    """
    print("=" * 80)
    print("🧪 INITIALIZING 3D STRATEGY PARAMETER OPTIMIZATION (FAST vs SLOW vs MACRO SMA)")
    print("=" * 80)
    
    # 1. Load data parameters
    market_setup = load_market_config(config_file)
    market_name = market_setup["market_name"]
    equity_tickers = market_setup["tickers"][:]
    
    print(f"[VERIFICATION CORE] Running universe size: {len(equity_tickers)} assets.")

    today_str = datetime.now().strftime("%Y%m%d")          
    yf_today_str = datetime.now().strftime("%Y-%m-%d")    
    current_time_str = datetime.now().strftime("%H%M")
    
    session_folder_path = os.path.join("cache_data", f"OptRun_{market_name}_{today_str}_{current_time_str}")

    dh = DataHandler(
        tickers=equity_tickers,
        start_date="2021-01-01",
        end_date=yf_today_str,               
        session_dir=session_folder_path,     
        market_name=market_name,
        today_str=today_str
    )
    data_universe = dh.fetch_data()
    
    for ticker in list(data_universe.keys()):
        df = data_universe[ticker]
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.sort_index()
        data_universe[ticker] = df

    # Chronological Train-Test Split
    train_universe = {}
    test_universe = {}
    
    sample_ticker = equity_tickers[0]
    if sample_ticker in data_universe and not data_universe[sample_ticker].empty:
        total_days = len(data_universe[sample_ticker])
        split_idx = int(total_days * split_ratio)
        split_date = data_universe[sample_ticker].index[split_idx]
        print(f"[SPLIT INFO] Splitting chronologically at: {split_date.strftime('%Y-%m-%d')}")
    else:
        raise ValueError("Data universe is empty or invalid.")

    for ticker in equity_tickers:
        if ticker in data_universe and not data_universe[ticker].empty:
            df = data_universe[ticker]
            train_universe[ticker] = df.loc[df.index < split_date]
            test_universe[ticker] = df.loc[df.index >= split_date]

    # 2. Define our 3D parameter grid sweep bounds
    fast_windows = list(range(20, 55, 5))
    slow_windows = list(range(100, 250, 10))
    macro_windows = list(range(150, 251, 15))  # NEW Iterations: Multiples of 15 between 150 and 250
    
    bps_penalty = 0.0010 
    optimization_ledger = []
    
    total_combinations = len(fast_windows) * len(slow_windows) * len(macro_windows)
    print(f"\n🔄 Sweeping 3D parameter matrix across {total_combinations} combinations on IN-SAMPLE data...")
    print("-" * 80)

    # 3. Triple-loop parameter grid optimization sweep
    for fast in fast_windows:
        for slow in slow_windows:
            if fast >= slow:
                continue
            for macro in macro_windows: # Third loop dimension
                
                temp_returns = pd.DataFrame()
                # Pass the loop's current macro variable straight into the strategy instance
                opt_strategy = DualMovingAverageVolumeStrategy(fast_period=fast, slow_period=slow, vol_period=20, macro_period=macro)
                
                for ticker in equity_tickers:
                    if ticker not in train_universe or train_universe[ticker].empty:
                        continue
                        
                    df_asset = train_universe[ticker].copy()
                    df_signals = opt_strategy.generate_signals(df_asset)
                    
                    asset_pct = df_signals['Close'].pct_change()
                    raw_returns = df_signals['Position'] * asset_pct
                    
                    position_changes = df_signals['Position'].diff().abs().fillna(0.0)
                    friction_drag = position_changes * bps_penalty
                    
                    temp_returns[ticker] = raw_returns - friction_drag
                
                if temp_returns.empty:
                    continue
                    
                # Safe crop based on the largest lookback window to prevent initialization skew
                max_warmup = max(slow, macro)
                temp_returns = temp_returns.fillna(0.0).iloc[max_warmup:]
                portfolio_net_series = temp_returns.mean(axis=1)
                
                initial_cap = 100000.0
                equity_curve = initial_cap * (1 + portfolio_net_series).cumprod()
                if len(equity_curve) == 0:
                    continue
                equity_curve.iloc[0] = initial_cap
                
                run_metrics = calculate_performance_metrics(equity_curve)
                
                try:
                    sharpe_val = float(str(run_metrics.get("Sharpe Ratio", "-99.9")).replace('%','').strip())
                    total_ret_val = float(str(run_metrics.get("Total Return", "0")).replace('%','').strip())
                except ValueError:
                    sharpe_val = -99.9
                    total_ret_val = 0.0

                daily_returns = portfolio_net_series.fillna(0.0)
                cagr_val = (1.0 + (total_ret_val / 100.0)) ** (252.0 / len(equity_curve)) - 1.0 if total_ret_val > -100 else 0.0
                downside_returns = daily_returns[daily_returns < 0]
                downside_vol = (downside_returns.std() * (252.0 ** 0.5)) if len(downside_returns) > 0 else 0.0
                sortino_val = (cagr_val / downside_vol) if downside_vol > 0 else 0.0

                print(f"📍 Tested Train: Fast_EMA={fast:<2} | Slow_EMA={slow:<3} | Macro_SMA={macro:<3} -> IS Sharpe: {sharpe_val:.2f} | IS Sortino: {sortino_val:.2f}")
                
                optimization_ledger.append({
                    "Fast_Window": fast,
                    "Slow_Window": slow,
                    "Macro_Window": macro, # Saved to ledger
                    "Total_Return_Pct": total_ret_val,
                    "CAGR": cagr_val * 100.0,
                    "Sharpe_Ratio": sharpe_val,
                    "Sortino_Ratio": sortino_val,
                    "Max_Drawdown_Pct": run_metrics.get("Max Drawdown", "0%")
                })
            
    # 4. Extract optimal parameter layout based on In-Sample Sortino Ratio
    df_results = pd.DataFrame(optimization_ledger)
    best_config = df_results.sort_values(by="Sortino_Ratio", ascending=False).iloc[0]
    
    best_fast = int(best_config['Fast_Window'])
    best_slow = int(best_config['Slow_Window'])
    best_macro = int(best_config['Macro_Window']) # Extracted winning macro lookback

    print("-" * 80)
    print("3D PARAMETER MATRIX SWEEP COMPLETE — OPTIMAL CONFIGURATION IDENTIFIED")
    print("-" * 80)
    print(f" Optimal Fast Moving Average Lookback Window : {best_fast} Days")
    print(f" Optimal Slow Moving Average Lookback Window : {best_slow} Days")
    print(f" Optimal Macro Moving Average Filter Window  : {best_macro} Days") # Prints winner
    print("-" * 80)
    
    # 5. OUT-OF-SAMPLE (TEST) VALIDATION BLOCK USING ALL THREE WINNING PARAMETERS
    print("🔬 RUNNING OUT-OF-SAMPLE (TEST DATA) VALIDATION ON WINNING PARAMETERS...")
    
    test_returns = pd.DataFrame()
    # Instantiate using the calculated best_macro parameter found in training
    final_strategy = DualMovingAverageVolumeStrategy(fast_period=best_fast, slow_period=best_slow, vol_period=20, macro_period=best_macro)
    
    for ticker in equity_tickers:
        if ticker not in test_universe or test_universe[ticker].empty:
            continue
            
        df_asset_test = test_universe[ticker].copy()
        df_signals_test = final_strategy.generate_signals(df_asset_test)
        
        asset_pct_test = df_signals_test['Close'].pct_change()
        raw_returns_test = df_signals_test['Position'] * asset_pct_test
        
        position_changes_test = df_signals_test['Position'].diff().abs().fillna(0.0)
        friction_drag_test = position_changes_test * bps_penalty
        
        test_returns[ticker] = raw_returns_test - friction_drag_test
        
    if not test_returns.empty:
        test_returns = test_returns.fillna(0.0)
        test_portfolio_series = test_returns.mean(axis=1)
        
        test_equity_curve = initial_cap * (1 + test_portfolio_series).cumprod()
        test_equity_curve.iloc[0] = initial_cap
        
        test_metrics = calculate_performance_metrics(test_equity_curve)
        
        try:
            test_sharpe = float(str(test_metrics.get("Sharpe Ratio", "-99.9")).replace('%','').strip())
            test_return = float(str(test_metrics.get("Total Return", "0")).replace('%','').strip())
        except ValueError:
            test_sharpe = -99.9
            test_return = 0.0
            
        test_cagr = (1.0 + (test_return / 100.0)) ** (252.0 / len(test_equity_curve)) - 1.0 if test_return > -100 else 0.0
        test_downside = test_portfolio_series[test_portfolio_series < 0]
        test_downside_vol = (test_downside.std() * (252.0 ** 0.5)) if len(test_downside) > 0 else 0.0
        test_sortino = (test_cagr / test_downside_vol) if test_downside_vol > 0 else 0.0
        test_cagr_pct = test_cagr * 100.0
        
        print("\n" + "=" * 80)
        print("📊 STRATEGY PERFORMANCE VARIANCE REPORT: IN-SAMPLE VS. OUT-OF-SAMPLE")
        print("=" * 80)
        print(f"Selected Configuration: Fast_EMA={best_fast} | Slow_EMA={best_slow} | Macro_SMA={best_macro}")
        print("-" * 80)
        print(f" Metric                  | In-Sample (Train)      | Out-of-Sample (Test)")
        print(f"-------------------------+------------------------+-----------------------")
        print(f" Total Return            | {best_config['Total_Return_Pct']:>20.2f}% | {test_return:>19.2f}%")
        print(f" Annualized Return (CAGR)| {best_config['CAGR']:>20.2f}% | {test_cagr_pct:>19.2f}%")
        print(f" Sharpe Ratio            | {best_config['Sharpe_Ratio']:>20.2f} | {test_sharpe:>19.2f}")
        print(f" Sortino Ratio           | {best_config['Sortino_Ratio']:>20.2f} | {test_sortino:>19.2f}")
        print(f" Max Drawdown            | {str(best_config['Max_Drawdown_Pct']):>21} | {str(test_metrics.get('Max Drawdown', '0%')):>20}")
        print("=" * 80)
        
        sharpe_delta = test_sharpe - best_config['Sharpe_Ratio']
        if sharpe_delta < -1.0:
            print(f"⚠️ WARNING: Significant performance decay detected (Sharpe drop: {sharpe_delta:.2f}). Model might be overfitted.")
        elif sharpe_delta > 0:
            print(f"🚀 OUTPERFORMANCE: Strategy performed better on Test data by a Sharpe delta of +{sharpe_delta:.2f}!")
        else:
            print(f"✅ STABLE: Out-of-sample behavior is inline with training data expectations.")
        print("=" * 80)
        
    else:
        print("   [WARNING] Test returns matrix resulted empty.")
        
    output_dir = "backtest_reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")    
    output_path = os.path.join(output_dir, f"Parameter_Optimization_Matrix_{timestamp_suffix}.csv")
    df_results.to_csv(output_path, index=False)
    print(f"\n[SUCCESS] Comprehensive sweep metrics logged permanently to: {output_path}")

if __name__ == "__main__":
    run_parameter_optimization("india_market.json")