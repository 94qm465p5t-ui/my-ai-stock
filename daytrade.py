import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ページ設定
st.set_page_config(page_title="AI Live Strategist", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

# API設定
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("APIキーを設定してください")
    st.stop()

st.title("📡 AI Live Strategist")

# サイドバー
input_code = st.sidebar.text_input("監視銘柄コード", "BTC-USD")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code
mode = st.sidebar.radio("モード選択", ["本番データ", "テスト(仮想データ)"])

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
        # auto_adjustをTrueにして、マルチインデックスを防ぐ
        return yf.download(t, period="1d", interval="1m", progress=False, auto_adjust=True)

df = get_data(ticker, mode)

# --- データ解析 ---
if not df.empty and len(df) > 0:
    try:
        # マルチインデックス対策: 列名を単純化
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 指標計算
        v = df['Volume']
        p = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (p * v).cumsum() / v.cumsum()
        
        # 値の抽出（.item()を使用して確実にスカラー値を取得）
        last_p = float(df['Close'].iloc[-1])
        last_vwap = float(df['VWAP'].iloc[-1])

        st.subheader(f"📊 {ticker} 分析結果")
        
        # AI診断
        try:
            prompt = f"銘柄{ticker}, 価格{last_p:.1f}, VWAP{last_vwap:.1f}。今の戦略を「～だから～だ」で30字以内で語れ。"
            res = model.generate_content(prompt)
            st.success(f"**AI実況: {res.text}**")
        except:
            st.write("AI分析中...")

        # チャート
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格"
        )])
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow')))
        fig.update_layout(height=450, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"データ処理エラーが発生しました。サイドバーで『テストモード』を試してください。")
        # st.write(e) # デバッグが必要な場合はコメントを外す
else:
    st.warning("データが取得できません。市場が開いているか、銘柄コードを確認してください。")
