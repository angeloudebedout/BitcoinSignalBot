# 🧠 BTC Signal Bot

Streamlit-powered command center for watching Bitcoin price action, producing RSI/MACD-informed trade calls, and auditing simulated performance without leaving your browser.

## ✨ Features
- **Market data ingestion** — fetches BTC-USD candles from Yahoo Finance, then reshapes them into 4h, weekly, or monthly frames automatically.
- **Signal engine** — couples RSI crossover triggers with EMA trend gating, MACD confirmation, and divergence annotations.
- **Backtesting** — simulates long-only execution with fees and slippage baked in, reporting win rate, drawdown, exposure, and every trade.
- **Interactive UI** — Plotly overlays, downloadable CSV output, and an auto-refresh toggle keep dashboards current.
- **Automated tests** — unit suites cover the strategy core and backtester to guard against regressions.

## 🚀 Quick start
```bash
git clone https://github.com/angeloudebedout/BTCSignalBot.git
cd BTCSignalBot

# Create a Python environment (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run unit tests
python -m unittest discover -s Tests

# Launch the dashboard
streamlit run streamlit_app.py
```

The Streamlit board boots into 4h candles with auto-refresh enabled. Adjust indicator knobs in the sidebar and flip on overlays for MACD, RSI, EMAs, Bollinger Bands, divergence markers, or backtest trades.

## 📦 Package usage
```python
from signalbot.main import run

df = run(interval="1h", oversold=25, overbought=75, lookback_days=120)
print(df.tail()[["close", "rsi", "signal", "signal_strength"]])
```

`signalbot.backtest.backtest_signals(df)` yields `(metrics, trades_df, equity_curve)`, letting you slot the simulated track record into other workflows.

## ☁️ Deploying to Streamlit Cloud
1. Push the repository to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io/), create a new app pointing to `streamlit_app.py`.
3. Use `python -m venv .venv && pip install -r requirements.txt` for the build step (or lean on Streamlit Cloud's cached pip env).
4. Surface `streamlit_app.py` as the entry point—auto-refresh is already wired up.

## 🛠️ Project structure
```
signalbot/
  data.py        # Yahoo Finance ingestion helpers
  indicators.py  # RSI, EMA, MACD, Bollinger, candlestick patterns
  strategy.py    # Signal generation and divergence detection
  backtest.py    # Fee-aware performance simulation
  plotting.py    # Plotly figure factories used by the UI
streamlit_app.py # Streamlit dashboard
Tests/           # Unit tests for strategy and backtester
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
