import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- ページ設定 ---
st.set_page_config(page_title="Professional Stock Analyzer", layout="wide")

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
stock = yf.Ticker(ticker)
df = stock.history(period=period)

if not df.empty:
    # --- テクニカル指標の計算 ---
    # 1. RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    # 2. 移動平均線 (5日 / 25日)
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA25'] = df['Close'].rolling(window=25).mean()
    
    # 3. ボリンジャーバンド (20日)
    ma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    df['Upper'] = ma20 + (std20 * 2)
    df['Lower'] = ma20 - (std20 * 2)

    # 銘柄名表示
    stock_name = stock.info.get('longName', ticker)
    st.header(f"{stock_name} ({ticker})")

    # --- ダッシュボード (主要数値) ---
    c1, c2, c3, c4 = st.columns(4)
    last_p = df['Close'].iloc[-1]
    diff = last_p - df['Close'].iloc[-2]
    c1.metric("現在値", f"{last_p:.1f}", f"{diff:.1f}")
    c2.metric("RSI", f"{df['RSI'].iloc[-1]:.1f}")
    c3.metric("5日移動平均", f"{df['MA5'].iloc[-1]:.1f}")
    c4.metric("出来高", f"{df['Volume'].iloc[-1]:,}")

    # --- 【新機能】テクニカル分析サマリー ---
    st.subheader("🔍 テクニカル分析診断")
    t_col1, t_col2, t_col3 = st.columns(3)
    
    # RSI判定
    rsi_val = df['RSI'].iloc[-1]
    if rsi_val > 70: rsi_status = "⚠️ 買われすぎ"
    elif rsi_val < 30: rsi_status = "✅ 売られすぎ (反発期待)"
    else: rsi_status = "🔄 中立"
    t_col1.info(f"**RSI判断**\n\n{rsi_status}")

    # 移動平均判定
    ma5, ma25 = df['MA5'].iloc[-1], df['MA25'].iloc[-1]
    if ma5 > ma25: ma_status = "📈 上昇トレンド"
    else: ma_status = "📉 下落トレンド"
    t_col2.info(f"**トレンド判断**\n\n{ma_status}")

    # ボリンジャーバンド判定
    upper, lower = df['Upper'].iloc[-1], df['Lower'].iloc[-1]
    if last_p > upper: bb_status = "🚨 過熱気味 (上限突破)"
    elif last_p < lower: bb_status = "📉 下げすぎ (下限突破)"
    else: bb_status = "安定"
    t_col3.info(f"**ボリンジャー判断**\n\n{bb_status}")

    # --- プロフェッショナル・チャート ---
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # メインチャート (ローソク足 + ボリンジャーバンド + 移動平均)
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='株価'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='5日線', line=dict(color='blue', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], name='BB上限', line=dict(color='rgba(255,0,0,0.2)', dash='dot')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], name='BB下限', line=dict(color='rgba(0,255,0,0.2)', dash='dot')), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='orange')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(height=800, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # --- AI分析 ---
    st.write("---")
    if st.button("⚖️ AIテクニカル総合診断を実行"):
        with st.spinner("AIストラテジストが計算中..."):
            try:
                prompt = f"""
                銘柄:{stock_name}
                価格:{last_p}, RSI:{rsi_val:.1f}, MA5:{ma5:.1f}, MA25:{ma25:.1f}
                直近終値推移:{df['Close'].tail(5).tolist()}
                
                これら全てのテクニカル指標を統合し、プロの視点で明日の戦略を15文字以内で断定して。
                """
                res = model.generate_content(prompt)
                st.success(f"🔮 AI予測：{res.text}")
            except:
                st.error("AI分析エラー。")
else:
    st.error("データがありません。")
