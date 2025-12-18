import streamlit as st
from utils.data_utils import format_currency_short

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
    
    # hiển thị các thông tin
    # st.markdown(f"<small><b>{main_data['name']}</b></small></br><small><i>{main_data['industry']}</i></small>", unsafe_allow_html=True)
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
    markdown_table = f"""
    | Chỉ số | Giá trị |
    |--------|---------|
    | RSI 14 ngày | {formatted_rsi} |
    | Giá cao nhất | {"N/A" if main_data.get('high') is None else main_data.get('high')} |
    | Giá thấp nhất | {"N/A" if main_data.get('low') is None else main_data.get('low')} |
    | GAP | {formatted_gap} % |
    | Tổng cổ phiếu | {main_data.get('total', 0):,} |
    | KLGD TB 20 | {format_currency_short(main_data.get('avg_trading_volume', 0))} |
    | Quyết định | {"N/A" if main_data.get('trend') is None else main_data.get('trend')} |
    """
    st.markdown(markdown_table, unsafe_allow_html=True)
    # RẤT QUAN TRỌNG: Thêm tham số unsafe_allow_html=True để cho phép HTML/Màu sắc
    st.markdown(f"<small><b>{main_data['name']} - {main_data['exchange']}</b></small></br><small><i>{main_data['industry']}</i></small></br><small><href target='{main_data['website']}'>{main_data['website']}</href></small>", unsafe_allow_html=True)
    pass
