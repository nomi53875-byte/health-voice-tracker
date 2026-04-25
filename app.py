import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# 設定網頁標題
st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 背景樣式優化 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

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
    
    # 修改 1：預設改為開啟 (True)
    manual_mode = st.toggle("手動輸入", value=True)

    # --- 三次平均計算助手 ---
    with st.expander("🔢 三次平均計算助手 (點擊展開)"):
        st.write("輸入三次測量值：")
        colA, colB, colC = st.columns(3)
        # 修改 2：平均助手欄位預設清空 (value=None)
        m1 = st.number_input("第 1 次", min_value=0, max_value=250, value=None, placeholder="0")
        m2 = st.number_input("第 2 次", min_value=0, max_value=250, value=None, placeholder="0")
        m3 = st.number_input("第 3 次", min_value=0, max_value=250, value=None, placeholder="0")
        
        vals = [v for v in [m1, m2, m3] if v is not None and v > 0]
        if vals:
            avg_val = int(sum(vals) / len(vals))
            st.info(f"計算結果平均值：**{avg_val}**")
            if st.button("✅ 套用此平均值至下方表單"):
                st.session_state['sys_input'] = avg_val
                st.toast("已帶入平均值！")

    # 準備表單介面
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        
        c1, c2 = st.columns(2)
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
            
        # 取得暫存值或預設值
        temp_sys = st.session_state.get('sys_input')

        # 修改 3：確保手動模式下 value=None，達到清空效果
        if manual_mode:
            sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=temp_sys, placeholder="120")
            dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=None, placeholder="80")
            pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=None, placeholder="70")
        else:
            sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=temp_sys if temp_sys else 120)
            dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=80)
            pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=70)
        
        context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
        notes = st.text_input("備註", placeholder="感覺...")
        
        submit_button = st.form_submit_button(label="📝 儲存紀錄")

    if submit_button:
        # 防呆處理
        f_sys = sys_val if sys_val is not None else 120
        f_dia = dia_val if dia_val is not None else 80
        f_pul = pul_val if pul_val is not None else 70
        
        worksheet.append_row([str(date_val), time_val.strftime("%H:%M"), f_sys, f_dia, f_pul, context, notes])
        st.balloons()
        st.success(f"✅ 已存入：{f_sys}/{f_dia}")
        # 存檔後清空 session
        if 'sys_input' in st.session_state:
            st.session_state.pop('sys_input')

    st.divider()
    records = worksheet.get_all_records()
    if records:
        st.dataframe(pd.DataFrame(records).tail(5), use_container_width=True)

except Exception as e:
    st.error("連線錯誤")
    st.exception(e)
