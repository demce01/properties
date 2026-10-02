"""Bar-by-bar backtester. Entry at next bar open; SL checked before TP inside a bar (conservative)."""
from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

from .config import Config
from .strategy import prepare, day_signals


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    side: int
    entry: float
    exit: float
    lots: float
    pnl: float
    r: float
    score: float
    fallback: bool
    reason: str


def run(m15: pd.DataFrame, cfg: Config = Config(), equity: float = 10_000.0, warmup_days: int = 15):
    df = prepare(m15, cfg)
    df = df[df.index >= df.index[0].normalize() + pd.Timedelta(days=warmup_days)]
    trades: List[Trade] = []
    eq = equity
    for _, day in df.groupby(df.index.date):
        for i, sig in day_signals(day, cfg):
            t = _execute(day, i, sig, cfg, eq)
            if t:
                trades.append(t)
                eq += t.pnl
    return trades, eq, df.index.normalize().nunique()


def _execute(day: pd.DataFrame, i: int, sig, cfg: Config, equity: float):
    ebar = day.iloc[i + 1]
    side = sig.side
    entry = ebar["open"] + side * (cfg.spread + cfg.slippage)
    risk_px = cfg.sl_atr_mult * sig.atr
    sl = entry - side * risk_px
    tp = entry + side * cfg.tp_r_mult * risk_px
    risk_cash = equity * cfg.risk_per_trade * (cfg.fallback_risk_mult if sig.fallback else 1.0)
    lots = risk_cash / (risk_px * cfg.contract_size)
    exit_px, reason, exit_time = None, "eod", day.index[-1]
    for j in range(i + 1, len(day)):
        b = day.iloc[j]
        ts = day.index[j]
        hit_sl = b["low"] <= sl if side == 1 else b["high"] >= sl
        hit_tp = b["high"] >= tp if side == 1 else b["low"] <= tp
        if hit_sl:                      # SL first when both touched
            exit_px, reason, exit_time = sl - side * cfg.slippage, "sl", ts
            break
        if hit_tp:
            exit_px, reason, exit_time = tp, "tp", ts
            break
        if ts.hour >= cfg.flat_hour:
            exit_px, reason, exit_time = b["close"], "flat", ts
            break
    if exit_px is None:
        exit_px = day.iloc[-1]["close"]
    pnl = (exit_px - entry) * side * lots * cfg.contract_size
    return Trade(day.index[i + 1], exit_time, side, entry, exit_px, lots, pnl,
                 (exit_px - entry) * side / risk_px, sig.score, sig.fallback, reason)


def summarize(trades: List[Trade], start_equity: float, end_equity: float, n_days: int) -> dict:
    if not trades:
        return {"trades": 0}
    pnl = np.array([t.pnl for t in trades])
    curve = start_equity + np.cumsum(pnl)
    peak = np.maximum.accumulate(np.concatenate([[start_equity], curve]))[1:]
    gp, gl = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    strict = [t for t in trades if not t.fallback]
    fb = [t for t in trades if t.fallback]
    avg = lambda ts: round(float(np.mean([t.r for t in ts])), 3) if ts else None
    return {
        "trading_days": n_days,
        "trades": len(trades),
        "trades_per_day": round(len(trades) / n_days, 2),
        "win_rate": round(float((pnl > 0).mean()), 3),
        "avg_R": avg(trades),
        "profit_factor": round(float(gp / gl), 2) if gl else float("inf"),
        "return_pct": round(100 * (end_equity / start_equity - 1), 2),
        "max_drawdown_pct": round(float(100 * ((peak - curve) / peak).max()), 2),
        "strict_trades": len(strict), "strict_avg_R": avg(strict),
        "fallback_trades": len(fb), "fallback_avg_R": avg(fb),
    }
