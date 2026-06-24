import os
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

class BacktestVisualizer:
    """
    Module 310: Institutional Plotting and Visualization Suite.
    Generates high-resolution comparative performance curves and drawdown profiles.
    """
    @staticmethod
    def generate_plots(equity_curve: pd.Series, data_universe: dict, 
                       benchmark_symbol: str, market_name: str, 
                       strategy_name: str, allocation_mode: str):
        """Plots the standardized strategy equity curve vs baseline benchmark indices with unique timestamps."""
        output_dir = "backtest_reports/charts"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        if benchmark_symbol not in data_universe:
            print(f"[WARN] Benchmark {benchmark_symbol} missing from data universe. Plotting skipped.")
            return
            
        bench_df = data_universe[benchmark_symbol]
        
        # Sync indices explicitly
        common_idx = equity_curve.index.intersection(bench_df.index)
        if len(common_idx) == 0:
            common_idx = equity_curve.index
            bench_close = pd.to_numeric(bench_df['Close'], errors='coerce').reindex(common_idx, method='ffill')
        else:
            bench_close = pd.to_numeric(bench_df['Close'], errors='coerce').loc[common_idx]
            equity_curve = equity_curve.loc[common_idx]
            
        normalized_bench = (bench_close / bench_close.iloc[0]) * 100000.0
        rolling_max = equity_curve.cummax()
        strategy_drawdown = (equity_curve - rolling_max) / rolling_max * 100.0
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
        
        # Top Plot
        ax1.plot(equity_curve.index, equity_curve.values, label=f"Strategy: {strategy_name} ({allocation_mode})", color='#1f77b4', lw=2)
        ax1.plot(normalized_bench.index, normalized_bench.values, label=f"Benchmark: {benchmark_symbol}", color='#ff7f0e', linestyle='--', lw=1.5)
        ax1.set_title(f"Performance Analysis Suite - {market_name} Equities", fontsize=14, fontweight='bold', pad=15)
        ax1.set_ylabel("Portfolio Value ($)", fontsize=11)
        ax1.grid(True, linestyle=':', alpha=0.6)
        ax1.legend(loc="upper left", fontsize=10)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
        
        # Bottom Plot
        ax2.fill_between(strategy_drawdown.index, strategy_drawdown.values, 0, color='#d62728', alpha=0.3, label="Drawdown %")
        ax2.plot(strategy_drawdown.index, strategy_drawdown.values, color='#d62728', lw=1)
        ax2.set_ylabel("Drawdown (%)", fontsize=11)
        ax2.set_xlabel("Timeline Horizon", fontsize=11)
        ax2.set_ylim(bottom=min(strategy_drawdown.min() * 1.1, -5.0), top=1.0)
        ax2.grid(True, linestyle=':', alpha=0.6)
        ax2.legend(loc="lower left", fontsize=10)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.1f}%"))
        
        plt.tight_layout()
        
        # ADD TIMEOFFSET TIMESTAMP FOR UNIQUE GENERATION
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"Chart_{market_name}_{strategy_name}_{allocation_mode}_{timestamp_str}.png"
        full_path = os.path.join(output_dir, file_name)
        
        plt.savefig(full_path, dpi=150)
        plt.close()
        print(f"[SUCCESS] Performance data chart permanently saved to: {full_path}")