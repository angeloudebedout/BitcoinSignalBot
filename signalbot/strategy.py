from __future__ import annotations

import pandas as pd

from .indicators import ema, macd, rsi


def rsi_signal(
    df: pd.DataFrame,
    period: int = 14,
    oversold: int = 30,
    overbought: int = 70,
    ema_fast_period: int = 12,
    ema_slow_period: int = 26,
) -> pd.DataFrame:
    """
    Compute RSI crossover signals and enrich the frame with supporting indicators.

    BUY and SELL triggers occur when RSI crosses out of oversold/overbought.
    MACD and EMA agreement upgrades those signals to STRONG variants.
    """
    if df.empty:
        return df.copy()

    out = df.copy().sort_index()

    # Core indicator suite
    out["rsi"] = rsi(out["close"], period=period)

    ema_fast = ema(out["close"], length=ema_fast_period).reindex(out.index)
    ema_slow = ema(out["close"], length=ema_slow_period).reindex(out.index)
    out["ema_fast"] = ema_fast
    out["ema_slow"] = ema_slow

    macd_df = macd(out["close"], fast=ema_fast_period, slow=ema_slow_period, signal=9)
    if macd_df.empty:
        macd_df = pd.DataFrame(index=out.index, columns=["macd", "signal", "histogram"], dtype=float)
    else:
        macd_df = macd_df.reindex(out.index)

    out["macd"] = macd_df["macd"]
    out["macd_signal"] = macd_df["signal"]
    out["macd_histogram"] = macd_df["histogram"]

    prev_rsi = out["rsi"].shift(1)
    rsi_cross_up = (prev_rsi < oversold) & (out["rsi"] >= oversold)
    rsi_cross_down = (prev_rsi > overbought) & (out["rsi"] <= overbought)

    prev_macd = out["macd"].shift(1)
    prev_signal = out["macd_signal"].shift(1)
    macd_cross_up = (prev_macd < prev_signal) & (out["macd"] > out["macd_signal"])
    macd_cross_down = (prev_macd > prev_signal) & (out["macd"] < out["macd_signal"])

    ema_uptrend = out["ema_fast"] > out["ema_slow"]
    ema_downtrend = out["ema_fast"] < out["ema_slow"]

    out["signal"] = "HOLD"
    out["signal_strength"] = "NEUTRAL"

    buy_mask = rsi_cross_up & ema_uptrend & out["rsi"].notna() & prev_rsi.notna()
    sell_mask = rsi_cross_down & ema_downtrend & out["rsi"].notna() & prev_rsi.notna()

    out.loc[buy_mask, "signal"] = "BUY"
    out.loc[sell_mask, "signal"] = "SELL"
    out.loc[buy_mask, "signal_strength"] = "BUY"
    out.loc[sell_mask, "signal_strength"] = "SELL"

    strong_buy = buy_mask & macd_cross_up
    strong_sell = sell_mask & macd_cross_down

    out.loc[strong_buy, "signal"] = "STRONG BUY"
    out.loc[strong_sell, "signal"] = "STRONG SELL"
    out.loc[strong_buy, "signal_strength"] = "BULLISH"
    out.loc[strong_sell, "signal_strength"] = "BEARISH"

    # Simple divergence heuristic for additional context
    out["divergence"] = None
    price = out["close"]
    rsi_vals = out["rsi"]

    higher_high = (price > price.shift(1)) & (price.shift(1) > price.shift(2))
    lower_high = (rsi_vals < rsi_vals.shift(1)) & (rsi_vals.shift(1) < rsi_vals.shift(2))
    bearish_div = higher_high & lower_high

    lower_low = (price < price.shift(1)) & (price.shift(1) < price.shift(2))
    higher_low = (rsi_vals > rsi_vals.shift(1)) & (rsi_vals.shift(1) > rsi_vals.shift(2))
    bullish_div = lower_low & higher_low

    out.loc[bearish_div, "divergence"] = "BEARISH"
    out.loc[bullish_div, "divergence"] = "BULLISH"

    return out
