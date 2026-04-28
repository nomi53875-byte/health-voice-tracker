import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz
import time
from io import StringIO

st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- CSS 視覺優化 ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { 
        width: 100%; height: 3.5em; font-size: 18px !important; font-weight: bold; 
        background-color: #28a745 !important; color: white !important; border-radius: 12px;
    }
    /* 讓側邊欄篩選器更顯眼 */
    section[data-testid="stSidebar"] { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手</p>', unsafe_allow_html=True)

# --- 1. GitHub 核心參數 ---
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

# --- 2. 輸入介面 ---
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

if st.button("🚀 確定儲存紀錄"):
    if s_val is None or d_val is None or p_val is None:
        st.error("⚠️ 請填寫完整數值！")
    else:
        with st.spinner('同步至 GitHub...'):
            content, sha = get_gh()
            new_entry = f"{date_v},{time_v.strftime('%H:%M')},{s_val},{d_val},{p_val},{context}"
            
            if content is None or "日期,時間,高壓,低壓,心跳,情境" not in content:
                full_txt = CSV_HEADER + "\n" + new_entry
            else:
                full_txt = content.strip() + "\n" + new_entry
            
            if up_gh(full_txt, sha, "Update records"):
                st.success("✅ 儲存成功！")
                time.sleep(1.5)
                st.rerun()

st.divider()

# --- 3. 數據分析與分類顯示區 ---
try:
    data_str, _ = get_gh()
    
    if data_str and len(data_str.strip().split('\n')) > 1:
        df = pd.read_csv(StringIO(data_str.strip()), on_bad_lines='skip')
        df = df.iloc[:, :6]
        df.columns = ["日期", "時間", "高壓", "低壓", "心跳", "情境"]
        
        # 數據清理與格式轉換
        for col in ["高壓", "低壓", "心跳"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['日期格式'] = pd.to_datetime(df['日期'])
        df = df.dropna(subset=["高壓"])
        df = df.sort_values(by=['日期格式', '時間'])

        # --- 新增：情境篩選器 ---
        st.subheader("🔍 數據篩選")
        all_contexts = ["全部"] + sorted(df['情境'].unique().tolist())
        selected_context = st.selectbox("選擇要查看的情境", all_contexts)

        # 根據選擇篩選數據
        if selected_context == "全部":
            filtered_df = df
        else:
            filtered_df = df[df['情境'] == selected_context]

        # --- 圖表顯示 ---
        if not filtered_df.empty:
            st.subheader(f"📈 趨勢分析 ({selected_context})")
            chart_data = filtered_df.copy()
            chart_data['時間點'] = chart_data['日期格式'].dt.strftime('%m/%d') + " " + chart_data['時間']
            chart_data = chart_data.set_index('時間點')
            st.line_chart(chart_data[['高壓', '低壓', '心跳']])

            # --- 數據統計分析 ---
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("平均高壓", int(filtered_df['高壓'].mean()))
            with col2: st.metric("平均低壓", int(filtered_df['低壓'].mean()))
            with col3: st.metric("最高心跳", int(filtered_df['心跳'].max()))
        else:
            st.info(f"尚無 '{selected_context}' 的數據。")

        # --- 歷史清單 ---
        st.write("📊 紀錄明細 (由新到舊)")
        df_display = filtered_df.tail(20).copy()
        df_display['日期顯示'] = df_display['日期格式'].dt.strftime('%Y-%m-%d')
        
        cfg = {
            "日期顯示": st.column_config.TextColumn("日期", width=90),
            "時間": st.column_config.TextColumn("時間", width=60),
            "高壓": st.column_config.NumberColumn("高壓", width=50),
            "低壓": st.column_config.NumberColumn("低壓", width=50),
            "心跳": st.column_config.NumberColumn("心跳", width=50),
            "情境": st.column_config.TextColumn("情境", width=70)
        }
        
        final_df = df_display[['日期顯示', '時間', '高壓', '低壓', '心跳', '情境']].iloc[::-1]
        styled = final_df.style.map(lambda v: 'color: red; font-weight: bold' if isinstance(v, (int, float)) and v >= 140 else '', subset=['高壓'])\
                               .map(lambda v: 'color: red; font-weight: bold' if isinstance(v, (int, float)) and v >= 90 else '', subset=['低壓'])
        
        st.dataframe(styled, hide_index=True, column_config=cfg)

    else:
        st.info("📊 目前無歷史數據。")

except Exception as e:
    st.warning("🔄 資料同步中...")

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
