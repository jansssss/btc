import requests, pandas as pd
import streamlit as st
from datetime import datetime, timezone
import plotly.graph_objects as go

# Configuration
st.set_page_config(
    page_title="BTC 김프 모니터", 
    page_icon="📊", 
    layout="wide"
)

# API Endpoints
UPBIT_URL = "https://api.upbit.com/v1/ticker"
BINANCE_URLS = [
    "https://api.binance.com/api/v3/ticker/price",
    "https://api1.binance.com/api/v3/ticker/price",
    "https://api2.binance.com/api/v3/ticker/price"
]
BYBIT_URL = "https://api.bybit.com/v5/market/tickers"
BITHUMB_URL = "https://api.bithumb.com/public/ticker/USDT_KRW"

# Clean, professional styling
st.markdown("""
<style>
body { 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #fafafa;
}

.main-header {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #e1e5e9;
    margin-bottom: 2rem;
}

.metric-box {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #e1e5e9;
    margin: 0.5rem 0;
}

.alert-box {
    padding: 1rem 1.5rem;
    border-radius: 6px;
    margin: 1rem 0;
    font-weight: 500;
}

.alert-info { background: #e3f2fd; border-left: 4px solid #2196f3; }
.alert-warning { background: #fff3e0; border-left: 4px solid #ff9800; }
.alert-danger { background: #ffebee; border-left: 4px solid #f44336; }

.price-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

@media (max-width: 768px) {
    .price-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# Data functions
@st.cache_data(ttl=10)
def get_upbit_btc():
    r = requests.get(UPBIT_URL, params={"markets": "KRW-BTC"})
    return float(r.json()[0]["trade_price"])

@st.cache_data(ttl=10)
def get_international_btc():
    # Try Binance first
    for url in BINANCE_URLS:
        try:
            r = requests.get(url, params={"symbol": "BTCUSDT"}, timeout=5)
            r.raise_for_status()
            data = r.json()
            if 'price' in data:
                return float(data["price"]), "Binance"
        except:
            continue
    
    # Fallback to Bybit
    try:
        r = requests.get(BYBIT_URL, params={"category": "linear", "symbol": "BTCUSDT"}, timeout=5)
        r.raise_for_status()
        data = r.json()
        if 'result' in data and 'list' in data['result'] and len(data['result']['list']) > 0:
            return float(data['result']['list'][0]['lastPrice']), "Bybit"
    except:
        pass
    
    raise Exception("모든 국제 거래소 접속 실패")

@st.cache_data(ttl=15)
def get_usdt_rate():
    r = requests.get(BITHUMB_URL)
    return float(r.json()["data"]["closing_price"])

def calc_premium(krw_price, usdt_price, rate):
    return ((krw_price / (usdt_price * rate)) - 1) * 100

# Main app
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; color: #1a1a1a;">BTC 김치프리미엄 모니터</h1>
    <p style="margin: 0.5rem 0 0 0; color: #666;">실시간 차익거래 기회 분석</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("설정")
    capital = st.number_input("투자금액 (원)", value=10000000, step=1000000)
    alert_threshold = st.slider("알림 임계값 (%)", 0.5, 3.0, 1.5, 0.1)
    
    theme = st.selectbox("테마", ["라이트", "다크"])
    if theme == "다크":
        st.markdown("""
        <style>
        body { background: #1a1a1a; color: #e0e0e0; }
        .main-header, .metric-box { 
            background: #2d2d2d; 
            border-color: #404040;
            color: #e0e0e0;
        }
        </style>
        """, unsafe_allow_html=True)

# Fetch data
try:
    krw_btc = get_upbit_btc()
    usdt_btc, exchange_name = get_international_btc()
    usdt_rate = get_usdt_rate()
    premium = calc_premium(krw_btc, usdt_btc, usdt_rate)
    
    # Price display
    st.markdown('<div class="price-grid">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("업비트 BTC", f"{krw_btc:,.0f}원")
    with col2:
        st.metric(f"{exchange_name} BTC", f"{usdt_btc:,.2f} USDT")
    with col3:
        st.metric("USDT 환율", f"{usdt_rate:,.0f}원")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Premium analysis
    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
    st.metric(
        "김치프리미엄", 
        f"{premium:+.2f}%",
        help="양수: 한국이 비쌈 (매도 유리), 음수: 해외가 비쌈 (매수 유리)"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Calculate potential profit
    if abs(premium) > 0.5:  # 최소 수수료 고려
        cost_pct = 0.4  # 대략적인 총 비용 (수수료 + 슬리피지)
        net_premium = abs(premium) - cost_pct
        potential_profit = capital * (net_premium / 100)
        
        if net_premium > 0:
            profit_text = f"예상 수익: {potential_profit:+,.0f}원 (순 {net_premium:.1f}%)"
        else:
            profit_text = f"수익 불가: 비용({cost_pct}%) > 프리미엄({abs(premium):.1f}%)"
    else:
        profit_text = "차익거래 기회 없음"
    
    st.info(profit_text)
    
    # Alerts
    if abs(premium) >= alert_threshold:
        if abs(premium) >= 2.0:
            st.markdown(f'<div class="alert-box alert-danger">🚨 높은 차익거래 기회: {abs(premium):.1f}%</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-box alert-warning">⚠️ 차익거래 기회: {abs(premium):.1f}%</div>', 
                       unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box alert-info">📊 정상 범위</div>', unsafe_allow_html=True)
    
    # History chart
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    now = datetime.now()
    st.session_state.history.append({
        'time': now.strftime('%H:%M:%S'),
        'premium': premium
    })
    
    # Keep last 50 points
    if len(st.session_state.history) > 50:
        st.session_state.history = st.session_state.history[-50:]
    
    if len(st.session_state.history) > 1:
        df = pd.DataFrame(st.session_state.history)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['premium'],
            mode='lines+markers',
            name='김치프리미엄',
            line=dict(color='#2196f3', width=2),
            marker=dict(size=4)
        ))
        
        fig.add_hline(y=alert_threshold, line_dash="dash", line_color="orange", 
                     annotation_text=f"알림선 ({alert_threshold}%)")
        fig.add_hline(y=-alert_threshold, line_dash="dash", line_color="orange")
        fig.add_hline(y=0, line_dash="dot", line_color="gray")
        
        fig.update_layout(
            title="김치프리미엄 추이",
            xaxis_title="시간",
            yaxis_title="프리미엄 (%)",
            height=400,
            showlegend=False,
            template="plotly_white",
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Simple checklist
    with st.expander("거래 체크리스트"):
        st.markdown("""
        **거래 전 확인사항:**
        - [ ] 프리미엄이 총 비용(0.4%) 초과
        - [ ] 충분한 거래량 확인
        - [ ] 출금 한도 확인
        - [ ] 세금 신고 준비
        
        **예상 비용:**
        - 업비트 매매: 0.05% × 2 = 0.1%
        - 바이낸스 매매: 0.1%
        - 송금 수수료 + 슬리피지: ~0.2%
        - **총 예상 비용: ~0.4%**
        """)

    # Data source info
    st.caption(f"📡 데이터 소스: 업비트, {exchange_name}, 빗썸")

except Exception as e:
    st.error(f"❌ 데이터 로딩 실패: {e}")
    st.info("💡 해결 방법:")
    st.write("1. 인터넷 연결 확인")
    st.write("2. VPN 사용 시 한국 서버로 변경")
    st.write("3. 잠시 후 새로고침 버튼 클릭")

# Auto refresh
if st.button("새로고침"):
    st.cache_data.clear()
    st.rerun()

st.markdown("---")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
