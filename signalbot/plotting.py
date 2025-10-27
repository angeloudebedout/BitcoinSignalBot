from __future__ import annotations

from typing import Any

import pandas as pd

try:  # Plotly is optional in certain environments
    import plotly.graph_objects as go  # type: ignore[import-untyped]
    from plotly.subplots import make_subplots  # type: ignore[import-untyped]

    PLOTLY_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only when plotly is absent
    go = None  # type: ignore[assignment]
    make_subplots = None  # type: ignore[assignment]
    PLOTLY_AVAILABLE = False


def plot_btc_chart(
    df: pd.DataFrame,
    interval: str,
    period: int,
    oversold: float,
    overbought: float,
    *,
    show_signals: bool = True,
    show_bbands: bool = True,
    show_emas: bool = True,
    show_divergence: bool = True,
    show_backtest_trades: bool = False,
    trades_df: pd.DataFrame | None = None,
    show_rsi: bool = True,
    show_macd: bool = True,
) -> "go.Figure":
    """
    Build a layered Plotly figure with candlesticks plus optional overlays.
    """
    if not PLOTLY_AVAILABLE:  # pragma: no cover - triggered when plotly missing
        raise RuntimeError("Plotly is not installed; install plotly to render interactive charts.")

    secondary_panels: list[str] = []
    if show_rsi:
        secondary_panels.append("rsi")
    if show_macd:
        secondary_panels.append("macd")

    row_specs = [[{"type": "xy"}]]
    row_heights = []
    if secondary_panels:
        price_height = 0.6 if len(secondary_panels) == 2 else 0.72
        row_heights.append(price_height)
        shared_height = (1 - price_height) / len(secondary_panels)
        row_heights.extend([shared_height] * len(secondary_panels))
        row_specs.extend([[{"type": "xy"}] for _ in secondary_panels])
    else:
        row_heights.append(1.0)

    base_height = 580
    fig_height = base_height + (220 * len(secondary_panels))

    fig = make_subplots(
        rows=len(row_specs),
        cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.08 if len(row_specs) > 1 else 0.02,
        specs=row_specs,
    )

    price_row = 1
    rsi_row = None
    macd_row = None
    for idx, panel in enumerate(secondary_panels, start=2):
        if panel == "rsi":
            rsi_row = idx
        elif panel == "macd":
            macd_row = idx

    if df.empty:
        raise ValueError("Cannot plot BTC chart with an empty dataframe.")

    # Compute Heikin-Ashi candles for a smoother price representation
    ha_close = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    ha_open = ha_close.copy()
    ha_open_values = ha_open.to_numpy()
    ha_close_values = ha_close.to_numpy()
    source_open = df["open"].to_numpy()
    source_close = df["close"].to_numpy()
    ha_open_values[0] = (source_open[0] + source_close[0]) / 2
    if len(ha_open_values) > 1:
        ha_open_values[1:] = (ha_open_values[:-1] + ha_close_values[:-1]) / 2
    ha_open = pd.Series(ha_open_values, index=df.index, name="ha_open")
    ha_high = pd.concat(
        (df["high"], ha_open, ha_close.rename("ha_close")), axis=1
    ).max(axis=1)
    ha_low = pd.concat(
        (df["low"], ha_open, ha_close.rename("ha_close")), axis=1
    ).min(axis=1)

    # Price candlesticks (Heikin-Ashi)
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=ha_open,
            high=ha_high,
            low=ha_low,
            close=ha_close,
            name="Heikin-Ashi",
            legendgroup="price",
            showlegend=True,
            increasing=dict(line=dict(color="#16a34a", width=1.2), fillcolor="rgba(34,197,94,0.68)"),
            decreasing=dict(line=dict(color="#ef4444", width=1.2), fillcolor="rgba(248,113,113,0.68)"),
            whiskerwidth=0.4,
            opacity=0.9,
        ),
        row=price_row,
        col=1,
    )

    # Buy/Sell markers
    if show_signals and "signal" in df.columns:
        buys = df[df["signal"].str.contains("BUY", na=False)]
        sells = df[df["signal"].str.contains("SELL", na=False)]

        fig.add_trace(
            go.Scatter(
                x=buys.index,
                y=ha_close.reindex(buys.index),
                mode="markers",
                marker=dict(symbol="triangle-up", color="#22c55e", size=10),
                name="Buy",
            ),
            row=price_row,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=sells.index,
                y=ha_close.reindex(sells.index),
                mode="markers",
                marker=dict(symbol="triangle-down", color="#ef4444", size=10),
                name="Sell",
            ),
            row=price_row,
            col=1,
        )

    # Backtest trade markers
    if show_backtest_trades and trades_df is not None and not trades_df.empty:
        fig.add_trace(
            go.Scatter(
                x=trades_df["entry_time"],
                y=ha_close.reindex(trades_df["entry_time"]).fillna(trades_df["entry_price"]),
                mode="markers",
                marker=dict(symbol="triangle-up", color="#bef264", size=12),
                name="Backtest Entry",
            ),
            row=price_row,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=trades_df["exit_time"],
                y=ha_close.reindex(trades_df["exit_time"]).fillna(trades_df["exit_price"]),
                mode="markers",
                marker=dict(symbol="triangle-down", color="#facc15", size=12),
                name="Backtest Exit",
            ),
            row=price_row,
            col=1,
        )

    # Divergence highlights
    if show_divergence and "divergence" in df.columns:
        bull = df[df["divergence"] == "BULLISH"]
        bear = df[df["divergence"] == "BEARISH"]

        if not bull.empty:
            fig.add_trace(
                go.Scatter(
                    x=bull.index,
                    y=ha_close.reindex(bull.index),
                    mode="markers",
                    marker=dict(symbol="star", color="#22c55e", size=12),
                    name="Bullish Divergence",
                ),
                row=price_row,
                col=1,
            )
        if not bear.empty:
            fig.add_trace(
                go.Scatter(
                    x=bear.index,
                    y=ha_close.reindex(bear.index),
                    mode="markers",
                    marker=dict(symbol="star", color="#f97316", size=12),
                    name="Bearish Divergence",
                ),
                row=price_row,
                col=1,
            )

    # Bollinger Bands
    if show_bbands and {"bb_upper", "bb_lower"} <= set(df.columns):
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["bb_upper"],
                mode="lines",
                line=dict(color="#38bdf8", dash="dot"),
                name="Bollinger Upper",
            ),
            row=price_row,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["bb_lower"],
                mode="lines",
                line=dict(color="#38bdf8", dash="dot"),
                name="Bollinger Lower",
            ),
            row=price_row,
            col=1,
        )

    # EMAs
    if show_emas and {"ema_fast", "ema_slow"} <= set(df.columns):
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["ema_fast"],
                mode="lines",
                line=dict(color="#fb7185", width=1.5),
                name="EMA Fast",
            ),
            row=price_row,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["ema_slow"],
                mode="lines",
                line=dict(color="#a855f7", width=1.5),
                name="EMA Slow",
            ),
            row=price_row,
            col=1,
        )

    # RSI subplot
    if show_rsi and rsi_row and "rsi" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["rsi"],
                mode="lines",
                line=dict(color="#f97316"),
                name=f"RSI ({period})",
            ),
            row=rsi_row,
            col=1,
        )
        fig.add_hline(y=overbought, line=dict(color="#ef4444", dash="dot"), row=rsi_row, col=1)
        fig.add_hline(y=oversold, line=dict(color="#22c55e", dash="dot"), row=rsi_row, col=1)

    # MACD subplot
    if show_macd and macd_row and {"macd", "macd_signal"} <= set(df.columns):
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["macd"],
                mode="lines",
                line=dict(color="#22c55e"),
                name="MACD",
            ),
            row=macd_row,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["macd_signal"],
                mode="lines",
                line=dict(color="#ef4444"),
                name="Signal",
            ),
            row=macd_row,
            col=1,
        )

    fig.update_layout(
        height=fig_height,
        title=dict(
            text=f"BTC/USD · {interval.upper()} Heikin-Ashi",
            x=0.01,
            xanchor="left",
            font=dict(size=22, color="#e2e8f0", family="Inter, sans-serif"),
        ),
        paper_bgcolor="#050c1a",
        plot_bgcolor="#0b152c",
        font=dict(family="Inter, sans-serif", color="#e2e8f0"),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.99,
            font=dict(size=12),
            bgcolor="rgba(8,17,36,0.78)",
            bordercolor="rgba(148,163,184,0.35)",
            borderwidth=1,
            itemclick="toggle",
            itemdoubleclick="toggleothers",
        ),
        margin=dict(l=24, r=120, t=70, b=40),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#121f3b", font=dict(color="#e2e8f0")),
    )

    subplot_backgrounds: list[tuple[int, str]] = [
        (price_row, "rgba(11,23,45,0.86)"),
    ]
    if rsi_row:
        subplot_backgrounds.append((rsi_row, "rgba(18,33,60,0.78)"))
    if macd_row:
        subplot_backgrounds.append((macd_row, "rgba(16,28,52,0.82)"))

    for row_idx, color in subplot_backgrounds:
        axis_key = "yaxis" if row_idx == 1 else f"yaxis{row_idx}"
        axis = getattr(fig.layout, axis_key, None)
        domain = getattr(axis, "domain", None)
        if domain:
            fig.add_shape(
                type="rect",
                x0=0,
                x1=1,
                y0=domain[0],
                y1=domain[1],
                xref="paper",
                yref="paper",
                fillcolor=color,
                layer="below",
                line_width=0,
            )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        color="#9ca3c0",
        spikemode="across",
        spikecolor="#38bdf8",
        spikethickness=1,
        showspikes=True,
        spikesnap="cursor",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#15233f",
        zeroline=False,
        color="#9ca3c0",
        spikemode="across",
        spikecolor="#38bdf8",
        spikethickness=1,
        showspikes=True,
    )

    fig.update_yaxes(
        title_text="BTC / USD (HA)",
        title_font=dict(color="#cbd5f5", size=12),
        tickprefix="$",
        row=price_row,
        col=1,
    )
    fig.update_xaxes(
        showgrid=False,
        row=price_row,
        col=1,
    )

    if rsi_row:
        fig.update_yaxes(
            title_text="RSI",
            title_font=dict(color="#cbd5f5", size=11),
            range=[0, 100],
            row=rsi_row,
            col=1,
        )
        fig.add_hrect(
            y0=0,
            y1=oversold,
            fillcolor="rgba(34,197,94,0.12)",
            layer="below",
            line_width=0,
            row=rsi_row,
            col=1,
        )
        fig.add_hrect(
            y0=overbought,
            y1=100,
            fillcolor="rgba(239,68,68,0.12)",
            layer="below",
            line_width=0,
            row=rsi_row,
            col=1,
        )
        fig.update_xaxes(
            showgrid=True,
            gridcolor="#1c2c4f",
            row=rsi_row,
            col=1,
        )
    if macd_row:
        fig.update_yaxes(
            title_text="MACD",
            title_font=dict(color="#cbd5f5", size=11),
            zeroline=True,
            zerolinecolor="#60a5fa",
            zerolinewidth=1,
            row=macd_row,
            col=1,
        )
        fig.update_xaxes(
            showgrid=True,
            gridcolor="#1c2c4f",
            row=macd_row,
            col=1,
        )
        fig.add_hline(
            y=0,
            line=dict(color="#60a5fa", width=1, dash="dot"),
            row=macd_row,
            col=1,
        )

    # Highlight the latest closing price similar to trading terminals
    if not df.empty:
        last_close = ha_close.iloc[-1]
        fig.add_annotation(
            x=1.01,
            y=last_close,
            xref="paper",
            yref="y1",
            text=f"${last_close:,.2f}",
            font=dict(color="#e2e8f0", size=12, family="Inter, sans-serif"),
            bgcolor="#1f2937",
            bordercolor="#38bdf8",
            borderwidth=1,
            borderpad=4,
            xanchor="left",
            showarrow=False,
        )

    fig.update_layout(showlegend=False)
    return fig


