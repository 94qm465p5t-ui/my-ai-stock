import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- ページ設定 ---
st.set_page_config(page_title="AI Live Strategist", layout="wide")

# 1分（60000ミリ秒）ごとに画面を自動更新する設定
st_autorefresh(interval=60000, key="datarefresh")

# 🔑 Geminiの設定
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("📡 AI Live Strategist (1分更新分析)")

# --- サイドバー ---
input_code = st.sidebar.text_input("監視銘柄 (4桁)", "7203")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code

# データ取得
df = yf.download(ticker, period="1d", interval="1m")

if not df.empty:
    # --- 指標計算 (MACD, RSI, VWAP) ---
    # VWAP
    v = df['Volume'].values
    p = (df['High'] + df['Low'] + df['Close']).values / 3
    df['VWAP'] = (p * v).cumsum() / v.cumsum()
    
    # MACD (12, 26, 9)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 最新値の取得
    last_p = df['Close'].iloc[-1]
    last_vwap = df['VWAP'].iloc[-1]
    last_macd = df['MACD'].iloc[-1]
    last_sig = df['Signal'].iloc[-1]
    vol_last = df['Volume'].iloc[-1]

    # --- メイン表示 ---
    st.subheader(f"📊 {ticker} リアルタイム状況")
    col1, col2, col3 = st.columns(3)
    col1.metric("現在値", f"{last_p:.1f}")
    col2.metric("VWAP乖離", f"{last_p - last_vwap:.1f}")
    col3.metric("MACDステータス", "ゴールデンクロス" if last_macd > last_sig else "デッドクロス")

    # --- AIへの指示 (プロンプトの超強化) ---
    # ここに「今の情勢」などのコンテキストを自動生成します
    prompt = f"""
    あなたは凄腕のデイトレーダーです。以下のリアルタイムデータを踏まえ、現状を実況・分析してください。
    
    【銘柄情報】 {ticker}
    【現在値】 {last_p}
    【VWAP】 {last_vwap:.1f} (これより上なら強気)
    【MACD】 値:{last_macd:.2f} / シグナル:{last_sig:.2f}
    【出来高】 直近1分間で {vol_last} 株の商い
    
    分析の型：
    「価格がVWAPの〇〇に位置し、MACDが〇〇を示唆している。出来高の推移は〇〇だ。したがって、今は〇〇すべきだ。」
    という形式で、30～50文字程度の鋭い考察を述べて。
    """

    # AI診断（自動で実行される）
    with st.container():
        st.write("---")
        st.markdown("### 🔮 AIのリアルタイム実況解説")
        try:
            res = model.generate_content(prompt)
            st.success(res.text)
        except:
            st.write("AI分析更新中...")

    # チャート表示
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='1分足'))
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name='VWAP', line=dict(color='yellow', dash='dot')))
    fig.update_layout(height=400, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("市場稼働時間外、またはデータ取得エラーです。")