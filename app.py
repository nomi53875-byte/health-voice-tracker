import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz

# --- 設定 ---
st.set_page_config(page_title="Wynter 健康紀錄", layout="centered")

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.csv"

def save_to_github(new_data_row):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    content = r.json()
    old_csv_content = base64.b64decode(content['content']).decode('utf-8')
    sha = content['sha']
    new_csv_content = old_csv_content + "\n" + ",".join(map(str, new_data_row))
    payload = {
        "message": f"Log Data {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(new_csv_content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    requests.put(url, headers=headers, json=payload)

# --- 介面 ---
st.title("🩸 血壓平均值紀錄")

with st.form("health_form", clear_on_submit=True):
    # 時間設定
    taipei_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taipei_tz)
    date_val = st.date_input("紀錄日期", now.date())
    time_val = st.time_input("紀錄時間", now.time())

    # 輸入區：雖然垂直排，但我們用簡短的標題
    st.divider()
    st.write("### 📥 三次收縮壓 (高壓)")
    s1 = st.number_input("第一次", value=120, key="s1")
    s2 = st.number_input("第二次", value=120, key="s2")
    s3 = st.number_input("第三次", value=120, key="s3")
    
    st.write("### 📥 三次舒張壓 (低壓)")
    d1 = st.number_input("第一次", value=80, key="d1")
    d2 = st.number_input("第二次", value=80, key="d2")
    d3 = st.number_input("第三次", value=80, key="d3")

    st.divider()
    context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
    notes = st.text_input("備註 (選填)")
    
    # 按鈕
    submit = st.form_submit_button("✅ 計算並儲存平均值")

    if submit:
        # 在按下按鈕的瞬間完成計算
        final_sys = round((s1 + s2 + s3) / 3, 1)
        final_dia = round((d1 + d2 + d3) / 3, 1)
        
        # 只存入平均後的資料
        new_row = [date_val, time_val.strftime("%H:%M"), final_sys, final_dia, context, notes]
        save_to_github(new_row)
        st.success(f"紀錄成功！本次平均：{final_sys} / {final_dia}")
        st.balloons()

# --- 顯示歷史 ---
st.divider()
st.write("📊 近期平均趨勢")
try:
    data_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
    df = pd.read_csv(data_url)
    # 只顯示最近 10 筆平均後的結果
    st.dataframe(df.tail(10), use_container_width=True)
except:
    st.write("尚無歷史資料。")
