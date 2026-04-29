import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ設定と自動更新 ---
st.set_page_config(page_title="AI Live Strategist", layout="wide")
# 60秒ごとに画面を自動更新
st_autorefresh(interval=60000, key="datarefresh")

# --- 2. Gemini APIの設定 (エラー防止強化) ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ Secretsに 'GEMINI_API_KEY' が設定されていません。")
    st.stop()

# グローバル変数としてモデルを初期化
model = None
try:
    # 鍵から余計な空白を徹底的に排除
    API_KEY = st.secrets["GEMINI_API_KEY"].strip().replace('"', '').replace("'", "")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ API初期化エラー。キーを確認してください。")

st.title("📡 AI Live Strategist (最終完全版)")

# --- 3. サイドバー設定 ---
input_code = st.sidebar.text_input("監視銘柄コード", "BTC-USD")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code
# 最初からテストモードを選択できるように「テスト」を先に配置
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
            return yf.download(t, period="1d", interval="1m", progress=False, auto_adjust=True)
        except:
            return pd.DataFrame()

df = get_data(ticker, mode)

# --- 5. 解析と表示 ---
if not df.empty and len(df) > 0:
    try:
        # マルチインデックスの強制解除
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 指標計算 (VWAP)
        v = df['Volume']
        p = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (p * v).cumsum() / v.cumsum()
        
        last_p = float(df['Close'].values[-1])
        last_vwap = float(df['VWAP'].values[-1])
        
        st.subheader(f"📊 {ticker} 分析結果")

        # --- 6. AI診断 (絶対止まらない書き方) ---
        with st.container(border=True):
            if model is not None:
                try:
                    prompt = f"銘柄{ticker}, 価格{last_p:.1f}, VWAP{last_vwap:.1f}。プロの視点で「～だから～だ」と30字以内で助言して。"
                    res = model.generate_content(prompt)
                    st.markdown(f"### 🔮 AI軍師の託宣\n**{res.text}**")
                except Exception as ai_err:
                    st.warning("⚠️ AIが現在応答できません。APIキーの形式（Secrets）を再確認してください。")
            else:
                st.info("💡 AIを準備中です...")

        # --- 7. チャート表示 ---
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格"
        )])
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow', width=2)))
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error("データ処理中にエラーが発生しました。モードを切り替えてください。")
else:
    st.info("💡 データを読み込んでいます。市場時間外の場合は『テストモード』にしてください。")
