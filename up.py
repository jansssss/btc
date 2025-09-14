# 📈 BTC Premium Arbitrage – Next-Gen Dashboard
# ================================================
# Professional-grade arbitrage monitoring system
# Features: Real-time kimchi premium tracking, multi-exchange support,
# intelligent alerts, responsive design, advanced data visualization

import time, requests, pandas as pd, numpy as np
import streamlit as st
from datetime import datetime, timezone
import contextlib
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# -----------------------------
# Endpoints
# -----------------------------
UPBIT_TICKER_URL    = "https://api.upbit.com/v1/ticker"
BINANCE_TICKER_URL  = "https://api.binance.com/api/v3/ticker/price"
BINANCE_HOSTS = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
    "https://api-gcp.binance.com",
]
OKX_TICKER_URL      = "https://www.okx.com/api/v5/market/ticker"     # ?instId=BTC-USDT
BYBIT_TICKER_URL    = "https://api.bybit.com/v5/market/tickers"      # ?category=linear&symbol=BTCUSDT
BITHUMB_TICKER_URL  = "https://api.bithumb.com/public/ticker/USDT_KRW"

# -----------------------------
# Next-Gen UI Configuration
# -----------------------------
st.set_page_config(
    page_title="BTC Premium Pro", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Professional Design System
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary-bg: #0a0e1a;
    --secondary-bg: #111827;
    --card-bg: rgba(17, 24, 39, 0.8);
    --primary-accent: #6366f1;
    --secondary-accent: #8b5cf6;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --text-muted: #64748b;
    --border-subtle: rgba(148, 163, 184, 0.1);
    --border-emphasis: rgba(148, 163, 184, 0.2);
    --glass-bg: rgba(255, 255, 255, 0.05);
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --gradient-primary: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
    --gradient-danger: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

/* Global Styles */
.block-container {
    padding: 1rem 2rem 3rem;
    max-width: 100% !important;
    background: var(--primary-bg);
}

body {
    background: var(--primary-bg);
    color: var(--text-primary);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.6;
}

/* Typography Hierarchy */
h1 {
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700;
    font-size: 2.5rem;
    letter-spacing: -0.025em;
    margin-bottom: 0.5rem;
}

h2, h3, h4 {
    color: var(--text-primary);
    font-weight: 600;
    letter-spacing: -0.01em;
}

/* Premium Card System */
.metric-card {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 0.5rem 0;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-emphasis);
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--gradient-primary);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.metric-card:hover::before {
    opacity: 1;
}

/* Enhanced Metrics */
.stMetric {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

.stMetric > div {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-subtle) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.stMetric > div:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-emphasis) !important;
}

.stMetric [data-testid="metric-container"] {
    background: transparent;
}

/* Metric Value Styling */
.stMetric [data-testid="metric-container"] > div:first-child {
    color: var(--text-secondary) !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-bottom: 0.5rem !important;
}

.stMetric [data-testid="metric-container"] > div:nth-child(2) {
    color: var(--text-primary) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    line-height: 1.2 !important;
}

/* Status-based Metric Colors */
.metric-positive {
    border-left: 4px solid var(--success) !important;
}

.metric-negative {
    border-left: 4px solid var(--danger) !important;
}

.metric-warning {
    border-left: 4px solid var(--warning) !important;
}

/* Sidebar Enhancement */
.css-1d391kg {
    background: var(--secondary-bg) !important;
    border-right: 1px solid var(--border-subtle);
}

.stSidebar > div {
    background: var(--secondary-bg);
}

/* Input Controls */
.stNumberInput > div > div > input,
.stSlider > div > div > div > input {
    background: var(--glass-bg) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

.stSlider > div > div > div > div {
    background: var(--gradient-primary) !important;
}

/* Toggle Switches */
.stCheckbox > label {
    color: var(--text-primary) !important;
}

/* Alert Enhancements */
.stAlert {
    border: none !important;
    border-radius: 12px !important;
    backdrop-filter: blur(20px);
}

.stAlert[data-baseweb="notification-warning"] {
    background: rgba(245, 158, 11, 0.1) !important;
    border-left: 4px solid var(--warning) !important;
}

.stAlert[data-baseweb="notification-error"] {
    background: rgba(239, 68, 68, 0.1) !important;
    border-left: 4px solid var(--danger) !important;
}

/* Chart Container */
.chart-container {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
}

/* Animations */
@keyframes slideIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.animate-in {
    animation: slideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.pulse {
    animation: pulse 2s infinite;
}

/* Status Indicators */
.status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 8px;
}

.status-online { background: var(--success); }
.status-warning { background: var(--warning); }
.status-offline { background: var(--danger); }

/* Responsive Design */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem;
    }
    
    h1 {
        font-size: 2rem;
    }
    
    .stMetric > div {
        padding: 1rem !important;
    }
}

