"""
Trend-pullback strategy with a daily setup score.

Every closed M15 bar is scored 0-100 for a long and a short. Direction comes from the H1 trend.
  - strict entry:   score >= strict_score during the session
  - daily fallback: if no trade yet by fallback_hour, take the best-scoring bar seen today
                    (>= fallback_score) at reduced size. This is how "at least 1 trade/day"
                    is met without trading random noise.

All features use only data available at bar close (H1 values are shifted so the
in-progress H1 candle is never used -> no look-ahead).
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from .config import Config
from .indicators import adx, atr, ema, rsi


@dataclass
class Signal:
    time: pd.Timestamp       # bar-close time the signal was generated on
    side: int                # +1 long, -1 short
    score: float
    atr: float
    fallback: bool


def prepare(m15: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Add indicator + score columns. m15: UTC DatetimeIndex (bar OPEN time), columns open/high/low/close."""
    df = m15.copy()
    df["ema"] = ema(df["close"], cfg.ema_fast)
    df["atr"] = atr(df, cfg.atr_period)
    df["rsi"] = rsi(df["close"], cfg.rsi_period)
    df["adx"] = adx(df, cfg.adx_period)

    h1 = m15["close"].resample("1h").last().dropna().to_frame("close")
    h1_ohlc = m15.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    h1["e50"] = ema(h1_ohlc["close"], cfg.h1_ema_fast)
    h1["e200"] = ema(h1_ohlc["close"], cfg.h1_ema_slow)
    h1["slope"] = h1["e50"].diff(3)
    # H1 candle stamped T covers [T, T+1h): usable only from T+1h on -> shift by one H1 bar, then ffill to M15
    h1 = h1[["close", "e50", "e200", "slope"]].shift(1).add_prefix("h1_")
    df = df.join(h1.reindex(df.index, method="ffill"))

    bull = (df["h1_e50"] > df["h1_e200"]) & (df["h1_slope"] > 0) & (df["h1_close"] > df["h1_e200"])
    bear = (df["h1_e50"] < df["h1_e200"]) & (df["h1_slope"] < 0) & (df["h1_close"] < df["h1_e200"])
    df["bias"] = np.where(bull, 1, np.where(bear, -1, 0))
    # no clear H1 bias -> fall back to short-term slope so a fallback trade still has a direction
    weak = np.where(df["ema"].diff(4) >= 0, 1, -1)
    df["side"] = np.where(df["bias"] != 0, df["bias"], weak)

    s = df["side"]
    trend = np.where(df["bias"] != 0, 30.0, 8.0)
    strength = np.clip((df["adx"] - 15) / 15, 0, 1) * 20
    dist = (df["close"] - df["ema"]) * s / df["atr"]                     # ATR units; + = extended in trend direction
    touched = np.where(s == 1, df["low"] <= df["ema"] + 0.3 * df["atr"], df["high"] >= df["ema"] - 0.3 * df["atr"])
    reclaimed = dist > 0                                                  # closed back on the trend side of EMA
    not_overext = dist < 1.2
    pullback = (touched & reclaimed & not_overext) * 25.0
    bar_dir = np.sign(df["close"] - df["open"])
    confirm = (bar_dir == s) * 10.0                                       # signal bar closes in trade direction
    r = df["rsi"]
    mom = np.where(s == 1, ((r > 40) & (r < 65)), ((r < 60) & (r > 35))) * 10.0
    hr = df.index.hour
    sess = np.where((hr >= 12) & (hr < 17), 5.0, np.where((hr >= 7) & (hr < 12), 3.0, 0.0))
    df["score"] = trend + strength + pullback + confirm + mom + sess
    return df


def day_signals(day: pd.DataFrame, cfg: Config, open_ok=lambda ts: True):
    """
    Yield (bar_position, Signal) for one UTC day of prepared bars. At most one signal per day.
    The caller executes at the NEXT bar's open.

    Strict: first bar with score >= strict_score.
    Fallback (no strict setup yet): from fallback_hour, enter on the first bar scoring within 10 points
    of the best score seen so far today (and >= fallback_score); on the last allowed bar, enter if
    score >= fallback_score. Only past/current bars are used -> no hindsight.
    """
    best = -1.0
    for i in range(len(day) - 1):
        ts = day.index[i]
        row = day.iloc[i]
        close_time = ts + pd.Timedelta(minutes=15)
        h = close_time.hour
        if h < cfg.session_start_hour or h > cfg.last_entry_hour or np.isnan(row["atr"]) or not open_ok(ts):
            continue
        sc = float(row["score"])
        sig = Signal(close_time, int(row["side"]), sc, float(row["atr"]), False)
        if sc >= cfg.strict_score:
            yield i, sig
            return
        if h >= cfg.fallback_hour and sc >= cfg.fallback_score:
            last_bar = day.index[i + 1].hour > cfg.last_entry_hour or i + 2 >= len(day)
            if sc >= best - 10 or last_bar:
                sig.fallback = True
                yield i, sig
                return
        best = max(best, sc)
