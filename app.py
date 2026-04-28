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
            return base64.decodebytes(res['content'].encode('utf-8')).decode('utf-8'), res['sha']
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
with v3: p_val = st.number_input("心跳
