import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz
import time

st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- CSS 視覺優化 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { 
        width: 100%; height: 3.5em; font-size: 18px !important; font-weight: bold; 
        background-color: #28a745 !important; color: white !important; border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 1. GitHub 核心函數 ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"
CSV_HEADER = "日期,時間,高壓,低壓,心跳,情境"

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
            # 如果 CSV 不存在或完全沒內容，初始化它
            if content is None or len(content.strip()) == 0:
                content = CSV_HEADER
            
            new_line = f"{date_v},{time_v.strftime('%H:%M')},{s_val},{d_val},{p_val},{context}"
            updated = content.strip() + "\n" + new_line
            if up_gh(updated, sha, "Add record"):
                st.success("✅ 儲存成功！")
                time.sleep(1)
                st.rerun()

st.divider()

# --- 3. 數據分析與圖表區 ---
try:
    csv_raw_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?c={time.time()}"
    # 讀取時強制指定欄位名稱，防止 CSV 標題錯誤導致無法繪圖
    df = pd.read_csv(csv_raw_url)
    
    if len(df) > 0:
        # 統一欄位名稱（防呆處理）
        df.columns = ["日期", "時間", "高壓", "低壓", "心跳", "情境"]
        df = df.dropna(subset=['高壓', '低壓', '心跳'])
        
        # 日期處理
        df['日期格式'] = pd.to_datetime(df['日期'])
        df = df.sort_values(by=['日期格式', '時間'])

        # 圖表顯示
        st.subheader("📈 趨勢分析")
        chart_df = df[['日期格式', '高壓', '低壓', '心跳']].copy()
        # 建立時間軸標籤
        df['時間點'] = df['日期格式'].dt.strftime('%m/%d') + " " + df['時間']
        chart_df.index = df['時間點']
        st.line_chart(chart_df[['高壓', '低壓', '心跳']])

        # 明細顯示
        st.write("📊 最近紀錄")
        df_display = df.tail(10).copy()
        df_display['日期'] = df_display['日期格式'].dt.strftime('%Y-%m-%d')
        
        cfg = {
            "日期": st.column_config.TextColumn("日期", width=90),
            "時間": st.column_config.TextColumn("時間", width=60),
            "高壓": st.column_config.NumberColumn("高壓", width=50),
            "低壓": st.column_config.NumberColumn("低壓", width=50),
            "心跳": st.column_config.NumberColumn("心跳", width=50),
            "情境": st.column_config.TextColumn("情境", width=60)
        }
        
        styled = df_display.iloc[::-1].style.map(lambda v: 'color: red' if isinstance(v, (int, float)) and v >= 140 else '', subset=['高壓'])\
                                           .map(lambda v: 'color: red' if isinstance(v, (int, float)) and v >= 90 else '', subset=['低壓'])
        
        st.dataframe(styled, hide_index=True, column_config=cfg)
    else:
        st.info("尚未偵測到數據。")

except Exception as e:
    st.info("正在等待第一筆有效數據產生圖表...")

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
