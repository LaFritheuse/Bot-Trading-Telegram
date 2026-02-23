"""VWAP Fade Range — Research strategy for BTC intraday.

Goal:
- Winrate-oriented mean reversion
- Target: return to session VWAP
- Trade only in range regime (ADX filter)
- Realistic execution: next-candle entry, fees, slippage

Notes:
- VWAP is computed per UTC day (session resets at 00:00 UTC).
- We avoid the early-session VWAP instability with `min_session_bars`.
- We optionally force-close positions at session end to avoid VWAP reset issues.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class VWAPFadeConfig:
    # Data
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    start: str = ""
    end: str = ""

    # Execution model
    fee_rate: float = 0.0004
    slippage_rate: float = 0.0002
    risk_per_trade: float = 0.005  # 0.5% equity risk per trade

    # Regime filter
    adx_length: int = 14
    adx_threshold: float = 18.0

    # Mean-reversion signal
    atr_length: int = 14
    band_atr_mult: float = 1.0  # distance from VWAP to consider as "excess"
    min_session_bars: int = 8   # ignore first N bars of each UTC day

    # Optional RSI filter (can be disabled by setting to None)
    rsi_length: int = 14
    rsi_long_max: float = 45.0
    rsi_short_min: float = 55.0

    # Risk management
    sl_atr_mult: float = 1.0
    max_hold_bars: int = 12
    close_at_session_end: bool = True

    # Initial capital (research)
    initial_capital: float = 1000.0


@dataclass
class VWAPFadeResult:
    trades: pd.DataFrame
    summary: Dict[str, float]


def _apply_slippage(price: float, side: str, slippage_rate: float, is_entry: bool) -> float:
    # Simple market slippage model
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


def add_indicators(df: pd.DataFrame, cfg: VWAPFadeConfig) -> pd.DataFrame:
    """Add VWAP (per UTC day), ADX, ATR, RSI using pandas_ta."""
    import pandas_ta as ta

    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")

    out = df.copy()

    # VWAP per UTC day (session reset)
    if out.index.tz is None:
        out.index = out.index.tz_localize("UTC")

    typ = (out["high"] + out["low"] + out["close"]) / 3.0
    pv = typ * out["volume"]
    day = out.index.date

    cum_pv = pv.groupby(day).cumsum()
    cum_vol = out["volume"].groupby(day).cumsum().replace(0, pd.NA)
    out["VWAP"] = (cum_pv / cum_vol).astype(float)

    # Bar count within session (for min_session_bars)
    out["SESSION_BAR"] = out.groupby(day).cumcount()

    # Regime + risk indicators
    adx = ta.adx(out["high"], out["low"], out["close"], length=cfg.adx_length)
    adx_col = next((c for c in adx.columns if str(c).startswith("ADX_")), None)
    if not adx_col:
        raise ValueError(f"ADX column not found in: {list(adx.columns)}")
    out["ADX"] = adx[adx_col]

    out["ATR"] = ta.atr(out["high"], out["low"], out["close"], length=cfg.atr_length)

    out["RSI"] = ta.rsi(out["close"], length=cfg.rsi_length)

    return out


def run_vwap_fade_backtest(df: pd.DataFrame, cfg: VWAPFadeConfig) -> VWAPFadeResult:
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must be indexed by time (DatetimeIndex)")
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")

    df = add_indicators(df, cfg)

    warmup = max(cfg.adx_length, cfg.atr_length, cfg.rsi_length) + 5
    if len(df) <= warmup + 2:
        raise ValueError("Not enough candles for indicators")

    equity = cfg.initial_capital
    equity_curve: List[Optional[float]] = [None] * len(df)
    trades: List[Dict] = []

    in_pos = False
    side = ""
    entry_i = -1
    entry_time = None
    entry_price = 0.0
    sl = 0.0
    tp = 0.0
    qty = 0.0
    entry_day = None

    idx = df.index

    for i in range(warmup, len(df) - 2):
        equity_curve[i] = equity

        row = df.iloc[i]

        # Session end management: if we crossed into a new day, close at previous close.
        if in_pos and cfg.close_at_session_end and entry_day is not None:
            if idx[i].date() != entry_day:
                exit_time = idx[i]
                exit_raw = float(df.iloc[i]["open"])  # first bar open of new day
                exit_price = _apply_slippage(exit_raw, side, cfg.slippage_rate, is_entry=False)

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
                        "entry_time": entry_time,
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
                        "reason": "SESSION_END",
                    }
                )
                in_pos = False
                side = ""
                entry_i = -1
                entry_time = None
                entry_price = 0.0
                sl = 0.0
                tp = 0.0
                qty = 0.0
                entry_day = None
                # Continue to evaluate signals on this bar (new session)
                # (no continue)

        if in_pos:
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
                exit_reason = "SL/TP same candle -> SL (worst)"
                exit_price_raw = sl
            elif hit_sl:
                exit_reason = "SL"
                exit_price_raw = sl
            elif hit_tp:
                exit_reason = "TP"
                exit_price_raw = tp
            else:
                if (i - entry_i) >= cfg.max_hold_bars:
                    exit_reason = "TIME"
                    exit_price_raw = float(df.iloc[i]["close"])

            if exit_reason is not None and exit_price_raw is not None:
                exit_time = idx[i]
                exit_price = _apply_slippage(exit_price_raw, side, cfg.slippage_rate, is_entry=False)

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
                        "entry_time": entry_time,
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
                entry_time = None
                entry_price = 0.0
                sl = 0.0
                tp = 0.0
                qty = 0.0
                entry_day = None

            continue

        # --- No open position: evaluate signal on candle i, enter on i+1 open ---
        if pd.isna(row["ADX"]) or float(row["ADX"]) >= cfg.adx_threshold:
            continue

        if pd.isna(row["ATR"]) or pd.isna(row["VWAP"]) or pd.isna(row["RSI"]):
            continue

        if int(row["SESSION_BAR"]) < cfg.min_session_bars:
            continue

        atr = float(row["ATR"])
        vwap = float(row["VWAP"])
        rsi = float(row["RSI"])

        band = cfg.band_atr_mult * atr
        lower = vwap - band
        upper = vwap + band

        lo = float(row["low"])
        hi = float(row["high"])
        close = float(row["close"])

        long_signal = (lo <= lower) and (close > lower) and (rsi <= cfg.rsi_long_max)
        short_signal = (hi >= upper) and (close < upper) and (rsi >= cfg.rsi_short_min)

        if not (long_signal or short_signal):
            continue

        side = "LONG" if long_signal else "SHORT"

        entry_open = float(df.iloc[i + 1]["open"])
        entry_price = _apply_slippage(entry_open, side, cfg.slippage_rate, is_entry=True)
        entry_i = i + 1
        entry_time = idx[entry_i]
        entry_day = entry_time.date()

        # SL based on ATR at signal candle
        if side == "LONG":
            sl = entry_price - cfg.sl_atr_mult * atr
        else:
            sl = entry_price + cfg.sl_atr_mult * atr

        # TP: static VWAP at entry bar (reduces moving-target bias)
        tp = float(df.iloc[entry_i]["VWAP"])

        # Skip if TP would be on the wrong side (avoid bad setups)
        if side == "LONG" and tp <= entry_price * 1.00005:
            side = ""
            entry_i = -1
            entry_time = None
            entry_day = None
            continue
        if side == "SHORT" and tp >= entry_price * 0.99995:
            side = ""
            entry_i = -1
            entry_time = None
            entry_day = None
            continue

        # Position sizing by risk
        risk_usd = equity * cfg.risk_per_trade
        risk_per_unit = abs(entry_price - sl)
        if risk_per_unit <= 0:
            side = ""
            entry_i = -1
            entry_time = None
            entry_day = None
            continue

        qty = risk_usd / risk_per_unit
        if qty <= 0:
            side = ""
            entry_i = -1
            entry_time = None
            entry_day = None
            continue

        in_pos = True

    # Fill equity curve
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

    total_trades = int(len(trades_df))
    wins = int((trades_df["net_pnl"] > 0).sum()) if total_trades else 0
    winrate = float(wins / total_trades * 100) if total_trades else 0.0

    gross_profit = float(trades_df.loc[trades_df["net_pnl"] > 0, "net_pnl"].sum()) if total_trades else 0.0
    gross_loss = float(trades_df.loc[trades_df["net_pnl"] < 0, "net_pnl"].sum()) if total_trades else 0.0
    profit_factor = float(gross_profit / abs(gross_loss)) if gross_loss < 0 else float("inf") if gross_profit > 0 else 0.0

    final_equity = float(equity_series.iloc[-1])
    total_return_pct = float((final_equity / cfg.initial_capital - 1) * 100)
    max_dd_pct = float(_max_drawdown(equity_series) * 100)

    daily = equity_series.resample("1D").last().pct_change().dropna()
    green_days_pct = float((daily > 0).mean() * 100) if len(daily) else 0.0

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
        "trades_per_day_median": trades_per_day_median,
        "trades_per_day_mean": trades_per_day_mean,
    }

    return VWAPFadeResult(trades=trades_df, summary=summary)
