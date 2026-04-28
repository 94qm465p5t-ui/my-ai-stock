import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- ページ設定 ---
st.set_page_config(page_title="Pro Stock Analyzer", layout="wide")

# 🔑 Geminiの設定
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🛡️ Professional Stock Analyzer")

# --- サイドバー ---
st.sidebar.header("設定")
input_code = st.sidebar.text_input("銘柄コード (4桁数字)", "7203")

if input_code.isdigit() and len(input_code) == 4:
    ticker = f"{input_code}.T"
else:
    ticker = input_code

period = st.sidebar.selectbox("分析期間", ["3mo", "6mo", "1y"], index=0)

# 1. データ取得
@st.cache_data(ttl=300) # 5分間はデータを使い回して高速化
def get_data(t, p):
    s = yf.Ticker(t)
    return s.history(period=p), s.info

df, info = get_data(ticker, period)

if not df.empty:
    # --- テクニカル指標の計算 ---
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA25'] = df['Close'].rolling(window=25).mean()
    
    ma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    df['Upper'] = ma20 + (std20 * 2)
    df['Lower'] = ma20 - (std20 * 2)

    stock_name = info.get('longName', ticker)
    st.header(f"{stock_name} ({ticker})")

    # --- ダッシュボード ---
    c1, c2, c3, c4 = st.columns(4)
    last_p = df['Close'].iloc[-1]
    diff = last_p - df['Close'].iloc[-2]
    c1.metric("現在値", f"{last_p:.1f}", f"{diff:.1f}")
    c2.metric("RSI", f"{df['RSI'].iloc[-1]:.1f}")
    c3.metric("5日線比", f"{((last_p/df['MA5'].iloc[-1]-1)*100):.1f}%")
    c4.metric("出来高", f"{df['Volume'].iloc[-1]:,}")

    # --- テクニカル分析診断 ---
    st.subheader("🔍 テクニカル診断")
    t_col1, t_col2, t_col3 = st.columns(3)
    rsi_val = df['RSI'].iloc[-1]
    t_col1.info(f"**RSI**\n\n{'⚠️過熱' if rsi_val > 70 else '✅割安' if rsi_val < 30 else '🔄中立'}")
    t_col2.info(f"**トレンド**\n\n{'📈上昇' if df['MA5'].iloc[-1] > df['MA25'].iloc[-1] else '📉下落'}")
    t_col3.info(f"**ボリンジャー**\n\n{'🚨警戒' if last_p > df['Upper'].iloc[-1] else '📉底値' if last_p < df['Lower'].iloc[-1] else '安定'}")

    # --- プロフェッショナル・チャート (操作性改善) ---
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='株価'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='5日線', line=dict(color='blue', width=1)), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='orange')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # グラフの操作性UP（拡大・縮小しやすく）
    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=10, b=10),
        dragmode='pan', # デフォルトを「移動」にする
        hovermode='x unified'
    )
    # スマホでもダブルタップでリセットできるように
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'scrollZoom': True})

    # --- AI分析 (高速化版) ---
    st.write("---")
    if st.button("⚖️ 最速AI診断を実行"):
        with st.status("AIがデータを確認中...", expanded=True) as status:
            try:
                st.write("チャートパターンをスキャン...")
                prompt = f"{stock_name}終値{last_p},RSI{rsi_val:.1f}。明日を15文字で予言。"
                res = model.generate_content(prompt)
                status.update(label="診断完了！", state="complete", expanded=False)
                st.success(f"🔮 結論：{res.text}")
            except:
                st.error("エラー。少し待ってね。")
else:
    st.error("データなし。")
