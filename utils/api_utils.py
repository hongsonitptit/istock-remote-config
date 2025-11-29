import requests
import json
from tcbs import get_token, tcbs_son
from datetime import datetime
from logger import default_logger as logger
from statistics import median


def get_dividend_payment_histories(symbol, page=0, size=20):
    url = f"https://apiextaws.tcbs.com.vn/tcanalysis/v1/company/{symbol.upper()}/dividend-payment-histories?page={page}&size={size}"

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
    current_year = datetime.now().year

    result = []
    for item in data['listDividendPaymentHis']:
        exe_date = item['exerciseDate']
        value = item['cashDividendPercentage']
        method = item['issueMethod']
        exe_date = datetime.strptime(exe_date, "%d/%m/%y")
        exe_date_str = exe_date.strftime("%Y-%m-%d")
        if exe_date.year < current_year - 1:
            continue
        result.append({
            'Thời gian': exe_date_str,
            'Giá trị %': f"{round(value*100,2)}",
            'Loại': "Tiền mặt" if method == "cash" else "Cổ phiếu",
        })

    return result

# get_dividend_payment_histories("MSN", page=0, size=5)


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

# logger.info(get_list_similar_company("MSN"))
# logger.info(get_avg_pe_pb_industry("MSN"))
