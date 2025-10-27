from __future__ import annotations

from typing import Any, Dict
from datetime import datetime, timedelta

import logging
import math

import numpy as np
import pandas as pd
import requests

try:  # Optional dependency – handled gracefully if missing
    from pycoingecko import CoinGeckoAPI
except ImportError:  # pragma: no cover - exercised indirectly
    CoinGeckoAPI = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Initialize CoinGecko API client when available
cg: CoinGeckoAPI | None = CoinGeckoAPI() if CoinGeckoAPI is not None else None

# Map display intervals to days that provide sufficient lookback.
_PERIOD_BY_INTERVAL: Dict[str, str] = {
    "1m": "7d",
    "2m": "60d",
    "5m": "60d",
    "15m": "60d",
    "30m": "60d",
    "1h": "730d",
    "4h": "730d",
    "1d": "365d",
    "1w": "730d",
    "1wk": "730d",
    "1mo": "max",
    "1y": "max",
}

# Fetch lower timeframe data for custom aggregation where yfinance lacks support.
_FETCH_INTERVAL_BY_INTERVAL: Dict[str, str] = {
    "4h": "1h",
    "1w": "1d",
    "1wk": "1d",
    "1mo": "1d",
    "1y": "1d",
}

# Local resampling rules to rebuild the requested timeframe.
_RESAMPLE_RULES: Dict[str, str] = {
    "4h": "4h",
    "1w": "1W",
    "1wk": "1W",
    "1mo": "1M",
    "1y": "1Y",
}


def get_btc_ohlc(interval: str = "4h", lookback_days: int = 365) -> pd.DataFrame:
    """
    Fetch BTC-USD OHLCV data from CoinGecko, optionally resampling to
    higher intervals and trimming to the requested lookback window.

    When CoinGecko is unreachable or the optional dependency is unavailable,
    a deterministic synthetic dataset is produced so the application can
    operate offline (useful for tests and restricted environments).
    """
    # Convert interval to days for CoinGecko API
    interval_map = {
        "1d": 1,
        "4h": 1 / 6,
        "1h": 1 / 24,
        "15m": 1 / 96,
        "5m": 1 / 288,
        "1m": 1 / 1440,
        "1wk": 7,
        "1mo": 30,
        "1y": 365,
    }
    
    norm_interval = interval.lower()
    if norm_interval not in interval_map:
        supported = ", ".join(sorted(interval_map))
        raise ValueError(f"Unsupported interval '{interval}'. Choose from: {supported}.")

    if lookback_days < 1:
        raise ValueError("lookback_days must be at least 1.")

    # Calculate timestamps
    end_time = datetime.now()
    start_time = end_time - timedelta(days=lookback_days)
    
    # Convert timestamps to Unix timestamps in seconds
    from_timestamp = int(start_time.timestamp())
    to_timestamp = int(end_time.timestamp())
    
    market_data: dict[str, Any] | None = None
    fetch_error: Exception | None = None

    if cg is not None:
        try:
            market_data = cg.get_coin_market_chart_range_by_id(
                id="bitcoin",
                vs_currency="usd",
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
            )
        except Exception as exc:  # pragma: no cover - network dependent
            fetch_error = exc
            logger.debug("CoinGecko client failed, will try HTTP fallback: %s", exc)
    else:
        fetch_error = ImportError("pycoingecko is not installed")

    if market_data is None:
        try:
            market_data = _download_coingecko_market_chart(from_timestamp, to_timestamp)
        except Exception as exc:  # pragma: no cover - network dependent
            fetch_error = exc if fetch_error is None else exc
            logger.debug("Direct HTTP fetch failed: %s", exc)

    if market_data is not None:
        try:
            df = _build_ohlcv_frame(market_data, norm_interval)
            df.attrs["data_source"] = "coingecko"
            return df
        except Exception as exc:
            fetch_error = exc
            logger.debug("Failed to build OHLCV data from response: %s", exc)

    fallback = _generate_synthetic_ohlc(norm_interval, lookback_days)
    fallback.attrs["data_source"] = "synthetic"
    if fetch_error is not None:
        fallback.attrs["data_error"] = str(fetch_error)
        logger.warning(
            "Falling back to synthetic BTC data due to fetch issue: %s",
            fetch_error,
        )
    else:
        logger.warning("Falling back to synthetic BTC data (no market data available).")
    return fallback


