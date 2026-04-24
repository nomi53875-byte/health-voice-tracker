import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("📊 數據倉庫狀態")

# 建立一個處理 Secrets 格式的函式
def get_conn():
    # 取得 Secrets
    s = st.secrets["connections"]["gsheets"]
    
    # 建構連線資訊字典
    conn_info = {
        "type": s["type"],
        "project_id": s["project_id"],
        "private_key_id": s["private_key_id"],
        "private_key": s["private_key"].replace("\\n", "\n"), # 核心修正：強制轉換換行符號
        "client_email": s["client_email"],
        "client_id": s["client_id"],
        "auth_uri": s["auth_uri"],
        "token_uri": s["token_uri"],
        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
        "client_x509_cert_url": s["client_x509_cert_url"]
    }
    
    return st.connection("gsheets", type=GSheetsConnection, **conn_info)

try:
    conn = get_conn()
    df = conn.read()
    st.success("✅ 雲端倉庫連線成功！")
    
    if st.button("🚀 寫入測試數據"):
        test_entry = pd.DataFrame([{
            "Date": "2026-04-25", "Time": "02:30",
            "Systolic": 120, "Diastolic": 80, "Pulse": 70,
            "Context": "拆解格式測試", "Notes": "這次絕對會通"
        }])
        updated_df = pd.concat([df, test_entry], ignore_index=True)
        conn.update(data=updated_df)
        st.balloons()
        st.success("寫入成功！")

except Exception as e:
    st.error("❌ 連線仍有問題")
    st.exception(e)
