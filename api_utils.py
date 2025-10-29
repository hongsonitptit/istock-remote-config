import requests
import json
from tcbs import get_token, tcbs_son
from datetime import datetime

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
        if exe_date.year < current_year -1:
            continue
        result.append({
            'Thời gian': exe_date_str,
            'Giá trị %': f"{round(value*100,2)}",
            'Loại': "Tiền mặt" if method == "cash" else "Cổ phiếu",
        })

    return result

# get_dividend_payment_histories("MSN", page=0, size=5)