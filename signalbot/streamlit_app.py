from __future__ import annotations

import io
import json
import math
import sys
import traceback
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

st.set_page_config(
    page_title="BTC Signal Bot",
    page_icon="🧠",
    layout="wide",
)

CUSTOM_CSS = """
<style>
:root {
    --surface-bg: #f8fafc;
    --border-soft: #e2e8f0;
    --accent: #2563eb;
    --text-strong: #0f172a;
    --text-muted: #64748b;
}
.hero {
    background: linear-gradient(135deg, #0f172a, #2563eb);
    color: #f8fafc;
    padding: 1.4rem 1.7rem;
    border-radius: 18px;
    margin-bottom: 1.2rem;
}
.hero h1 {
    margin: 0;
    font-size: 1.95rem;
    font-weight: 700;
    color: #ffffff;
}
.hero p {
    margin: 0.45rem 0 0;
    font-size: 1.02rem;
    color: #e2e8f0;
}
.metric-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 1rem 1.2rem;
    border: 1px solid var(--border-soft);
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.metric-label {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
}
.metric-value {
    margin-top: 0.45rem;
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--text-strong);
}
.metric-delta {
    margin-top: 0.35rem;
    display: inline-block;
    font-weight: 600;
    font-size: 0.9rem;
}
.metric-card-flash {
    animation: metric-flash 0.9s ease-in-out;
}
@keyframes metric-flash {
    0% {
        box-shadow: 0 0 0 rgba(56, 189, 248, 0.0);
    }
    35% {
        box-shadow: 0 0 0 10px rgba(56, 189, 248, 0.18);
    }
    100% {
        box-shadow: 0 0 0 rgba(56, 189, 248, 0.0);
    }
}
.metric-delta.positive {
    color: #16a34a;
}
.metric-delta.negative {
    color: #dc2626;
}
.metric-delta.neutral {
    color: #94a3b8;
}
.metric-badge {
    padding: 0.18rem 0.6rem;
    border-radius: 999px;
    background: #e0f2fe;
    color: #0c4a6e;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid rgba(14, 165, 233, 0.35);
}
.metric-card.metric-card-signal {
    min-height: 148px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.55rem;
    border: none;
    box-shadow: 0 14px 30px rgba(15, 23, 42, 0.2);
}
.metric-card.metric-card-signal .metric-label,
.metric-card.metric-card-signal .metric-value,
.metric-card.metric-card-signal .metric-delta {
    color: rgba(248, 250, 252, 0.92);
}
.metric-card.metric-card-signal .metric-label strong {
    color: inherit;
}
.metric-card.metric-card-signal .metric-badge {
    background: rgba(15, 23, 42, 0.32);
    color: #f8fafc;
    border-color: rgba(241, 245, 249, 0.3);
}
.metric-card.metric-card-signal.signal-buy {
    background: linear-gradient(135deg, #14532d, #22c55e);
}
.metric-card.metric-card-signal.signal-sell {
    background: linear-gradient(135deg, #7f1d1d, #ef4444);
}
.metric-card.metric-card-signal.signal-hold {
    background: linear-gradient(135deg, #1e293b, #64748b);
}
.metric-card.metric-card-signal.signal-hold .metric-badge {
    background: rgba(15, 23, 42, 0.3);
}
.metric-card.metric-card-signal.signal-buy .metric-badge {
    border-color: rgba(187, 247, 208, 0.45);
}
.metric-card.metric-card-signal.signal-sell .metric-badge {
    border-color: rgba(254, 202, 202, 0.4);
}
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin: 0.1rem 0 1.3rem;
}
.chip {
    padding: 0.4rem 0.75rem;
    border-radius: 999px;
    border: 1px solid;
    font-size: 0.85rem;
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
}
.chip-on {
    background: #e0f2fe;
    color: #075985;
    border-color: #38bdf8;
}
.chip-off {
    background: #f8fafc;
    color: #94a3b8;
    border-color: #e2e8f0;
}
.chip strong {
    font-weight: 600;
}
.backtest-summary {
    background: linear-gradient(130deg, #0f172a, #1e3a8a);
    color: #f8fafc;
    padding: 1.1rem 1.4rem;
    border-radius: 18px;
    margin: 1rem 0 1.4rem;
    border: 1px solid rgba(148, 163, 184, 0.25);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.25);
}
.backtest-summary h3 {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 700;
}
.backtest-summary p {
    margin: 0.6rem 0 0.9rem;
    font-size: 0.98rem;
    line-height: 1.5;
    color: #e2e8f0;
}
.summary-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
    border: 1px solid rgba(226, 232, 240, 0.35);
    background: rgba(15, 23, 42, 0.35);
    color: #f8fafc;
}
.summary-chip.positive {
    background: rgba(22, 163, 74, 0.18);
    color: #bbf7d0;
    border-color: rgba(34, 197, 94, 0.45);
}
.summary-chip.negative {
    background: rgba(220, 38, 38, 0.18);
    color: #fecaca;
    border-color: rgba(248, 113, 113, 0.45);
}
.backtest-steps {
    display: grid;
    gap: 0.85rem;
    margin: 1.2rem 0 1.5rem;
}
.step-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 0.95rem 1.05rem;
    border: 1px solid var(--border-soft);
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}
.step-card h4 {
    margin: 0 0 0.35rem;
    font-size: 0.95rem;
    color: var(--text-strong);
}
.step-card p {
    margin: 0;
    color: var(--text-muted);
    font-size: 0.86rem;
    line-height: 1.5;
}
.metric-section-title {
    margin: 1.2rem 0 0.8rem;
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
}
.data-output-title {
    margin: 2rem 0 0.7rem;
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.overlay-active-badge {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 0.45rem;
    margin-bottom: 0.55rem;
    flex-wrap: wrap;
}
.overlay-active-badge span {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border-radius: 999px;
    padding: 0.25rem 0.65rem;
    font-size: 0.78rem;
    font-weight: 600;
    border: 1px solid rgba(59, 130, 246, 0.35);
}
.overlay-active-badge .inactive {
    background: rgba(148, 163, 184, 0.18);
    color: #94a3b8;
    border-color: rgba(148, 163, 184, 0.35);
}
.overlay-toggle-container {
    margin: 0.6rem 0 0.2rem;
}
.overlay-toggle-container > div[data-testid="stVerticalBlock"] {
    gap: 0.55rem;
}
.overlay-toggle-container div[data-testid="stCheckbox"] {
    background: rgba(37, 99, 235, 0.08);
    border: 1px solid rgba(56, 189, 248, 0.28);
    border-radius: 14px;
    padding: 0.45rem 0.7rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}
.overlay-toggle-container div[data-testid="stCheckbox"][aria-checked="false"] {
    background: rgba(15, 23, 42, 0.25);
    border-color: rgba(148, 163, 184, 0.35);
    opacity: 0.72;
}
.overlay-toggle-container div[data-testid="stCheckbox"]:hover {
    border-color: rgba(96, 165, 250, 0.8);
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.16);
    background: rgba(37, 99, 235, 0.15);
}
.overlay-toggle-container div[data-testid="stCheckbox"] label {
    color: #e2e8f0;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.overlay-toggle-container div[data-testid="stCheckbox"] label > div:first-child {
    margin-right: 0.55rem;
}
.overlay-toggle-container div[data-testid="stCheckbox"][aria-checked="true"] {
    background: rgba(56, 189, 248, 0.2);
    border-color: rgba(14, 165, 233, 0.55);
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.22);
}
.copy-export-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin-top: 0.6rem;
}
.copy-button {
    padding: 0.5rem 0.85rem;
    border-radius: 12px;
    border: 1px solid rgba(56, 189, 248, 0.45);
    background: rgba(37, 99, 235, 0.18);
    color: #e0f2fe;
    font-weight: 600;
    letter-spacing: 0.03em;
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.copy-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 18px rgba(56, 189, 248, 0.18);
    border-color: rgba(96, 165, 250, 0.8);
}
.copy-button:active {
    transform: translateY(0);
}
.toast-stack {
    position: fixed;
    top: 1.1rem;
    right: 1.1rem;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    z-index: 9999;
}
.custom-toast {
    min-width: 260px;
    max-width: 320px;
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.75rem 0.85rem;
    border-radius: 12px;
    box-shadow: 0 16px 35px rgba(15, 23, 42, 0.35);
    font-size: 0.88rem;
    font-weight: 600;
    transition: opacity 0.25s ease, transform 0.3s ease;
    position: relative;
    backdrop-filter: blur(8px);
}
.custom-toast .toast-icon {
    font-size: 1rem;
}
.custom-toast .toast-message {
    flex: 1;
}
.custom-toast.success {
    background: rgba(22, 163, 74, 0.22);
    border: 1px solid rgba(34, 197, 94, 0.45);
    color: #bbf7d0;
}
.custom-toast.error {
    background: rgba(220, 38, 38, 0.22);
    border: 1px solid rgba(248, 113, 113, 0.48);
    color: #fecaca;
}
.custom-toast.info {
    background: rgba(14, 165, 233, 0.22);
    border: 1px solid rgba(56, 189, 248, 0.48);
    color: #e0f2fe;
}
.custom-toast .toast-close {
    background: transparent;
    border: none;
    color: inherit;
    font-size: 1rem;
    cursor: pointer;
    margin-left: auto;
    line-height: 1;
}
.custom-toast .toast-close:hover {
    opacity: 0.85;
}
.custom-toast.hide {
    opacity: 0;
    transform: translateX(16px);
}
.sidebar-hamburger {
    display: none;
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 1001;
    background: rgba(15, 23, 42, 0.9);
    color: #f8fafc;
    border-radius: 12px;
    padding: 0.55rem 0.8rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    cursor: pointer;
    border: 1px solid rgba(148, 163, 184, 0.35);
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.35);
}
.sidebar-overlay {
    display: none;
}
.sidebar-section-title {
    margin: 1rem 0 0.5rem;
    padding: 0.45rem 0.75rem;
    border-radius: 12px;
    background: rgba(148, 163, 184, 0.12);
    color: #e2e8f0;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.sidebar-slider-spacer {
    height: 0.6rem;
}
[data-testid="stSidebar"] .stSlider {
    padding-top: 0.2rem;
    padding-bottom: 0.15rem;
}
[data-testid="stSidebar"] .stSlider > div {
    padding-right: 0.35rem;
}
[data-testid="stSidebar"] .stNumberInput {
    margin-top: 0.1rem;
}
@media (max-width: 900px) {
    .sidebar-hamburger {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
    }
    .sidebar-overlay {
        display: block;
        position: fixed;
        inset: 0;
        background: rgba(15, 23, 42, 0.45);
        z-index: 1000;
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
    }
    body.sidebar-open .sidebar-overlay {
        opacity: 1;
        pointer-events: auto;
    }
    [data-testid="stSidebar"] {
        position: fixed;
        top: 0;
        left: 0;
        height: 100%;
        width: 78vw;
        max-width: 320px;
        transform: translateX(-100%);
        transition: transform 0.3s ease;
        z-index: 1002;
        box-shadow: 8px 0 24px rgba(15, 23, 42, 0.45);
    }
    body.sidebar-open [data-testid="stSidebar"] {
        transform: translateX(0);
    }
    .main .block-container {
        padding-top: 3.25rem;
    }
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
}
[data-testid="stToggle"][aria-checked="false"] {
    filter: grayscale(0.6);
    opacity: 0.75;
}
</style>
"""
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom right, #1D2951, #3A5DFF);
        color: white;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <div class="sidebar-hamburger" onclick="toggleSidebar()">☰ Menu</div>
    <div class="sidebar-overlay" onclick="toggleSidebar()"></div>
    <script>
    (function() {
        if (window.sidebarToggleInitialized) return;
        window.sidebarToggleInitialized = true;
        window.toggleSidebar = function() {
            document.body.classList.toggle('sidebar-open');
        };
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                document.body.classList.remove('sidebar-open');
            }
        });
        window.addEventListener('resize', function() {
            if (window.innerWidth > 900) {
                document.body.classList.remove('sidebar-open');
            }
        });
    })();
    </script>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div id="toast-stack" class="toast-stack"></div>', unsafe_allow_html=True)


