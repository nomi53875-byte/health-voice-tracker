import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="健康語音助手", layout="centered")
st.title("📊 數據倉庫狀態 (官方直連穩定版)")

def get_gspread_client():
    # 1. 直接從 Secrets 抓取你剛剛貼的那一整包資料
    s = st.secrets["connections"]["gsheets"]
    
    # 2. 建構認證字典 (不加額外加工，直接讓 google-auth 讀取多行 key)
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
    
    # 3. 定義 Google Sheets 存取權限範圍
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 4. 建立認證物件並授權
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

try:
    # 執行連線
    client = get_gspread_client()
    
    # 取得試算表網址 (從 Secrets)
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    sh = client.open_by_url(sheet_url)
    worksheet = sh.get_worksheet(0) # 讀取第一個分頁 (Sheet1)
    
    # 讀取現有資料
    records = worksheet.get_all_records()
    
    if records:
        df = pd.DataFrame(records)
        st.success("✅ 官方驅動連線成功！")
        st.write(f"目前紀錄筆數：{len(df)}")
        st.dataframe(df.tail(5)) # 顯示最後 5 筆
    else:
        st.info("✅ 連線成功，但目前試算表是空的（或只有標題）。")

    st.divider()

    # 寫入測試
    st.subheader("寫入測試")
    if st.button("🚀 點我寫入測試紀錄"):
        # 準備一行資料 (對應你的欄位：Date, Time, Systolic, Diastolic, Pulse, Context, Notes)
        new_row = ["2026-04-25", "04:30", 120, 80, 70, "官方直連", "物理換行測試成功"]
        worksheet.append_row(new_row)
        st.balloons()
        st.success("寫入成功！請重新整理頁面查看結果。")
        st.rerun()

except Exception as e:
    st.error("❌ 連線失敗")
    st.info("請確認：1. Secrets 格式正確 2. 服務帳號 Email 已加入試算表共用 3. 網路連線正常")
    st.exception(e)
