import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ設定と自動更新 ---
st.set_page_config(page_title="AI Live Strategist", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

# --- 2. Gemini APIの設定 ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsに 'GEMINI_API_KEY' を設定してください。")
    st.stop()

try:
    # 鍵から余計な空白を削除して設定
    API_KEY = st.secrets["GEMINI_API_KEY"].strip()
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"API設定エラーが発生しました。")
    st.stop()

st.title("📡 AI Live Strategist (完成版)")

# --- 3. サイドバー設定 ---
input_code = st.sidebar.text_input("監視銘柄コード", "BTC-USD")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code
mode = st.sidebar.radio("モード選択", ["本番データ", "テスト(仮想データ)"])

# --- 4. データ取得関数 ---
def get_data(t, m):
    if m == "テスト(仮想データ)":
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
        try:
            return yf.download(t, period="1d", interval="1m", progress=False, auto_adjust=True)
        except:
            return pd.DataFrame()

df = get_data(ticker, mode)

# --- 5. 解析と表示 ---
if not df.empty:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 指標計算
    v = df['Volume']
    p = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (p * v).cumsum() / v.cumsum()
    
    last_p = float(df['Close'].values[-1])
    last_vwap = float(df['VWAP'].values[-1])
    
    st.subheader(f"📊 {ticker} 分析結果")

    # --- 6. AI診断 (復活！) ---
    with st.container(border=True):
        try:
            prompt = f"銘柄{ticker}, 価格{last_p:.1f}, VWAP{last_vwap:.1f}。今の状況から、プロのデイトレーダーとして次にすべき行動を「～だから～だ」という形式で30字以内でアドバイスして。"
            res = model.generate_content(prompt)
            st.markdown(f"### 🔮 AI軍師の託宣\n**{res.text}**")
        except:
            st.warning("AIが思考中、またはAPIキーのエラーです。Secretsを確認してください。")

    # --- 7. チャート表示 ---
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格"
    )])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow')))
    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("データを取得できません。モードを切り替えてください。")
