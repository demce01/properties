"""All tunable parameters in one place. Times are UTC (convert broker server time first)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    symbol: str = "XAUUSD"

    # --- indicators (on M15 bars; H1 is resampled internally) ---
    ema_fast: int = 21
    h1_ema_fast: int = 50
    h1_ema_slow: int = 200
    atr_period: int = 14
    adx_period: int = 14
    rsi_period: int = 14

    # --- trading window (UTC) ---
    session_start_hour: int = 7      # London open
    fallback_hour: int = 15          # after this, take best-of-day if nothing passed strict filter
    last_entry_hour: int = 19        # no new entries after this
    flat_hour: int = 21              # close any open trade (avoid rollover/spread widening)

    # --- setup scoring (0-100) ---
    strict_score: float = 70.0       # normal entry threshold
    fallback_score: float = 45.0     # minimum for the daily-minimum fallback trade
    fallback_risk_mult: float = 0.5  # fallback trades use reduced size

    # --- risk / exits ---
    risk_per_trade: float = 0.005    # 0.5% of equity at risk per trade
    sl_atr_mult: float = 1.5
    tp_r_mult: float = 2.0
    max_spread_points: float = 0.50  # USD; skip strict entries when spread is wider
    max_trades_per_day: int = 1

    # --- backtest costs ---
    spread: float = 0.25             # USD per oz, paid on entry
    slippage: float = 0.05           # USD per oz, against us on entry and SL exits
    contract_size: float = 100.0     # oz per 1.00 lot
