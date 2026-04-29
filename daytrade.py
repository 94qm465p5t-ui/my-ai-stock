import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. ページ基本設定 (Duplicateエラー防止のため最初に書く)
# ==========================================
st.set_page_config(page_title="AI Live Strategist", layout="wide")

# 自動更新 (1分ごとに画面をリフレッシュ)
# エラーが出た場合は、この key を "unique_refresh_key" などに変更してください
st_autorefresh(interval=60000, key="refresh_engine_v1")

# ==========================================
# 2. AI設定 (APIキーのスペルミスを自動カバー)
# ==========================================
def get_ai_model():
    # Secretsに GEMINI_API_KEY または GEMIN_API_KEY があれば読み込む
    keys = ["GEMINI_API_KEY", "GEMIN_API_KEY", "api_key"]
    token = None
    for k in keys:
        if k in st.secrets:
            token = st.secrets[k]
            break
    
    if not token or token == "あなたのAPIキー":
        return None
    
    try:
        # 余計な空白や引用符を削除して設定
        clean_token = str(token).strip().strip('"').strip("'")
        genai.configure(api_key=clean_token)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = get_ai_model()

# ==========================================
# 3. メイン画面の構成
# ==========================================
st.title("📡 AI Live Strategist")

# サイドバー設定
st.sidebar.header("設定")
ticker = st.sidebar.text_input("銘柄コード (例: BTC-USD, AAPL)", "BTC-USD")
mode = st.sidebar.radio("データ取得モード", ["テスト(仮想データ)", "本番データ"])

# ==========================================
# 4. データ取得関数 (エラー対策版)
# ==========================================
@st.cache_data(ttl=60)
def load_market_data(t, m):
    if m == "テスト(仮想データ)":
        # テスト用のダミーデータ生成
        idx = pd.date_range(pd.Timestamp.now(), periods=100, freq='1min')
        return pd.DataFrame({
            'Open': np.random.randn(100).cumsum()+100,
            'High': np.random.randn(100).cumsum()+102,
            'Low': np.random.randn(100).cumsum()+98,
            'Close': np.random.randn(100).cumsum()+100,
            'Volume': np.random.randint(100, 1000, 100)
        }, index=idx)
    
    try:
        # Yahoo Financeからデータ取得
        d = yf.download(t, period="1d", interval="1m", progress=False, auto_adjust=True)
        if d is None or d.empty:
            return pd.DataFrame()
        # 列名が複雑な場合の対策
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        return d
    except Exception:
        return pd.DataFrame()

df = load_market_data(ticker, mode)

# ==========================================
# 5. 解析・表示
# ==========================================
if not df.empty and len(df) > 1:
    # テクニカル指標計算 (VWAP)
    df['VWAP'] = ((df['High'] + df['Low'] + df['Close']) / 3 * df['Volume']).cumsum() / df['Volume'].cumsum()
    current_price = float(df['Close'].iloc[-1])

    # --- AIの助言セクション ---
    st.subheader("🔮 AI軍師のリアルタイム分析")
    if model:
        try:
            # AIへの指示
            prompt = f"銘柄{ticker}の現在価格は{current_price:.2f}です。最近の推移を見て、デイトレードのアドバイスを日本語30文字以内でズバッと言ってください。"
            response = model.generate_content(prompt)
            st.success(f"【助言】: {response.text}")
        except Exception as e:
            st.warning("AIが休憩中です（APIキーを確認してください）")
    else:
        st.info("💡 Secretsに正しいAPIキーを設定すると、ここにAIの助言が表示されます。")

    # --- チャート表示 ---
    fig = go.Figure()
    # ローソク足
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], 
        low=df['Low'], close=df['Close'], name="価格"
    ))
    # VWAP線
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow', width=1.5)))
    
    fig.update_layout(
        height=500,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("データを取得できませんでした。銘柄コードが正しいか確認するか、テストモードに切り替えてください。")
