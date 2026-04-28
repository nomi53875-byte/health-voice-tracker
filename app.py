import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz

# --- 基礎設定 ---
st.set_page_config(page_title="Wynter's 健康助手", layout="centered")

# 從 Secrets 讀取 GitHub 資訊
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    FILE_PATH = "data.csv"
except:
    st.error("❌ 尚未在 Streamlit Cloud 設定 Secrets！")
    st.stop()

# --- 讀寫 GitHub 的核心函數 ---
def save_to_github(new_data_row):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 1. 抓取舊資料
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        st.error(f"讀取 CSV 失敗，請檢查 Token 權限與檔案路徑。錯誤代碼：{r.status_code}")
        return
    
    content = r.json()
    old_csv_content = base64.b64decode(content['content']).decode('utf-8')
    sha = content['sha']
    
    # 2. 合併新資料 (轉換為 CSV 格式的一行)
    new_csv_content = old_csv_content + "\n" + ",".join(map(str, new_data_row))
    
    # 3. 推送回 GitHub
    payload = {
        "message": f"Update health data {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(new_csv_content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=payload)
    if res.status_code == 200:
        st.success("✅ 資料已同步至 GitHub CSV！")
        st.balloons()
    else:
        st.error(f"儲存失敗：{res.text}")

# --- 介面開始 ---
st.title("❤️ 血壓紀錄 (GitHub 穩定版)")

with st.form("health_form", clear_on_submit=True):
    taipei_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taipei_tz)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1: date_val = st.date_input("日期", now.date())
    with col_t2: time_val = st.time_input("時間", now.time())

    st.markdown("### 🩸 收縮壓 (高壓) 三次測量")
    c1, c2, c3 = st.columns(3)
    with c1: s1 = st.number_input("第一次", value=120, key="s1")
    with c2: s2 = st.number_input("第二次", value=120, key="s2")
    with c3: s3 = st.number_input("第三次", value=120, key="s3")
    avg_s = round((s1+s2+s3)/3, 1)

    st.markdown("### 🩸 舒張壓 (低壓) 三次測量")
    c4, c5, c6 = st.columns(3)
    with c4: d1 = st.number_input("第一次", value=80, key="d1")
    with c5: d2 = st.number_input("第二次", value=80, key="d2")
    with c6: d3 = st.number_input("第三次", value=80, key="d3")
    avg_d = round((d1+d2+d3)/3, 1)

    context = st.selectbox("情境", ["一般", "起床", "下班", "睡前", "飯後"])
    notes = st.text_input("備註")
    
    if st.form_submit_button("📝 儲存紀錄"):
        new_row = [date_val, time_val.strftime("%H:%M"), s1, s2, s3, avg_s, d1, d2, d3, avg_d, context, notes]
        save_to_github(new_row)

st.divider()
st.write("📊 歷史紀錄預覽")
# 讀取並顯示 CSV 的最後幾筆 (可選功能)
try:
    data_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
    df = pd.read_csv(data_url)
    st.dataframe(df.tail(5), use_container_width=True)
except:
    st.write("尚無歷史資料。")