def render_metric_card(
    label: str,
    value: str,
    *,
    delta: float | None = None,
    delta_suffix: str = "",
    badge: str | None = None,
    variant: str | None = None,
    highlight: bool = False,
) -> None:
    delta_html = ""
    if delta is not None:
        threshold = 1e-9
        if delta > threshold:
            sign_class = "positive"
            icon = "⬆️"
        elif delta < -threshold:
            sign_class = "negative"
            icon = "⬇️"
        else:
            sign_class = "neutral"
            icon = "⏺"
        delta_text = f"{delta:+.2f}{delta_suffix}"
        delta_html = f"<span class='metric-delta {sign_class}'>{icon} {delta_text}</span>"

    badge_html = f"<span class='metric-badge'>{badge}</span>" if badge else ""

    classes = ["metric-card"]
    if variant:
        classes.extend(part for part in variant.split(" ") if part)
    if highlight:
        classes.append("metric-card-flash")
    class_attr = " ".join(classes)

    st.markdown(
        f"""
        <div class="{class_attr}">
            <div class="metric-label">{label}{badge_html}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_slider_with_input(
    label: str,
    *,
    min_value: float | int,
    max_value: float | int,
    value: float | int,
    step: float | int,
    key: str,
    help_text: str | None = None,
    format_str: str | None = None,
) -> float | int:
    """
    Render a slider paired with a compact number input for precise adjustments.
    Synchronises both widgets via the provided key.
    """
    value_type = float if any(isinstance(v, float) for v in (min_value, max_value, value, step)) else int
    if key not in st.session_state:
        st.session_state[key] = value_type(value)

    current_value = value_type(st.session_state[key])
    slider_kwargs = dict(
        min_value=value_type(min_value),
        max_value=value_type(max_value),
        value=current_value,
        step=value_type(step),
        help=help_text,
    )
    if format_str:
        slider_kwargs["format"] = format_str

    slider_col, input_col = st.sidebar.columns((5, 1))
    slider_value = slider_col.slider(label, **slider_kwargs)
    slider_value = value_type(slider_value)

    precision_label = f"{label} precise"
    number_value = input_col.number_input(
        precision_label,
        min_value=value_type(min_value),
        max_value=value_type(max_value),
        value=slider_value,
        step=value_type(step),
        help=help_text,
        label_visibility="collapsed",
    )
    number_value = value_type(number_value)

    new_value = number_value
    if st.session_state[key] != new_value:
        st.session_state[key] = new_value

    st.sidebar.markdown("<div class='sidebar-slider-spacer'></div>", unsafe_allow_html=True)
    return st.session_state[key]


def track_metric_change(key: str, value: Any) -> bool:
    """
    Store a normalised snapshot of the metric and return True when the value changes.
    """
    if isinstance(value, float):
        normalized: Any = round(value, 6)
    elif isinstance(value, (int,)):
        normalized = value
    elif value is None:
        normalized = "None"
    else:
        normalized = str(value)

    changed = key in st.session_state and st.session_state[key] != normalized
    st.session_state[key] = normalized
    return changed


def show_toast(message: str, *, variant: str = "info", duration: int = 6) -> None:
    """Render a dismissible toast in the top-right corner."""
    toast_id = uuid.uuid4().hex
    icon_map = {
        "success": "✅",
        "error": "❌",
        "info": "ℹ️",
    }
    icon = icon_map.get(variant, "ℹ️")
    safe_message = (
        message.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "<br>")
    )
    toast_script = f"""
    <script>
    (function() {{
        const stack = document.getElementById('toast-stack');
        if (!stack) {{ return; }}
        const toast = document.createElement('div');
        toast.className = 'custom-toast {variant}';
        toast.id = '{toast_id}';
        toast.innerHTML = `
            <span class="toast-icon">{icon}</span>
            <span class="toast-message">{safe_message}</span>
            <button class="toast-close" aria-label="Dismiss">×</button>
        `;
        toast.querySelector('.toast-close').addEventListener('click', function() {{
            toast.classList.add('hide');
            setTimeout(() => toast.remove(), 320);
        }});
        stack.appendChild(toast);
        setTimeout(() => {{
            if (toast.parentNode) {{
                toast.classList.add('hide');
                setTimeout(() => toast.remove(), 320);
            }}
        }}, {duration * 1000});
    }})();
    </script>
    """
    st.markdown(toast_script, unsafe_allow_html=True)


def render_overlay_controls(
    layer_meta: dict[str, dict[str, str]],
    *,
    backtest_mode_enabled: bool,
    container: Any = st,
    expand_label: str = "📊 Overlay Options",
) -> dict[str, bool]:
    """
    Render overlay toggles within the provided container and sync them with session state.
    """
    toggle_order = [
        "layer_signals",
        "layer_bbands",
        "layer_emas",
        "layer_divergence",
        "layer_macd",
        "layer_rsi",
        "layer_backtest_trades",
    ]
    states: dict[str, bool] = {}
    with container.expander(expand_label, expanded=False):
        container.markdown("<div class='overlay-toggle-container'>", unsafe_allow_html=True)
        columns_func = getattr(container, "columns", st.columns)
        toggle_columns = columns_func(2)
        for idx, key in enumerate(toggle_order):
            meta = layer_meta[key]
            disabled = key == "layer_backtest_trades" and not backtest_mode_enabled
            current_value = st.session_state.get(key, False)
            widget_value = False if disabled else bool(current_value)
            column = toggle_columns[idx % len(toggle_columns)]
            widget_key = f"{key}_main"
            if disabled and st.session_state.get(widget_key, False):
                st.session_state[widget_key] = False
            with column:
                states[key] = st.checkbox(
                    meta["label"],
                    value=widget_value,
                    key=widget_key,
                    help=meta["help"],
                    disabled=disabled,
                )
            if disabled:
                states[key] = False
            st.session_state[key] = states[key]
        container.markdown("</div>", unsafe_allow_html=True)
    return states


# Internal imports
from streamlit_autorefresh import st_autorefresh
try:
    from signalbot.main import run
except ModuleNotFoundError as exc:  # pragma: no cover - configuration dependent
    raise RuntimeError(
        "Failed to import `signalbot.main`. Make sure the project root is on PYTHONPATH "
        "or install the package with `pip install -e .`."
    ) from exc
from signalbot.backtest import backtest_signals
from signalbot.plotting import (
    PLOTLY_AVAILABLE,
    plot_btc_chart,
    plot_btc_chart_altair,
    plot_equity_curve,
    plot_equity_curve_altair,
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom right, #1D2951, #3A5DFF);
        color: white;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div id="toast-stack" class="toast-stack"></div>', unsafe_allow_html=True)

# ==============================
# ⚙️ Sidebar Controls
# ==============================
st.sidebar.header("⚙️ Settings")

settings_tabs = st.sidebar.tabs(["Strategy", "Chart Layers", "Backtest"])

# Strategy Settings Tab
with settings_tabs[0]:
    interval_options = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1W": "1wk",
        "1M": "1mo",
        "1Y": "1y",
    }
    interval_labels = list(interval_options.keys())
    default_interval_index = interval_labels.index("4h")
    selected_interval_label = st.selectbox(
        "Chart Interval",
        interval_labels,
        index=default_interval_index,
        key="interval_select",
        help="Controls the BTC timeframe used for the strategy and displayed chart.",
    )
    interval = interval_options[selected_interval_label]
    st.markdown("<div class='sidebar-slider-spacer'></div>", unsafe_allow_html=True)

    period = sidebar_slider_with_input(
        "RSI Period",
        min_value=5,
        max_value=50,
        value=14,
        step=1,
        key="setting_rsi_period",
        help_text="Number of periods used to calculate RSI. Lower values react faster but are noisier.",
    )
    oversold = sidebar_slider_with_input(
        "Oversold Threshold",
        min_value=10,
        max_value=50,
        value=30,
        step=1,
        key="setting_oversold",
        help_text="RSI level considered oversold. Signals below this threshold may highlight potential entries.",
    )
    overbought = sidebar_slider_with_input(
        "Overbought Threshold",
        min_value=50,
        max_value=90,
        value=70,
        step=1,
        key="setting_overbought",
        help_text="RSI level considered overbought. Signals above this threshold may suggest taking profits.",
    )
    lookback_days = sidebar_slider_with_input(
        "Lookback Window (days)",
        min_value=30,
        max_value=1825,
        value=365,
        step=1,
        key="setting_lookback_days",
        help_text="How many days of BTC history to download before generating signals.",
    )
    refresh_rate = sidebar_slider_with_input(
        "Auto-refresh (seconds)",
        min_value=1,
        max_value=300,
        value=5,
        step=1,
        key="setting_refresh_rate",
        help_text="Interval for auto-refreshing the chart when the app stays open.",
    )

# Shared overlay metadata
layer_defaults = {
    "layer_macd": True,
    "layer_rsi": False,
    "layer_signals": False,
    "layer_bbands": False,
    "layer_emas": False,
    "layer_divergence": False,
    "layer_backtest_trades": False,
}
for key, default in layer_defaults.items():
    st.session_state.setdefault(key, default)

layer_definitions = {
    "layer_macd": {
        "label": "MACD Panel",
        "help": "Plot MACD and signal lines in a dedicated panel to track momentum shifts.",
        "badge": "MACD",
    },
    "layer_rsi": {
        "label": "RSI Panel",
        "help": "Display the RSI panel beneath the chart for overbought/oversold confirmation.",
        "badge": "RSI",
    },
    "layer_signals": {
        "label": "Buy & Sell Markers",
        "help": "Overlay generated buy/sell markers directly on the price candles.",
        "badge": "Signals",
    },
    "layer_bbands": {
        "label": "Bollinger Bands",
        "help": "Add Bollinger Bands around price to visualize volatility envelopes.",
        "badge": "Bollinger",
    },
    "layer_emas": {
        "label": "EMAs",
        "help": "Draw fast and slow exponential moving averages to assess trend bias.",
        "badge": "EMAs",
    },
    "layer_divergence": {
        "label": "Divergence Markers",
        "help": "Highlight bullish or bearish divergences detected by the strategy.",
        "badge": "Divergence",
    },
    "layer_backtest_trades": {
        "label": "Backtest Trades",
        "help": "Reveal simulated trade entries and exits when backtesting is enabled.",
        "badge": "Backtest",
    },
}

# Chart Layers Tab
with settings_tabs[1]:
    st.caption("Toggle overlays via the expander to tailor the view.")
    overlay_states_sidebar = render_overlay_controls(
        layer_definitions,
        backtest_mode_enabled=st.session_state.get("toggle_backtest_mode", False),
        container=st,
        expand_label="📊 Overlay Options",
    )

# Backtest Tab
with settings_tabs[2]:
    st.session_state.setdefault("toggle_backtest_mode", False)
    backtest_mode = st.toggle(
        "🧪 Enable Backtest Mode",
        key="toggle_backtest_mode",
        help="Toggle on to simulate historical trades using the current strategy settings.",
    )
    st.caption("Backtest trades and overlays become available once enabled.")

if "backtest_mode" not in locals():
    backtest_mode = st.session_state.get("toggle_backtest_mode", False)

# Ensure overlay states reflect most recent sidebar selections
if 'overlay_states_sidebar' in locals():
    for key, value in overlay_states_sidebar.items():
        st.session_state[key] = value

st.sidebar.markdown("---")

st.sidebar.markdown("""
🧠 Use the tabs above to configure the strategy, overlays, and backtest options.

ℹ️ **Chart Layers**  
Overlay toggles appear in the Chart Layers tab for quick adjustments.
""")



# ==============================
# 🔁 Auto-refresh (only chart)
# ==============================
st_autorefresh(interval=refresh_rate * 1000, key="autorefresh")

# ==============================
# 💾 Session State
# ==============================
if "df" not in st.session_state:
    st.session_state["df"] = None

if "params" not in st.session_state:
    st.session_state["params"] = {}

st.markdown(
    """
    <div class="hero">
        <h1>🚀 BTC Signal Bot</h1>
        <p>Track price action, momentum, and trend confirmation in one place. Adjust settings in the sidebar and rerun the strategy to refresh.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"Charts auto-refresh every {refresh_rate} seconds on the {selected_interval_label} interval. "
    "Overlays can be switched on or off via the sidebar."
)

