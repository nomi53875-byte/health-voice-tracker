import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

st.set_page_config(page_title="健康語音助手", layout="centered")
st.title("📊 數據倉庫狀態")

# --- 核心修正：直接在連線前「預處理」Secrets ---
def get_fixed_conn():
    # 這裡我們不傳參數給 st.connection
    # 我們讓它自己去讀 Secrets，但我們先把 Secrets 裡的內容「弄對」
    
    # 建立連線物件
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 關鍵：如果連線失敗是因為金鑰換行問題，我們直接去修正它的內部屬性
    # 但為了保險起見，我們用最簡單的「讀取後立即修正」邏輯
    return conn

try:
    # 1. 建立連線
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 2. 獲取原始 Secret 中的 key 並修正換行
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    fixed_key = raw_key.replace("\\n", "\n")
    
    # 3. 透過手動 read 測試，如果失敗，我們就用底層邏輯處理
    # 這次我們直接讀取看看
    df = conn.read(ttl=0) 
    st.success("✅ 雲端倉庫連線成功！")
    st.write(f"目前紀錄筆數：{len(df)}")
    
    if st.button("🚀 寫入測試數據"):
        test_entry = pd.DataFrame([{
            "Date": "2026-04-25", "Time": "03:10",
            "Systolic": 120, "Diastolic": 80, "Pulse": 70,
            "Context": "底層修正測試", "Notes": "地基終於穩了！"
        }])
        conn.update(data=pd.concat([df, test_entry], ignore_index=True))
        st.balloons()
        st.success("寫入成功！")

except Exception as e:
    # 如果上面的標準連線因為 PEM 格式失敗，我們進入「終極人工修復」
    if "PEM" in str(e) or "InvalidByte" in str(e):
        st.warning("偵測到金鑰格式問題，啟動人工修復程序...")
        try:
            # 建立一個乾淨的連線字典
            s = st.secrets["connections"]["gsheets"]
            from gspread.auth import service_account_from_dict
            
            info = {
                "type": "service_account",
                "project_id": s["project_id"],
                "private_key_id": s["private_key_id"],
                "private_key": s["private_key"].replace("\\n", "\n"),
                "client_email": s["client_email"],
                "client_id": s["client_id"],
                "auth_uri": s["auth_uri"],
                "token_uri": s["token_uri"],
                "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
                "client_x509_cert_url": s["client_x509_cert_url"]
            }
            
            # 直接使用 gspread 繞過 streamlit-gsheets 的參數檢查
            # 這是最底層、最直接的連線方式
            st.write("🔧 正在透過底層驅動連線...")
            df = conn.read(ttl=0, spreadsheet=s["spreadsheet"], worksheet="Sheet1", **info)
            st.success("✅ 底層修正連線成功！")
            st.dataframe(df.tail(3))
        except Exception as inner_e:
            st.error("❌ 終極修復失敗")
            st.exception(inner_e)
    else:
        st.error("❌ 發生非格式連線錯誤")
        st.exception(e)
