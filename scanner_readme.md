# ArbitrageIQ — Scanner Setup Guide

## How It Works
- `scanner.py` runs in the background 24/7, scanning every N minutes
- Results are saved to SQLite database automatically
- `app.py` reads from the same database in real-time
- Telegram alerts sent for every opportunity found

---

## Step 1 — Set up Telegram Bot

1. Open Telegram, search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy your **bot token** (looks like `123456:ABC-DEF...`)
4. Start a chat with your bot, then get your chat ID:
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Copy the `"id"` value from the response

5. Add to your `.env` file:
```
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

---

## Step 2 — Run the Background Scanner

Open a NEW terminal (keep Streamlit running in the other one):

```powershell
cd C:\Users\HP\crypto-arbitrage-tracker
.\venv\Scripts\Activate.ps1

# Scan every 10 minutes, alert on opportunities ≥ 0.15% profit
python scanner.py --interval 10 --threshold 0.15

# Scan every 5 minutes
python scanner.py --interval 5 --threshold 0.1

# Scan every 15 minutes
python scanner.py --interval 15 --threshold 0.2

# Run once and exit (good for testing)
python scanner.py --once --threshold 0.1
```

---

## Step 3 — Run the Dashboard (separate terminal)

```powershell
cd C:\Users\HP\crypto-arbitrage-tracker
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

The dashboard auto-refreshes every 60 seconds and shows:
- Live opportunities from the scanner
- Historical data from DB
- Analytics charts

---

## Recommended Thresholds

| Market Condition | Threshold | Interval |
|---|---|---|
| Volatile (news/pump) | 0.10% | 5 min |
| Normal | 0.15% | 10 min |
| Quiet | 0.20% | 15 min |

---

## Run Scanner on Windows Startup (Optional)

Create `start_scanner.bat`:
```batch
cd C:\Users\HP\crypto-arbitrage-tracker
call venv\Scripts\activate
python scanner.py --interval 10 --threshold 0.15
```

Add to Windows Task Scheduler to auto-start on boot.

---

## Telegram Alert Example

```
🟢 ARBITRAGE OPPORTUNITY
━━━━━━━━━━━━━━━━━━━━
Pair: SOL/USDT
Route: GATE → KUCOIN

💰 Prices
  Buy:  $71.74 on gate
  Sell: $71.93 on kucoin

📊 Metrics
  Spread:      0.265%
  Fees:        0.205%
  Net Profit:  0.060%
  Per coin:    $0.0431
  Volume:      $2,847,291

🕐 2026-06-27 14:32:11 UTC
━━━━━━━━━━━━━━━━━━━━
ArbitrageIQ · yemifatodu.online
```
