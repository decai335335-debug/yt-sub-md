"""重试工具（当前主要由 tenacity 在 downloader 中直接处理）"""
from tenacity import retry, stop_after_attempt, wait_exponential
from config import RETRY_ATTEMPTS, RETRY_BACKOFF_MIN, RETRY_BACKOFF_MAX


def with_retry(fn):
    """通用重试装饰器"""
    return retry(
        stop=stop_after_attempt(RETRY_ATTEMPTS),
        wait=wait_exponential(min=RETRY_BACKOFF_MIN, max=RETRY_BACKOFF_MAX),
        reraise=True,
    )(fn)
