#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from main import execute_historical_backtest_workflow

try:
    execute_historical_backtest_workflow("us_market.json")
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
