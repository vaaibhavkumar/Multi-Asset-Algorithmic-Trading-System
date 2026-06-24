# Multi-Asset Algorithmic Trading System

A custom-built, modular, Python-based algorithmic trading system designed for backtesting and paper trading across Indian (Nifty 50) and US (S&P 500) equity markets.

## 🚀 Overview
Developed as a capstone project for the Certificate Program in Algorithmic Trading (CPAT), this system implements a complete trading lifecycle: from data ingestion and signal generation to risk management and performance analysis.

## 🛠 Features
- **Custom Backtesting Engine:** Built from scratch—no external backtesting libraries used—to ensure full transparency.
- **Adaptive Strategy:** Dual Moving Average crossover with a Macro SMA regime filter.
- **Risk Governance:** Volatility-based position sizing (ATR-based) and hard constraints (Stop-Loss, Daily Loss Limits, Concentration Caps).
- **Bias Prevention:** Rigorous handling of look-ahead and survivorship biases.
- **Paper Trading Ready:** Modular gateway for simulation with realistic slippage/transaction costs.

## 📊 Performance Summary
* **Strategy:** Dual Moving Average + Macro SMA filter
* **Optimal Config:** Fast EMA 25 / Slow EMA 240 / Macro SMA 150
* **Sharpe Ratio (Out-of-Sample):** 2.48
* **Max Drawdown:** -3.89%

## 📁 Project Structure
- `data/`: Automated ingestion via Yahoo Finance with local caching.
- `strategy/`: Core signal computation.
- `risk/`: Position sizing and constraint enforcement.
- `trading/`: Execution gateway for simulation.
