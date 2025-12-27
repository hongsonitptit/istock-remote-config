import streamlit as st
import pandas as pd
import altair as alt
from vnstock import Vnstock
from datetime import datetime, timedelta
from logger import default_logger as logger

def show_portfolio_page():
    st.title("🤖 Phân tích Hiệu quả Danh mục")
    
    # 1. Tạo tập dữ liệu mẫu (20 mẫu dữ liệu)
    if 'portfolio_data' not in st.session_state:
        st.session_state.portfolio_data = [
            {'symbol': 'FPT', 'buy_date': '2024-01-05', 'sell_date': None, 'quantity': 1000},
            {'symbol': 'VCB', 'buy_date': '2024-02-10', 'sell_date': '2024-06-15', 'quantity': 500},
            {'symbol': 'HPG', 'buy_date': '2024-03-15', 'sell_date': None, 'quantity': 2000},
            {'symbol': 'TCB', 'buy_date': '2024-01-20', 'sell_date': '2024-05-10', 'quantity': 1500},
            {'symbol': 'MWG', 'buy_date': '2024-04-01', 'sell_date': None, 'quantity': 800},
            {'symbol': 'VIC', 'buy_date': '2024-02-05', 'sell_date': None, 'quantity': 400},
            {'symbol': 'VNM', 'buy_date': '2024-05-20', 'sell_date': None, 'quantity': 600},
            {'symbol': 'DGC', 'buy_date': '2024-01-10', 'sell_date': '2024-08-01', 'quantity': 300},
            {'symbol': 'SSI', 'buy_date': '2024-03-01', 'sell_date': None, 'quantity': 1200},
            {'symbol': 'PVD', 'buy_date': '2024-04-15', 'sell_date': '2024-09-10', 'quantity': 1000},
            {'symbol': 'STB', 'buy_date': '2024-02-15', 'sell_date': None, 'quantity': 2000},
            {'symbol': 'MBB', 'buy_date': '2024-01-25', 'sell_date': None, 'quantity': 2500},
            {'symbol': 'VRE', 'buy_date': '2024-05-05', 'sell_date': '2024-11-20', 'quantity': 700},
            {'symbol': 'HDB', 'buy_date': '2024-06-01', 'sell_date': None, 'quantity': 1100},
            {'symbol': 'GAS', 'buy_date': '2024-03-10', 'sell_date': None, 'quantity': 200},
            {'symbol': 'PLX', 'buy_date': '2024-07-15', 'sell_date': '2024-12-01', 'quantity': 500},
            {'symbol': 'POW', 'buy_date': '2024-01-15', 'sell_date': None, 'quantity': 1500},
            {'symbol': 'MSN', 'buy_date': '2024-08-10', 'sell_date': None, 'quantity': 400},
            {'symbol': 'SAB', 'buy_date': '2024-09-01', 'sell_date': None, 'quantity': 100},
            {'symbol': 'VJC', 'buy_date': '2024-10-15', 'sell_date': None, 'quantity': 300},
        ]
    
    transactions = pd.DataFrame(st.session_state.portfolio_data)
    
    with st.expander("📝 Xem danh sách giao dịch mẫu (20 mã)"):
        st.dataframe(transactions, use_container_width=True)

    # 2. Dùng thư viện vnstock để tính giá mua và giá bán
    @st.cache_data(ttl=3600)
    def get_market_data(symbols, start_date):
        market_data = {}
        vnstock_client = Vnstock()
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Lấy tất cả mã cổ phiếu + VNINDEX để so sánh
        all_symbols = list(set(symbols) | {'VNINDEX'})
        
        progress_bar = st.progress(0)
        for i, sym in enumerate(all_symbols):
            try:
                # Ưu tiên VCI vì dữ liệu chỉ số ổn định
                source = 'VCI'
                stock = vnstock_client.stock(symbol=sym, source=source)
                df = stock.quote.history(start=start_date, end=end_date)
                
                if df is not None and not df.empty:
                    df['time'] = pd.to_datetime(df['time'])
                    df = df.set_index('time')
                    market_data[sym] = df['close']
                else:
                    logger.warning(f"Không có dữ liệu cho {sym}")
            except Exception as e:
                logger.error(f"Lỗi khi tải {sym}: {e}")
            
            progress_bar.progress((i + 1) / len(all_symbols))
        progress_bar.empty()
        return market_data

    min_buy_date = transactions['buy_date'].min()
    market_prices = get_market_data(transactions['symbol'].unique(), min_buy_date)
    
    if 'VNINDEX' not in market_prices:
        st.error("❌ Không thể kết nối dữ liệu VN-Index. Vui lòng thử lại sau.")
        return

    # Chuẩn bị bảng giá hội tụ (aligned price table)
    all_dates = pd.date_range(start=min_buy_date, end=datetime.now(), freq='D')
    price_df = pd.DataFrame(index=all_dates)
    for sym, p_series in market_prices.items():
        # Reindex và fill để có giá cho mọi ngày (kể cả cuối tuần)
        price_df[sym] = p_series.reindex(all_dates).ffill()
    
    # Bỏ các ngày trống hoàn toàn ở đầu
    price_df = price_df.dropna(subset=['VNINDEX'])

    # 3. Tính lợi nhuận % và so sánh với VN-Index
    
    # Tính toán chi tiết từng mã
    portfolio_results = []
    for idx, row in transactions.iterrows():
        sym = row['symbol']
        b_date = pd.to_datetime(row['buy_date'])
        s_date = pd.to_datetime(row['sell_date']) if row['sell_date'] else None
        qty = row['quantity']
        
        if sym not in price_df.columns:
            continue
            
        # Lấy giá mua (gần nhất với ngày mua)
        buy_price = price_df.loc[b_date, sym]
        
        # Giá hiện tại hoặc giá bán
        curr_date = s_date if s_date else price_df.index[-1]
        exit_price = price_df.loc[curr_date, sym]
        
        profit_pct = (exit_price - buy_price) / buy_price * 100
        status = "Đã bán" if s_date else "Đang nắm giữ"
        
        portfolio_results.append({
            'Mã': sym,
            'Ngày mua': row['buy_date'],
            'Ngày bán': row['sell_date'] or 'N/A',
            'Sổ lượng': qty,
            'Giá mua': round(buy_price, 2),
            'Giá hiện tại/bán': round(exit_price, 2),
            'Lợi nhuận (%)': round(profit_pct, 2),
            'Trạng thái': status
        })

    st.write("### 📊 Chi tiết hiệu quả từng mã")
    res_df = pd.DataFrame(portfolio_results)
    
    # Định dạng màu cho cột lợi nhuận
    def highlight_profit(val):
        color = '#1ed760' if val > 0 else '#ff4b4b'
        return f'color: {color}; font-weight: bold'

    st.dataframe(res_df.style.map(highlight_profit, subset=['Lợi nhuận (%)']), use_container_width=True)

    # VẼ BIỂU ĐỒ LỊCH SỬ SO SÁNH
    st.write("### 📈 Biểu đồ so sánh Hiệu suất Tích lũy")
    
    # Tính lợi suất hàng ngày (Daily Returns)
    returns_df = price_df.pct_change().fillna(0)
    
    # Tính trọng số danh mục hàng ngày dựa trên giá trị nắm giữ
    weights = pd.DataFrame(0.0, index=price_df.index, columns=transactions['symbol'].unique())
    for idx, row in transactions.iterrows():
        sym = row['symbol']
        b_date = pd.to_datetime(row['buy_date'])
        s_date = pd.to_datetime(row['sell_date']) if row['sell_date'] else None
        qty = row['quantity']
        
        mask = (price_df.index >= b_date)
        if s_date:
            mask = mask & (price_df.index <= s_date)
        
        weights.loc[mask, sym] += qty * price_df.loc[mask, sym]

    # Tổng giá trị danh mục hàng ngày
    portfolio_total_value = weights.sum(axis=1)
    
    # Lọc những ngày có giá trị đầu tư > 0
    active_mask = portfolio_total_value > 0
    active_dates = price_df.index[active_mask]
    
    if len(active_dates) < 2:
        st.info("Chưa đủ dữ liệu lịch sử để vẽ biểu đồ.")
        return

    # Chuẩn hóa trọng số để tính Daily Return của danh mục
    normalized_weights = weights.div(portfolio_total_value.replace(0, 1), axis=0)
    
    # Portfolio Daily Return = Sum of (Weight_i * Return_i)
    port_daily_ret = (returns_df[normalized_weights.columns] * normalized_weights).sum(axis=1)
    port_daily_ret = port_daily_ret[active_dates]
    
    # Cumulative Growth (Bắt đầu từ 100)
    port_cum_growth = (1 + port_daily_ret).cumprod()
    
    # VNINDEX Growth trong cùng khoảng thời gian
    vni_daily_ret = returns_df.loc[active_dates, 'VNINDEX']
    vni_cum_growth = (1 + vni_daily_ret).cumprod()
    
    # Chuẩn bị dữ liệu cho Altair
    # (Trường hợp index đầu tiên, cumprod là 1.0, ta có thể prepend 1.0 nếu cần)
    chart_df = pd.DataFrame({
        'Ngày': active_dates,
        'Danh mục': (port_cum_growth - 1) * 100,
        'VN-Index': (vni_cum_growth - 1) * 100
    })
    
    chart_melted = chart_df.melt('Ngày', var_name='Đối tượng', value_name='Tỉ suất lợi nhuận (%)')

    # Vẽ biểu đồ với Altair (Glassmorphism aesthetics)
    line_chart = alt.Chart(chart_melted).mark_line(strokeWidth=3, interpolate='monotone').encode(
        x=alt.X('Ngày:T', axis=alt.Axis(title='Thời gian', format='%d/%m/%Y', labelAngle=-45)),
        y=alt.Y('Tỉ suất lợi nhuận (%):Q', axis=alt.Axis(title='Lợi nhuận tích lũy (%)')),
        color=alt.Color('Đối tượng:N', scale=alt.Scale(range=['#36A2EB', '#FF6384']), legend=alt.Legend(orient='top-left')),
        tooltip=[alt.Tooltip('Ngày:T', format='%d/%m/%Y'), 'Đối tượng:N', alt.Tooltip('Tỉ suất lợi nhuận (%):Q', format='.2f')]
    ).properties(
        height=450
    ).interactive()

    st.altair_chart(line_chart, use_container_width=True)

    # Hiển thị thẻ tóm tắt (Highlight metrics)
    final_port_ret = (port_cum_growth.iloc[-1] - 1) * 100
    final_vni_ret = (vni_cum_growth.iloc[-1] - 1) * 100
    alpha = final_port_ret - final_vni_ret
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Lợi nhuận Danh mục", f"{final_port_ret:.2f}%", f"{final_port_ret:+.2f}%")
    m2.metric("Lợi nhuận VN-Index", f"{final_vni_ret:.2f}%", f"{final_vni_ret:+.2f}%")
    m3.metric("Chênh lệch (Alpha)", f"{alpha:.2f}%", delta=round(alpha, 2), delta_color="normal")

    st.success(f"💡 Danh mục của bạn đang {'vượt trội' if alpha > 0 else 'kém hơn'} thị trường {abs(alpha):.2f}% kể từ khi bắt đầu đầu tư.")

if __name__ == "__main__":
    show_portfolio_page()
