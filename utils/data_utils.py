from database.postgre import PostgreDatabase
from logger import default_logger as logger
from utils.vnstock_utils import get_company_info

db_conn = PostgreDatabase()


def format_currency_short(value):
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return f"{value:.0f}"


def get_report_by_symbol(symbol: str):
    report_sql = f"""
    SELECT * FROM (
    SELECT DISTINCT ON (source)
    id, symbol, source, report_date,
    round(gia_muc_tieu/1000.0,1) gia_muc_tieu, doanh_thu, loi_nhuan_sau_thue, link
    FROM report
    where symbol = '{symbol.upper()}'
    ORDER BY source, report_date DESC
    ) as t
    ORDER BY t.report_date DESC
    """

    reports = db_conn.raw_query(report_sql)
    return reports


get_report_by_symbol('FPT')


def get_main_stock_data(symbol: str):
    company_info = get_company_info(symbol)
    data = dict()
    data['name'] = company_info['name']
    data['industry'] = company_info['industry']
    data['avg_trading_volume'] = company_info['avg_trading_volume']
    price_rsi_sql = f"""
    select price::float/1000 price, rsi as rsi_14, change_percent from current_price cp  
    where cp.symbol = '{symbol.upper()}'
    """
    rsi_sql = f"""
    select rsi_14 from price_config
    where symbol = '{symbol.upper()}'
    """
    gia_von_sql = f"""
    select total, round(cost_price::float/1000,1) cost_price from portfolio where symbol = '{symbol.upper()}'  
    """
    # prefill data to avoid KeyError
    data['total'] = 0
    data['cost_price'] = 0.0
    price_config_sql = f"""
    select high, low, (high/(cp.price::float/1000)-1)*100 as gap, trend from price_config pc
    inner join current_price cp 
    on pc.symbol = cp.symbol
    where cp.symbol = '{symbol.upper()}'   
    """
    # prefill data to avoid KeyError
    data['high'] = 0.0
    data['low'] = 0.0
    data['gap'] = 0.0
    data['trend'] = 'N/A'
    queries = [price_rsi_sql,
               rsi_sql,
               price_config_sql,
               gia_von_sql]
    for query in queries:
        result = db_conn.raw_query(query)
        if result:
            data.update(result[0])
        # print(result)

    # Example output structure: {'price': 88100, 'rsi_14': 32.5, 'high': 120.0, 'low': 90.0, 'gap': 36.20885357548242, 'total': 5055, 'cost_price': 108560.8}
    return data


def get_doanh_thu_loi_nhuan_quy(symbol: str):
    doanh_thu_sql = f"""
    select 
    "doanh_thu_Q1" as "Q1",
    "doanh_thu_Q2" as "Q2",
    "doanh_thu_Q3" as "Q3",
    "doanh_thu_Q4" as "Q4",
    ("doanh_thu_Q1" + "doanh_thu_Q2" + "doanh_thu_Q3" + "doanh_thu_Q4") as "DOANH THU"
    from financial_statement where symbol = '{symbol.upper()}'
    """
    loi_nhuan_sql = f"""
    select 
    "lnst_Q1" as "Q1",
    "lnst_Q2" as "Q2",
    "lnst_Q3" as "Q3",
    "lnst_Q4" as "Q4",
    ("lnst_Q1" + "lnst_Q2" + "lnst_Q3" + "lnst_Q4") as "LNST"
    from financial_statement where symbol = '{symbol.upper()}'
    """
    queries = [doanh_thu_sql, loi_nhuan_sql]
    data = []
    for query in queries:
        result = db_conn.raw_query(query)
        if result:
            data.append(list(result[0].values()))
        else:
            data.append([0, 0, 0, 0, 0])
    return data


def parse_doanh_thu_loi_nhuan(data_str: str) -> list:
    result = []
    data = data_str.split('<br>')
    for item in data:
        if ": " in item:
            value = int(item.split(": ")[1])
            result.append(value)
    return result


