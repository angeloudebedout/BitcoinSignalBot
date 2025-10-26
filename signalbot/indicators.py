from __future__ import annotations

import numpy as np
import pandas as pd


# ────────────────────────────────────────────────
# Core Technical Indicators
# ────────────────────────────────────────────────
def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Wilder's RSI using exponential weighting (a.k.a. RMA).
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def ema(series: pd.Series, length: int = 14) -> pd.Series:
    """
    Exponential moving average.
    """
    return series.ewm(span=length, adjust=False).mean()


def bollinger_bands(series: pd.Series, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    """
    Compute upper/middle/lower Bollinger Bands.
    """
    middle = series.rolling(window=length, min_periods=length).mean()
    deviation = series.rolling(window=length, min_periods=length).std(ddof=0)
    upper = middle + std * deviation
    lower = middle - std * deviation
    return pd.DataFrame({"upper": upper, "middle": middle, "lower": lower})


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    MACD (Moving Average Convergence Divergence) with histogram.
    """
    ema_fast = ema(series, length=fast)
    ema_slow = ema(series, length=slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return pd.DataFrame(
        {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram,
        }
    )


# ────────────────────────────────────────────────
# Candlestick Pattern Detection Helpers
# ────────────────────────────────────────────────
def detect_doji(df: pd.DataFrame, body_ratio: float = 0.1) -> pd.Series:
    body = (df["close"] - df["open"]).abs()
    candle_range = (df["high"] - df["low"]).replace(0, np.nan)

    is_doji = (candle_range.notna()) & (body <= candle_range * body_ratio)
    return is_doji.fillna(False).astype(int)


def detect_hammer(df: pd.DataFrame, shadow_ratio: float = 2.0) -> pd.Series:
    high, low = df["high"], df["low"]
    open_, close = df["open"], df["close"]

    body = (close - open_).abs()
    candle_range = (high - low).replace(0, np.nan)

    upper_shadow = high - pd.concat([open_, close], axis=1).max(axis=1)
    lower_shadow = pd.concat([open_, close], axis=1).min(axis=1) - low

    near_high = upper_shadow <= body
    long_lower_shadow = lower_shadow >= shadow_ratio * body
    small_body = body <= candle_range * 0.3

    mask = candle_range.notna()
    is_hammer = long_lower_shadow & near_high & small_body & mask
    return is_hammer.fillna(False).astype(int)


def detect_shooting_star(df: pd.DataFrame, shadow_ratio: float = 2.0) -> pd.Series:
    high, low = df["high"], df["low"]
    open_, close = df["open"], df["close"]

    body = (close - open_).abs()
    candle_range = (high - low).replace(0, np.nan)

    upper_shadow = high - pd.concat([open_, close], axis=1).max(axis=1)
    lower_shadow = pd.concat([open_, close], axis=1).min(axis=1) - low

    near_low = lower_shadow <= body
    long_upper_shadow = upper_shadow >= shadow_ratio * body
    small_body = body <= candle_range * 0.3

    mask = candle_range.notna()
    is_shooting_star = long_upper_shadow & near_low & small_body & mask
    return is_shooting_star.fillna(False).astype(int)


def detect_engulfing(df: pd.DataFrame) -> pd.Series:
    open_, close = df["open"], df["close"]
    prev_open, prev_close = open_.shift(1), close.shift(1)

    bullish = (
        (close > open_)
        & (prev_close < prev_open)
        & (close >= prev_open)
        & (open_ <= prev_close)
    )

    bearish = (
        (close < open_)
        & (prev_close > prev_open)
        & (open_ >= prev_close)
        & (close <= prev_open)
    )

    result = pd.Series(0, index=df.index, dtype="int8")
    result.loc[bullish] = 1
    result.loc[bearish] = -1
    return result
