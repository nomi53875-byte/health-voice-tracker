import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 核心 CSS：強制移除所有 Streamlit 欄位保護 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    
    /* 這裡是最強悍的 CSS，強制鎖定手機端的顯示 */
    @media (max-width: 640px) {
        /* 強制 expander 內部的所有 columns 不准換行 */
        .stExpander div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
        }
        /* 強制縮小每個 column 的最小寬度限制 */
        .stExpander div[data-testid="column"] {
            min-width: 0px !important;
            flex: 1 1 0% !important;
        }
    }
    
    /* 讓輸入框變得非常緊湊 */
    .stExpander input {
        padding: 5px !important;
        text-align: center !important;
        font-size: 14px !important;
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
        # 標頭 (使用 st.columns，但搭配我們上面的強制 CSS)
        h = st.columns([1, 3.6, 3.6, 3.6])
        h[1].caption("高壓")
        h[2].caption("低壓")
        h[3].caption("心跳")

        def avg_row(label):
            cols = st.columns([1, 3.6, 3.6, 3.6])
            with cols[0]: st.write(f"**{label}**")
            # 使用 text_input 避開 number_input 的按鈕寬度限制
            s = cols[1].text_input(f"S{label}", value="", placeholder="0", key=f"s_{label}", label_visibility="collapsed")
            d = cols[2].text_input(f"D{label}", value="", placeholder="0", key=f"d_{label}", label_visibility="collapsed")
            p = cols[3].text_input(f"P{label}", value="", placeholder="0", key=f"p_{label}", label_visibility="collapsed")
            return s, d, p

        s1, d1, p1 = avg_row("1")
        s2, d2, p2 = avg_row("2")
        s3, d3, p3 = avg_row("3")

        # 計算與套用邏輯 (這裡我們要把字串轉成整數)
        def to_int(v): return int(v) if v and v.strip().isdigit() else None
        
        sl = [to_int(v) for v in [s1, s2, s3] if to_int(v)]
        dl = [to_int(v) for v in [d1, d2, d3] if to_int(v)]
        pl = [to_int(v) for v in [p1, p2, p3] if to_int(v)]

        if sl and dl and pl:
            avg_s, avg_d, avg_p = int(sum(sl)/len(sl)), int(sum(dl)/len(dl)), int(sum(pl)/len(pl))
            st.info(f"💡 平均：{avg_s}/{avg_d} ({avg_p})")
            if st.button("✅ 套用平均值"):
                st.session_state.update({'sys_input': avg_s, 'dia_input': avg_d, 'pul_input': avg_p})

    # --- 正式紀錄表單 (維持穩定) ---
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        c1, c2 = st.columns(2)
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
        
        ts, td, tp = st.session_state.get('sys_input'), st.session_state.get('dia_input'), st.session_state.get('pul_input')
        
        # 表單內維持 number_input，因為空間充足
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
