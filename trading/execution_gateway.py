import pandas as pd
import numpy as np
from datetime import datetime

class PaperExecutionGateway:
    """
    Institutional Mock Broker API & Paper Trading Engine.
    Simulates real-time order management, market-fill latencies, account balances,
    and micro-structural transaction slippage penalties.
    """
    def __init__(self, initial_cash: float = 100000.0, default_slippage_pct: float = 0.0005):
        self.account_balance = initial_cash
        self.portfolio_positions = {}  # Format: {TICKER: SHARES_HELD}
        self.slippage_rate = default_slippage_pct
        self.order_ledger = []
        
    def query_account_status(self) -> dict:
        """Returns verified real-time account balances and risk exposure."""
        return {
            "Account_Balance_Cash": f"${self.account_balance:,.2f}",
            "Active_Positions": self.portfolio_positions,
            "Total_Orders_Logged": len(self.order_ledger)
        }

    def transmit_order(self, ticker: str, target_signal: int, current_market_price: float, timestamp: datetime) -> dict:
        """
        Simulates live execution gateway entry.
        Applies a mandatory microstructural slippage penalty to mirror real-order fills.
        """
        current_shares = self.portfolio_positions.get(ticker, 0)
        
        if target_signal == 1 and current_shares == 0:
            # Action: Simulate BUY order with execution slippage markup
            executed_fill_price = current_market_price * (1.0 + self.slippage_rate)
            allocated_cash = self.account_balance * 0.05  # Deploy a flat 5% cash slice per position
            shares_to_buy = int(allocated_cash // executed_fill_price)
            
            if shares_to_buy > 0:
                cost = shares_to_buy * executed_fill_price
                self.account_balance -= cost
                self.portfolio_positions[ticker] = shares_to_buy
                order_status = "FILLED_BUY"
            else:
                order_status = "REJECTED_INSUFFICIENT_FUNDS"
                executed_fill_price = 0.0
                shares_to_buy = 0
                
        elif target_signal == 0 and current_shares > 0:
            # Action: Simulate LIQUIDATE/SELL order with execution slippage markdown
            executed_fill_price = current_market_price * (1.0 - self.slippage_rate)
            revenue = current_shares * executed_fill_price
            self.account_balance += revenue
            self.portfolio_positions[ticker] = 0
            shares_to_buy = current_shares  
            order_status = "FILLED_LIQUIDATION"
            
        else:
            order_status = "HOLD_NO_ACTION"
            executed_fill_price = current_market_price
            shares_to_buy = 0

        execution_log = {
            "Timestamp": timestamp,
            "Ticker": ticker,
            "Action_Status": order_status,
            "Executed_Price": executed_fill_price,
            "Volume_Shares": shares_to_buy,
            "Remaining_Cash": self.account_balance
        }
        
        if order_status in ["FILLED_BUY", "FILLED_LIQUIDATION"]:
            self.order_ledger.append(execution_log)
            
        return execution_log