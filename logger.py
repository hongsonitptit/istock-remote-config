"""
Logger module với màu sắc và định dạng đầy đủ thông tin
"""
import logging
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter với màu sắc cho các log level khác nhau"""
    
    # Mã màu ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    
    # Màu cho các thành phần khác
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    TIMESTAMP_COLOR = '\033[90m'  # Gray
    NAME_COLOR = '\033[94m'       # Light Blue
    LOCATION_COLOR = '\033[90m'   # Gray
    
    def format(self, record):
        # Lấy màu cho log level
        level_color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Format log level với padding
        level_name = f"{record.levelname:8}"
        
        # Format location (file:line)
        location = f"{record.filename}:{record.lineno}"
        
        # Format function name
        func_name = record.funcName
        
        # Tạo message với màu sắc
        colored_message = (
            f"[{level_color}{self.BOLD}{level_name}{self.RESET}] "
            f"{self.TIMESTAMP_COLOR}{timestamp}{self.RESET} "
            # f"{self.NAME_COLOR}[{record.name}]{self.RESET} "
            # f"{self.LOCATION_COLOR}({location}:{func_name}){self.RESET} "
            f"{location}{self.RESET} "
            f": {record.getMessage()}"
        )
        
        # Thêm exception info nếu có
        if record.exc_info:
            colored_message += f"\n{self.formatException(record.exc_info)}"
        
        return colored_message


class Logger:
    """Wrapper class cho logger với cấu hình sẵn"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None, level: int = logging.DEBUG) -> logging.Logger:
        """
        Lấy hoặc tạo logger với tên được chỉ định
        
        Args:
            name: Tên của logger (mặc định là __name__ của module gọi)
            level: Log level (mặc định là DEBUG)
            
        Returns:
            logging.Logger: Logger instance
        """
        if name is None:
            name = __name__
        
        # Kiểm tra xem logger đã tồn tại chưa
        if name in cls._loggers:
            return cls._loggers[name]
        
        # Tạo logger mới
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Xóa các handler cũ nếu có
        logger.handlers.clear()
        
        # Tạo console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Áp dụng colored formatter
        formatter = ColoredFormatter()
        console_handler.setFormatter(formatter)
        
        # Thêm handler vào logger
        logger.addHandler(console_handler)
        
        # Tránh propagate để không bị duplicate log
        logger.propagate = False
        
        # Lưu logger vào cache
        cls._loggers[name] = logger
        
        return logger


# Tạo logger mặc định cho module này
default_logger = Logger.get_logger(__name__)


# Các hàm tiện ích để sử dụng trực tiếp
def debug(msg, *args, **kwargs):
    """Log debug message"""
    default_logger.debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Log info message"""
    default_logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Log warning message"""
    default_logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """Log error message"""
    default_logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """Log critical message"""
    default_logger.critical(msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    """Log exception với stack trace"""
    default_logger.exception(msg, *args, **kwargs)


# Demo usage
if __name__ == "__main__":
    # Tạo logger với tên custom
    logger = Logger.get_logger("TestLogger")
    
    # Test các log level
    logger.debug("Đây là debug message - thông tin chi tiết cho developer")
    logger.info("Đây là info message - thông tin chung về hoạt động")
    logger.warning("Đây là warning message - cảnh báo cần chú ý")
    logger.error("Đây là error message - lỗi đã xảy ra")
    logger.critical("Đây là critical message - lỗi nghiêm trọng!")
    
    # Test exception logging
    try:
        result = 1 / 0
    except Exception as e:
        logger.exception("Lỗi khi thực hiện phép chia")
    
    # Test với logger khác
    another_logger = Logger.get_logger("AnotherModule")
    another_logger.info("Logger từ module khác")
    
    # Test các hàm tiện ích
    info("Sử dụng hàm info() trực tiếp")
    warning("Sử dụng hàm warning() trực tiếp")
