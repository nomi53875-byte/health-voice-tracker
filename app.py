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
    /* 讓平均助手的標題緊湊一點 */
    .avg-label { font-size: 14px; font-weight: bold; color: #555; margin-bottom: 5px; }
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
    manual_mode = st.toggle("手動輸入", value=True)

    # --- 核心更新：全功能平均助手 ---
    with st.expander("🔢 三次平均計算助手 (高壓/低壓/心跳)"):
        st.write("請輸入三次完整數據：")
        
        # 建立三列（分別代表三次測量）
        col_labels = st.columns([1, 1, 1, 1])
        with col_labels[1]: st.markdown('<p class="avg-label">高壓</p>', unsafe_allow_html=True)
        with col_labels[2]: st.markdown('<p class="avg-label">低壓</p>', unsafe_allow_html=True)
        with col_labels[3]: st.markdown('<p class="avg-label">心跳</p>', unsafe_allow_html=True)

        def avg_row(label):
            cols = st.columns([1, 1, 1, 1])
            with cols[0]: st.write(label)
            s = cols[1].number_input(f"{label}_S", min_value=0, max_value=250, value=None, placeholder="0", label_visibility="collapsed")
            d = cols[2].number_input(f"{label}_D", min_value=0, max_value=200, value=None, placeholder="0", label_visibility="collapsed")
            p = cols[3].number_input(f"{label}_P", min_value=0, max_value=200, value=None, placeholder="0", label_visibility="collapsed")
            return s, d, p

        s1, d1, p1 = avg_row("1次")
        s2, d2, p2 = avg_row("2次")
        s3, d3, p3 = avg_row("3次")

        # 計算平均
        sys_list = [v for v in [s1, s2, s3] if v is not None and v > 0]
        dia_list = [v for v in [d1, d2, d3] if v is not None and v > 0]
        pul_list = [v for v in [p1, p2, p3] if v is not None and v > 0]

        if sys_list and dia_list and pul_list:
            avg_s = int(sum(sys_list) / len(sys_list))
            avg_d = int(sum(dia_list) / len(dia_list))
            avg_p = int(sum(pul_list) / len(pul_list))
            
            st.info(f"💡 平均結果：**{avg_s} / {avg_d}** 心跳: **{avg_p}**")
            if st.button("✅ 一鍵套用這三項數據"):
                st.session_state['sys_input'] = avg_s
                st.session_state['dia_input'] = avg_d
                st.session_state['pul_input'] = avg_p
                st.toast("數據已同步帶入下方表單！")

    # 準備正式表單介面
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        
        c1, c2 = st.columns(2)
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
            
        # 取得暫存值
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
        submit_button = st.form_submit_button(label="📝 儲存紀錄")

    if submit_button:
        f_sys = sys_val if sys_val is not None else 120
        f_dia = dia_val if dia_val is not None else 80
        f_pul = pul_val if pul_val is not None else 70
        
        worksheet.append_row([str(date_val), time_val.strftime("%H:%M"), f_sys, f_dia, f_pul, context, notes])
        st.balloons()
        st.success(f"✅ 已存入：{f_sys}/{f_dia}")
        # 清除所有暫存
        for k in ['sys_input', 'dia_input', 'pul_input']:
            if k in st.session_state: st.session_state.pop(k)

    st.divider()
    records = worksheet.get_all_records()
    if records:
        st.dataframe(pd.DataFrame(records).tail(5), use_container_width=True)

except Exception as e:
    st.error("連線錯誤")
    st.exception(e)
