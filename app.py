import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# 設定網頁標題
st.set_page_config(page_title="血壓記錄助手", layout="centered")

# --- 背景樣式優化 ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 3em;
        font-size: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🩺 血壓手動紀錄")

# --- 連線邏輯 ---
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

# --- 讀取與顯示主邏輯 ---
try:
    client = get_gspread_client()
    sheet_id = "1SUnTdHJFPFbo2pr8dnAib3tTSrCCSygBcp4eAOxWz4g"
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)
    
    # 準備表單介面
    with st.form("health_form", clear_on_submit=True):
        st.subheader("📝 填寫新數據")
        
        # 設定台北時間
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        
        col1, col2 = st.columns(2)
        with col1:
            date_val = st.date_input("日期", now.date())
        with col2:
            time_val = st.time_input("時間", now.time())
            
        systolic = st.number_input("收縮壓 (高壓)", min_value=50, max_value=250, value=120)
        # 修正這裡：將 max_VALUE 改為 max_value
        diastolic = st.number_input("舒張壓 (低壓)", min_value=30, max_value=150, value=80)
        pulse = st.number_input("心跳 (Pulse)", min_value=30, max_value=200, value=70)
        
        context = st.selectbox("情境", ["一般", "起床", "睡前", "運動後", "不舒服"])
        notes = st.text_input("備註 (可不填)", placeholder="例如：感覺有點累")
        
        submit_button = st.form_submit_button(label="🚀 儲存紀錄")

    if submit_button:
        new_row = [
            str(date_val), 
            time_val.strftime("%H:%M"), 
            systolic, 
            diastolic, 
            pulse, 
            context, 
            notes
        ]
        worksheet.append_row(new_row)
        st.balloons()
        st.success("✅ 數據已成功存入雲端倉庫！")

    # --- 顯示歷史紀錄 ---
    st.divider()
    st.subheader("📊 最近紀錄預覽")
    records = worksheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        # 顯示最後 5 筆並讓表格寬度自動適應
        st.dataframe(df.tail(5), use_container_width=True)
    else:
        st.write("目前尚無資料。")

except Exception as e:
    st.error("連線發生錯誤，請檢查設定。")
    st.exception(e)
