import streamlit as st
import altair as alt
import pandas as pd
from utils.api_utils import get_finance_history 
from utils.data_utils import get_main_stock_data

def display_summary_reports(symbol):
    """Hiển thị đồ thị lịch sử P/E và P/B của cổ phiếu"""
    # Lấy dữ liệu chính của cổ phiếu
    main_stock_data = get_main_stock_data(symbol)
    close_price = main_stock_data['price']*1000

    # Lấy dữ liệu P/E và P/B từ API mới
    finance_data_df = get_finance_history(symbol)
    # tạo eps_df = cách lấy data từ finance_data_df theo các cột: year, quarter, earningPerShare
    eps_df = finance_data_df[['year', 'quarter', 'earningPerShare']].copy()
    # tạo bvps_df = cách lấy data từ finance_data_df theo các cột: year, quarter, bookValuePerShare
    bvps_df = finance_data_df[['year', 'quarter', 'bookValuePerShare']].copy()
    # tạo pe_df = cách lấy data từ finance_data_df theo các cột: year, quarter, priceToEarning
    pe_df = finance_data_df[['year', 'quarter', 'priceToEarning']].copy()
    # tạo pb_df = cách lấy data từ finance_data_df theo các cột: year, quarter, priceToBook
    pb_df = finance_data_df[['year', 'quarter', 'priceToBook']].copy()
    # tạo time = cách lấy data từ finance_data_df theo các cột: year, quarter
    pe_df['time'] = pe_df['year'].astype(str) + '-Q' + pe_df['quarter'].astype(str)
    pb_df['time'] = pb_df['year'].astype(str) + '-Q' + pb_df['quarter'].astype(str)
    bvps_df['time'] = bvps_df['year'].astype(str) + '-Q' + bvps_df['quarter'].astype(str)
    eps_df['time'] = eps_df['year'].astype(str) + '-Q' + eps_df['quarter'].astype(str)

    # đổi tên cột priceToEarning thành pe
    pe_df = pe_df.rename(columns={'priceToEarning': 'pe'})
    # đổi tên cột priceToBook thành pb
    pb_df = pb_df.rename(columns={'priceToBook': 'pb'})
    # lấy dữ liệu của 10 năm gần nhất, tức là 40 quý gần nhất
    pe_df = pe_df.head(40)
    pb_df = pb_df.head(40)

    # Sắp xếp lại dữ liệu theo thời gian (cũ -> mới)
    pe_df = pe_df.sort_values('time').reset_index(drop=True)
    pb_df = pb_df.sort_values('time').reset_index(drop=True)
    bvps_df = bvps_df.sort_values('time').reset_index(drop=True)
    eps_df = eps_df.sort_values('time').reset_index(drop=True)

    # Tính toán P/E và P/B hiện tại
    current_pe = close_price / eps_df['earningPerShare'].iloc[-1]
    current_pb = close_price / bvps_df['bookValuePerShare'].iloc[-1]

    # thêm P/E và P/B hiện tại vào DataFrame
    current_pe_df = pd.DataFrame([{'time': 'Current', 'pe': current_pe}])
    pe_df = pd.concat([pe_df, current_pe_df], ignore_index=True)
    
    current_pb_df = pd.DataFrame([{'time': 'Current', 'pb': current_pb}])
    pb_df = pd.concat([pb_df, current_pb_df], ignore_index=True)

    draw_pe_pb_charts(pe_df, pb_df)


