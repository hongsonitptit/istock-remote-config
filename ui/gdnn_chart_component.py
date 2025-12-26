import streamlit as st
import pandas as pd
import altair as alt
from logger import default_logger as logger
from utils.data_utils import (get_forigener_trading_trend, get_rsi_history, format_currency_short)
from utils.api_utils import get_foreigner_room
from datetime import datetime, timedelta

def display_forigener_trading_trend_chart(foreigner_trading, symbol):
    # Sample data for demonstration
    data = {
        'Net Buy Value': foreigner_trading
    }
    df = pd.DataFrame(data)
    df['index'] = df.index  # Add an index column to use as x-axis

    df['Net Buy Value Formatted'] = df['Net Buy Value'].apply(
        format_currency_short)

    # Lấy giá trị đầu tiên và cuối cùng
    first_value = df['Net Buy Value'].iloc[0]
    first_index = df['index'].iloc[0]
    last_value = df['Net Buy Value'].iloc[-1]
    last_index = df['index'].iloc[-1]
    
    # Xác định màu cho line chart dựa trên xu hướng
    line_color = 'green' if last_value >= first_value else 'red'
    # line_color = 'blue'
    
    # Tạo base chart
    base = alt.Chart(df).encode(
        # x=alt.X('index:O', axis=alt.Axis(title='Ngày', labelAngle=0)),  # Hiển thị trục X
        x=alt.X('index:O', axis=None),  # Ẩn trục X
        y=alt.Y('Net Buy Value:Q', 
                # axis=alt.Axis(title='Giá trị (VNĐ)', format='~s'),
                axis=alt.Axis(title='', format='~s'),
                scale=alt.Scale(zero=False)
        ),  # Hiển thị trục Y dạng rút gọn (15M) và tự động căn chỉnh theo dữ liệu (không bắt đầu từ 0)
        tooltip=['index', 'Net Buy Value Formatted']  # Update tooltip
    )
    
    # Tạo đường line với màu động
    line = base.mark_line(color=line_color, strokeWidth=2)
    
    # Tạo các điểm với màu động
    points = base.mark_point(color=line_color, size=50, filled=True)
    
    # Kết hợp line và points
    # line_chart = line + points
    line_chart = line
    
    # Lấy giá trị max của y để đặt text ở góc trên
    max_value = df['Net Buy Value'].max()
    
    # Tạo text annotation cố định ở góc trên bên trái
    first_text = alt.Chart(pd.DataFrame({
        'text': [format_currency_short(first_value)]
    })).mark_text(
        align='left',
        baseline='top',
        dx=5,  # Offset từ cạnh trái
        dy=5,  # Offset từ cạnh trên
        fontSize=12,
        fontWeight='bold',
        color='black'
    ).encode(
        x=alt.value(0),  # Vị trí pixel cố định bên trái
        y=alt.value(0),  # Vị trí pixel cố định ở trên
        text='text:N'
    )
    
    # Tạo text annotation cố định ở góc trên bên phải
    last_text = alt.Chart(pd.DataFrame({
        'text': [format_currency_short(last_value)]
    })).mark_text(
        align='right',
        baseline='top',
        dx=-5,  # Offset từ cạnh phải
        dy=5,  # Offset từ cạnh trên
        fontSize=12,
        fontWeight='bold',
        color='black'
    ).encode(
        x=alt.value(200),  # Vị trí pixel cố định bên phải (điều chỉnh theo width)
        y=alt.value(0),  # Vị trí pixel cố định ở trên
        text='text:N'
    )
    
    # Kết hợp các layer
    # chart = (line_chart + first_text + last_text).properties(
    chart = (line_chart).properties(
        title=f'GDNN ({len(df)} ngày)',
        height=150
    )
    
    st.altair_chart(chart, use_container_width=True)
    pass

def display_foreiger_room(symbol):
    start = datetime.now() - timedelta(days=90)
    end = datetime.now()
    foreigner_room = get_foreigner_room(symbol, start_date=start.strftime('%Y-%m-%d'), end_date=end.strftime('%Y-%m-%d'))
    # đảo ngươc lại room NN để tính xu hướng mua / bán của khối ngoại 
    start_volume = foreigner_room[0]
    foreigner_room = [start_volume - x for x in foreigner_room]
    display_forigener_trading_trend_chart(foreigner_room, symbol)
