import functools
import logging
import time

logger = logging.getLogger(__name__)


def retry(
    max_retries: int,
    min_retry_delay_sec: float | int,
    exceptions: type[Exception] | tuple[type[Exception], ...],
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for retry_number in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions:
                    delay = min_retry_delay_sec * retry_number

                    logger.warning(
                        f"Retrying in {delay} seconds. "
                        f"Retry: {retry_number}/{max_retries}"
                    )

                    time.sleep(delay)

            return func(*args, **kwargs)

        return wrapper

    return decorator
