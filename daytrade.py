import google.generativeai as genai
import yfinance as yf
import time

# --- 設定エリア ---
API_KEY = "あなたのGEMINI_API_KEY"
TICKER_SYMBOL = "285A.T"  # キオクシア (東証) ※ここを自由に変更可能
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_stock_analysis(symbol):
    # 1. 株価データの取得
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d", interval="1m").tail(1)
    
    if data.empty:
        return "データが取得できませんでした。市場が閉まっている可能性があります。"

    current_price = data['Close'].iloc[0]
    volume = data['Volume'].iloc[0]

    # 2. Geminiへのプロンプト作成
    prompt = f"""
    銘柄: {symbol}
    現在価格: {current_price}円
    直近の出来高: {volume}
    
    上記のデータを元に、プロのトレーダーの視点で、今後1分間の値動きに対する
    超短期的な分析を30文字程度で述べてください。
    """

    # 3. 分析の実行
    response = model.generate_content(prompt)
    return f"【{symbol} 1分足分析】\n価格: {current_price}円\n分析: {response.text}"

# --- 実行ループ ---
print(f"{TICKER_SYMBOL} の1分間分析を開始します...")
while True:
    try:
        result = get_stock_analysis(TICKER_SYMBOL)
        print(result)
        print("-" * 30)
        time.sleep(60) # 60秒待機
    except Exception as e:
        print(f"エラー発生: {e}")
        time.sleep(10)
