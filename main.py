import os
import sys
import time
from datetime import datetime
import pandas as pd

from utils.config_loader import load_market_config
from data.data_handler import DataHandler
from strategy.trend_follower import DualMovingAverageVolumeStrategy
from risk.volatility_sizer import VolatilityBasedPositionSizer
from risk.risk_manager import RiskManager
from utils.metrics import calculate_performance_metrics
from utils.trade_analyzer import TradePerformanceAnalyzer
from utils.visualizer import BacktestVisualizer  
from utils.signal_visualizer import SignalVisualizer 

from optimize import run_parameter_optimization
from live_paper_trader import execute_simulated_live_session

def execute_historical_backtest_workflow(config_file: str):
    """Runs the complete production backtest engine."""
    print("\n" + "="*80)
    print(f"RUNNING HISTORICAL BACKTEST WORKFLOW FOR: {config_file.upper()}")
    print("="*80)
    
    # 1. LOAD CONFIGURATION
    market_setup = load_market_config(config_file)
    market_name = market_setup["market_name"]
    equity_tickers = market_setup["tickers"]
    benchmark_index = market_setup["index"]  
    
    # 2. DATA INGESTION
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_time_str = datetime.now().strftime("%H%M")
    session_folder_path = os.path.join("cache_data", f"{market_name}__{today_str}_{current_time_str}")
    benchmark_folder_path = os.path.join("cache_data", f"{market_name}_Benchmark__{today_str}_{current_time_str}")

    dh = DataHandler(
        tickers=equity_tickers,
        start_date="2020-01-01",
        end_date=today_str,                   
        session_dir=session_folder_path,      
        market_name=market_name,
        today_str=today_str
    )
    data_universe = dh.fetch_data()
    
    bh = DataHandler(
        tickers=[benchmark_index],
        start_date="2020-01-01",
        end_date=today_str,                   
        session_dir=benchmark_folder_path,    
        market_name=f"{market_name}_Benchmark",
        today_str=today_str
    )
    benchmark_universe = bh.fetch_data()
    
    full_data_universe = {**data_universe, **benchmark_universe}
    
    # 3. INITIALIZE STRATEGY (Fallback Baseline Defaults)
    strategy = DualMovingAverageVolumeStrategy(fast_period=20, slow_period=50, vol_period=20)
    
    # 4. GENERATE SIGNALS & PLOT INDIVIDUAL SIGNAL OVERLAYS
    signal_universe = {}
    print("\n[*] Generating strategy technical indicators and mapping signal overlays...")
    for ticker in equity_tickers:
        if ticker in data_universe and not data_universe[ticker].empty:
            df_signals = strategy.generate_signals(data_universe[ticker])
            if 'Position' not in df_signals.columns:
                if 'Signal' in df_signals.columns:
                    df_signals['Position'] = df_signals['Signal']
                else:
                    df_signals['Position'] = 0
            signal_universe[ticker] = df_signals
            
    sample_ticker = equity_tickers[0]
    if sample_ticker in signal_universe:
        SignalVisualizer.plot_asset_signals(
            df_signals=signal_universe[sample_ticker], 
            ticker=sample_ticker, 
            fast_p=20, 
            slow_p=50
        )
    
    # 5. RISK MANAGEMENT & POSITION SIZING
    sizer = VolatilityBasedPositionSizer(lookback=20)
    weight_dataframe = sizer.calculate_weights(data_universe, equity_tickers)
    risk_gate = RiskManager(max_daily_loss_pct=0.03, stop_loss_pct=0.05)
    
    print("[*] Calculating trade execution efficiencies across asset historical vectors...")
    trade_analysis = TradePerformanceAnalyzer.profile_trade_metrics(
        data_universe=data_universe, 
        active_tickers=equity_tickers, 
        strategy=strategy
    )
    
    portfolio_daily_returns = []
    for ticker in equity_tickers:
        if ticker not in signal_universe:
            continue
        df_sig = signal_universe[ticker]
        asset_pct_change = df_sig['Close'].pct_change()
        traded_returns = df_sig['Position'].shift(1) * asset_pct_change
        
        position_changes = df_sig['Position'].diff().abs().fillna(0)
        friction_penalty = position_changes * 0.0015
        adjusted_returns = traded_returns - friction_penalty
        
        if ticker in weight_dataframe.columns:
            ticker_weight = weight_dataframe[ticker].fillna(1.0 / len(equity_tickers))
        else:
            ticker_weight = 1.0 / len(equity_tickers)
            
        portfolio_daily_returns.append(adjusted_returns * ticker_weight)
        
    portfolio_net_returns = pd.concat(portfolio_daily_returns, axis=1).sum(axis=1)
    portfolio_net_returns = risk_gate.enforce_portfolio_limits(portfolio_net_returns)
    
    initial_capital = 100000.0
    portfolio_equity_curve = initial_capital * (1 + portfolio_net_returns).cumprod()
    portfolio_equity_curve.iloc[0] = initial_capital
    
    # 6. PERFORMANCE METRICS
    metrics_summary = calculate_performance_metrics(portfolio_equity_curve)
    
    # 7. EXPORT DISPLAY TERMINAL REPORT
    print("\n" + "="*20 + f" CAPSTONE BACKTEST: {market_name} " + "="*20)
    print(f"Allocation Model  : Volatility-Sized Matrix")
    print(f"Model Applied     : DualMovingAverageVolumeStrategy")
    print("-"*80)
    for k, v in metrics_summary.items():
        print(f"{k:<19} : {v}")
    print("-"*80)
    
    print(f"Total_Trades_Count : {trade_analysis.get('Total_Trades_Count', 0)}")
    print(f"Win_Rate           : {trade_analysis.get('Win_Rate_Percentage', '0.00%')}")
    print(f"Profit_Factor      : {trade_analysis.get('Profit_Factor_Ratio', '1.00')}")
    print(f"Gross_Profits_Sum  : {trade_analysis.get('Gross_Profits_Sum', 0.0):.4f}")
    print(f"Gross_Losses_Sum   : {trade_analysis.get('Gross_Losses_Sum', 0.0):.4f}")
    print("="*80)
    
    BacktestVisualizer.generate_plots(
        equity_curve=portfolio_equity_curve,
        data_universe=full_data_universe,
        benchmark_symbol=benchmark_index,
        market_name=market_name,
        strategy_name="DualMovingAverageVolumeStrategy",
        allocation_mode="Volatility_Sized"
    )

