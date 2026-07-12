import streamlit as st
import pandas as pd
import asyncio
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(__file__))

from src.config import Config
from src.exchanges import ExchangeManager
from src.arbitrage import ArbitrageDetector
from src.notifications import NotificationManager
from database import DatabaseManager

st.set_page_config(
    page_title="ArbitrageIQ | Trading Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    .stApp { background-color: #0B0E11; }
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: #0B0E11; }
    ::-webkit-scrollbar-thumb { background: #2D3140; border-radius: 2px; }

    [data-testid="stSidebar"] { background: #13161C; border-right: 1px solid #1E2329; }
    [data-testid="stSidebar"] * { color: #848E9C !important; }
    [data-testid="stSidebar"] hr { border-color: #1E2329 !important; }
    [data-testid="stSidebar"] a { color: #F0B90B !important; }
    [data-testid="stAppViewContainer"] > .main { background-color: #0B0E11; padding: 0; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    .ticker-wrap { background: #13161C; border-bottom: 1px solid #1E2329;
                   padding: 8px 0; overflow: hidden; white-space: nowrap; }
    .ticker-inner { display: inline-block; animation: ticker 30s linear infinite; }
    .ticker-inner:hover { animation-play-state: paused; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
    .ticker-item { display: inline-block; margin: 0 28px;
                   font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; }
    .ticker-symbol { color: #EAECEF; font-weight: 600; }
    .ticker-price  { color: #EAECEF; margin: 0 6px; }
    .ticker-up   { color: #0ECB81; }
    .ticker-down { color: #F6465D; }

    .top-nav { background: #13161C; border-bottom: 1px solid #1E2329;
               padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; }
    .brand { display: flex; align-items: center; gap: 10px; }
    .brand-icon { width: 34px; height: 34px; background: linear-gradient(135deg,#F0B90B,#F8D12F);
                  border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
    .brand-name { font-size: 1.1rem; font-weight: 700; color: #EAECEF; letter-spacing: -0.3px; }
    .brand-name span { color: #F0B90B; }
    .live-badge { background: rgba(14,203,129,0.12); border: 1px solid rgba(14,203,129,0.3);
                  color: #0ECB81; font-size: 0.65rem; font-weight: 700; letter-spacing: 1.5px;
                  padding: 3px 10px; border-radius: 4px; margin-left: 10px; }
    .nav-meta { font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: #5E6673; text-align: right; }

    .stTabs [data-baseweb="tab-list"] { background: #13161C; border-bottom: 1px solid #1E2329;
                                         gap: 0; padding: 0 24px; border-radius: 0; }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 0; padding: 12px 20px;
                                    color: #5E6673; font-size: 0.8rem; font-weight: 500;
                                    border-bottom: 2px solid transparent; margin-bottom: -1px; }
    .stTabs [data-baseweb="tab"]:hover { color: #EAECEF; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #F0B90B;
        border-bottom: 2px solid #F0B90B; background: transparent; }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"]    { display: none; }

    .stat-card { background: #13161C; border: 1px solid #1E2329; border-radius: 8px;
                 padding: 16px 18px; position: relative; overflow: hidden; }
    .stat-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px;
                          background: linear-gradient(90deg,#F0B90B,transparent); }
    .stat-card-green::before { background: linear-gradient(90deg,#0ECB81,transparent); }
    .stat-card-red::before   { background: linear-gradient(90deg,#F6465D,transparent); }
    .stat-card-blue::before  { background: linear-gradient(90deg,#3B82F6,transparent); }
    .stat-card-teal::before  { background: linear-gradient(90deg,#06B6D4,transparent); }
    .stat-label { font-size:0.65rem; font-weight:600; letter-spacing:1.5px;
                  text-transform:uppercase; color:#5E6673; margin-bottom:8px; }
    .stat-value { font-family:'IBM Plex Mono',monospace; font-size:1.8rem;
                  font-weight:600; color:#EAECEF; line-height:1; }
    .stat-value-green { color:#0ECB81; }
    .stat-value-red   { color:#F6465D; }
    .stat-value-gold  { color:#F0B90B; }
    .stat-sub { font-size:0.68rem; color:#5E6673; margin-top:5px; font-family:'IBM Plex Mono',monospace; }

    .panel { background:#13161C; border:1px solid #1E2329; border-radius:8px;
             overflow:hidden; margin-bottom:16px; }
    .panel-header { background:#1A1D24; padding:10px 16px; border-bottom:1px solid #1E2329;
                    display:flex; align-items:center; justify-content:space-between; }
    .panel-title { font-size:0.68rem; font-weight:700; letter-spacing:1.5px;
                   text-transform:uppercase; color:#848E9C; }

    .opp-table-header { display:grid; grid-template-columns:80px 1fr 1fr 100px 100px 90px;
                         gap:8px; padding:8px 16px; border-bottom:1px solid #1E2329;
                         font-size:0.63rem; font-weight:700; letter-spacing:1.5px;
                         text-transform:uppercase; color:#5E6673; }
    .opp-row { display:grid; grid-template-columns:80px 1fr 1fr 100px 100px 90px;
               gap:8px; padding:12px 16px; border-bottom:1px solid #1A1D24;
               align-items:center; transition:background 0.15s; }
    .opp-row:hover { background:#1A1D24; }
    .opp-row:last-child { border-bottom:none; }
    .opp-symbol { font-family:'IBM Plex Mono',monospace; font-size:0.85rem; font-weight:600; color:#EAECEF; }
    .opp-price  { font-family:'IBM Plex Mono',monospace; font-size:0.75rem; color:#848E9C; }
    .profit-pill-high { background:rgba(14,203,129,0.12); border:1px solid rgba(14,203,129,0.25);
                        color:#0ECB81; font-family:'IBM Plex Mono',monospace; font-size:0.8rem;
                        font-weight:600; padding:4px 10px; border-radius:4px; display:inline-block; }
    .profit-pill-mid  { background:rgba(240,185,11,0.12); border:1px solid rgba(240,185,11,0.25);
                        color:#F0B90B; font-family:'IBM Plex Mono',monospace; font-size:0.8rem;
                        font-weight:600; padding:4px 10px; border-radius:4px; display:inline-block; }
    .profit-pill-low  { background:rgba(246,70,93,0.12); border:1px solid rgba(246,70,93,0.25);
                        color:#F6465D; font-family:'IBM Plex Mono',monospace; font-size:0.8rem;
                        font-weight:600; padding:4px 10px; border-radius:4px; display:inline-block; }
    .buy-tag  { background:rgba(14,203,129,0.08); color:#0ECB81; font-size:0.68rem; font-weight:600;
                padding:2px 7px; border-radius:3px; font-family:'IBM Plex Mono',monospace; }
    .sell-tag { background:rgba(246,70,93,0.08); color:#F6465D; font-size:0.68rem; font-weight:600;
                padding:2px 7px; border-radius:3px; font-family:'IBM Plex Mono',monospace; }

    /* Watchlist coin chips */
    .coin-chip { display:inline-flex; align-items:center; gap:5px;
                 background:#1E2329; border:1px solid #2D3140; border-radius:4px;
                 padding:4px 10px; margin:3px; font-family:'IBM Plex Mono',monospace;
                 font-size:0.72rem; color:#848E9C; }
    .coin-chip-active { border-color:#0ECB81; color:#0ECB81; background:rgba(14,203,129,0.06); }
    .coin-dot { width:5px; height:5px; border-radius:50%; background:#5E6673; }
    .coin-dot-active { background:#0ECB81; }

    /* Telegram CTA card */
    .tg-card { background:linear-gradient(135deg,#0D1F3C 0%,#1A1D24 100%);
               border:1px solid #2A4A7F; border-radius:10px; padding:20px 22px;
               margin-bottom:16px; display:flex; align-items:center; justify-content:space-between; gap:16px; }
    .tg-left { display:flex; align-items:center; gap:14px; }
    .tg-icon { width:44px; height:44px; background:linear-gradient(135deg,#229ED9,#1A8BC4);
               border-radius:10px; display:flex; align-items:center; justify-content:center;
               font-size:1.4rem; flex-shrink:0; }
    .tg-title { font-size:0.9rem; font-weight:700; color:#EAECEF; margin-bottom:4px; }
    .tg-desc  { font-size:0.75rem; color:#848E9C; line-height:1.5; }
    .tg-btn   { background:linear-gradient(135deg,#229ED9,#1A8BC4); color:#FFFFFF;
                border:none; border-radius:6px; padding:10px 20px; font-size:0.8rem;
                font-weight:700; letter-spacing:0.5px; cursor:pointer; white-space:nowrap;
                text-decoration:none; display:inline-block; }

    /* Scanner status */
    .scanner-status { background:#13161C; border:1px solid #1E2329; border-radius:8px;
                      padding:12px 18px; margin-bottom:16px; display:flex;
                      align-items:center; justify-content:space-between; }
    .scanner-dot-on  { width:8px; height:8px; background:#0ECB81; border-radius:50%;
                        display:inline-block; margin-right:8px; animation:pulse 2s infinite; }
    .scanner-dot-off { width:8px; height:8px; background:#5E6673; border-radius:50%;
                        display:inline-block; margin-right:8px; }
    @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }

    /* Exchange badges */
    .ex-badge { background:#1E2329; border:1px solid #2D3140; border-radius:6px;
                padding:8px 14px; display:inline-block; margin:4px;
                font-family:'IBM Plex Mono',monospace; font-size:0.75rem; color:#848E9C; }
    .ex-badge-on { border-color:#0ECB81; color:#0ECB81; background:rgba(14,203,129,0.08); }

    .stButton > button[kind="primary"] {
        background:linear-gradient(135deg,#F0B90B,#F8D12F) !important; color:#0B0E11 !important;
        border:none !important; border-radius:6px !important; font-weight:700 !important;
        font-size:0.85rem !important; letter-spacing:1px !important; text-transform:uppercase !important;
        padding:12px 0 !important; box-shadow:0 4px 16px rgba(240,185,11,0.25) !important; }
    .stButton > button[kind="primary"]:hover { box-shadow:0 6px 24px rgba(240,185,11,0.4) !important; }
    .stButton > button:not([kind="primary"]) { background:#1E2329 !important; color:#848E9C !important;
        border:1px solid #2D3140 !important; border-radius:6px !important; font-size:0.8rem !important; }

    [data-testid="stMetric"] { background:#13161C; border:1px solid #1E2329; border-radius:6px; padding:12px 14px; }
    [data-testid="stMetricLabel"] { font-size:0.65rem !important; font-weight:700 !important;
                                    letter-spacing:1.5px !important; text-transform:uppercase !important; color:#5E6673 !important; }
    [data-testid="stMetricValue"] { font-family:'IBM Plex Mono',monospace !important;
                                    font-size:1.3rem !important; font-weight:600 !important; color:#EAECEF !important; }
    [data-testid="stDataFrame"] { background:#13161C !important; border:1px solid #1E2329 !important; border-radius:6px !important; }
    [data-testid="stAlert"] { border-radius:6px !important; }
    label { color:#848E9C !important; font-size:0.75rem !important; font-weight:500 !important;
            text-transform:uppercase !important; letter-spacing:0.8px !important; }
    [data-testid="stSlider"] > div > div > div { background:#F0B90B !important; }
    [data-testid="stMultiSelect"] > div { background:#1E2329 !important;
        border:1px solid #2D3140 !important; border-radius:6px !important; }

    .terminal-footer { background:#13161C; border-top:1px solid #1E2329; padding:10px 24px;
                       display:flex; justify-content:space-between; align-items:center; margin-top:24px; }
    .footer-left  { font-family:'IBM Plex Mono',monospace; font-size:0.62rem; color:#2D3140; }
    .footer-right { font-size:0.62rem; color:#2D3140; }
    .footer-right a { color:#F0B90B !important; text-decoration:none; }
</style>
""", unsafe_allow_html=True)

# ── Init ──────────────────────────────────────────────────────────────────────
@st.cache_resource
def initialize_components():
    return {
        'exchange_manager': ExchangeManager(),
        'detector':         ArbitrageDetector(),
        'notifier':         NotificationManager(),
        'database':         DatabaseManager(),
    }

components = initialize_components()
db = components['database']

# ── Watchlist ─────────────────────────────────────────────────────────────────
SCAN_SYMBOLS = [
    'BTC','ETH','BNB','SOL','XRP','ADA','DOT','DOGE','AVAX','MATIC',
    'LINK','NEAR','INJ','ARB','OP','APT','SUI','TRX','ATOM','FIL',
    'LTC','SAND','MANA','AXS','AAVE','CRV','SNX','UNI','MKR','ETC',
]

EXCHANGES = ['BINANCE','KUCOIN','BYBIT','OKX','GATE']

# Telegram channel link — update this to your actual channel
TELEGRAM_CHANNEL = "https://t.me/YemiCryptoTracker_Bot"
TELEGRAM_BOT_LINK = "https://t.me/YemiCryptoTracker_Bot"

# ── Ticker tape ───────────────────────────────────────────────────────────────
# NOTE: these values are static placeholders, not live prices. Wire this to
# ExchangeManager for real-time data before presenting the app as fully "live" —
# a visibly frozen ticker undermines that framing more than removing it would.
ticker_items = [
    ("BTC/USDT","$109,687","+1.09%",True), ("ETH/USDT","$3,842","+2.34%",True),
    ("SOL/USDT","$176.34","+3.45%",True),  ("BNB/USDT","$584.21","+0.87%",True),
    ("XRP/USDT","$0.5234","-1.23%",False), ("ADA/USDT","$0.4521","+2.14%",True),
    ("INJ/USDT","$22.14","+5.21%",True),   ("ARB/USDT","$0.8821","+2.34%",True),
    ("SNX/USDT","$1.92","+0.91%",True),    ("ETC/USDT","$19.42","-0.33%",False),
    ("DOT/USDT","$8.92","-0.54%",False),   ("NEAR/USDT","$4.21","+3.12%",True),
]

def make_ticker(items):
    html = ""
    for sym, price, chg, up in items:
        cls = "ticker-up" if up else "ticker-down"
        html += (f'<span class="ticker-item">'
                 f'<span class="ticker-symbol">{sym}</span>'
                 f'<span class="ticker-price">{price}</span>'
                 f'<span class="{cls}">{chg}</span>'
                 f'</span>')
    return html * 2

st.markdown(f'<div class="ticker-wrap"><div class="ticker-inner">{make_ticker(ticker_items)}</div></div>',
            unsafe_allow_html=True)

# ── Top nav ───────────────────────────────────────────────────────────────────
scanner_active = os.path.exists('scanner.log') and (time.time() - os.path.getmtime('scanner.log') < 900)

scanner_badge = (
    '<span style="color:#0ECB81;font-size:0.65rem;font-weight:700;background:rgba(14,203,129,0.1);'
    'border:1px solid rgba(14,203,129,0.3);padding:3px 10px;border-radius:4px;margin-left:8px;">SCANNER ON</span>'
    if scanner_active else
    '<span style="color:#5E6673;font-size:0.65rem;font-weight:700;background:#1E2329;'
    'border:1px solid #2D3140;padding:3px 10px;border-radius:4px;margin-left:8px;">SCANNER OFF</span>'
)

st.markdown(f"""
<div class="top-nav">
    <div class="brand">
        <div class="brand-icon">⚡</div>
        <div>
            <div class="brand-name">Arbitrage<span>IQ</span>
                <span class="live-badge">LIVE</span>
                {scanner_badge}
            </div>
        </div>
    </div>
    <div class="nav-meta">
        <div style="color:#848E9C;">{datetime.now().strftime('%d %b %Y  %H:%M UTC')}</div>
        <div style="color:#2D3140;margin-top:2px;">v2.0 · SQLite · 5 Exchanges · 30 Symbols</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 12px 0;border-bottom:1px solid #1E2329;margin-bottom:16px;">
        <div style="font-size:0.65rem;font-weight:700;letter-spacing:2px;
                    text-transform:uppercase;color:#5E6673;">Control Panel</div>
    </div>
    """, unsafe_allow_html=True)

    scan_mode = st.radio("Mode", ["Auto (Background Scanner)", "Manual Scan"],
                         label_visibility="collapsed")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    threshold = st.slider("Min Profit Threshold (%)", 0.001, 2.0, 0.005, step=0.001, format="%.3f")

    interval = "10 minutes"  # default fallback so it's always defined below
    if scan_mode == "Auto (Background Scanner)":
        interval = st.selectbox("Scan Interval", ["5 minutes", "10 minutes", "15 minutes"], index=1)
        st.markdown(f"""
        <div style="background:#1A1D24;border:1px solid #2D3140;border-radius:6px;
                    padding:10px 12px;margin-top:8px;font-size:0.72rem;color:#848E9C;line-height:1.8;">
        Scanning every {interval} &nbsp;·&nbsp; Threshold {threshold:.3f}%
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1E2329;margin:14px 0;'>", unsafe_allow_html=True)

    auto_refresh = st.checkbox("Auto-refresh (60s)", value=True)

    # ── Auto-mode scan trigger ──────────────────────────────────────────────
    # This makes "Auto" mode actually run a scan on schedule, instead of being
    # a label with no behavior behind it. IMPORTANT CAVEAT: this only fires
    # while a browser tab is open and the auto-refresh loop is actively
    # cycling (see time.sleep(60) below) — Streamlit Cloud does not run any
    # code when no one is connected, so this is NOT true 24/7 background
    # scanning. For genuine always-on coverage, scanner.py needs to run on a
    # host with a persistent process (a small VPS, a Render/Railway background
    # worker, or a scheduled GitHub Action), not inside this Streamlit app.
    if scan_mode == "Auto (Background Scanner)" and auto_refresh:
        interval_map = {"5 minutes": 300, "10 minutes": 600, "15 minutes": 900}
        interval_sec = interval_map.get(interval, 600)
        last_scan_time = st.session_state.get('last_auto_scan', time.time())
        st.session_state.setdefault('last_auto_scan', last_scan_time)

        if time.time() - last_scan_time >= interval_sec:
            with st.spinner("Running scheduled scan..."):
                try:
                    subprocess.run(
                        [sys.executable, "scanner.py", "--once", f"--threshold={threshold:.3f}"],
                        capture_output=True, timeout=180,
                        cwd=os.path.dirname(os.path.abspath(__file__))
                    )
                except Exception:
                    pass
            st.session_state['last_auto_scan'] = time.time()

    st.markdown("<hr style='border-color:#1E2329;margin:14px 0;'>", unsafe_allow_html=True)

    if st.button("Refresh Now", use_container_width=True):
        st.rerun()

    st.markdown("<hr style='border-color:#1E2329;margin:14px 0;'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:0.68rem;color:#2D3140;line-height:1.9;">
    <strong style="color:#F0B90B;">ArbitrageIQ</strong><br/>
    Built by <strong style="color:#848E9C;">Yemi Fatodu</strong><br/>
    Data Scientist · Full-Stack Builder<br/><br/>
    <a href="https://yemifatodu.online" style="color:#F0B90B;">Portfolio</a> &nbsp;·&nbsp;
    <a href="https://linkedin.com/in/yemifatodu" style="color:#F0B90B;">LinkedIn</a><br/><br/>
    <a href="{TELEGRAM_CHANNEL}" style="color:#229ED9;font-weight:600;">
        Join Telegram Channel
    </a><br/>
    <em style="color:#2D3140;font-size:0.65rem;">Get live alerts on your phone</em>
    </div>
    """, unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "⬛  Dashboard",
    "⚡  Opportunities",
    "📈  Analytics",
    "📋  History"
])

# ── DB data ───────────────────────────────────────────────────────────────────
history_df = db.get_history(limit=500)
stats      = db.get_statistics() or {}

recent_df  = pd.DataFrame()
latest_opps = pd.DataFrame()

if not history_df.empty:
    history_df['ts'] = pd.to_datetime(history_df['timestamp'])
    cutoff24 = datetime.now() - timedelta(hours=24)
    cutoff30 = datetime.now() - timedelta(minutes=30)
    recent_df   = history_df[history_df['ts'] >= cutoff24]
    latest_opps = history_df[history_df['ts'] >= cutoff30]

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div style='padding:20px 24px 0 24px;'>", unsafe_allow_html=True)

    # ── Telegram CTA ──
    tg_col1, tg_col2 = st.columns([2.7, 1])
    with tg_col1:
        st.markdown(f"""
        <div class="tg-card">
            <div class="tg-left">
                <div class="tg-icon">✈</div>
                <div>
                    <div class="tg-title">Get Live Arbitrage Alerts on Telegram</div>
                    <div class="tg-desc">
                        Join the ArbitrageIQ channel to receive instant alerts every time a profitable
                        opportunity is detected — directly on your phone.
                    </div>
                </div>
            </div>
            <div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;">
                <a href="{TELEGRAM_CHANNEL}" target="_blank" class="tg-btn">
                    Join Channel
                </a>
                <span style="font-size:0.65rem;color:#5E6673;font-family:'IBM Plex Mono',monospace;">
                    Free · Instant alerts · No signup
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with tg_col2:
        qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "telegram_qr.png")
        if os.path.exists(qr_path):
            st.image(qr_path, width=130, caption="Scan to join")
        else:
            st.markdown("""
            <div style="background:#13161C;border:1px solid #1E2329;border-radius:8px;
                        padding:30px 10px;text-align:center;font-size:0.65rem;color:#5E6673;">
                QR pending
            </div>
            """, unsafe_allow_html=True)

    # ── Scanner status ──
    total_records = len(history_df) if not history_df.empty else 0
    recent_count  = len(recent_df)  if not recent_df.empty  else 0
    best_profit   = stats.get('best_profit', 0)
    avg_profit    = stats.get('avg_profit', 0)

    last_scan_str = "No scans yet"
    if not history_df.empty:
        last_ts = history_df['ts'].max()
        diff    = datetime.now() - last_ts
        mins    = int(diff.total_seconds() / 60)
        last_scan_str = f"{mins} min ago" if mins < 60 else last_ts.strftime('%H:%M')

    dot_cls = "scanner-dot-on" if scanner_active else "scanner-dot-off"
    status_txt = "RUNNING" if scanner_active else "STOPPED"
    st.markdown(f"""
    <div class="scanner-status">
        <div style="display:flex;align-items:center;">
            <span class="{dot_cls}"></span>
            <span style="font-size:0.75rem;font-weight:600;color:#EAECEF;">
                Background Scanner — {status_txt}
            </span>
        </div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;color:#5E6673;">
            Last data: {last_scan_str} &nbsp;|&nbsp; Total records: {total_records}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stat cards ──
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown("""<div class="stat-card stat-card-blue">
            <div class="stat-label">Exchanges</div>
            <div class="stat-value">5</div>
            <div class="stat-sub">Connected & active</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="stat-card">
            <div class="stat-label">Symbols Tracked</div>
            <div class="stat-value">30</div>
            <div class="stat-sub">Per scan cycle</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        rc_cls = "stat-value-green" if recent_count > 0 else "stat-value"
        st.markdown(f"""<div class="stat-card stat-card-green">
            <div class="stat-label">Last 24h Opps</div>
            <div class="stat-value {rc_cls}">{recent_count}</div>
            <div class="stat-sub">Detected & saved</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="stat-card stat-card-red">
            <div class="stat-label">Best Profit</div>
            <div class="stat-value stat-value-gold">{best_profit:.3f}%</div>
            <div class="stat-sub">Net after fees</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="stat-card stat-card-teal">
            <div class="stat-label">Avg Profit</div>
            <div class="stat-value stat-value-gold">{avg_profit:.3f}%</div>
            <div class="stat-sub">All-time average</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Two columns: watchlist + manual scan / latest results ──
    left_col, right_col = st.columns([1, 1.4], gap="medium")

    with left_col:
        # Exchange badges
        st.markdown("""
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">Active Exchanges</span>
                <span style="font-size:0.65rem;color:#0ECB81;font-family:'IBM Plex Mono',monospace;">5 ONLINE</span>
            </div>
            <div style="padding:12px 14px;display:flex;flex-wrap:wrap;gap:6px;">
                <span class="ex-badge ex-badge-on">BINANCE</span>
                <span class="ex-badge ex-badge-on">KUCOIN</span>
                <span class="ex-badge ex-badge-on">BYBIT</span>
                <span class="ex-badge ex-badge-on">OKX</span>
                <span class="ex-badge ex-badge-on">GATE.IO</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Watchlist - selectable
        active_symbols = set()
        if not recent_df.empty:
            active_symbols = set(recent_df['symbol'].unique())

        st.markdown(f"""
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">Watchlist</span>
                <span style="font-size:0.65rem;color:#F0B90B;font-family:'IBM Plex Mono',monospace;">
                    {len(active_symbols)} HIT IN 24H
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if 'selected_symbols' not in st.session_state:
            st.session_state['selected_symbols'] = SCAN_SYMBOLS.copy()

        selected_symbols = st.multiselect(
            "Select symbols to scan",
            options=SCAN_SYMBOLS,
            default=st.session_state['selected_symbols'],
            label_visibility="collapsed",
            key="watchlist_select"
        )
        st.session_state['selected_symbols'] = selected_symbols

        chip_html = ""
        for sym in selected_symbols:
            is_active = sym in active_symbols
            chip_cls = "coin-chip coin-chip-active" if is_active else "coin-chip"
            dot_c    = "coin-dot coin-dot-active"   if is_active else "coin-dot"
            chip_html += f'<span class="{chip_cls}"><span class="{dot_c}"></span>{sym}</span>'

        st.markdown(f'<div style="padding:8px 0;">{chip_html}</div>', unsafe_allow_html=True)

        # Manual scan
        if scan_mode == "Manual Scan":
            st.markdown("""
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">Manual Scan</span>
                </div>
                <div style="padding:12px 14px;">
            """, unsafe_allow_html=True)

            if st.button("⚡  RUN SCAN NOW", type="primary", use_container_width=True):
                with st.spinner("Scanning..."):
                    try:
                        symbols_arg = ",".join(st.session_state.get('selected_symbols', SCAN_SYMBOLS))
                        result = subprocess.run(
                            [sys.executable, "scanner.py", "--once",
                             f"--threshold={threshold:.3f}",
                             f"--symbols={symbols_arg}"],
                            capture_output=True, text=True, timeout=180,
                            cwd=os.path.dirname(os.path.abspath(__file__))
                        )
                        output = result.stdout + result.stderr
                        found_count = output.lower().count("opportunity:")
                        if found_count > 0:
                            st.success(f"{found_count} opportunities found")
                        else:
                            st.info("No opportunities above threshold")
                        st.rerun()
                    except subprocess.TimeoutExpired:
                        st.warning("Scan timed out.")
                    except Exception as e:
                        st.error("Scan failed.")

            st.markdown("</div></div>", unsafe_allow_html=True)

    with right_col:
        # Latest opportunities from DB
        if not latest_opps.empty:
            st.markdown("""
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">Latest Opportunities</span>
                    <span style="font-size:0.65rem;color:#F0B90B;font-family:'IBM Plex Mono',monospace;">
                        LAST 30 MIN
                    </span>
                </div>
            """, unsafe_allow_html=True)

            for _, row in latest_opps.sort_values('net_profit_pct', ascending=False).head(8).iterrows():
                profit   = row['net_profit_pct']
                pill_cls = "profit-pill-high" if profit >= 0.5 else "profit-pill-mid" if profit >= 0.1 else "profit-pill-low"
                st.markdown(f"""
                <div class="opp-row" style="grid-template-columns:70px 1fr 1fr 100px 90px;">
                    <div class="opp-symbol">{row['symbol']}</div>
                    <div><span class="buy-tag">{row['buy_exchange']}</span>
                         <br/><span class="opp-price">${row['buy_price']:.4f}</span></div>
                    <div><span class="sell-tag">{row['sell_exchange']}</span>
                         <br/><span class="opp-price">${row['sell_price']:.4f}</span></div>
                    <div><span class="{pill_cls}">+{profit:.3f}%</span></div>
                    <div class="opp-price" style="font-size:0.65rem;color:#5E6673;">
                         {row['ts'].strftime('%H:%M:%S')}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Show the most recent opportunity ever recorded, Telegram-style
            if not history_df.empty:
                last_row = history_df.sort_values('ts', ascending=False).iloc[0]
                profit = last_row['net_profit_pct']
                pill_cls = ("profit-pill-high" if profit >= 0.5
                           else "profit-pill-mid" if profit >= 0.1 else "profit-pill-low")
                mins_ago = int((datetime.now() - last_row['ts']).total_seconds() / 60)
                time_label = f"{mins_ago} min ago" if mins_ago < 60 else last_row['ts'].strftime('%H:%M')
                st.markdown(f"""
                <div class="panel">
                    <div class="panel-header">
                        <span class="panel-title">Most Recent Opportunity</span>
                        <span style="font-size:0.65rem;color:#5E6673;font-family:'IBM Plex Mono',monospace;">
                            {time_label}
                        </span>
                    </div>
                    <div style="padding:18px;">
                        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                            <span class="opp-symbol" style="font-size:1.1rem;">{last_row['symbol']}/USDT</span>
                            <span class="{pill_cls}" style="font-size:0.95rem;">+{profit:.3f}%</span>
                        </div>
                        <div style="display:flex;gap:20px;margin-bottom:10px;">
                            <div>
                                <span class="buy-tag">{last_row['buy_exchange']}</span>
                                <div class="opp-price" style="margin-top:4px;">${last_row['buy_price']:.4f}</div>
                            </div>
                            <div style="color:#5E6673;align-self:center;">→</div>
                            <div>
                                <span class="sell-tag">{last_row['sell_exchange']}</span>
                                <div class="opp-price" style="margin-top:4px;">${last_row['sell_price']:.4f}</div>
                            </div>
                        </div>
                        <div style="font-size:0.7rem;color:#5E6673;font-family:'IBM Plex Mono',monospace;">
                            Spread {last_row['spread_pct']:.3f}% &nbsp;·&nbsp;
                            Fees {last_row['fees_pct']:.3f}% &nbsp;·&nbsp;
                            Volume ${last_row['volume']:,.0f}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align:center;padding:40px 20px;background:#13161C;
                            border:1px solid #1E2329;border-radius:8px;">
                    <div style="font-size:1.4rem;margin-bottom:10px;">⚡</div>
                    <div style="font-size:0.82rem;color:#848E9C;margin-bottom:6px;font-weight:600;">
                        Awaiting first scan result
                    </div>
                    <div style="font-size:0.72rem;color:#5E6673;">
                        Results will appear here automatically
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Auto refresh
    if auto_refresh:
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;
                    color:#2D3140;text-align:center;margin-top:14px;">
            AUTO-REFRESH · 60s
        </div>
        """, unsafe_allow_html=True)
        time.sleep(60)
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — OPPORTUNITIES
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)

    if not recent_df.empty:
        fc1, fc2, fc3 = st.columns([1, 1, 2])
        with fc1:
            min_profit = st.number_input("Min Profit %", 0.0, 5.0, 0.0, 0.001, format="%.3f")
        with fc2:
            symbol_filter = st.selectbox("Symbol", ["All"] + sorted(recent_df['symbol'].unique().tolist()))

        filtered = recent_df.copy()
        if min_profit > 0:
            filtered = filtered[filtered['net_profit_pct'] >= min_profit]
        if symbol_filter != "All":
            filtered = filtered[filtered['symbol'] == symbol_filter]
        filtered = filtered.sort_values('net_profit_pct', ascending=False)

        st.markdown(f"""
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">Arbitrage Opportunities — Last 24 Hours</span>
                <span style="font-size:0.65rem;color:#0ECB81;font-family:'IBM Plex Mono',monospace;">
                    {len(filtered)} RESULTS
                </span>
            </div>
            <div class="opp-table-header">
                <div>PAIR</div><div>BUY AT</div><div>SELL AT</div>
                <div>SPREAD</div><div>NET PROFIT</div><div>TIME</div>
            </div>
        """, unsafe_allow_html=True)

        for _, row in filtered.head(50).iterrows():
            profit = row['net_profit_pct']
            if profit >= 0.5:   pill = f'<span class="profit-pill-high">+{profit:.3f}%</span>'
            elif profit >= 0.1: pill = f'<span class="profit-pill-mid">+{profit:.3f}%</span>'
            else:               pill = f'<span class="profit-pill-low">+{profit:.3f}%</span>'

            st.markdown(f"""
            <div class="opp-row">
                <div class="opp-symbol">{row['symbol']}</div>
                <div><span class="buy-tag">{row['buy_exchange']}</span>
                     <br/><span class="opp-price">${row['buy_price']:.4f}</span></div>
                <div><span class="sell-tag">{row['sell_exchange']}</span>
                     <br/><span class="opp-price">${row['sell_price']:.4f}</span></div>
                <div class="opp-price">{row['spread_pct']:.3f}%
                     <br/><span style="color:#5E6673;font-size:0.65rem;">fees {row['fees_pct']:.3f}%</span></div>
                <div>{pill}
                     <br/><span style="color:#5E6673;font-size:0.65rem;font-family:'IBM Plex Mono',monospace;">
                     ${row['profit_per_btc']:.4f}/coin</span></div>
                <div class="opp-price" style="font-size:0.68rem;">{row['ts'].strftime('%H:%M:%S')}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Telegram CTA inside opportunities tab
        st.markdown(f"""
        <div style="background:#0D1F3C;border:1px solid #2A4A7F;border-radius:8px;
                    padding:14px 18px;margin-top:12px;display:flex;align-items:center;
                    justify-content:space-between;gap:12px;">
            <div style="font-size:0.8rem;color:#94B4E0;">
                <strong style="color:#EAECEF;">Want instant alerts?</strong>
                Join the ArbitrageIQ Telegram channel and get notified the moment
                an opportunity is detected.
            </div>
            <a href="{TELEGRAM_CHANNEL}" target="_blank"
               style="background:#229ED9;color:#fff;border-radius:6px;padding:9px 18px;
                      font-size:0.78rem;font-weight:700;text-decoration:none;white-space:nowrap;">
                Join Now
            </a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:2rem;margin-bottom:12px;">⚡</div>
            <div style="font-size:0.9rem;font-weight:600;color:#848E9C;margin-bottom:6px;">
                No opportunities in last 24 hours
            </div>
            <div style="font-size:0.75rem;color:#5E6673;font-family:'IBM Plex Mono',monospace;">
                Keep scanner.py running · python scanner.py --interval 10 --threshold 0.15
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — ANALYTICS
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)

    if not history_df.empty and len(history_df) >= 2:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Opportunities", len(history_df))
        m2.metric("Avg Net Profit",      f"{avg_profit:.3f}%")
        m3.metric("Best Profit",         f"{best_profit:.3f}%")
        m4.metric("Last 24h",            len(recent_df))

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # Profit over time
        st.markdown('<div class="panel"><div class="panel-header"><span class="panel-title">Net Profit Over Time</span></div>', unsafe_allow_html=True)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=history_df['ts'], y=history_df['net_profit_pct'],
            mode='markers+lines',
            marker=dict(color='#F0B90B', size=5, opacity=0.8),
            line=dict(color='#F0B90B', width=1, dash='dot'),
        ))
        fig1.add_hline(y=avg_profit, line_dash="dash", line_color="#5E6673",
                       annotation_text="avg", annotation_font_color="#5E6673")
        fig1.update_layout(template='plotly_dark', height=260,
                            plot_bgcolor='#13161C', paper_bgcolor='#13161C',
                            margin=dict(l=40,r=20,t=16,b=40), showlegend=False,
                            xaxis=dict(tickfont=dict(color='#5E6673',size=9)),
                            yaxis=dict(tickfont=dict(color='#5E6673',size=9),title="Net Profit %"))
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="panel"><div class="panel-header"><span class="panel-title">Top Symbols</span></div>', unsafe_allow_html=True)
            sym_counts = history_df['symbol'].value_counts().head(10)
            fig2 = go.Figure(go.Bar(
                x=sym_counts.values, y=sym_counts.index, orientation='h',
                marker=dict(color='#F0B90B', opacity=0.8),
                text=sym_counts.values, textposition='auto',
                textfont=dict(color='#0B0E11', size=9)
            ))
            fig2.update_layout(template='plotly_dark', height=260,
                                plot_bgcolor='#13161C', paper_bgcolor='#13161C',
                                margin=dict(l=10,r=20,t=10,b=20), showlegend=False,
                                xaxis=dict(tickfont=dict(color='#5E6673',size=9)),
                                yaxis=dict(tickfont=dict(color='#EAECEF',size=9)))
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="panel"><div class="panel-header"><span class="panel-title">Best Buy Exchanges</span></div>', unsafe_allow_html=True)
            buy_counts = history_df['buy_exchange'].value_counts()
            fig3 = go.Figure(go.Pie(
                labels=buy_counts.index, values=buy_counts.values, hole=0.6,
                marker=dict(colors=['#F0B90B','#0ECB81','#3B82F6','#F6465D','#8B5CF6']),
                textfont=dict(size=10, color='#EAECEF'), textinfo='label+percent'
            ))
            fig3.update_layout(template='plotly_dark', height=260,
                                plot_bgcolor='#13161C', paper_bgcolor='#13161C',
                                margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><div class="panel-header"><span class="panel-title">Profit Distribution</span></div>', unsafe_allow_html=True)
        fig4 = go.Figure(go.Histogram(
            x=history_df['net_profit_pct'], nbinsx=30,
            marker=dict(color='#0ECB81', opacity=0.7, line=dict(color='#13161C', width=1))
        ))
        fig4.update_layout(template='plotly_dark', height=200,
                            plot_bgcolor='#13161C', paper_bgcolor='#13161C',
                            margin=dict(l=40,r=20,t=10,b=40), showlegend=False,
                            xaxis=dict(title="Net Profit %", tickfont=dict(color='#5E6673',size=9)),
                            yaxis=dict(title="Count", tickfont=dict(color='#5E6673',size=9)))
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;">
            <div style="font-size:0.9rem;color:#848E9C;margin-bottom:8px;font-weight:600;">
                Not enough data for analytics yet
            </div>
            <div style="font-size:0.75rem;color:#5E6673;font-family:'IBM Plex Mono',monospace;">
                Keep scanner.py running to build history
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — HISTORY
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)

    if not history_df.empty:
        h1, h2, h3, h4 = st.columns(4)
        h1.metric("Total Records",  len(history_df))
        h2.metric("Avg Profit",     f"{avg_profit:.3f}%")
        h3.metric("Best",           f"{best_profit:.3f}%")
        h4.metric("Total Profit $", f"${history_df['profit_per_btc'].sum():.4f}")

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        disp = history_df[['timestamp','symbol','buy_exchange','sell_exchange',
                            'net_profit_pct','profit_per_btc','volume']].copy()
        disp['timestamp'] = pd.to_datetime(disp['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        disp = disp.sort_values('timestamp', ascending=False)

        st.dataframe(disp, column_config={
            "timestamp":      "Time",
            "symbol":         "Pair",
            "buy_exchange":   "Buy",
            "sell_exchange":  "Sell",
            "net_profit_pct": st.column_config.NumberColumn("Profit %", format="%.3f%%"),
            "profit_per_btc": st.column_config.NumberColumn("Profit $", format="$%.4f"),
            "volume":         st.column_config.NumberColumn("Volume",   format="$%.0f"),
        }, use_container_width=True, hide_index=True)

        csv = db.export_to_csv()
        if csv:
            ca, cb, _ = st.columns([1, 1, 3])
            with ca:
                st.download_button("Export CSV", csv,
                    f"arbitrage_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv", use_container_width=True)
            with cb:
                if st.button("Clear History", use_container_width=True):
                    if db.clear_data():
                        st.success("History cleared.")
                        st.rerun()
    else:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:0.9rem;color:#848E9C;margin-bottom:6px;">No historical data yet</div>
            <div style="font-size:0.75rem;color:#5E6673;">Run scanner.py to start building history</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="terminal-footer">
    <div class="footer-left">
        ArbitrageIQ v2.0 &nbsp;·&nbsp; 5 Exchanges &nbsp;·&nbsp; 30 Symbols &nbsp;·&nbsp;
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
    </div>
    <div class="footer-right">
        Built by <a href="https://yemifatodu.online">Yemi Fatodu</a>
        &nbsp;·&nbsp; Data Scientist &amp; Full-Stack Product Builder
        &nbsp;·&nbsp; <a href="https://linkedin.com/in/yemifatodu">LinkedIn</a>
        &nbsp;·&nbsp; <a href="{TELEGRAM_CHANNEL}">Telegram</a>
    </div>
</div>
""", unsafe_allow_html=True)
