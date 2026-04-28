import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, timedelta
import pytz

# --- 基礎網頁設定 ---
st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- CSS 視覺優化：緊湊表格與置中 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; font-size: 16px; }
    /* 讓表格靠左且不撐開 */
    [data-testid="stDataFrame"] { max-width: fit-content !important; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 1. GitHub Secrets 讀取 ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"

# --- 2. 核心讀寫函數 ---
def get_github_file():
    # 讀取檔案內容與 SHA
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        res = r.json()
        return base64.b64decode(res['content']).decode('utf-8'), res['sha']
    return None, None

def update_github_file(new_content, sha, message):
    # 推送內容回 GitHub
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
    # 紅字警示：高壓 >= 140, 低壓 >= 90
    return df.style.map(lambda v: 'color: red' if isinstance(v, (int, float)) and v >= 140 else '', subset=['高壓'])\
                   .map(lambda v: 'color: red' if isinstance(v, (int, float)) and v >= 90 else '', subset=['低壓'])

# --- 3. 輸入介面 ---
manual_mode = st.toggle("切換輸入模式 (手動/預設)", value=True)

with st.form("health_form", clear_on_submit=True):
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    
    c1, c2 = st.columns(2)
    with c1: date_val = st.date_input("日期", now.date())
    with c2: time_val = st.time_input("時間", now.time())
    
    context = st.selectbox("情境", ["日常", "起床", "下班", "睡前", "飯後"])
    st.divider()
    
    if manual_mode:
        sys = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=None, placeholder="120")
        dia = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=None, placeholder="80")
        pul = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=None, placeholder="70")
    else:
        sys = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=120)
        dia = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=80)
        pul = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=70)
    
    if st.form_submit_button("📝 儲存紀錄"):
        if sys is None or dia is None or pul is None:
            st.error("請完整填寫數值")
        else:
            # 1. 抓取舊資料與 SHA
            content, sha = get_github_file()
            if content is not None:
                # 2. 準備新行
                new_row = f"{date_val},{time_val.strftime('%H:%M')},{sys},{dia},{pul},{context}"
                updated_content = content.strip() + "\n" + new_row
                # 3. 更新 GitHub
                if update_github_file(updated_content, sha, "Add entry"):
                    st.success("✅ 已存入！")
                    st.rerun()

# --- 4. 管理與顯示 ---
with st.expander("🗑️ 紀錄管理"):
    if st.button("確認刪除最後一筆"):
        content, sha = get_github_file()
        if content:
            lines = [l for l in content.split('\n') if l.strip()]
            if len(lines) > 1:
                new_content = '\n'.join(lines[:-1])
                if update_github_file(new_content, sha, "Delete last"):
                    st.warning("已刪除最後一筆")
                    st.rerun()

st.divider()

# 顯示歷史表格
try:
    # 加上隨機參數避免快取
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?cache={now.timestamp()}"
    df = pd.read_csv(csv_url)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')

    cfg = {
        "日期": st.column_config.TextColumn("日期", width=95),
        "時間": st.column_config.TextColumn("時間", width=65),
        "高壓": st.column_config.NumberColumn("高壓", width=50),
        "低壓": st.column_config.NumberColumn("低壓", width=50),
        "心跳": st.column_config.NumberColumn("心跳", width=50),
        "情境": st.column_config.TextColumn("情境", width=65)
    }

    st.write("📊 最近 5 筆紀錄")
    st.dataframe(apply_style(df.tail(5).iloc[::-1]), hide_index=True, use_container_width=False, column_config=cfg)

    if st.button("🔍 讀取六個月內完整紀錄"):
        cut_off = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        f_df = df[df['日期'] >= cut_off].iloc[::-1]
        st.dataframe(apply_style(f_df), hide_index=True, use_container_width=False, column_config=cfg)
except:
    st.info("尚無資料預覽。")
