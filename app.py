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
    sheet_id = "1SUnTdHJFPFbo2pr8dnAib3tTSrCCSygBcp4eAOxWz4g" 
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)

    # 快捷功能區
    st.link_button("📂 開啟試算表查閱", f"https://docs.google.com/spreadsheets/d/{sheet_id}")
    
    # --- 重要：手動模式開關 ---
    manual_mode = st.toggle("開啟手動輸入日期/時間", value=False)

    # --- 紀錄表單 ---
    with st.form("health_record_form", clear_on_submit=True):
        # 設定台北時區
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        
        col1, col2 = st.columns(2)
        
        if manual_mode:
            # 手動模式：顯示輸入框讓使用者調整
            with col1:
                date_val = st.date_input("測量日期", now.date())
            with col2:
                time_val = st.time_input("測量時間", now.time())
        else:
            # 自動模式：不顯示輸入框，直接抓現在，但給使用者看一眼確認
            date_val = now.date()
            time_val = now.time()
            st.info(f"📅 自動記錄：{date_val} {time_val.strftime('%H:%M')}")

        st.divider()

        # 數值輸入
        sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=120, step=1)
        dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=200, value=80, step=1)
        pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=70, step=1)
        
        st.divider()

        # 額外資訊
        context = st.selectbox("量測情境", ["一般", "起床", "睡前", "運動後", "感冒/不適"])
        notes =
