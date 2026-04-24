import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.title("📊 數據倉庫狀態 (官方直連穩定版)")

def get_gspread_client():
    s = st.secrets["connections"]["gsheets"]
    
    # 直接使用 Secrets 內容，不再做任何字串替換
    info = {
        "type": s["type"],
        "project_id": s["project_id"],
        "private_key_id": s["private_key_id"],
        "private_key": s["private_key"],
        "client_email": s["client_email"],
        "client_id": s["client_id"],
        "auth_uri": s["auth_uri"],
        "token_uri": s["token_uri"],
        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
        "client_x509_cert_url": s["client_x509_cert_url"]
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    sh = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    worksheet = sh.get_worksheet(0)
    data = worksheet.get_all_records()
    
    st.success("✅ 終於連線成功了！")
    st.write(f"目前紀錄筆數：{len(data)}")
    if data:
        st.dataframe(pd.DataFrame(data).tail(3))
    
    if st.button("🚀 寫入測試"):
        worksheet.append_row(["2026-04-25", "04:00", 120, 80, 70, "三引號測試", "物理換行成功"])
        st.balloons()
        st.rerun()

except Exception as e:
    st.error("❌ 連線失敗")
    st.exception(e)
