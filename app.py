import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="健康語音助手測試", layout="centered")
st.title("📊 倉庫連線測試")

try:
    # 建立與 Google Sheets 的連線
    conn = st.connection("gsheets", type=GSheetsConnection)

    st.success("✅ 雲端設定讀取成功！")

    if st.button("寫入第一筆測試紀錄"):
        # 取得現有資料
        existing_data = conn.read()

        # 建立測試資料
        test_entry = pd.DataFrame([{
            "Date": "2026-04-24",
            "Time": "23:55",
            "Systolic": 120,
            "Diastolic": 80,
            "Pulse": 70,
            "Context": "連線測試",
            "Notes": "GitHub 部署成功！"
        }])

        # 合併並更新
        updated_df = pd.concat([existing_data, test_entry], ignore_index=True)
        conn.update(data=updated_df)

        st.balloons()
        st.success("成功！請查看您的 Google Sheets。")

except Exception as e:
    st.error(f"連線失敗，請確認 Streamlit Cloud 的 Secrets 是否已設定。錯誤: {e}")