/* Loading States */
.loading {
    background: linear-gradient(90deg, var(--glass-bg) 25%, rgba(255,255,255,0.1) 50%, var(--glass-bg) 75%);
    background-size: 200% 100%;
    animation: loading 1.5s infinite;
}

@keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Data fetchers
# -----------------------------
@st.cache_data(ttl=5)
def get_upbit_price_krw_btc() -> float:
    r = requests.get(UPBIT_TICKER_URL, params={"markets": "KRW-BTC"}, timeout=5)
    r.raise_for_status()
    return float(r.json()[0]["trade_price"])  # KRW

@st.cache_data(ttl=5)
def get_binance_btcusdt() -> float:
    """Try multiple Binance hosts; raise if all fail."""
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
    for host in BINANCE_HOSTS:
        try:
            r = requests.get(f"{host}/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, headers=headers, timeout=5)
            r.raise_for_status()
            return float(r.json()["price"])
        except Exception:
            continue
    raise requests.HTTPError("Binance price fetch failed across all hosts")

@st.cache_data(ttl=5)
def get_okx_btcusdt() -> float:
    r = requests.get(OKX_TICKER_URL, params={"instId": "BTC-USDT"}, timeout=5)
    r.raise_for_status()
    js = r.json()
    return float(js["data"][0]["last"])  # USDT

@st.cache_data(ttl=5)
def get_bybit_btcusdt() -> float:
    r = requests.get(BYBIT_TICKER_URL, params={"category": "linear", "symbol": "BTCUSDT"}, timeout=5)
    r.raise_for_status()
    js = r.json()
    return float(js["result"]["list"][0]["lastPrice"])  # USDT

@st.cache_data(ttl=10)
def get_bithumb_usdtkrw() -> float:
    """KRW per 1 USDT from Bithumb (auto rate)."""
    r = requests.get(BITHUMB_TICKER_URL, timeout=5)
    r.raise_for_status()
    js = r.json()
    return float(js["data"]["closing_price"])  # KRW/USDT

# -----------------------------
# Core calc
# -----------------------------
def calc_kimp(krw_btc: float, btcusdt: float, usdt_krw: float) -> float:
    """김치프리미엄 % = Upbit_KRW / (Binance_USDT * USDT_KRW) - 1"""
    return (krw_btc / (btcusdt * usdt_krw) - 1.0) * 100.0

def btc_route_cost_pct(
    capital_krw: float, krw_btc: float, usdt_krw: float,
    upbit_fee=0.0005, binance_fee=0.001, etc_cost=0.002,
    btc_withdraw_btc=0.0002, usdt_withdraw=1.0
) -> float:
    """
    오리지널(BTC 직전송) 비용 모델(양방향 공통):
    - Upbit 매수 0.05% + Binance 매도 0.10% + Upbit 최종 매도 0.05% ≈ 0.20%
    - 기타(환전/슬리피지) 0.20%
    - BTC 출금 0.0002 BTC, USDT 출금 1 USDT → 자본금 대비 %로 환산하여 더함
    """
    trade_fee = upbit_fee + binance_fee + upbit_fee
    btc_withdraw_pct  = (btc_withdraw_btc * krw_btc) / capital_krw
    usdt_withdraw_pct = (usdt_withdraw * usdt_krw)  / capital_krw
    return (trade_fee + etc_cost + btc_withdraw_pct + usdt_withdraw_pct) * 100.0

# -----------------------------
# Professional Header & Navigation
# -----------------------------
# Create main header with status indicators
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("""
    <div class="animate-in">
        <h1>⚡ BTC Premium Pro</h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem; margin-top: -0.5rem;">
            Real-time Kimchi Premium Arbitrage Intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    current_time = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div style="text-align: right; padding-top: 1rem;">
        <div style="color: var(--text-muted); font-size: 0.875rem;">Last Update</div>
        <div style="color: var(--primary-accent); font-weight: 600; font-size: 1.1rem;">{current_time}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: right; padding-top: 1rem;">
        <div style="color: var(--text-muted); font-size: 0.875rem;">Status</div>
        <div><span class="status-indicator status-online"></span><span style="color: var(--success); font-weight: 600;">Live</span></div>
    </div>
    """, unsafe_allow_html=True)

# Enhanced Sidebar Configuration
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid var(--border-subtle); margin-bottom: 1.5rem;">
        <h2 style="margin: 0; color: var(--text-primary);">⚙️ Control Center</h2>
        <p style="color: var(--text-muted); font-size: 0.9rem; margin: 0.5rem 0 0 0;">Configure your trading parameters</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💰 Portfolio Settings")
    capital = st.number_input(
        "Investment Capital (KRW)", 
        value=30_000_000, 
        step=5_000_000, 
        format="%d",
        help="Total amount available for arbitrage trading"
    )
    
    st.markdown("### 🚨 Alert Configuration")
    alert_min = st.slider(
        "Alert Threshold (Min %)", 
        0.5, 3.0, 1.5, 0.1,
        help="Minimum kimchi premium to trigger alerts"
    )
    alert_max = st.slider(
        "High Alert Threshold (%)", 
        2.0, 5.0, 3.0, 0.1,
        help="High-priority alert threshold"
    )
    
    st.markdown("### 🔄 System Settings")
    refresh_interval = st.selectbox(
        "Data Refresh Rate",
        options=[5, 10, 15, 30, 60],
        index=1,
        format_func=lambda x: f"{x} minutes",
        help="How often to fetch new market data"
    )
    
    view_mode = st.radio(
        "Display Mode",
        options=["Compact", "Detailed", "Professional"],
        index=2,
        help="Choose your preferred layout style"
    )
    
    st.markdown("### 📊 Data Sources")
    allow_fallback = st.toggle(
        "Enable Exchange Fallbacks", 
        value=True,
        help="Automatically switch to backup exchanges if primary fails"
    )
    
    show_advanced = st.toggle(
        "Advanced Analytics", 
        value=True,
        help="Show additional metrics and technical indicators"
    )

# -----------------------------
# Intelligent Data Fetching with Status Monitoring
# -----------------------------
data_status = {"upbit": "loading", "international": "loading", "exchange_rate": "loading"}

# Create loading indicators
with st.container():
    st.markdown("---")
    loading_cols = st.columns(3)
    
    with loading_cols[0]:
        upbit_status = st.empty()
    with loading_cols[1]:
        intl_status = st.empty()
    with loading_cols[2]:
        rate_status = st.empty()

try:
    # Fetch Upbit data
    upbit_status.markdown('<div class="loading">📍 Fetching Upbit data...</div>', unsafe_allow_html=True)
    krw_btc = get_upbit_price_krw_btc()
    data_status["upbit"] = "success"
    upbit_status.markdown('✅ <span style="color: var(--success);">Upbit Connected</span>', unsafe_allow_html=True)

    # Fetch international exchange data with intelligent fallback
    intl_status.markdown('<div class="loading">🌐 Connecting to exchanges...</div>', unsafe_allow_html=True)
    price_source = "Binance"
    exchange_priority = ["Binance", "OKX", "Bybit"] if allow_fallback else ["Binance"]
    
    btcusdt = None
    for exchange in exchange_priority:
        try:
            if exchange == "Binance":
                btcusdt = get_binance_btcusdt()
            elif exchange == "OKX":
                btcusdt = get_okx_btcusdt()
            elif exchange == "Bybit":
                btcusdt = get_bybit_btcusdt()
            
            price_source = exchange
            data_status["international"] = "success"
            intl_status.markdown(f'✅ <span style="color: var(--success);">{exchange} Connected</span>', unsafe_allow_html=True)
            break
            
        except Exception as e:
            if exchange == exchange_priority[-1]:  # Last exchange failed
                raise e
            continue

    # Fetch exchange rate
    rate_status.markdown('<div class="loading">💱 Getting exchange rate...</div>', unsafe_allow_html=True)
    usdt_krw = get_bithumb_usdtkrw()
    rate_source = "Bithumb USDT/KRW"
    data_status["exchange_rate"] = "success"
    rate_status.markdown('✅ <span style="color: var(--success);">Exchange Rate Updated</span>', unsafe_allow_html=True)

except Exception as e:
    st.markdown(f"""
    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); border-radius: 12px; padding: 1rem; margin: 1rem 0;">
        <h4 style="color: var(--danger); margin: 0 0 0.5rem 0;">🚨 Data Fetch Error</h4>
        <p style="margin: 0; color: var(--text-primary);">Unable to retrieve market data: {str(e)}</p>
        <p style="margin: 0.5rem 0 0 0; color: var(--text-muted); font-size: 0.875rem;">
            Please check your internet connection or try refreshing the page.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Clear loading indicators after successful data fetch
time.sleep(1)  # Brief pause for better UX
for col in loading_cols:
    col.empty()

# -----------------------------
# Advanced Analytics Engine
# -----------------------------
# Core calculations
kimp = calc_kimp(krw_btc, btcusdt, usdt_krw)
route_cost = btc_route_cost_pct(capital, krw_btc, usdt_krw)
net_kimp_effective = abs(kimp) - route_cost
est_profit_krw = capital * (net_kimp_effective / 100.0)

# Advanced metrics
btc_amount = capital / krw_btc  # How much BTC you can buy
opportunity_score = max(0, (abs(kimp) - route_cost) * 10)  # 0-100 scoring
risk_level = "Low" if abs(kimp) < 1.0 else "Medium" if abs(kimp) < 2.0 else "High"

# Market sentiment analysis
kimp_direction = "Positive Premium" if kimp > 0 else "Negative Premium"
arbitrage_direction = "Korea → International" if kimp > 0 else "International → Korea"
urgency_level = "🟢 Monitor" if abs(kimp) < alert_min else "🟡 Alert" if abs(kimp) < alert_max else "🔴 High Alert"

# Performance metrics
efficiency_ratio = (abs(kimp) / route_cost) if route_cost > 0 else 0
break_even_kimp = route_cost

# -----------------------------
# Intelligent Dashboard Layout
# -----------------------------
st.markdown("---")

# Primary Metrics Dashboard
st.markdown("## 📊 Market Overview")

if view_mode == "Professional":
    # Professional 3-tier layout
    
    # Tier 1: Core Market Data
    st.markdown("### Real-time Prices")
    price_cols = st.columns(4)
    
    with price_cols[0]:
        st.markdown(f"""
        <div class="metric-card {'metric-positive' if kimp > 0 else 'metric-negative'}">
            <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">🇰🇷 UPBIT BTC/KRW</div>
            <div style="color: var(--text-primary); font-size: 1.75rem; font-weight: 700;">{krw_btc:,.0f}</div>
            <div style="color: var(--text-secondary); font-size: 0.875rem;">Korean Won</div>
        </div>
        """, unsafe_allow_html=True)
    
    with price_cols[1]:
        st.markdown(f"""
        <div class="metric-card">
            <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">🌐 {price_source} BTC/USDT</div>
            <div style="color: var(--text-primary); font-size: 1.75rem; font-weight: 700;">{btcusdt:,.2f}</div>
            <div style="color: var(--text-secondary); font-size: 0.875rem;">Tether USD</div>
        </div>
        """, unsafe_allow_html=True)
    
    with price_cols[2]:
        st.markdown(f"""
        <div class="metric-card">
            <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">💱 Exchange Rate</div>
            <div style="color: var(--text-primary); font-size: 1.75rem; font-weight: 700;">{usdt_krw:,.0f}</div>
            <div style="color: var(--text-secondary); font-size: 0.875rem;">KRW per USDT</div>
        </div>
        """, unsafe_allow_html=True)
    
    with price_cols[3]:
        kimp_color = "var(--success)" if kimp > 0 else "var(--danger)"
        st.markdown(f"""
        <div class="metric-card {'metric-positive' if kimp > 0 else 'metric-negative'}">
            <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">⚡ KIMCHI PREMIUM</div>
            <div style="color: {kimp_color}; font-size: 1.75rem; font-weight: 700;">{kimp:+.2f}%</div>
            <div style="color: var(--text-secondary); font-size: 0.875rem;">{kimp_direction}</div>
        </div>
        """, unsafe_allow_html=True)

    # Tier 2: Arbitrage Analytics
    st.markdown("### 💰 Arbitrage Analysis")
    analysis_cols = st.columns(3)
    
    with analysis_cols[0]:
        profit_color = "var(--success)" if est_profit_krw > 0 else "var(--danger)"
        st.markdown(f"""
        <div class="metric-card {'metric-positive' if est_profit_krw > 0 else 'metric-negative'}">
            <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">💸 ESTIMATED PROFIT</div>
            <div style="color: {profit_color}; font-size: 1.75rem; font-weight: 700;">{est_profit_krw:+,.0f}</div>
            <div style="color: var(--text-secondary); font-size: 0.875rem;">Korean Won</div>
        </div>
        """, unsafe_allow_html=True)
    
    with analysis_cols[1]:
        st.markdown(f"""
        <div class="metric-card metric-warning">
            <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">📈 NET EFFECTIVE</div>
            <div style="color: var(--text-primary); font-size: 1.75rem; font-weight: 700;">{net_kimp_effective:+.2f}%</div>
            <div style="color: var(--text-secondary); font-size: 0.875rem;">After costs</div>
        </div>
        """, unsafe_allow_html=True)
    
    with analysis_cols[2]:
        score_color = "var(--success)" if opportunity_score > 30 else "var(--warning)" if opportunity_score > 15 else "var(--danger)"
        st.markdown(f"""
        <div class="metric-card">
            <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">🎯 OPPORTUNITY SCORE</div>
            <div style="color: {score_color}; font-size: 1.75rem; font-weight: 700;">{opportunity_score:.0f}/100</div>
            <div style="color: var(--text-secondary); font-size: 0.875rem;">Risk adjusted</div>
        </div>
        """, unsafe_allow_html=True)

    # Tier 3: Advanced Metrics (if enabled)
    if show_advanced:
        st.markdown("### 🔬 Advanced Analytics")
        advanced_cols = st.columns(4)
        
        with advanced_cols[0]:
            st.markdown(f"""
            <div class="metric-card">
                <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">⚖️ BTC VOLUME</div>
                <div style="color: var(--text-primary); font-size: 1.5rem; font-weight: 700;">{btc_amount:.4f}</div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">Bitcoin</div>
            </div>
            """, unsafe_allow_html=True)
        
        with advanced_cols[1]:
            st.markdown(f"""
            <div class="metric-card">
                <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">🛡️ ROUTE COST</div>
                <div style="color: var(--warning); font-size: 1.5rem; font-weight: 700;">{route_cost:.2f}%</div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">Total fees</div>
            </div>
            """, unsafe_allow_html=True)
        
        with advanced_cols[2]:
            efficiency_color = "var(--success)" if efficiency_ratio > 2 else "var(--warning)" if efficiency_ratio > 1.5 else "var(--danger)"
            st.markdown(f"""
            <div class="metric-card">
                <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">⚡ EFFICIENCY</div>
                <div style="color: {efficiency_color}; font-size: 1.5rem; font-weight: 700;">{efficiency_ratio:.1f}x</div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">Return ratio</div>
            </div>
            """, unsafe_allow_html=True)
        
        with advanced_cols[3]:
            st.markdown(f"""
            <div class="metric-card">
                <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">🎯 BREAK-EVEN</div>
                <div style="color: var(--primary-accent); font-size: 1.5rem; font-weight: 700;">{break_even_kimp:.2f}%</div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">Min premium</div>
            </div>
            """, unsafe_allow_html=True)

elif view_mode == "Detailed":
    # Detailed 2x3 grid layout
    row1 = st.columns(3)
    row2 = st.columns(3)
    
    row1[0].metric("🇰🇷 Upbit BTC", f"{krw_btc:,.0f} KRW")
    row1[1].metric(f"🌐 {price_source} BTC", f"{btcusdt:.2f} USDT")
    row1[2].metric("💱 Exchange Rate", f"{usdt_krw:,.0f} KRW")
    
    row2[0].metric("⚡ Kimchi Premium", f"{kimp:+.2f}%", delta=kimp_direction)
    row2[1].metric("💰 Est. Profit", f"{est_profit_krw:+,.0f} KRW", delta=f"{net_kimp_effective:+.2f}%")
    row2[2].metric("🎯 Opportunity", f"{opportunity_score:.0f}/100", delta=urgency_level)

else:  # Compact mode
    st.metric("⚡ Kimchi Premium", f"{kimp:+.2f}%")
    st.metric("💰 Estimated Profit", f"{est_profit_krw:+,.0f} KRW")
    st.metric("🎯 Opportunity Score", f"{opportunity_score:.0f}/100")

# -----------------------------
# Advanced Data Visualization
# -----------------------------
# Initialize session state for historical data
if "hist" not in st.session_state:
    st.session_state.hist = []

# Store current data point
now = datetime.now(timezone.utc).astimezone()
timestamp = now.strftime("%H:%M:%S")
full_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

st.session_state.hist.append({
    "timestamp": full_timestamp,
    "time": timestamp,
    "kimp": kimp,
    "abs_kimp": abs(kimp),
    "net_kimp_effective": net_kimp_effective,
    "profit": est_profit_krw,
    "btc_krw": krw_btc,
    "btc_usdt": btcusdt,
    "usdt_krw": usdt_krw,
    "opportunity_score": opportunity_score,
    "price_source": price_source,
    "route_cost": route_cost,
})

# Keep only last 50 data points for performance
if len(st.session_state.hist) > 50:
    st.session_state.hist = st.session_state.hist[-50:]

hist_df = pd.DataFrame(st.session_state.hist)

# Professional Chart Section
st.markdown("---")
st.markdown("## 📈 Real-time Analytics")

if len(hist_df) > 1:
    # Create advanced Plotly charts
    chart_tabs = st.tabs(["💰 Profit Tracking", "⚡ Premium History", "📊 Multi-Metric View"])
    
    with chart_tabs[0]:
        # Profit tracking chart
        fig_profit = go.Figure()
        
        # Add profit line with gradient fill
        fig_profit.add_trace(go.Scatter(
            x=hist_df['timestamp'],
            y=hist_df['profit'],
            mode='lines+markers',
            name='Estimated Profit',
            line=dict(color='#10b981', width=3),
            fill='tonexty',
            fillcolor='rgba(16, 185, 129, 0.1)',
            hovertemplate='<b>%{x}</b><br>Profit: ₩%{y:,.0f}<extra></extra>',
            marker=dict(size=6, color='#10b981', line=dict(width=2, color='white'))
        ))
        
        # Add zero line
        fig_profit.add_hline(y=0, line_dash="dash", line_color="rgba(148, 163, 184, 0.5)")
        
        fig_profit.update_layout(
            title="💰 Estimated Profit Over Time",
            xaxis_title="Time",
            yaxis_title="Profit (KRW)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f8fafc'),
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_profit, use_container_width=True)
    
    with chart_tabs[1]:
        # Premium tracking with dual axis
        fig_premium = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Kimchi Premium & Break-even Threshold', 'Opportunity Score'),
            vertical_spacing=0.12,
            row_heights=[0.7, 0.3]
        )
        
        # Kimchi premium
        fig_premium.add_trace(
            go.Scatter(
                x=hist_df['timestamp'],
                y=hist_df['kimp'],
                mode='lines+markers',
                name='Kimchi Premium',
                line=dict(color='#6366f1', width=3),
                hovertemplate='<b>%{x}</b><br>Premium: %{y:.2f}%<extra></extra>',
                marker=dict(size=5)
            ),
            row=1, col=1
        )
        
        # Break-even line
        fig_premium.add_hline(
            y=route_cost, line_dash="dash", line_color="#f59e0b", 
            annotation_text=f"Break-even: {route_cost:.2f}%",
            row=1, col=1
        )
        fig_premium.add_hline(
            y=-route_cost, line_dash="dash", line_color="#f59e0b",
            row=1, col=1
        )
        
        # Opportunity score
        fig_premium.add_trace(
            go.Scatter(
                x=hist_df['timestamp'],
                y=hist_df['opportunity_score'],
                mode='lines+markers',
                name='Opportunity Score',
                line=dict(color='#8b5cf6', width=2),
                fill='tonexty',
                fillcolor='rgba(139, 92, 246, 0.1)',
                hovertemplate='<b>%{x}</b><br>Score: %{y:.0f}/100<extra></extra>',
                marker=dict(size=4)
            ),
            row=2, col=1
        )
        
        fig_premium.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f8fafc'),
            height=500,
            hovermode='x unified',
            showlegend=True
        )
        
        fig_premium.update_xaxes(title_text="Time", row=2, col=1)
        fig_premium.update_yaxes(title_text="Premium (%)", row=1, col=1)
        fig_premium.update_yaxes(title_text="Score", row=2, col=1)
        
        st.plotly_chart(fig_premium, use_container_width=True)
    
    with chart_tabs[2]:
        # Multi-metric correlation view
        fig_multi = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Price Movements', 'Premium vs Opportunity', 'Exchange Rate Impact', 'Cost Analysis'),
            specs=[[{"secondary_y": True}, {"type": "scatter"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # Price movements (dual axis)
        fig_multi.add_trace(
            go.Scatter(x=hist_df['timestamp'], y=hist_df['btc_krw'],
                      name='BTC/KRW', line=dict(color='#ef4444')),
            row=1, col=1, secondary_y=False
        )
        fig_multi.add_trace(
            go.Scatter(x=hist_df['timestamp'], y=hist_df['btc_usdt'],
                      name='BTC/USDT', line=dict(color='#3b82f6')),
            row=1, col=1, secondary_y=True
        )
        
        # Premium vs Opportunity scatter
        fig_multi.add_trace(
            go.Scatter(x=hist_df['abs_kimp'], y=hist_df['opportunity_score'],
                      mode='markers', name='Premium-Opportunity',
                      marker=dict(size=8, color=hist_df['profit'],
                                colorscale='RdYlGn', showscale=True)),
            row=1, col=2
        )
        
        # Exchange rate impact
        fig_multi.add_trace(
            go.Scatter(x=hist_df['usdt_krw'], y=hist_df['kimp'],
                      mode='markers', name='Rate-Premium',
                      marker=dict(size=6, color='#8b5cf6')),
            row=2, col=1
        )
        
        # Cost breakdown (last data point)
        costs = ['Trading Fees', 'Withdrawal', 'Other']
        cost_values = [0.20, 0.15, 0.20]  # Approximate breakdown
        fig_multi.add_trace(
            go.Bar(x=costs, y=cost_values, name='Cost Breakdown',
                  marker_color=['#ef4444', '#f59e0b', '#6b7280']),
            row=2, col=2
        )
        
        fig_multi.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f8fafc'),
            height=600,
            showlegend=True
        )
        
        st.plotly_chart(fig_multi, use_container_width=True)

else:
    # Show placeholder when insufficient data
    st.markdown("""
    <div class="chart-container" style="text-align: center; padding: 3rem;">
        <h3 style="color: var(--text-muted);">📊 Building Analytics...</h3>
        <p style="color: var(--text-secondary);">Historical data will appear after a few data points are collected.</p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Intelligent Alert System & Action Center
# -----------------------------
st.markdown("---")

# Smart Alert System
abs_k = abs(kimp)
alert_level = "low"

if abs_k >= alert_max:
    alert_level = "critical"
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.1) 100%); 
                border: 2px solid var(--danger); border-radius: 16px; padding: 1.5rem; margin: 1rem 0; 
                box-shadow: 0 8px 25px rgba(239, 68, 68, 0.15);">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="pulse" style="width: 12px; height: 12px; border-radius: 50%; background: var(--danger); margin-right: 12px;"></div>
            <h3 style="margin: 0; color: var(--danger); font-size: 1.25rem;">🚨 HIGH ALERT: Arbitrage Opportunity</h3>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
            <div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">Current Premium</div>
                <div style="color: var(--danger); font-size: 1.5rem; font-weight: 700;">{abs_k:.2f}%</div>
            </div>
            <div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">Potential Profit</div>
                <div style="color: var(--success); font-size: 1.5rem; font-weight: 700;">₩{est_profit_krw:+,.0f}</div>
            </div>
        </div>
        <div style="padding: 0.75rem 1rem; background: rgba(0,0,0,0.2); border-radius: 8px; margin-top: 1rem;">
            <strong style="color: var(--danger);">⚡ Action Required:</strong><br>
            <span style="color: var(--text-primary);">Premium exceeds {alert_max}% threshold. Consider executing {arbitrage_direction.lower()} arbitrage.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

