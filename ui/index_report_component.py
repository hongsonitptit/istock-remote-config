import streamlit as st
import altair as alt
from utils.vnstock_utils import get_pe_pb_history

def display_summary_reports(symbol):
    """Hiển thị đồ thị lịch sử P/E và P/B của cổ phiếu"""

    # st.write("### 📊 Lịch sử P/E và P/B")

    # Lấy dữ liệu P/E và P/B
    pe_pb_data = get_pe_pb_history(symbol)

    if pe_pb_data is None:
        st.warning(f"Không thể lấy dữ liệu P/E và P/B cho mã {symbol}")
        return

    chart_data = pe_pb_data['data']
    stats = pe_pb_data['stats']

    # Hiển thị 2 cột cho 2 đồ thị
    col1, col2 = st.columns(2)

    with col1:
        st.write("#### P/E (Price-to-Earnings)")

        # Tạo DataFrame cho đường trung bình
        mean_pe = stats['pe']['mean']
        chart_data_with_mean = chart_data.copy()
        chart_data_with_mean['P/E Mean'] = mean_pe

        # Tạo biểu đồ line cho P/E
        base_pe = alt.Chart(chart_data_with_mean).encode(
            x=alt.X('time_label:N', axis=alt.Axis(
                title='Kỳ báo cáo', labelAngle=-45))
        )

        # Đường P/E thực tế
        line_pe = base_pe.mark_line(point=True, color='#2E86AB', strokeWidth=2).encode(
            y=alt.Y('P/E:Q', title='P/E', scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip('time_label:N', title='Kỳ'),
                alt.Tooltip('P/E:Q', title='P/E', format='.2f')
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
            y=alt.Y('P/E:Q')
        )

        # Kết hợp các layer
        chart_pe = (area_pe + line_pe + mean_line_pe).properties(
            height=300
        )

        st.altair_chart(chart_pe, use_container_width=True)

        # Hiển thị thống kê P/E
        pe_deviation = ((stats['pe']['current'] - mean_pe) / mean_pe) * 100

        st.markdown(f"""
        **Thống kê P/E:**
        - Hiện tại: **{stats['pe']['current']:.2f}**
        - Trung bình: {mean_pe:.2f}
        - Cao nhất: {stats['pe']['max']:.2f}
        - Thấp nhất: {stats['pe']['min']:.2f}
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

        # Tạo DataFrame cho đường trung bình
        mean_pb = stats['pb']['mean']
        chart_data_with_mean = chart_data.copy()
        chart_data_with_mean['P/B Mean'] = mean_pb

        # Tạo biểu đồ line cho P/B
        base_pb = alt.Chart(chart_data_with_mean).encode(
            x=alt.X('time_label:N', axis=alt.Axis(
                title='Kỳ báo cáo', labelAngle=-45))
        )

        # Đường P/B thực tế
        line_pb = base_pb.mark_line(point=True, color='#A23B72', strokeWidth=2).encode(
            y=alt.Y('P/B:Q', title='P/B', scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip('time_label:N', title='Kỳ'),
                alt.Tooltip('P/B:Q', title='P/B', format='.2f')
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
            y=alt.Y('P/B:Q')
        )

        # Kết hợp các layer
        chart_pb = (area_pb + line_pb + mean_line_pb).properties(
            height=300
        )

        st.altair_chart(chart_pb, use_container_width=True)

        # Hiển thị thống kê P/B
        pb_deviation = ((stats['pb']['current'] - mean_pb) / mean_pb) * 100

        st.markdown(f"""
        **Thống kê P/B:**
        - Hiện tại: **{stats['pb']['current']:.2f}**
        - Trung bình: {mean_pb:.2f}
        - Cao nhất: {stats['pb']['max']:.2f}
        - Thấp nhất: {stats['pb']['min']:.2f}
        """)

        if pb_deviation > 10:
            st.warning(
                f"⚠️ Cao hơn TB {pb_deviation:.1f}% - Có thể định giá cao")
        elif pb_deviation < -10:
            st.success(
                f"✓ Thấp hơn TB {abs(pb_deviation):.1f}% - Có thể định giá thấp")
        else:
            st.info(f"→ Gần mức TB ({pb_deviation:+.1f}%)")