if not PLOTLY_AVAILABLE:
    st.info(
        "Plotly is not installed in this environment. Falling back to a simplified Altair chart; "
        "install `plotly` for the full interactive experience."
    )

run_button = st.button("🚀 Run Strategy", type="primary")

current_params = {
    "interval": interval,
    "interval_label": selected_interval_label,
    "period": period,
    "oversold": oversold,
    "overbought": overbought,
    "lookback_days": lookback_days,
}

should_fetch = run_button or st.session_state["df"] is None

if st.session_state["params"] != current_params:
    should_fetch = True
    st.session_state["params"] = current_params

# ==============================
# 📡 Fetch & Run Strategy
# ==============================
just_ran = False
if should_fetch:
    with st.spinner("🔄 Fetching BTC data and running strategy..."):
        try:
            df = run(
                interval=interval,
                period=period,
                oversold=oversold,
                overbought=overbought,
                lookback_days=lookback_days,
            )
            st.session_state["df"] = df
            st.session_state["last_run_time"] = pd.Timestamp.utcnow().isoformat()
            just_ran = True
        except Exception as exc:
            error_message = f"Error while running strategy: {exc}"
            st.error(f"❌ {error_message}")
            show_toast(error_message, variant="error", duration=8)
            st.code(traceback.format_exc(), language="python")
            st.stop()

