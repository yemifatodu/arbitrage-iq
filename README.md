# ⚡ ArbitrageIQ

A real-time crypto arbitrage scanner that monitors five centralized exchanges for fee-adjusted profit opportunities, stores them in SQLite, and pushes instant alerts to Telegram. Built as a decision-support tool for spotting inefficiencies — not an automated execution bot.

**Live Demo:** https://yemifatodu-arbitrageiq.streamlit.app
**Portfolio Case Study:** https://yemifatodu.online/projects/arbitrageiq

---

## What It Does

Price discrepancies between exchanges create short-lived, theoretically risk-free profit windows — but they typically last well under a minute and are impossible to track manually across multiple venues. ArbitrageIQ automates that monitoring:

- Scans **5 exchanges** (Binance, KuCoin, Bybit, OKX, Gate) across **30 symbols** every scan cycle
- Calculates **true net profit** — spread minus buy fee, sell fee, and withdrawal fee — not just raw price difference
- Persists every detected opportunity to SQLite for historical tracking
- Sends real-time Telegram alerts the moment a profitable opportunity clears the threshold
- Provides a live Streamlit terminal (dashboard, opportunity feed, analytics, history/export)

## Key Features

- **Async concurrent scanning** — fetches 150 price points per cycle (5 exchanges × 30 symbols) using `asyncio.gather` with sync CCXT calls run through a thread executor
- **Fee-aware detection** — every opportunity accounts for exchange-specific trading fees and withdrawal fees before it's flagged as profitable
- **Geo-aware exchange selection** — filtered to exchanges accessible from Nigeria (Kraken, Coinbase, and Bitfinex excluded due to IP blocking / reliability issues)
- **Liquidity filtering** — ignores pairs with under $100k in trading volume to avoid slippage-prone, illiquid opportunities
- **Decoupled background scanner** — `scanner.py` runs independently of the Streamlit UI, so scanning continues even when no one has the dashboard open
- **Telegram integration** — rich, formatted alerts with route, prices, spread, fees, and net profit per opportunity

## System Metrics (Verified)

| Metric | Value |
|---|---|
| Exchanges monitored | 5 (Binance, KuCoin, Bybit, OKX, Gate) |
| Symbols tracked | 30 |
| Concurrent requests per scan | 150 (5 × 30) |
| Minimum volume filter | $100,000 USD |
| Default scan interval | 10 minutes |
| Persistence | SQLite (`data/arbitrage.db`) |
| Alert channel | Telegram Bot API |

*Note: exchange-frequency and hit-rate statistics are intentionally omitted from this documentation. Current production data (as of this writing) spans a single ~15-hour window with 15 total logged opportunities — not a large enough sample to report meaningful percentages. These will be added once sufficient historical data has accumulated.*

## Tech Stack

- **Data & Exchanges:** CCXT, asyncio
- **Detection Logic:** pandas
- **Persistence:** SQLite
- **Dashboard:** Streamlit, Plotly
- **Alerts:** Telegram Bot API (`requests`)
- **Background Scanning:** standalone Python process (`scanner.py`), independent of the web UI

## Installation

```powershell
git clone https://github.com/yemifatodu/arbitrageiq.git
cd arbitrageiq
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in the project root with your Telegram credentials:

```
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## Usage

**Run the Streamlit dashboard:**
```powershell
streamlit run app.py
```

**Run the background scanner continuously (default: every 10 minutes):**
```powershell
python scanner.py --interval 10 --threshold 0.15
```

**Run a single scan and exit:**
```powershell
python scanner.py --once
```

**Common flags:**
| Flag | Default | Description |
|---|---|---|
| `--interval` | `10` | Minutes between scans |
| `--threshold` | `0.15` | Minimum net profit % to log/alert |
| `--notify` | `True` | Send Telegram alerts |
| `--silent-none` | `True` | Skip Telegram message when no opportunities are found |
| `--once` | — | Run a single scan cycle and exit (used by the dashboard's manual scan button) |

## Project Structure

```
arbitrageiq/
├── app.py                  # Streamlit dashboard (Dashboard, Opportunities, Analytics, History tabs)
├── scanner.py               # Standalone background scanner + Telegram alert formatting
├── database.py               # SQLite schema, save/query/export logic
├── src/
│   ├── config.py            # Fee tables, volume filter, Telegram credentials
│   ├── exchanges.py          # ExchangeManager — async price fetching across 5 exchanges
│   ├── arbitrage.py          # ArbitrageDetector — spread + fee-adjusted profit calculation
│   └── notifications.py       # NotificationManager — Telegram alert delivery
└── data/
    └── arbitrage.db          # SQLite database (created on first run)
```

## Honest Limitations

- **Decision-support, not auto-execution.** ArbitrageIQ detects and alerts on opportunities; it does not place trades. By the time a human acts on an alert, the spread may have closed.
- **OKX and Gate fee entries are estimated, not confirmed.** The fee tables in `src/config.py` include verified rates for Binance, KuCoin, Kraken, Coinbase, Bitfinex, Bybit, and Bitbns. OKX (0.1%) and Gate (0.2%) use standard published taker rates as placeholders and have not yet been confirmed against actual account-tier fees — net profit figures for opportunities routed through these two exchanges may be slightly under- or overstated until this is verified.
- **Small sample size.** Historical statistics (exchange win-rate, hit rate, profit-tier distribution) are not yet reported publicly because current logged data is limited (15 opportunities over ~15 hours as of this writing). These will be added as more data accumulates.
- **Latency between detection and execution** remains the primary real-world bottleneck — a detected 0.2% net profit opportunity can vanish within seconds of being logged.
- **No slippage modeling.** Profit calculations use last-traded price, not order book depth, so large orders may not achieve the calculated profit in practice.

## Future Work

- Confirm and hardcode verified OKX/Gate fee rates once account-tier data is available
- Add hit-rate and exchange-distribution analytics once sufficient historical data (100+ logged opportunities) has accumulated
- Explore semi-automated execution for the highest-confidence opportunity tier
- Add per-symbol historical spread charts to the Analytics tab

## License

MIT

## Acknowledgements

Built by [Yemi Fatodu](https://yemifatodu.online) — Data Scientist & Full-Stack Product Builder.
[LinkedIn](https://linkedin.com/in/yemifatodu) · [Telegram Alerts](https://t.me/YemiCryptoTracker_Bot)
