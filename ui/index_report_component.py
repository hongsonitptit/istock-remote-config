import streamlit as st
import altair as alt
import pandas as pd
from utils.api_utils import get_finance_history 
from utils.data_utils import get_main_stock_data
from datetime import datetime, timedelta

def get_latest_reported_quarter(date_obj):
    """
    Xác định quý báo cáo gần nhất dựa trên ngày hiện tại.
    """
    year = date_obj.year
    month = date_obj.month
    day = date_obj.day
    
    if (month > 10) or (month == 10 and day > 30):
        return year, 3
    elif (month > 7) or (month == 7 and day > 30):
        return year, 2
    elif (month > 4) or (month == 4 and day > 30):
        return year, 1
    elif (month > 1) or (month == 1 and day > 30):
        return year - 1, 4
    else:
        return year - 1, 3

def get_previous_quarters(year, quarter, num_quarters=4):
    """Lấy danh sách n quý liên tiếp lùi về quá khứ"""
    quarters = []
    current_y, current_q = year, quarter
    for _ in range(num_quarters):
        quarters.append((current_y, current_q))
        if current_q == 1:
            current_q = 4
            current_y -= 1
        else:
            current_q -= 1
    return quarters

def parse_eps_financial_data(df, source='TCBS'):
    """
    Chuyển đổi dữ liệu tài chính (từ TCBS hoặc VCI) về dạng chuẩn dictionary: {(year, quarter): eps_value}
    """
    eps_map = {}
    
    if df is None or df.empty:
        return eps_map

    try:
        if source == 'VCI':
            flat_cols = []
            for col in df.columns:
                if isinstance(col, tuple):
                    flat_cols.append(" - ".join(map(str, col)))
                else:
                    flat_cols.append(str(col))
            
            eps_col_idx = -1
            best_match = None
            
            for i, col_name in enumerate(flat_cols):
                c_upper = col_name.upper()
                if 'EPS' in c_upper:
                    if 'TTM' not in c_upper:
                        best_match = i
                        break 
                    elif best_match is None:
                        best_match = i
            
            if best_match is not None:
                year_col_idx = -1
                period_col_idx = -1
                
                for i, col_name in enumerate(flat_cols):
                    if 'Năm' in col_name or 'Year' in col_name:
                        year_col_idx = i
                    if 'Kỳ' in col_name or 'Quarter' in col_name or 'LengthReport' in col_name:
                        period_col_idx = i
                
                if year_col_idx != -1 and period_col_idx != -1:
                    for idx, row in df.iterrows():
                        try:
                            y = int(row.iloc[year_col_idx])
                            q = int(row.iloc[period_col_idx])
                            val = row.iloc[best_match]
                            if pd.notna(val) and val != 0:
                                eps_map[(y, q)] = float(val)
                        except:
                            continue
            else:
                 print("Không tìm thấy cột EPS trong dữ liệu VCI.")

        else: # TCBS
            eps_col = 'earning_per_share'
            if eps_col not in df.columns:
                candidates = [c for c in df.columns if 'earn' in c.lower() or 'eps' in c.lower()]
                if candidates:
                    eps_col = candidates[0]
                else:
                    return eps_map

            for idx, row in df.iterrows():
                try:
                    parts = str(idx).split('-Q')
                    if len(parts) == 2:
                        y = int(parts[0])
                        q = int(parts[1])
                        val = row[eps_col]
                        if pd.notna(val):
                            eps_map[(y, q)] = float(val)
                except:
                    continue
                    
    except Exception as e:
        print(f"Lỗi khi parse dữ liệu tài chính ({source}): {e}")
        
    return eps_map

