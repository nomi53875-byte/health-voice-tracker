import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# 頁面基本設定
st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 基礎美化 CSS ---
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; color: #2E7D32; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #4CAF50; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手 (穩定版)</p>', unsafe_allow_html=True)

# --- Google Sheets 連線函式 ---
def get_gspread_client():
    s = st.secrets["connections"]["gsheets"]
    info = {
        "type": s["type"],
        "project_id": s["project_id"],
        "private_key_id": s["private_key_id"],
        "private_key": s["private_key"].replace('\\n', '\n'),
        "client_email": s["client_email"],
        "client_id": s["client_id"],
        "auth_uri": s["auth_uri"],
        "token_uri": s["token_uri"],
        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
        "client_x509_cert_url": s["client_x509_cert_url"]
    }
    creds = Credentials.from_service_account_info(info, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    return gspread.authorize(creds)

try:
    # 初始化連線
    client = get_gspread_client()
    sheet_id = "1SUnTdHJFPFbo2pr8dnAib3tTSrCCSygBcp4eAOxWz4g" # 您的試算表 ID
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)

    # 快捷按鈕
    st.link_button("📂 開啟試算表查閱", f"https://docs.google.com/spreadsheets/d/{sheet_id}")

    # --- 紀錄表單 ---
    with st.form("health_record_form", clear_on_submit=True):
        # 設定台北時區
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        
        col1, col2 = st.columns(2)
        with col1:
            date_val = st.date_input("測量日期", now.date())
        with col2:
            time_val = st.time_input("測量時間", now.time())

        st.divider()

        # 數值輸入
        sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=120, step=1)
        dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=200, value=80, step=1)
        pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=70, step=1)
        
        st.divider()

        # 額外資訊
        context = st.selectbox("量測情境", ["一般", "起床", "睡前", "運動後", "感冒/不適"])
        notes = st.text_input("備註 (心情或身體狀況)")

        # 提交按鈕
        submit_clicked = st.form_submit_button("📝 儲存紀錄")

        if submit_clicked:
            # 準備寫入的資料列
            new_row = [
                str(date_val),
                time_val.strftime("%H:%M"),
                sys_val,
                dia_val,
                pul_val,
                context,
                notes
            ]
            
            # 寫入 Google Sheets
            worksheet.append_row(new_row)
            st.success("✅ 紀錄成功儲存到雲端！")
            st.balloons()

except Exception as e:
    st.error(f"系統連接中，請稍候... (錯誤訊息: {e})")
