import numpy as np
import pandas as pd


def load_csv(path: str) -> pd.DataFrame:
    """Load M15 XAUUSD bars. Needs a time column (+ open/high/low/close). Times must be UTC (bar open)."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().strip("<>") for c in df.columns]
    if "date" in df and "time" in df:                       # MT5 export style
        df["time"] = pd.to_datetime(df["date"].astype(str) + " " + df["time"].astype(str))
    tcol = next(c for c in ("time", "datetime", "timestamp", "date") if c in df)
    df.index = pd.to_datetime(df[tcol], utc=True)
    df = df[["open", "high", "low", "close"]].astype(float).sort_index()
    return df[~df.index.duplicated()]


def synthetic(days: int = 120, seed: int = 0, drift: float = 0.0) -> pd.DataFrame:
    """Random-walk M15 gold-like bars (Mon-Fri, 24h). For tests/plumbing only - NOT evidence of edge."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=days * 96 * 7 // 5 + 96, freq="15min", tz="UTC")
    idx = idx[idx.dayofweek < 5][: days * 96]
    vol = 0.9 + 0.6 * ((idx.hour >= 7) & (idx.hour < 17))     # more movement in London/NY
    ret = rng.normal(drift, 1.0, len(idx)) * vol
    close = 2000 + np.cumsum(ret)
    open_ = np.concatenate([[2000], close[:-1]])
    spread = np.abs(rng.normal(0.5, 0.3, len(idx))) * vol
    return pd.DataFrame({"open": open_, "high": np.maximum(open_, close) + spread,
                         "low": np.minimum(open_, close) - spread, "close": close}, index=idx)
