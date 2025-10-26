from __future__ import annotations

import unittest

import pandas as pd

from signalbot.backtest import backtest_signals


class BacktestSignalsTests(unittest.TestCase):
    def test_metrics_for_profitable_trade(self) -> None:
        df = pd.DataFrame(
            {
                "close": [100.0, 110.0, 115.0, 90.0, 88.0],
                "signal": ["HOLD", "BUY", "SELL", "BUY", "SELL"],
            },
            index=pd.date_range("2023-01-01", periods=5, freq="h"),
        )

        metrics, trades, equity_curve = backtest_signals(df, initial_balance=1000.0)

        self.assertEqual(metrics["total_trades"], 2)
        self.assertAlmostEqual(metrics["win_rate"], 50.0)
        self.assertGreater(metrics["net_return"], 0.0)
        self.assertLessEqual(metrics["max_drawdown"], 0.0)
        self.assertEqual(len(trades), 2)
        self.assertFalse(equity_curve.empty)
        self.assertEqual(metrics["initial_balance"], 1000.0)

    def test_initial_balance_validation(self) -> None:
        df = pd.DataFrame({"close": [100.0], "signal": ["HOLD"]})
        with self.assertRaises(ValueError):
            backtest_signals(df, initial_balance=0)

    def test_empty_dataframe_returns_zero_metrics(self) -> None:
        df = pd.DataFrame(columns=["close", "signal"])
        metrics, trades, equity_curve = backtest_signals(df, initial_balance=500.0)

        self.assertEqual(metrics["total_trades"], 0)
        self.assertEqual(metrics["win_rate"], 0.0)
        self.assertEqual(metrics["net_return"], 0.0)
        self.assertEqual(metrics["max_drawdown"], 0.0)
        self.assertTrue(trades.empty)
        self.assertTrue(equity_curve.empty)


if __name__ == "__main__":
    unittest.main()
