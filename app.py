import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

st.set_page_config(page_title="血壓記錄助手", layout="centered")

# --- 背景樣式優化 ---
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 3em; font-size: 18px; }
    /* 讓說明文字小一點 */
    .small-hint { font-size: 12px; color: #888; margin-top: -10px; margin-bottom: 10px; }
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
    
    st.link_button("📂 開啟 Google 試算表原始檔", f"https://docs.google.com/spreadsheets/d/{sheet_id}")

    # --- 核心邏輯：新增一個開關來切換模式 ---
    manual_mode = st.toggle("⌨️ 開啟手動輸入模式 (點擊即清空)", value=False)
    if manual_mode:
        st.markdown('<p class="small-hint">模式：手動打字（點擊框框即可輸入，無預設值）</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="small-hint">模式：快速加減（從 120/80 開始調整）</p>', unsafe_allow_html=True)

    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        
        col1, col2 = st.columns(2)
        with col1: date_val = st.date_input("日期", now.date())
        with col2: time_val = st.time_input("時間", now.time())
            
        # 根據開關狀態決定 value
        if manual_mode:
            # 手動模式：value 為 None，方便直接打字
            sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=None, placeholder="120", step=1)
            dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=None, placeholder="80", step=1)
            pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=None, placeholder="70", step=1)
        else:
            # 正常模式：有預設值，+/- 按鈕可用
            sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=120, step=1)
            dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=80, step=1)
            pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=70, step=1)
        
        context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
        notes = st.text_input("備註 (可不填)", placeholder="例如：感覺有點累")
        
        submit_button = st.form_submit_button(label="💾 點擊儲存紀錄")

    if submit_button:
        # 處理 None 值 (防呆)
        f_sys = sys_val if sys_val is not None else 120
        f_dia = dia_val if dia_val is not None else 80
        f_pul = pul_val if pul_val is not None else 70
        
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