df = st.session_state["df"]

if df is None or df.empty:
    show_toast("No data returned for the selected configuration. Adjust the interval or lookback and try again.", variant="error")
    st.info("Adjust settings and press **Run Strategy** to fetch data.")
    st.stop()

data_source = df.attrs.get("data_source", "unknown")
data_error = df.attrs.get("data_error")
if data_source == "synthetic":
    synthetic_note = (
        "Using synthetic BTC data because live data could not be downloaded. "
        "Reconnect to the internet and ensure `pycoingecko` is installed for real market data."
    )
    st.warning(synthetic_note)
    if just_ran:
        show_toast("Running with synthetic BTC candles (offline mode).", variant="info", duration=7)
    if data_error:
        st.caption(f"Data fetch error details: `{data_error}`")

# ==============================
# 🧩 Latest Signal Snapshot
# ==============================
last = df.iloc[-1]
if just_ran:
    show_toast("Strategy executed successfully.", variant="success")

st.markdown("<div class='metric-section-title'>📈 Current Metrics</div>", unsafe_allow_html=True)

last_run_iso = st.session_state.get("last_run_time")
if last_run_iso:
    last_run_ts = pd.Timestamp(last_run_iso)
    if last_run_ts.tzinfo is None:
        last_run_ts = last_run_ts.tz_localize("UTC")
    else:
        last_run_ts = last_run_ts.tz_convert("UTC")
    st.caption(f"Last run: {last_run_ts.strftime('%Y-%m-%d %H:%M:%S %Z')}")

