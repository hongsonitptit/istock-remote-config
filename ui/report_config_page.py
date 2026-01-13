import streamlit as st
import pandas as pd
import math
from pathlib import Path
from database.postgre import PostgreDatabase
from ui.ui_utils import highlight_rows
from ui.main_stock_data_component import display_main_stock_data
from ui.gdnn_chart_component import display_foreiger_room
from ui.report_table_component import display_report_table
from ui.index_report_component import display_summary_reports
from ui.trading_view import display_trading_view
from utils.api_utils import get_doanh_thu_loi_nhuan_nam, get_last_doanh_thu_loi_nhuan_quy
from utils.data_utils import (get_main_stock_data,
                              save_report,
                            #   get_doanh_thu_loi_nhuan_quy, 
                            #   get_doanh_thu_loi_nhuan_nam,
                              update_price_config, get_forigener_trading_trend,
                              format_currency_short, get_company_estimations,
                              get_rsi_history)
import altair as alt

from datetime import datetime
from logger import default_logger as logger


def clear_filter_date_report():
    st.session_state["filter_date_report"] = ""
    if "last_dividend_event_time" in st.session_state:
        del st.session_state["last_dividend_event_time"]


def save_report_to_database(symbol, source, report_date, gia_muc_tieu, doanh_thu, loi_nhuan_sau_thue, link):
    save_report(symbol, source, report_date, gia_muc_tieu,
                doanh_thu, loi_nhuan_sau_thue, link)


def display_lnst_doanhthu_quy_chart(symbol):
    if len(symbol) > 3:
        # skip this chart for ETF
        return
    st.write("Doanh thu và Lợi nhuận sau thuế ")
    data = get_last_doanh_thu_loi_nhuan_quy(symbol)
    chart_data = pd.DataFrame(
        {
            "Danh mục": ["Q0", "Q1", "Q2", "Q3", "Q4", "Total"],
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
        # title='Doanh thu và Lợi nhuận sau thuế theo quý',
        height=200
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
    # st.write("Doanh thu và Lợi nhuận sau thuế theo năm")
    if len(symbol) > 3:
        # skip this chart for ETF
        return
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
        # title='Doanh thu và Lợi nhuận sau thuế theo năm',
        height=200
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


def display_dividend_payment_history_table(symbol):
    if len(symbol) > 3:
        # skip this chart for ETF
        return
    from utils.api_utils import get_dividend_payment_histories
    dividend_data = get_dividend_payment_histories(symbol)
    if dividend_data:
        df = pd.DataFrame(dividend_data)
        # sort by time
        df = df.sort_values(by='Thời gian', ascending=False)

        # lưu lại sự kiện đầu tiên của dividend_data vào session state 
        if "last_dividend_event_time" not in st.session_state:
            st.session_state["last_dividend_event_time"] = df['Thời gian'][0]

        def highlight_rows(row):
            try:
                payment_date = pd.to_datetime(row['Thời gian'])
                current_date = pd.Timestamp.now()

                if payment_date > current_date:
                    return ['background-color: #d1e7dd; color: #0f5132'] * len(row)
            except Exception:
                pass

            if row.name % 2 == 0:
                # Light grey for even rows
                return ['background-color: #f0f2f6'] * len(row)
            else:
                # White for odd rows
                return ['background-color: #ffffff'] * len(row)

        st.dataframe(
            df.style.apply(highlight_rows, axis=1),
            hide_index=True,
            # width='stretch',
            # Set max height to 800px to prevent excessively tall tables
            height=min(35 * len(df) + 35, 800)
        )
    else:
        st.write(
            f"Không tìm thấy dữ liệu trả cổ tức cho mã chứng khoán: {symbol}")





def display_company_estimations(symbol):
    if len(symbol) > 3:
        # skip this chart for ETF
        return
    estimations = get_company_estimations(symbol)
    with st.expander("Đánh giá 360", expanded=True):
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
            st.write(
                f"Không tìm thấy dữ liệu định giá cho mã chứng khoán: {symbol}")
        pass


# -----------------------------------------------------------------------------
# Declare some useful functions.

def show_report_config_page():
    # Initialize symbol from query params if not in session state
    if "symbol_input" not in st.session_state:
        st.session_state["symbol_input"] = st.query_params.get("symbol", "FPT")

    def update_symbol_url():
        st.query_params["symbol"] = st.session_state["symbol_input"].upper().strip()
        clear_filter_date_report()

    left_col, right_col = st.columns([1, 1])

    with left_col:
        col1, col2 = st.columns([2, 5])
        with col1:

            symbol = st.text_input("Nhập mã chứng khoán (ví dụ: FPT):",
                                   key="symbol_input", on_change=update_symbol_url)
            
            # Ensure query params are set on first load
            if "symbol" not in st.query_params:
                st.query_params["symbol"] = symbol

            symbol = symbol.upper().strip()
            main_data = get_main_stock_data(symbol)
            display_main_stock_data(main_data, symbol)
            display_foreiger_room(symbol)
            display_company_estimations(symbol)

        with col2:
            display_lnst_doanhthu_quy_chart(symbol)
            display_lnst_doanh_thu_nam_chart(symbol)
            # display_gdnn_and_rsi_chart(symbol)
            display_trading_view(symbol)
            '###### Lịch sử trả cổ tức'
            display_dividend_payment_history_table(symbol)

    with right_col:
        if symbol:
            display_report_table(symbol)
        display_summary_reports(symbol)
