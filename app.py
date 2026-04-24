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
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 15px; }
    /* 讓按鈕高度適中 */
    .stButton>button { width: 100%; height: 3em; font-size: 16px; }
    /* 調整元件之間的間距 */
    [data-testid="column"] {
        width: fit-content !important;
        min-width: unset !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🩺 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 連線邏輯 ---
def get_gspread_client():
    s = st.secrets["connections"]["gsheets"]
    info = {
        "type": s["type"], "project_id": s["project_id"], "private_key_id": s["private_key_id"],
        "private_key": s["private_key"], "client_email": s["client_email"], "client_id": s["client_id"],
        "auth_uri": s["auth_uri"], "token_uri": s["token_uri"],
        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
        "client_x509_cert_url": s["client_x509_cert_url"]
    }
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    sheet_id = "1SUnTdHJFPFbo2pr8dnAib3tTSrCCSygBcp4eAOxWz4g"
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)
    
    # --- 關鍵修正：調整比例與縮短文字 ---
    # 使用 0.5:0.5 平分，或稍微偏向按鈕
    col_link, col_toggle = st.columns([0.5, 0.5])
    with col_link:
        # 縮短按鈕文字，避免擠壓空間
        st.link_button("📂 開啟試算表", f"https://docs.google.com/spreadsheets/d/{sheet_id}")
    with col_toggle:
        # 將開關文字簡化，確保開關本體能顯示
        manual_mode = st.toggle("手動模式", value=False)

    # 準備表單介面
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        
        c1, c2 = st.columns(2)
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
            
        if manual_mode:
            sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=None, placeholder="120")
            dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=None, placeholder="80")
            pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=None, placeholder="70")
        else:
            sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=120)
            dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=80)
            pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=70)
        
        context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
        notes = st.text_input("備註", placeholder="感覺...")
        
        submit_button = st.form_submit_button(label="📝 儲存紀錄")

    if submit_button:
        f_sys = sys_val if sys_val is not None else 120
        f_dia = dia_val if dia_val is not None else 80
        f_pul = pulse_val if pul_val is not None else 70 # 注意這裡變數名稱修正
        
        worksheet.append_row([str(date_val), time_val.strftime("%H:%M"), f_sys, f_dia, f_pul, context, notes])
        st.balloons()
        st.success(f"✅ 已存入：{f_sys}/{f_dia}")

    st.divider()
    records = worksheet.get_all_records()
    if records:
        st.dataframe(pd.DataFrame(records).tail(5), use_container_width=True)

except Exception as e:
    st.error("連線錯誤")
    st.exception(e)
