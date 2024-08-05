import time
from collections import deque

LOGLINES_LIMIT = 1000
LOG_LINES = deque([], LOGLINES_LIMIT)
LOGGER_LAST_FETCH = {}

def log(log_line: str) -> None:
    print(log_line)
    LOG_LINES.append((time.monotonic(), log_line))

def get_unsent_loglines(logger_key: str, count: int = None) -> list:
    # Initialize last fetch time if logger_key is accessed for the first time
    if logger_key not in LOGGER_LAST_FETCH:
        LOGGER_LAST_FETCH[logger_key] = 0.0

    last_fetch_time = LOGGER_LAST_FETCH[logger_key]
    unsent_logs = []

    # Collect unsent logs since the last fetch time
    for timestamp, log_line in LOG_LINES:
        if timestamp > last_fetch_time:
            unsent_logs.append(log_line)
        # Stop collecting if the count limit is reached
        if count is not None and len(unsent_logs) >= count:
            break
    
    # Update the last fetch time to the current time
    LOGGER_LAST_FETCH[logger_key] = time.monotonic()
    return unsent_logs