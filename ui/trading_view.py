import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts
from utils.api_utils import get_trading_view_data
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from logger import default_logger as logger

# Màu sắc
COLOR_BULL = 'rgba(38,166,154,0.9)'  # #26a69a
COLOR_BEAR = 'rgba(239,83,80,0.9)'   # #ef5350

# Thử import ta-lib (thư viện chuyên nghiệp cho phân tích kỹ thuật)
try:
    import talib
    HAS_TALIB = True
    logger.info("✅ Sử dụng TA-Lib để tính RSI (phương pháp chuyên nghiệp)")
except ImportError:
    HAS_TALIB = False
    logger.info(
        "⚠️  TA-Lib chưa được cài đặt, sử dụng phương pháp tính RSI chuẩn với pandas")
    logger.info("   Để cài đặt TA-Lib: pip install TA-Lib")


def calculate_rsi(data: pd.DataFrame, period: int = 14) -> list:
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
        return rsi.tolist()
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
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] *
                                (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] *
                                (period - 1) + loss.iloc[i]) / period

        # Tính RS và RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.tolist()


# Hàm tính RSI
def calculate_rsi_2(prices, period=14):
    """Tính RSI (Relative Strength Index)"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi


def display_trading_view(symbol):
    start = datetime.now() - timedelta(days=180)
    end = datetime.now()
    df = get_trading_view_data(symbol, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))

    # Tính RSI
    close_prices = df['close'].values
    # rsi_values = calculate_rsi_2(close_prices, period=14)
    rsi_values = calculate_rsi(df, period=14)
    df['rsi'] = rsi_values

    # Tạo màu cho nến và volume
    df['color'] = np.where(df['open'] > df['close'], COLOR_BEAR, COLOR_BULL)

    # lấy ra 60 ngày dữ liệu cuối cùng
    df = df.tail(60)

    # Chuyển đổi sang JSON
    candles = json.loads(df[['time', 'open', 'high', 'low', 'close']].to_json(orient="records"))
    # Volume với màu sắc dựa trên giá tăng/giảm
    volume_data = json.loads(df[['time', 'volume', 'color']].rename(columns={"volume": "value"}).to_json(orient="records"))
    rsi_data = json.loads(df[['time', 'rsi']].rename(columns={"rsi": "value"}).to_json(orient="records"))

    # Cấu hình biểu đồ
    chartMultipaneOptions = [
        # Biểu đồ giá + khối lượng (Candlestick + Histogram overlay)
        {
            # "width": 800,
            "height": 300,
            "rightPriceScale": {
                "scaleMargins": {
                    "top": 0.2,
                    "bottom": 0.25,
                },
                "borderVisible": False,
            },
            "overlayPriceScales": {
                "scaleMargins": {
                    "top": 0.8,
                    "bottom": 0,
                }
            },
            "layout": {
                "background": {
                    "type": "solid",
                    "color": '#1e222d'
                },
                "textColor": "#d1d4dc"
            },
            "grid": {
                "vertLines": {
                    "color": "rgba(42, 46, 57, 0.6)"
                },
                "horzLines": {
                    "color": "rgba(42, 46, 57, 0.6)"
                }
            },
            "crosshair": {
                "mode": 0
            },
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "timeVisible": True
            },
            "watermark": {
                "visible": True,
                "fontSize": 32,
                "horzAlign": 'center',
                "vertAlign": 'center',
                "color": 'rgba(171, 71, 188, 0.3)',
                "text": f'{symbol}',
            },
            "handleScroll": False,
            "handleScale": False,
        },
        # Biểu đồ RSI (Line)
        {
            # "width": 800,
            "height": 100,
            "layout": {
                "background": {
                    "type": "solid",
                    "color": '#1e222d'
                },
                "textColor": "#d1d4dc"
            },
            "grid": {
                "vertLines": {
                    "color": "rgba(42, 46, 57, 0.6)"
                },
                "horzLines": {
                    "color": "rgba(42, 46, 57, 0.6)"
                }
            },
            "timeScale": {
                "visible": False,
            },
            "rightPriceScale": {
                "scaleMargins": {
                    "top": 0.1,
                    "bottom": 0.1,
                }
            },
            "watermark": {
                "visible": True,
                "fontSize": 18,
                "horzAlign": 'left',
                "vertAlign": 'center',
                "color": 'rgba(171, 71, 188, 0.7)',
                "text": 'RSI (14)',
            },
            "handleScroll": False,
            "handleScale": False,
        },
        # Biểu đồ Khối Ngoại (Foreign Net Volume)
        {
            # "width": 800,
            "height": 100,
            "layout": {
                "background": {
                    "type": "solid",
                    "color": '#1e222d'
                },
                "textColor": "#d1d4dc"
            },
            "grid": {
                "vertLines": {
                    "color": "rgba(42, 46, 57, 0.6)"
                },
                "horzLines": {
                    "color": "rgba(42, 46, 57, 0.6)"
                }
            },
            "timeScale": {
                "visible": True,
                "borderColor": "rgba(197, 203, 206, 0.8)",
            },
            "rightPriceScale": {
                "scaleMargins": {
                    "top": 0.1,
                    "bottom": 0.1,
                }
            },
            "watermark": {
                "visible": True,
                "fontSize": 18,
                "horzAlign": 'left',
                "vertAlign": 'center',
                "color": 'rgba(171, 71, 188, 0.7)',
                "text": 'Khối Ngoại (Cộng Dồn)',
            },
            "handleScroll": False,
            "handleScale": False,
        }
    ]

    # Cấu hình series - Giá và khối lượng trong cùng 1 panel
    seriesPriceVolumeChart = [
        # Candlestick cho giá
        {
            "type": 'Candlestick',
            # "type": 'Area',
            "data": candles,
            "options": {
                "upColor": COLOR_BULL,
                "downColor": COLOR_BEAR,
                "borderVisible": False,
                "wickUpColor": COLOR_BULL,
                "wickDownColor": COLOR_BEAR
            }
        },
        # Histogram cho khối lượng (overlay)
        {
            "type": 'Histogram',
            "data": volume_data,
            "options": {
                "priceFormat": {
                    "type": 'volume',
                },
                "priceScaleId": ""
            },
            "priceScale": {
                "scaleMargins": {
                    "top": 0.85,
                    "bottom": 0,
                }
            }
        }
    ]

    seriesRSIChart = [
        # Đường RSI chính
        {
            "type": 'Line',
            "data": rsi_data,
            "options": {
                "color": '#2962FF',
                "lineWidth": 2
            }
        },
        # Đường RSI = 70 (Overbought)
        {
            "type": 'Line',
            "data": [{"time": item["time"], "value": 70} for item in rsi_data],
            "options": {
                "color": '#ff8e8e',
                "lineWidth": 1,
                "lineStyle": 2,  # Dashed line
                "crosshairMarkerVisible": False,
                "lastValueVisible": False,
                "priceLineVisible": False
            }
        },
        # Đường RSI = 30 (Oversold)
        {
            "type": 'Line',
            "data": [{"time": item["time"], "value": 30} for item in rsi_data],
            "options": {
                "color": '#73ffa6',  # Xanh nhạt
                "lineWidth": 1,
                "lineStyle": 2,  # Dashed line
                "crosshairMarkerVisible": False,
                "lastValueVisible": False,
                "priceLineVisible": False
            }
        }
    ]

    # Hiển thị biểu đồ
    renderLightweightCharts([
        {
            "chart": chartMultipaneOptions[0],
            "series": seriesPriceVolumeChart
        },
        {
            "chart": chartMultipaneOptions[1],
            "series": seriesRSIChart
        }
    ], 'stock_analysis')