previous_row = df.iloc[-2] if len(df) >= 2 else None
price_delta = None
if previous_row is not None:
    prev_close = previous_row.get("close", 0)
    if prev_close not in (0, None):
        price_delta = (last["close"] / prev_close - 1) * 100

rsi_delta = None
if "rsi" in df.columns and previous_row is not None:
    current_rsi = last.get("rsi")
    previous_rsi = previous_row.get("rsi")
    if pd.notna(current_rsi) and pd.notna(previous_rsi):
        rsi_delta = current_rsi - previous_rsi

signal_text = last.get("signal", "HOLD")
signal_strength = (last.get("signal_strength", "N/A") or "N/A").replace("_", " ").title()
divergence_text = (last.get("divergence", "None") or "None").title()

price_changed = track_metric_change("metric_close_price", float(last["close"]))
rsi_value = last.get("rsi")
rsi_changed = track_metric_change(
    "metric_rsi",
    float(rsi_value) if pd.notna(rsi_value) else None,
)
signal_state = (signal_text or "HOLD").strip().upper()
signal_changed = track_metric_change("metric_signal", f"{signal_state}|{signal_strength}")
signal_display = signal_state.replace("_", " ") if signal_state else "HOLD"
signal_variant_map = {
    "BUY": "metric-card-signal signal-buy",
    "SELL": "metric-card-signal signal-sell",
    "HOLD": "metric-card-signal signal-hold",
}
signal_variant = signal_variant_map.get(signal_state, "metric-card-signal signal-hold")

