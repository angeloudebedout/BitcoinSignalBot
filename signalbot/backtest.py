from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd


TradeLog = pd.DataFrame


def backtest_signals(
    df: pd.DataFrame,
    *,
    initial_balance: float = 10_000.0,
    buy_signals: Iterable[str] = ("BUY", "STRONG BUY"),
    sell_signals: Iterable[str] = ("SELL", "STRONG SELL"),
    slippage: float = 0.0005,
    commission: float = 0.0007,
) -> Tuple[Dict[str, float], TradeLog, pd.Series]:
    """
    Backtest a long-only strategy using signal columns.

    Returns a tuple of (metrics dict, trades dataframe, equity series).
    """
    if initial_balance <= 0:
        raise ValueError("initial_balance must be > 0")

    empty_metrics = {
        "total_trades": 0,
        "win_rate": 0.0,
        "avg_gain": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "net_return": 0.0,
        "max_drawdown": 0.0,
        "final_balance": float(initial_balance),
        "gross_gain": 0.0,
        "gross_loss": 0.0,
        "best_trade": 0.0,
        "worst_trade": 0.0,
        "win_loss_ratio": 0.0,
        "initial_balance": float(initial_balance),
        "avg_hold_hours": 0.0,
        "median_hold_hours": 0.0,
        "exposure_pct": 0.0,
    }
    empty_trades = pd.DataFrame(
        columns=[
            "entry_time",
            "exit_time",
            "entry_price",
            "exit_price",
            "pnl_pct",
            "duration_hrs",
        ]
    )

    if df.empty:
        empty_equity = pd.Series(dtype=float, name="equity")
        return empty_metrics, empty_trades, empty_equity

    if not {"close", "signal"} <= set(df.columns):
        raise ValueError("DataFrame must include 'close' and 'signal' columns")

    data = df.sort_index().copy()
    closes = data["close"].astype(float)
    signals = data["signal"].astype(str).str.upper()

    buy_set = {s.upper() for s in buy_signals}
    sell_set = {s.upper() for s in sell_signals}

    cash = float(initial_balance)
    position = 0.0
    entry_price = None
    entry_time = None

    trade_log = []
    pnl_decimals = []

    equity_curve = []
    equity_timestamps = []
    peak_equity = cash
    max_drawdown = 0.0

    for timestamp, price, signal in zip(closes.index, closes.values, signals.values):
        price = float(price)
        if price <= 0:
            raise ValueError("Close prices must be positive for backtesting")

        if position == 0 and signal in buy_set:
            commission_fee = cash * commission
            cash_after_fee = cash - commission_fee
            effective_price = price * (1 + slippage)
            position = cash_after_fee / effective_price
            cash = cash_after_fee - position * effective_price
            entry_price = effective_price
            entry_time = timestamp

        elif position > 0 and signal in sell_set:
            effective_price = price * (1 - slippage)
            gross_proceeds = position * effective_price
            commission_fee = gross_proceeds * commission
            proceeds_net = gross_proceeds - commission_fee

            pnl_decimal = (effective_price - entry_price) / entry_price
            pnl_decimals.append(pnl_decimal)
            trade_log.append(
                {
                    "entry_time": entry_time,
                    "exit_time": timestamp,
                    "entry_price": entry_price,
                    "exit_price": effective_price,
                    "pnl_pct": pnl_decimal * 100.0,
                    "duration_hrs": (
                        (timestamp - entry_time).total_seconds() / 3600.0
                        if entry_time is not None
                        else 0.0
                    ),
                }
            )

            cash += proceeds_net
            position = 0.0
            entry_price = None
            entry_time = None

        equity = cash + position * price
        equity_curve.append(float(equity))
        equity_timestamps.append(timestamp)
        peak_equity = max(peak_equity, equity)
        drawdown = (equity - peak_equity) / peak_equity if peak_equity else 0.0
        max_drawdown = min(max_drawdown, drawdown)

    if position > 0 and entry_price is not None:
        final_timestamp = closes.index[-1]
        price = float(closes.iloc[-1])
        effective_price = price * (1 - slippage)
        gross_proceeds = position * effective_price
        commission_fee = gross_proceeds * commission
        proceeds_net = gross_proceeds - commission_fee

        pnl_decimal = (effective_price - entry_price) / entry_price
        pnl_decimals.append(pnl_decimal)
        trade_log.append(
            {
                "entry_time": entry_time,
                "exit_time": final_timestamp,
                "entry_price": entry_price,
                "exit_price": effective_price,
                "pnl_pct": pnl_decimal * 100.0,
                "duration_hrs": (
                    (final_timestamp - entry_time).total_seconds() / 3600.0
                    if entry_time is not None
                    else 0.0
                ),
            }
        )

        cash += proceeds_net
        position = 0.0
        entry_price = None
        entry_time = None
        if equity_curve:
            equity_curve[-1] = float(cash)

    final_equity = cash

    total_trades = len(pnl_decimals)
    wins = [p for p in pnl_decimals if p > 0]
    losses = [p for p in pnl_decimals if p <= 0]

    win_rate = (len(wins) / total_trades * 100.0) if total_trades else 0.0
    avg_gain = np.mean(wins) * 100.0 if wins else 0.0
    avg_loss = np.mean(losses) * 100.0 if losses else 0.0
    profit_factor = (
        abs(np.sum(wins) / np.sum(losses)) if losses and np.sum(losses) != 0 else np.inf if wins else 0.0
    )
    net_return = (final_equity / initial_balance - 1.0) * 100.0

    gross_gain_pct = sum(p for p in pnl_decimals if p > 0) * 100.0
    gross_loss_pct = abs(sum(p for p in pnl_decimals if p < 0)) * 100.0
    best_trade = max(pnl_decimals) * 100.0 if pnl_decimals else 0.0
    worst_trade = min(pnl_decimals) * 100.0 if pnl_decimals else 0.0
    win_loss_ratio = (
        len(wins) / len(losses) if losses else float("inf") if wins else 0.0
    )

    metrics = {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "avg_gain": avg_gain,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "net_return": net_return,
        "max_drawdown": max_drawdown * 100.0,
        "final_balance": final_equity,
        "gross_gain": gross_gain_pct,
        "gross_loss": gross_loss_pct,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "win_loss_ratio": win_loss_ratio,
        "initial_balance": float(initial_balance),
    }

    trades_df = (
        pd.DataFrame(trade_log, columns=empty_trades.columns)
        if trade_log
        else empty_trades.copy()
    )

    if not trades_df.empty:
        avg_hold = trades_df["duration_hrs"].mean()
        median_hold = trades_df["duration_hrs"].median()
    else:
        avg_hold = 0.0
        median_hold = 0.0

    metrics.update(
        {
            "avg_hold_hours": float(avg_hold),
            "median_hold_hours": float(median_hold),
        }
    )

    metrics = {
        key: float(value) if isinstance(value, (np.floating, np.float64, np.float32)) else value
        for key, value in metrics.items()
    }

    if equity_timestamps:
        equity_index = pd.Index(
            equity_timestamps,
            name=data.index.name or "timestamp",
        )
        equity_series = pd.Series(equity_curve, index=equity_index, name="equity")
    else:
        equity_series = pd.Series(dtype=float, name="equity")

    total_hours = 0.0
    if equity_timestamps:
        time_span = equity_timestamps[-1] - equity_timestamps[0]
        total_hours = time_span.total_seconds() / 3600.0 if time_span.total_seconds() > 0 else 0.0
    exposure_pct = (
        trades_df["duration_hrs"].sum() / total_hours * 100.0
        if not trades_df.empty and total_hours > 0
        else 0.0
    )
    metrics["exposure_pct"] = float(exposure_pct)

    return metrics, trades_df, equity_series