def _download_coingecko_market_chart(from_ts: int, to_ts: int) -> dict[str, Any]:
    """
    Lightweight HTTP fallback when pycoingecko is unavailable.
    """
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
    params = {"vs_currency": "usd", "from": from_ts, "to": to_ts}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _build_ohlcv_frame(market_data: dict[str, Any], interval: str) -> pd.DataFrame:
    """
    Convert CoinGecko market data into an OHLCV dataframe.
    """
    if "prices" not in market_data or "total_volumes" not in market_data:
        raise ValueError("CoinGecko response missing expected keys.")

    prices_df = pd.DataFrame(market_data["prices"], columns=["timestamp", "price"])
    volume_df = pd.DataFrame(market_data["total_volumes"], columns=["timestamp", "volume"])

    prices_df["timestamp"] = pd.to_datetime(prices_df["timestamp"], unit="ms")
    volume_df["timestamp"] = pd.to_datetime(volume_df["timestamp"], unit="ms")

    prices_df = prices_df.set_index("timestamp").sort_index()
    volume_df = volume_df.set_index("timestamp").sort_index()

    combined = pd.DataFrame(index=prices_df.index)
    combined["price"] = prices_df["price"]
    combined["volume"] = volume_df.reindex(prices_df.index, method="ffill")["volume"]

    resample_map = {
        "1m": "1min",
        "2m": "2min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1H",
        "4h": "4H",
        "1d": "1D",
        "1w": "1W",
        "1wk": "1W",
        "1mo": "1M",
        "1y": "1Y",
    }

    rule = resample_map.get(interval)
    if rule:
        price_ohlc = combined["price"].resample(rule, label="right", closed="right").ohlc()
        volume_resampled = combined["volume"].resample(rule, label="right", closed="right").sum()
        df = price_ohlc.join(volume_resampled.rename("volume"), how="inner")
    else:
        df = combined.rename(columns={"price": "close"})
        df["open"] = df["close"]
        df["high"] = df["close"]
        df["low"] = df["close"]

    df = df[["open", "high", "low", "close", "volume"]].dropna()

    if df.empty:
        raise ValueError("No BTC price data returned for the requested interval.")

    return df


def _generate_synthetic_ohlc(interval: str, lookback_days: int, seed: int = 42) -> pd.DataFrame:
    """
    Build a pseudo-random OHLCV dataframe when live data is unavailable.
    """
    freq_map = {
        "1m": "1min",
        "2m": "2min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1w": "7d",
        "1wk": "7d",
        "1mo": "30d",
        "1y": "365d",
    }
    step_map = {
        "1m": pd.Timedelta(minutes=1),
        "2m": pd.Timedelta(minutes=2),
        "5m": pd.Timedelta(minutes=5),
        "15m": pd.Timedelta(minutes=15),
        "30m": pd.Timedelta(minutes=30),
        "1h": pd.Timedelta(hours=1),
        "4h": pd.Timedelta(hours=4),
        "1d": pd.Timedelta(days=1),
        "1w": pd.Timedelta(weeks=1),
        "1wk": pd.Timedelta(weeks=1),
        "1mo": pd.Timedelta(days=30),
        "1y": pd.Timedelta(days=365),
    }

    norm_interval = interval.lower()
    if norm_interval not in freq_map:
        raise ValueError(f"Unsupported interval '{interval}' for synthetic data.")

    step = step_map[norm_interval]
    total_minutes = max(1, lookback_days) * 24 * 60
    step_minutes = max(step.total_seconds() / 60.0, 1.0)
    periods = max(int(math.ceil(total_minutes / step_minutes)), 60)

    end = pd.Timestamp.utcnow().floor("min")
    freq = freq_map[norm_interval]
    index = pd.date_range(end=end, periods=periods, freq=freq)

    rng = np.random.default_rng(seed)
    base_price = 30_000.0
    drift = rng.normal(0.0001, 0.0005, size=periods)
    volatility = rng.normal(0, 0.008, size=periods)
    log_returns = drift + volatility
    close = base_price * np.exp(np.cumsum(log_returns))

    open_ = close.copy()
    open_[1:] = close[:-1]
    open_[0] = close[0] * (1 + rng.normal(0, 0.002))

    body = np.abs(close - open_)
    wick = np.maximum(body, base_price * rng.random(periods) * 0.01)
    high = np.maximum(open_, close) + wick
    low = np.maximum(0.01, np.minimum(open_, close) - wick)

    volume = rng.lognormal(mean=12, sigma=0.35, size=periods)

    df = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=index,
    )
    df.attrs["data_source"] = "synthetic"
    return df
