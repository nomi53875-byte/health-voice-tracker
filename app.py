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

c1, c2, c3 = st.columns([1.5, 1.2, 1.2])
with c1: date_v = st.date_input("日期", now.date())
with c2: time_v = st.time_input("時間", now.time())
with c3: context = st.selectbox("情境", ["日常", "起床", "下班", "睡前", "飯後"])

st.divider()

v1, v2, v3 = st.columns(3)
with v1: s_val = st.number_input("高壓", min_value=0, max_value=250, value=None, placeholder="120")
with v2: d_val = st.number_input("低壓", min_value=0, max_value=150, value=None, placeholder="80")
with v3: p_val = st.number_input("心跳", min_value=0, max_value=200, value=None, placeholder="70")

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

st.divider()

# --- 3. 數據分析與圖表區 ---
try:
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?c={time.time()}"
    df = pd.read_csv(csv_url)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df['日期'] = pd.to_datetime(df['日期'])
    
    # 畫圖用的數據處理
    df_chart = df.copy()
    df_chart = df_chart.sort_values('日期')
    # 建立一個合併日期與時間的欄位，讓圖表軸更精確
    df_chart['時間點'] = df_chart['日期'].dt.strftime('%m/%d') + " " + df_chart['時間']
    df_chart = df_chart.set_index('時間點')

    # 顯示圖表
    st.subheader("📈 血壓趨勢分析 (最近 30 筆)")
    chart_data = df_chart[['高壓', '低壓', '心跳']].tail(30)
    st.line_chart(chart_data)

    # 顯示表格
    st.write("📊 最近紀錄明細")
    df['顯示日期'] = df['日期'].dt.strftime('%m-%d')
    cfg = {
        "顯示日期": st.column_config.TextColumn("日期", width=60),
        "時間": st.column_config.TextColumn("時間", width=60),
        "高壓": st.column_config.NumberColumn("高壓", width=50),
        "低壓": st.column_config.NumberColumn("低壓", width=50),
        "心跳": st.column_config.NumberColumn("心跳", width=50),
        "情境": st.column_config.TextColumn("情境", width=60)
    }
    
    display_df = df.tail(10).iloc[::-1] # 顯示最近 10 筆
    styled = display_df.style.map(lambda v: 'color: red' if isinstance(v, (int, float)) and v >= 140 else '', subset=['高壓'])\
                             .map(lambda v: 'color: red' if isinstance(v, (int, float)) and v >= 90 else '', subset=['低壓'])
    
    st.dataframe(styled, hide_index=True, column_config=cfg)

except Exception as e:
    st.info("尚無足夠數據產生圖表。")

with st.expander("🗑️ 管理"):
    if st.button("刪除最後一筆"):
        c, s = get_gh()
        if c:
            lines = [l for l in c.split('\n') if l.strip()]
            if len(lines) > 1:
                if up_gh('\n'.join(lines[:-1]), s, "Del"):
                    st.warning("已刪除")
                    time.sleep(1)
                    st.rerun()
