import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# 設定網頁標題
st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 核心排版 CSS 優化 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; font-size: 16px; }
    
    /* 網格背景樣式 - 僅在校正模式開啟時顯現 */
    .grid-overlay {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none;
        z-index: 9999;
        display: flex;
        justify-content: space-between;
        padding: 0 1rem;
    }
    .grid-line {
        width: 1px;
        height: 100%;
        background-color: rgba(255, 0, 0, 0.2); /* 淡淡的紅線 */
        position: relative;
    }
    .grid-num {
        position: absolute;
        top: 0; left: -5px;
        font-size: 10px;
        color: red;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 網格控制開關 (放在側邊欄或最底部) ---
show_grid = st.sidebar.checkbox("📐 開啟排版校正網格", value=False)

if show_grid:
    # 建立 12 條參考線
    grid_html = '<div class="grid-overlay">'
    for i in range(1, 14):
        grid_html += f'<div class="grid-line"><span class="grid-num">{i}</span></div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

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
    manual_mode = st.toggle("手動輸入", value=True)

    # --- 三次平均計算助手 ---
    with st.expander("🔢 三次平均計算助手 (高壓/低壓/心跳)"):
        # 在手機上，我們強制使用較窄的間距
        st.write("請輸入三次數據：")
        
        # 定義每一列的比例
        # [1, 2, 2, 2] 表示：第一欄標籤佔 1 份，其餘三欄各佔 2 份
        col_spec = [1, 2, 2, 2]
        
        header = st.columns(col_spec)
        header[1].caption("高壓")
        header[2].caption("低壓")
        header[3].caption("心跳")

        def avg_row(label):
            cols = st.columns(col_spec)
            cols[0].write(label)
            s = cols[1].number_input(f"{label}_S", min_value=0, max_value=250, value=None, placeholder="0", label_visibility="collapsed")
            d = cols[2].number_input(f"{label}_D", min_value=0, max_value=200, value=None, placeholder="0", label_visibility="collapsed")
            p = cols[3].number_input(f"{label}_P", min_value=0, max_value=200, value=None, placeholder="0", label_visibility="collapsed")
            return s, d, p

        s1, d1, p1 = avg_row("1次")
        s2, d2, p2 = avg_row("2次")
        s3, d3, p3 = avg_row("3次")

        sys_list = [v for v in [s1, s2, s3] if v is not None and v > 0]
        dia_list = [v for v in [d1, d2, d3] if v is not None and v > 0]
        pul_list = [v for v in [p1, p2, p3] if v is not None and v > 0]

        if sys_list and dia_list and pul_list:
            avg_s = int(sum(sys_list) / len(sys_list))
            avg_d = int(sum(dia_list) / len(dia_list))
            avg_p = int(sum(pul_list) / len(pul_list))
            st.info(f"💡 平均：{avg_s}/{avg_d} ({avg_p})")
            if st.button("✅ 套用"):
                st.session_state['sys_input'] = avg_s
                st.session_state['dia_input'] = avg_d
                st.session_state['pul_input'] = avg_p

    # --- 正式紀錄表單 ---
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        
        c1, c2 = st.columns(2)
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
            
        t_sys = st.session_state.get('sys_input')
        t_dia = st.session_state.get('dia_input')
        t_pul = st.session_state.get('pul_input')

        if manual_mode:
            sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=t_sys, placeholder="120")
            dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=200, value=t_dia, placeholder="80")
            pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=t_pul, placeholder="70")
        else:
            sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=t_sys if t_sys else 120)
            dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=200, value=t_dia if t_dia else 80)
            pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=t_pul if t_pul else 70)
        
        context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
        notes = st.text_input("備註", placeholder="感覺...")
        st.form_submit_button("📝 儲存紀錄")

except Exception as e:
    st.error("連線錯誤")
