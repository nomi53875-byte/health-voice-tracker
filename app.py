import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, timedelta
import pytz

# --- 基礎網頁設定 ---
st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- CSS 視覺優化 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; font-size: 16px; }
    [data-testid="stDataFrame"] { max-width: fit-content !important; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 1. GitHub Secrets ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"

# --- 2. 核心函數 ---
def get_gh():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            return base64.b64decode(res['content']).decode('utf-8'), res['sha']
    except:
        pass
    return None, None

def up_gh(txt, sha, msg):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {"message": msg, "content": base64.b64encode(txt.encode('utf-8')).decode('utf-8'), "sha": sha}
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code == 200

# --- 3. 輸入介面 ---
manual_mode = st.toggle("手動輸入模式 (開啟則清空數值)", value=True)

# 移除 clear_on_submit，改由程式邏輯控制清空
with st.form("health_form"):
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    c1, c2 = st.columns(2)
    with c1: date_v = st.date_input("日期", now.date())
    with c2: time_v = st.time_input("時間", now.time())
    context = st.selectbox("情境", ["日常", "起床", "下班", "睡前", "飯後"])
    st.divider()
    
    if manual_mode:
        s_in = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=None, placeholder="120")
        d_in = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=None, placeholder="80")
        p_in = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=None, placeholder="70")
    else:
        s_in = st.number_input("收縮壓 (高壓)", min_value=0, max_value=250, value=120)
        d_in = st.number_input("舒張壓 (低壓)", min_value=0, max_value=150, value=80)
        p_in = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=70)
    
    submit_clicked = st.form_submit_button("📝 儲存紀錄")

# 儲存邏輯移到 Form 外，確保變數穩定
if submit_clicked:
    with st.spinner('正在同步至 GitHub...'):
        fs = s_in if s_in is not None else 0
        fd = d_in if d_in is not None else 0
        fp = p_in if p_in is not None else 0
        
        content, sha = get_gh()
        if content is not None:
            new_line = f"{date_v},{time_v.strftime('%H:%M')},{fs},{fd},{fp},{context}"
            updated = content.strip() + "\n" + new_line
            if up_gh(updated, sha, "Add data"):
                st.success("✅ 儲存成功！")
                # 儲存成功後重整網頁，達到自動清空效果
                st.rerun()
            else:
                st.error("連線 GitHub 失敗，請稍後再試。")

# --- 4. 管理與預覽 ---
with st.expander("🗑️ 紀錄管理"):
    if st.button("確認刪除最後一筆"):
        content, sha = get_gh()
        if content:
            lines = [l for l in content.split('\n') if l.strip()]
            if len(lines) > 1:
                updated = '\n'.join(lines[:-1])
                if up_gh(updated, sha, "Delete"):
                    st.warning("已刪除最後一筆")
                    st.rerun()

st.divider()

try:
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?c={datetime.now().timestamp()}"
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
    styled = df.tail(5).iloc[::-1].style.map(lambda v: 'color: red' if isinstance(v, (int, float)) and v >= 140 else '', subset=['高壓'])\
                                        .map(lambda v: 'color: red' if isinstance(v, (int, float)) and v >= 90 else '', subset=['低壓'])
    
    st.dataframe(styled, hide_index=True, use_container_width=False, column_config=cfg)
except:
    st.info("尚無資料預覽。")
