import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 恢復乾淨的 CSS ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; }
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

    # --- 平均助手：改用表格編輯器 ---
    with st.expander("🔢 三次平均助手 (點擊儲存格輸入)"):
        st.write("請在表格中填入數值：")
        
        # 建立一個初始 DataFrame
        init_df = pd.DataFrame(
            [[None, None, None], [None, None, None], [None, None, None]],
            columns=["高壓", "低壓", "心跳"],
            index=["1次", "2次", "3次"]
        )
        
        # 使用 data_editor，這在手機上會是一個可以橫向滑動的表格，絕不換行
        edited_df = st.data_editor(
            init_df,
            column_config={
                "高壓": st.column_config.NumberColumn(min_value=0, max_value=250),
                "低壓": st.column_config.NumberColumn(min_value=0, max_value=200),
                "心跳": st.column_config.NumberColumn(min_value=0, max_value=200),
            },
            use_container_width=True,
            hide_index=False
        )
        
        # 計算平均值
        if edited_df.notna().any().any():
            avgs = edited_df.mean()
            s_avg = int(avgs["高壓"]) if not pd.isna(avgs["高壓"]) else None
            d_avg = int(avgs["低壓"]) if not pd.isna(avgs["低壓"]) else None
            p_avg = int(avgs["心跳"]) if not pd.isna(avgs["心跳"]) else None
            
            if s_avg and d_avg:
                st.info(f"💡 平均結果：{s_avg} / {d_avg} ({p_avg if p_avg else '--'})")
                if st.button("✅ 套用至下方表單"):
                    st.session_state.update({'sys_input': s_avg, 'dia_input': d_avg, 'pul_input': p_avg})

    # --- 正式紀錄表單 ---
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        c1, c2 = st.columns(2)
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
        
        ts = st.session_state.get('sys_input')
        td = st.session_state.get('dia_input')
        tp = st.session_state.get('pul_input')
        
        # 為了保證不破圖，正式區也改為一列一個，或維持 columns(2)
        sys_val = st.number_input("收縮壓 (高壓)", min_value=0, value=ts, placeholder="120")
        dia_val = st.number_input("舒張壓 (低壓)", min_value=0, value=td, placeholder="80")
        pul_val = st.number_input("心跳 (Pulse)", min_value=0, value=tp, placeholder="70")
        
        context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
        notes = st.text_input("備註")
        if st.form_submit_button("📝 儲存紀錄"):
            worksheet.append_row([str(date_val), time_val.strftime("%H:%M"), sys_val, dia_val, pul_val, context, notes])
            st.balloons()
            for k in ['sys_input', 'dia_input', 'pul_input']: st.session_state.pop(k, None)

except Exception as e:
    st.error("系統維護中")
