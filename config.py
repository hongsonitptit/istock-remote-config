import os
from dotenv import load_dotenv

# 1. Tải các biến môi trường từ tệp .env
# load_dotenv() sẽ tìm kiếm tệp .env trong thư mục hiện tại
# và tải các cặp key/value vào môi trường của hệ thống (os.environ).
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

TCBS_NAME = os.getenv("TCBS_NAME", "default_account")
TCBS_USER = os.getenv("TCBS_USER", "default_user")
TCBS_PASSWORD = os.getenv("TCBS_PASSWORD", "default_password")

NEON_HOST = os.getenv("NEON_HOST", "default_neon_host")
NEON_DATABASE = os.getenv("NEON_DATABASE", "default_neon_db")
NEON_USER = os.getenv("NEON_USER", "default_neon_user")
NEON_PASSWORD = os.getenv("NEON_PASSWORD", "default_neon_password")

NHOST_HOST = os.getenv("NHOST_HOST", "default_nhost_host")
NHOST_DATABASE = os.getenv("NHOST_DATABASE", "default_nhost_db")
NHOST_USER = os.getenv("NHOST_USER", "default_nhost_user")
NHOST_PASSWORD = os.getenv("NHOST_PASSWORD", "default_nhost_password")

COCK_HOST = os.getenv("COCK_HOST", "default_cock_host")
COCK_DATABASE = os.getenv("COCK_DATABASE", "default_cock_db")
COCK_USER = os.getenv("COCK_USER", "default_cock_user")
COCK_PASSWORD = os.getenv("COCK_PASSWORD", "default_cock_password")

USE_VNSTOCK = os.getenv("USE_VNSTOCK", False)
