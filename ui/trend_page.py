import streamlit as st
import pandas as pd
from database.postgre import PostgreDatabase
from ui.utils import highlight_rows

def get_price_config_data():
    query = f"select * from price_config"
    db_conn = PostgreDatabase()
    data = db_conn.raw_query(query)
    return data

def show_table():
    data = get_price_config_data()
    df =  pd.DataFrame(data)

    drop_columns = 'note'
    df = df.drop(columns=drop_columns.split(','), errors='ignore')

    st.dataframe(df.style.apply(highlight_rows, axis=1),
                height=min(35 * len(df) + 35, 800))
    pass


def show_trend_page():
    # symbol = st.text_input("Filter company ...", "FPT")
    show_table()
    # st.write("### TODO show P/E, P/B ...")

# get_company_data()