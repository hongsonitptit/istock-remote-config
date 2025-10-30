import streamlit as st
import pandas as pd
from database.postgre import PostgreDatabase
from ui.ui_utils import highlight_rows
from utils.data_utils import convert_forigener_trading_data

def get_price_config_data():
    query = f"select * from price_config"
    db_conn = PostgreDatabase()
    data = db_conn.raw_query(query)
    for item in data:
        foreigner_data_str = item['foreigner']
        item['foreigner'] = convert_forigener_trading_data(foreigner_data_str)
    return data

def show_table():
    data = get_price_config_data()
    df =  pd.DataFrame(data)

    drop_columns = 'note'
    df = df.drop(columns=drop_columns.split(','), errors='ignore')
    

    st.dataframe(df.style.apply(highlight_rows, axis=1),
                 column_config={
                    "foreigner": st.column_config.LineChartColumn(
                        "Foreigner (past 30 days)",
                        #   y_min=0, y_max=5000
                    ),
                },
                height=min(35 * len(df) + 35, 800))
    pass


def show_trend_page():
    # symbol = st.text_input("Filter company ...", "FPT")
    show_table()
    # st.write("### TODO show P/E, P/B ...")

get_price_config_data()