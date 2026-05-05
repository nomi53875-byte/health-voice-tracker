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
        min-width: 150px; height: 2.8em !important; font-size: 15px !important; 
        font-weight: 500 !important; background-color: #5a7d9a !important; 
        color: white !important; border-radius: 8px; border: none; margin-top: 10px;
    }
    .stButton>button:hover { background-color: #4a667d !important; color: #e0e0e0 !important; }
    [data-testid="stDataFrame"] { font-size: 12px !important; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { padding: 2px 5px !important; }
    [data-testid="stVegaLiteChart"] { touch-action: pan-y !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# 3. GitHub 核心函數 (保持不變)
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
    except: pass
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
with c3: context = st.selectbox("錄入情境", ["日常", "起床", "下班", "睡前", "飯後", "運動"])

st.divider()
v1, v2, v3 = st.columns(3)
with v1: s_val = st.number_input("高壓", min_value=0, max_value=250, value=None, placeholder="120")
with v2: d_val = st.number_input("低壓", min_value=0, max_value=150, value=None, placeholder="80")
with v3: p_val = st.number_input("心跳", min_value=0, max_value=200, value=None, placeholder="70")

if st.button("📝 儲存紀錄"):
    if s_val is None or d_val is None or p_val is None:
        st.error("⚠️ 請填寫完整數值！")
    else:
        with st.spinner('同步中...'):
            content, sha = get_gh()
            new_line = f"{date_v},{time_v.strftime('%H:%M')},{s_val},{d_val},{p_val},{context}"
            full_txt = (content.strip() if content else CSV_HEADER) + "\n" + new_line
            if up_gh(full_txt, sha, "Add entry"):
                st.success("✅ 儲存成功"); time.sleep(1); st.rerun()

st.divider()

# 5. 數據分析與圖表區 (進化版)
try:
    data_str, _ = get_gh()
    if data_str and len(data_str.strip().split('\n')) > 1:
        df = pd.read_csv(StringIO(data_str.strip()), on_bad_lines='skip')
        df.columns = ["日期", "時間", "高壓", "低壓", "心跳", "情境"]
        for col in ["高壓", "低壓", "心跳"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['日期格式'] = pd.to_datetime(df['日期'])
        df = df.dropna(subset=["高壓"]).sort_values(by=['日期格式', '時間'])

        # 控制區
        filter_col1, filter_col2 = st.columns([1, 1])
        with filter_col1:
            all_contexts = ["全部"] + sorted(df['情境'].unique().tolist())
            selected_context = st.selectbox("🔍 篩選情境", all_contexts)
        with filter_col2:
            show_n = st.slider("明細顯示筆數", 10, 200, 30, 10)

        filtered_df = df if selected_context == "全部" else df[df['情境'] == selected_context]

        # --- 進化版圖表邏輯 ---
        st.subheader(f"📈 健康趨勢分析 ({selected_context})")
        
        if not filtered_df.empty:
            # 計算 7 次移動平均線 (過濾雜訊)
            chart_df = filtered_df.copy()
            chart_df['高壓平均'] = chart_df['高壓'].rolling(window=7, min_periods=1).mean()
            chart_df['低壓平均'] = chart_df['低壓'].rolling(window=7, min_periods=1).mean()
            chart_df['時間點'] = chart_df['日期格式'].dt.strftime('%m/%d') + " " + chart_df['時間']
            chart_df = chart_df.set_index('時間點')

            # 使用帶狀圖概念：同時顯示原始點與平均線
            # Streamlit 的 line_chart 會自動幫我們處理多條線
            st.line_chart(chart_df[['高壓', '低壓', '高壓平均', '低壓平均']], color=["#FF4B4B", "#1F77B4", "#FFBABA", "#AEC7E8"])
            st.caption("💡 淺色線為每日數值，深色線為 7 次紀錄移動平均趨勢。")
        else:
            st.info("尚無數據。")

        # 明細表格
        st.subheader(f"📊 紀錄明細 (最近 {show_n} 筆)")
        df_display = filtered_df.tail(show_n).copy()
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
        styled = final_df.style.map(lambda v: 'color: red; font-weight: bold' if isinstance(v, (int, float)) and v >= 140 else '', subset=['高壓'])\
                               .map(lambda v: 'color: red; font-weight: bold' if isinstance(v, (int, float)) and v >= 90 else '', subset=['低壓'])
        st.dataframe(styled, hide_index=True, column_config=cfg, use_container_width=True)

        if st.button("🗑️ 刪除最後一筆"):
            with st.spinner('執行中...'):
                c, s = get_gh()
                if c and len(c.strip().split('\n')) > 1:
                    new_txt = '\n'.join(c.strip().split('\n')[:-1])
                    if up_gh(new_txt, s, "Delete Last"):
                        st.success("已刪除"); time.sleep(1); st.rerun()
    else: st.info("尚無歷史數據。")
except Exception as e: st.warning("🔄 資料同步中...")
