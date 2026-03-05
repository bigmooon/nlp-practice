"""
Github REST API 클라이언트
"""

import os
import time

import requests

from src.utils.rate_limiter import RateLimiter

GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"

MAX_RETRIES = 5
DEFAULT_TIMEOUT = 30


class GitHubClient:
    def __init__(self, token=None, *, search_rate_limit=25, general_rate_limit=80):
        self._token = token or os.getenv("GITHUB_TOKEN")
        self._session = requests.Session()
        self._session.headers.update(self._default_headers())
        self._search_limiter = RateLimiter(search_rate_limit)
        self._general_limiter = RateLimiter(general_rate_limit)

    def get(self, path, *, is_search=False, raw=False, **kwargs):
        """
        return JSON or raw text responses
        return None if 404
        """
        if raw:
            kwargs["extra_headers"] = {"Accept": "application/vnd.github.raw+json"}
        res = self._request("GET", self._url(path), is_search=is_search, **kwargs)
        if res.status_code == 404:
            return None
        res.raise_for_status()
        return res.text if raw else res.json()

    def pagination(
        self, path, *, is_search=False, max_pages=10, per_page=100, **kwargs
    ):
        params = kwargs.pop("params", {})
        params.setdefault("per_page", per_page)
        url = self._url(path)

        for _ in range(max_pages):
            if not url:
                break

            res = self._request(
                "GET", url, is_search=is_search, params=params, **kwargs
            )
            if res.status_code == 404:
                break
            res.raise_for_status()

            data = res.json()
            items = data.get("items") if isinstance(data, dict) else data
            if not items:
                break

            yield items

            url = res.links.get("next", {}).get("url")
            params = {}

    def rate_limit_status(self):
        return self.get("/rate_limit")

    # ============================
    # internal methods
    # ============================
    def _request(self, method, url, *, is_search=False, extra_headers=None, **kwargs):
        """
        공통 API 요청 메서드
        - is_search: 검색 API는 별도의 레이트 리미터 사용
        - extra_headers: 추가 헤더 (예: Accept)
        """
        limiter = self._search_limiter if is_search else self._general_limiter
        limiter.acquire()

        if extra_headers:
            kwargs.setdefault("headers", {}).update(extra_headers)

        last_res = None
        for attempt in range(MAX_RETRIES):
            last_res = self._session.request(
                method, url, timeout=DEFAULT_TIMEOUT, **kwargs
            )

            # rate limit 초과 시 대기 후 재시도
            if self._handle_rate_limit(last_res):
                continue

            # 서버 오류 시 exponential backoff으로 재시도
            if last_res.status_code >= 500:
                wait = 2**attempt
                print(
                    f"[GithubClient] 서버 오류 {last_res.status_code}, {wait}s 후 재시도 (attempt {attempt + 1}/{MAX_RETRIES})"
                )
                time.sleep(wait)
                continue

            # 정상 응답 or 클라이언트 오류(4xx)인 경우 반복 종료
            return last_res

        last_res.raise_for_status()
        return last_res

    def _handle_rate_limit(self, res):
        """
        rate limit 초과 판별
        - True: 대기
        """
        # 403: 시간 당 할당량 초과
        is_exceed = (
            res.status_code == 403 and res.headers.get("X-RateLimit-Remaining") == "0"
        )
        # 429: Too Many Requests
        is_too_many = res.status_code == 429

        if not (is_exceed or is_too_many):
            return False

        # 대기 시간 계산
        retry_after = res.headers.get("Retry-After")
        if retry_after:
            wait_time = int(retry_after) + 1

        else:
            reset_at = int(
                res.headers.get("X-RateLimit-Reset", str(int(time.time()) + 60))
            )
            wait_time = max(reset_at - time.time(), 1) + 2

        print(f"[GithubClient] RateLimit 초과, {wait_time:.1f}s 후 재시도")
        time.sleep(wait_time)
        return True

    def _default_headers(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    @staticmethod
    def _url(path):
        """
        API 엔드포인트 URL 생성
        """
        return GITHUB_API_BASE + path
