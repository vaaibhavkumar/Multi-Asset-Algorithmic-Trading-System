import pandas as pd
import yfinance as yf
import os
import glob

class DataHandler:
    def __init__(self, tickers: list, start_date: str, end_date: str, session_dir: str, market_name: str, today_str: str):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.session_dir = session_dir
        self.market_name = market_name
        self.today_str = today_str
        self.final_dir = self.session_dir  

        # Check if ANY cache folder exists for this market from TODAY
        search_pattern = os.path.join("cache_data", f"{self.market_name}__{self.today_str}_*")
        existing_today_dirs = glob.glob(search_pattern)

        if existing_today_dirs:
            self.final_dir = existing_today_dirs[0]
            print(f"[CACHE MATCH] Found existing data folder from today: {self.final_dir}. Skipping fresh downloads.")
        else:
            if not os.path.exists(self.final_dir):
                os.makedirs(self.final_dir)
            print(f"[NEW SESSION] Generating fresh workspace location: {self.final_dir}")

    def fetch_data(self) -> dict:
        """Loads historical data from local daily cache or downloads if missing."""
        data_store = {}
        for ticker in self.tickers:
            safe_ticker_name = ticker.replace("^", "INDEX_")
            file_path = os.path.join(self.final_dir, f"{safe_ticker_name}.csv")
            
            if os.path.exists(file_path):
                # Instantly read from drive if it exists
                df = pd.read_csv(file_path, index_col=0)
                df.index = pd.to_datetime(df.index, errors='coerce', utc=True).tz_localize(None)
                
                # FIX: Force numeric float conversion on all market data columns to satisfy TA-Lib and Metrics modules
                numeric_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                print(f"Downloading historical data for {ticker}...")
                df = yf.download(ticker, start=self.start_date, end=self.end_date, progress=False)
                if not df.empty:
                    df.to_csv(file_path)
            
            if not df.empty:
                data_store[ticker] = self.clean_data(df)
        return data_store

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Flattens Multi-Index columns and cleans missing data gaps safely."""
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.columns = [str(col).strip() for col in df.columns]
        
        # This prevents future lookahead leakage across missing data points.
        df = df.ffill().dropna()
        
        return df