import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="健康語音助手", layout="centered")
st.title("📊 數據倉庫狀態")

def get_conn():
    # 取得 Secrets
    s = st.secrets["connections"]["gsheets"]
    
    # 建構連線資訊字典 (排除掉 type，因為 st.connection 已經指定了)
    conn_info = {
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
    
    # 關鍵修正：這裡的 type=GSheetsConnection 就已經告訴 Streamlit 是什麼種類了
    return st.connection("gsheets", type=GSheetsConnection, **conn_info)

try:
    conn = get_conn()
    # 試著讀取一下 (這會觸發真正的 Google 驗證)
    df = conn.read()
    st.success("✅ 雲端倉庫連線成功！")
    
    st.write(f"目前紀錄筆數：{len(df)}")
    
    if st.button("🚀 寫入測試數據"):
        test_entry = pd.DataFrame([{
            "Date": "2026-04-25", "Time": "02:40",
            "Systolic": 120, "Diastolic": 80, "Pulse": 70,
            "Context": "連線大成功", "Notes": "地基打好了！"
        }])
        updated_df = pd.concat([df, test_entry], ignore_index=True)
        conn.update(data=updated_df)
        st.balloons()
        st.success("寫入成功！請檢查 Google Sheets。")

except Exception as e:
    st.error("❌ 連線仍有問題")
    st.exception(e)