def display_master_launcher_menu():
    """Command-Line Menu System Control Center."""
    while True:
        print("\n" + "=" * 80)
        print("🏛️  MASTER SYSTEM LAUNCHER CONTROL CENTER: QUANTITATIVE TRADING ENGINE")
        print("=" * 80)
        print(" [1] Run Historical Backtest - US Equity Market (Standard Config)")
        print(" [2] Run Historical Backtest - India Equity Market (Standard Config)")
        print(" [3] Run Parameter Optimization Grid Sweep Matrix (US Markets)")
        print(" [4] Run Parameter Optimization Grid Sweep Matrix (India Markets)")  
        print(" [5] Initiate Simulated Live-Paper Trading Infrastructure Loop")
        print(" [6] Exit System Control Center")
        print("-" * 80)
        
        choice = input("👉 Enter target execution operational mode [1-6]: ").strip()
        
        if choice == "1":
            execute_historical_backtest_workflow("us_market.json") 
            input("\n[PAUSE] Press Enter to return to Master Menu...")
        elif choice == "2":
            execute_historical_backtest_workflow("india_market.json") 
            input("\n[PAUSE] Press Enter to return to Master Menu...")
        elif choice == '3':
            print("\n🚀 Launching US Parameter Optimization Matrix...")
            run_parameter_optimization("us_market.json")             
        elif choice == '4':  
            print("\n🚀 Launching India Parameter Optimization Matrix...")
            run_parameter_optimization("india_market.json")   
        elif choice == '5':
            print("\n📡 Simulated Live Deployment Sub-System Selection:")
            print("    [A] Deploy US Market Live Stream (Fast=25, Slow=240, Macro=150)")
            print("    [B] Deploy India Market Live Stream (Fast=25, Slow=240, Macro=150)")
            sub_choice = input("👉 Select target market infrastructure [A/B]: ").strip().upper()
            
            if sub_choice == 'A':
                execute_simulated_live_session("us_market.json", fast_period=25, slow_period=240, macro_period=150)
            elif sub_choice == 'B':
                execute_simulated_live_session("india_market.json", fast_period=25, slow_period=240, macro_period=150)
            else:
                print("❌ Invalid market destination selection.")
            input("\n[PAUSE] Press Enter to return to Master Menu...")
        elif choice == '6':
            print("Shutting down Trading Engine Control Center. Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid selection. Please enter a number between 1 and 6.\n")            
            time.sleep(1.5)

if __name__ == "__main__":
    display_master_launcher_menu()