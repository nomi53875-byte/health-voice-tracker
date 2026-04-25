import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 終極暴力 CSS ---
# 這次我們直接對 .stHorizontalBlock 下死命令，無視所有斷點
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    
    /* 核心：鎖死所有橫向區塊 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 2px !important;
    }
    
    /* 強制每個 Column 寬度按比例分配，不准有最小寬度 */
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
        max-width: none !important;
    }

    /* 針對輸入框內部的微小細節 */
    input {
        padding: 4px 2px !important;
        font-size: 14px !important;
        text-align: center !important;
    }
    
    /* 移除所有可能導致換行的隱形邊距 */
    div[data-testid="stVerticalBlock"] > div {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 連線邏輯 (保持不變) ---
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
        # 直接使用簡約標題，不佔用行空間
        st.markdown("<div style='display:flex; text-align:center; font-size:11px; color:gray; margin-bottom:-10px;'><div style='flex:1;'></div><div style='flex:3;'>高壓</div><div style='flex:3;'>低壓</div><div style='flex:3;'>心跳</div></div>", unsafe_allow_html=True)

        def avg_row(label, key_pre):
            # 比例：1:3:3:3 (標籤佔 1 份，其餘各 3 份)
            cols = st.columns([1, 3, 3, 3])
            with cols[0]: st.write(f"**{label}**")
            # 使用 text_input 避開 number_input 的內部保護結構
            s = cols[1].text_input(f"s{key_pre}", placeholder="0", label_visibility="collapsed")
            d = cols[2].text_input(f"d{key_pre}", placeholder="0", label_visibility="collapsed")
            p = cols[3].text_input(f"p{key_pre}", placeholder="0", label_visibility="collapsed")
            return s, d, p

        s1, d1, p1 = avg_row("1", "r1")
        s2, d2, p2 = avg_row("2", "r2")
        s3, d3, p3 = avg_row("3", "r3")

        def to_int(v): return int(v) if v and v.strip().isdigit() else None
        sl = [to_int(v) for v in [s1, s2, s3] if to_int(v)]
        dl = [to_int(v) for v in [d1, d2, d3] if to_int(v)]
        pl = [to_int(v) for v in [p1, p2, p3] if to_int(v)]

        if sl and dl and pl:
            avg_s, avg_d, avg_p = int(sum(sl)/len(sl)), int(sum(dl)/len(dl)), int(sum(pl)/len(pl))
            st.info(f"💡 平均：{avg_s}/{avg_d} ({avg_p})")
            if st.button("✅ 套用"):
                st.session_state.update({'sys_input': avg_s, 'dia_input': avg_d, 'pul_input': avg_p})

    # --- 正式紀錄區 ---
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        c1, c2 = st.columns(2) # 這裡只有兩欄，所以直屏絕對沒問題
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
        
        ts, td, tp = st.session_state.get('sys_input'), st.session_state.get('dia_input'), st.session_state.get('pul_input')
        
        sys_val = st.number_input("收縮壓", value=ts if ts else 120)
        dia_val = st.number_input("舒張壓", value=td if td else 80)
        pul_val = st.number_input("心跳", value=tp if tp else 70)
        
        context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
        notes = st.text_input("備註")
        if st.form_submit_button("📝 儲存紀錄"):
            worksheet.append_row([str(date_val), time_val.strftime("%H:%M"), sys_val, dia_val, pul_val, context, notes])
            st.balloons()
            for k in ['sys_input', 'dia_input', 'pul_input']: st.session_state.pop(k, None)

except Exception as e:
    st.error(f"連線錯誤: {e}")
