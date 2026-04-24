import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="健康語音助手", layout="centered")
st.title("📊 數據倉庫狀態")

try:
    # 建立標準連線
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
    st.success("✅ 雲端倉庫連線成功！")
    
    st.write(f"目前紀錄筆數：{len(df)}")
    
    if st.button("🚀 寫入測試數據"):
        test_entry = pd.DataFrame([{
            "Date": "2026-04-25", "Time": "01:50",
            "Systolic": 120, "Diastolic": 80, "Pulse": 70,
            "Context": "TOML格式測試", "Notes": "連線終於通了！"
        }])
        updated_df = pd.concat([df, test_entry], ignore_index=True)
        conn.update(data=updated_df)
        st.balloons()
        st.success("寫入成功！")

except Exception as e:
    st.error("❌ 連線仍有問題")
    st.exception(e) # 這會顯示完整的錯誤追蹤，非常有助於除錯
