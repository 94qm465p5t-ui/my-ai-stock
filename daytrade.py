import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ・自動更新設定 ---
st.set_page_config(page_title="AI Live Strategist", layout="wide")
st_autorefresh(interval=90000, key="datarefresh")

# --- 2. Gemini APIの設定 (直接埋め込み版) ---
# 下の "ここにAPIキーを貼る" をあなたの実際のキー（AIza...）に書き換えてください
MY_API_KEY = "ここにあなたのAPIキーを貼り付けてください"

try:
    genai.configure(api_key=MY_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"API設定エラー: {e}")
    st.stop()

st.title("📡 AI Live Strategist (最終修正版)")

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
            data = yf.download(t, period="1d", interval="1m", progress=False, auto_adjust=True)
            return data
        except:
            return pd.DataFrame()

df = get_data(ticker, mode)

# --- 5. データ解析と表示 ---
if not df.empty and len(df) > 0:
    try:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        v = df['Volume']
        p = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (p * v).cumsum() / v.cumsum()
        
        last_p = float(df['Close'].values[-1])
        last_vwap = float(df['VWAP'].values[-1])

        st.subheader(f"📊 {ticker} 分析中")
        
        # AI診断
        try:
            prompt = f"銘柄{ticker}, 価格{last_p:.1f}, VWAP{last_vwap:.1f}。今の戦略を「～だから～だ」で30字以内で語れ。"
            res = model.generate_content(prompt)
            st.success(f"**AI実況: {res.text}**")
        except:
            st.warning("AIが応答していません。APIキーを確認してください。")

        # チャート
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格"
        )])
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow', width=2)))
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error("エラーが発生しました。サイドバーでテストモードを試してください。")
else:
    st.info("💡 データが取得できません。テストモードに切り替えると動作を確認できます。")
