"""python -m xauusd_bot.run_backtest [path/to/xauusd_m15.csv]   (no arg -> synthetic data, plumbing check only)"""
import sys

from .backtest import run, summarize
from .config import Config
from .data import load_csv, synthetic

if __name__ == "__main__":
    if len(sys.argv) > 1:
        m15 = load_csv(sys.argv[1])
    else:
        print("!! No CSV given: using synthetic random-walk data. Results are meaningless.")
        m15 = synthetic()
    trades, eq, n_days = run(m15, Config())
    for k, v in summarize(trades, 10_000.0, eq, n_days).items():
        print(f"{k:>20}: {v}")
