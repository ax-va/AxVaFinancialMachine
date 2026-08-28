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


def rate_limit(min_interval_sec: float | int):
    def decorator(func):
        last_call_time = 0.0

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call_time

            elapsed = time.monotonic() - last_call_time
            delay = min_interval_sec - elapsed

            if delay > 0:
                time.sleep(delay)

            last_call_time = time.monotonic()

            return func(*args, **kwargs)

        return wrapper

    return decorator
