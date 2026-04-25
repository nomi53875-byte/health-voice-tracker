import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

st.set_page_config(page_title="健康紀錄助手", layout="centered")

# --- 基礎美化 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    /* 隱形調整：讓表格看起來更清爽 */
    [data-testid="stDataEditor"] { border: none !important; }
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
    manual_mode = st.toggle("手動輸入模式", value=True)

    # --- 🔢 平均助手優化版 ---
    with st.expander("🔢 三次平均助手", expanded=True):
        # 1. 初始化資料列：順序改為 低壓 > 高壓 > 心跳
        if 'editor_df' not in st.session_state:
            st.session_state.editor_df = pd.DataFrame(
                [[None, None, None], [None, None, None], [None, None, None]],
                columns=["低壓", "高壓", "心跳"]
            )

        # 2. & 3. & 4. 資料編輯器配置
        # 注意：Streamlit 的 Enter 鍵行為是向下跳，但 Tab 鍵是向右跳。
        # 這是瀏覽器行為，我們透過隱藏索引來優化視覺。
        edited_df = st.data_editor(
            st.session_state.editor_df,
            column_config={
                "低壓": st.column_config.NumberColumn("低壓", min_value=0, max_value=200, format="%d", required=True),
                "高壓": st.column_config.NumberColumn("高壓", min_value=0, max_value=250, format="%d", required=True),
                "心跳": st.column_config.NumberColumn("心跳", min_value=0, max_value=200, format="%d", required=True),
            },
            hide_index=True,  # 去掉左側的選項/序號按鈕
            use_container_width=True,
            num_rows="fixed", # 固定列數，避免出現新增列的按鈕
            key="blood_pressure_editor"
        )

        # 5. 計算與套用功能
        # 檢查是否有輸入數據
        if edited_df.any(axis=None):
            # 排除空值計算平均
            avgs = edited_df.mean()
            s_avg = int(avgs["高壓"]) if not pd.isna(avgs["高壓"]) else None
            d_avg = int(avgs["低壓"]) if not pd.isna(avgs["低壓"]) else None
            p_avg = int(avgs["心跳"]) if not pd.isna(avgs["心跳"]) else None
            
            if s_avg or d_avg or p_avg:
                st.markdown(f"**平均值預覽：** `{d_avg or '--'}` / `{s_avg or '--'}` (心跳: `{p_avg or '--'}`)")
                if st.button("✅ 存入下方表單"):
                    st.session_state.update({
                        'sys_input': s_avg,
                        'dia_input': d_avg,
                        'pul_input': p_avg
                    })
                    st.success("已載入數據，請確認後提交儲存。")

    # --- 📝 正式紀錄表單 ---
    with st.form("health_form", clear_on_submit=True):
        taipei_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(taipei_tz)
        
        c1, c2 = st.columns(2)
        with c1: date_val = st.date_input("日期", now.date())
        with c2: time_val = st.time_input("時間", now.time())
        
        # 從 session_state 讀取平均值
        ts = st.session_state.get('sys_input')
        td = st.session_state.get('dia_input')
        tp = st.session_state.get('pul_input')
        
        sys_val = st.number_input("收縮壓 (高壓)", min_value=0, value=ts if ts else 120)
        dia_val = st.number_input("舒張壓 (低壓)", min_value=0, value=td if td else 80)
        pul_val = st.number_input("心跳 (Pulse)", min_value=0, value=tp if tp else 70)
        
        context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
        notes = st.text_input("備註")
        
        if st.form_submit_button("📝 儲存紀錄至 Google Sheet"):
            worksheet.append_row([
                str(date_val), 
                time_val.strftime("%H:%M"), 
                sys_val, 
                dia_val, 
                pul_val, 
                context, 
                notes
            ])
            st.balloons()
            # 清除套用的暫存數據
            for k in ['sys_input', 'dia_input', 'pul_input']:
                st.session_state.pop(k, None)
            st.rerun()

except Exception as e:
    st.error(f"系統運行中...")
