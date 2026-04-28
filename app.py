import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz
import time
from io import StringIO

st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- 核心視覺優化：字體縮小與版面緊湊 ---
st.markdown("""
    <style>
    .main-title { font-size: 18px !important; font-weight: bold; margin-bottom: 5px; }
    .stButton>button { 
        width: 100%; height: 2.8em; font-size: 14px !important; font-weight: bold; 
        background-color: #28a745 !important; color: white !important; border-radius: 8px;
    }
    /* 關鍵：縮小表格內的字體 */
    [data-testid="stDataFrame"] { 
        font-size: 11px !important; 
        max-width: fit-content !important;
    }
    /* 縮小輸入框標籤字體 */
    div[data-testid="stMarkdownContainer"] p { font-size: 13px !important; margin-bottom: 0px; }
    /* 減少間距 */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康助手</p>', unsafe_allow_html=True)

# --- 1. GitHub 核心函數 (保持不變) ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"
CSV_HEADER = "日期,時間,高壓,低壓,心跳,情境"

def get_gh():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}?nocache={time.time()}"
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

# --- 2. 輸入介面 (緊湊排列) ---
tz = pytz.timezone('Asia/Taipei')
now = datetime.now(tz)

c1, c2, c3 = st.columns([1.2, 1, 1])
with c1: date_v = st.date_input("日期", now.date())
with c2: time_v = st.time_input("時間", now.time())
with c3: context = st.selectbox("情境", ["日常", "起床", "下班", "睡前", "飯後", "運動後"])

v1, v2, v3 = st.columns(3)
with v1: s_val = st.number_input("高壓", min_value=0, max_value=250, value=None, placeholder="120")
with v2: d_val = st.number_input("低壓", min_value=0, max_value=150, value=None, placeholder="80")
with v3: p_val = st.number_input("心跳", min_value=0, max_value=200, value=None, placeholder="70")

if st.button("🚀 儲存紀錄"):
    if s_val is None or d_val is None or p_val is None:
        st.error("⚠️ 請填寫數值")
    else:
        with st.spinner('同步中...'):
            content, sha = get_gh()
            new_entry = f"{date_v},{time_v.strftime('%H:%M')},{s_val},{d_val},{p_val},{context}"
            if content is None or "日期" not in content:
                full_txt = CSV_HEADER + "\n" + new_entry
            else:
                full_txt = content.strip() + "\n" + new_entry
            if up_gh(full_txt, sha, "Add entry"):
                st.success("✅ 成功")
                time.sleep(1)
                st.rerun()

# --- 3. 數據與圖表 (縮小顯示) ---
try:
    data_str, _ = get_gh()
    if data_str and len(data_str.strip().split('\n')) > 1:
        df = pd.read_csv(StringIO(data_str.strip()), on_bad_lines='skip')
        df = df.iloc[:, :6]
        df.columns = ["日期", "時間", "高壓", "低壓", "心跳", "情境"]
        for col in ["高壓", "低壓", "心跳"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['日期格式'] = pd.to_datetime(df['日期'])
        df = df.dropna(subset=["高壓"]).sort_values(by=['日期格式', '時間'])

        # 圖表縮小一點高度
        st.write("📈 趨勢分析")
        chart_data = df.copy()
        chart_data['時間點'] = chart_data['日期格式'].dt.strftime('%m/%d') + " " + chart_data['時間']
        chart_data = chart_data.set_index('時間點')
        st.line_chart(chart_data[['高壓', '低壓', '心跳']], height=180) # 固定高度防止撐開

        # 明細字體更小、更緊湊
        st.write("📊 紀錄明細")
        df_display = df.tail(15).copy()
        df_display['日期顯示'] = df_display['日期格式'].dt.strftime('%m-%d')
        
        # 💡 進一步縮窄欄位寬度
        cfg = {
            "日期顯示": st.column_config.TextColumn("日", width=45),
            "時間": st.column_config.TextColumn("時", width=45),
            "高壓": st.column_config.NumberColumn("高", width=35),
            "低壓": st.column_config.NumberColumn("低", width=35),
            "心跳": st.column_config.NumberColumn("脈", width=35),
            "情境": st.column_config.TextColumn("情", width=45)
        }
        
        final_df = df_display[['日期顯示', '時間', '高壓', '低壓', '心跳', '情境']].iloc[::-1]
        styled = final_df.style.map(lambda v: 'color: red; font-weight: bold' if isinstance(v, (int, float)) and v >= 140 else '', subset=['高壓'])\
                               .map(lambda v: 'color: red; font-weight: bold' if isinstance(v, (int, float)) and v >= 90 else '', subset=['低壓'])
        
        st.dataframe
