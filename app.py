import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import re

# 設定網頁標題
st.set_page_config(page_title="通用健康紀錄助手", layout="centered")

# --- 背景樣式 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 1. 取得網址中的試算表 ID ---
# 預設 ID (你的)
DEFAULT_ID = "1SUnTdHJFPFbo2pr8dnAib3tTSrCCSygBcp4eAOxWz4g"
query_params = st.query_params
url_id = query_params.get("id", DEFAULT_ID)

# --- 2. 設定區塊 (摺疊選單) ---
with st.expander("⚙️ 切換使用者 / 設定專屬試算表"):
    st.write("如果你想切換到自己的試算表：")
    new_url = st.text_input("請貼上你的 Google 試算表完整網址：", placeholder="https://docs.google.com/spreadsheets/d/...")
    
    if st.button("🔧 生成我專屬的 App 連結"):
        if "/d/" in new_url:
            # 使用正規表達式提取 ID
            extracted_id = re.search(r"/d/([^/]*)", new_url).group(1)
            # 更新網址參數
            st.query_params["id"] = extracted_id
            st.success("設定成功！請「重新整理網頁」後，將新網址加入手機主畫面。")
            st.info(f"記得將服務帳號加入編輯者：\n{st.secrets['connections']['gsheets']['client_email']}")
        else:
            st.error("網址格式不正確，請確認包含 /d/...")

# --- 3. 連線邏輯 ---
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
    # 使用目前網址參數中的 ID
    sh = client.open_by_key(url_id)
    worksheet = sh.get_worksheet(0)
    
    st.link_button("📂 開啟目前試算表原始檔", f"https://docs.google.com/spreadsheets/d/{url_id}")
    manual_mode = st.toggle("手動輸入模式", value=True)

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
        f_pul = pul_val if pul_val is not None else 70
        worksheet.append_row([str(date_val), time_val.strftime("%H:%M"), f_sys, f_dia, f_pul, context, notes])
        st.balloons()
        st.success(f"✅ 已存入試算表！")

    st.divider()
    records = worksheet.get_all_records()
    if records:
        st.dataframe(pd.DataFrame(records).tail(5), use_container_width=True)

except Exception as e:
    st.warning("⚠️ 尚未連線到有效的試算表。請確認是否已將服務帳號加入共用。")
    if "PermissionError" in str(e) or "spreadsheetNotFound" in str(e):
        st.error("存取失敗：請確保試算表已共享給該 Email。")
