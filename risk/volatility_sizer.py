import pandas as pd
import numpy as np

class VolatilityBasedPositionSizer:
    """
    Module 308: Advanced Position Sizing Engine.
    Calculates rolling historical volatility (Standard Deviation) for every asset 
    and dynamically assigns higher capital weights to steadier trends.
    """
    def __init__(self, lookback: int = 20):
        self.lookback = lookback

    def calculate_weights(self, data_universe: dict, active_tickers: list) -> pd.DataFrame:
        """
        Generates an Inverse-Volatility weighting matrix.
        Total active portfolio weight allocations across rows will sum to 1.0 (100%).
        """
        vol_matrix = pd.DataFrame()
        
        # 1. Compile individual daily return volatility tracks
        for ticker in active_tickers:
            if ticker in data_universe:
                close_prices = pd.to_numeric(data_universe[ticker]['Close'], errors='coerce')
                daily_returns = close_prices.pct_change()
                vol_matrix[ticker] = daily_returns.rolling(window=self.lookback).std()
                
        # Fill initial lookback window gaps cleanly
        vol_matrix = vol_matrix.bfill().fillna(0.001)
        
        # 2. Compute Inverse Volatility (1 / Vol)
        inverse_vol = 1.0 / vol_matrix
        inverse_vol = inverse_vol.replace([np.inf, -np.inf], 0.0)
        
        # 3. Normalize rows to force total allocation sum to exactly 1.0
        row_sums = inverse_vol.sum(axis=1)
        weight_matrix = inverse_vol.div(row_sums, axis=0).fillna(0.0)
        
        return weight_matrix