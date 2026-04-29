import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ・自動更新設定 ---
st.set_page_config(page_title="AI Live Strategist", layout="wide")
# 更新間隔を90秒(90000ms)に緩和して制限を回避
st_autorefresh(interval=90000, key="datarefresh")

# --- 2. Gemini APIの設定 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("APIキーが設定されていません。")
    st.stop()

st.title("📡 AI Live Strategist (安定稼働版)")

# --- 3. サイドバー設定 ---
input_code = st.sidebar.text_input("監視銘柄コード", "7203")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code

# --- 4. データ取得（キャッシュ機能を追加） ---
@st.cache_data(ttl=60)  # 60秒間は同じデータを使い回し、Yahooへの負荷を減らす
def get_stock_data(t):
    try:
        data = yf.download(t, period="1d", interval="1m", progress=False)
        return data
    except:
        return pd.DataFrame()

df = get_stock_data(ticker)

# --- 5. データが存在する場合の処理 ---
if not df.empty and len(df) > 5: # ある程度のデータ量がある時のみ実行
    try:
        # 指標計算
        v = df['Volume'].values
        p = (df['High'] + df['Low'] + df['Close']).values / 3
        df['VWAP'] = (p * v).cumsum() / v.cumsum()
        
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        last_p = float(df['Close'].iloc[-1])
        last_vwap = float(df['VWAP'].iloc[-1])
        last_macd = float(df['MACD'].iloc[-1])
        last_sig = float(df['Signal'].iloc[-1])

        # --- 表示 ---
        st.subheader(f"📊 {ticker} 状況分析")
        c1, c2, c3 = st.columns(3)
        c1.metric("現在値", f"{last_p:.1f}")
        c2.metric("VWAP乖離", f"{last_p - last_vwap:.1f}")
        c3.metric("MACD", "強気" if last_macd > last_sig else "弱気")

        # --- AI実況（キャッシュを活用してAPI節約） ---
        @st.cache_data(ttl=90) # AIの回答も90秒は保持
        def get_ai_analysis(t, p, v, m, s):
            prompt = f"銘柄{t},価格{p},VWAP{v:.1f},MACD{m:.2f}。プロとして「～だから～だ」という形式で今の戦略を40字で語れ。"
            response = model.generate_content(prompt)
            return response.text

        st.write("---")
        with st.container(border=True):
            st.markdown(f"### 🎯 AI軍師のリアルタイム実況\n**{get_ai_analysis(ticker, last_p, last_vwap, last_macd, last_sig)}**")
            st.caption(f"自動更新中... 次回更新までお待ちください")

        # --- チャート表示 ---
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='1分足'))
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name='VWAP', line=dict(color='yellow', dash='dot')))
        fig.update_layout(height=400, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning("現在、データを整理中です。数秒後に再試行します。")
else:
    st.info("市場が閉まっているか、アクセス制限がかかっています。15分ほど空けてから再接続してください。")
