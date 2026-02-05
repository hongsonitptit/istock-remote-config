import requests
import json
from tcbs import get_token, tcbs_son
from datetime import datetime, timedelta
from logger import default_logger as logger
from statistics import median
import pandas as pd
from typing import Tuple
from vnstock import Vnstock
import streamlit as st

FIREANT_JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkdYdExONzViZlZQakdvNERWdjV4QkRITHpnSSIsImtpZCI6IkdYdExONzViZlZQakdvNERWdjV4QkRITHpnSSJ9.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmZpcmVhbnQudm4iLCJhdWQiOiJodHRwczovL2FjY291bnRzLmZpcmVhbnQudm4vcmVzb3VyY2VzIiwiZXhwIjoxODg5NjIyNTMwLCJuYmYiOjE1ODk2MjI1MzAsImNsaWVudF9pZCI6ImZpcmVhbnQudHJhZGVzdGF0aW9uIiwic2NvcGUiOlsiYWNhZGVteS1yZWFkIiwiYWNhZGVteS13cml0ZSIsImFjY291bnRzLXJlYWQiLCJhY2NvdW50cy13cml0ZSIsImJsb2ctcmVhZCIsImNvbXBhbmllcy1yZWFkIiwiZmluYW5jZS1yZWFkIiwiaW5kaXZpZHVhbHMtcmVhZCIsImludmVzdG9wZWRpYS1yZWFkIiwib3JkZXJzLXJlYWQiLCJvcmRlcnMtd3JpdGUiLCJwb3N0cy1yZWFkIiwicG9zdHMtd3JpdGUiLCJzZWFyY2giLCJzeW1ib2xzLXJlYWQiLCJ1c2VyLWRhdGEtcmVhZCIsInVzZXItZGF0YS13cml0ZSIsInVzZXJzLXJlYWQiXSwianRpIjoiMjYxYTZhYWQ2MTQ5Njk1ZmJiYzcwODM5MjM0Njc1NWQifQ.dA5-HVzWv-BRfEiAd24uNBiBxASO-PAyWeWESovZm_hj4aXMAZA1-bWNZeXt88dqogo18AwpDQ-h6gefLPdZSFrG5umC1dVWaeYvUnGm62g4XS29fj6p01dhKNNqrsu5KrhnhdnKYVv9VdmbmqDfWR8wDgglk5cJFqalzq6dJWJInFQEPmUs9BW_Zs8tQDn-i5r4tYq2U8vCdqptXoM7YgPllXaPVDeccC9QNu2Xlp9WUvoROzoQXg25lFub1IYkTrM66gJ6t9fJRZToewCt495WNEOQFa_rwLCZ1QwzvL0iYkONHS_jZ0BOhBCdW9dWSawD6iF1SIQaFROvMDH1rg"



@st.cache_data(ttl=60)
def get_finance_history(symbol: str) -> pd.DataFrame:
    url = f"https://apiextaws.tcbs.com.vn/tcanalysis/v1/finance/{symbol.upper()}/financialratio?yearly=0&isAll=true"

    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0',
        'Accept': 'application/json',
        'Accept-Language': 'vi',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://tcinvest.tcbs.com.vn/',
        'Content-Type': 'application/json',
        'Origin': 'https://tcinvest.tcbs.com.vn',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Authorization': f'Bearer {get_token(tcbs_son)}',
        'Connection': 'keep-alive'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    result = pd.DataFrame(data)
    return result

# logger.info(get_finance_history('FPT')['bookValuePerShare'])



@st.cache_data(ttl=60)
def get_list_similar_company(symbol: str) -> list:
    url = f"https://api2.simplize.vn/api/personalize/compare/list/{symbol}"

    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Origin': 'https://simplize.vn',
        'Connection': 'keep-alive',
        'Referer': 'https://simplize.vn/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'TE': 'trailers'
    }

    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        data = json.loads(response.text)
        return data['data']['pickTickers']
    except Exception as e:
        logger.exception(f"Error getting list similar company: {e}")
        return []



