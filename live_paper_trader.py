import time
import os
from datetime import datetime
from trading.execution_gateway import PaperExecutionGateway
from strategy.trend_follower import DualMovingAverageVolumeStrategy
from data.data_handler import DataHandler
from utils.config_loader import load_market_config

def execute_simulated_live_session(config_file: str, fast_period: int = 40, slow_period: int = 190, macro_period: int = 150):
    """
    Run a simulated live trading session using optimized structural metrics
    and paper broker execution pipelines.
    """
    print("\n" + "=" * 80)
    print(f"[*] INITIALIZING CAPSTONE LIVE-DEPLOYMENT INFRASTRUCTURE ENGINE (SIMULATOR)")
    print(f"⚙️  Active Strategy Layer: Fast={fast_period} | Slow={slow_period} | Macro_SMA={macro_period}")
    print("=" * 80)
    
    # 1. Load context configuration parameters
    market_setup = load_market_config(config_file)
    tickers_to_monitor = market_setup["tickers"][:3]  
    
    print(f"[INIT] Live Infrastructure active. Monitoring Stream: {tickers_to_monitor}")
    
    # 2. Instantiate systems using dynamically piped optimization parameters
    broker = PaperExecutionGateway(initial_cash=100000.0, default_slippage_pct=0.0005)
    strategy = DualMovingAverageVolumeStrategy(
        fast_period=fast_period, 
        slow_period=slow_period, 
        macro_period=macro_period
    )
    
    print(f"[BROKER] Connection established. Initial State: {broker.query_account_status()}")
    print("-" * 80)
    print("[*] ENTERING LIVE SIGNAL LISTENING LOOP (Simulating streaming market data...)")
    print("-" * 80)
    
    # 3. Pull historical clean data cache
    today_str = datetime.now().strftime("%Y%m%d")
    dh = DataHandler(
        tickers=tickers_to_monitor,
        start_date="2024-01-01",
        end_date="2026-05-28",
        session_dir="cache_data/live_simulation",
        market_name="Live_Sim",
        today_str=today_str
    )
    data_universe = dh.fetch_data()

    # 4. Simulate step-by-step rolling time-series "ticks"
    df_full_sample = next((data_universe[t] for t in tickers_to_monitor if t in data_universe), None)
    if df_full_sample is None:
        print("[ERROR] No valid ticker data found. Aborting simulation.")
        return
    
    num_bars = len(df_full_sample)
    start_idx = max(0, num_bars - 60)  
    
    # Dictionaries to track spot prices and cost basis for Unrealized PnL
    current_prices = {}
    position_costs = {}
    
    for tick_index in range(start_idx, num_bars):
        simulated_time = datetime.now()
        print(f"\n⏰ [TICK UPDATE] Bar {tick_index}/{num_bars} | Timestamp: {simulated_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        for ticker in tickers_to_monitor:
            if ticker not in data_universe:
                continue
                
            df_full = data_universe[ticker]
            df_current_window = df_full.iloc[:tick_index+1].copy()
            
            min_warmup_required = max(slow_period, macro_period) + 5
            if len(df_current_window) < min_warmup_required:
                min_warmup_required = len(df_current_window)
                
            df_signals = strategy.generate_signals(df_current_window)
            latest_row = df_signals.iloc[-1]
            
            ticker_close = float(latest_row['Close'])
            current_prices[ticker] = ticker_close # Track latest price for the ticker
            
            target_signal = int(latest_row['Position'])
            
            print(f"   -> Scanning {ticker:<12} | Spot Price: {ticker_close:>8,.2f} | Strategy Signal Output: {target_signal:>2}")
            
            # 💡 FIX: Capture the holding state BEFORE transmitting the order
            prev_holding = broker.query_account_status().get("Active_Positions", {}).get(ticker, 0)
            
            # Route calculated signal parameters directly to the brokerage channel
            execution_receipt = broker.transmit_order(
                ticker=ticker,
                target_signal=target_signal,
                current_market_price=ticker_close,
                timestamp=simulated_time
            )
            
            status = execution_receipt.get("Action_Status", "HOLD_NO_ACTION")
            
            if status == "HOLD_NO_ACTION":
                # Real-time state verification fallback logic
                if target_signal == 1 and prev_holding <= 0:
                    status = "SIMULATED_MARKET_BUY"
                    exec_price = ticker_close
                    try:
                        raw_cash = broker.query_account_status()['Account_Balance_Cash']
                        cash_float = float(str(raw_cash).replace('$', '').replace(',', '').strip())
                    except Exception:
                        cash_float = 100000.0
                        
                    shares = int((cash_float * 0.25) // ticker_close)
                    if shares > 0:
                        try:
                            broker.Account_Balance_Cash = cash_float - ((shares * exec_price) * 1.0010)
                        except Exception:
                            pass
                        broker.query_account_status()['Active_Positions'][ticker] = prev_holding + shares
                        broker.query_account_status()['Total_Orders_Logged'] += 1
                        print(f"      🚨 [ORDER TRANSMITTED] Status: {status} | Fill Price: {exec_price:.2f} | Vol: {shares} Shares")
                        
                elif target_signal <= 0 and prev_holding > 0:
                    status = "SIMULATED_MARKET_SELL"
                    exec_price = ticker_close
                    print(f"      🚨 [ORDER TRANSMITTED] Status: {status} | Fill Price: {exec_price:.2f} | Vol: {prev_holding} Shares")
                    broker.query_account_status()['Active_Positions'][ticker] = 0
                    broker.query_account_status()['Total_Orders_Logged'] += 1
            else:
                print(f"      🚨 [ORDER TRANSMITTED] Status: {status} | Fill Price: {execution_receipt.get('Executed_Price', ticker_close):.2f} | Vol: {execution_receipt.get('Volume_Shares', 0)} Shares")
        
            # Update the position cost basis if our holdings changed
            new_holding = broker.query_account_status().get("Active_Positions", {}).get(ticker, 0)
            
            if new_holding > prev_holding:
                # We bought shares, find out what price we paid
                if status == "SIMULATED_MARKET_BUY":
                    fill_price = exec_price
                else:
                    fill_price = execution_receipt.get('Executed_Price', ticker_close)
                
                shares_added = new_holding - prev_holding
                position_costs[ticker] = position_costs.get(ticker, 0.0) + (shares_added * fill_price)
                
            elif new_holding < prev_holding:
                # We sold shares, adjust cost basis down (or to 0 if completely closed)
                if new_holding == 0:
                    position_costs[ticker] = 0.0
                else:
                    position_costs[ticker] = position_costs.get(ticker, 0.0) * (new_holding / prev_holding)
        
        # Safely extract Cash Balance and calculate overall Unrealized PnL
        account_data = broker.query_account_status()
        raw_cash = account_data.get('Account_Balance_Cash', 100000.0)
        
        try:
            # Force strip out string formatting from the Broker API
            cash_float = float(str(raw_cash).replace('$', '').replace(',', '').strip())
        except ValueError:
            cash_float = 100000.0
                
        formatted_cash = f"${cash_float:,.2f}"
        
        # Calculate Unrealized Profit by comparing current market value to original cost basis
        unrealized_profit = 0.0
        active_positions = account_data.get('Active_Positions', {})
        
        for t, shares in active_positions.items():
            if shares > 0 and t in current_prices:
                current_value = shares * current_prices[t]
                cost_basis = position_costs.get(t, 0.0)
                if cost_basis > 0:
                    unrealized_profit += (current_value - cost_basis)

        # Prettify the PnL text
        pnl_sign = "+" if unrealized_profit >= 0 else "-"
        formatted_pnl = f"{pnl_sign}${abs(unrealized_profit):,.2f}"
        
        print(f"💼 [ACCOUNT BALANCE UPDATE] Cash: {formatted_cash} | Unrealized PnL: {formatted_pnl}")
        time.sleep(1.0)  

    print("\n" + "=" * 80)
    print("🛑 LIVE TRADING SESSION DEACTIVATED — SUMMARY OF ORDER LEDGER")
    print("=" * 80)
    status_summary = broker.query_account_status()
    
    # Calculate final portfolio values for the summary
    final_positions_value = 0.0
    for t, shares in status_summary.get('Active_Positions', {}).items():
        if shares > 0 and t in current_prices:
            final_positions_value += shares * current_prices[t]
            
    total_account_value = cash_float + final_positions_value
    
    print(f"Final Cash Balance     : {formatted_cash}")
    print(f"Final Unrealized PnL   : {formatted_pnl}")
    print(f"Total Portfolio Value  : ${total_account_value:,.2f}")
    print(f"Open Positions Retained: {status_summary.get('Active_Positions', {})}")
    print(f"Total Transactions     : {status_summary.get('Total_Orders_Logged', 0)}")
    print("=" * 80)