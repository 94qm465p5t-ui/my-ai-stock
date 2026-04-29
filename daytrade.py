import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ構成と自動更新 ---
st.set_page_config(page_title="AI Live Strategist", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

# --- 2. APIキーの「超」クリーンアップ設定 ---
def get_model():
    if "GEMINI_API_KEY" not in st.secrets:
        return None
    try:
        # 改行、空白、引用符をすべて剥ぎ取る
        raw_key = str(st.secrets["GEMINI_API_KEY"])
        clean_key = raw_key.strip().strip('"').strip("'").replace("\n", "").replace("\r", "")
        genai.configure(api_key=clean_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = get_model()

st.title("📡 AI Live Strategist (究極完成版)")

# --- 3. サイドバー ---
input_code = st.sidebar.text_input("銘柄コード (例: BTC-USD)", "BTC-USD")
ticker = f"{input_code}.T" if input_code.isdigit() else input_code
mode = st.sidebar.radio("データ切替", ["本番データ", "テスト(仮想データ)"])

# --- 4. データ取得 (最新仕様対応) ---
def fetch_data(t, m):
    if m == "テスト(仮想データ)":
        dates = pd.date_range(pd.Timestamp.now(), periods=100, freq='1min')
        return pd.DataFrame({
            'Open': np.random.randn(100).cumsum() + 100,
            'High': np.random.randn(100).cumsum() + 102,
            'Low': np.random.randn(100).cumsum() + 98,
            'Close': np.random.randn(100).cumsum() + 100,
            'Volume': np.random.randint(100, 1000, 100)
        }, index=dates)
    else:
        try:
            data = yf.download(t, period="1d", interval="1m", progress=False, auto_adjust=True)
            if data.empty: return pd.DataFrame()
            # 2段構えのカラム名を1段に平坦化
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            return data
        except:
            return pd.DataFrame()

df = fetch_data(ticker, mode)

# --- 5. 解析と表示 ---
if not df.empty and len(df) > 1:
    # VWAP計算
    v, h, l, c = df['Volume'], df['High'], df['Low'], df['Close']
    df['VWAP'] = ((h + l + c) / 3 * v).cumsum() / v.cumsum()
    
    # 確実に単一の数値として抽出
    last_p = float(c.iloc[-1])
    last_vwap = float(df['VWAP'].iloc[-1])

    # AI診断セクション
    with st.expander("🔮 AI軍師の戦略分析", expanded=True):
        if model:
            try:
                diff = "上振れ" if last_p > last_vwap else "下振れ"
                prompt = f"銘柄:{ticker}, 価格:{last_p:.1f}, VWAP:{last_vwap:.1f}。現在{diff}中。プロの助言を30字以内で。語尾は『だ』。"
                res = model.generate_content(prompt)
                st.success(f"**AI: {res.text}**")
            except:
                st.error("AI通信エラー。Secretsのキー設定が依然として不正な可能性があります。")
        else:
            st.info("APIキーを設定してください。")

    # チャート表示
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="価格")])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow', width=1.5)))
    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("データが取得できません。市場時間外か、Yahoo Financeの制限中です。")
    st.info("サイドバーで『テスト(仮想データ)』に切り替えてみてください。")
