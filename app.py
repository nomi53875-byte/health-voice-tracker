import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 核心 CSS：極限壓縮輸入框 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    
    /* 1. 強制並排 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
    }
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }

    /* 2. 壓縮 number_input 的內部元件 */
    /* 縮減按鈕寬度 */
    .stExpander button[kind="secondary"] {
        width: 25px !important;
        min-width: 25px !important;
        padding: 0px !important;
    }
    /* 縮減輸入框間距 */
    .stExpander div[data-baseweb="input"] {
        padding-left: 2px !important;
        padding-right: 2px !important;
    }
    .stExpander input {
        padding: 2px !important;
        text-align: center !important;
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 網格控制項
show_grid = st.sidebar.checkbox("📐 開啟排版校正網格", value=False)
if show_grid:
    grid_html = '<div class="grid-overlay" style="position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9999; display:flex; justify-content:space-between; padding:0 1rem;">'
    for i in range(1, 14): grid_html += f'<div style="width:1px; height:100%; background:rgba(255,0,0,0.2); position:relative;"><span style="position:absolute; top:0; left:-2px; font-size:8px; color:red;">{i}</span></div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

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
        # 標籤 1.5, 三個數據框各 3.5 (總共 12)
        col_spec = [1.5, 3.5, 3.5, 3.5]
        
        h = st.columns(col_spec)
        h[1].caption("高壓")
        h[2].caption("低壓")
        h[3].caption("心跳")

        def avg_row(label):
            cols = st.columns(col_spec)
            with cols[0]: st.write(f"**{label}**")
            s = cols[1].number_input(f"{label}_S", min_value=0, max_value=250, value=None, placeholder="0", label_visibility="collapsed")
            d = cols[2].number_input(f"{label}_D", min_value=0, max_value=200, value=None, placeholder="0", label_visibility="collapsed")
            p = cols[3].number_input(f"{label}_P", min_value=0, max_value=200, value=None, placeholder="0", label_visibility="collapsed")
            return s, d, p

        s1, d1, p1 = avg_row("1")
        s2, d2, p2 = avg_row("2")
        s3, d3, p3 = avg_row("3")

        # 計算與套用邏輯 (略)
        sys_list = [v for v in [s1, s2, s3] if v is not None and v > 0]
        dia_list = [v for v in [d1, d2, d3] if v is not None and v > 0]
        pul_list = [v for v in [p1, p2, p3] if v is not None and v > 0]

        if sys_list and dia_list and pul_list:
            avg_s, avg_d, avg_p = int(sum(sys_list)/len(sys_list)), int(sum(dia_list)/len(dia_list)), int(sum(pul_list)/len(pul_list))
            st.info(f"💡 平均：{avg_s}/{avg_d} ({avg_p})")
            if st.button("✅ 套用數據"):
                st.session_state.update({'sys_input': avg_s, 'dia_input': avg_d, 'pul_input': avg_p})

    # --- 正式紀錄表單 (維持原樣) ---
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        c1, c2 = st.columns(2)
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
        
        ts, td, tp = st.session_state.get('sys_input'), st.session_state.get('dia_input'), st.session_state.get('pul_input')
        
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
