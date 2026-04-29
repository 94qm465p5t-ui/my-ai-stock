import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 1. 自動更新設定
st.set_page_config(page_title="AI Strategist", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

# 2. API設定（スペルミスがあっても動くように補強）
def init_ai():
    # GEMINI_API_KEY または GEMIN_API_KEY のどちらかがあれば読み込む
    key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GEMIN_API_KEY")
    if not key: return None
    try:
        clean_key = str(key).strip().strip('"').strip("'")
        genai.configure(api_key=clean_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except: return None

model = init_ai()
st.title("📡 AI Live Strategist")

# 3. サイドバー
input_code = st.sidebar.text_input("銘柄コード", "BTC-USD")
mode = st.sidebar.radio("モード選択", ["テスト(仮想データ)", "本番データ"])

# 4. データ取得（エラー対策版）
def load_data():
    if mode == "テスト(仮想データ)":
        idx = pd.date_range(pd.Timestamp.now(), periods=100, freq='1min')
        return pd.DataFrame({'Open': np.random.randn(100).cumsum()+100, 'High': np.random.randn(100).cumsum()+102, 'Low': np.random.randn(100).cumsum()+98, 'Close': np.random.randn(100).cumsum()+100, 'Volume': np.random.randint(100,1000,100)}, index=idx)
    else:
        try:
            d = yf.download(input_code, period="1d", interval="1m", progress=False, auto_adjust=True)
            if d is None or d.empty: return pd.DataFrame()
            if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
            return d
        except: return pd.DataFrame()

df = load_data()

# 5. 解析と表示
if not df.empty and len(df) > 1:
    # VWAP計算 (ゼロ除算防止)
    vol = df['Volume'].replace(0, 1)
    df['VWAP'] = ((df['High'] + df['Low'] + df['Close']) / 3 * vol).cumsum() / vol.cumsum()
    last_p = float(df['Close'].iloc[-1])
    
    # AI実況セクション
    if model:
        try:
            res = model.generate_content(f"{input_code}が現在{last_p:.1f}です。デイトレの助言を30字以内で。")
            st.success(f"🔮 AI分析: {res.text}")
        except: st.warning("AIが思考を整理中です...")
    else:
        st.info("Secretsの設定を完了するとAIが喋り出します。")
    
    # チャート表示
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow')))
    fig.update_layout(height=450, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("現在データを取得できません。左側で『テスト(仮想データ)』に切り替えてください。")
    import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 1. 自動更新設定
st.set_page_config(page_title="AI Strategist", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

# 2. API設定（スペルミスがあっても動くように補強）
def init_ai():
    # GEMINI_API_KEY または GEMIN_API_KEY のどちらかがあれば読み込む
    key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GEMIN_API_KEY")
    if not key: return None
    try:
        clean_key = str(key).strip().strip('"').strip("'")
        genai.configure(api_key=clean_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except: return None

model = init_ai()
st.title("📡 AI Live Strategist")

# 3. サイドバー
input_code = st.sidebar.text_input("銘柄コード", "BTC-USD")
mode = st.sidebar.radio("モード選択", ["テスト(仮想データ)", "本番データ"])

# 4. データ取得（エラー対策版）
def load_data():
    if mode == "テスト(仮想データ)":
        idx = pd.date_range(pd.Timestamp.now(), periods=100, freq='1min')
        return pd.DataFrame({'Open': np.random.randn(100).cumsum()+100, 'High': np.random.randn(100).cumsum()+102, 'Low': np.random.randn(100).cumsum()+98, 'Close': np.random.randn(100).cumsum()+100, 'Volume': np.random.randint(100,1000,100)}, index=idx)
    else:
        try:
            d = yf.download(input_code, period="1d", interval="1m", progress=False, auto_adjust=True)
            if d is None or d.empty: return pd.DataFrame()
            if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
            return d
        except: return pd.DataFrame()

df = load_data()

# 5. 解析と表示
if not df.empty and len(df) > 1:
    # VWAP計算 (ゼロ除算防止)
    vol = df['Volume'].replace(0, 1)
    df['VWAP'] = ((df['High'] + df['Low'] + df['Close']) / 3 * vol).cumsum() / vol.cumsum()
    last_p = float(df['Close'].iloc[-1])
    
    # AI実況セクション
    if model:
        try:
            res = model.generate_content(f"{input_code}が現在{last_p:.1f}です。デイトレの助言を30字以内で。")
            st.success(f"🔮 AI分析: {res.text}")
        except: st.warning("AIが思考を整理中です...")
    else:
        st.info("Secretsの設定を完了するとAIが喋り出します。")
    
    # チャート表示
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='yellow')))
    fig.update_layout(height=450, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("現在データを取得できません。左側で『テスト(仮想データ)』に切り替えてください。")
