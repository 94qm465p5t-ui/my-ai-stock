import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ・自動更新設定 ---
st.set_page_config(page_title="AI Live Strategist", layout="wide")
# 更新間隔を90秒に設定（アクセス制限回避のため少し緩和）
st_autorefresh(interval=90000, key="datarefresh")

# --- 2. Gemini APIの設定 (最安定化バージョン) ---
# Secretsから直接読み込み、エラーがあれば即停止させる
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ StreamlitのSecretsに 'GEMINI_API_KEY' が設定されていません。")
    st.stop()

try:
    API_KEY = st.secrets["GEMINI_API_KEY"].strip().replace('"', '').replace("'", "")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ APIキーの認証に失敗しました: {e}")
    st.stop()

st.title("📡 AI Live Strategist (安定版)")

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
            # yfinanceのマルチインデックス対策
            data = yf.download(t, period="1d", interval="1m", progress=False, auto_adjust=True)
            return data
        except:
            return pd.DataFrame()

df = get_data(ticker, mode)

# --- 5. データ解析と表示 ---
if not df.empty and len(df) > 0:
    try:
        # マルチインデックスの強制解除
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 指標計算
        v = df['Volume']
        p = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (p * v).cumsum() / v.cumsum()
        
        # 最新値の抽出（.iloc[-1] で最後の要素を取得）
        last_p = float(df['Close'].values[-1])
        last_vwap = float(df['VWAP'].values[-1])

        st.subheader(f"📊 {ticker} 分析中")
        
        # --- AI診断セクション ---
        try:
            prompt = f"銘柄{ticker}, 価格{last_p:.1f}, VWAP{last_vwap:.1f}。今の戦略を「～だから～だ」という形式でプロの視点から30字以内で語れ。"
            res = model.generate_content(prompt)
            st.success(f"**AI実況: {res.text}**")
        except Exception as ai_err:
            st.warning("AI分析を準備中です...")

        # --- チャート表示 ---
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格"
        )])
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow', width=2)))
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error("データ処理中にエラーが発生しました。サイドバーで『テストモード』に切り替えてみてください。")
else:
    st.info("💡 現在、有効なデータが取得できません。市場稼働時間外か、アクセス制限の可能性があります。")
    if mode == "本番データ":
        st.write("『テスト(仮想データ)』モードに切り替えると、動作テストが可能です。")
