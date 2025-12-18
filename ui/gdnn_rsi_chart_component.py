import streamlit as st
import pandas as pd
import altair as alt
from logger import default_logger as logger
from utils.data_utils import (get_forigener_trading_trend, get_rsi_history, format_currency_short)

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
    
    # Tạo base chart
    base = alt.Chart(df).encode(
        # x=alt.X('index:O', axis=alt.Axis(title='Ngày', labelAngle=0)),  # Hiển thị trục X
        x=alt.X('index:O', axis=None),  # Ẩn trục X
        y=alt.Y('Net Buy Value:Q', axis=alt.Axis(title='Giá trị (VNĐ)', format='~s')),  # Hiển thị trục Y dạng rút gọn (15M)
        tooltip=['index', 'Net Buy Value Formatted']  # Update tooltip
    )
    
    # Tạo đường line với màu động
    line = base.mark_line(color=line_color, strokeWidth=2)
    
    # Tạo các điểm với màu động
    points = base.mark_point(color=line_color, size=50, filled=True)
    
    # Kết hợp line và points
    line_chart = line + points
    
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
        title='GDNN',
        height=200
    )
    
    st.altair_chart(chart, use_container_width=True)
    pass


def display_rsi_14_chart(rsi_data, symbol):
    """Hiển thị biểu đồ RSI 14 ngày của cổ phiếu"""
    try:
        # st.write("RSI 14 ngày")
        if rsi_data is None or rsi_data.empty:
            st.warning(f"Không thể lấy dữ liệu RSI cho mã {symbol}")
            return
        
        # Tạo DataFrame cho biểu đồ
        # Kiểm tra xem có cột 'time' không, nếu không thì dùng index
        if 'time' in rsi_data.columns:
            time_labels = rsi_data['time'].astype(str).values
        elif hasattr(rsi_data.index, 'strftime'):
            # Index là DatetimeIndex
            time_labels = rsi_data.index.strftime('%Y-%m-%d').values
        else:
            # Index là RangeIndex hoặc kiểu khác, tạo label đơn giản
            time_labels = [f"T{i+1}" for i in range(len(rsi_data))]
        
        chart_data = pd.DataFrame({
            'index': range(len(rsi_data)),
            'RSI': rsi_data['rsi'].values,
            'time': time_labels,
            'oversold': 30,
            'overbought': 70
        })
        
        # Loại bỏ các giá trị NaN
        chart_data = chart_data.dropna()
        
        if chart_data.empty:
            st.warning(f"Không có dữ liệu RSI hợp lệ cho mã {symbol}")
            return
        
        # Tạo đường RSI chính
        line_rsi = alt.Chart(chart_data).mark_line(point=True, color='#2E86AB', strokeWidth=2).encode(
            # x=alt.X('index:O', axis=alt.Axis(title='Ngày', labelAngle=0)),  # Hiển thị trục X
            x=alt.X('index:O', axis=None),  # Ẩn trục X
            y=alt.Y('RSI:Q', axis=alt.Axis(title='RSI'), scale=alt.Scale(domain=[20, 90])),  # Hiển thị trục Y
            tooltip=[
                alt.Tooltip('time:N', title='Ngày'),
                alt.Tooltip('RSI:Q', title='RSI', format='.2f')
            ]
        )
        
        # Tạo đường mức 30 (oversold)
        oversold_line = alt.Chart(chart_data).mark_line(
            strokeDash=[5, 5], 
            color='red', 
            strokeWidth=2
        ).encode(
            x=alt.X('index:O', axis=None),
            y='oversold:Q'
        )
        
        # Tạo đường mức 70 (overbought)
        overbought_line = alt.Chart(chart_data).mark_line(
            strokeDash=[5, 5], 
            color='purple', 
            strokeWidth=2
        ).encode(
            x=alt.X('index:O', axis=None),
            y='overbought:Q'
        )
        
        # Kết hợp các layer (thêm text_annotation)
        # chart = (line_rsi + oversold_line + overbought_line + text_annotation).properties(
        chart = (line_rsi + oversold_line + overbought_line).properties(
            title='RSI 14 ngày',
            height=200
        )
        
        st.altair_chart(chart, use_container_width=True)
        
    except Exception as e:
        logger.exception(f"Lỗi khi hiển thị biểu đồ RSI cho {symbol}: {e}")
        st.error(f"Lỗi khi hiển thị biểu đồ RSI: {str(e)}")


def display_gdnn_and_rsi_chart(symbol):
    foreigner_trading = get_forigener_trading_trend(symbol)
    # Lấy dữ liệu RSI 30 ngày gần nhất
    rsi_data = get_rsi_history(symbol)
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        display_forigener_trading_trend_chart(foreigner_trading, symbol)

    with chart_col2:
        display_rsi_14_chart(rsi_data, symbol)
