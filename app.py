import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="健康語音助手", layout="centered")
st.title("📊 數據倉庫狀態")

def get_conn():
    # 1. 從 Secrets 抓取原始資料
    s = st.secrets["connections"]["gsheets"]
    
    # 2. 拼湊成 Google 標準的 service_account 格式
    # 這裡我們手動修正那個討厭的 \n
    service_account_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key_id": s["private_key_id"],
        "private_key": s["private_key"].replace("\\n", "\n"),
        "client_email": s["client_email"],
        "client_id": s["client_id"],
        "auth_uri": s["auth_uri"],
        "token_uri": s["token_uri"],
        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
        "client_x509_cert_url": s["client_x509_cert_url"]
    }
    
    # 3. 使用關鍵字參數傳遞這一整包資訊
    return st.connection("gsheets", type=GSheetsConnection, service_account_info=service_account_info)

try:
    conn = get_conn()
    # 嘗試讀取
    df = conn.read()
    st.success("✅ 雲端倉庫連線成功！")
    
    st.write(f"目前紀錄筆數：{len(df)}")
    
    if st.button("🚀 寫入測試數據"):
        test_entry = pd.DataFrame([{
            "Date": "2026-04-25", "Time": "02:50",
            "Systolic": 120, "Diastolic": 80, "Pulse": 70,
            "Context": "最終修正測試", "Notes": "這下總該通了吧！"
        }])
        # 確保連線物件可以寫入
        conn.update(data=pd.concat([df, test_entry], ignore_index=True))
        st.balloons()
        st.success("寫入成功！")

except Exception as e:
    st.error("❌ 連線仍有問題")
    st.exception(e)
