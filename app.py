import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 核心 CSS：專門應對直屏的布局 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    
    /* 1. 強制讓 expader 內部的 columns 比例在手機直屏下不崩潰 */
    /* 我們強制三個數據框平分剩下的寬度 */
    .stExpander [data-testid="column"] {
        min-width: 0px !important;
        flex: 1 1 25% !important; /* 讓四個欄位(1標籤+3數據)大約佔 25% */
        padding: 0 2px !important;
    }

    /* 2. 移除 text_input 的所有多餘邊距與外框 */
    .stExpander div[data-baseweb="base-input"] {
        background-color: #f8f9fa !important;
        border-radius: 5px !important;
    }
    .stExpander input {
        text-align: center !important;
        padding: 8px 2px !important;
        font-size: 15px !important;
        height: 40px !important;
    }
    
    /* 3. 標籤微調 */
    .row-label {
        font-size: 16px;
        font-weight: bold;
        line-height: 40px; /* 讓文字垂直居中對齊輸入框 */
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 連線邏輯 (略) ---
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
    
    st.link_button("📂 開啟試算表", f"https://docs.google.com/spreadsheets/d/{sheet_id}")
    manual_mode = st.toggle("手動輸入", value=True)

    with st.expander("🔢 三次平均計算助手"):
        # 使用平分比例 [1, 1, 1, 1] 確保不會有誰被擠出去
        col_spec = [1, 1, 1, 1]
        
        h = st.columns(col_spec)
        h[1].markdown("<p style='text-align:center;font-size:12px;color:grey;'>高壓</p>", unsafe_allow_html=True)
        h[2].markdown("<p style='text-align:center;font-size:12px;color:grey;'>低壓</p>", unsafe_allow_html=True)
        h[3].markdown("<p style='text-align:center;font-size:12px;color:grey;'>心跳</p>", unsafe_allow_html=True)

        def avg_row(label):
            cols = st.columns(col_spec)
            with cols[0]: st.markdown(f'<div class="row-label">{label}</div>', unsafe_allow_html=True)
            # 使用 key 確保狀態不打架，且全部使用 text_input 避開按鈕寬度限制
            s = cols[1].text_input(f"S{label}", placeholder="0", label_visibility="collapsed")
            d = cols[2].text_input(f"D{label}", placeholder="0", label_visibility="collapsed")
            p = cols[3].text_input(f"P{label}", placeholder="0", label_visibility="collapsed")
            return s, d, p

        s1, d1, p1 = avg_row("1")
        s2, d2, p2 = avg_row("2")
        s3, d3, p3 = avg_row("3")

        def to_int(v):
            if v and v.strip().isdigit(): return int(v)
            return None

        sys_list = [to_int(v) for v in [s1, s2, s3] if to_int(v)]
        dia_list = [to_int(v) for v in [d1, d2, d3] if to_int(v)]
        pul_list = [to_int(v) for v in [p1, p2, p3] if to_int(v)]

        if sys_list and dia_list and pul_list:
            avg_s, avg_d, avg_p = int(sum(sys_list)/len(sys_list)), int(sum(dia_list)/len(dia_list)), int(sum(pul_list)/len(pul_list))
            st.info(f"💡 平均結果：{avg_s} / {avg_d} ({avg_p})")
            if st.button("✅ 套用數據"):
                st.session_state.update({'sys_input': avg_s, 'dia_input': avg_d, 'pul_input': avg_p})

    # --- 正式紀錄表單 (維持穩定版本) ---
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        c1, c2 = st.columns(2)
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
        
        ts, td, tp = st.session_state.get('sys_input'), st.session_state.get('dia_input'), st.session_state.get('pul_input')
        
        # 表單內維持 number_input，因為空間足夠
        sys_val = st.number_input("收縮壓 (高壓)", min_value=0, value=ts, placeholder="120")
        dia_val = st.number_input("舒張壓 (低壓)", min_value=0, value=td, placeholder="80")
        pul_val = st.number_input("心跳 (Pulse)", min_value=0, value=tp, placeholder="70")
        
        context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
        notes = st.text_input("備註")
        if st.form_submit_button("📝 儲存紀錄"):
            worksheet.append_row([str(date_val), time_val.strftime("%H:%M"), sys_val or 120, dia_val or 80, pul_val or 70, context, notes])
            st.balloons()
            for k in ['sys_input', 'dia_input', 'pul_input']: st.session_state.pop(k, None)

except Exception as e:
    st.error("連線錯誤")
