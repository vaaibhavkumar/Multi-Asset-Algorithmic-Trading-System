import os
import matplotlib.pyplot as plt
import pandas as pd

class SignalVisualizer:
    """
    Module 310: Technical Asset Signal Plotter.
    Renders asset price, technical overlays, and exact historical execution signal triggers.
    """
    @staticmethod
    def plot_asset_signals(df_signals: pd.DataFrame, ticker: str, fast_p: int, slow_p: int):
        """Generates a detailed chart of price, EMAs, and buy/sell signals for a single stock."""
        output_dir = "backtest_reports/signals"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Dynamic column detection: Find whatever columns contain 'EMA' or 'MA'
        ema_cols = [col for col in df_signals.columns if 'EMA' in col or 'ma' in col.lower()]
        
        # Fallback tracking if columns aren't named explicitly with EMA strings
        df_clean = df_signals.copy()
        if ema_cols:
            df_clean = df_clean.dropna(subset=[ema_cols[0]]).copy()
            
        if df_clean.empty:
            print(f"[WARN] Not enough data to plot signals for {ticker}")
            return

        plt.figure(figsize=(14, 7))
        
        # 1. Plot Close Price
        plt.plot(df_clean.index, df_clean['Close'], label='Close Price', color='#7f7f7f', alpha=0.6, lw=1.5)
        
        # 2. Dynamic Overlay of calculated indicators found
        colors = ['#1f77b4', '#ff7f0e', '#9467bd']
        for idx, col in enumerate(ema_cols[:3]):  # Plot up to 3 detected lines
            plt.plot(df_clean.index, df_clean[col], label=col, color=colors[idx % len(colors)], lw=1.2)
        
        # 3. Derive specific Buy and Sell entry trigger points
        df_clean['Signal_Change'] = df_clean['Position'].diff()
        
        buys = df_clean[df_clean['Signal_Change'] == 1]
        sells = df_clean[df_clean['Signal_Change'] == -1]
        
        # 4. Overlay Signal Markers
        if not buys.empty:
            plt.scatter(buys.index, buys['Close'], label='BUY Signal', marker='^', color='#2ca02c', s=100, zorder=5)
        if not sells.empty:
            plt.scatter(sells.index, sells['Close'], label='SELL Signal', marker='v', color='#d62728', s=100, zorder=5)
        
        plt.title(f"Technical Indicator & Signal Execution Map: {ticker}", fontsize=13, fontweight='bold')
        plt.ylabel("Asset Price", fontsize=11)
        plt.xlabel("Timeline Horizon", fontsize=11)
        plt.grid(True, linestyle=':', alpha=0.5)
        plt.legend(loc='upper left', fontsize=10)
        
        plt.tight_layout()
        chart_path = os.path.join(output_dir, f"Signals_{ticker}.png")
        plt.savefig(chart_path, dpi=300)
        plt.close()
        
        print(f"[SUCCESS] Advanced technical signal chart saved to: {chart_path}")