def plot_equity_curve(equity: pd.Series, trades_df: pd.DataFrame | None = None) -> "go.Figure":
    """
    Plot the equity curve with optional entry/exit markers.
    """
    if not PLOTLY_AVAILABLE:  # pragma: no cover - triggered when plotly missing
        raise RuntimeError("Plotly is not installed; install plotly to render interactive charts.")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=equity.index,
            y=equity.values,
            mode="lines",
            line=dict(color="#0ea5e9", width=2.2),
            name="Equity",
        )
    )

    if trades_df is not None and not trades_df.empty:
        entry_equity = equity.reindex(trades_df["entry_time"]).ffill()
        exit_equity = equity.reindex(trades_df["exit_time"]).ffill()

        fig.add_trace(
            go.Scatter(
                x=trades_df["entry_time"],
                y=entry_equity.values,
                mode="markers",
                marker=dict(symbol="triangle-up", color="#34d399", size=9),
                name="Entry",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=trades_df["exit_time"],
                y=exit_equity.values,
                mode="markers",
                marker=dict(symbol="triangle-down", color="#f87171", size=9),
                name="Exit",
            )
        )

    fig.update_layout(
        height=420,
        title="Simulated Equity Curve",
        xaxis_title="Time",
        yaxis_title="Balance (USD)",
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=40),
    )
    return fig


