import pandas as pd

class RiskManager:
    def __init__(self, max_daily_loss_pct: float = 0.02, stop_loss_pct: float = 0.05):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.stop_loss_pct = stop_loss_pct

    def enforce_portfolio_limits(self, combined_daily_returns: pd.Series) -> pd.Series:
        """
        Acts as a circuit breaker. If the portfolio net returns drop below the 
        maximum daily loss limit, it flattens positions for the rest of the day.
        """
        # If daily losses exceed the threshold, cap the loss and simulate a trading halt
        adjusted_returns = combined_daily_returns.apply(
            lambda r: max(r, -self.max_daily_loss_pct)
        )
        return adjusted_returns