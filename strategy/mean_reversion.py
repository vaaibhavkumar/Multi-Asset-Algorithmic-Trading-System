import talib

class RSIBollingerBandStrategy:
    def __init__(self, rsi_period=14, bb_period=20):
        self.rsi_period = rsi_period
        self.bb_period = bb_period

    def generate_signals(self, df):
        # Calculate Indicators
        df['RSI'] = talib.RSI(df['Close'], timeperiod=self.rsi_period)
        upper, mid, lower = talib.BBANDS(df['Close'], timeperiod=self.bb_period)
        df['BB_Upper'] = upper
        df['BB_Lower'] = lower
        
        # Logic: Buy if RSI < 30 and Price < Lower Band
        # Logic: Sell if RSI > 70 or Price > Upper Band
        df['Signal'] = 0
        df.loc[(df['RSI'] < 30) & (df['Close'] < df['BB_Lower']), 'Signal'] = 1
        df.loc[(df['RSI'] > 70) | (df['Close'] > df['BB_Upper']), 'Signal'] = -1
        
        return df