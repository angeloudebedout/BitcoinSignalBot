from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from signalbot.strategy import rsi_signal


class RSISignalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_df = pd.DataFrame(
            {
                "open": [100, 101, 102, 103],
                "high": [101, 102, 103, 104],
                "low": [99, 100, 101, 102],
                "close": [100, 101, 102, 103],
                "volume": [1, 1, 1, 1],
            },
            index=pd.date_range("2023-01-01", periods=4, freq="h"),
        )

    def test_buy_sell_signals_vectorized(self) -> None:
        fake_rsi = pd.Series([25, 80, 65, 60], index=self.base_df.index)
        fake_macd = pd.DataFrame(
            {
                "macd": [-0.1, 0.2, 0.05, -0.1],
                "signal": [0.0, 0.1, 0.1, -0.05],
                "histogram": [-0.1, 0.1, -0.05, -0.05],
            },
            index=self.base_df.index,
        )

        def fake_ema(series, length):
            data = {
                12: pd.Series([1.2, 1.4, 0.8, 0.6], index=series.index),
                26: pd.Series([1.1, 1.3, 0.9, 0.7], index=series.index),
            }
            return data[length]

        with patch("signalbot.strategy.rsi", return_value=fake_rsi), patch(
            "signalbot.strategy.macd", return_value=fake_macd
        ), patch("signalbot.strategy.ema", side_effect=fake_ema):
            out = rsi_signal(self.base_df, oversold=30, overbought=70)

        self.assertEqual(out["signal"].tolist(), ["HOLD", "STRONG BUY", "STRONG SELL", "HOLD"])

    def test_empty_dataframe_returns_copy(self) -> None:
        empty = self.base_df.iloc[0:0]
        out = rsi_signal(empty)

        self.assertTrue(out.empty)
        self.assertIsNot(out, empty)

    def test_dataframe_sorted_by_index(self) -> None:
        unsorted = self.base_df.sort_index(ascending=False)
        fake_rsi = pd.Series([25, 80, 65, 60], index=self.base_df.index)
        fake_macd = pd.DataFrame(
            {
                "macd": [-0.1, 0.2, 0.05, -0.1],
                "signal": [0.0, 0.1, 0.1, -0.05],
                "histogram": [-0.1, 0.1, -0.05, -0.05],
            },
            index=self.base_df.index,
        )

        def fake_ema(series, length):
            data = {
                12: pd.Series([1.2, 1.4, 0.8, 0.6], index=series.index),
                26: pd.Series([1.1, 1.3, 0.9, 0.7], index=series.index),
            }
            return data[length]

        with patch("signalbot.strategy.rsi", return_value=fake_rsi), patch(
            "signalbot.strategy.macd", return_value=fake_macd
        ), patch("signalbot.strategy.ema", side_effect=fake_ema):
            out = rsi_signal(unsorted, oversold=30, overbought=70)

        self.assertTrue(out.index.is_monotonic_increasing)
        self.assertEqual(out["signal"].tolist(), ["HOLD", "STRONG BUY", "STRONG SELL", "HOLD"])


if __name__ == "__main__":
    unittest.main()
