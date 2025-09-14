# 📈 BTC차액거래 – Streamlit Dashboard
# --------------------------------------
# 모바일 압축 모드 지원, PC 모드에서 넓은 폭 + 2행 카드
# 순/역 김프 모두 고려, 예상 이익 마이너스 표기
# 환율은 수동 입력, 새로고침 5~60분

import time, requests, pandas as pd
import streamlit as st
from datetime import datetime, timezone
import contextlib

UPBIT_TICKER_URL   = "https://api.upbit.com/v1/ticker"
BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price"

# 페이지 설정
st.set_page_config(page_title="BTC차액거래", page_icon="📈", layout="centered")

# 스타일
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

# 데이터 요청 함수
@st.cache_data(ttl=5)
def get_upbit_price_krw_btc():
    r = requests.get(UPBIT_TICKER_URL, params={"markets": "KRW-BTC"}, timeout=5)
    r.raise_for_status()
    return float(r.json()[0]["trade_price"])

@st.cache_data(ttl=5)
def get_binance_btcusdt():
    r = requests.get(BINANCE_TICKER_URL, params={"symbol":"BTCUSDT"}, timeout=5)
    r.raise_for_status()
    return float(r.json()["price"])

def calc_kimp(krw_btc: float, btcusdt: float, usdt_krw: float) -> float:
    return (krw_btc / (btcusdt * usdt_krw) - 1.0) * 100.0

def btc_route_cost_pct(capital_krw: float, krw_btc: float, usdt_krw: float,
                       upbit_fee=0.0005, binance_fee=0.001, etc_cost=0.002,
                       btc_withdraw_btc=0.0002, usdt_withdraw=1.0) -> float:
    trade_fee = upbit_fee + binance_fee + upbit_fee
    btc_withdraw_pct = (btc_withdraw_btc * krw_btc) / capital_krw
    usdt_withdraw_pct = (usdt_withdraw * usdt_krw) / capital_krw
    return (trade_fee + etc_cost + btc_withdraw_pct + usdt_withdraw_pct) * 100.0

st.title("BTC차액거래")

# 사이드바
with st.sidebar:
    st.header("설정")
    mobile_compact = st.toggle("모바일 압축 모드", value=True, help="끄면 PC 화면에 맞춰 넓게 보여줍니다.")
    capital = st.number_input("자본금(원)", value=10_000_000, step=1_000_000, format="%d")
    alert_min = st.number_input("알림 하한(|김프|, %)", value=1.5, step=0.1)
    alert_max = st.number_input("알림 상한(|김프|, %)", value=2.0, step=0.1)
    refresh_min = st.slider("새로고침(분)", 5, 60, 10)
    st.subheader("환율(USDT/KRW)")
    usdt_krw = st.number_input("USDT 1개당 원화", value=1390.0, step=1.0)

# 데이터 취득
try:
    krw_btc = get_upbit_price_krw_btc()
    btcusdt = get_binance_btcusdt()
except Exception as e:
    st.error(f"시세 조회 오류: {e}")
    st.stop()

# 계산
kimp = calc_kimp(krw_btc, btcusdt, usdt_krw)
route_cost = btc_route_cost_pct(capital, krw_btc, usdt_krw)
net_kimp_effective = abs(kimp) - route_cost
est_profit_krw = capital * (net_kimp_effective / 100.0)

# 지표 카드
if mobile_compact:
    st.metric("Upbit BTC/KRW", f"{krw_btc:,.0f}원")
    st.metric("Binance BTC/USDT", f"{btcusdt:,.2f} USDT")
    st.metric("USDT/KRW (수동)", f"{usdt_krw:,.2f}원")
    st.metric("KIMP", f"{kimp:+.2f}%")
else:
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
    r1c2.metric("Binance BTC/USDT", f"{btcusdt:,.2f} USDT")
    r1c3.metric("USDT/KRW (수동)", f"{usdt_krw:,.2f}원")
    r1c4.metric("KIMP", f"{kimp:+.2f}%")

    r2c1, r2c2, r2c3 = st.columns(3)
    r2c1.metric("총비용(%)", f"{route_cost:.2f}%")
    r2c2.metric("유효 김프(|김프|-비용)", f"{net_kimp_effective:+.2f}%")
    r2c3.metric("예상 이익(원)", f"{est_profit_krw:,.0f}", delta=f"{net_kimp_effective:+.2f}%")

# 모바일 모드일 때 추가 표시
if mobile_compact:
    st.subheader("비용 및 이익 추정")
    st.metric("총비용(%)", f"{route_cost:.2f}%")
    st.metric("유효 김프(|김프|-비용)", f"{net_kimp_effective:+.2f}%")
    st.metric("예상 이익(원)", f"{est_profit_krw:,.0f}", delta=f"{net_kimp_effective:+.2f}%")

# 히스토리와 차트
if "hist" not in st.session_state:
    st.session_state.hist = []
now = datetime.now(timezone.utc).astimezone().strftime("%H:%M")
st.session_state.hist.append({
    "time": now,
    "kimp": kimp,
    "abs_kimp": abs(kimp),
    "net_kimp_effective": net_kimp_effective,
    "profit": est_profit_krw
})
hist_df = pd.DataFrame(st.session_state.hist)
st.line_chart(hist_df.set_index("time")["net_kimp_effective"], height=180, use_container_width=True)

# 알림
abs_k = abs(kimp)
if alert_min <= abs_k < alert_max:
    st.warning(f"⚠️ |김프| 경계구간(1.5~2.0%) {abs_k:.2f}%")
elif abs_k >= alert_max:
    st.error(f"🚨 |김프| 강한 구간(≥2.0%) {abs_k:.2f}%")

st.markdown(
    """
    ### 📋 체크리스트
    - |김프| ≥ 임계치(1.5~2.0%)일 때 **방향(정/역) 최적화**하여 실행 가능
    - 루트: 업비트 BTC 매수(0.05%) → BTC 출금(0.0002 BTC) → 바이낸스 BTC 매도(0.1%) → USDT 출금(1 USDT) → 업비트 USDT 매도(0.05%)
    - 전송 지연, 환율 변동, 규제·세금 의무 주의
    """
)

# 자동 새로고침
with contextlib.suppress(Exception):
    time.sleep(int(refresh_min) * 60)
    st.rerun()
