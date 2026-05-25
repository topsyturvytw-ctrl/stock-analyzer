import streamlit as st
import pandas as pd
import numpy as np
import talib
from FinMind.data import DataLoader

st.title("📈 股票技術分析器 (TA-Lib + FinMind)")

# 使用者輸入 FinMind API Token
api_token = st.text_input("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidG9wc3l0dXJ2eS50dyIsImVtYWlsIjoidG9wc3l0dXJ2eS50d0B5YWhvby5jb20udHciLCJ0b2tlbl92ZXJzaW9uIjowfQ.g8F7_b3ru58bFwW4JLe6JnD4IyV_0x5KFLFbG1j3Y8A", type="password")

# 使用者輸入股票代號
stock_id = st.text_input("請輸入股票代號 (例如 2330):", "2330")

# 選擇日期範圍
start_date = st.date_input("開始日期", pd.to_datetime("2024-01-01"))
end_date = st.date_input("結束日期", pd.to_datetime("2024-12-31"))

if st.button("取得資料並分析"):
    if not api_token:
        st.error("請先輸入 FinMind API Token")
    else:
        try:
            # 初始化 FinMind API
            api = DataLoader()
            api.login_by_token(api_token)

            # 抓取股價資料
            df = api.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=str(start_date),
                end_date=str(end_date)
            )

            if df.empty:
                st.error("查無資料，請確認股票代號或日期範圍。")
            else:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)

                # 計算技術指標
                df['MA20'] = talib.SMA(df['close'], timeperiod=20)
                df['RSI'] = talib.RSI(df['close'], timeperiod=14)
                macd, macd_signal, macd_hist = talib.MACD(df['close'])
                df['MACD'] = macd
                df['MACD_signal'] = macd_signal
                df['MACD_hist'] = macd_hist

                # 顯示表格
                st.subheader("📊 技術指標數據")
                st.dataframe(df[['close', 'MA20', 'RSI', 'MACD', 'MACD_signal', 'MACD_hist']].tail(30))

                # 畫圖
                st.subheader("📈 股價與 MA20")
                st.line_chart(df[['close', 'MA20']])

                st.subheader("📉 RSI 指標")
                st.line_chart(df[['RSI']])

                st.subheader("📉 MACD 指標")
                st.line_chart(df[['MACD', 'MACD_signal']])

        except Exception as e:
            st.error(f"發生錯誤: {e}")
