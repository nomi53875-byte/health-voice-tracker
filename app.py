import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz
import time
from io import StringIO

# 1. 網頁配置
st.set_page_config(page_title="Wynter 健康助手", layout="centered")

# 2. 視覺優化
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 15px; }
    
    .stButton>button { 
        min-width: 150px; 
        height: 2.8em !important; 
        font-size: 15px !important; 
        font-weight: 500 !important; 
        background-color: #5a7d9a !important; 
        color: white !important; 
        border-radius: 8px;
        border: none;
        padding: 0px 20px !important;
        margin-top: 10px;
    }
    
    .stButton>button:hover {
        background-color: #4a667d !important;
        color: #e0e0e0 !important;
    }

    [data-testid="stDataFrame"] { 
        font-size: 12px !important; 
    }
    
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        padding: 2px 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# 3. GitHub 核心函數
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"
CSV_HEADER = "日期,時間,高壓,低壓,心跳,情境"

def get_gh():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}?nocache={time.time()}"
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

# 4. 資料輸入區
tz = pytz.timezone('Asia/Taipei')
now = datetime.now(tz)

c1, c2, c3 = st.columns([1.5, 1.2, 1.2])
with c1: date_v = st.date_input("日期", now.date())
with c2: time_v = st.time_input("時間", now.time())
with c3: context = st.selectbox("錄入情境", ["日常", "起床", "下班", "睡前", "飯後", "運動後"])

st.divider()

v1, v2, v3 = st.columns(3)
with v1: s_val = st.number_input("高壓", min_value=0, max_value=250, value=None, placeholder="120")
with v2: d_val = st.number_input("低壓", min_value=0, max_value=150, value=None, placeholder="80")
with v3: p_val = st.number_input("心跳", min_value=0, max_value=200, value=None, placeholder="70")

if st.button("📝 儲存健康紀錄"):
    if s_val is None or d_val is None or p_val is None:
        st.error("⚠️ 請填寫完整數值！")
    else:
        with st.spinner('同步中...'):
            content, sha = get_gh()
            new_line = f"{date_v},{time_v.strftime('%H:%M')},{s_val},{d_val},{p_val},{context}"
            if content is None or "日期" not in content:
                full_txt = CSV_HEADER + "\n" + new_line
            else:
                full_txt = content.strip() + "\n" + new_line
            if up_gh(full_txt, sha, "Add entry"):
                st.success("✅ 儲存成功")
                time.sleep(1)
                st.rerun()

st.divider()

# 5. 數據分析與圖表區 (含情境篩選)
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

        # --- 新增：情境篩選功能 ---
        all_contexts = ["全部顯示"] + sorted(df['情境'].unique().tolist())
        selected_context = st.selectbox("🔍 篩選顯示情境", all_contexts)

        if selected_context == "全部顯示":
            filtered_df = df
        else:
            filtered_df = df[df['情境'] == selected_context]

        # 圖表顯示
        st.subheader(f"📈 趨勢分析 ({selected_context})")
        if not filtered_df.empty:
            chart_data = filtered_df.copy()
            chart_data['時間點'] = chart_data['日期格式'].dt.strftime('%m/%d') + " " + chart_data['時間']
            chart_data = chart_data.set_index('時間點')
            st.line_chart(chart_data[['高壓', '低壓', '心跳']])
        else:
            st.info("尚無該情境的數據。")

        # 明細表格
        st.subheader("📊 紀錄明細")
        df_display = filtered_df.tail(20).copy()
        df_display['顯示日期'] = df_display['日期格式'].dt.strftime('%m-%d')
        
        cfg = {
            "顯示日期": st.column_config.TextColumn("日期", width=60),
            "時間": st.column_config.TextColumn("時間", width=60),
            "高壓": st.column_config.NumberColumn("高壓", width=50),
            "低壓": st.column_config.NumberColumn("低壓", width=50),
            "心跳": st.column_config.NumberColumn("心跳", width=50),
            "情境": st.column_config.TextColumn("情境", width=60)
        }
        
        final_df = df_display[['顯示日期', '時間', '高壓', '低壓', '心跳', '情境']].iloc[::-1]
        styled =
