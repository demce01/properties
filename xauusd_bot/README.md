# XAUUSD bot

Trend-pullback strategy on M15 bars with an H1 trend filter, a 0-100 setup score, and a daily-minimum fallback.

**How it picks entries.** Each closed M15 bar is scored on H1 trend alignment (EMA50/200 + slope), ADX strength,
a pullback to the M15 EMA21 that closes back with the trend, a confirming candle, RSI zone, and session
(London/NY overlap scores highest). SL = 1.5 x ATR, TP = 2R, risk 0.5% of equity, flat by 21:00 UTC.

**1 trade per day.** Strict entry at score >= 70. If none by 15:00 UTC, it enters on the best setup of the day
(score >= 45) at half size, so the daily minimum is met without entering on random bars. Tune this in `config.py`.

## Use
```
pip install -r xauusd_bot/requirements.txt
python -m pytest xauusd_bot
python -m xauusd_bot.run_backtest path/to/xauusd_m15.csv   # export M15 from MT5, times in UTC
python -m xauusd_bot.live_mt5                              # dry run (Windows + MT5); --live to trade, DEMO first
```

## Caveats
- The synthetic backtest only checks the code. It has zero edge, as it should. **There is no evidence yet that the
  strategy is profitable.** Backtest on 2+ years of real M15 data, then walk-forward, then 4+ weeks on demo.
- Forcing one trade/day costs money on days with no edge; compare `strict_avg_R` vs `fallback_avg_R` in the output
  and consider raising `fallback_score` or dropping the fallback if it drags.
- Check `--server-utc-offset` against your broker, and model your real spread (gold spreads widen at rollover/news).
- Add a news filter (NFP, CPI, FOMC) before going live.