metrics_cols = st.columns((1.6, 1.6, 2.2))
with metrics_cols[0]:
    render_metric_card(
        "Close Price",
        f"${last['close']:,.2f}",
        delta=price_delta,
        delta_suffix="%",
        highlight=price_changed,
    )
with metrics_cols[1]:
    rsi_display = f"{rsi_value:.2f}" if pd.notna(rsi_value) else "–"
    render_metric_card(
        f"RSI ({period})",
        rsi_display,
        delta=rsi_delta,
        highlight=rsi_changed,
    )
with metrics_cols[2]:
    badge_value = None if signal_strength.upper() == "N/A" else signal_strength
    render_metric_card(
        "Signal",
        signal_display,
        badge=badge_value,
        variant=signal_variant,
        highlight=signal_changed,
    )

st.caption(f"Divergence flag: **{divergence_text}** · Signal strength reflects EMA trend alignment.")

overlay_states = {
    key: st.session_state.get(key, layer_defaults.get(key, False))
    for key in layer_definitions
}

show_signals = overlay_states.get("layer_signals", False)
show_bbands = overlay_states.get("layer_bbands", False)
show_emas = overlay_states.get("layer_emas", False)
show_divergence = overlay_states.get("layer_divergence", False)
show_macd = overlay_states.get("layer_macd", False)
show_rsi = overlay_states.get("layer_rsi", False)
show_backtest_trades = overlay_states.get("layer_backtest_trades", False)

st.session_state["layer_signals"] = show_signals
st.session_state["layer_bbands"] = show_bbands
st.session_state["layer_emas"] = show_emas
st.session_state["layer_divergence"] = show_divergence
st.session_state["layer_macd"] = show_macd
st.session_state["layer_rsi"] = show_rsi
st.session_state["layer_backtest_trades"] = show_backtest_trades

active_overlay_labels = [
    layer_definitions[key].get("badge", layer_definitions[key]["label"])
    for key, enabled in overlay_states.items()
    if enabled and key != "layer_backtest_trades"
]
if show_backtest_trades:
    active_overlay_labels.append(
        layer_definitions["layer_backtest_trades"].get("badge", layer_definitions["layer_backtest_trades"]["label"])
    )

indicator_items = [
    ("MACD", show_macd, "🧮"),
    ("RSI", show_rsi, "📐"),
    ("Signals", show_signals, "🎯"),
    ("Bollinger", show_bbands, "📊"),
    ("EMAs", show_emas, "📈"),
    ("Divergence", show_divergence, "🔀"),
]
if backtest_mode:
    indicator_items.append(("Backtest Trades", show_backtest_trades, "💼"))

chips_html = "".join(
    f"<span class='chip {'chip-on' if enabled else 'chip-off'}'>{icon}<strong>{name}</strong></span>"
    for name, enabled, icon in indicator_items
)
if chips_html:
    st.markdown("<div class='chip-row'>" + chips_html + "</div>", unsafe_allow_html=True)

st.markdown("<div class='data-output-title'>📁 Data Output</div>", unsafe_allow_html=True)
preview_columns = [
    col
    for col in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "rsi",
        "macd",
        "macd_signal",
        "signal",
        "signal_strength",
        "divergence",
    ]
    if col in df.columns
]
preview_df = df.head(8)[preview_columns] if preview_columns else df.head(8)
rounded_preview = preview_df.round(3)
preview_style = (
    rounded_preview.style.format(precision=3)
    .set_table_styles(
        [
            {
                "selector": "thead th",
                "props": [
                    ("position", "sticky"),
                    ("top", "0"),
                    ("background-color", "#0f172a"),
                    ("color", "#e2e8f0"),
                    ("box-shadow", "0 2px 6px rgba(15, 23, 42, 0.55)"),
                    ("z-index", "3"),
                ],
            },
            {
                "selector": "tbody tr:nth-child(odd)",
                "props": [("background-color", "rgba(15, 23, 42, 0.22)")],
            },
            {
                "selector": "tbody tr:nth-child(even)",
                "props": [("background-color", "rgba(15, 23, 42, 0.12)")],
            },
            {
                "selector": "tbody tr:hover",
                "props": [("background-color", "rgba(56, 189, 248, 0.18)")],
            },
            {
                "selector": "tbody td",
                "props": [("color", "#e2e8f0"), ("border", "none"), ("font-size", "0.88rem")],
            },
        ]
    )
)

column_config = {
    "volume": st.column_config.NumberColumn("Volume", width="medium", format="%0.0f"),
}
st.dataframe(
    preview_style,
    use_container_width=True,
    height=260,
    column_config=column_config,
)

csv_bytes = df.to_csv(index=True).encode("utf-8")
excel_bytes: bytes | None = None
excel_engine_used: str | None = None
excel_error: str | None = None
for engine in ("xlsxwriter", "openpyxl"):
    buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine=engine) as writer:
            df.to_excel(writer, sheet_name="BTC Signals", index=True)
        excel_bytes = buffer.getvalue()
        excel_engine_used = engine
        break
    except (ImportError, ValueError) as exc:
        excel_error = str(exc)
        continue

json_records = df.reset_index().to_json(orient="records", date_format="iso")
tsv_preview = rounded_preview.to_csv(sep="\t", index=True)

button_cols = st.columns([1, 1, 1, 1])
with button_cols[0]:
    st.download_button(
        label="⬇️ Download Full Dataset (.CSV)",
        data=csv_bytes,
        file_name=f"btc_signals_{selected_interval_label.lower()}.csv",
        mime="text/csv",
        use_container_width=True,
        help="Exports the full dataset including price history, calculated indicators, and strategy signals.",
    )
