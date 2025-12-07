"""
Utility functions để làm việc với thư viện vnstock
"""
import pandas as pd
from vnstock import Vnstock
from logger import default_logger as logger
from datetime import datetime, timedelta


def get_pe_pb_history(symbol: str, recent_years: int = 10):
    """
    Lấy lịch sử P/E và P/B của cổ phiếu từ vnstock
    
    Args:
        symbol: Mã cổ phiếu
        recent_years: Số năm gần đây cần lấy (mặc định = 10)
        
    Returns:
        dict: {
            'data': DataFrame với các cột ['time_label', 'P/E', 'P/B'],
            'stats': dict chứa thống kê P/E và P/B
        }
        Trả về None nếu có lỗi
    """
    try:
        stock = Vnstock().stock(symbol=symbol, source='VCI')

        # Lấy dữ liệu chỉ số tài chính theo quý
        logger.info(
            f"Đang lấy dữ liệu P/E và P/B cho {symbol} ({recent_years} năm gần đây)...")
        ratio_data = stock.finance.ratio(
            period='quarter', lang='vi', dropna=True)

        # Tìm các cột chứa P/E và P/B
        pe_columns = [col for col in ratio_data.columns if 'P/E' in str(col)]
        pb_columns = [col for col in ratio_data.columns if 'P/B' in str(col)]

        if not pe_columns or not pb_columns:
            logger.warning(f"Không tìm thấy dữ liệu P/E hoặc P/B cho {symbol}")
            return None

        # Lấy cột P/E và P/B đầu tiên
        pe_col = pe_columns[0]
        pb_col = pb_columns[0]

        logger.info(f"Sử dụng cột P/E: {pe_col}, P/B: {pb_col}")

        # Tạo DataFrame mới với dữ liệu P/E và P/B
        chart_data = pd.DataFrame({
            'P/E': ratio_data[pe_col],
            'P/B': ratio_data[pb_col]
        })

        # Tạo label thời gian và lọc theo số năm gần đây
        try:
            if ('Meta', 'Năm') in ratio_data.columns and ('Meta', 'Kỳ') in ratio_data.columns:
                # Thêm cột year và quarter để sắp xếp
                chart_data['year'] = ratio_data[('Meta', 'Năm')].astype(int)
                chart_data['quarter'] = ratio_data[('Meta', 'Kỳ')].astype(int)

                # Tạo time_label với format {Năm}-Q{Kỳ}
                chart_data['time_label'] = chart_data['year'].astype(
                    str) + '-Q' + chart_data['quarter'].astype(str)
                logger.info("Sử dụng cột 'Năm' và 'Kỳ' để tạo trục thời gian")

                # Lọc dữ liệu theo số năm gần đây
                if len(chart_data) > 0:
                    max_year = chart_data['year'].max()
                    min_year = max_year - recent_years + 1
                    chart_data = chart_data[chart_data['year'] >= min_year]
                    logger.info(
                        f"Lọc dữ liệu từ năm {min_year} đến {max_year}")

                # Sắp xếp theo năm và quý (từ cũ đến mới)
                chart_data = chart_data.sort_values(
                    by=['year', 'quarter']).reset_index(drop=True)

                # Xóa cột year và quarter sau khi sắp xếp
                chart_data = chart_data.drop(columns=['year', 'quarter'])
            else:
                chart_data['time_label'] = chart_data.index.astype(str)
                logger.info("Sử dụng index mặc định cho trục thời gian")
        except Exception as e:
            logger.warning(f"Lỗi khi tạo label thời gian: {e}")
            chart_data['time_label'] = chart_data.index.astype(str)

        # Tính thống kê
        stats = {
            'pe': {
                'current': float(chart_data['P/E'].iloc[-1]) if len(chart_data) > 0 else 0,
                'mean': float(chart_data['P/E'].mean()),
                'max': float(chart_data['P/E'].max()),
                'min': float(chart_data['P/E'].min()),
                'std': float(chart_data['P/E'].std())
            },
            'pb': {
                'current': float(chart_data['P/B'].iloc[-1]) if len(chart_data) > 0 else 0,
                'mean': float(chart_data['P/B'].mean()),
                'max': float(chart_data['P/B'].max()),
                'min': float(chart_data['P/B'].min()),
                'std': float(chart_data['P/B'].std())
            }
        }

        logger.info(
            f"Lấy thành công {len(chart_data)} quý dữ liệu P/E và P/B cho {symbol}")

        return {
            'data': chart_data,
            'stats': stats
        }

    except Exception as e:
        logger.exception(f"Lỗi khi lấy dữ liệu P/E và P/B cho {symbol}: {e}")
        return None


def get_company_info(symbol: str) -> dict:
    try:
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        company_info = stock.company.overview()
        info = company_info.iloc[0]
        industry_list = list(set([info[col] for col in company_info.columns.tolist() if col.startswith('icb_')]))
        industry = ", ".join(industry_list)

        print("\n\nĐang lấy dữ liệu giao dịch 20 phiên gần nhất...")

        # Tính ngày bắt đầu (lấy thêm 30 ngày để đảm bảo có đủ 20 phiên giao dịch)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        # Lấy lịch sử giá
        price_history = stock.quote.history(
            start=start_date,
            end=end_date,
            interval='1D'
        )
        # Tính khối lượng giao dịch trung bình 20 phiên
        if not price_history.empty and 'volume' in price_history.columns:
            # Lấy 20 phiên gần nhất
            last_20_sessions = price_history.tail(20)
            avg_volume_20 = last_20_sessions['volume'].mean()

            # Format số với dấu phẩy ngăn cách hàng nghìn
            avg_volume_20_formatted = f"{avg_volume_20:,.0f}"
        else:
            avg_volume_20 = None
            avg_volume_20_formatted = "N/A"

        company_name = info['company_profile'].split("(")[0]

        return {
            'name': company_name,
            'industry': industry,
            'avg_trading_volume': avg_volume_20
        }
    except Exception as e:
        logger.exception(f"Lỗi khi lấy thông tin cổ phiếu cho {symbol}: {e}")
        return {
            'name': "",
            'industry': "",
            'avg_trading_volume': ""
        }


# Test function
if __name__ == "__main__":
    # Test với mã FPT
    result = get_company_info("FPT")
    if result:
        print("\n=== Thông tin cổ phiếu ===")
        print(result)
