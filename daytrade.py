import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ構成と自動更新 (1分間隔) ---
st.set_page_config(page_title="AI Live Strategist", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

# --- 2. Gemini APIの徹底的なクリーン設定 ---
def configure_ai():
    if "GEMINI_API_KEY" not in st.secrets:
        return None
    try:
        # APIキーから改行、空白、引用符を完全に除去
        raw_key = st.secrets["GEMINI_API_KEY"]
        clean_key = raw_key.strip().replace('"', '').replace("'", "").replace("\n", "").replace("\r", "")
        genai.configure(api_key=clean_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = configure_ai()

st.title("📡 AI Live Strategist (最終修正版)")

# --- 3. 監視銘柄の設定 ---
input_code = st.sidebar.text_input("監視銘柄コード", "BTC-USD")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code
mode = st.sidebar.radio("モード選択", ["本番データ", "テスト(仮想データ)"])

# --- 4. データの取得 ---
def get_stock_data(t, m):
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
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
            return pd.DataFrame()

df = get_stock_data(ticker, mode)

# --- 5. 解析と表示 ---
if not df.empty and len(df) > 0:
    # マルチインデックス対策
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # VWAP計算
    v = df['Volume']
    p = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (p * v).cumsum() / v.cumsum()
    
    last_p = float(df['Close'].iloc[-1])
    last_vwap = float(df['VWAP'].iloc[-1])

    # --- 6. AI実況セクション ---
    with st.expander("🔮 AI軍師のリアルタイム分析", expanded=True):
        if model:
            try:
                diff = last_p - last_vwap
                status = "上振れ" if diff > 0 else "下振れ"
                prompt = f"銘柄:{ticker}, 価格:{last_p:.1f}, VWAP:{last_vwap:.1f}。現在VWAPより{status}している。プロのデイトレーダーとして一言アドバイスを30字以内で。語尾は「～だ」で。"
                response = model.generate_content(prompt)
                st.success(f"**{response.text}**")
            except:
                st.warning("AIが応答できません。APIキーが正しいか確認してください。")
        else:
            st.info("APIキーを設定するとAI実況が開始されます。")

    # --- 7. チャート表示 ---
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格"
    )])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow', width=1.5)))
    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("💡 データを取得中、または市場時間外です。テストモードをお試しください。")
