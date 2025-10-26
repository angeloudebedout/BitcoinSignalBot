# 🧠 BTC Signal Bot

Streamlit dashboard and Python toolkit for monitoring Bitcoin, generating RSI/MACD based trade signals, and reviewing simulated performance.

## ✨ Features
- **Market data ingestion** — pulls BTC‑USD candles from Yahoo Finance with automatic resampling for 4h/weekly/monthly views.
- **Signal engine** — RSI crossovers filtered by EMA trend and MACD confirmation with divergence tagging.
- **Backtesting** — fee & slippage aware long-only simulation that reports win rate, drawdown, exposure, and full trade logs.
- **Interactive UI** — Plotly-powered overlays, downloadable CSVs, and optional auto-refresh.
- **Automated tests** — unit coverage for the signal engine and backtester.

## 🚀 Quick start
```bash
git clone https://github.com/angeloudebedout/BTCSignalBot.git
cd BTCSignalBot

# Set up Python environment (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run unit tests
python -m unittest discover -s Tests

# Launch the dashboard
streamlit run streamlit_app.py
```

The Streamlit UI defaults to 4h candles and refreshes automatically. Tweak indicator parameters from the sidebar and toggle overlays for MACD, RSI, EMAs, Bollinger Bands, divergence markers, or backtest trades.

## 📦 Package usage
```python
from signalbot.main import run

df = run(interval="1h", oversold=25, overbought=75, lookback_days=120)
print(df.tail()[["close", "rsi", "signal", "signal_strength"]])
```

`signalbot.backtest.backtest_signals(df)` returns `(metrics, trades_df, equity_curve)` so you can integrate simulated performance elsewhere.

## ☁️ Deploying to Streamlit Cloud
1. Push the repository to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io/), create a new app pointing to `streamlit_app.py`.
3. Set `python -m venv .venv && pip install -r requirements.txt` as the build step (or reuse Streamlit Cloud’s cached pip env).
4. Expose `streamlit_app.py` as the entry point. Auto-refresh works out of the box.

## 🛠️ Project structure
```
signalbot/
  data.py        # Yahoo Finance ingestion helpers
  indicators.py  # RSI, EMA, MACD, Bollinger, candlestick patterns
  strategy.py    # Signal generation and divergence detection
  backtest.py    # Fee-aware performance simulation
  plotting.py    # Plotly figure factories used by the UI
streamlit_app.py # Streamlit dashboard
Tests/           # Unit tests for strategy & backtester
```

## 🤝 Contributing
Issues and PRs are welcome. Please:
- Keep the test suite green (`python -m unittest discover -s Tests`)
- Run `python -m compileall streamlit_app.py signalbot Tests` to catch syntax errors
- Use descriptive commit messages so deployment diffs stay clear

---

Maintained by [Angelou deBedout](https://github.com/angeloudebedout). If you ship improvements or deploy your own dashboard, feel free to share! 🚀


---

## 🧩 Dependencies & Setup

This project was developed and tested with:

| Library | Version |
|----------|----------|
| Python | 3.10+ |
| streamlit | 1.39.0 |
| streamlit-autorefresh | 1.0.1 |
| plotly | 5.24.1 |
| pandas | 2.2.3 |
| numpy | 1.26.4 |
| matplotlib | 3.9.2 |
| requests | 2.32.3 |
| yfinance | 0.2.43 |
| scikit-learn | 1.5.2 |
| pytest | 8.3.3 |

### Quick setup
```bash
python3 -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run streamlit_app.py

