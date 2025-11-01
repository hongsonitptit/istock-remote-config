import csv
from datetime import datetime
from utils.data_utils import save_report

def insert_reports_from_csv(csv_file_path):
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                # report_id = int(row['id'])
                symbol = row['symbol']
                source = row['source']
                report_date_str = row['report_date']
                
                # Convert report_date string to datetime object
                report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()

                # Handle potential empty string for numeric fields
                gia_muc_tieu = float(row['gia_muc_tieu']) if row['gia_muc_tieu'] else 0
                doanh_thu = float(row['doanh_thu']) if row['doanh_thu'] else 0
                loi_nhuan_sau_thue = float(row['loi_nhuan_sau_thue']) if row['loi_nhuan_sau_thue'] else 0
                link = row['link']

                save_report(symbol, source, report_date, gia_muc_tieu, doanh_thu, loi_nhuan_sau_thue, link)
            except ValueError as e:
                print(f"Error processing row: {row}. Error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred for row: {row}. Error: {e}")

if __name__ == "__main__":
    csv_file = 'command/reports.csv'
    insert_reports_from_csv(csv_file)