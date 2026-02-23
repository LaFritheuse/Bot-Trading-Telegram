"""Volatility Breakout Filtered — Research strategy for BTC intraday.

Purpose:
- Provide a robust "plan B" strategy that can do well in trending regimes.
- This is NOT optimized for winrate; it's here to compare regimes and avoid
  getting trapped in mean-reversion when BTC trends strongly.

Signal:
- Breakout of Donchian channel (N bars) with trend + ADX filters.

Execution:
- Next-candle entry, fees, slippage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class VolBreakoutConfig:
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    start: str = ""
    end: str = ""

    fee_rate: float = 0.0004
    slippage_rate: float = 0.0002
    risk_per_trade: float = 0.005

    # Indicators
    donchian_length: int = 20
    ema_length: int = 200
    adx_length: int = 14
    adx_min: float = 20.0
    atr_length: int = 14

    # Risk
    sl_atr_mult: float = 1.5
    tp_atr_mult: float = 3.0
    max_hold_bars: int = 48

    initial_capital: float = 1000.0


@dataclass
class VolBreakoutResult:
    trades: pd.DataFrame
    summary: Dict[str, float]


def _apply_slippage(price: float, side: str, slippage_rate: float, is_entry: bool) -> float:
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


def add_indicators(df: pd.DataFrame, cfg: VolBreakoutConfig) -> pd.DataFrame:
    import pandas_ta as ta

    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")

    out = df.copy()
    out["EMA"] = ta.ema(out["close"], length=cfg.ema_length)
    out["ATR"] = ta.atr(out["high"], out["low"], out["close"], length=cfg.atr_length)

    adx = ta.adx(out["high"], out["low"], out["close"], length=cfg.adx_length)
    adx_col = next((c for c in adx.columns if str(c).startswith("ADX_")), None)
    if not adx_col:
        raise ValueError(f"ADX column not found in: {list(adx.columns)}")
    out["ADX"] = adx[adx_col]

    # Donchian channels (shifted to avoid lookahead)
    out["DONCH_H"] = out["high"].rolling(cfg.donchian_length).max().shift(1)
    out["DONCH_L"] = out["low"].rolling(cfg.donchian_length).min().shift(1)

    # Simple slope proxy for EMA trend: compare EMA now vs EMA N bars ago
    out["EMA_SLOPE"] = out["EMA"] - out["EMA"].shift(10)

    return out


def run_vol_breakout_backtest(df: pd.DataFrame, cfg: VolBreakoutConfig) -> VolBreakoutResult:
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must be indexed by time (DatetimeIndex)")
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")

    df = add_indicators(df, cfg)

    warmup = max(cfg.ema_length, cfg.atr_length, cfg.adx_length, cfg.donchian_length) + 5
    if len(df) <= warmup + 2:
        raise ValueError("Not enough candles for indicators")

    equity = cfg.initial_capital
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
        equity_curve[i] = equity

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

        row = df.iloc[i]
        if pd.isna(row["ADX"]) or float(row["ADX"]) < cfg.adx_min:
            continue
        if pd.isna(row["ATR"]) or pd.isna(row["DONCH_H"]) or pd.isna(row["DONCH_L"]) or pd.isna(row["EMA"]) or pd.isna(row["EMA_SLOPE"]):
            continue

        atr = float(row["ATR"])
        donch_h = float(row["DONCH_H"])
        donch_l = float(row["DONCH_L"])
        close = float(row["close"])

        ema_slope = float(row["EMA_SLOPE"])

        long_signal = (close > donch_h) and (ema_slope > 0)
        short_signal = (close < donch_l) and (ema_slope < 0)

        if not (long_signal or short_signal):
            continue

        side = "LONG" if long_signal else "SHORT"
        entry_open = float(df.iloc[i + 1]["open"])
        entry_price = _apply_slippage(entry_open, side, cfg.slippage_rate, is_entry=True)
        entry_i = i + 1

        if side == "LONG":
            sl = entry_price - cfg.sl_atr_mult * atr
            tp = entry_price + cfg.tp_atr_mult * atr
        else:
            sl = entry_price + cfg.sl_atr_mult * atr
            tp = entry_price - cfg.tp_atr_mult * atr

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

    return VolBreakoutResult(trades=trades_df, summary=summary)
