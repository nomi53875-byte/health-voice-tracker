import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json

st.set_page_config(page_title="健康語音助手開發中", layout="centered")
st.title("📊 數據倉庫連線診斷")

try:
    # 從 Secrets 讀取原始 JSON 字串並轉換為字典
    conf = json.loads(st.secrets["connections"]["gsheets"]["json_key"])
    
    # 建立連線
    conn = st.connection("gsheets", type=GSheetsConnection, **conf)
    
    st.success("✅ 系統偵測到金鑰格式正確！")
    
    if st.button("🚀 測試寫入一筆資料"):
        existing_data = conn.read()
        test_entry = pd.DataFrame([{
            "Date": "2026-04-25",
            "Time": "01:40",
            "Systolic": 120, "Diastolic": 80, "Pulse": 70,
            "Context": "最終方案測試", "Notes": "JSON 直接解析成功"
        }])
        updated_df = pd.concat([existing_data, test_entry], ignore_index=True)
        conn.update(data=updated_df)
        st.balloons()
        st.success("成功寫入！請檢查 Google Sheets。")

except Exception as e:
    st.error("❌ 連線診斷失敗")
    st.code(f"錯誤類型: {type(e).__name__}")
    st.code(f"詳細訊息: {str(e)}")

if st.checkbox("顯示目前數據預覽"):
    try:
        st.dataframe(conn.read())
    except:
        st.warning("尚無數據或無法讀取")
