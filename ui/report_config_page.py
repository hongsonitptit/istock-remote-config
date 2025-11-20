import streamlit as st
import pandas as pd
import math
from pathlib import Path
from database.postgre import PostgreDatabase
from ui.ui_utils import highlight_rows
from utils.data_utils import (get_report_by_symbol, get_main_stock_data,
                        get_doanh_thu_loi_nhuan_quy, save_report,
                        get_doanh_thu_loi_nhuan_nam, delete_report, update_report,
                        update_price_config, get_forigener_trading_trend,
                        format_currency_short, get_company_estimations)
import altair as alt
from utils.redis_utils import REPORT_LINK_BLACKLIST_KEY, set_hexpired, set_hset
from datetime import datetime


def clear_filter_date_report():
    st.session_state["filter_date_report"] = ""




def save_report_to_database(symbol, source, report_date, gia_muc_tieu, doanh_thu, loi_nhuan_sau_thue, link):
    save_report(symbol, source, report_date, gia_muc_tieu,
                doanh_thu, loi_nhuan_sau_thue, link)


def display_report_table(symbol):
    reports_data = get_report_by_symbol(symbol)
    # print(reports_data)
    if reports_data:
        col_report_1, col_report_2 = st.columns([1,3])
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
        df_display['gia_muc_tieu'] = pd.to_numeric(df_display['gia_muc_tieu'], errors='coerce')
        df_display['doanh_thu'] = pd.to_numeric(df_display['doanh_thu'], errors='coerce')
        df_display['loi_nhuan_sau_thue'] = pd.to_numeric(df_display['loi_nhuan_sau_thue'], errors='coerce')

        # Calculate and display mean for 'doanh_thu' separately since it's a TextColumn
        doanh_thu_mean = int(df['doanh_thu'].mean())
        gia_muc_tieu_mean = round(df['gia_muc_tieu'].mean(),1)
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
        
        # Convert report_date to string
        report_table['report_date'] = report_table['report_date'].apply(str)

        # print(report_table.columns)
        # print(report_table)

        # Save a copy of the original table for comparison
        original_report_table = report_table.copy()

        # Initialize editor reset counter in session state
        if 'editor_reset_counter' not in st.session_state:
            st.session_state.editor_reset_counter = 0

        # display the table with checkbox column using data_editor
        # Use counter in key to force reset after save
        edited_df = st.data_editor(
            report_table,
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
            key=f"report_table_editor_{st.session_state.editor_reset_counter}"  # Dynamic key to reset state
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
                    orig_gia = float(original_df.iloc[idx]['gia_muc_tieu'])  # Already divided by 1000 from query
                    orig_dt = int(original_df.iloc[idx]['doanh_thu'])
                    orig_lnst = int(original_df.iloc[idx]['loi_nhuan_sau_thue'])
                    orig_link = str(original_df.iloc[idx]['link'])
                    
                    # Get edited data
                    edited_row = edited_df.iloc[idx]
                    edit_source = str(edited_row['source'])
                    edit_date = str(edited_row['report_date'])
                    edit_gia = float(edited_row['gia_muc_tieu'])  # This is in thousands (divided by 1000)
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
                selected_indices = edited_df[edited_df['Xóa'] == True].index.tolist()
                # Filter out the Mean row (last row)
                selected_indices = [idx for idx in selected_indices if idx < len(original_ids)]
                
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
                            set_hset(REPORT_LINK_BLACKLIST_KEY, link, current_year)
                            blacklisted_count += 1
                        
                        # Delete the report
                        delete_report(report_id)
                        deleted_count += 1
                    
                    st.success(f"Đã xóa {deleted_count} báo cáo và thêm {blacklisted_count} link vào blacklist")
                    # Increment counter to reset editor on next run
                    st.session_state.editor_reset_counter += 1
                    st.rerun()
                else:
                    st.warning("Vui lòng chọn ít nhất một báo cáo để xóa")
    else:
        st.write(f"Không tìm thấy báo cáo cho mã chứng khoán: {symbol}")
    pass




@st.dialog("Update price config")
def show_update_price_config_dialog(main_data, symbol):
    new_high = st.number_input("High", min_value=0.0, value=float(
        main_data.get('high', 0)), key="new_high")
    new_low = st.number_input("Low", min_value=0.0, value=float(
        main_data.get('low', 0)), key="new_low")
    new_rsi_14 = st.number_input("RSI 14", value=main_data.get(
        'rsi_14', 0), min_value=0.0, max_value=100.0, format="%.2f", key="new_rsi_14")
    if new_rsi_14 <= 30:
        st.warning("RSI 14 <= 30 !")
    new_trend = st.text_input("Quyết định", value=main_data.get(
        'trend', 'N/A'), key="new_trend")

    if st.button("Update"):
        # Placeholder for saving to database
        update_price_config(symbol, new_high, new_low, new_rsi_14, new_trend)
        st.success("Dữ liệu đã được lưu (placeholder)")
        st.rerun()  # Refresh the app to show updated data
    pass


def display_update_price_config_button(main_data, symbol):
    if st.button('Update price config'):
        show_update_price_config_dialog(main_data, symbol)
    pass


def display_main_stock_data(main_data):
    # Lấy giá trị rsi_14, mặc định là 'N/A' nếu không có
    rsi_value = main_data.get('rsi_14')
    gap_value = main_data.get('gap', 'N/A')

    # Biến để lưu chuỗi RSI đã được định dạng màu
    formatted_rsi = str(rsi_value)
    formatted_gap = str(gap_value)

    # Kiểm tra nếu rsi_value là một số (int/float) thì mới tiến hành tô màu
    if isinstance(rsi_value, (int, float)):
        # Xác định màu dựa trên điều kiện
        if rsi_value >= 35 and rsi_value < 70:
            # Xanh lá cây nếu >= 35 và < 70
            color = 'green'
        elif rsi_value < 35:
            # Đỏ nếu < 35
            color = 'red'
        elif rsi_value >= 70:
            # Tím nếu >= 70 (tôi dùng >= 70 thay vì > 70 để bao gồm cả 70)
            color = 'purple'
        else:
            # Nếu có lỗi gì đó, vẫn để màu mặc định
            color = 'inherit'

        # Tạo chuỗi HTML để hiển thị giá trị với màu sắc
        # Sử dụng :.2f để làm tròn đến 2 chữ số thập phân (nếu cần) và bọc bằng thẻ span
        formatted_rsi = f'<span style="color: {color}; font-weight: bold;">{rsi_value:.2f}</span>'
        # Lưu ý: Markdown trong Streamlit hỗ trợ HTML.

    # Kiểm tra nếu rsi_value là một số (int/float) thì mới tiến hành tô màu
    if isinstance(gap_value, (int, float)):
        # Xác định màu dựa trên điều kiện
        if gap_value >= 10 and gap_value <= 20:
            # Xanh lá cây nếu >= 10 và < 20
            color = 'green'
        elif gap_value < 5:
            # Đỏ nếu < 5
            color = 'red'
        elif gap_value >= 5 and gap_value < 10:
            # Vàng nếu > 5 và < 10
            color = 'orange'
        elif gap_value > 20:
            # Tím nếu > 20
            color = 'purple'
        else:
            # Nếu có lỗi gì đó, vẫn để màu mặc định
            color = 'inherit'

        # Tạo chuỗi HTML để hiển thị giá trị với màu sắc
        # Sử dụng :.2f để làm tròn đến 2 chữ số thập phân (nếu cần) và bọc bằng thẻ span
        formatted_gap = f'<span style="color: {color}; font-weight: bold;">{gap_value:.2f}</span>'
        # Lưu ý: Markdown trong Streamlit hỗ trợ HTML.
    markdown_table = f"""
    | Chỉ số | Giá trị |
    |--------|---------|
    | RSI 14 ngày | {formatted_rsi} |
    | Giá cao nhất | {"N/A" if main_data.get('high') is None else main_data.get('high')} |
    | Giá thấp nhất | {"N/A" if main_data.get('low') is None else main_data.get('low')} |
    | GAP | {formatted_gap} % |
    | Tổng cổ phiếu | {main_data.get('total', 0):,} |
    | Quyết định | {"N/A" if main_data.get('trend') is None else main_data.get('trend')} |
    """
    col1, col2 = st.columns(2)
    current_price = main_data.get('price', 'N/A')
    cost_price = main_data.get('cost_price', 0)
    with col1:
        st.metric(label="Giá hiện tại", value=f"{current_price:,}", delta=f"{main_data.get('change_percent', 0):.2f}%")
    with col2:
        if cost_price > 0:
            if current_price >= cost_price:
                pnl = (current_price/cost_price-1)*100
            else:
                pnl = -(cost_price/current_price-1)*100
            st.metric(label="Giá vốn", value=f"{cost_price:,}", delta=f"{pnl:.2f}%")
        else:
            st.metric(label="Giá vốn", value=f"{cost_price:,}")


    # Hiển thị bảng đã được tô màu
    st.markdown(markdown_table, unsafe_allow_html=True)
    # RẤT QUAN TRỌNG: Thêm tham số unsafe_allow_html=True để cho phép HTML/Màu sắc
    pass


def display_lnst_doanhthu_quy_chart(symbol):
    data = get_doanh_thu_loi_nhuan_quy(symbol)
    chart_data = pd.DataFrame(
        {
            "Danh mục": ["Q1", "Q2", "Q3", "Q4", "Total"],
            "Doanh thu": data[0],
            "LNST": data[1]
        }
    )

    chart_melted = chart_data.melt(
        "Danh mục", var_name="Loại giá trị", value_name="Giá trị")

    bars = alt.Chart(chart_melted).mark_bar().encode(
        x=alt.X("Danh mục:N", axis=alt.Axis(title="Danh mục", labelAngle=0)),
        xOffset="Loại giá trị:N",
        y="Giá trị:Q",
        color=alt.Color("Loại giá trị:N", legend=None),
        tooltip=["Danh mục", "Loại giá trị", "Giá trị"]
    ).properties(
        title='Doanh thu và Lợi nhuận sau thuế theo quý',
        height=250
    )

    text = bars.mark_text(
        align='center',
        baseline='bottom',
        fontSize=15  # Increased font size
    ).encode(
        x=alt.X("Danh mục:N", axis=alt.Axis(title="Danh mục", labelAngle=0)),
        xOffset="Loại giá trị:N",
        y=alt.Y("Giá trị:Q"),
        text=alt.Text("Giá trị:Q", format=",.0f"),
        color=alt.value('black')
    )

    st.altair_chart(bars + text, use_container_width=True)
    pass


def display_lnst_doanh_thu_nam_chart(symbol):
    data = get_doanh_thu_loi_nhuan_nam(symbol)
    current_year = datetime.today().year
    columns = []
    for index in range(len(data[0])):
        year = current_year - index
        columns.append(year)
    columns.reverse()
    chart_data = pd.DataFrame(
        {
            "Danh mục": columns,
            "Doanh thu": data[0],
            "LNST": data[1]
        }
    )

    chart_melted = chart_data.melt(
        "Danh mục", var_name="Loại giá trị", value_name="Giá trị")

    bars = alt.Chart(chart_melted).mark_bar().encode(
        x=alt.X("Danh mục:N", axis=alt.Axis(title="Danh mục", labelAngle=0)),
        xOffset="Loại giá trị:N",
        y="Giá trị:Q",
        color=alt.Color("Loại giá trị:N", legend=None),
        tooltip=["Danh mục", "Loại giá trị", "Giá trị"]
    ).properties(
        title='Doanh thu và Lợi nhuận sau thuế theo năm',
        height=250
    )

    text = bars.mark_text(
        align='center',
        baseline='bottom',
        fontSize=15  # Increased font size
    ).encode(
        x=alt.X("Danh mục:N", axis=alt.Axis(title="Danh mục", labelAngle=0)),
        xOffset="Loại giá trị:N",
        y=alt.Y("Giá trị:Q"),
        text=alt.Text("Giá trị:Q", format=",.0f"),
        color=alt.value('black')
    )

    st.altair_chart(bars + text, use_container_width=True)
    pass


def display_forigener_trading_trend_chart(foreigner_trading):
    # Sample data for demonstration
    data = {
        'Net Buy Value': foreigner_trading
    }
    df = pd.DataFrame(data)
    df['index'] = df.index  # Add an index column to use as x-axis

    df['Net Buy Value Formatted'] = df['Net Buy Value'].apply(
        format_currency_short)

    chart = alt.Chart(df).mark_line(point=True).encode(
        # Use index as ordinal data for x-axis
        x=alt.X('index:O', axis=alt.Axis(title='Thời gian', labelAngle=0)),
        y=alt.Y('Net Buy Value:Q', title='Giá trị mua ròng',
                axis=alt.Axis(format='s')),  # Apply short format to Y-axis
        tooltip=['index', 'Net Buy Value Formatted']  # Update tooltip
    ).properties(
        title='Xu hướng giao dịch mua ròng của nhà đầu tư nước ngoài',
        height=250
    )
    st.altair_chart(chart, use_container_width=True)
    pass


def display_dividend_payment_history_table(symbol):
    from utils.api_utils import get_dividend_payment_histories
    dividend_data = get_dividend_payment_histories(symbol, page=0, size=10)
    if dividend_data:
        df = pd.DataFrame(dividend_data)

        def highlight_rows(row):
            if row.name % 2 == 0:
                # Light grey for even rows
                return ['background-color: #f0f2f6'] * len(row)
            else:
                # White for odd rows
                return ['background-color: #ffffff'] * len(row)

        st.dataframe(
            df.style.apply(highlight_rows, axis=1),
            hide_index=True,
            # use_container_width=True,
            # Set max height to 800px to prevent excessively tall tables
            height=min(35 * len(df) + 35, 800)
        )
    else:
        st.write(
            f"Không tìm thấy dữ liệu trả cổ tức cho mã chứng khoán: {symbol}")
        
def display_summary_reports():
    st.write("### Summary Reports")
    pass

def display_company_estimations(symbol):
    estimations = get_company_estimations(symbol)
    with st.expander("Đánh giá 360"):
        if estimations:
            markdown_table = f"""
            | Tiêu chí | Điểm |
            |--------|---------|
            | Định giá (V) | {estimations.get('dinh_gia', 'N/A')} |
            | Tăng trưởng (G) | {estimations.get('tang_truong', 'N/A')} |
            | Lợi nhuận (P) | {estimations.get('loi_nhuan', 'N/A')} |
            | Tài chính (F) | {estimations.get('tai_chinh', 'N/A')} |
            | Cổ tức (D) | {estimations.get('co_tuc', 'N/A')} |
            """
            st.markdown(markdown_table, unsafe_allow_html=True)
        else:
            st.write(f"Không tìm thấy dữ liệu định giá cho mã chứng khoán: {symbol}")
        pass

# -----------------------------------------------------------------------------
# Declare some useful functions.

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
# '''
# # :earth_americas: GDP dashboard

# Browse GDP data from the [World Bank Open Data](https://data.worldbank.org/) website. As you'll
# notice, the data only goes to 2022 right now, and datapoints for certain years are often missing.
# But it's otherwise a great (and did I mention _free_?) source of data.
# '''

# # Add some spacing
# ''
# # ''

def show_report_config_page():
    left_col, right_col = st.columns([1, 1])


    with left_col:
        # f'''
        # for debugging purpose, display main_data:
        # {main_data}
        # '''
        col1, col2 = st.columns([2, 5])
        with col1:

            symbol = st.text_input("Nhập mã chứng khoán (ví dụ: FPT):",
                                "FPT", key="symbol_input", on_change=clear_filter_date_report)
            main_data = get_main_stock_data(symbol)
            display_main_stock_data(main_data)
            display_update_price_config_button(main_data, symbol)
            display_company_estimations(symbol)

        with col2:
            foreigner_trading = get_forigener_trading_trend(symbol)
            display_lnst_doanhthu_quy_chart(symbol)
            display_lnst_doanh_thu_nam_chart(symbol)
            display_forigener_trading_trend_chart(foreigner_trading)
            '###### Lịch sử trả cổ tức'
            display_dividend_payment_history_table(symbol)
            


    with right_col:
        if symbol:
            display_report_table(symbol)
        display_summary_reports()
