import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="AI Live Strategist", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

# API設定
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("APIキーを設定してください")
    st.stop()

st.title("📡 AI Live Strategist (テストモード搭載)")

# サイドバー
input_code = st.sidebar.text_input("監視銘柄コード", "BTC-USD")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code
mode = st.sidebar.radio("モード選択", ["本番データ", "テスト(仮想データ)"])

# --- データ取得 ---
def get_data(t, m):
    if m == "テスト(仮想データ)":
        # 制限を回避するために人工的なデータを作成
        dates = pd.date_range(pd.Timestamp.now(), periods=100, freq='1min')
        df = pd.DataFrame({
            'Open': np.random.randn(100).cumsum() + 100,
            'High': np.random.randn(100).cumsum() + 105,
            'Low': np.random.randn(100).cumsum() + 95,
            'Close': np.random.randn(100).cumsum() + 100,
            'Volume': np.random.randint(100, 1000, 100)
        }, index=dates)
        return df
    else:
        return yf.download(t, period="1d", interval="1m", progress=False)

df = get_data(ticker, mode)

if not df.empty:
    # 指標計算 (VWAP / MACD)
    v = df['Volume'].values
    p = (df['High'] + df['Low'] + df['Close']).values / 3
    df['VWAP'] = (p * v).cumsum() / v.cumsum()
    
    last_p = float(df['Close'].iloc[-1])
    last_vwap = float(df['VWAP'].iloc[-1])

    st.subheader(f"📊 {ticker} 分析中")
    
    # AI診断
    prompt = f"銘柄{ticker}, 価格{last_p:.1f}, VWAP{last_vwap:.1f}。デイトレ戦略を「～だから～だ」で30字で。"
    try:
        res = model.generate_content(prompt)
        st.success(f"**AI実況: {res.text}**")
    except:
        st.write("AI準備中...")

    # チャート
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow')))
    fig.update_layout(height=400, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Yahoo Financeが制限されています。サイドバーで『テストモード』に切り替えてください。")
