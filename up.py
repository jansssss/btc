import requests, pandas as pd, streamlit as st
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="BTC 김프 모니터", page_icon="📊", layout="wide")

# 간단한 스타일
st.markdown("""
<style>
.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #ddd;
    margin: 0.5rem 0;
}
.alert { padding: 1rem; border-radius: 6px; margin: 1rem 0; }
.alert-info { background: #e3f2fd; border-left: 4px solid #2196f3; }
.alert-warning { background: #fff3e0; border-left: 4px solid #ff9800; }
.alert-danger { background: #ffebee; border-left: 4px solid #f44336; }
</style>
""", unsafe_allow_html=True)

# API 함수들
@st.cache_data(ttl=10)
def get_upbit_btc():
    r = requests.get("https://api.upbit.com/v1/ticker", params={"markets": "KRW-BTC"})
    return float(r.json()[0]["trade_price"])

@st.cache_data(ttl=10)
def get_international_btc():
    # 바이낸스 시도
    binance_hosts = [
        "https://api.binance.com/api/v3/ticker/price",
        "https://api1.binance.com/api/v3/ticker/price",
        "https://api2.binance.com/api/v3/ticker/price"
    ]
    
    for url in binance_hosts:
        try:
            r = requests.get(url, params={"symbol": "BTCUSDT"}, timeout=5)
            if r.status_code == 200:
                return float(r.json()["price"]), "Binance"
        except:
            continue
    
    # Bybit 백업
    try:
        r = requests.get("https://api.bybit.com/v5/market/tickers", 
                        params={"category": "linear", "symbol": "BTCUSDT"}, timeout=5)
        if r.status_code == 200:
            return float(r.json()["result"]["list"][0]["lastPrice"]), "Bybit"
    except:
        pass
        
    raise Exception("모든 해외 거래소 접속 실패")

@st.cache_data(ttl=15)
def get_usdt_rate():
    r = requests.get("https://api.bithumb.com/public/ticker/USDT_KRW")
    return float(r.json()["data"]["closing_price"])

def calc_premium(krw, usdt, rate):
    return ((krw / (usdt * rate)) - 1) * 100

# UI
st.title("BTC 김치프리미엄 모니터")

# 사이드바
with st.sidebar:
    st.header("설정")
    capital = st.number_input("투자금액 (원)", value=10000000, step=1000000)
    alert_threshold = st.slider("알림 기준 (%)", 0.5, 3.0, 1.5, 0.1)

# 데이터 가져오기
try:
    col1, col2, col3 = st.columns(3)
    
    with st.spinner("데이터 로딩중..."):
        krw_btc = get_upbit_btc()
        usdt_btc, exchange = get_international_btc()
        usdt_rate = get_usdt_rate()
    
    premium = calc_premium(krw_btc, usdt_btc, usdt_rate)
    
    # 가격 표시
    with col1:
        st.metric("업비트 BTC", f"{krw_btc:,.0f}원")
    with col2:
        st.metric(f"{exchange} BTC", f"{usdt_btc:,.2f} USDT")
    with col3:
        st.metric("USDT 환율", f"{usdt_rate:,.0f}원")
    
    # 김프 표시
    st.metric("김치프리미엄", f"{premium:+.2f}%", 
             help="양수: 한국이 비쌈, 음수: 해외가 비쌈")
    
    # 수익 계산
    cost = 0.4  # 총 비용 약 0.4%
    net_premium = abs(premium) - cost
    profit = capital * (net_premium / 100)
    
    if net_premium > 0:
        st.success(f"💰 예상 수익: {profit:+,.0f}원 ({net_premium:.1f}%)")
    else:
        st.info(f"📊 수익 불가: 비용({cost}%) > 프리미엄({abs(premium):.1f}%)")
    
    # 알림
    if abs(premium) >= alert_threshold:
        if abs(premium) >= 2.0:
            st.error(f"🚨 높은 차액거래 기회: {abs(premium):.1f}%")
        else:
            st.warning(f"⚠️ 차액거래 기회: {abs(premium):.1f}%")
    
    # 히스토리 차트
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    st.session_state.history.append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'premium': premium
    })
    
    if len(st.session_state.history) > 50:
        st.session_state.history = st.session_state.history[-50:]
    
    if len(st.session_state.history) > 1:
        df = pd.DataFrame(st.session_state.history)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['premium'],
            mode='lines+markers', name='김프',
            line=dict(color='#2196f3', width=2)
        ))
        
        fig.add_hline(y=alert_threshold, line_dash="dash", line_color="orange")
        fig.add_hline(y=-alert_threshold, line_dash="dash", line_color="orange")
        fig.add_hline(y=0, line_dash="dot", line_color="gray")
        
        fig.update_layout(
            title="김치프리미엄 추이",
            xaxis_title="시간", yaxis_title="프리미엄 (%)",
            height=300, showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 간단한 가이드
    with st.expander("거래 가이드"):
        st.markdown(f"""
        **현재 상황:**
        - 김치프리미엄: {premium:+.1f}%
        - 예상 총 비용: ~0.4%
        - 최소 수익 기준: {cost}% 이상
        
        **거래 단계:**
        1. 업비트 BTC 매수/매도 (수수료 0.05%)
        2. 해외거래소 매도/매수 (수수료 0.1%)  
        3. 송금 수수료 + 환율 변동 (약 0.25%)
        
        ⚠️ 규제, 세금, 송금 지연 등 추가 리스크 고려 필요
        """)
    
    st.caption(f"📡 {exchange}, 빗썸 | ⏰ {datetime.now().strftime('%H:%M:%S')}")

except Exception as e:
    st.error(f"❌ 오류: {e}")
    st.info("💡 해결방법: VPN 확인, 잠시 후 새로고침")

# 새로고침 버튼
if st.button("🔄 새로고침"):
    st.cache_data.clear()
    st.rerun()
