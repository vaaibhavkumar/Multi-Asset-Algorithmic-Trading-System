import pandas as pd
import numpy as np
import talib as ta

class RSIBollingerMeanReversionStrategy:
    def __init__(self, bb_period: int = 20, bb_std: float = 2.0, rsi_period: int = 14, 
                 rsi_oversold: float = 30.0, rsi_overbought: float = 70.0):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates mean-reversion signals based on Bollinger Bands and RSI extremes.
        """
        df = df.copy()
        
        # Extract C-arrays for TA-Lib processing
        close_prices = df['Close'].to_numpy().flatten()

        # Calculate Indicators using TA-Lib
        df['Upper_BB'], df['Middle_BB'], df['Lower_BB'] = ta.BBANDS(
            close_prices, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0
        )
        df['RSI'] = ta.RSI(close_prices, timeperiod=self.rsi_period)

        # Drop rows where indicators cannot be calculated to prevent look-ahead or data gaps
        df = df.dropna(subset=['Upper_BB', 'RSI']).copy()

        # Initialize Signal column: 1 = Long, -1 = Short, 0 = Flat
        df['Signal'] = 0

        # We keep track of active positions to manage the mid-band exit rule
        current_position = 0
        signals = []

        for i in range(len(df)):
            price = df['Close'].iloc[i]
            rsi = df['RSI'].iloc[i]
            upper_bb = df['Upper_BB'].iloc[i]
            middle_bb = df['Middle_BB'].iloc[i]
            lower_bb = df['Lower_BB'].iloc[i]

            if current_position == 0:
                # ENTRY CONDITIONS
                if price < lower_bb and rsi < self.rsi_oversold:
                    current_position = 1  # Enter Long
                elif price > upper_bb and rsi > self.rsi_overbought:
                    current_position = -1  # Enter Short
            else:
                # EXIT CONDITIONS (Reverted to the mean / Middle Band)
                if current_position == 1 and price >= middle_bb:
                    current_position = 0  # Exit Long
                elif current_position == -1 and price <= middle_bb:
                    current_position = 0  # Exit Short

            signals.append(current_position)

        df['Signal'] = signals
        
        # Shift positions by 1 day to prevent look-ahead bias (trading occurs on the next open/close)
        df['Position'] = df['Signal'].shift(1).fillna(0)
        
        return df