import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="健康語音助手", layout="centered")
st.title("📊 數據倉庫狀態 (官方直連)")

def get_gspread_client():
    # 1. 抓取 Secrets
    s = st.secrets["connections"]["gsheets"]
    
    # 2. 拼湊成標準 Google 認證格式，並手動修復換行
    info = {
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
    
    # 3. 定義權限範圍 (讀取 + 寫入)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 4. 建立認證
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

try:
    # 執行連線
    client = get_gspread_client()
    # 開啟試算表 (透過 Secrets 裡的網址)
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    sh = client.open_by_url(sheet_url)
    worksheet = sh.get_worksheet(0) # 讀取第一個分頁
    
    # 讀取現有資料轉為 DataFrame
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    st.success("✅ 官方驅動連線成功！")
    st.write(f"目前紀錄筆數：{len(df)}")
    st.dataframe(df.tail(3))
    
    if st.button("🚀 寫入測試數據"):
        # 準備新資料列
        new_row = ["2026-04-25", "03:40", 120, 80, 70, "官方直連測試", "格式不再是問題"]
        worksheet.append_row(new_row)
        st.balloons()
        st.success("寫入成功！請檢查 Google Sheets。")
        st.rerun() # 重新整理頁面顯示新資料

except Exception as e:
    st.error("❌ 連線失敗")
    st.exception(e)
