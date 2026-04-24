import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="健康語音助手", layout="centered")
st.title("📊 數據倉庫狀態")

# 初始化連線變數
connection_success = False

try:
    # 1. 嘗試最標準的連線
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    st.success("✅ 雲端倉庫連線成功！")
    connection_success = True
    
except Exception as e:
    # 2. 如果標準連線失敗，啟動人工修復
    st.warning("偵測到金鑰格式問題，啟動人工修復程序...")
    
    try:
        # 獲取 Secrets
        s = st.secrets["connections"]["gsheets"]
        
        # 建立修復過的資訊字典
        info = {
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
        
        # 重新建立一個「純淨」的連線，不帶任何預設參數
        # 我們直接把修好的 info 塞進去
        st.write("🔧 正在透過底層驅動重新嘗試...")
        
        # 重新定義 conn 以修復 NameError
        conn = st.connection("gsheets_fixed", type=GSheetsConnection, **info)
        df = conn.read(spreadsheet=s["spreadsheet"])
        
        st.success("✅ 底層修正連線成功！")
        connection_success = True
        
    except Exception as inner_e:
        st.error("❌ 終極修復失敗")
        st.exception(inner_e)

# 3. 如果連線成功，顯示資料與寫入按鈕
if connection_success:
    st.write(f"目前紀錄筆數：{len(df)}")
    st.dataframe(df.tail(3))
    
    if st.button("🚀 寫入測試數據"):
        try:
            test_entry = pd.DataFrame([{
                "Date": "2026-04-25", "Time": "03:20",
                "Systolic": 120, "Diastolic": 80, "Pulse": 70,
                "Context": "NameError修正測試", "Notes": "這次真的定義了！"
            }])
            new_df = pd.concat([df, test_entry], ignore_index=True)
            conn.update(data=new_df, spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"])
            st.balloons()
            st.success("寫入成功！")
        except Exception as write_e:
            st.error(f"寫入失敗：{write_e}")