@st.cache_data(ttl=60)
def get_avg_pe_pb_industry(symbol: str) -> dict:
    url = "https://api2.simplize.vn/api/company/view/fi-data"

    list_similar_company = get_list_similar_company(symbol)
    list_similar_company.append(symbol)

    payload = json.dumps({
        "tickers": list_similar_company
    })
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Content-Type': 'application/json',
        'Origin': 'https://simplize.vn',
        'Connection': 'keep-alive',
        'Referer': 'https://simplize.vn/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'TE': 'trailers',
        # 'Cookie': 'JSESSIONID=WfHPxjN9hEhBOmH0fcDitvXnpq7bXQ0NcOViVQrK'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    data = json.loads(response.text)

    avg_pe = median([item['peRatio'] for item in data['data']])
    avg_pb = median([item['pbRatio'] for item in data['data']])
    return {
        'avg_pe': avg_pe,
        'avg_pb': avg_pb
    }



@st.cache_data(ttl=60)
def get_dividend_payment_histories(symbol: str) -> list:
    try:
        url = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/events"
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://trading.vietcap.com.vn/',
            'Origin': 'https://trading.vietcap.com.vn',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }
        current_year = datetime.now().year
        params = {
            'ticker': symbol,
            'fromDate': f'{current_year-2}0101',
            'toDate': f'{current_year}1231',
            'eventCode': 'DIV,ISS',
            'page': '0',
            'size': '50'
        }

        response = requests.get(url, headers=headers, params=params)
        # response.raise_for_status()
        data = json.loads(response.text)
        data = data['data']['content']
        result = []
        for item in data:
            exe_date = item['displayDate1'].split("T")[0]
            value = item['exerciseRatio']
            method = ' - '.join(item['eventTitleVi'].split(" - ")[1:])
            result.append({
                'Thời gian': exe_date,
                'Giá trị %': f"{round(value*100,2)}",
                'Loại': method,
            })
        return result
    except Exception as e:
        logger.exception(f"Error getting dividend payment histories: {e}")
        return []



@st.cache_data(ttl=60)
def get_trading_view_data(symbol: str, start: str, end: str) -> pd.DataFrame:
    try:
        url = f"https://trade.pinetree.vn/stockHis.pt?symbol={symbol}&from={start}&to={end}&page=1&pageSize=1000"

        payload = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://trade.pinetree.vn/',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=4',
            'Cookie': 'route=797533ac5607ed1f4076438965e16adf'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        result = []
        data = json.loads(response.text)
        for item in data:
            date = item['TradingDate']
            time = date.split("T")[0]
            open = round(item['OpenPrice']/1000, 2)
            high = round(item['HighestPrice']/1000, 2)
            low = round(item['LowestPrice']/1000, 2)
            close = round(item['ClosePrice']/1000, 2)
            volume = item['TotalVol']
            result.append({
                'date': date,
                'open': open,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'time': time,
            })
        result = pd.DataFrame(result)
        result = result.sort_values(
            by='date', ascending=True, ignore_index=True)
        return result
    except Exception as e:
        logger.exception(f"Error getting volume history: {e}")
        return pd.DataFrame()


# get_trading_view_data("PC1", "2024-01-01", "2024-12-31")



@st.cache_data(ttl=60)
def get_company_info(symbol: str) -> dict:
    try:
        url = f"https://trade.pinetree.vn/companyInfo.pt?symbol={symbol.upper()}"

        payload = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://trade.pinetree.vn/',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=4',
            'Cookie': 'route=797533ac5607ed1f4076438965e16adf'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        data = json.loads(response.text)

        company_name = data['FullName']
        website = data['URL']
        exchange = data['Exchange']
        if data['IndustryName'] in data['SubIndustryName']:
            industry = ', '.join([data['SubIndustryName'], data['SectorName']])
        else:
            industry = ', '.join(
                [data['IndustryName'], data['SubIndustryName']])

        return {
            'name': company_name,
            'industry': industry,
            'website': website,
            'exchange': exchange,
        }
    except Exception as e:
        logger.exception(f"Lỗi khi lấy thông tin cổ phiếu cho {symbol}: {e}")
        return {
            'name': "",
            'industry': "",
            'website': "",
            'exchange': "",
        }



