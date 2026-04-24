import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="健康語音助手", layout="centered")
st.title("📊 數據倉庫狀態 (最終驗證版)")

def get_gspread_client():
    s = st.secrets["connections"]["gsheets"]
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
    
    # 直接使用你的試算表唯一 ID
    sheet_id = "1SUnTdHJFPFbo2pr8dnAib3tTSrCCSygBcp4eAOxWz4g"
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)
    
    records = worksheet.get_all_records()
    
    st.success("✅ 權限驗證通過！地基已打好。")
    if records:
        st.dataframe(pd.DataFrame(records).tail(5))
    else:
        st.info("連線成功，目前表格為空（僅顯示標題欄）。")

    if st.button("🚀 測試寫入一筆資料"):
        # 依照你的欄位順序寫入：日期, 時間, 收縮壓, 舒張壓, 心跳, 情境, 備註
        worksheet.append_row(["2026-04-25", "05:05", 120, 80, 70, "系統測試", "權限終於開通了"])
        st.balloons()
        st.success("寫入成功！")
        st.rerun()

except Exception as e:
    st.error("❌ 存取被拒絕 (Permission Denied)")
    st.info(f"請確保已在 Google Sheets 中將此帳號設為編輯者：\n{st.secrets['connections']['gsheets']['client_email']}")
    st.exception(e)
