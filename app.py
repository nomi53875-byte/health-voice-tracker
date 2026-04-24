import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="健康語音助手", layout="centered")
st.title("📊 數據倉庫狀態")

# 強制在記憶體中修正 Secrets 的內容
# 這樣 st.connection 內部讀取時就會讀到正確的換行
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    # 我們從 Secrets 讀取出來，修好換行，再放回 Streamlit 的快取中
    fixed_key = st.secrets["connections"]["gsheets"]["private_key"].replace("\\n", "\n")
    
    # 這裡是一個小技巧：雖然 st.secrets 本身不建議動，但我們可以用這招確保連線成功
    try:
        conn = st.connection("gsheets", type=GSheetsConnection, private_key=fixed_key)
        
        # 嘗試讀取
        df = conn.read()
        st.success("✅ 雲端倉庫連線成功！")
        st.write(f"目前紀錄筆數：{len(df)}")
        
        if st.button("🚀 寫入測試數據"):
            test_entry = pd.DataFrame([{
                "Date": "2026-04-25", "Time": "02:55",
                "Systolic": 120, "Diastolic": 80, "Pulse": 70,
                "Context": "環境變數修正測試", "Notes": "地基終於穩了！"
            }])
            conn.update(data=pd.concat([df, test_entry], ignore_index=True))
            st.balloons()
            st.success("寫入成功！")
            
    except Exception as e:
        st.error("❌ 連線過程中發生錯誤")
        st.exception(e)
else:
    st.warning("⚠️ 找不到 Secrets 設定，請確認 Streamlit Cloud 的 Secrets 頁面。")
