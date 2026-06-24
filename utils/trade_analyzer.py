import pandas as pd
import numpy as np

class TradePerformanceAnalyzer:
    """
    Module 310: Institutional Trade Performance Analytics Engine.
    Analyzes asset signal history to parse win rates, trade frequency,
    and structural profit metrics.
    """
    @staticmethod
    def profile_trade_metrics(data_universe: dict, active_tickers: list, strategy) -> dict:
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        gross_profits = 0.0
        gross_losses = 0.0
        
        for ticker in active_tickers:
            if ticker not in data_universe:
                continue
                
            df = data_universe[ticker].copy()
            signals = strategy.generate_signals(df)
            
            # Identify exact execution points via position states
            positions = signals['Position'].fillna(0.0).values
            close_pct = df['Close'].pct_change().fillna(0.0).values
            
            in_position = False
            trade_return = 1.0
            
            # State machine tracker to record complete entry-to-exit horizons
            for i in range(1, len(positions)):
                if in_position:
                    trade_return *= (1.0 + close_pct[i])
                    
                # Entry Transition: Moved from cash neutral (0) to long position (1)
                if positions[i] > 0 and positions[i-1] == 0:
                    in_position = True
                    trade_return = 1.0
                    
                # Exit Transition: Moved from long position (1) back to cash neutral (0)
                elif positions[i] == 0 and positions[i-1] > 0 and in_position:
                    total_trades += 1
                    final_return = trade_return - 1.0
                    
                    if final_return > 0:
                        winning_trades += 1
                        gross_profits += final_return
                    else:
                        losing_trades += 1
                        gross_losses += abs(final_return)
                    in_position = False
                    
        # Calculate final aggregated portfolio statistics
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else (gross_profits if gross_profits > 0 else 1.0)
        
        return {
            "Total_Trades_Count": int(total_trades),
            "Win_Rate_Percentage": f"{win_rate:.2f}%",
            "Profit_Factor_Ratio": f"{profit_factor:.2f}",
            "Gross_Profits_Sum": float(gross_profits),
            "Gross_Losses_Sum": float(gross_losses)
        }