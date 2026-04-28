import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz
import re

# 設定網頁標題
st.set_page_config(page_title="Wynter 健康紀錄助手", layout="centered")

# --- 背景樣式 (保留你的原始設定) ---
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { width: 100%; height: 3.2em; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">❤️ 血壓健康紀錄助手 (GitHub 版)</p>', unsafe_allow_html=True)

# --- 1. GitHub 連線參數 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]  # 格式如: "nomi53875-byte/health-voice-tracker"
    FILE_PATH = "data.csv"
except:
    st.error("⚠️ 尚未在 Streamlit Secrets 中設定 GITHUB_TOKEN 或 REPO_NAME")
    st.stop()

# --- 2. 讀寫核心函數 ---
def save_to_github(new_data_row):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 抓取舊資料
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        st.error("讀取資料檔失敗，請確認 data.csv 是否已建立且 Token 權限正確。")
        return False
    
    content = r.json()
    old_csv_content = base64.b64decode(content['content']).decode('utf-8')
    sha = content['sha']
    
    # 合併新資料
    new_csv_content = old_csv_content.strip() + "\n" + ",".join(map(str, new_data_row))
    
    # 推送更新
    payload = {
        "message": f"Log health data {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(new_csv_content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code == 200

# --- 3. 介面區塊 ---
# (保留你的切換設定區塊，雖然現在是用 CSV，但留著結構讓你之後擴充)
with st.expander("⚙️ 系統資訊"):
    st.write(f"目前儲存庫：{REPO_NAME}")
    st.write(f"目標檔案：{FILE_PATH}")

manual_mode = st.toggle("切換輸入模式 (手動/預設)", value=True)

with st.form("health_form", clear_on_submit=True):
    taipei_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taipei_tz)
    
    c1, c2 = st.columns(2)
    with c1: date_val = st.date_input("日期", now.date())
    with c2: time_val = st.time_input("時間", now.time())
    
    st.divider()
    
    # 這裡實作你需要的「三次測量」邏輯
    st.write("### 📥 血壓測量數據")
    
    # 根據你的需求，這裡維持垂直排列，確保手機好點擊
    col_sys, col_dia = st.columns(2)
    with col_sys:
        st.markdown("**高壓 (收縮壓)**")
        s1 = st.number_input("第一次測量", min_value=0, max_value=250, value=120 if not manual_mode else None)
        s2 = st.number_input("第二次測量", min_value=0, max_value=250, value=120 if not manual_mode else None)
        s3 = st.number_input("第三次測量", min_value=0, max_value=250, value=120 if not manual_mode else None)
    
    with col_dia:
        st.markdown("**低壓 (舒張壓)**")
        d1 = st.number_input("第一次測量 ", min_value=0, max_value=150, value=80 if not manual_mode else None)
        d2 = st.number_input("第二次測量 ", min_value=0, max_value=150, value=80 if not manual_mode else None)
        d3 = st.number_input("第三次測量 ", min_value=0, max_value=150, value=80 if not manual_mode else None)
    
    pul_val = st.number_input("心跳 (Pulse)", min_value=0, max_value=200, value=70 if not manual_mode else None)
    
    context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
    notes = st.text_input("備註", placeholder="感覺...")
    
    submit_button = st.form_submit_button(label="📝 計算並儲存紀錄")

if submit_button:
    # 邏輯判斷與平均計算
    try:
        # 如果是手動模式且沒填，給予預設或報錯
        vals = [s1, s2, s3, d1, d2, d3]
        if any(v is None for v in vals):
            st.error("請填寫完整的三次測量數值！")
        else:
            avg_sys = round((s1 + s2 + s3) / 3, 1)
            avg_dia = round((d1 + d2 + d3) / 3, 1)
            
            # 準備存入 CSV 的資料列
            new_row = [
                str(date_val), 
                time_val.strftime("%H:%M"), 
                avg_sys, 
                avg_dia, 
                pul_val, 
                context, 
                notes
            ]
            
            if save_to_github(new_row):
                st.balloons()
                st.success(f"✅ 已存入 GitHub！平均血壓為：{avg_sys} / {avg_dia}")
            else:
                st.error("儲存失敗，請檢查網路或 Token。")
    except Exception as e:
        st.error(f"發生錯誤：{e}")

# --- 4. 歷史紀錄預覽 ---
st.divider()
st.write("📊 歷史紀錄 (最後 5 筆)")
try:
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
    # 加入 timestamp 避免快取問題
    df = pd.read_csv(f"{csv_url}?t={datetime.now().timestamp()}")
    st.dataframe(df.tail(5), use_container_width=True)
except:
    st.info("目前尚無資料或檔案讀取中...")
