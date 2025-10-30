import streamlit as st

def show_trend_page():
    # Tạo chuỗi HTML với thẻ iframe
    # Thay đổi 'width', 'height', và 'src' theo nhu cầu của bạn
    iframe_html = f'''
    <iframe 
        src="https://priceconfig.vercel.app/" 
        width="100%" 
        height="1000px" 
        style="border:none;"
    ></iframe>
    '''

    # Sử dụng st.markdown để hiển thị nội dung HTML
    # **Phải bật unsafe_allow_html=True để hiển thị iframe**
    st.markdown(iframe_html, unsafe_allow_html=True) 