@st.cache_data(ttl=60)
def get_stock_data_and_rsi(symbol: str, days: int = 30, rsi_period: int = 14):
    """
    Lấy dữ liệu giá cổ phiếu và tính RSI
    
    Args:
        symbol (str): Mã cổ phiếu (VD: 'PC1', 'VCB', 'HPG')
        days (int): Số ngày lấy dữ liệu, mặc định 30 ngày
        rsi_period (int): Chu kỳ tính RSI, mặc định 14
    
    Returns:
        pd.DataFrame: DataFrame chứa dữ liệu giá và RSI
    """
    # Tính ngày bắt đầu và kết thúc
    # Lấy thêm dữ liệu để tính RSI chính xác (cần ít nhất rsi_period + days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    # Format ngày theo định dạng YYYY-MM-DD
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    logger.info(
        f"📊 Đang lấy dữ liệu cổ phiếu {symbol} từ {start_str} đến {end_str}...")

    # Khởi tạo Vnstock và lấy dữ liệu
    # Thử TCBS trước, nếu lỗi thì dùng VCI
    try:
        stock = Vnstock().stock(symbol=symbol, source='TCBS')
        df = stock.quote.history(start=start_str, end=end_str, interval='1D')
    except Exception as e:
        logger.warning(f"⚠️  TCBS khong ho tro ma {symbol}, thu dung VCI...")
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        df = stock.quote.history(start=start_str, end=end_str, interval='1D')

    if df.empty:
        logger.error(f"Không thể lấy dữ liệu cho mã {symbol}")
        return None

    logger.info(f"✅ Đã lấy {len(df)} phiên giao dịch")

    # Tính RSI
    # df['rsi'] = calculate_rsi(df, period=rsi_period)

    # Lấy chỉ số ngày gần đây nhất
    df = df.tail(days)

    return df

# print(get_stock_data_and_rsi('FPT'))



@st.cache_data(ttl=60)
def get_foreigner_room(symbol: str, start_date: str, end_date: str) -> list:
    limit = 1000
    offset = 0

    payload = {}
    headers = {
        'Authorization': f'Bearer {FIREANT_JWT_TOKEN}'
    }

    data = []

    while True:
        url = f"https://restv2.fireant.vn/symbols/{symbol}/historical-quotes?startDate={start_date}&endDate={end_date}&offset={offset}&limit={limit}"
        logger.info(f"Get data from {url}")
        response = requests.request(
            "GET", url, headers=headers, data=payload, verify=False)
        records = json.loads(response.text)

        if len(records) == 0:
            break

        data.extend(records)
        offset += limit

    data.reverse()

    foreign_room = []

    for item in data:
        foreign_room.append(item['currentForeignRoom'])

    return foreign_room

# get_foreigner_room('FPT', '2025-12-01', '2025-12-25')


@st.cache_data(ttl=60)
def get_last_doanh_thu_loi_nhuan_quy(symbol: str) -> list:
    url = f"https://apiextaws.tcbs.com.vn/tcanalysis/v1/finance/{symbol}/incomestatement?yearly=0&isAll=true"

    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
        'Accept': 'application/json',
        'Accept-Language': 'vi',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://tcinvest.tcbs.com.vn/',
        'Content-Type': 'application/json',
        'traceparent': '00-190d322f262d65d8af5a423f5a27d21a-5ff8cc3633d64852-01',
        'tracestate': 'es=s:1',
        'Origin': 'https://tcinvest.tcbs.com.vn',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Authorization': f'Bearer {get_token(tcbs_son)}',
        'Connection': 'keep-alive'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    data = json.loads(response.text)

    current_year = datetime.now().year
    last_year = current_year - 1

    doanh_thu_quy = []
    lnst_quy = []
    init_doanh_thu_quy = {
        f'{last_year}-4': 0,
        f'{current_year}-1': 0,
        f'{current_year}-2': 0,
        f'{current_year}-3': 0,
        f'{current_year}-4': 0,
    }
    init_lnst_quy = {
        f'{last_year}-4': 0,
        f'{current_year}-1': 0,
        f'{current_year}-2': 0,
        f'{current_year}-3': 0,
        f'{current_year}-4': 0,
    }

    for item in data:
        current_key = f'{item["year"]}-{item["quarter"]}'
        last_key = f'{item["year"]}-{item["quarter"]}'
        if current_key in init_doanh_thu_quy:
            init_doanh_thu_quy[current_key] = item['revenue']
        if current_key in init_lnst_quy:
            init_lnst_quy[current_key] = item['postTaxProfit']
        if last_key in init_doanh_thu_quy:
            init_doanh_thu_quy[last_key] = item['revenue']
        if last_key in init_lnst_quy:
            init_lnst_quy[last_key] = item['postTaxProfit']
    
    doanh_thu_quy = []
    lnst_quy = []
    for key, value in init_doanh_thu_quy.items():
        doanh_thu_quy.append(value)
    for key, value in init_lnst_quy.items():
        lnst_quy.append(value)
    doanh_thu_quy.append(sum(doanh_thu_quy[1:]))
    lnst_quy.append(sum(lnst_quy[1:]))
    return doanh_thu_quy, lnst_quy
    


