from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from signalbot.data import get_btc_ohlc
from signalbot.indicators import (
    bollinger_bands,
    detect_doji,
    detect_engulfing,
    detect_hammer,
    detect_shooting_star,
    ema,
    macd,
)
from signalbot.strategy import rsi_signal


def run(
    interval: str = "4h",
    period: int = 14,
    oversold: int = 30,
    overbought: int = 70,
    save: str | None = None,
    lookback_days: int = 365,
) -> pd.DataFrame:
    """
    Execute the RSI strategy pipeline and enrich OHLC data with indicators.
    """
    # Fetch market data
    df = get_btc_ohlc(interval=interval, lookback_days=lookback_days)

    # Primary signal calculation
    df = rsi_signal(df, period=period, oversold=oversold, overbought=overbought)
    if df.empty:
        raise ValueError("RSI strategy returned no data.")

    # Candlestick patterns
    df["doji"] = detect_doji(df)
    df["hammer"] = detect_hammer(df)
    df["engulfing"] = detect_engulfing(df)
    df["shooting_star"] = detect_shooting_star(df)

    # Bollinger Bands (upper/lower only for now)
    bb = bollinger_bands(df["close"], length=20, std=2.0)
    if not bb.empty:
        df["bb_upper"] = bb["upper"]
        df["bb_lower"] = bb["lower"]

    # EMAs
    df["ema_fast"] = ema(df["close"], length=9)
    df["ema_slow"] = ema(df["close"], length=21)

    # MACD
    macd_df = macd(df["close"], fast=12, slow=26, signal=9)
    if not macd_df.empty:
        df["macd"] = macd_df["macd"]
        df["macd_signal"] = macd_df["signal"]
        df["macd_histogram"] = macd_df["histogram"]

    # Enforce EMA logic (fast > slow for buys, fast < slow for sells)
    if "signal_strength" not in df.columns:
        df["signal_strength"] = "NEUTRAL"

    buy_mask = df["signal"].isin(["BUY", "STRONG BUY"])
    sell_mask = df["signal"].isin(["SELL", "STRONG SELL"])

    ema_bull = df["ema_fast"] > df["ema_slow"]
    ema_bear = df["ema_fast"] < df["ema_slow"]

    mismatch_buy = buy_mask & ~ema_bull
    mismatch_sell = sell_mask & ~ema_bear

    df.loc[mismatch_buy, "signal"] = "HOLD"
    df.loc[mismatch_buy, "signal_strength"] = "EMA MISMATCH"

    df.loc[mismatch_sell, "signal"] = "HOLD"
    df.loc[mismatch_sell, "signal_strength"] = "EMA MISMATCH"

    df.loc[(df["signal"] == "HOLD") & ema_bull & (df["signal_strength"] == "NEUTRAL"), "signal_strength"] = "BULLISH"
    df.loc[(df["signal"] == "HOLD") & ema_bear & (df["signal_strength"] == "NEUTRAL"), "signal_strength"] = "BEARISH"

    # Optional CSV export
    if save:
        save_path = Path(save).expanduser()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            df.to_csv(save_path)
        except OSError as exc:
            raise OSError(f"Failed to save CSV to '{save_path}': {exc}") from exc

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="BTCSignalBot — RSI Trading Signal Generator")
    parser.add_argument("--interval", default="4h", help="1m,5m,15m,30m,1h,4h,1d")
    parser.add_argument("--period", type=int, default=14)
    parser.add_argument("--oversold", type=int, default=30)
    parser.add_argument("--overbought", type=int, default=70)
    parser.add_argument("--lookback-days", type=int, default=365)
    parser.add_argument("--save", default="", help="Save enriched OHLC data to this CSV path")
    args = parser.parse_args()

    df = run(
        interval=args.interval,
        period=args.period,
        oversold=args.oversold,
        overbought=args.overbought,
        lookback_days=args.lookback_days,
        save=args.save or None,
    )

    last = df.iloc[-1]
    print("\nBTC Signal Snapshot")
    print("-------------------")
    print(f"Interval: {args.interval}")
    print(f"Timestamp: {last.name}")
    print(f"Close: ${last['close']:.2f}")
    print(f"RSI({args.period}): {last['rsi']:.2f}")
    print(f"Signal: {last['signal']} ({last.get('signal_strength', 'N/A')})")


if __name__ == "__main__":
    main()
