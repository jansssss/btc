# 📈 BTC차액거래 – Streamlit Dashboard
# --------------------------------------
# - 환율: 빗썸 USDT/KRW 자동 반영
# - 순/역 김프 모두 고려(절대값 기준)
# - 예상 이익(원) 음수도 그대로 표기
# - 모바일 압축 모드 / PC 모드(2행 카드) 지원
# - 새로고침: 5~60분
# - Binance 451 대응: 다중 호스트 + OKX→Bybit 대체

import time, requests, pandas as pd
import streamlit as st
from datetime import datetime, timezone
import contextlib

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
# Page setup & theme
# -----------------------------
st.set_page_config(page_title="BTC solution", page_icon="📈", layout="centered")
st.markdown(
    """
    <style>
    .block-container {padding-top:1rem; padding-bottom:2rem; max-width:700px;}
    body {background-color:#0d1117; color:#f0f6fc; font-family:'Segoe UI',sans-serif;}
    h1,h2,h3,h4 {color:#58a6ff;}
    .stMetric {background:rgba(88,166,255,0.08); border-radius:14px; padding:0.6rem 0.8rem; border:1px solid rgba(88,166,255,0.12);}
    .stSlider > div {padding-top:0.5rem; padding-bottom:0.5rem;}
    @media (max-width:640px){.stMetric{text-align:left!important;}}
    </style>
    """,
    unsafe_allow_html=True,
)

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
# Sidebar
# -----------------------------
st.title("BTC solution")
with st.sidebar:
    st.header("설정")
    mobile_compact = st.toggle("모바일 압축 모드", value=True, help="끄면 PC 화면에 맞춰 넓게 보여줍니다.")
    capital     = st.number_input("자본금(원)", value=30_000_000, step=3_000_000, format="%d")
    alert_min   = st.number_input("알림 하한(|김프|, %)", value=1.5, step=0.1)
    alert_max   = st.number_input("알림 상한(|김프|, %)", value=2.0, step=0.1)
    refresh_min = st.slider("새로고침(분)", 5, 60, 10, help="5~60분 사이에서 선택")
    st.subheader("데이터 소스")
    allow_alt   = st.toggle("바이낸스 장애 시 대체 거래소 사용(OKX→Bybit)", value=True)

# -----------------------------
# Fetch data with fallbacks
# -----------------------------
try:
    krw_btc = get_upbit_price_krw_btc()

    price_source = "Binance"
    try:
        btcusdt = get_binance_btcusdt()
    except Exception:
        if allow_alt:
            try:
                btcusdt = get_okx_btcusdt()
                price_source = "OKX"
            except Exception:
                btcusdt = get_bybit_btcusdt()
                price_source = "Bybit"
        else:
            raise

    # 환율: 빗썸 USDT/KRW 자동
    usdt_krw = get_bithumb_usdtkrw()
    rate_source = "Bithumb USDT/KRW"

except Exception as e:
    st.error(f"시세/환율 조회 오류: {e}")
    st.stop()

# -----------------------------
# Compute
# -----------------------------
kimp = calc_kimp(krw_btc, btcusdt, usdt_krw)
route_cost = btc_route_cost_pct(capital, krw_btc, usdt_krw)
net_kimp_effective = abs(kimp) - route_cost            # <0 손실, >0 이익 가능
est_profit_krw     = capital * (net_kimp_effective / 100.0)

# -----------------------------
# UI – Metrics
# -----------------------------
if mobile_compact:
    st.metric("Upbit BTC/KRW", f"{krw_btc:,.0f}원")
    st.metric(f"{price_source} BTC/USDT", f"{btcusdt:,.2f} USDT")
    st.metric(f"{rate_source}", f"{usdt_krw:,.2f}원")
    st.metric("KIMP", f"{kimp:+.2f}%")
else:
    # Desktop wide & 2 rows
    st.markdown(
        """
        <style>
        .block-container {max-width:1200px;}
        .stMetric {padding:0.9rem 1rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    r1c1.metric("Upbit BTC/KRW", f"{krw_btc:,.0f}원")
    r1c2.metric(f"{price_source} BTC/USDT", f"{btcusdt:,.2f} USDT")
    r1c3.metric(f"{rate_source}", f"{usdt_krw:,.2f}원")
    r1c4.metric("KIMP", f"{kimp:+.2f}%")

    r2c1, r2c2, r2c3 = st.columns(3)
    r2c1.metric("총비용(%)", f"{route_cost:.2f}%")
    r2c2.metric("유효 김프(|김프|-비용)", f"{net_kimp_effective:+.2f}%")
    r2c3.metric("예상 이익(원)", f"{est_profit_krw:,.0f}", delta=f"{net_kimp_effective:+.2f}%")

# 모바일 압축 모드일 때 추가 지표
if mobile_compact:
    st.subheader("비용 및 이익 추정")
    st.metric("총비용(%)", f"{route_cost:.2f}%")
    st.metric("유효 김프(|김프|-비용)", f"{net_kimp_effective:+.2f}%")
    st.metric("예상 이익(원)", f"{est_profit_krw:,.0f}", delta=f"{net_kimp_effective:+.2f}%")

# -----------------------------
# History & chart
# -----------------------------
if "hist" not in st.session_state:
    st.session_state.hist = []
now = datetime.now(timezone.utc).astimezone().strftime("%H:%M")
st.session_state.hist.append({
    "time": now,
    "kimp": kimp,
    "abs_kimp": abs(kimp),
    "net_kimp_effective": net_kimp_effective,
    "profit": est_profit_krw,
    "price_src": price_source,
    "rate_src": rate_source,
})
hist_df = pd.DataFrame(st.session_state.hist)
st.line_chart(hist_df.set_index("time")["net_kimp_effective"], height=180, use_container_width=True)

# -----------------------------
# Alerts
# -----------------------------
abs_k = abs(kimp)
if alert_min <= abs_k < alert_max:
    st.warning(f"⚠️ |김프| 경계구간(1.5~2.0%) {abs_k:.2f}%")
elif abs_k >= alert_max:
    st.error(f"🚨 |김프| 강한 구간(≥2.0%) {abs_k:.2f}%")

st.markdown(
    """
    ### 📋 체크리스트 (오리지널 경로: BTC 직전송)
    - |김프| ≥ 임계치(1.5~2.0%)일 때 **방향(정/역) 최적화**하여 실행 가능
    - 루트: 업비트 BTC 매수(0.05%) → BTC 출금(0.0002 BTC) → 바이낸스 BTC 매도(0.1%) → USDT 출금(1 USDT) → 업비트 USDT 매도(0.05%)
    - 전송 지연, 환율 변동, 규제·세금 의무 주의
    """
)

# -----------------------------
# Auto refresh (minutes)
# -----------------------------
with contextlib.suppress(Exception):
    time.sleep(int(refresh_min) * 60)
    st.rerun()



