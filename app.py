import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 終極 CSS：鎖死寬度與位置 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    
    /* 1. 強制讓 expander 內的內容不換行 */
    .stExpander [data-testid="stVerticalBlock"] {
        display: block !important; /* 破解 flex 排版 */
    }

    /* 2. 針對輸入框進行極致寬度鎖定 */
    .stExpander div[data-testid="column"] {
        float: left !important; /* 使用舊式浮動，強制並排 */
        width: 31% !important; /* 精確鎖定在 1/3 左右 */
        min-width: 0px !important;
        margin: 1% !important;
    }

    /* 3. 移除輸入框內的按鈕，確保格子可以縮到最短 */
    .stExpander button { display: none !important; }
    .stExpander div[data-baseweb="input"] { height: 35px !important; }
    .stExpander input { text-align: center !important; font-size: 16px !important; padding: 0 !important; }
    
    /* 清除浮動防止下面崩潰 */
    .clearfix::after { content: ""; clear: both; display: table; }
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
        # 顯示標題
        st.markdown("""
            <div style="display: flex; text-align: center; font-size: 12px; color: grey;">
                <div style="flex: 1;">高壓</div>
                <div style="flex: 1;">低壓</div>
                <div style="flex: 1;">心跳</div>
            </div>
        """, unsafe_allow_html=True)

        def avg_row(label):
            st.write(f"**{label}**")
            # 強制並排三列
            c1, c2, c3 = st.columns(3)
            with c1: s = st.text_input(f"S{label}", placeholder="高壓", label_visibility="collapsed")
            with c2: d = st.text_input(f"D{label}", placeholder="低壓", label_visibility="collapsed")
            with c3: p = st.text_input(f"P{label}", placeholder="心跳", label_visibility="collapsed")
            return s, d, p

        s1, d1, p1 = avg_row("1次")
        s2, d2, p2 = avg_row("2次")
        s3, d3, p3 = avg_row("3次")

        # 計算邏輯...
        def to_int(v): return int(v) if v and v.strip().isdigit() else None
        sl = [to_int(v) for v in [s1, s2, s3] if to_int(v)]
        dl = [to_int(v) for v in [d1, d2, d3] if to_int(v)]
        pl = [to_int(v) for v in [p1, p2, p3] if to_int(v)]

        if sl and dl and pl:
            avg_s, avg_d, avg_p = int(sum(sl)/len(sl)), int(sum(dl)/len(dl)), int(sum(pl)/len(pl))
            st.info(f"💡 平均：{avg_s} / {avg_d} ({avg_p})")
            if st.button("✅ 套用"):
                st.session_state.update({'sys_input': avg_s, 'dia_input': avg_d, 'pul_input': avg_p})

    # --- 正式紀錄表單 (維持穩定) ---
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
