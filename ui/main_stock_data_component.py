import streamlit as st
from utils.data_utils import format_currency_short
from utils.data_utils import update_price_config, add_price_config, delete_price_config

def display_main_stock_data(main_data, symbol):
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
    # print(main_data)
    # Hiển thị bảng đã được tô màu
    markdown_table = f"""
    | Chỉ số | Giá trị |
    |--------|---------|
    | RSI | {formatted_rsi} |
    | Giá bán | {"N/A" if main_data.get('high') is None else main_data.get('high')} |
    | Giá mua | {"N/A" if main_data.get('low') is None else main_data.get('low')} |
    | Biên an toàn | {formatted_gap} % |
    | Tổng CP | {main_data.get('total', 0):,} |
    | Bước đặt KL | {main_data.get('gap_volume', 0):,} |
    | Quyết định | {"N/A" if main_data.get('trend') is None else main_data.get('trend')} |
    """
    st.markdown(markdown_table, unsafe_allow_html=True)

    simplize_link = f"https://simplize.vn/co-phieu/{main_data['symbol']}"

    # RẤT QUAN TRỌNG: Thêm tham số unsafe_allow_html=True để cho phép HTML/Màu sắc
    st.markdown(f"<small><b><a href='{main_data['website']}' target='_blank'>{main_data['name']} - {main_data['exchange']}</a> <a href='{simplize_link}' target='_blank' style='color: purple;'>(Simplize)</a></b></small></br><small><i>{main_data['industry']}</i></small>", unsafe_allow_html=True)

    display_update_price_config_button(main_data, symbol)


@st.dialog("Update price config")
def show_update_price_config_dialog(main_data, symbol):
    new_high = st.number_input("High", min_value=0.0, value=float(
        main_data.get('high') or 0), key="update_high")
    new_low = st.number_input("Low", min_value=0.0, value=float(
        main_data.get('low') or 0), key="update_low")
    new_rsi_14 = st.number_input("RSI 14", value=float(main_data.get(
        'rsi_14') or 0), min_value=0.0, max_value=100.0, format="%.2f", key="update_rsi_14")
    if new_rsi_14 <= 30:
        st.warning("RSI 14 <= 30 !")
    new_trend = st.text_input("Quyết định", value=main_data.get(
        'trend') or 'N/A', key="update_trend")
    new_gap_volume = st.number_input("Bước đặt KL", value=int(main_data.get(
        'gap_volume') or 0), key="update_gap_volume")

    if st.button("Update"):
        update_price_config(symbol, new_high, new_low, new_rsi_14, new_trend, new_gap_volume)
        st.success("Dữ liệu đã được cập nhật")
        st.rerun()


@st.dialog("Add price config")
def show_add_price_config_dialog(main_data, symbol):
    new_high = st.number_input("High", min_value=0.0, value=float(
        main_data.get('high') or 0), key="add_high")
    new_low = st.number_input("Low", min_value=0.0, value=float(
        main_data.get('low') or 0), key="add_low")
    new_rsi_14 = st.number_input("RSI 14", value=float(main_data.get(
        'rsi_14') or 0), min_value=0.0, max_value=100.0, format="%.2f", key="add_rsi_14")
    if new_rsi_14 <= 30:
        st.warning("RSI 14 <= 30 !")
    new_trend = st.text_input("Quyết định", value=main_data.get(
        'trend') or 'N/A', key="add_trend")
    new_gap_volume = st.number_input("Bước đặt KL", value=int(main_data.get(
        'gap_volume') or 0), key="add_gap_volume")

    if st.button("Add"):
        add_price_config(symbol, new_high, new_low, new_rsi_14, new_trend, new_gap_volume)
        st.success("Dữ liệu đã được thêm mới")
        st.rerun()


@st.dialog("Delete confirmation")
def show_delete_confirmation_dialog(symbol):
    st.warning(f"Bạn có chắc chắn muốn xóa cấu hình giá cho {symbol}?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, delete it", type="primary", use_container_width=True):
            delete_price_config(symbol)
            st.success("Đã xóa cấu hình giá")
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()


def display_update_price_config_button(main_data, symbol):
    cols = st.columns([1, 1, 1])
    with cols[0]:
        if st.button('🔄', disabled=not main_data.get('in_price_config', False), use_container_width=True, help="Update price config"):
            show_update_price_config_dialog(main_data, symbol)
    with cols[1]:
        if st.button('➕', disabled=main_data.get('in_price_config', False), use_container_width=True, help="Add price config"):
            show_add_price_config_dialog(main_data, symbol)
    with cols[2]:
        if st.button('🗑️', disabled=not main_data.get('in_price_config', False), use_container_width=True, help="Delete price config"):
            show_delete_confirmation_dialog(symbol)