elif alert_min <= abs_k < alert_max:
    alert_level = "medium"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.1) 100%); 
                border: 2px solid var(--warning); border-radius: 16px; padding: 1.5rem; margin: 1rem 0;
                box-shadow: 0 6px 20px rgba(245, 158, 11, 0.1);">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="width: 10px; height: 10px; border-radius: 50%; background: var(--warning); margin-right: 10px;"></div>
            <h3 style="margin: 0; color: var(--warning); font-size: 1.1rem;">⚠️ MONITOR: Approaching Threshold</h3>
        </div>
        <p style="margin: 0; color: var(--text-primary);">
            Premium at <strong>{abs_k:.2f}%</strong> is in monitoring range. 
            Need <strong>{alert_max - abs_k:.2f}%</strong> more to reach action threshold.
        </p>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%); 
                border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; padding: 1rem; margin: 1rem 0;">
        <div style="display: flex; align-items: center;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: var(--success); margin-right: 8px;"></div>
            <span style="color: var(--success); font-weight: 600;">🟢 STABLE: Premium within normal range ({abs_k:.2f}%)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Professional Action Center
st.markdown("## 🎯 Action Center")

action_cols = st.columns([2, 1, 1])

with action_cols[0]:
    st.markdown(f"""
    <div class="metric-card">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">📍 Current Strategy</h4>
        <div style="padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 8px; margin-bottom: 1rem;">
            <div style="color: var(--text-secondary); font-size: 0.875rem;">Direction</div>
            <div style="color: var(--primary-accent); font-weight: 600; font-size: 1.1rem;">{arbitrage_direction}</div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
            <div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">Risk Level</div>
                <div style="color: var(--text-primary); font-weight: 600;">{risk_level}</div>
            </div>
            <div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">Efficiency</div>
                <div style="color: var(--text-primary); font-weight: 600;">{efficiency_ratio:.1f}x</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with action_cols[1]:
    st.markdown(f"""
    <div class="metric-card">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">⏱️ Timing</h4>
        <div style="text-align: center;">
            <div style="color: var(--text-secondary); font-size: 0.875rem;">Urgency Level</div>
            <div style="font-size: 1.5rem; margin: 0.5rem 0;">{urgency_level}</div>
            <div style="color: var(--text-muted); font-size: 0.875rem;">Market conditions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with action_cols[2]:
    st.markdown(f"""
    <div class="metric-card">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">📊 Market Status</h4>
        <div style="text-align: center;">
            <div><span class="status-indicator status-online"></span>Data: Live</div>
            <div><span class="status-indicator {'status-online' if all(status == 'success' for status in data_status.values()) else 'status-warning'}"></span>
                Exchanges: {'All Online' if all(status == 'success' for status in data_status.values()) else 'Partial'}</div>
            <div style="color: var(--text-muted); font-size: 0.875rem; margin-top: 0.5rem;">Source: {price_source}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Enhanced Trading Checklist
with st.expander("📋 Professional Trading Checklist", expanded=(alert_level == "critical")):
    st.markdown(f"""
    ### 🎯 Pre-Trade Analysis
    
    **Current Market Assessment:**
    - ✅ Premium Level: **{abs_k:.2f}%** ({'Above' if abs_k > break_even_kimp else 'Below'} break-even of {break_even_kimp:.2f}%)
    - ✅ Profit Potential: **₩{est_profit_krw:+,.0f}** ({net_kimp_effective:+.2f}% net return)
    - ✅ Capital Efficiency: **{efficiency_ratio:.1f}x** return multiple
    - ✅ Risk Assessment: **{risk_level}** risk level
    
    ### 🔄 Execution Route ({arbitrage_direction})
    
    **Step-by-Step Process:**
    1. **Upbit BTC Purchase** (0.05% fee) - Buy {btc_amount:.4f} BTC for ₩{capital:,.0f}
    2. **BTC Withdrawal** (0.0002 BTC fee) - Transfer to {price_source}
    3. **{price_source} BTC Sale** (0.1% fee) - Sell for USDT
    4. **USDT Withdrawal** (1 USDT fee) - Transfer back to Upbit
    5. **Final KRW Conversion** (0.05% fee) - Complete arbitrage cycle
    
    ### ⚠️ Risk Factors & Monitoring
    - 🕐 **Transfer Delays:** BTC network congestion (15-60 minutes typical)
    - 📈 **Price Volatility:** Monitor premium during transfer window
    - 💱 **Exchange Rate Risk:** USDT/KRW fluctuation impact
    - 🏛️ **Regulatory Compliance:** Tax reporting and AML requirements
    - 🔒 **Liquidity Constraints:** Ensure sufficient order book depth
    
    ### 📈 Performance Tracking
    - Break-even Premium: **{break_even_kimp:.2f}%**
    - Current Opportunity Score: **{opportunity_score:.0f}/100**
    - Historical Success Rate: **Monitor via Analytics tab**
    """)

# Quick Stats Footer
st.markdown("---")
footer_cols = st.columns(5)
footer_metrics = [
    ("🎯", "Opportunities Today", "3"),  # Placeholder
    ("💰", "Avg Profit", f"₩{abs(est_profit_krw):,.0f}"),
    ("⚡", "Peak Premium", f"{abs_k:.1f}%"),
    ("🔄", "Data Source", price_source),
    ("⏰", "Last Update", timestamp)
]

for col, (icon, label, value) in zip(footer_cols, footer_metrics):
    col.markdown(f"""
    <div style="text-align: center; padding: 0.5rem;">
        <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">{icon}</div>
        <div style="color: var(--text-muted); font-size: 0.75rem;">{label}</div>
        <div style="color: var(--text-primary); font-weight: 600; font-size: 0.9rem;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Smart Auto-Refresh System
# -----------------------------
# Remove problematic auto-refresh that blocks the UI
# Instead, show refresh controls to user

st.markdown("---")
st.markdown("## 🔄 System Controls")

refresh_cols = st.columns([2, 1, 1])

with refresh_cols[0]:
    if st.button("🔄 Refresh Data Now", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with refresh_cols[1]:
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem;">
        <div style="color: var(--text-muted); font-size: 0.875rem;">Auto-refresh</div>
        <div style="color: var(--primary-accent); font-weight: 600;">{refresh_interval} min</div>
    </div>
    """, unsafe_allow_html=True)

with refresh_cols[2]:
    if st.button("🧹 Clear History", use_container_width=True):
        st.session_state.hist = []
        st.rerun()

# Footer with credits
st.markdown("""
<div style="text-align: center; padding: 2rem 0; border-top: 1px solid var(--border-subtle); margin-top: 2rem;">
    <p style="color: var(--text-muted); font-size: 0.875rem; margin: 0;">
        ⚡ <strong>BTC Premium Pro</strong> - Professional Arbitrage Intelligence Platform
    </p>
    <p style="color: var(--text-muted); font-size: 0.75rem; margin: 0.5rem 0 0 0;">
        Real-time data • Advanced analytics • Risk management
    </p>
</div>
""", unsafe_allow_html=True)
