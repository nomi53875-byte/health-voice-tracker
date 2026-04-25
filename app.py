import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 核心 CSS：確保直屏不崩潰 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    
    /* 1. 讓平均助手區塊內的輸入框更緊湊 */
    .avg-input-area input {
        text-align: center !important;
        padding: 5px !important;
        font-size: 16px !important; /* 適合手指點擊的大小 */
        height: 35px !important;
    }
    
    /* 2. 強制橫向並排 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
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
    
    st.link_button("📂 開啟試算表", f"https://docs.google.com/spreadsheets/d/{sheet_id}")
    manual_mode = st.toggle("手動輸入", value=True)

    # --- 關鍵修正：改用 text_input 模擬極簡數字框 ---
    with st.expander("🔢 三次平均計算助手"):
        # 標籤佔 1，其餘佔 3 (1+3+3+3 = 10) 留一點邊緣保險
        col_spec = [1, 3, 3, 3]
        h = st.columns(col_spec)
        h[1].caption("高壓")
        h[2].caption("低壓")
        h[3].caption("心跳")

        def avg_row(label):
            cols = st.columns(col_spec)
            with cols[0]: st.write(f"**{label}**")
            # 改用 text_input 並加入自定義 class
            s = cols[1].text_input(f"{label}_S", placeholder="0", label_visibility="collapsed", key=f"{label}_s")
            d = cols[2].text_input(f"{label}_D", placeholder="0", label_visibility="collapsed", key=f"{label}_d")
            p = cols[3].text_input(f"{label}_P", placeholder="0", label_visibility="collapsed", key=f"{label}_p")
            return s, d, p

        s1, d1, p1 = avg_row("1")
        s2, d2, p2 = avg_row("2")
        s3, d3, p3 = avg_row("3")

        # 轉換數值並計算
        def to_int(v):
            try: return int(v) if v and v.isdigit() else None
            except: return None

        sys_list = [to_int(v) for v in [s1, s2, s3] if to_int(v)]
        dia_list = [to_int(v) for v in [d1, d2, d3] if to_int(v)]
        pul_list = [to_int(v) for v in [p1, p2, p3] if to_int(v)]

        if sys_list and dia_list and pul_list:
            avg_s, avg_d, avg_p = int(sum(sys_list)/len(sys_list)), int(sum(dia_list)/len(dia_list)), int(sum(pul_list)/len(pul_list))
            st.info(f"💡 平均：{avg_s}/{avg_d} ({avg_p})")
            if st.button("✅ 套用數據"):
                st.session_state.update({'sys_input': avg_s, 'dia_input': avg_d, 'pul_input': avg_p})

    # --- 正式紀錄表單 (維持原本好用的 number_input) ---
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        c1, c2 = st.columns(2)
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
        
        ts, td, tp = st.session_state.get('sys_input'), st.session_state.get('dia_input'), st.session_state.get('pul_input')
        
        # 這裡保留帶有按鈕的格式，因為這裡是最後確認區
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
