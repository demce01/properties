"""
Live runner for MetaTrader 5 (Windows; MT5 terminal installed + logged in).

    pip install MetaTrader5
    python -m xauusd_bot.live_mt5            # DRY RUN (logs only) - default
    python -m xauusd_bot.live_mt5 --live     # sends real orders. Use a DEMO account first.

Reuses the exact strategy code from the backtest. Acts only on a signal produced by the most
recently CLOSED M15 bar, and never opens a 2nd trade on the same UTC day (checked via magic number).
"""
import argparse
import logging
import time
from datetime import datetime, timedelta, timezone

import pandas as pd

from .config import Config
from .strategy import day_signals, prepare

MAGIC = 26_0001
log = logging.getLogger("xauusd_bot")


def _to_lots(mt5, info, risk_cash: float, risk_px: float) -> float:
    per_lot_loss = risk_px / info.trade_tick_size * info.trade_tick_value
    lots = risk_cash / per_lot_loss
    step = info.volume_step
    lots = max(info.volume_min, min(info.volume_max, round(lots / step) * step))
    return round(lots, 2)


def _bars(mt5, cfg: Config, server_utc_offset_h: int, n: int = 2500) -> pd.DataFrame:
    rates = mt5.copy_rates_from_pos(cfg.symbol, mt5.TIMEFRAME_M15, 0, n)
    df = pd.DataFrame(rates)
    # MT5 'time' is broker-server time stamped as if UTC; shift to real UTC
    df.index = pd.to_datetime(df["time"], unit="s", utc=True) - pd.Timedelta(hours=server_utc_offset_h)
    return df[["open", "high", "low", "close"]]


def _traded_today(mt5, cfg: Config) -> bool:
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    deals = mt5.history_deals_get(start - timedelta(hours=14), datetime.now(timezone.utc) + timedelta(hours=14))
    pos = mt5.positions_get(symbol=cfg.symbol) or []
    return any(p.magic == MAGIC for p in pos) or any(
        d.magic == MAGIC and d.entry == mt5.DEAL_ENTRY_IN and
        datetime.fromtimestamp(d.time, timezone.utc).date() == start.date() for d in (deals or []))


def step(mt5, cfg: Config, live: bool, server_utc_offset_h: int):
    bars = _bars(mt5, cfg, server_utc_offset_h)
    df = prepare(bars, cfg)                       # last row is the still-forming bar; it only acts as "next bar"
    today = df[df.index.date == df.index[-1].date()]
    if len(today) < 2 or _traded_today(mt5, cfg):
        return
    latest_closed = today.index[-2] + pd.Timedelta(minutes=15)
    for i, sig in day_signals(today, cfg):
        if sig.time != latest_closed:
            return                                # stale signal (e.g. bot restarted late) - do not chase
        info, tick = mt5.symbol_info(cfg.symbol), mt5.symbol_info_tick(cfg.symbol)
        if not sig.fallback and (tick.ask - tick.bid) > cfg.max_spread_points:
            log.warning("spread %.2f too wide, skipping bar", tick.ask - tick.bid)
            return
        price = tick.ask if sig.side == 1 else tick.bid
        risk_px = cfg.sl_atr_mult * sig.atr
        sl, tp = price - sig.side * risk_px, price + sig.side * cfg.tp_r_mult * risk_px
        acct = mt5.account_info()
        risk_cash = acct.equity * cfg.risk_per_trade * (cfg.fallback_risk_mult if sig.fallback else 1.0)
        lots = _to_lots(mt5, info, risk_cash, risk_px)
        req = dict(action=mt5.TRADE_ACTION_DEAL, symbol=cfg.symbol, volume=lots,
                   type=mt5.ORDER_TYPE_BUY if sig.side == 1 else mt5.ORDER_TYPE_SELL,
                   price=price, sl=round(sl, info.digits), tp=round(tp, info.digits), deviation=30,
                   magic=MAGIC, comment=f"s{sig.score:.0f}{'F' if sig.fallback else ''}",
                   type_time=mt5.ORDER_TIME_GTC, type_filling=mt5.ORDER_FILLING_IOC)
        log.info("SIGNAL side=%+d score=%.0f fallback=%s lots=%.2f sl=%.2f tp=%.2f",
                 sig.side, sig.score, sig.fallback, lots, sl, tp)
        if live:
            res = mt5.order_send(req)
            log.info("order_send -> retcode=%s %s", res.retcode, res.comment)
        return


def close_all_if_flat_time(mt5, cfg: Config):
    if datetime.now(timezone.utc).hour < cfg.flat_hour:
        return
    for p in mt5.positions_get(symbol=cfg.symbol) or []:
        if p.magic != MAGIC:
            continue
        t = mt5.symbol_info_tick(cfg.symbol)
        buy = p.type == mt5.POSITION_TYPE_BUY
        mt5.order_send(dict(action=mt5.TRADE_ACTION_DEAL, symbol=cfg.symbol, volume=p.volume, position=p.ticket,
                            type=mt5.ORDER_TYPE_SELL if buy else mt5.ORDER_TYPE_BUY,
                            price=t.bid if buy else t.ask, deviation=30, magic=MAGIC, comment="flat",
                            type_filling=mt5.ORDER_FILLING_IOC))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="send real orders (default: dry run)")
    ap.add_argument("--server-utc-offset", type=int, default=2,
                    help="broker server time minus UTC in hours (check your broker! many use +2/+3)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    import MetaTrader5 as mt5                       # imported here so backtests work without it

    cfg = Config()
    if not mt5.initialize():
        raise SystemExit(f"MT5 init failed: {mt5.last_error()}")
    mt5.symbol_select(cfg.symbol, True)
    log.info("started (%s) symbol=%s", "LIVE" if args.live else "DRY RUN", cfg.symbol)
    last = None
    try:
        while True:
            now = datetime.now(timezone.utc)
            bar = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0)
            if bar != last and now.second >= 3:     # a new M15 bar just closed
                last = bar
                try:
                    step(mt5, cfg, args.live, args.server_utc_offset)
                    if args.live:
                        close_all_if_flat_time(mt5, cfg)
                except Exception:
                    log.exception("step failed")
            time.sleep(1)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
