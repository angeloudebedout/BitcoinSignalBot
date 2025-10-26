from __future__ import annotations

from importlib import import_module
from typing import Any, Dict, Tuple

__all__ = [
    "get_btc_ohlc",
    "rsi",
    "rsi_signal",
    "plot_btc_chart",
    "plot_equity_curve",
    "plot_price_rsi",
    "run",
]

_LAZY_ATTRS: Dict[str, Tuple[str, str]] = {
    "get_btc_ohlc": ("signalbot.data", "get_btc_ohlc"),
    "rsi": ("signalbot.indicators", "rsi"),
    "rsi_signal": ("signalbot.strategy", "rsi_signal"),
    "plot_btc_chart": ("signalbot.plotting", "plot_btc_chart"),
    "plot_equity_curve": ("signalbot.plotting", "plot_equity_curve"),
    "run": ("signalbot.main", "run"),
}

_ALIASES: Dict[str, str] = {
    "plot_price_rsi": "plot_btc_chart",
}


def __getattr__(name: str) -> Any:
    if name in _ALIASES:
        target = _ALIASES[name]
        value = __getattr__(target)
        globals()[name] = value
        return value

    try:
        module_name, attr_name = _LAZY_ATTRS[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise AttributeError(f"module {__name__} has no attribute {name}") from exc

    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(__all__))
