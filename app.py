import streamlit as st
import pandas as pd
import yfinance as yf

st.title("📈 股票技術分析器 (純 pandas + yfinance)")

stock_id = st.text_input("請輸入股票代號 (例如 2330.TW):", "2330.TW")
start_date = st.date_input("開始日期", pd.to_datetime("2024-01-01"))
end_date = st.date_input("結束日期", pd.to_datetime("2024-12-31"))

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

if st.button("取得資料並分析"):
    try:
        df = yf.download(stock_id, start=start_date, end=end_date)

        if df.empty:
            st.error("查無資料，請確認股票代號或日期範圍。")
        else:
            df['MA20'] = df['Close'].rolling(20).mean()
            df['RSI'] = compute_rsi(df['Close'])
            df['MACD'], df['MACD_signal'], df['MACD_hist'] = compute_macd(df['Close'])

            st.subheader("📊 技術指標數據")
            st.dataframe(df[['Close', 'MA20', 'RSI', 'MACD', 'MACD_signal', 'MACD_hist']].tail(30))

            st.subheader("📈 股價與 MA20")
            st.line_chart(df[['Close', 'MA20']])

            st.subheader("📉 RSI 指標")
            st.line_chart(df[['RSI']])

            st.subheader("📉 MACD 指標")
            st.line_chart(df[['MACD', 'MACD_signal']])
    except Exception as e:
        st.error(f"發生錯誤: {e}")