@st.cache_data(ttl=60)
def get_doanh_thu_loi_nhuan_quy(symbol: str, year: int) -> list:
    url = f"https://apiextaws.tcbs.com.vn/tcanalysis/v1/finance/{symbol}/incomestatement?yearly=0&isAll=true"

    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
        'Accept': 'application/json',
        'Accept-Language': 'vi',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://tcinvest.tcbs.com.vn/',
        'Content-Type': 'application/json',
        'traceparent': '00-190d322f262d65d8af5a423f5a27d21a-5ff8cc3633d64852-01',
        'tracestate': 'es=s:1',
        'Origin': 'https://tcinvest.tcbs.com.vn',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Authorization': f'Bearer {get_token(tcbs_son)}',
        'Connection': 'keep-alive'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    data = json.loads(response.text)

    current_year = datetime.now().year

    doanh_thu_quy = []
    lnst_quy = []
    for item in data:
        if item['year'] == year:
            doanh_thu_quy.append(item['revenue'])
            lnst_quy.append(item['postTaxProfit'])

    return doanh_thu_quy, lnst_quy



@st.cache_data(ttl=60)
def get_doanh_thu_loi_nhuan_nam(symbol: str) -> list:
    url = f"https://apiextaws.tcbs.com.vn/tcanalysis/v1/finance/{symbol}/incomestatement?yearly=1&isAll=true"

    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
        'Accept': 'application/json',
        'Accept-Language': 'vi',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://tcinvest.tcbs.com.vn/',
        'Content-Type': 'application/json',
        'traceparent': '00-190d322f262d65d8af5a423f5a27d21a-5ff8cc3633d64852-01',
        'tracestate': 'es=s:1',
        'Origin': 'https://tcinvest.tcbs.com.vn',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Authorization': f'Bearer {get_token(tcbs_son)}',
        'Connection': 'keep-alive'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    data = json.loads(response.text)

    df = pd.DataFrame(data)

    current_year = datetime.now().year

    # tạo df2 chứa các năm từ current_year - 5 đến current_year
    df2 = pd.DataFrame({
        'year': range(current_year - 5, current_year + 1)
    })

    df = pd.merge(df2, df, on='year', how='left')

    # chỉ giữ lại các cột year, revenue, postTaxProfit
    df = df[['year', 'revenue', 'postTaxProfit']]

    for index, row in df.iterrows():
        if pd.isna(row['revenue']):
            doanh_thu_list, loi_nhuan_list = get_doanh_thu_loi_nhuan_quy(symbol, row['year'])
            df.at[index, 'revenue'] = sum(doanh_thu_list)
            df.at[index, 'postTaxProfit'] = sum(loi_nhuan_list)

    # print(df)
    result = []
    result.append(df['revenue'].tolist())
    result.append(df['postTaxProfit'].tolist())

    return result


# get_doanh_thu_loi_nhuan_nam('VCG')
