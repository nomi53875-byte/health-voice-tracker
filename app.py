import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, timedelta
import pytz

# 設定網頁標題
st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- 背景樣式 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; font-size: 16px; }
    .stDataFrame { font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 1. GitHub 連線參數 ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"

# --- 2. 核心功能函數 ---
def save_to_github(new_data_row):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200: return False
    content = r.json()
    old_csv_content = base64.b64decode(content['content']).decode('utf-8')
    sha = content['sha']
    new_csv_content = old_csv_content.strip() + "\n" + ",".join(map(str, new_data_row))
    payload = {
        "message": f"Log data {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(new_csv_content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code == 200

def apply_style(df):
    def highlight_high(val):
        return 'color: red' if isinstance(val, (int, float)) and val >= 140 else ''
    def highlight_low(val):
        return 'color: red' if isinstance(val, (int, float)) and val >= 90 else ''
    return df.style.map(highlight_high, subset=['高壓']).map(highlight_low, subset=['低壓'])

# --- 3. 介面區塊 ---
manual_mode = st.toggle("切換輸入模式 (手動/預設)", value=True)

with st.form("health_form", clear_on_submit=True):
    taipei_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taipei_tz)
    
    c1, c2 = st.columns(2)
    with c1: date_val = st.date_input("日期", now.date())
    with c2: time_val = st.time_input("時間", now.time())
    
    context = st.selectbox("情境", ["日常", "起床", "下班", "睡前", "飯後"])
    st.divider()
    
    if manual_mode:
        sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=None, placeholder="120")
        dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=None, placeholder="80")
        pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=None, placeholder="70")
    else:
        sys_val = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=120)
        dia_val = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=80)
        pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=70)
    
    submit_button = st.form_submit_button(label="📝 儲存紀錄")

if submit_button:
    f_sys = sys_val if sys_val is not None else 120
    f_dia = dia_val if dia_val is not None else 80
    f_pul = pul_val if pul_val is not None else 70
    new_row = [str(date_val), time_val.strftime("%H:%M"), f_sys, f_dia, f_pul, context]
    if save_to_github(new_row):
        st.success(f"✅ 已存入！")
        st.rerun()

# --- 4. 歷史紀錄預覽 ---
st.divider()
try:
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?t={datetime.now().timestamp()}"
    df = pd.read_csv(csv_url)
    
    # 修正 1：移除無意義的 Unnamed 欄位
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # 修正 2：強制日期格式為純日期字串，避免出現 00:00:00
    df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
    
    st.write("📊 最近 5 筆紀錄 (異常數值顯示 :red[紅色])")
    # 只取最後 5 筆並倒序
    recent_df = df.tail(5).iloc[::-1]
    st.dataframe(apply_style(recent_df), hide_index=True, use_container_width=True)
    
    if st.button("🔍 讀取六個月內完整紀錄"):
        st.write("📋 六個月內完整資料")
        # 過濾六個月內的資料
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        full_df = df[df['日期'] >= six_months_ago].iloc[::-1]
        st.dataframe(apply_style(full_df), hide_index=True, use_container_width=True)
        
        csv_data = full_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 下載此表為 CSV", csv_data, "health_history.csv", "text/csv")
except Exception as e:
    st.info("尚無資料預覽。")
