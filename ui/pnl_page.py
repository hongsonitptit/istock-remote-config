import streamlit as st
import pandas as pd
from database.postgre import PostgreDatabase

def get_company_data(symbol):
    query = f"select * from company where symbol = '{symbol.upper()}'"
    db_conn = PostgreDatabase()
    data = db_conn.raw_query(query)
    return data

def show_table(symbol):
    data = get_company_data(symbol)
    df =  pd.DataFrame(data)
    # 2. Xóa tất cả các cột rỗng (chứa toàn bộ NaN/None)
    # axis=1: áp dụng cho cột
    # how='all': chỉ xóa nếu TẤT CẢ các giá trị trong cột đều là NaN/None
    df = df.dropna(axis=1, how='all')

    drop_columns = 'gtnt,max_recmd,min_recmd,group,min_gtnt'
    df = df.drop(columns=drop_columns.split(','), errors='ignore')

    html_table = df.to_html(index=False, escape=False)

    # Thêm thẻ <div> với CSS để cuộn ngang (overflow-x: auto)
    scrollable_html = f"""
    <div style="overflow-x: auto; border: 1px solid #e6e6e6; padding: 10px; border-radius: 5px;">
        {html_table}
    </div>
    """

    st.write(scrollable_html, unsafe_allow_html=True)
    # st.write(df.to_html(escape=False), unsafe_allow_html=True)
    pass


def show_pnl_page():
    symbol = st.text_input("Filter company ...", "FPT")
    show_table(symbol)
    st.write("### TODO show P/E, P/B ...")

# get_company_data()