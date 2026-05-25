import streamlit as st
import pandas as pd
import yfinance as yf

st.title("📈 股票技術分析器 (含進出場判斷 + 本益比河流)")

# 使用者輸入
stock_id = st.text_input("請輸入股票代號 (例如 2330.TW):", "2330.TW")
start_date = st.date_input("開始日期", pd.to_datetime("2026-01-01"))
end_date = st.date_input("結束日期", pd.to_datetime("2026-05-25"))

# 技術指標計算
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

# 本益比河流計算
def pe_river(price, eps, pe_ratios=[10,15,20,25]):
    fair_values = {f"PE{pe}": eps * pe for pe in pe_ratios}
    return fair_values

if st.button("取得資料並分析"):
    try:
        df = yf.download(stock_id, start=start_date, end=end_date)

        # 展平 MultiIndex 欄位
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [' '.join(col).strip() for col in df.columns.values]

        if df.empty:
            st.error("查無資料，請確認股票代號或日期範圍。")
        else:
            df['MA20'] = df['Close'].rolling(20).mean()
            df['RSI'] = compute_rsi(df['Close'])
            df['MACD'], df['MACD_signal'], df['MACD_hist'] = compute_macd(df['Close'])

            # 進出場判斷
            latest = df.iloc[-1]
            signals = []
            if latest['Close'] > latest['MA20']:
                signals.append("股價在 MA20 之上 → 偏多")
            else:
                signals.append("股價在 MA20 之下 → 偏空")

            if latest['RSI'] > 70:
                signals.append("RSI > 70 → 超買，可能回檔")
            elif latest['RSI'] < 30:
                signals.append("RSI < 30 → 超賣，可能反彈")

            if latest['MACD'] > latest['MACD_signal']:
                signals.append("MACD > Signal → 偏多")
            else:
                signals.append("MACD < Signal → 偏空")

            st.subheader("📊 技術指標數據")
            st.dataframe(df[['Close','MA20','RSI','MACD','MACD_signal','MACD_hist']].tail(30))

            st.subheader("📈 股價與 MA20")
            st.line_chart(df[['Close','MA20']])

            st.subheader("📉 RSI 指標")
            st.line_chart(df[['RSI']])

            st.subheader("📉 MACD 指標")
            st.line_chart(df[['MACD','MACD_signal']])

            st.subheader("📌 進出場判斷")
            for s in signals:
                st.write("- " + s)

            # 自動抓 EPS
            ticker = yf.Ticker(stock_id)
            eps_data = ticker.financials.loc['Net Income'] / ticker.financials.loc['Shares Outstanding']
            if not eps_data.empty:
                eps = eps_data.iloc[-1]  # 最近一期 EPS
            else:
                eps = 10  # fallback 假設值

            fair_values = pe_river(latest['Close'], eps)
            st.subheader("💰 本益比河流合理股價")
            st.write(f"最近 EPS: {eps:.2f}")
            for k,v in fair_values.items():
                st.write(f"{k}: {v:.2f}")

    except Exception as e:
        st.error(f"發生錯誤: {e}")