def calculate_pe_history(symbol) -> pd.DataFrame:
    print(f"Bắt đầu tính toán P/E lịch sử 10 năm cho mã {symbol}...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10*365)
    
    # 1. Lấy dữ liệu GIÁ (Ưu tiên VCI)
    print(f"- Đang tải dữ liệu giá từ {start_date.strftime('%Y-%m-%d')} đến {end_date.strftime('%Y-%m-%d')}...")
    source_used = 'VCI'
    try:
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        df_price = stock.quote.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
        
        if df_price is None or df_price.empty:
            print("VCI trả về rỗng, thử TCBS...")
            stock = Vnstock().stock(symbol=symbol, source='TCBS')
            df_price = stock.quote.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
            source_used = 'TCBS'

        if df_price is None or df_price.empty:
            print("Không thể lấy dữ liệu giá từ cả VCI và TCBS.")
            return

        df_price['time'] = pd.to_datetime(df_price['time'])
        df_price = df_price.sort_values('time')
        print(f"  -> Đã lấy {len(df_price)} dòng dữ liệu giá (Nguồn: {source_used})")

    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu giá: {e}")
        return

    # 2. Lấy dữ liệu EPS (Ưu tiên VCI)
    print(f"- Đang tải dữ liệu tài chính (EPS)...")
    eps_map = {}
    
    try:
        print("  -> Thử nguồn VCI...")
        stock_vci = Vnstock().stock(symbol=symbol, source='VCI')
        df_ratio_vci = stock_vci.finance.ratio(period='quarter', dropna=False, lang='vi')
        eps_map = parse_eps_financial_data(df_ratio_vci, source='VCI')
    except Exception as e:
        print(f"  -> VCI lỗi: {e}")
    
    if not eps_map:
        try:
            print("  -> Thử nguồn TCBS...")
            stock_tcbs = Vnstock().stock(symbol=symbol, source='TCBS')
            df_ratio_tcbs = stock_tcbs.finance.ratio(period='quarter', dropna=False)
            eps_map = parse_eps_financial_data(df_ratio_tcbs, source='TCBS')
        except Exception as e:
             print(f"  -> TCBS lỗi: {e}")

    if not eps_map:
        print("Không thể lấy dữ liệu EPS từ bất kỳ nguồn nào.")
        return

    print(f"  -> Tìm thấy dữ liệu EPS cho {len(eps_map)} quý.")

    # 3. Tính toán P/E
    pe_history = []
    dates = []
    prices = []
    eps_history = []
    
    print("- Đang tính P/E...")
    for _, row in df_price.iterrows():
        current_date_obj = row['time']
        price = row['close']
        
        # Nếu data trả về giá dạng nghìn đồng (ví dụ 26.5 thay vì 26500), cần nhân 1000
        # HPG giá ~26000. Nếu row['close'] < 1000, chắc chắn là nghìn đồng.
        if price < 500: # Threshold an toàn
            price = price * 1000
            
        report_year, report_quarter = get_latest_reported_quarter(current_date_obj)
        quarters_to_sum = get_previous_quarters(report_year, report_quarter, 4)
        
        ttm_eps = 0
        missing_count = 0
        
        for q_y, q_q in quarters_to_sum:
            val = eps_map.get((q_y, q_q))
            if val is None:
                missing_count += 1
            else:
                ttm_eps += val
        
        if missing_count == 0 and ttm_eps > 0:
            pe = price / ttm_eps
            pe_history.append(pe)
            dates.append(current_date_obj)
            prices.append(price)
            eps_history.append(ttm_eps)
        else:
            pass 

    if not dates:
        print("Không tính được P/E nào.")
        return

    df_plot = pd.DataFrame({
        'time': dates,
        'pe': pe_history,
        'price': prices,
        'eps_ttm': eps_history
    })
    return df_plot


def parse_bvps_financial_data(df, source='TCBS'):
    """
    Chuyển đổi dữ liệu tài chính (từ TCBS hoặc VCI) về dạng chuẩn dictionary: {(year, quarter): bvps_value}
    """
    bvps_map = {}
    
    if df is None or df.empty:
        return bvps_map

    try:
        if source == 'VCI':
            flat_cols = []
            for col in df.columns:
                if isinstance(col, tuple):
                    flat_cols.append(" - ".join(map(str, col)))
                else:
                    flat_cols.append(str(col))
            
            bvps_col_idx = -1
            
            # Tìm cột BVPS
            for i, col_name in enumerate(flat_cols):
                c_upper = col_name.upper()
                if 'BVPS' in c_upper:
                   bvps_col_idx = i
                   break
            
            if bvps_col_idx != -1:
                year_col_idx = -1
                period_col_idx = -1
                
                for i, col_name in enumerate(flat_cols):
                    if 'Năm' in col_name or 'Year' in col_name:
                        year_col_idx = i
                    if 'Kỳ' in col_name or 'Quarter' in col_name or 'LengthReport' in col_name:
                        period_col_idx = i
                
                if year_col_idx != -1 and period_col_idx != -1:
                    for idx, row in df.iterrows():
                        try:
                            y = int(row.iloc[year_col_idx])
                            q = int(row.iloc[period_col_idx])
                            val = row.iloc[bvps_col_idx]
                            if pd.notna(val) and val != 0:
                                bvps_map[(y, q)] = float(val)
                        except:
                            continue
            else:
                 print("Không tìm thấy cột BVPS trong dữ liệu VCI.")

        else: # TCBS
            bvps_col = 'book_value_per_share' # Tên dự đoán, cần kiểm tra nếu code chạy thực tế với TCBS
            # Thông thường TCBS cột là 'price_to_book' hoặc 'book_value_per_share', trong ratio
            # Nếu không tìm thấy chính xác, thử tìm
            if bvps_col not in df.columns:
                candidates = [c for c in df.columns if 'book' in c.lower() or 'bvps' in c.lower()]
                if candidates:
                    bvps_col = candidates[0]
                else:
                    return bvps_map

            for idx, row in df.iterrows():
                try:
                    parts = str(idx).split('-Q')
                    if len(parts) == 2:
                        y = int(parts[0])
                        q = int(parts[1])
                        val = row[bvps_col]
                        if pd.notna(val):
                            bvps_map[(y, q)] = float(val)
                except:
                    continue
                    
    except Exception as e:
        print(f"Lỗi khi parse dữ liệu tài chính ({source}): {e}")
        
    return bvps_map

def calculate_pb_history(symbol):
    print(f"Bắt đầu tính toán P/B lịch sử 5 năm cho mã {symbol}...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    
    # 1. Lấy dữ liệu GIÁ (Ưu tiên VCI)
    print(f"- Đang tải dữ liệu giá từ {start_date.strftime('%Y-%m-%d')} đến {end_date.strftime('%Y-%m-%d')}...")
    source_used = 'VCI'
    try:
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        df_price = stock.quote.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
        
        if df_price is None or df_price.empty:
            print("VCI trả về rỗng, thử TCBS...")
            stock = Vnstock().stock(symbol=symbol, source='TCBS')
            df_price = stock.quote.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
            source_used = 'TCBS'

        if df_price is None or df_price.empty:
            print("Không thể lấy dữ liệu giá từ cả VCI và TCBS.")
            return

        df_price['time'] = pd.to_datetime(df_price['time'])
        df_price = df_price.sort_values('time')
        print(f"  -> Đã lấy {len(df_price)} dòng dữ liệu giá (Nguồn: {source_used})")

    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu giá: {e}")
        return

    # 2. Lấy dữ liệu BVPS (Ưu tiên VCI)
    print(f"- Đang tải dữ liệu tài chính (BVPS)...")
    bvps_map = {}
    
    try:
        print("  -> Thử nguồn VCI...")
        stock_vci = Vnstock().stock(symbol=symbol, source='VCI')
        df_ratio_vci = stock_vci.finance.ratio(period='quarter', dropna=False, lang='vi')
        bvps_map = parse_bvps_financial_data(df_ratio_vci, source='VCI')
    except Exception as e:
        print(f"  -> VCI lỗi: {e}")
    
    if not bvps_map:
        try:
            print("  -> Thử nguồn TCBS...")
            stock_tcbs = Vnstock().stock(symbol=symbol, source='TCBS')
            df_ratio_tcbs = stock_tcbs.finance.ratio(period='quarter', dropna=False)
            bvps_map = parse_bvps_financial_data(df_ratio_tcbs, source='TCBS')
        except Exception as e:
             print(f"  -> TCBS lỗi: {e}")

    if not bvps_map:
        print("Không thể lấy dữ liệu BVPS từ bất kỳ nguồn nào.")
        return

    print(f"  -> Tìm thấy dữ liệu BVPS cho {len(bvps_map)} quý.")

    # 3. Tính toán P/B
    pb_history = []
    dates = []
    prices = []
    bvps_history = []
    
    print("- Đang tính P/B...")
    for _, row in df_price.iterrows():
        current_date_obj = row['time']
        price = row['close']
        
        # Nếu data trả về giá dạng nghìn đồng (ví dụ 26.5 thay vì 26500), cần nhân 1000
        if price < 500: # Threshold an toàn
            price = price * 1000
            
        report_year, report_quarter = get_latest_reported_quarter(current_date_obj)
        
        # Với P/B, chỉ cần lấy BVPS của quý gần nhất
        bvps = bvps_map.get((report_year, report_quarter))
        
        if bvps and bvps > 0:
            pb = price / bvps
            pb_history.append(pb)
            dates.append(current_date_obj)
            prices.append(price)
            bvps_history.append(bvps)
        else:
            pass 

    if not dates:
        print("Không tính được P/B nào.")
        return

    df_plot = pd.DataFrame({
        'time': dates,
        'pb': pb_history,
        'price': prices,
        'bvps': bvps_history
    })

    return df_plot


def display_summary_reports(symbol):
    """Hiển thị đồ thị lịch sử P/E và P/B của cổ phiếu"""
    # Thử tính P/E và P/B bằng thư viện vnstock
    pe_df = calculate_pe_history(symbol)
    pb_df = calculate_pb_history(symbol)

    # nếu không tính được pe/pb bằng thư viện vnstock thì lấy data từ API
    if pe_df is None or pe_df.empty or pb_df is None or pb_df.empty:
        print("Không tính được P/E và P/B bằng thư viện vnstock, thử lấy từ API...")
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