with button_cols[1]:
    excel_help = (
        f"Download the dataset as an Excel workbook (engine: {excel_engine_used})."
        if excel_bytes is not None
        else "Excel export unavailable — install `xlsxwriter` or `openpyxl` to enable this download."
    )
    st.download_button(
        label="📊 Export to Excel (.XLSX)",
        data=excel_bytes or b"",
        file_name=f"btc_signals_{selected_interval_label.lower()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        help=excel_help,
        disabled=excel_bytes is None,
    )
    if excel_bytes is None and excel_error:
        st.caption(f"Excel export disabled: `{excel_error}`")
with button_cols[2]:
    st.download_button(
        label="🧾 Export JSON",
        data=json_records,
        file_name=f"btc_signals_{selected_interval_label.lower()}.json",
        mime="application/json",
        use_container_width=True,
        help="Download the dataset as newline-free JSON records.",
    )
with button_cols[3]:
    copy_button_html = (
        f'<button class="copy-button" onclick="navigator.clipboard.writeText({json.dumps(tsv_preview)});">'
        "📋 Copy Preview (TSV)"
        "</button>"
    )
    st.markdown(copy_button_html, unsafe_allow_html=True)

metrics = None
trades_df = None
equity_curve = None
if backtest_mode:
    metrics, trades_df, equity_curve = backtest_signals(df)

trades_for_chart = (
    trades_df if show_backtest_trades and trades_df is not None and not trades_df.empty else None
)

tab_labels = ["Interactive Chart", "Recent Signals"]
if backtest_mode:
    tab_labels.append("Backtest Insights")
tabs = st.tabs(tab_labels)

with tabs[0]:
    badge_html = "".join(f"<span>{label}</span>" for label in active_overlay_labels) or "<span class='inactive'>No overlays active</span>"
    st.markdown(f"<div class='overlay-active-badge'>{badge_html}</div>", unsafe_allow_html=True)
    fallback_chart_used = False
    if PLOTLY_AVAILABLE:
        try:
            fig = plot_btc_chart(
                df,
                interval,
                period,
                oversold,
                overbought,
                show_signals=show_signals,
                show_bbands=show_bbands,
                show_emas=show_emas,
                show_divergence=show_divergence,
                show_backtest_trades=show_backtest_trades and trades_for_chart is not None,
                trades_df=trades_for_chart,
                show_rsi=show_rsi,
                show_macd=show_macd,
            )
            st.plotly_chart(
                fig,
                config={
                    "responsive": True,
                    "displayModeBar": False,
                },
            )
        except Exception as exc:
            fallback_chart_used = True
            st.error(f"Plotly chart failed to render ({exc}). Showing simplified chart instead.")
            basic_chart = plot_btc_chart_altair(
                df,
                show_signals=show_signals,
                show_bbands=show_bbands,
                show_emas=show_emas,
            )
            st.altair_chart(basic_chart, use_container_width=True)
    else:
        fallback_chart_used = True
        basic_chart = plot_btc_chart_altair(
            df,
            show_signals=show_signals,
            show_bbands=show_bbands,
            show_emas=show_emas,
        )
        st.altair_chart(basic_chart, use_container_width=True)

    if fallback_chart_used:
        st.caption("Displaying simplified Altair chart. Install `plotly` for the full multi-panel experience.")
    else:
        st.caption("Tip: Combine trend (EMAs) and momentum (MACD/RSI) overlays to confirm breakout confidence.")

with tabs[1]:
    table_cols = [
        col for col in ["close", "rsi", "signal", "signal_strength", "divergence"] if col in df.columns
    ]
    st.dataframe(df.tail(10)[table_cols].round(3), use_container_width=True)
    st.caption("Most recent 10 signals. Use the download button above to export the entire dataset.")

