import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, timedelta
import pytz
import time

# 設定網頁標題
st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- 背景樣式優化 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; font-size: 16px; }
    /* 讓表格內的文字緊湊並置中 */
    div[data-testid="stDataFrame"] td { text-align: center !important; }
    div[data-testid="stDataFrame"] th { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 1. GitHub 連線參數 ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"

# --- 2. 核心功能函數 (加入延遲處理) ---
def get_github_data_fresh():
    # 使用隨機參數 t 確保不抓到快取資料
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}?t={time.time()}"
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
    # 數值顯色邏輯
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
    old_content, sha = get_github_data_fresh()
    if old_content:
        # 確保不會因為空行造成格式混亂
        clean_content = old_content.strip()
        new_content = clean_content + "\n" + ",".join(map(str, new_row))
        if update_github_file(new_content, sha, "Add entry"):
            st.success("✅ 已存入！")
            time.sleep(1) # 給予 GitHub 小段同步時間
            st.rerun()

with st.expander("🗑️ 紀錄管理"):
    if st.button("確認刪除最後一筆資料"):
        # 強制抓取當下最真實的檔案內容
        old_content, sha = get_github_data_fresh()
        if old_content:
            lines = [line for line in old_content.split('\n') if line.strip()] # 過濾空行
            if len(lines) > 1:
                new_content = '\n'.join(lines[:-1])
                if update_github_file(new_content, sha, "Manual delete"):
                    st.warning("資料已刪除，更新中...")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("目前只有標題行，無資料可刪。")

# --- 4. 歷史紀錄預覽 ---
st.divider()
try:
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?t={time.time()}"
    df = pd.read_csv(csv_url)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
    
    # 💡 更精細的寬度控制，解決空白過多問題
    col_cfg = {
        "日期": st.column_config.TextColumn("日期", width=90),
        "時間": st.column_config.TextColumn("時間", width=60),
        "高壓": st.column_config.NumberColumn("高壓", width=50),
        "低壓": st.column_config.NumberColumn("低壓", width=50),
        "心跳": st.column_config.NumberColumn("心跳", width=50),
        "情境": st.column_config.TextColumn("情境", width=60)
    }

    st.write("📊 最近 5 筆紀錄")
    st.dataframe(
        apply_style(df.tail(5).iloc[::-1]), 
        hide_index=True, 
        use_container_width=False, 
        column_config=col_cfg
    )
    
    if st.button("🔍 讀取六個月內完整紀錄"):
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        full_df = df[df['日期'] >= six_months_ago].iloc[::-1]
        st.dataframe(apply_style(full_df), hide_index=True, use_container_width=False, column_config=col_cfg)
except:
    st.info("尚無資料預覽。")
