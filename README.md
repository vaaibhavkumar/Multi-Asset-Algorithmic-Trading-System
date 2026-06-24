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

## Roadmap & Future Iterations
This project serves as a foundational engine for algorithmic trading. Future development will focus on enhancing strategy robustness, scaling the execution infrastructure, and refining risk governance.

## 🚀 Phase 1: Real-World Execution
Broker API Integration: Transition from the current simulation gateway to a live BrokerExecutionGateway using robust APIs (e.g., Alpaca or Indian Broker APIs).

Parallel Validation: Execute side-by-side paper trading for 2–4 weeks to reconcile slippage and execution latency between models and reality.

## 📈 Phase 2: Strategy Robustness
ADX Integration: Implement an Average Directional Index (ADX) module to validate trend strength and filter out market noise.

Walk-Forward Analysis: Move from static backtesting to rolling-window optimization to ensure strategy parameters remain relevant across changing market regimes.

## 🛡 Phase 3: Advanced Risk & Infrastructure
Dynamic Circuit Breakers: Incorporate automated trading halts based on SEBI/SEC-aligned market volatility thresholds.

Real-time Monitoring: Develop a dashboard to track P&L, latency, and system health in real-time.
