import streamlit as st
import pandas as pd
import pandas_ta as ta
from FinMind.data import DataLoader

# ========================================================
# 🌟 請在下方貼上你在 FinMind 官網申請的免費 API Token 🌟
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidG9wc3l0dXJ2eS50dyIsImVtYWlsIjoidG9wc3l0dXJ2eS50d0B5YWhvby5jb20udHciLCJ0b2tlbl92ZXJzaW9uIjowfQ.g8F7_b3ru58bFwW4JLe6JnD4IyV_0x5KFLFbG1j3Y8A"
# ========================================================

st.set_page_config(page_title="台股綜合分析器", layout="wide")

st.title("📊 台股綜合分析器 - Web 版")

stock_code = st.text_input("請輸入股票代號", "1789")

if st.button("執行全面技術與估值分析"):
    if not stock_code.strip():
        st.warning("請先輸入股票代號！")
    elif FINMIND_TOKEN == "你的_FINMIND_TOKEN":
        st.error("請先填入您的 FinMind API Token！")
    else:
        try:
            api = DataLoader()
            api.login_by_token(api_token=FINMIND_TOKEN)

            # 技術面分析
            start_dt_tech = (pd.Timestamp.now() - pd.Timedelta(days=120)).strftime('%Y-%m-%d')
            end_dt_tech = pd.Timestamp.now().strftime('%Y-%m-%d')

            df_daily = api.taiwan_stock_daily(stock_id=stock_code, start_date=start_dt_tech, end_date=end_dt_tech)
            if df_daily.empty:
                st.error("找不到該股票的技術面股價資料")
            else:
                df_daily = df_daily.sort_values('date').reset_index(drop=True)
                df_daily['MA5'] = df_daily['close'].rolling(window=5).mean()
                df_daily['MA20'] = df_daily['close'].rolling(window=20).mean()
                df_daily['RSI14'] = ta.rsi(df_daily['close'], length=14)

                kd_df = ta.stoch(high=df_daily['max'], low=df_daily['min'], close=df_daily['close'], k=9, d=3, smooth_k=3)
                df_daily['K'] = kd_df['STOCHk_9_3_3']
                df_daily['D'] = kd_df['STOCHd_9_3_3']

                today = df_daily.iloc[-1]
                yesterday = df_daily.iloc[-2]

                st.subheader("📈 技術面分析")
                st.write(f"今日收盤價: {today['close']} 元")
                st.write(f"5MA: {today['MA5']:.1f} / 20MA: {today['MA20']:.1f}")
                st.write(f"K={today['K']:.1f}, D={today['D']:.1f}, RSI={today['RSI14']:.1f}")

            # 基本面河流分析
            start_dt_river = f"{pd.Timestamp.now().year-3}-01-01"
            df_river = api.taiwan_stock_daily(stock_id=stock_code, start_date=start_dt_river, end_date=end_dt_tech)
            df_financial = api.taiwan_stock_financial_statement(stock_id=stock_code, start_date=start_dt_river)

            if df_river.empty or df_financial.empty:
                st.error("找不到該股票的財報或股價資料")
            else:
                type_col = 'type' if 'type' in df_financial.columns else 'Type'
                val_col = 'value' if 'value' in df_financial.columns else 'Value'
                df_eps_raw = df_financial[df_financial[type_col].str.contains('EPS', case=False, na=False)].copy()
                df_eps_raw['date'] = pd.to_datetime(df_eps_raw['date'])
                df_eps_raw = df_eps_raw.sort_values('date').reset_index(drop=True)

                eps_timeline = []
                for i in range(len(df_eps_raw)):
                    if i >= 3:
                        eps_timeline.append({'date': df_eps_raw['date'].iloc[i], 'rolling_eps': df_eps_raw[val_col].iloc[i-3:i+1].sum()})
                df_eps_rolling = pd.DataFrame(eps_timeline)

                df_river['date'] = pd.to_datetime(df_river['date'])
                df_merge = pd.merge_asof(df_river, df_eps_rolling, on='date', direction='backward')
                df_merge['PE'] = df_merge['close'] / df_merge['rolling_eps']
                df_clean_pe = df_merge[(df_merge['PE'] > 2) & (df_merge['PE'] < 60)]['PE']

                pe_low, pe_mid, pe_high = df_clean_pe.quantile(0.15), df_clean_pe.quantile(0.50), df_clean_pe.quantile(0.85)
                eps_4q = df_eps_rolling.iloc[-1]['rolling_eps']

                st.subheader("🏠 財報估值分析")
                st.write(f"近四季累積 EPS：{eps_4q:.2f} 元")
                st.write(f"本益比區間：便宜 {pe_low:.1f} / 合理 {pe_mid:.1f} / 昂貴 {pe_high:.1f}")
                st.write(f"河流估值：便宜 {eps_4q*pe_low:.1f} 元 / 合理 {eps_4q*pe_mid:.1f} 元 / 昂貴 {eps_4q*pe_high:.1f} 元")

        except Exception as e:
            st.error(f"系統發生錯誤: {str(e)}")
