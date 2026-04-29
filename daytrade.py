import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ構成と自動更新 ---
st.set_page_config(page_title="AI Live Strategist (完成)", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

# --- 2. APIキーの洗浄 ---
def get_model():
    if "GEMINI_API_KEY" not in st.secrets:
        return None
    try:
        key = str(st.secrets["GEMINI_API_KEY"]).strip().strip('"').strip("'")
        genai.configure(api_key=key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = get_model()
st.title("📡 AI Live Strategist (完成版)")

# --- 3. サイドバー ---
input_code = st.sidebar.text_input("銘柄コード", "BTC-USD")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code
mode = st.sidebar.radio("データ切替", ["テスト(仮想データ)", "本番データ"])

# --- 4. データ取得 (エラー回避強化) ---
def fetch_data(t, m):
    if m == "テスト(仮想データ)":
        dates = pd.date_range(pd.Timestamp.now(), periods=100, freq='1min')
        return pd.DataFrame({
            'Open': np.random.randn(100).cumsum() + 100,
            'High': np.random.randn(100).cumsum() + 102,
            'Low': np.random.randn(100).cumsum() + 98,
            'Close': np.random.randn(100).cumsum() + 100,
            'Volume': np.random.randint(100, 1000, 100)
        }, index=dates)
    else:
        try:
            data = yf.download(t, period="1d", interval="1m", progress=False, auto_adjust=True)
            if data is None or data.empty: return pd.DataFrame()
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            return data
        except Exception as e:
            return pd.DataFrame()

df = fetch_data(ticker, mode)

# --- 5. 解析と表示 ---
if not df.empty and len(df) > 1:
    # VWAP計算 (ゼロ除算エラー対策)
    v = df['Volume'].replace(0, 1) # 出来高0によるエラー防止
    df['VWAP'] = ((df['High'] + df['Low'] + df['Close']) / 3 * v).cumsum() / v.cumsum()
    
    last_p = float(df['Close'].iloc[-1])
    last_vwap = float(df['VWAP'].iloc[-1])

    # AI実況
    with st.container(border=True):
        if model:
            try:
                diff = "上振れ" if last_p > last_vwap else "下振れ"
                prompt = f"銘柄:{ticker}, 価格:{last_p:.1f}, VWAP:{last_vwap:.1f}。現在{diff}中。プロのアドバイスを30字以内で。語尾は『だ』。"
                res = model.generate_content(prompt)
                st.markdown(f"### 🔮 AI軍師の託宣\n**{res.text}**")
            except:
                st.warning("AIが準備中、またはAPIキーが正しくありません。")
        else:
            st.info("SecretsでAPIキーを正しく設定してください。")

    # チャート
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格")])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow', width=2)))
    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("データを取得できません。現在、Yahoo Financeのアクセス制限がかかっている可能性があります。")
    st.info("一度『テスト(仮想データ)』モードに切り替えて、AIが喋るか確認してください。")
