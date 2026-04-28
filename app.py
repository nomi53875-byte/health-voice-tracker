# --- 3. 數據與圖表 (縮小顯示) ---
try:
    data_str, _ = get_gh()
    if data_str and len(data_str.strip().split('\n')) > 1:
        df = pd.read_csv(StringIO(data_str.strip()), on_bad_lines='skip')
        df = df.iloc[:, :6]
        df.columns = ["日期", "時間", "高壓", "低壓", "心跳", "情境"]
        for col in ["高壓", "低壓", "心跳"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['日期格式'] = pd.to_datetime(df['日期'])
        df = df.dropna(subset=["高壓"]).sort_values(by=['日期格式', '時間'])

        # 圖表縮小高度
        st.write("📈 趨勢分析")
        chart_data = df.copy()
        chart_data['時間點'] = chart_data['日期格式'].dt.strftime('%m/%d') + " " + chart_data['時間']
        chart_data = chart_data.set_index('時間點')
        st.line_chart(chart_data[['高壓', '低壓', '心跳']], height=180)

        # 明細字體更小、更緊湊
        st.write("📊 紀錄明細")
        df_display = df.tail(15).copy()
        df_display['日期顯示'] = df_display['日期格式'].dt.strftime('%m-%d')
        
        cfg = {
            "日期顯示": st.column_config.TextColumn("日", width=45),
            "時間": st.column_config.TextColumn("時", width=45),
            "高壓": st.column_config.NumberColumn("高", width=35),
            "低壓": st.column_config.NumberColumn("低", width=35),
            "心跳": st.column_config.NumberColumn("脈", width=35),
            "情境": st.column_config.TextColumn("情", width=45)
        }
        
        final_df = df_display[['日期顯示', '時間', '高壓', '低壓', '心跳', '情境']].iloc[::-1]
        styled = final_df.style.map(lambda v: 'color: red; font-weight: bold' if isinstance(v, (int, float)) and v >= 140 else '', subset=['高壓'])\
                               .map(lambda v: 'color: red; font-weight: bold' if isinstance(v, (int, float)) and v >= 90 else '', subset=['低壓'])
        
        # 這裡就是之前出錯的地方，必須完整閉合
        st.dataframe(styled, hide_index=True, column_config=cfg)
    else:
        st.info("資料加載中...")

except Exception as e:
    # 補上錯誤處理區塊
    st.warning("🔄 資料同步中...")

# 刪除功能放入 expander
with st.expander("🗑️"):
    if st.button("確認刪除最後一筆"):
        c, s = get_gh()
        if c:
            lines = [l for l in c.split('\n') if l.strip()]
            if len(lines) > 1:
                if up_gh('\n'.join(lines[:-1]), s, "Del"):
                    st.success("已刪除")
                    time.sleep(1)
                    st.rerun()