def get_doanh_thu_loi_nhuan_nam(symbol: str):
    query_1 = f"""
    SELECT symbol, doanh_thu_nam, ln_sau_thue_nam FROM company where symbol = '{symbol.upper()}'
    """
    result = db_conn.raw_query(query_1)
    data = []
    doanh_thu_nam_str = result[0]['doanh_thu_nam']
    lnst_nam_str = result[0]['ln_sau_thue_nam']
    doanh_thu_nam = parse_doanh_thu_loi_nhuan(doanh_thu_nam_str)
    lnst_nam = parse_doanh_thu_loi_nhuan(lnst_nam_str)
    query_2 = f"""
    select 
    ("doanh_thu_Q1" + "doanh_thu_Q2" + "doanh_thu_Q3" + "doanh_thu_Q4") as "DOANH THU",
    ("lnst_Q1" + "lnst_Q2" + "lnst_Q3" + "lnst_Q4") as "LNST"
    from financial_statement where symbol = '{symbol.upper()}'
    """
    result = db_conn.raw_query(query_2)
    doanh_thu_nam.append(result[0]['DOANH THU'])
    lnst_nam.append(result[0]['LNST'])
    data.append(doanh_thu_nam)
    data.append(lnst_nam)
    return data


get_doanh_thu_loi_nhuan_nam("FPT")


def save_report(symbol, source, report_date, gia_muc_tieu, doanh_thu, loi_nhuan_sau_thue, link):
    insert_sql = f"""
    INSERT INTO report (symbol, source, report_date, gia_muc_tieu, doanh_thu, loi_nhuan_sau_thue, link)
    VALUES ('{symbol.upper()}', '{source}', '{report_date}', {gia_muc_tieu}, {doanh_thu}, {loi_nhuan_sau_thue}, '{link}');
    """
    db_conn.crud_query(insert_sql)
    logger.info(f"Report saved for {symbol} - {source} - {report_date}")


def delete_report(report_id):
    delete_sql = f"""
    DELETE FROM report WHERE id = {report_id};
    """
    db_conn.crud_query(delete_sql)
    logger.info(f"Report deleted with id: {report_id}")


def update_report(report_id, source, report_date, gia_muc_tieu, doanh_thu, loi_nhuan_sau_thue, link):
    update_sql = f"""
    UPDATE report
    SET source = '{source}', 
        report_date = '{report_date}', 
        gia_muc_tieu = {gia_muc_tieu}, 
        doanh_thu = {doanh_thu}, 
        loi_nhuan_sau_thue = {loi_nhuan_sau_thue}, 
        link = '{link}'
    WHERE id = {report_id};
    """
    logger.info(update_sql)
    db_conn.crud_query(update_sql)
    logger.info(f"Report updated with id: {report_id}")


def update_price_config(symbol, high, low, rsi, trend):
    update_sql = f"""
    UPDATE price_config
    SET high = {high}, low = {low}, rsi_14 = {rsi}, trend = '{trend}'
    WHERE symbol = '{symbol.upper()}';
    """
    db_conn.crud_query(update_sql)
    logger.info(f"Price config updated for {symbol} - high: {high}, low: {low}")


def convert_forigener_trading_data(foreigner_data_str: str):
    # Parse the string data
    if not foreigner_data_str:
        return []

    # Remove parentheses and split by comma
    cleaned_data = foreigner_data_str.replace(
        '(', '').replace(')', '').split(', ')

    parsed_data = []
    for item in cleaned_data:
        item = item.strip()
        if 'M' in item:
            value = float(item.replace('M', '')) * 1_000_000
        elif 'K' in item:
            value = float(item.replace('K', '')) * 1_000
        else:
            value = float(item)
        parsed_data.append(value)
    parsed_data.reverse()
    return parsed_data


def get_forigener_trading_trend(symbol: str):
    trading_sql = f"""
    select foreigner from price_config
    where symbol = '{symbol.upper()}'
    """
    result = db_conn.raw_query(trading_sql)
    if not result:
        return []
    foreigner_data_str = result[0].get('foreigner', "")

    # Parse the string data
    if not foreigner_data_str:
        return []

    return convert_forigener_trading_data(foreigner_data_str)


def get_company_estimations(symbol: str):
    estimation_sql = f"""
    select 
    v_point as dinh_gia,
    g_point as tang_truong,
    p_point as loi_nhuan,
    f_point as tai_chinh,
    d_point as co_tuc
    from company_estimation
    where symbol = '{symbol.upper()}'
    """
    result = db_conn.raw_query(estimation_sql)
    if result:
        return result[0]
    return {}

# get_forigener_trading_trend('FPT')
