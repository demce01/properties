"""Run on the Windows machine with MT5: python -m xauusd_bot.export_mt5_csv [years] -> xauusd_m15.csv (UTC)
Set SERVER_UTC_OFFSET to your broker's server-time offset from UTC."""
import sys
from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5
import pandas as pd

SERVER_UTC_OFFSET = 2
years = float(sys.argv[1]) if len(sys.argv) > 1 else 2
mt5.initialize()
mt5.symbol_select("XAUUSD", True)
r = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_M15, datetime.now(timezone.utc) - timedelta(days=365 * years),
                         datetime.now(timezone.utc))
df = pd.DataFrame(r)
df["time"] = pd.to_datetime(df["time"], unit="s") - pd.Timedelta(hours=SERVER_UTC_OFFSET)
df[["time", "open", "high", "low", "close"]].to_csv("xauusd_m15.csv", index=False)
print(len(df), "bars written")
