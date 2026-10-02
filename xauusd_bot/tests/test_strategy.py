import numpy as np
import pandas as pd

from xauusd_bot.backtest import run
from xauusd_bot.config import Config
from xauusd_bot.data import synthetic
from xauusd_bot.strategy import prepare


def test_at_most_one_trade_per_day_and_most_days_traded():
    m15 = synthetic(days=80, seed=1)
    trades, _, n_days = run(m15, Config())
    days = [t.entry_time.date() for t in trades]
    assert len(days) == len(set(days))
    assert len(trades) >= 0.95 * n_days          # daily-minimum fallback works


def test_no_lookahead_in_features():
    """Changing future bars must not change earlier scores."""
    m15 = synthetic(days=40, seed=2)
    a = prepare(m15, Config())
    m2 = m15.copy()
    cut = len(m2) - 200
    m2.iloc[cut:, :] = m2.iloc[cut:, :] + 50     # perturb the future
    b = prepare(m2, Config())
    pd.testing.assert_series_equal(a["score"].iloc[:cut - 8], b["score"].iloc[:cut - 8])


def test_sl_checked_before_tp_when_both_hit():
    from xauusd_bot.backtest import _execute
    from xauusd_bot.strategy import Signal
    idx = pd.date_range("2024-03-01 10:00", periods=4, freq="15min", tz="UTC")
    day = pd.DataFrame({"open": [100, 100, 100, 100], "high": [100, 100, 200, 100],
                        "low": [100, 100, 0, 100], "close": [100] * 4}, index=idx)
    cfg = Config(spread=0, slippage=0)
    t = _execute(day, 0, Signal(idx[0], 1, 80, 2.0, False), cfg, 10_000)
    assert t.reason == "sl" and t.r < 0


def test_fallback_uses_reduced_risk():
    from xauusd_bot.backtest import _execute
    from xauusd_bot.strategy import Signal
    idx = pd.date_range("2024-03-01 10:00", periods=3, freq="15min", tz="UTC")
    day = pd.DataFrame({"open": [100.0] * 3, "high": [100.0] * 3, "low": [100.0] * 3, "close": [100.0] * 3}, index=idx)
    cfg = Config(spread=0, slippage=0)
    full = _execute(day, 0, Signal(idx[0], 1, 80, 2.0, False), cfg, 10_000)
    fb = _execute(day, 0, Signal(idx[0], 1, 50, 2.0, True), cfg, 10_000)
    assert np.isclose(fb.lots, full.lots * cfg.fallback_risk_mult)