def draw_pe_pb_charts(pe_df, pb_df):
    # Hiển thị 2 cột cho 2 đồ thị
    col1, col2 = st.columns(2)

    with col1:
        st.write("#### P/E (Price-to-Earnings)")
        if pe_df.empty:
            st.warning(f"Không thể lấy dữ liệu P/E cho mã {symbol}")
        else:
            # Tính toán thống kê P/E
            current_pe = pe_df['pe'].iloc[-1]
            mean_pe = float(pe_df['pe'].mean())
            max_pe = float(pe_df['pe'].max())
            min_pe = float(pe_df['pe'].min())

            pe_chart_data = pe_df.copy()
            pe_chart_data['P/E Mean'] = mean_pe

            # Tạo biểu đồ P/E
            base_pe = alt.Chart(pe_chart_data).encode(
                x=alt.X('time:N', axis=alt.Axis(
                    title='Kỳ báo cáo', labelAngle=-45))
            )

            # Đường P/E thực tế
            line_pe = base_pe.mark_line(point=True, color='#2E86AB', strokeWidth=2).encode(
                y=alt.Y('pe:Q', title='P/E', scale=alt.Scale(zero=False)),
                tooltip=[
                    alt.Tooltip('time:N', title='Kỳ'),
                    alt.Tooltip('pe:Q', title='P/E', format='.2f')
                ]
            )

            # Đường trung bình
            mean_line_pe = base_pe.mark_line(strokeDash=[5, 5], color='red', strokeWidth=2).encode(
                y=alt.Y('P/E Mean:Q'),
                tooltip=[alt.Tooltip(
                    'P/E Mean:Q', title='TB lịch sử', format='.2f')]
            )

            # Vùng fill
            area_pe = base_pe.mark_area(opacity=0.3, color='#2E86AB').encode(
                y=alt.Y('pe:Q')
            )

            # Kết hợp các layer
            chart_pe = (area_pe + line_pe + mean_line_pe).properties(
                height=300
            )

            st.altair_chart(chart_pe, use_container_width=True)

            # Hiển thị thống kê P/E
            pe_deviation = ((current_pe - mean_pe) / mean_pe) * 100

            st.markdown(f"""
            **Thống kê P/E:**
            - Hiện tại: **{current_pe:.2f}**
            - Trung bình: {mean_pe:.2f}
            - Cao nhất: {max_pe:.2f}
            - Thấp nhất: {min_pe:.2f}
            """)

            if pe_deviation > 10:
                st.warning(
                    f"⚠️ Cao hơn TB {pe_deviation:.1f}% - Có thể định giá cao")
            elif pe_deviation < -10:
                st.success(
                    f"✓ Thấp hơn TB {abs(pe_deviation):.1f}% - Có thể định giá thấp")
            else:
                st.info(f"→ Gần mức TB ({pe_deviation:+.1f}%)")

    with col2:
        st.write("#### P/B (Price-to-Book)")
        if pb_df.empty:
            st.warning(f"Không thể lấy dữ liệu P/B cho mã {symbol}")
        else:
            # Tính toán thống kê P/B
            current_pb = pb_df['pb'].iloc[-1]
            mean_pb = float(pb_df['pb'].mean())
            max_pb = float(pb_df['pb'].max())
            min_pb = float(pb_df['pb'].min())

            pb_chart_data = pb_df.copy()
            pb_chart_data['P/B Mean'] = mean_pb

            # Tạo biểu đồ P/B
            base_pb = alt.Chart(pb_chart_data).encode(
                x=alt.X('time:N', axis=alt.Axis(
                    title='Kỳ báo cáo', labelAngle=-45))
            )

            # Đường P/B thực tế
            line_pb = base_pb.mark_line(point=True, color='#A23B72', strokeWidth=2).encode(
                y=alt.Y('pb:Q', title='P/B', scale=alt.Scale(zero=False)),
                tooltip=[
                    alt.Tooltip('time:N', title='Kỳ'),
                    alt.Tooltip('pb:Q', title='P/B', format='.2f')
                ]
            )

            # Đường trung bình
            mean_line_pb = base_pb.mark_line(strokeDash=[5, 5], color='red', strokeWidth=2).encode(
                y=alt.Y('P/B Mean:Q'),
                tooltip=[alt.Tooltip(
                    'P/B Mean:Q', title='TB lịch sử', format='.2f')]
            )

            # Vùng fill
            area_pb = base_pb.mark_area(opacity=0.3, color='#A23B72').encode(
                y=alt.Y('pb:Q')
            )

            # Kết hợp các layer
            chart_pb = (area_pb + line_pb + mean_line_pb).properties(
                height=300
            )

            st.altair_chart(chart_pb, use_container_width=True)

            # Hiển thị thống kê P/B
            pb_deviation = ((current_pb - mean_pb) / mean_pb) * 100

            st.markdown(f"""
            **Thống kê P/B:**
            - Hiện tại: **{current_pb:.2f}**
            - Trung bình: {mean_pb:.2f}
            - Cao nhất: {max_pb:.2f}
            - Thấp nhất: {min_pb:.2f}
            """)

            if pb_deviation > 10:
                st.warning(
                    f"⚠️ Cao hơn TB {pb_deviation:.1f}% - Có thể định giá cao")
            elif pb_deviation < -10:
                st.success(
                    f"✓ Thấp hơn TB {abs(pb_deviation):.1f}% - Có thể định giá thấp")
            else:
                st.info(f"→ Gần mức TB ({pb_deviation:+.1f}%)")
