import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="健康語音助手開發中", layout="centered")
st.title("📊 數據倉庫連線測試")

# 顯示目前的連線檢查狀態
with st.expander("🔍 系統連線診斷", expanded=True):
    try:
        # 建立連線
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 測試讀取
        df = conn.read()
        st.success("✅ 成功連線至 Google Sheets！")
        st.write("目前倉庫內的資料筆數：", len(df))
    except Exception as e:
        st.error("❌ 連線失敗")
        st.info("請檢查 Streamlit Cloud 的 Secrets 設定是否完整。")
        st.code(str(e))

st.divider()

# 測試寫入功能
st.subheader("寫入測試")
if st.button("🚀 點我寫入一筆測試紀錄"):
    try:
        # 1. 讀取現有資料
        existing_data = conn.read()
        
        # 2. 準備測試數據
        test_entry = pd.DataFrame([{
            "Date": "2026-04-25",
            "Time": "00:30",
            "Systolic": 120,
            "Diastolic": 80,
            "Pulse": 70,
            "Context": "連線測試",
            "Notes": "GitHub 遠端寫入成功！"
        }])
        
        # 3. 合併並更新
        updated_df = pd.concat([existing_data, test_entry], ignore_index=True)
        conn.update(data=updated_df)
        
        st.balloons()
        st.success("🎉 太棒了！資料已成功寫入 Google Sheets。")
        st.info("現在去查看你的 Google 表格，應該會看到新的一行。")
    except Exception as e:
        st.error(f"寫入過程出錯：{e}")

# 預覽目前的數據
if st.checkbox("顯示目前倉庫數據"):
    st.dataframe(conn.read())
