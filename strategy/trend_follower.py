import numpy as np
import pandas as pd
class DualMovingAverageVolumeStrategy:
    def __init__(self, fast_period: int, slow_period: int, vol_period: int = 20, macro_period: int = 200): # 💡 Added macro_period
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.vol_period = vol_period
        self.macro_period = macro_period  # Store it dynamically

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # 1. Core EMAs
        df['Fast_EMA'] = df['Close'].ewm(span=self.fast_period, adjust=False).mean()
        df['Slow_EMA'] = df['Close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # 2. Dynamic Macro Regime Filter 
        df['Macro_SMA'] = df['Close'].rolling(window=self.macro_period, min_periods=1).mean() # dynamic
        
        # 3. Base Signals
        df['Position'] = 0
        df.loc[df['Fast_EMA'] > df['Slow_EMA'], 'Position'] = 1
        df.loc[df['Fast_EMA'] < df['Slow_EMA'], 'Position'] = -1
        
        # 4. Macro Filter Constraint
        df.loc[(df['Close'] < df['Macro_SMA']) & (df['Position'] == 1), 'Position'] = 0
        
        return df