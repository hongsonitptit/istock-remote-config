import streamlit as st
import pandas as pd
import json
from vnstock import Vnstock
from datetime import datetime, timedelta
from utils.data_utils import get_deals
from logger import default_logger as logger
from streamlit_lightweight_charts import renderLightweightCharts
import time

@st.cache_data(ttl=3600)
def get_market_data(symbols, start_date):
    """
    Tải dữ liệu giá đóng cửa lịch sử cho các mã cổ phiếu và chỉ số VNINDEX, VN30.
    """
    market_data = {}
    vnstock_client = Vnstock()
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Lấy tất cả mã cổ phiếu + VNINDEX, VN30 để so sánh
    all_symbols = list(set(symbols) | {'VNINDEX', 'VN30'})
    
    progress_bar = st.progress(0)
    for i, sym in enumerate(all_symbols):
        logger.info(f"Loading history price data for {sym}")
        try:
            time.sleep(1)
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

def _draw_performance_chart(chart_df):
    """
    Vẽ biểu đồ so sánh hiệu suất tích lũy của danh mục với VN-Index và VN30 sử dụng Lightweight Charts.
    """
    st.write("### 📈 Biểu đồ so sánh Hiệu suất Tích lũy")
    
    # Chuẩn bị dữ liệu cho Lightweight Charts
    df = chart_df.copy()
    df['time'] = df['Ngày'].dt.strftime('%Y-%m-%d')
    
    # Chuyển đổi dữ liệu sang định dạng JSON mà Lightweight Charts yêu cầu
    portfolio_data = json.loads(df[['time', 'Danh mục']].rename(columns={'Danh mục': 'value'}).to_json(orient="records"))
    vni_data = json.loads(df[['time', 'VN-Index']].rename(columns={'VN-Index': 'value'}).to_json(orient="records"))
    vn30_data = json.loads(df[['time', 'VN30']].rename(columns={'VN30': 'value'}).to_json(orient="records"))

    # Cấu hình biểu đồ
    chart_options = {
        "height": 450,
        "layout": {
            "background": {"type": "solid", "color": "#1e222d"},
            "textColor": "#d1d4dc",
        },
        "grid": {
            "vertLines": {"color": "rgba(42, 46, 57, 0.6)"},
            "horzLines": {"color": "rgba(42, 46, 57, 0.6)"},
        },
        "timeScale": {
            "borderColor": "rgba(197, 203, 206, 0.8)",
            "timeVisible": True,
            "secondsVisible": False,
        },
        "rightPriceScale": {
            "borderColor": "rgba(197, 203, 206, 0.8)",
        },
        "crosshair": {
            "mode": 0, # Normal mode
        },
        "handleScroll": False,
        "handleScale": False,
    }

    # Cấu hình các đường dữ liệu
    series = [
        {
            "type": 'Line',
            "data": portfolio_data,
            "options": {
                "color": '#36A2EB',
                "lineWidth": 3,
                "title": "Danh mục",
            }
        },
        {
            "type": 'Line',
            "data": vni_data,
            "options": {
                "color": '#FF6384',
                "lineWidth": 2,
                "title": "VN-Index",
            }
        },
        {
            "type": 'Line',
            "data": vn30_data,
            "options": {
                "color": '#FFCE56',
                "lineWidth": 2,
                "title": "VN30",
            }
        }
    ]

    # Hiển thị biểu đồ
    renderLightweightCharts([
        {
            "chart": chart_options,
            "series": series
        }
    ], 'performance_chart')

def _display_portfolio_metrics(port_cum_growth, vni_cum_growth, vn30_cum_growth):
    """
    Hiển thị các thẻ chỉ số tóm tắt về lợi nhuận danh mục và VN-Index.
    """
    final_port_ret = (port_cum_growth.iloc[-1] - 1) * 100
    final_vni_ret = (vni_cum_growth.iloc[-1] - 1) * 100
    final_vn30_ret = (vn30_cum_growth.iloc[-1] - 1) * 100
    alpha = final_port_ret - final_vni_ret
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Lợi nhuận Danh mục", f"{final_port_ret:.2f}%", f"{final_port_ret:+.2f}%")
    m2.metric("Lợi nhuận VN-Index", f"{final_vni_ret:.2f}%", f"{final_vni_ret:+.2f}%")
    m3.metric("Lợi nhuận VN30", f"{final_vn30_ret:.2f}%", f"{final_vn30_ret:+.2f}%")
    m4.metric("Chênh lệch (Alpha)", f"{alpha:.2f}%", delta=round(alpha, 2), delta_color="normal")
    
    st.success(f"💡 Danh mục của bạn đang {'vượt trội' if alpha > 0 else 'kém hơn'} thị trường {abs(alpha):.2f}% kể từ khi bắt đầu đầu tư.")

@st.fragment
def _display_performance_table(portfolio_results):
    """
    Hiển thị bảng chi tiết hiệu quả đầu tư cho từng mã cổ phiếu.
    """
    st.write("### 📊 Chi tiết hiệu quả từng mã")
    res_df = pd.DataFrame(portfolio_results)
    # làm tròn gia_mua , gia_ban , loi_nhuan 
    res_df['Giá mua'] = res_df['Giá mua'].round(2)
    res_df['Giá hiện tại/bán'] = res_df['Giá hiện tại/bán'].round(2)
    res_df['Lợi nhuận (%)'] = res_df['Lợi nhuận (%)'].round(2)
    
    # Bộ lọc theo mã cổ phiếu
    col1, _ = st.columns([1, 2])
    with col1:
        search_symbol = st.text_input("🔍 Lọc theo mã cổ phiếu", "").strip().upper()
    
    if search_symbol:
        res_df = res_df[res_df['Mã'].str.contains(search_symbol, na=False)]
    
    # Định dạng màu cho cột lợi nhuận
    def highlight_profit(val):
        color = '#1ed760' if val > 0 else '#ff4b4b'
        return f'color: {color}; font-weight: bold'

    st.dataframe(res_df.style.map(highlight_profit, subset=['Lợi nhuận (%)']), width='stretch')

