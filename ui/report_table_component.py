import streamlit as st
import pandas as pd
from datetime import datetime
from logger import default_logger as logger
from utils.data_utils import get_report_by_symbol, update_report, delete_report
from utils.redis_utils import REPORT_LINK_BLACKLIST_KEY, set_hset

def display_report_table(symbol):
    if len(symbol) > 3:
        # skip this chart for ETF
        return
    reports_data = get_report_by_symbol(symbol)
    # logger.debug(reports_data)
    if reports_data:
        col_report_1, col_report_2 = st.columns([1, 3])
        col_report_2 = col_report_2.container(
            horizontal_alignment="right"
        )
        '###### Báo cáo dự phóng'
        with col_report_1:
            filter_date_report = st.text_input(
                label="xxx", placeholder="Lọc theo ngày báo cáo ...",
                key="filter_date_report", label_visibility='hidden')
        with col_report_2:
            # if st.button("Xóa bộ lọc"):
            #     show_dialog_to_add_link_to_blacklist()
            pass
            # '###### Dữ liệu báo cáo 2'
        df = pd.DataFrame(reports_data)

        # Convert report_date to datetime for filtering
        df['report_date'] = pd.to_datetime(df['report_date'])

        # Apply date filter if filter_date_report is provided
        if filter_date_report:
            try:
                filter_date = pd.to_datetime(filter_date_report)
                df = df[df['report_date'] >= filter_date]
            except ValueError:
                st.warning(
                    "Định dạng ngày không hợp lệ. Vui lòng nhập theo định dạng YYYY-MM-DD.")

        # Store original IDs and data before formatting
        original_ids = df['id'].tolist()
        original_df = df.copy()  # Keep original data for comparison

        df_display = df.copy()

        # Add checkbox column for deletion at the beginning
        df_display.insert(0, 'Xóa', False)

        # Keep numeric columns as numbers for editing (don't format yet)
        # Only format ID as string
        df_display['id'] = df['id'].apply(lambda x: "{:,}".format(int(x)))

        # Ensure numeric columns are actually numeric
        df_display['gia_muc_tieu'] = pd.to_numeric(
            df_display['gia_muc_tieu'], errors='coerce')
        df_display['doanh_thu'] = pd.to_numeric(
            df_display['doanh_thu'], errors='coerce')
        df_display['loi_nhuan_sau_thue'] = pd.to_numeric(
            df_display['loi_nhuan_sau_thue'], errors='coerce')

        # Calculate and display mean for 'doanh_thu' separately since it's a TextColumn
        doanh_thu_mean = int(df['doanh_thu'].mean())
        gia_muc_tieu_mean = round(df['gia_muc_tieu'].mean(), 1)
        loi_nhuan_sau_thue_mean = int(df['loi_nhuan_sau_thue'].mean())
        mean_data = [False, "Mean", "", "", "",
                     gia_muc_tieu_mean,
                     doanh_thu_mean,
                     loi_nhuan_sau_thue_mean,
                     ""]
        footer = pd.DataFrame([mean_data], columns=df_display.columns)
        # Changed ignore_index to True
        report_table = pd.concat([df_display, footer], ignore_index=True)

        # Convert specific columns to string (not numeric ones)
        for col in ['id', 'symbol', 'source', 'link']:
            if col in report_table.columns:
                report_table[col] = report_table[col].apply(str)

        # đổi cột report_date thành ngày dạng string YYYY-MM-DD 
        report_table['report_date'] = pd.to_datetime(report_table['report_date']).dt.strftime('%Y-%m-%d')

        # Convert report_date to string
        # report_table['report_date'] = report_table['report_date'].apply(str)

        # logger.debug(report_table.columns)
        # logger.debug(report_table)

        # Save a copy of the original table for comparison
        original_report_table = report_table.copy()

        # Define highlight function for reports after last dividend event
        last_dividend_time = st.session_state.get("last_dividend_event_time")

        def highlight_new_reports(row):
            if last_dividend_time and row['id'] != "Mean":
                try:
                    r_date = pd.to_datetime(row['report_date'])
                    l_date = pd.to_datetime(last_dividend_time)
                    if r_date > l_date:
                        # Light green highlight for new reports
                        return ['background-color: #d1e7dd; color: #0f5132'] * len(row)
                except Exception:
                    pass
            return [''] * len(row)

        # Initialize editor reset counter in session state
        if 'editor_reset_counter' not in st.session_state:
            st.session_state.editor_reset_counter = 0

        # display the table with checkbox column using data_editor
        # Use counter in key to force reset after save
        edited_df = st.data_editor(
            report_table.style.apply(highlight_new_reports, axis=1),
            column_config={
                "Xóa": st.column_config.CheckboxColumn(
                    "Xóa",
                    help="Chọn để xóa báo cáo",
                    default=False,
                ),
                "id": st.column_config.TextColumn(
                    "ID",
                    width="small",
                ),
                "source": st.column_config.TextColumn("Nguồn"),
                "gia_muc_tieu": st.column_config.NumberColumn(
                    "Giá mục tiêu",
                    format="%.1f",
                ),
                "doanh_thu": st.column_config.NumberColumn(
                    "Doanh thu",
                    format="%d",
                ),
                "loi_nhuan_sau_thue": st.column_config.NumberColumn(
                    "LNST",
                    format="%d",
                ),
                "link": st.column_config.LinkColumn("Link", help="Báo cáo chi tiết"),
                "report_date": st.column_config.TextColumn("Ngày báo cáo", help="Ngày phát hành báo cáo"),
            },
            hide_index=True,
            # use_container_width=True,
            # Set max height to 800px to prevent excessively tall tables
            height=min(35 * len(report_table) + 35, 800),
            width='content',
            disabled=["id", "symbol"],  # Only disable id and symbol columns
            num_rows="fixed",  # Prevent adding/deleting rows
            # Dynamic key to reset state
            key=f"report_table_editor_{st.session_state.editor_reset_counter}"
        )

        # Add buttons for save and blacklist/delete (aligned to the right)
        col_btn_1, col_btn_2 = st.columns([3, 1])

        with col_btn_1:
            if st.button("💾 Lưu thay đổi", type="secondary"):
                # Compare original database data and edited dataframes to find changes
                changes_made = False
                update_count = 0

                # Only check rows that are not the Mean row
                for idx in range(len(original_ids)):
                    # Get original data from database
                    orig_source = str(original_df.iloc[idx]['source'])
                    orig_date = str(original_df.iloc[idx]['report_date'])
                    # Already divided by 1000 from query
                    orig_gia = float(original_df.iloc[idx]['gia_muc_tieu'])
                    orig_dt = int(original_df.iloc[idx]['doanh_thu'])
                    orig_lnst = int(
                        original_df.iloc[idx]['loi_nhuan_sau_thue'])
                    orig_link = str(original_df.iloc[idx]['link'])

                    # Get edited data
                    edited_row = edited_df.iloc[idx]
                    edit_source = str(edited_row['source'])
                    edit_date = str(edited_row['report_date'])
                    # This is in thousands (divided by 1000)
                    edit_gia = float(edited_row['gia_muc_tieu'])
                    edit_dt = int(edited_row['doanh_thu'])
                    edit_lnst = int(edited_row['loi_nhuan_sau_thue'])
                    edit_link = str(edited_row['link'])

                    # Check if any editable field has changed
                    if (orig_source != edit_source or
                        orig_date != edit_date or
                        orig_gia != edit_gia or
                        orig_dt != edit_dt or
                        orig_lnst != edit_lnst or
                            orig_link != edit_link):

                        # Update the report
                        # Note: gia_muc_tieu needs to be multiplied by 1000 before saving to database
                        report_id = original_ids[idx]
                        update_report(
                            report_id,
                            edit_source,
                            edit_date,
                            edit_gia * 1000,  # Multiply by 1000 to convert back to VND
                            edit_dt,
                            edit_lnst,
                            edit_link
                        )
                        changes_made = True
                        update_count += 1

                if changes_made:
                    st.success(f"Đã cập nhật {update_count} báo cáo")
                    # Increment counter to reset editor on next run
                    st.session_state.editor_reset_counter += 1
                    st.rerun()
                else:
                    st.info("Không có thay đổi nào để lưu")

        with col_btn_2:
            if st.button("🚫 Blacklist & Xóa", type="secondary", use_container_width=True):
                # Get selected rows (excluding the Mean row which is the last one)
                selected_indices = edited_df[edited_df['Xóa']
                                             == True].index.tolist()
                # Filter out the Mean row (last row)
                selected_indices = [
                    idx for idx in selected_indices if idx < len(original_ids)]

                if selected_indices:
                    # Add URLs to blacklist and delete selected reports
                    deleted_count = 0
                    blacklisted_count = 0
                    current_year = datetime.now().year

                    for idx in selected_indices:
                        report_id = original_ids[idx]
                        # Get the link/URL from the original dataframe
                        link = df.iloc[idx]['link']

                        # Add to blacklist if link is not empty
                        if link and link.strip():
                            set_hset(REPORT_LINK_BLACKLIST_KEY,
                                     link, current_year)
                            blacklisted_count += 1

                        # Delete the report
                        delete_report(report_id)
                        deleted_count += 1

                    st.success(
                        f"Đã xóa {deleted_count} báo cáo và thêm {blacklisted_count} link vào blacklist")
                    # Increment counter to reset editor on next run
                    st.session_state.editor_reset_counter += 1
                    st.rerun()
                else:
                    st.warning("Vui lòng chọn ít nhất một báo cáo để xóa")
    else:
        st.write(f"Không tìm thấy báo cáo cho mã chứng khoán: {symbol}")
    pass