if backtest_mode:
    with tabs[2]:
        if metrics is None:
            st.info("Enable the backtest switch in the sidebar to calculate trade performance.")
        else:
            total_trades = int(metrics.get("total_trades", 0))
            if total_trades == 0:
                st.warning("No completed trades were detected for the selected date range. Consider widening the lookback window or enabling more aggressive signals.")
            net_return = float(metrics.get("net_return", 0.0))
            max_drawdown = abs(float(metrics.get("max_drawdown", 0.0)))
            final_balance = float(metrics.get("final_balance", 0.0))
            initial_balance = float(metrics.get("initial_balance", final_balance / (1 + net_return / 100.0) if net_return != -100 else 0.0))
            win_rate = float(metrics.get("win_rate", 0.0))
            profit_factor = float(metrics.get("profit_factor", 0.0))
            best_trade = float(metrics.get("best_trade", 0.0))
            worst_trade = float(metrics.get("worst_trade", 0.0))
            avg_hold = float(metrics.get("avg_hold_hours", 0.0))
            median_hold = float(metrics.get("median_hold_hours", 0.0))
            exposure_pct = float(metrics.get("exposure_pct", 0.0))
            gross_gain = float(metrics.get("gross_gain", 0.0))
            gross_loss = float(metrics.get("gross_loss", 0.0))
            win_loss_ratio = metrics.get("win_loss_ratio", 0.0)

            net_class = "positive" if net_return >= 0 else "negative"
            win_class = "positive" if win_rate >= 50 else "negative"
            dd_class = "negative" if max_drawdown > 0 else "positive"
            summary_html = f"""
            <div class="backtest-summary">
                <h3>Backtest Overview</h3>
                <p>Starting from <strong>${initial_balance:,.2f}</strong>, the strategy finished with <strong>${final_balance:,.2f}</strong> ({net_return:+.2f}%) over the last {lookback_days} days on the {selected_interval_label} chart. It captured {win_rate:.1f}% of {total_trades} simulated trades with a peak drawdown of {max_drawdown:.2f}%.</p>
                <div class="chip-row" style="margin:0;gap:0.5rem;">
                    <span class="summary-chip {net_class}">Net return {net_return:+.2f}%</span>
                    <span class="summary-chip {win_class}">Win rate {win_rate:.1f}%</span>
                    <span class="summary-chip {dd_class}">Max drawdown {max_drawdown:.2f}%</span>
                </div>
            </div>
            """
            st.markdown(summary_html, unsafe_allow_html=True)

            steps_html = f"""
            <div class="backtest-steps">
                <div class="step-card">
                    <h4>1. Gather price & indicators</h4>
                    <p>Pulls {lookback_days} days of {selected_interval_label} candles and computes EMA, RSI, MACD, and Bollinger overlays.</p>
                </div>
                <div class="step-card">
                    <h4>2. Simulate the strategy</h4>
                    <p>Runs the signal rules to open and close long positions, accounting for 0.07% commission and 0.05% slippage on each side.</p>
                </div>
                <div class="step-card">
                    <h4>3. Summarise performance</h4>
                    <p>Builds the equity curve, calculates trade stats, and highlights risk/reward metrics so you can judge robustness.</p>
                </div>
            </div>
            """
            st.markdown(steps_html, unsafe_allow_html=True)

            score_cols = st.columns(3)
            with score_cols[0]:
                render_metric_card("Total Trades", f"{total_trades}")
            with score_cols[1]:
                render_metric_card(
                    "Net Return",
                    f"{net_return:.2f}%",
                    delta=net_return,
                    delta_suffix="%",
                )
            with score_cols[2]:
                render_metric_card("Final Balance", f"${final_balance:,.2f}")

            risk_cols = st.columns(3)
            with risk_cols[0]:
                render_metric_card("Win Rate", f"{win_rate:.2f}%")
            with risk_cols[1]:
                render_metric_card(
                    "Max Drawdown",
                    f"{max_drawdown:.2f}%",
                    delta=-max_drawdown,
                    delta_suffix="%",
                )
            with risk_cols[2]:
                profit_factor_display = "∞" if not math.isfinite(profit_factor) else f"{profit_factor:.2f}"
                render_metric_card("Profit Factor", profit_factor_display)

            texture_cols = st.columns(3)
            with texture_cols[0]:
                render_metric_card(
                    "Best / Worst Trade",
                    f"{best_trade:+.2f}% / {worst_trade:+.2f}%",
                )
            with texture_cols[1]:
                render_metric_card(
                    "Avg Hold Time",
                    f"{avg_hold:.1f} hrs",
                    badge=f"median {median_hold:.1f} hrs",
                )
            with texture_cols[2]:
                render_metric_card("Exposure", f"{exposure_pct:.1f}% of time")

            st.markdown("**Quick takeaways**")
            win_loss_display = "∞" if not isinstance(win_loss_ratio, float) or not math.isfinite(win_loss_ratio) else f"{win_loss_ratio:.2f}"
            takeaways = [
                f"- {total_trades} trades simulated across the selected window.",
                f"- Equity {'grew' if net_return >= 0 else 'declined'} by {abs(net_return):.2f}% with a max drawdown of {max_drawdown:.2f}%.",
                f"- Strategy was in the market {exposure_pct:.1f}% of the time, holding trades for about {avg_hold:.1f} hours on average.",
                f"- Win/loss ratio: {win_loss_display} with gross gains of +{gross_gain:.2f}% versus losses of -{gross_loss:.2f}%.",
            ]
            st.markdown("\n".join(takeaways))

            if equity_curve is not None and not equity_curve.empty:
                st.markdown("##### Equity Curve (net of fees)")
                equity_fallback = False
                if PLOTLY_AVAILABLE:
                    try:
                        equity_fig = plot_equity_curve(equity_curve, trades_df if trades_df is not None and not trades_df.empty else None)
                        st.plotly_chart(
                            equity_fig,
                            use_container_width=True,
                            config={"displayModeBar": False},
                        )
                    except Exception as exc:
                        equity_fallback = True
                        st.error(f"Could not render Plotly equity curve ({exc}). Showing simplified view.")
                        fallback_chart = plot_equity_curve_altair(equity_curve)
                        st.altair_chart(fallback_chart, use_container_width=True)
                else:
                    equity_fallback = True
                    fallback_chart = plot_equity_curve_altair(equity_curve)
                    st.altair_chart(fallback_chart, use_container_width=True)

                if equity_fallback:
                    st.caption("Simplified equity curve shown. Install `plotly` for enhanced interactivity.")
                else:
                    st.caption("Shows how the portfolio would have evolved after slippage (0.05%) and commission (0.07%) deductions.")

            if trades_df is not None and not trades_df.empty:
                st.markdown("##### Trade Log")
                trades_show = trades_df[
                    ["entry_time", "exit_time", "entry_price", "exit_price", "pnl_pct", "duration_hrs"]
                ].copy()
                trades_show.columns = [
                    "Entry",
                    "Exit",
                    "Entry Price",
                    "Exit Price",
                    "PnL (%)",
                    "Hold (hrs)",
                ]
                st.dataframe(trades_show.round(2), width="stretch")
            else:
                st.info("Backtest completed, but no closed trades were recorded for this window.")

            with st.expander("How to read these stats"):
                st.markdown(
                    """
                    - **Net Return** aggregates every closed trade and compares the final balance to the starting cash.
                    - **Max Drawdown** captures the worst peak-to-trough dip of the equity curve, a proxy for risk.
                    - **Profit Factor** is gross profits divided by gross losses; values above 1.3 are generally resilient.
                    - **Exposure** tracks how often the strategy was in a position so you can gauge capital utilisation.
                    """
                )

            with st.expander("Backtest assumptions & limits"):
                st.markdown(
                    """
                    - Long-only execution using the generated signals; shorts are not simulated.
                    - Commission is fixed at 0.07% per side and slippage at 0.05%, even in volatile candles.
                    - Orders are filled at the close price of the signal candle; intra-candle stops are not modelled.
                    - Results depend on the lookback window; rerun with different ranges to stress test robustness.
                    """
                )
