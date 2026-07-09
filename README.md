```
# ⚡ ArbitrageIQ — Real-Time Crypto Arbitrage Trading Terminal

A production-grade crypto arbitrage scanner monitoring 5 exchanges and 30 symbols — with fee-adjusted profit calculations, async architecture, Telegram alerts, and a live Streamlit terminal.

**Live demo:** https://yemifatodu-arbitrageiq.streamlit.app/  
**Repo:** https://github.com/yemifatodu/arbitrageiq

---

## What it does

ArbitrageIQ scans 5 major cryptocurrency exchanges (Binance, KuCoin, Bybit, OKX, Gate.io) across 30 trading pairs in real-time, calculating **true net profit after all fees** (trading + withdrawal). It delivers instant Telegram alerts and persists historical opportunities in a SQLite database with full analytics.

### Key features

- **Async price fetching** — 150 concurrent requests complete in ~150ms
- **Fee-adjusted profit calculation** — accounts for trading fees + withdrawal fees per exchange
- **Liquidity filtering** — ignores pairs with <$100k volume (slippage protection)
- **Real-time Telegram alerts** — instant notifications to your phone
- **Historical tracking** — SQLite database with analytics dashboard
- **Geographic filtering** — Nigeria-accessible exchanges only (removed Kraken, Coinbase)
- **Professional UI** — Binance-inspired dark theme with 4-tab terminal

## System metrics

| Metric | Value |
|--------|-------|
| Exchanges monitored | 5 (Binance, KuCoin, Bybit, OKX, Gate.io) |
| Symbols tracked | 30 (BTC, ETH, SOL, INJ, ARB, etc.) |
| Avg scan time | ~150ms (150 concurrent requests) |
| Min breakeven threshold | 0.15% (after fees) |
| Opportunity hit rate | 2-3% of scans find >0.15% net profit |
| System uptime | 24/7 background scanner |

### Opportunity distribution

| Tier | Net Profit Range | % of Opportunities |
|------|------------------|---------------------|
| High | >0.5% | ~2% |
| Medium | 0.1-0.5% | ~15% |
| Low / Unprofitable | <0.1% or negative | ~83% |

## Tech stack

- **Backend:** Python, asyncio, CCXT, SQLite
- **Frontend:** Streamlit, Plotly, custom CSS (Binance-inspired dark theme)
- **Notifications:** Telegram Bot API
- **Data:** pandas, numpy

## Installation

```bash
git clone https://github.com/yemifatodu/arbitrageiq.git
cd arbitrageiq
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root directory with your Telegram credentials:

```env
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## Usage

### 1. Run the background scanner

The scanner runs independently of the UI. It fetches prices, calculates arbitrage, saves to the database, and sends Telegram alerts.

```bash
python scanner.py --interval 10 --threshold 0.15 --notify
```

**CLI Arguments:**
- `--interval` — scan interval in minutes (default: 10)
- `--threshold` — minimum net profit % (default: 0.15)
- `--notify` — send Telegram alerts (default: True)
- `--silent-none` — skip alert when no opportunities found (default: True)
- `--once` — run once and exit (used by the Streamlit "Manual Scan" button)

### 2. Run the Streamlit terminal

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser to view the live dashboard, filterable opportunities, and analytics.

## Project structure

```
arbitrageiq/
├── app.py                      # Streamlit terminal (UI, analytics, history)
├── scanner.py                  # Background scanner (async fetching, detection, alerts)
├── database.py                 # SQLite database manager
├── requirements.txt            # Python dependencies
├── .env                        # Telegram credentials (not in repo)
├── src/
│   ├── config.py               # Configuration (fees, thresholds, credentials)
│   ├── arbitrage.py            # Arbitrage detection logic (fee calculation)
│   ├── exchanges.py            # Exchange manager (CCXT integration, async fetching)
│   └── notifications.py        # Telegram alert manager
├── data/
│   └── arbitrage.db            # SQLite database (persisted opportunities)
└── images/
    └── telegram_qr.png         # Telegram channel QR code
```

## limitations

### Execution latency

**This is the big one.** ArbitrageIQ detects opportunities in real-time, but **manual execution is too slow** to capture them profitably. By the time you:
1. See the Telegram alert
2. Open your exchange app
3. Buy the asset
4. Withdraw to the second exchange (10-30 min confirmation)
5. Sell the asset

...the opportunity is long gone. Price discrepancies last **seconds**, not minutes.

### What's needed for profitability

To make this system actually profitable, you'd need:
1. **Pre-funded accounts** on all 5 exchanges (eliminates withdrawal delay)
2. **Automated execution engine** (separate trading bot that executes instantly via API)
3. **Co-located servers** near exchange APIs (reduce network latency)
4. **WebSocket connections** instead of REST polling (faster price updates)

### Current scope

ArbitrageIQ is a **decision-support tool and research platform**, not an automated trading bot. It's excellent for:
- Understanding market microstructure
- Identifying which exchange pairs have persistent spreads
- Backtesting arbitrage strategies
- Learning async Python and trading system architecture

For live trading, you'd need to build the execution layer on top of this detection layer.

## Future work

1. **Automated execution engine** — build a trading bot that executes instantly via API
2. **WebSocket integration** — replace REST polling with real-time subscriptions
3. **Machine learning** — train classifier to predict opportunity persistence
4. **Multi-chain arbitrage** — expand to DEX arbitrage (Uniswap, PancakeSwap)
5. **Risk management** — max position size, daily loss limits, circuit breakers
6. **Automated testing and CI** — add unit tests, integration tests, deployment pipeline


## Acknowledgements

- CCXT library for unified exchange API
- Streamlit for the interactive dashboard framework
- Telegram Bot API for real-time notifications

---

**Built by Yemi Fatodu** — Data Scientist · Full-Stack Product Builder  
Open to freelance & contract engagements.  
[Portfolio](https://yemifatodu.online) · [LinkedIn](https://linkedin.com/in/yemifatodu) · [GitHub](https://github.com/yemifatodu)
```
