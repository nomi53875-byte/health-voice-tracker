import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz

# 設定網頁標題
st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- 背景樣式 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 1. GitHub 連線參數 ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"

# --- 2. 讀寫核心函數 ---
def save_to_github(new_data_row):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        st.error("讀取資料檔失敗，請確認 GitHub 倉庫中已建立 data.csv 檔案。")
        return False
    
    content = r.json()
    old_csv_content = base64.b64decode(content['content']).decode('utf-8')
    sha = content['sha']
    
    # 合併新資料
    new_csv_content = old_csv_content.strip() + "\n" + ",".join(map(str, new_data_row))
    
    payload = {
        "message": f"Log data {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(new_csv_content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code == 200

# --- 3. 介面區塊 ---
manual_mode = st.toggle("切換輸入模式 (手動/預設)", value=True)

with st.form("health_form", clear_on_submit=True):
    taipei_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taipei_tz)
    
    c1, c2 = st.columns(2)
    with c1: date_val = st.date_input("日期", now.date())
    with c2: time_val = st.time_input("時間", now.time())
    
    # 依照要求：將「情境」移至時間與收縮壓之間
    context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
    
    st.divider()
    
    if manual_mode:
        sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=None, placeholder="120")
        dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=None, placeholder="80")
        pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=None, placeholder="70")
    else:
        sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=120)
        dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=80)
        pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=70)
    
    notes = st.text_input("備註", placeholder="感覺...")
    
    submit_button = st.form_submit_button(label="📝 儲存紀錄")

if submit_button:
    f_sys = sys_val if sys_val is not None else 120
    f_dia = dia_val if dia_val is not None else 80
    f_pul = pul_val if pul_val is not None else 70
    
    new_row = [str(date_val), time_val.strftime("%H:%M"), f_sys, f_dia, f_pul, context, notes]
    
    if save_to_github(new_row):
        st.success(f"✅ 已存入 GitHub！({f_sys}/{f_dia})")
        st.balloons()
        # 強制重新導向以更新下方表格內容
        st.rerun()

# --- 4. 歷史紀錄預覽 ---
st.divider()
st.write("📊 歷史紀錄 (最後 5 筆)")
try:
    # 加上隨機參數避免 GitHub Raw 的快取延遲
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?t={datetime.now().timestamp()}"
    df = pd.read_csv(csv_url)
    if not df.empty:
        st.dataframe(df.tail(5), use_container_width=True)
    else:
        st.write("檔案內尚無資料。")
except Exception as e:
    st.info("尚未讀取到資料。請確認 GitHub 倉庫中的 data.csv 是否已正確建立標題行。")
