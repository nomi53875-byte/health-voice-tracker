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
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 1. GitHub 連線參數 ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"

# --- 2. 核心功能函數 ---
def get_github_data():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json()
        return base64.b64decode(content['content']).decode('utf-8'), content['sha']
    return None, None

def update_github_file(new_content, sha, message):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {
        "message": message,
        "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
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
    old_content, sha = get_github_data()
    if old_content:
        new_content = old_content.strip() + "\n" + ",".join(map(str, new_row))
        if update_github_file(new_content, sha, "Add entry"):
            st.success("✅ 已存入！")
            st.rerun()

# 刪除最後一筆功能
with st.expander("🗑️ 紀錄管理"):
    if st.button("撤銷/刪除最後一筆紀錄"):
        old_content, sha = get_github_data()
        if old_content:
            lines = old_content.strip().split('\n')
            if len(lines) > 1: # 確保不刪到標題
                new_content = '\n'.join(lines[:-1])
                if update_github_file(new_content, sha, "Delete last entry"):
                    st.warning("已刪除最後一筆資料！")
                    st.rerun()

# --- 4. 歷史紀錄預覽 ---
st.divider()
try:
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?t={datetime.now().timestamp()}"
    df = pd.read_csv(csv_url)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
    
    # 設定欄位寬度配置，讓日期不要太長
    col_cfg = {
        "日期": st.column_config.TextColumn("日期", width="small"),
        "時間": st.column_config.TextColumn("時間", width="small"),
        "高壓": st.column_config.NumberColumn("高壓", width="x-small"),
        "低壓": st.column_config.NumberColumn("低壓", width="x-small"),
        "心跳": st.column_config.NumberColumn("心跳", width="x-small"),
        "情境": st.column_config.TextColumn("情境", width="small")
    }

    st.write("📊 最近 5 筆紀錄")
    st.dataframe(apply_style(df.tail(5).iloc[::-1]), hide_index=True, use_container_width=True, column_config=col_cfg)
    
    if st.button("🔍 讀取六個月內完整紀錄"):
        st.write("📋 六個月內完整資料")
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        full_df = df[df['日期'] >= six_months_ago].iloc[::-1]
        st.dataframe(apply_style(full_df), hide_index=True, use_container_width=True, column_config=col_cfg)
        csv_data = full_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 下載此表為 CSV", csv_data, "health_history.csv", "text/csv")
except:
    st.info("尚無資料預覽。")
