import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json

st.title("📊 數據倉庫狀態")

def get_connection():
    # 讀取 Secrets 裡的原始 JSON
    raw_json = st.secrets["connections"]["gsheets"]["json_key"]
    info = json.loads(raw_json)
    
    # 核心修正：強制將 JSON 裡的 \n 轉義字元轉成真正的換行符號
    # 這是解決 Unable to load PEM file 的特效藥
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    return st.connection("gsheets", type=GSheetsConnection, **info)

try:
    conn = get_connection()
    df = conn.read()
    st.success("✅ 雲端倉庫連線成功！")
    
    if st.button("🚀 寫入測試數據"):
        test_entry = pd.DataFrame([{
            "Date": "2026-04-25", "Time": "02:10",
            "Systolic": 120, "Diastolic": 80, "Pulse": 70,
            "Context": "JSON轉義測試", "Notes": "這招一定通"
        }])
        updated_df = pd.concat([df, test_entry], ignore_index=True)
        conn.update(data=updated_df)
        st.balloons()
        st.success("寫入成功！")

except Exception as e:
    st.error("❌ 連線仍有問題")
    st.exception(e)
