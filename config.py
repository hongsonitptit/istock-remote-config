import os
from dotenv import load_dotenv

# 1. Tải các biến môi trường từ tệp .env
# load_dotenv() sẽ tìm kiếm tệp .env trong thư mục hiện tại
# và tải các cặp key/value vào môi trường của hệ thống (os.environ).
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
