"""BRR — Bollinger Rejection Range (Research strategy).

Design goals:
- Winrate-oriented mean reversion
- Trade only in *range* regime (ADX filter)
- Realistic backtest: next-candle execution, fees, slippage

This is not wired to the Telegram bot on purpose.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class BRRConfig:
    # Data
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    start: str = ""
    end: str = ""

    # Execution model
    fee_rate: float = 0.0004
    slippage_rate: float = 0.0002
    risk_per_trade: float = 0.005  # 0.5% of equity per trade

    # Strategy params
    bb_length: int = 20
    bb_std: float = 2.0
    adx_length: int = 14
    adx_threshold: float = 18.0
    rsi_length: int = 14
    rsi_long_max: float = 45.0
    rsi_short_min: float = 55.0
    atr_length: int = 14
    atr_mult: float = 1.2
    max_hold_bars: int = 12

    # Initial capital for research
    initial_capital: float = 1000.0


@dataclass
class BRRResult:
    trades: pd.DataFrame
    summary: Dict[str, float]


def _bb_col(prefix: str, length: int, std: float, cols: List[str]) -> str:
    """Robust column selector for pandas_ta bbands output."""
    std_variants: List[str] = []
    for s in [str(std), f"{std:g}"]:
        if s not in std_variants:
            std_variants.append(s)
    try:
        if float(std).is_integer():
            si = str(int(float(std)))
            if si not in std_variants:
                std_variants.append(si)
    except Exception:
        pass

    for s in std_variants:
        c = f"{prefix}_{length}_{s}"
        if c in cols:
            return c
    # fallback: startswith
    pref = f"{prefix}_{length}_"
    for c in cols:
        if str(c).startswith(pref):
            return str(c)
    for c in cols:
        if str(c).startswith(prefix):
            return str(c)
    raise KeyError(f"{prefix}_{length}_{std}")


def add_indicators(df: pd.DataFrame, cfg: BRRConfig) -> pd.DataFrame:
    """Add BB, RSI, ADX, ATR indicators using pandas_ta (required dependency)."""
    # Import locally to keep bot imports light
    import pandas_ta as ta

    # Ensure columns exist
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")

    out = df.copy()
    out["RSI"] = ta.rsi(out["close"], length=cfg.rsi_length)

    bb = ta.bbands(out["close"], length=cfg.bb_length, std=cfg.bb_std)
    bbu = _bb_col("BBU", cfg.bb_length, cfg.bb_std, list(bb.columns))
    bbm = _bb_col("BBM", cfg.bb_length, cfg.bb_std, list(bb.columns))
    bbl = _bb_col("BBL", cfg.bb_length, cfg.bb_std, list(bb.columns))
    out["BBU"] = bb[bbu]
    out["BBM"] = bb[bbm]
    out["BBL"] = bb[bbl]

    adx = ta.adx(out["high"], out["low"], out["close"], length=cfg.adx_length)
    # Typical columns: ADX_14, DMP_14, DMN_14
    adx_col = next((c for c in adx.columns if str(c).startswith("ADX_")), None)
    if not adx_col:
        raise ValueError(f"ADX column not found in: {list(adx.columns)}")
    out["ADX"] = adx[adx_col]

    atr = ta.atr(out["high"], out["low"], out["close"], length=cfg.atr_length)
    out["ATR"] = atr

    return out


def _apply_slippage(price: float, side: str, slippage_rate: float, is_entry: bool) -> float:
    """Apply a simple slippage model for market orders."""
    # side: LONG or SHORT
    # For a long, entry is worse (higher), exit is worse (lower)
    # For a short, entry is worse (lower), exit is worse (higher)
    if side == "LONG":
        return price * (1 + slippage_rate) if is_entry else price * (1 - slippage_rate)
    else:
        return price * (1 - slippage_rate) if is_entry else price * (1 + slippage_rate)


def _fees(notional: float, fee_rate: float) -> float:
    return abs(notional) * fee_rate


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())


def run_brr_backtest(df: pd.DataFrame, cfg: BRRConfig) -> BRRResult:
    """Run the BRR backtest on a dataframe indexed by UTC datetime."""
    df = df.copy()
    if df.index.name != "time" and not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must be indexed by time (DatetimeIndex)")
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")

    df = add_indicators(df, cfg)

    # Warmup
    warmup = max(cfg.bb_length, cfg.rsi_length, cfg.adx_length, cfg.atr_length) + 5
    if len(df) <= warmup + 2:
        raise ValueError("Not enough candles for indicators")

    equity = cfg.initial_capital
    # Store equity snapshot per candle, then forward-fill.
    equity_curve: List[Optional[float]] = [None] * len(df)

    trades: List[Dict] = []

    in_pos = False
    side = ""
    entry_i = -1
    entry_price = 0.0
    sl = 0.0
    tp = 0.0
    qty = 0.0

    idx = df.index

    for i in range(warmup, len(df) - 2):
        # Snapshot equity at candle close (simple hold model)
        equity_curve[i] = equity

        if in_pos:
            # Manage open position by scanning current candle for fills
            hi = float(df.iloc[i]["high"])
            lo = float(df.iloc[i]["low"])

            hit_sl = hit_tp = False
            if side == "LONG":
                hit_sl = lo <= sl
                hit_tp = hi >= tp
            else:
                hit_sl = hi >= sl
                hit_tp = lo <= tp

            exit_reason: Optional[str] = None
            exit_price_raw: Optional[float] = None

            if hit_sl and hit_tp:
                # Worst-case assumption: SL first
                exit_reason = "SL/TP same candle -> SL (worst)"
                exit_price_raw = sl
            elif hit_sl:
                exit_reason = "SL"
                exit_price_raw = sl
            elif hit_tp:
                exit_reason = "TP"
                exit_price_raw = tp
            else:
                # Time stop check
                if (i - entry_i) >= cfg.max_hold_bars:
                    exit_reason = "TIME"
                    exit_price_raw = float(df.iloc[i]["close"])

            if exit_reason is not None and exit_price_raw is not None:
                exit_time = idx[i]
                exit_price = _apply_slippage(exit_price_raw, side, cfg.slippage_rate, is_entry=False)

                # PnL
                if side == "LONG":
                    gross = qty * (exit_price - entry_price)
                else:
                    gross = qty * (entry_price - exit_price)

                fee = _fees(qty * entry_price, cfg.fee_rate) + _fees(qty * exit_price, cfg.fee_rate)
                pnl = gross - fee

                equity_before = equity
                equity += pnl

                trades.append(
                    {
                        "entry_time": idx[entry_i],
                        "exit_time": exit_time,
                        "side": side,
                        "entry": entry_price,
                        "exit": exit_price,
                        "sl": sl,
                        "tp": tp,
                        "qty": qty,
                        "gross_pnl": gross,
                        "fees": fee,
                        "net_pnl": pnl,
                        "equity_before": equity_before,
                        "equity_after": equity,
                        "bars_held": i - entry_i,
                        "reason": exit_reason,
                    }
                )

                in_pos = False
                side = ""
                entry_i = -1
                entry_price = 0.0
                sl = 0.0
                tp = 0.0
                qty = 0.0

            continue

        # --- No open position: evaluate signal on candle i (enter on i+1 open) ---
        row = df.iloc[i]
        # Filters
        if pd.isna(row["ADX"]) or float(row["ADX"]) >= cfg.adx_threshold:
            continue

        if pd.isna(row["ATR"]) or pd.isna(row["RSI"]) or pd.isna(row["BBU"]) or pd.isna(row["BBL"]) or pd.isna(row["BBM"]):
            continue

        rsi = float(row["RSI"])
        atr = float(row["ATR"])
        bbu = float(row["BBU"])
        bbm = float(row["BBM"])
        bbl = float(row["BBL"])

        # Candle attributes
        lo = float(row["low"])
        hi = float(row["high"])
        close = float(row["close"])

        long_signal = (lo <= bbl) and (close > bbl) and (rsi <= cfg.rsi_long_max)
        short_signal = (hi >= bbu) and (close < bbu) and (rsi >= cfg.rsi_short_min)

        if not (long_signal or short_signal):
            continue

        side = "LONG" if long_signal else "SHORT"
        # Entry next candle open
        entry_open = float(df.iloc[i + 1]["open"])
        entry_price = _apply_slippage(entry_open, side, cfg.slippage_rate, is_entry=True)
        entry_i = i + 1

        # SL via ATR at signal candle (i)
        if side == "LONG":
            sl = entry_price - cfg.atr_mult * atr
            tp = bbm
            # If TP is not above entry, skip trade (bad mean-reversion setup)
            if tp <= entry_price * 1.0001:
                side = ""
                entry_i = -1
                continue
        else:
            sl = entry_price + cfg.atr_mult * atr
            tp = bbm
            if tp >= entry_price * 0.9999:
                side = ""
                entry_i = -1
                continue

        # Position sizing by risk (equity fraction) relative to distance to SL
        risk_usd = equity * cfg.risk_per_trade
        risk_per_unit = abs(entry_price - sl)
        if risk_per_unit <= 0:
            side = ""
            entry_i = -1
            continue

        qty = risk_usd / risk_per_unit
        if qty <= 0:
            side = ""
            entry_i = -1
            continue

        in_pos = True

    # Forward-fill equity curve from start to end.
    last = cfg.initial_capital
    filled: List[float] = []
    for v in equity_curve:
        if v is None:
            filled.append(last)
        else:
            last = float(v)
            filled.append(last)

    equity_series = pd.Series(filled, index=df.index, name="equity")

    trades_df = pd.DataFrame(trades)

    # Metrics
    total_trades = int(len(trades_df))
    wins = int((trades_df["net_pnl"] > 0).sum()) if total_trades else 0
    losses = total_trades - wins
    winrate = float(wins / total_trades * 100) if total_trades else 0.0

    gross_profit = float(trades_df.loc[trades_df["net_pnl"] > 0, "net_pnl"].sum()) if total_trades else 0.0
    gross_loss = float(trades_df.loc[trades_df["net_pnl"] < 0, "net_pnl"].sum()) if total_trades else 0.0
    profit_factor = float(gross_profit / abs(gross_loss)) if gross_loss < 0 else float("inf") if gross_profit > 0 else 0.0

    final_equity = float(equity_series.iloc[-1])
    total_return_pct = float((final_equity / cfg.initial_capital - 1) * 100)
    max_dd_pct = float(_max_drawdown(equity_series) * 100)

    # Daily green %
    daily = equity_series.resample("1D").last().pct_change().dropna()
    green_days_pct = float((daily > 0).mean() * 100) if len(daily) else 0.0

    # Trades per day (approx)
    if total_trades and "entry_time" in trades_df.columns:
        trades_df["entry_time"] = pd.to_datetime(trades_df["entry_time"], utc=True)
        tpd = trades_df.groupby(trades_df["entry_time"].dt.date).size()
        trades_per_day_median = float(tpd.median())
        trades_per_day_mean = float(tpd.mean())
    else:
        trades_per_day_median = 0.0
        trades_per_day_mean = 0.0

    summary: Dict[str, float] = {
        "initial_capital": float(cfg.initial_capital),
        "final_equity": final_equity,
        "total_return_pct": total_return_pct,
        "total_trades": float(total_trades),
        "winrate_pct": winrate,
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_dd_pct,
        "green_days_pct": green_days_pct,
        "trades_per_day_mean": trades_per_day_mean,
        "trades_per_day_median": trades_per_day_median,
    }

    return BRRResult(trades=trades_df, summary=summary)
