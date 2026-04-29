import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. ページ基本設定 (Duplicateエラー防止)
# ==========================================
st.set_page_config(page_title="AI Live Strategist", layout="wide")

# 自動更新 (1分ごとにリフレッシュ)
st_autorefresh(interval=60000, key="refresh_engine_final")

# ==========================================
# 2. AI設定 (Secretsから確実にキーを読み込む)
# ==========================================
def get_ai_model():
    # Secretsの "GEMINI_API_KEY" を直接指定して取得
    token = st.secrets.get("GEMINI_API_KEY")
    
    if not token or token == "あなたのAPIキー":
        return None
    
    try:
        # キーの前後にある余計な空白などを除去
        clean_token = str(token).strip().strip('"').strip("'")
        genai.configure(api_key=clean_token)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception:
        return None

model = get_ai_model()

# ==========================================
# 3. メイン画面の表示
# ==========================================
st.title("📡 AI Live Strategist")

# サイドバー設定
st.sidebar.header("設定")
ticker = st.sidebar.text_input("銘柄コード", "BTC-USD")
mode = st.sidebar.radio("データ取得モード", ["本番データ", "テスト(仮想データ)"])

# ==========================================
# 4. データ取得
# ==========================================
@st.cache_data(ttl=60)
def load_market_data(t, m):
    if m == "テスト(仮想データ)":
        idx = pd.date_range(pd.Timestamp.now(), periods=100, freq='1min')
        return pd.DataFrame({
            'Open': np.random.randn(100).cumsum()+100,
            'High': np.random.randn(100).cumsum()+102,
            'Low': np.random.randn(100).cumsum()+98,
            'Close': np.random.randn(100).cumsum()+100,
            'Volume': np.random.randint(100, 1000, 100)
        }, index=idx)
    
    try:
        d = yf.download(t, period="1d", interval="1m", progress=False, auto_adjust=True)
        if d is None or d.empty: return pd.DataFrame()
        if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
        return d
    except:
        return pd.DataFrame()

df = load_market_data(ticker, mode)

# ==========================================
# 5. 解析・チャート表示
# ==========================================
if not df.empty and len(df) > 1:
    # VWAP計算
    df['VWAP'] = ((df['High'] + df['Low'] + df['Close']) / 3 * df['Volume']).cumsum() / df['Volume'].cumsum()
    current_price = float(df['Close'].iloc[-1])

    # --- AIの助言 ---
    st.subheader("🔮 AI軍師のリアルタイム分析")
    if model:
        try:
            prompt = f"銘柄{ticker}の現在価格は{current_price:.2f}です。最近の推移を見て、デイトレードのアドバイスを日本語30文字以内でズバッと簡潔に言ってください。"
            response = model.generate_content(prompt)
            st.success(f"【助言】: {response.text}")
        except Exception:
            st.warning("AIが応答できません。APIキーが有効か確認してください。")
    else:
        st.error("⚠️ AIキーが読み込めていません。Secretsの設定を見直してください。")

    # --- チャート表示 ---
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格"))
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow', width=1.5)))
    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("データを取得できません。銘柄コードを確認してください。")
