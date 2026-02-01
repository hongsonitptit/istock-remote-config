import time
import functools
from logger import default_logger as logger

def retry(retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    Decorator để thực hiện retry khi có exception xảy ra với 1 method.
    
    Args:
        retries (int): Số lần thử lại tối đa. Mặc định là 3.
        delay (float): Thời gian chờ giữa các lần retry (giây). Mặc định là 1.0.
        exceptions (tuple): Các loại exception sẽ thực hiện retry. Mặc định là Exception.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < retries:
                        logger.warning(
                            f"⚠️ Lỗi khi thực hiện '{func.__name__}': {str(e)}. "
                            f"Đang thực hiện retry lần {attempt + 1}/{retries} sau {delay} giây..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"❌ Đã hết số lần retry cho '{func.__name__}' sau {retries} lần thử. "
                            f"Lỗi cuối cùng: {str(e)}"
                        )
                        raise last_exception
        return wrapper
    return decorator
