import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ・自動更新設定 ---
st.set_page_config(page_title="AI Live Strategist", layout="wide")
# 60秒ごとに自動リフレッシュ
st_autorefresh(interval=60000, key="datarefresh")

# --- 2. Gemini APIの設定 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("APIキーが設定されていません。Secretsを確認してください。")
    st.stop()

st.title("📡 AI Live Strategist (1分更新分析)")

# --- 3. サイドバー設定 ---
input_code = st.sidebar.text_input("監視銘柄コード (4桁)", "7203")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code

# データ取得（デイトレ用1分足）
df = yf.download(ticker, period="1d", interval="1m")

# --- 4. データが存在する場合の処理 ---
if not df.empty and len(df) > 0:
    try:
        # 指標計算: VWAP
        v = df['Volume'].values
        p = (df['High'] + df['Low'] + df['Close']).values / 3
        df['VWAP'] = (p * v).cumsum() / v.cumsum()
        
        # 指標計算: MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # 指標計算: RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))

        # 最新データの抽出（型変換でエラーを防止）
        last_p = float(df['Close'].iloc[-1])
        last_vwap = float(df['VWAP'].iloc[-1])
        last_macd = float(df['MACD'].iloc[-1])
        last_sig = float(df['Signal'].iloc[-1])
        last_rsi = float(df['RSI'].iloc[-1])
        vol_last = int(df['Volume'].iloc[-1])

        # --- 5. メイン表示 ---
        st.subheader(f"📊 {ticker} リアルタイム状況")
        c1, c2, c3 = st.columns(3)
        c1.metric("現在値", f"{last_p:.1f}")
        c2.metric("VWAP乖離", f"{last_p - last_vwap:.1f}")
        status = "買い優勢" if last_macd > last_sig else "売り優勢"
        c3.metric("MACD診断", status)

        # --- 6. AI実況セクション ---
        st.write("---")
        st.markdown("### 🔮 AIストラテジストの実況解説")
        
        prompt = f"""
        あなたはプロのデイトレーダーです。以下のデータを踏まえ、現状を実況・分析してください。
        銘柄:{ticker}, 現在値:{last_p}, VWAP:{last_vwap:.1f}, MACD:{last_macd:.2f}, RSI:{last_rsi:.1f}
        
        「価格がVWAPの〇〇にあり、MACDとRSIから〇〇と判断できる。だから、今は〇〇すべきだ」
        という形式で、論理的な日本語で40文字程度で答えて。
        """

        with st.container(border=True):
            try:
                res = model.generate_content(prompt)
                st.success(f"**{res.text}**")
                st.caption(f"最終更新：{pd.Timestamp.now(tz='Asia/Tokyo').strftime('%H:%M:%S')}")
            except:
                st.write("AI分析を更新中...")

        # --- 7. チャート表示 ---
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='1分足'))
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name='VWAP', line=dict(color='yellow', width=2, dash='dot')))
        fig.update_layout(height=450, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"データ処理中にエラーが発生しました。市場が開くまでお待ちください。")
        # st.write(e) # デバッグ用
else:
    st.info("💡 現在、有効なリアルタイムデータが取得できません。市場稼働時間（平日9:00〜15:00）に自動的に開始されます。")
    st.image("https://images.unsplash.com/photo-1611974717483-5828d1dd0fb8?auto=format&fit=crop&q=80&w=1000", caption="Waiting for market open...")
