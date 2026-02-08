"""
Utility functions để làm việc với thư viện vnstock
"""
import os
import pandas as pd
from vnstock import Vnstock
import streamlit as st
from logger import default_logger as logger
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from vnstock import register_user, check_status
register_user(api_key=os.getenv('VNSTOCK_API_KEY'))
check_status()

# Try to import TA-Lib, set flag if available
try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False



@st.cache_data(ttl=60)
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
        try:
            stock = Vnstock().stock(symbol=symbol, source='KBS')
        except Exception as e:
            logger.warning(f"⚠️  KBS lỗi hoặc không hỗ trợ mã {symbol}, thử dùng VCI: {e}")
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



@st.cache_data(ttl=60)
def get_company_info(symbol: str) -> dict:
    try:
        try:
            stock = Vnstock().stock(symbol=symbol, source='KBS')
        except Exception as e:
            logger.warning(f"⚠️  KBS lỗi hoặc không hỗ trợ mã {symbol}, thử dùng VCI: {e}")
            stock = Vnstock().stock(symbol=symbol, source='VCI')
        company_info = stock.company.overview()
        info = company_info.iloc[0]
        industry_list = list(set([info[col] for col in company_info.columns.tolist() if col.startswith('icb_')]))
        industry = ", ".join(industry_list)

        logger.info("Đang lấy dữ liệu giao dịch 20 phiên gần nhất...")

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
            'avg_trading_volume': None
        }


def calculate_rsi_14(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Tính RSI (Relative Strength Index) sử dụng TA-Lib hoặc pandas
    
    Args:
        data (pd.DataFrame): DataFrame chứa cột 'close' (giá đóng cửa)
        period (int): Chu kỳ tính RSI, mặc định là 14
    
    Returns:
        pd.Series: Series chứa giá trị RSI
    """
    if HAS_TALIB:
        # Sử dụng TA-Lib (chuẩn công nghiệp)
        rsi = talib.RSI(data['close'].values, timeperiod=period)
        return pd.Series(rsi, index=data.index)
    else:
        # Sử dụng phương pháp Wilder's Smoothing (chuẩn RSI)
        # Đây là phương pháp chính xác theo công thức gốc của J. Welles Wilder
        delta = data['close'].diff()
        
        # Tách lãi và lỗ
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Tính trung bình lãi/lỗ ban đầu (SMA cho period đầu tiên)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        
        # Áp dụng Wilder's Smoothing cho các giá trị tiếp theo
        for i in range(period, len(data)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + loss.iloc[i]) / period
        
        # Tính RS và RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


@st.cache_data(ttl=60)
def get_list_rsi_14(symbol: str, days: int = 30, rsi_period: int = 14):
    """
    Lấy dữ liệu giá cổ phiếu và tính RSI
    
    Args:
        symbol (str): Mã cổ phiếu (VD: 'PC1', 'VCB', 'HPG')
        days (int): Số ngày lấy dữ liệu, mặc định 30 ngày
        rsi_period (int): Chu kỳ tính RSI, mặc định 14
    
    Returns:
        pd.DataFrame: DataFrame chứa dữ liệu giá và RSI với cột 'time'
    """
    # Tính ngày bắt đầu và kết thúc
    # Lấy thêm dữ liệu để tính RSI chính xác (cần ít nhất rsi_period + days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + rsi_period + 10)
    
    # Format ngày theo định dạng YYYY-MM-DD
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    logger.info(f"📊 Đang lấy dữ liệu cổ phiếu {symbol} từ {start_str} đến {end_str}...")
    
    # Khởi tạo Vnstock và lấy dữ liệu
    # Thử KBS trước, nếu lỗi thì dùng VCI
    try:
        stock = Vnstock().stock(symbol=symbol, source='KBS')
        df = stock.quote.history(start=start_str, end=end_str, interval='1D')
    except Exception as e:
        logger.warning(f"⚠️  KBS khong ho tro ma {symbol}, thu dung VCI...")
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        df = stock.quote.history(start=start_str, end=end_str, interval='1D')
    
    if df.empty:
        raise ValueError(f"Không thể lấy dữ liệu cho mã {symbol}")
    
    logger.info(f"✅ Đã lấy {len(df)} phiên giao dịch")
    
    # Tính RSI
    df['rsi'] = calculate_rsi_14(df, period=rsi_period)
    
    # Lấy chỉ số ngày gần đây nhất
    df = df.tail(days)
    
    # Đảm bảo có cột 'time' để dễ dàng vẽ biểu đồ
    if 'time' not in df.columns:
        # Nếu index là DatetimeIndex, chuyển thành cột 'time'
        if hasattr(df.index, 'strftime'):
            df['time'] = df.index.strftime('%Y-%m-%d')
        else:
            # Nếu không, tạo cột time từ index
            df['time'] = df.index.astype(str)
    
    # Reset index để tránh vấn đề với RangeIndex
    df = df.reset_index(drop=False)
    
    return df
    


# Test function
if __name__ == "__main__":
    # Test với mã FPT
    result = get_company_info("FPT")
    if result:
        logger.info("=== Thông tin cổ phiếu ===")
        logger.info(result)
