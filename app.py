import streamlit as st
import google.generativeai as genai
import yfinance as yf
import time

# 🔑 Geminiの設定
# あとでStreamlitの設定画面に貼り付ける名前と一致させる必要があります
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("📈 AI株価アナリスト")

# サイドバーで銘柄を変えられるようにする
ticker = st.sidebar.text_input("銘柄コード (例: 285A.T)", "285A.T")

placeholder = st.empty()

while True:
    with placeholder.container():
        # 株価データを取得（yfinanceを使用）
        data = yf.Ticker(ticker).history(period="1d", interval="1m")
        
        if not data.empty:
            now_price = data['Close'].iloc[-1]
            st.metric("現在の価格", f"{now_price} 円")
            
            # AIに分析を頼む（エラーが起きても止まらないように対策済み）
            try:
                prompt = f"銘柄{ticker}の現在価格は{now_price}円。これからの動きをプロっぽく15文字で予測して。"
                res = model.generate_content(prompt)
                st.info(f"🤖 AIの分析：{res.text}")
            except:
                st.warning("AIが考え中です...")
                
            st.line_chart(data['Close'])
        else:
            st.error("データが取れません。市場が閉まっているか、コードが間違っています。")
            
    time.sleep(60) # 1分待つ
    st.rerun()