def plot_btc_chart_altair(
    df: pd.DataFrame,
    *,
    show_signals: bool = True,
    show_bbands: bool = True,
    show_emas: bool = True,
) -> Any:
    """
    Simpler Altair-based price chart fallback when Plotly is unavailable.
    """
    if df.empty:
        raise ValueError("Cannot plot BTC chart with an empty dataframe.")

    try:
        import altair as alt  # type: ignore[import-untyped]
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Altair is required for the fallback chart but is not installed.") from exc

    frame = df.copy().reset_index().rename(columns={df.index.name or "index": "timestamp"})
    if "timestamp" not in frame.columns:
        frame = frame.rename(columns={frame.columns[0]: "timestamp"})

    base = alt.Chart(frame).encode(x="timestamp:T")
    tooltip_fields = [
        alt.Tooltip("timestamp:T", title="Time"),
        alt.Tooltip("close:Q", title="Close", format=",.2f"),
        alt.Tooltip("volume:Q", title="Volume", format=",.0f"),
    ]

    layers = [
        base.mark_line(color="#38bdf8", strokeWidth=2).encode(y=alt.Y("close:Q", title="BTC / USD"), tooltip=tooltip_fields)
    ]

    if show_emas and {"ema_fast", "ema_slow"} <= set(frame.columns):
        layers.append(
            base.mark_line(color="#fb7185", strokeDash=[4, 4], strokeWidth=1.5).encode(y="ema_fast:Q", tooltip=tooltip_fields)
        )
        layers.append(
            base.mark_line(color="#a855f7", strokeDash=[2, 4], strokeWidth=1.5).encode(y="ema_slow:Q", tooltip=tooltip_fields)
        )

    if show_bbands and {"bb_upper", "bb_lower"} <= set(frame.columns):
        layers.append(
            base.mark_line(color="#38bdf8", strokeDash=[6, 4]).encode(y="bb_upper:Q", tooltip=tooltip_fields)
        )
        layers.append(
            base.mark_line(color="#38bdf8", strokeDash=[6, 4]).encode(y="bb_lower:Q", tooltip=tooltip_fields)
        )

    if show_signals and "signal" in frame.columns:
        buys = frame[frame["signal"].str.contains("BUY", na=False)]
        sells = frame[frame["signal"].str.contains("SELL", na=False)]
        if not buys.empty:
            layers.append(
                alt.Chart(buys)
                .mark_point(shape="triangle-up", color="#22c55e", size=70)
                .encode(x="timestamp:T", y="close:Q", tooltip=tooltip_fields + [alt.Tooltip("signal", title="Signal")])
            )
        if not sells.empty:
            layers.append(
                alt.Chart(sells)
                .mark_point(shape="triangle-down", color="#ef4444", size=70)
                .encode(x="timestamp:T", y="close:Q", tooltip=tooltip_fields + [alt.Tooltip("signal", title="Signal")])
            )

    chart = alt.layer(*layers).resolve_scale(y="shared").properties(height=420)
    return chart.interactive()


def plot_equity_curve_altair(equity: pd.Series) -> Any:
    """
    Altair fallback for the equity curve visualisation.
    """
    if equity is None or equity.empty:
        raise ValueError("Equity series is empty.")

    try:
        import altair as alt  # type: ignore[import-untyped]
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Altair is required for the fallback equity chart but is not installed.") from exc

    frame = equity.reset_index()
    frame.columns = ["timestamp", "equity"]

    tooltip_fields = [
        alt.Tooltip("timestamp:T", title="Time"),
        alt.Tooltip("equity:Q", title="Equity", format=",.2f"),
    ]

    chart = (
        alt.Chart(frame)
        .mark_line(color="#0ea5e9", strokeWidth=2)
        .encode(x="timestamp:T", y=alt.Y("equity:Q", title="Balance (USD)"), tooltip=tooltip_fields)
        .properties(height=320)
        .interactive()
    )
    return chart
