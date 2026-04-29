import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ設定と自動更新 ---
st.set_page_config(page_title="AI Live Strategist", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

st.title("📡 AI Live Strategist (復旧モード)")

# --- 2. API設定を完全に無視する ---
# ログの原因となるAI通信をすべてコメントアウトし、エラーを物理的に遮断します

# --- 3. サイドバー設定 ---
input_code = st.sidebar.text_input("監視銘柄コード", "BTC-USD")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code
mode = st.sidebar.radio("モード選択", ["テスト(仮想データ)", "本番データ"])

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
            # プログレスバーなし、自動調整あり
            return yf.download(t, period="1d", interval="1m", progress=False, auto_adjust=True)
        except:
            return pd.DataFrame()

df = get_data(ticker, mode)

# --- 5. 表示 ---
if not df.empty:
    # 列名の整理
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # シンプルな指標
    v = df['Volume']
    p = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (p * v).cumsum() / v.cumsum()
    
    last_p = float(df['Close'].values[-1])
    
    st.subheader(f"📊 {ticker} 分析結果")
    st.info(f"現在値: {last_p:.1f} | ※現在、エラー防止のためAI実況を停止しています")

    # チャート
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格"
    )])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow')))
    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("データを取得できません。モードを『テスト』に切り替えてください。")
