import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- CSS 視覺優化 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { 
        width: 100%; 
        height: 3.5em; 
        font-size: 18px !important; 
        font-weight: bold; 
        background-color: #28a745 !important; 
        color: white !important; 
        border-radius: 12px;
    }
    /* 讓數字輸入框的標籤變小一點，適合並排 */
    div[data-testid="stMarkdownContainer"] p { font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 1. GitHub 核心函數 ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"

def get_gh():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}?t={time.time()}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        res = r.json()
        return base64.b64decode(res['content']).decode('utf-8'), res['sha']
    return None, None

def up_gh(txt, sha, msg):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {"message": msg, "content": base64.b64encode(txt.encode('utf-8')).decode('utf-8'), "sha": sha}
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code == 200

# --- 2. 輸入介面 ---
tz = pytz.timezone('Asia/Taipei')
now = datetime.now(tz)

# 日期時間並排
c1, c2, c3 = st.columns([1.5, 1.2, 1.2])
with c1: date_v = st.date_input("日期", now.date())
with c2: time_v = st.time_input("時間", now.time())
with c3: context = st.selectbox("情境", ["日常", "起床", "下班", "睡前", "飯後"])

st.divider()

# 💡 核心改動：高壓、低壓、心跳橫向並排
# 這樣你只需要在同一個水平線上點擊，手感會接近「跳格」
v1, v2, v3 = st.columns(3)
with v1: s_val = st.number_input("高壓", min_value=0, max_value=250, value=None, placeholder="120")
with v2: d_val = st.number_input("低壓", min_value=0, max_value=150, value=None, placeholder="80")
with v3: p_val = st.number_input("心跳", min_value=0, max_value=200, value=None, placeholder="70")

st.write("") 

if st.button("🚀 確定儲存紀錄"):
    if s_val is None or d_val is None or p_val is None:
        st.error("⚠️ 請填寫完整數值！")
    else:
        with st.spinner('同步中...'):
            content, sha = get_gh()
            if content is not None:
                new_line = f"{date_v},{time_v.strftime('%H:%M')},{s_val},{d_val},{p_val},{context}"
                updated = content.strip() + "\n" + new_line
                if up_gh(updated, sha, "Add entry"):
                    st.success("✅ 儲存成功！")
                    time.sleep(1)
                    st.rerun()

# --- 3. 預覽 ---
st.divider()
try:
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?c={time.time()}"
    df = pd.read_csv(csv_url)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%m-%d') # 日期顯示簡短一點

    cfg = {
        "日期": st.column_config.TextColumn("日期", width=60),
        "時間": st.column_config.TextColumn("時間", width=60),
        "高壓": st.column_config.NumberColumn("高壓", width=50),
        "低壓": st.column_config.NumberColumn("低壓", width=50),
        "心跳": st.column_config.NumberColumn("心跳", width=50),
        "情境": st.column_config.TextColumn("情境", width=60)
    }

    st.write("📊 最近紀錄 (紅字異常)")
    styled = df.tail(5).iloc[::-1].style.map(lambda v: 'color: red' if isinstance(v, (int, float)) and v >= 140 else '', subset=['高壓'])\
                                        .map(lambda v: 'color: red' if isinstance(v, (int, float)) and v >= 90 else '', subset=['低壓'])
    
    st.dataframe(styled, hide_index=True, use_container_width=False, column_config=cfg)
except:
    st.info("尚無資料預覽。")

with st.expander("🗑️ 紀錄管理"):
    if st.button("確認刪除最後一筆"):
        content, sha = get_gh()
        if content:
            lines = [l for l in content.split('\n') if l.strip()]
            if len(lines) > 1:
                updated = '\n'.join(lines[:-1])
                if up_gh(updated, sha, "Delete last"):
                    st.warning("最後一筆已刪除")
                    time.sleep(1)
                    st.rerun()
