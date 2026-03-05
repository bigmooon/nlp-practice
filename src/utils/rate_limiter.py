from collections import deque
import time


class RateLimiter:
    """
    API 호출 횟수 제한
    """

    def __init__(self, calls_per_minute=30):
        self._limit = calls_per_minute
        self._timestamps = deque()

    def acquire(self):
        cutoff = time.time() - 60.0

        # 1분 이전 기록 제거
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        # 호출 가능 여부 확인
        if len(self._timestamps) >= self._limit:
            sleep_time = 60.0 - (time.time() - self._timestamps[0]) + 0.1

            if sleep_time > 0:
                print(f"[RateLimiter] RateLimit 대기: {sleep_time:.1f}초")
                time.sleep(sleep_time)

        self._timestamps.append(time.time())
