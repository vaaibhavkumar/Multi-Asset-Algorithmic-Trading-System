import pandas as pd
import talib as ta

class DualMovingAverageVolumeStrategy:
    def __init__(self, fast_period: int = 50, slow_period: int = 200, volume_period: int = 20):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.volume_period = volume_period

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generates buy (1), sell (-1), and hold (0) signals."""
        df = df.copy()
        
        close_prices = df['Close'].to_numpy().flatten()
        volume_data = df['Volume'].to_numpy().flatten()

        df['Fast_MA'] = ta.SMA(close_prices, timeperiod=self.fast_period)
        df['Slow_MA'] = ta.SMA(close_prices, timeperiod=self.slow_period)
        df['Volume_MA'] = ta.SMA(volume_data, timeperiod=self.volume_period)

        df['Signal'] = 0

        ma_crossover_up = df['Fast_MA'] > df['Slow_MA']
        volume_confirmation = df['Volume'] > df['Volume_MA']

        df.loc[ma_crossover_up & volume_confirmation, 'Signal'] = 1
        
        # CRITICAL FIX: Explicitly assign compiled signal paths into the Position column
        df['Position'] = df['Signal'].fillna(0.0)
        
        return df