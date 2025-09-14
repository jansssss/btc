# 📈 BTC차액거래 – Streamlit Dashboard (모바일 최적화 / 수동 환율)
# -------------------------------------------------
# - 제목 간략화: BTC차액거래
# - 예상 이익: 양수/0/음수 모두 표시 (손실일 경우 마이너스 표시)
# - 디자인: 클로드 스타일(깔끔·미래지향)

import time, requests, pandas as pd
import streamlit as st
from datetime import datetime, timezone
import contextlib

UPBIT_TICKER_URL   = "https://api.upbit.com/v1/ticker"
BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price"
BINANCE_HOSTS = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
    "https://api-gcp.binance.com",
]
OKX_TICKER_URL = "https://www.okx.com/api/v5/market/ticker"  # ?instId=BTC-USDT
BYBIT_TICKER_URL = "https://api.bybit.com/v5/market/tickers"  # ?category=linear&symbol=BTCUSDT

# ---- 페이지 / 전역 스타일 ----
# 페이지 레이아웃은 기본 centered로 시작 (모바일 최적화)
st.set_page_config(page_title="BTC차액거래", page_icon="📈", layout="centered")

# 기본(모바일) 스타일
st.markdown(
    """
    <style>
    .block-container {padding-top:1rem; padding-bottom:2rem; max-width:700px;}
    body {background-color:#0d1117; color:#f0f6fc; font-family: 'Segoe UI', sans-serif;}
    h1, h2, h3, h4 {color:#58a6ff;}
    .stMetric {background:rgba(88,166,255,0.08); border-radius:14px; padding:0.6rem 0.8rem; border:1px solid rgba(88,166,255,0.12);} 
    .stSlider > div {padding-top:0.5rem; padding-bottom:0.5rem;}
    @media (max-width:640px){.stMetric{text-align:left!important;}}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(ttl=5)
def get_upbit_price_krw_btc():
    r = requests.get(UPBIT_TICKER_URL, params={"markets": "KRW-BTC"}, timeout=5)
    r.raise_for_status()
    return float(r.json()[0]["trade_price"])

@st.cache_data(ttl=5)
def get_binance_btcusdt():
    """여러 호스트로 바이낸스 REST를 시도. 451 등 오류 시 예외 발생."""
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
    for host in BINANCE_HOSTS:
        try:
            r = requests.get(f"{host}/api/v3/ticker/price", params={"symbol":"BTCUSDT"}, headers=headers, timeout=5)
            r.raise_for_status()
            return float(r.json()["price"])
        except Exception:
            continue
    raise requests.HTTPError("Binance price fetch failed across all hosts")

@st.cache_data(ttl=5)
def get_okx_btcusdt():
    r = requests.get(OKX_TICKER_URL, params={"instId": "BTC-USDT"}, timeout=5)
    r.raise_for_status()
    js = r.json()
    return float(js["data"][0]["last"])  # USDT

@st.cache_data(ttl=5)
def get_bybit_btcusdt():
    r = requests.get(BYBIT_TICKER_URL, params={"category":"linear", "symbol":"BTCUSDT"}, timeout=5)
    r.raise_for_status()
    js = r.json()
    return float(js["result"]["list"][0]["lastPrice"])  # USDT

def calc_kimp(krw_btc: float, btcusdt: float, usdt_krw: float) -> float:
    return (krw_btc / (btcusdt * usdt_krw) - 1.0) * 100.0

def btc_route_cost_pct(capital_krw: float, krw_btc: float, usdt_krw: float,
                       upbit_fee=0.0005, binance_fee=0.001, etc_cost=0.002,
                       btc_withdraw_btc=0.0002, usdt_withdraw=1.0) -> float:
    trade_fee = upbit_fee + binance_fee + upbit_fee
    btc_withdraw_pct  = (btc_withdraw_btc * krw_btc) / capital_krw
    usdt_withdraw_pct = (usdt_withdraw * usdt_krw) / capital_krw
    return (trade_fee + etc_cost + btc_withdraw_pct + usdt_withdraw_pct) * 100.0

st.title("📈 BTC차액거래")

with st.sidebar:
    st.header("설정")
    mobile_compact = st.toggle("모바일 압축 모드", value=True, help="끄면 PC 화면에 맞춰 넓게 보여줍니다.")
    capital = st.number_input("자본금(원)", value=10_000_000, step=1_000_000, format="%d")
    alert_min = st.number_input("알림 하한(|김프|, %)", value=1.5, step=0.1)
    alert_max = st.number_input("알림 상한(|김프|, %)", value=2.0, step=0.1)
    refresh_min = st.slider("새로고침(분)", 5, 60, 10)
    st.subheader("환율(USDT/KRW)")
    usdt_krw = st.number_input("USDT 1개당 원화", value=1390.0, step=1.0)
    st.subheader("데이터 소스")
    allow_alt = st.toggle("바이낸스 장애 시 대체 거래소 사용(OKX→Bybit)", value=True)

try:
    krw_btc = get_upbit_price_krw_btc()
    price_source = "Binance"
    try:
        btcusdt = get_binance_btcusdt()
    except Exception as be:
        if allow_alt:
            # Fallback: OKX → Bybit 순서로 시도
            try:
                btcusdt = get_okx_btcusdt()
                price_source = "OKX"
            except Exception:
                btcusdt = get_bybit_btcusdt()
                price_source = "Bybit"
        else:
            raise be
except Exception as e:
    st.error(f"시세 조회 오류: {e}")
    st.stop()

kimp = calc_kimp(krw_btc, btcusdt, usdt_krw)
route_cost = btc_route_cost_pct(capital, krw_btc, usdt_krw)
net_kimp = abs(kimp) - route_cost
est_profit_krw = capital * (net_kimp / 100.0)

if mobile_compact:
    st.metric("Upbit BTC/KRW", f"{krw_btc:,.0f}원")
    st.metric(f"{price_source} BTC/USDT", f"{btcusdt:,.2f} USDT")
    st.metric("USDT/KRW (수동)", f"{usdt_krw:,.2f}원")
    st.metric("KIMP", f"{kimp:+.2f}%")
else:
    # 데스크톱(압축 해제): 넓은 영역 활용, 2행 카드 레이아웃
    st.markdown(
        """
        <style>
        /* 데스크톱 전용 확장 폭 및 카드 여백 개선 */
        .block-container { max-width: 1200px; }
        .stMetric { padding: 0.9rem 1.0rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    r1c1, r1c2, r1c3, r1c4 = st.columns([1,1,1,1])
    r1c1.metric("Upbit BTC/KRW", f"{krw_btc:,.0f}원")
    r1c2.metric(f"{price_source} BTC/USDT", f"{btcusdt:,.2f} USDT")
    r1c3.metric("USDT/KRW (수동)", f"{usdt_krw:,.2f}원")
    r1c4.metric("KIMP", f"{kimp:+.2f}%")

    r2c1, r2c2, r2c3 = st.columns([1,1,1])
    r2c1.metric("총비용(%)", f"{route_cost:.2f}%")
    r2c2.metric("유효 김프(|김프|-비용)", f"{net_kimp:+.2f}%")
    r2c3.metric("예상 이익(원)", f"{est_profit_krw:,.0f}", delta=f"{net_kimp:+.2f}%")
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Upbit BTC/KRW", f"{krw_btc:,.0f}원")
    col2.metric("Binance BTC/USDT", f"{btcusdt:,.2f} USDT")
    col3.metric("USDT/KRW (수동)", f"{usdt_krw:,.2f}원")
    col4.metric("KIMP", f"{kimp:+.2f}%")

st.subheader("비용 및 이익 추정")
if mobile_compact:
    st.metric("총비용(%)", f"{route_cost:.2f}%")
    st.metric("유효 김프(|김프|-비용)", f"{net_kimp:+.2f}%")
else:
    # 데스크톱에서는 위에서 r2 행으로 노출했으므로 중복 노출 생략
    pass

# 예상 이익 (손실 시 마이너스 표시)
profit_text = f"{est_profit_krw:,.0f} 원" if est_profit_krw != 0 else "0 원"
st.metric("예상 이익(원)", profit_text)

if "hist" not in st.session_state:
    st.session_state.hist = []
now = datetime.now(timezone.utc).astimezone().strftime("%H:%M")
st.session_state.hist.append({"time":now, "kimp":kimp, "net_kimp":net_kimp, "profit":est_profit_krw})
hist_df = pd.DataFrame(st.session_state.hist)
st.line_chart(hist_df.set_index("time")["net_kimp"], height=180, use_container_width=True)

abs_k = abs(kimp)
if alert_min <= abs_k < alert_max:
    st.warning(f"⚠️ |김프| 경계구간(1.5~2.0%) {abs_k:.2f}%")
elif abs_k >= alert_max:
    st.error(f"🚨 |김프| 강한 구간(≥2.0%) {abs_k:.2f}%")

st.markdown(
    """
    ### 📋 체크리스트
    - |김프| ≥ 임계치(1.5~2.0%)일 때 실행 가능 (정/역 모두 고려)
    - 업비트 BTC 매수 → BTC 전송 → 바이낸스 매도 → USDT 전송 → 업비트 매도
    - 전송 지연, 환율 변동, 규제·세금 유의
    """
)

with contextlib.suppress(Exception):
    time.sleep(int(refresh_min) * 60)
    st.rerun()