def show_portfolio_page():
    st.title("🤖 Phân tích Hiệu quả Danh mục")
    
    # 1. Lấy dữ liệu giao dịch
    transactions = get_deals()
    transactions = transactions.sort_values(by=['symbol', 'ngay_mua'])

    # transactions = transactions[transactions['ngay_mua'] >= '2025-01-01']
    # transactions = transactions[transactions['symbol'] == 'VHM']
    
    # 2. Dùng thư viện vnstock để tính giá mua và giá bán
    min_ngay_mua = transactions['ngay_mua'].min()
    market_prices = get_market_data(transactions['symbol'].unique(), min_ngay_mua)
    
    if 'VNINDEX' not in market_prices:
        st.error("❌ Không thể kết nối dữ liệu VN-Index. Vui lòng thử lại sau.")
        return

    # Chuẩn bị bảng giá hội tụ (aligned price table)
    all_dates = pd.date_range(start=min_ngay_mua, end=datetime.now(), freq='D')
    price_df = pd.DataFrame(index=all_dates)
    for sym, p_series in market_prices.items():
        # Reindex và fill để có giá cho mọi ngày (kể cả cuối tuần)
        price_df[sym] = p_series.reindex(all_dates).ffill()
    
    # Bỏ các ngày trống hoàn toàn ở đầu
    price_df = price_df.dropna(subset=['VNINDEX'])

    # 3. Tính lợi nhuận % chi tiết từng mã
    portfolio_results = []
    for idx, row in transactions.iterrows():
        sym = row['symbol']
        qty = row['khoi_luong']
        b_date = row['ngay_mua']
        s_date = row['ngay_ban']
        
        gia_mua = row['gia_mua']
        exit_price = row['gia_ban']
        
        if pd.isna(exit_price):
            if sym in market_prices and not market_prices[sym].empty:
                exit_price = market_prices[sym].iloc[-1]
            else:
                exit_price = gia_mua
        
        profit_pct = (exit_price - gia_mua) / gia_mua * 100
        status = "Đã bán" if s_date else "Đang nắm giữ"
        
        portfolio_results.append({
            'Mã': sym,
            'Ngày mua': b_date,
            'Ngày bán': s_date or 'N/A',
            'Số lượng': qty,
            'Giá mua': round(gia_mua, 2),
            'Giá hiện tại/bán': round(exit_price, 2),
            'Lợi nhuận (%)': round(profit_pct, 2),
            'Trạng thái': status
        })

    # 4. TÍNH TOÁN HIỆU SUẤT TÍCH LŨY
    returns_df = price_df.pct_change().fillna(0)
    
    # Tính trọng số danh mục hàng ngày dựa trên giá trị nắm giữ
    weights = pd.DataFrame(0.0, index=price_df.index, columns=transactions['symbol'].unique())
    for idx, row in transactions.iterrows():
        sym = row['symbol']
        b_date = pd.to_datetime(row['ngay_mua'])
        s_date = pd.to_datetime(row['ngay_ban']) if row['ngay_ban'] else None
        qty = row['khoi_luong']
        
        mask = (price_df.index >= b_date)
        if s_date:
            mask = mask & (price_df.index <= s_date)
        
        weights.loc[mask, sym] += qty * price_df.loc[mask, sym]

    # Tổng giá trị danh mục hàng ngày
    portfolio_total_value = weights.sum(axis=1)
    comparison_dates = price_df.index
    
    if len(comparison_dates) < 2:
        st.info("Chưa đủ dữ liệu lịch sử để vẽ biểu đồ.")
        return

    # Chuẩn hóa trọng số để tính Daily Return của danh mục
    normalized_weights = weights.div(portfolio_total_value.replace(0, 1), axis=0)
    
    # Portfolio Daily Return = Sum of (Weight_i * Return_i)
    port_daily_ret = (returns_df[normalized_weights.columns] * normalized_weights).sum(axis=1)
    port_daily_ret = port_daily_ret[comparison_dates]
    
    # Cumulative Growth (Bắt đầu từ 1.0)
    port_cum_growth = (1 + port_daily_ret).cumprod()
    
    # VNINDEX/VN30 Growth trong cùng khoảng thời gian
    vni_daily_ret = returns_df.loc[comparison_dates, 'VNINDEX']
    vni_cum_growth = (1 + vni_daily_ret).cumprod()
    
    vn30_daily_ret = returns_df.loc[comparison_dates, 'VN30']
    vn30_cum_growth = (1 + vn30_daily_ret).cumprod()
    
    # Chuẩn bị dữ liệu cho Altair
    chart_df = pd.DataFrame({
        'Ngày': comparison_dates,
        'Danh mục': (port_cum_growth - 1) * 100,
        'VN-Index': (vni_cum_growth - 1) * 100,
        'VN30': (vn30_cum_growth - 1) * 100
    })
    # 5. Hiển thị Dashboard
    # Vẽ đồ thị
    _draw_performance_chart(chart_df)

    # Hiển thị thẻ tóm tắt
    _display_portfolio_metrics(port_cum_growth, vni_cum_growth, vn30_cum_growth)

    # Hiển thị bảng chi tiết
    _display_performance_table(portfolio_results)


if __name__ == "__main__":
    show_portfolio_page()
