import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, timedelta
import pytz
import time

# 設定網頁標題
st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- 1. CSS 視覺修正：鎖定表格寬度與文字置中 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; font-size: 16px; }
    
    /* 核心修正：強制讓表格不撐開，保持靠左緊湊 */
    [data-testid="stDataFrame"] {
        max-width: fit-content !important;
    }
    /* 讓內容文字置中 */
    [data-testid="stDataFrame"] td { text-align: center !important; }
    [data-testid="stDataFrame"] th { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 2. GitHub 連線參數 ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"

# --- 3. 核心功能函數 ---
def get_github_content():
    # 使用時間戳記避免快取
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}?t={time.time()}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        res = r.json()
        return base64.b64decode(res['content']).decode('utf-8'), res['sha']
    return None, None

def update_github_content(new_text, sha, msg):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {
        "message": msg,
        "content": base64.b64encode(new_text.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code == 200

def apply_style(df):
    def high_red(v): return 'color: red' if isinstance(v, (int, float)) and v >= 140 else ''
    def low_red(v): return 'color: red' if isinstance(v, (int, float)) and v >= 90 else ''
    return df.style.map(high_red, subset=['高壓']).map(low_red, subset=['低壓'])

# --- 4. 介面區塊 ---
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
    
    submit = st.form_submit_button("📝 儲存紀錄")

if submit:
    f_sys = sys_val if sys_val is not None else 120
    f_dia = dia_val if dia_val is not None else 80
    f_pul = pul_val if pul_val is not None else 70
    new_data = [str(date_val), time_val.strftime("%H:%M"), f_sys, f_dia, f_pul, context]
    
    text, sha = get_github_content()
    if text is not None:
        updated_text = text.strip() + "\n" + ",".join(map(str, new_data))
        if update_github_content(updated_text, sha, "Add entry"):
            st.success("✅ 已存入！")
            st.rerun()

# 刪除功能：改為更安全的邏輯
with st.expander("🗑️ 紀錄管理"):
    st.write("點擊下方按鈕將刪除最後一筆紀錄。")
    if st.button("確認刪除"):
        text, sha = get_github_content()
        if text:
            lines = [l for l in text.split('\n') if l.strip()]
            if len(lines) > 1:
                final_text = '\n'.join(lines[:-1])
                if update_github_content(final_text, sha, "Delete last"):
                    st.warning("最後一筆已刪除")
                    st.rerun()
            else:
                st.info("無資料可刪")

# --- 5. 表格預覽 ---
st.divider()
try:
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?t={time.time()}"
    df = pd.read_csv(csv_url)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
    
    # 欄位寬度鎖定
    cfg = {
        "日期": st.column_config.TextColumn("日期", width=95),
        "時間": st.column_config.TextColumn("時間", width=65),
        "高壓": st.column_config.NumberColumn("高壓", width=50),
        "低壓": st.column_config.NumberColumn("低壓", width=50),
        "心跳": st.column_config.NumberColumn("心跳", width=50),
        "情境": st.column_config.TextColumn("情境", width=65)
    }

    st.write("📊 最近 5 筆紀錄")
    # 套用 CSS 鎖定寬度
    st.dataframe(apply_style(df.tail(5).iloc[::-1]), hide_index=True, use_container_width=False, column_config=cfg)
    
    if st.button("🔍 讀取六個月內完整紀錄"):
        cut_off = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        f_df = df[df['日期'] >= cut_off].iloc[::-1]
        st.dataframe(apply_style(f_df), hide_index=True, use_container_width=False, column_config=cfg)
except:
    st.info("尚無資料預覽。")
