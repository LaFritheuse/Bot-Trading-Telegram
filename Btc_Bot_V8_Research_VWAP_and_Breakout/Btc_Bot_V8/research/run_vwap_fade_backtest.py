"""Research backtest runner: VWAP Fade Range (BTC).

Usage example:
    py research\run_vwap_fade_backtest.py --start 2025-11-01 --end 2026-02-01
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import sys

import ccxt
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.strategies.vwap_fade_range import VWAPFadeConfig, run_vwap_fade_backtest


def _parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def fetch_ohlcv_range(
    exchange: ccxt.Exchange,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
    limit: int = 1000,
    sleep_s: float = 0.05,
) -> pd.DataFrame:
    since_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    rows = []
    exchange.enableRateLimit = True

    while True:
        batch = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=limit)
        if not batch:
            break
        rows.extend(batch)
        last_ts = batch[-1][0]
        if last_ts >= end_ms:
            break
        since_ms = last_ts + 1
        if sleep_s:
            time.sleep(sleep_s)
        if len(rows) > 2_000_000:
            raise RuntimeError("Too many candles fetched; check your date range/timeframe")

    df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    df = df.set_index("time").sort_index()
    df = df[df.index <= end]
    return df


def maybe_load_cache(cache_path: Path) -> Optional[pd.DataFrame]:
    if cache_path.exists():
        try:
            df = pd.read_csv(cache_path)
            df["time"] = pd.to_datetime(df["time"], utc=True)
            df = df.set_index("time").sort_index()
            return df
        except Exception:
            return None
    return None


def save_cache(df: pd.DataFrame, cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    out = df.reset_index().copy()
    out.to_csv(cache_path, index=False)


def main() -> None:
    p = argparse.ArgumentParser(description="Research backtest: VWAP Fade Range")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="15m", choices=["5m", "15m"], help="Start with 15m")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")

    # Execution
    p.add_argument("--fee", type=float, default=0.0004)
    p.add_argument("--slippage", type=float, default=0.0002)
    p.add_argument("--risk", type=float, default=0.005)

    # Strategy params
    p.add_argument("--adx", type=float, default=18.0, help="ADX(14) threshold for RANGE")
    p.add_argument("--band-atr", dest="band_atr", type=float, default=1.0, help="VWAP band distance in ATR multiples")
    p.add_argument("--min-session-bars", dest="min_session_bars", type=int, default=8)
    p.add_argument("--rsi-long", dest="rsi_long", type=float, default=45.0)
    p.add_argument("--rsi-short", dest="rsi_short", type=float, default=55.0)
    p.add_argument("--sl-atr", dest="sl_atr", type=float, default=1.0)
    p.add_argument("--max-hold", dest="max_hold", type=int, default=12)
    p.add_argument("--no-session-close", dest="no_session_close", action="store_true", help="Do not force-close at session end")

    # Output
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--outdir", default="research/output")

    args = p.parse_args()
    start = _parse_date(args.start)
    end = _parse_date(args.end)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    cache_name = f"ohlcv_{args.symbol.replace('/', '')}_{args.timeframe}_{args.start}_{args.end}.csv"
    cache_path = Path("research/data") / cache_name
    df = None if args.no_cache else maybe_load_cache(cache_path)

    if df is None:
        ex = ccxt.binance()
        df = fetch_ohlcv_range(ex, args.symbol, args.timeframe, start, end)
        if not args.no_cache:
            save_cache(df, cache_path)

    cfg = VWAPFadeConfig(
        symbol=args.symbol,
        timeframe=args.timeframe,
        start=args.start,
        end=args.end,
        fee_rate=args.fee,
        slippage_rate=args.slippage,
        risk_per_trade=args.risk,
        adx_threshold=args.adx,
        band_atr_mult=args.band_atr,
        min_session_bars=args.min_session_bars,
        rsi_long_max=args.rsi_long,
        rsi_short_min=args.rsi_short,
        sl_atr_mult=args.sl_atr,
        max_hold_bars=args.max_hold,
        close_at_session_end=(not args.no_session_close),
    )

    result = run_vwap_fade_backtest(df.copy(), cfg)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = f"VWAP_FADE_{args.timeframe}_{args.start}_{args.end}_{stamp}"
    trades_path = outdir / f"trades_{base}.csv"
    summary_path = outdir / f"summary_{base}.json"

    result.trades.to_csv(trades_path, index=False)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"config": asdict(cfg), "summary": result.summary}, f, ensure_ascii=False, indent=2)

    print("\n===== VWAP Fade Research Backtest =====")
    print(f"Symbol: {args.symbol} | TF: {args.timeframe} | {args.start} -> {args.end}")
    for k, v in result.summary.items():
        print(f"{k}: {v}")
    print("--------------------------------")
    print(f"Trades CSV : {trades_path}")
    print(f"Summary JSON: {summary_path}")


if __name__ == "__main__":
    main()
