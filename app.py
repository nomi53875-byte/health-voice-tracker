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
    .main-title {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 20px;
    }
    /* 讓輸入框的提示文字更明顯一點 */
    input::placeholder {
        color: #aaaaaa !important;
        opacity: 1;
    }
    .stButton>button {
        width: 100%;
        height: 3em;
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🩺 血壓健康紀錄助手</p>', unsafe_allow_html=True)

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

try:
    client = get_gspread_client()
    sheet_id = "1SUnTdHJFPFbo2pr8dnAib3tTSrCCSygBcp4eAOxWz4g"
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)
    
    st.link_button("📂 開啟 Google 試算表原始檔", f"https://docs.google.com/spreadsheets/d/{sheet_id}")

    # 準備表單介面
    with st.form("health_form", clear_on_submit=True):
        st.subheader("📝 填寫數據")
        
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        
        col1, col2 = st.columns(2)
        with col1:
            date_val = st.date_input("日期", now.date())
        with col2:
            time_val = st.time_input("時間", now.time())
            
        # --- 改動核心：value=None 讓點擊時是空的，但保留 placeholder 提示 ---
        systolic = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=None, placeholder="120", step=1)
        diastolic = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=None, placeholder="80", step=1)
        pulse = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=None, placeholder="70", step=1)
        
        context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
        notes = st.text_input("備註 (可不填)", placeholder="例如：感覺有點累")
        
        submit_button = st.form_submit_button(label="💾 點擊儲存紀錄")

    if submit_button:
        # 如果用戶沒填，我們就自動補上預設值，這樣你沒打字也可以直接按儲存
        final_sys = systolic if systolic is not None else 120
        final_dia = diastolic if diastolic is not None else 80
        final_pul = pulse if pulse is not None else 70
        
        new_row = [
            str(date_val), 
            time_val.strftime("%H:%M"), 
            final_sys, 
            final_dia, 
            final_pul, 
            context, 
            notes
        ]
        worksheet.append_row(new_row)
        st.balloons()
        st.success(f"✅ 成功存入！({final_sys}/{final_dia} 心跳:{final_pul})")

    st.divider()
    st.subheader("📊 最近紀錄預覽")
    records = worksheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        st.dataframe(df.tail(5), use_container_width=True)

except Exception as e:
    st.error("連線發生錯誤")
    st.exception(e)
