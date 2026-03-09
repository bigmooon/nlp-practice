from pathlib import Path

from tqdm import tqdm

from src.utils.file_io import append_jsonl, load_json

_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = _ROOT / "data/raw"
OUTPUT_PATH = RAW_DIR / "topics.jsonl"
QUERIES_PATH = _ROOT / "config/search_queries.json"


def collect_topics(client, resume=True):
    """
    미리 정의한 키워드로 github 토픽 정보를 수집
    """
    config = load_json(QUERIES_PATH)
    keywords = config.get("topic_keywords", [])

    collected = set()
    cnt = 0

    # API 호출
    for keyword in tqdm(keywords, desc="토픽 수집"):
        res = client.get(
            "/search/topics",
            is_search=True,
            params={"q": keyword, "per_page": 10},
            headers={"Accept": "application/vnd.github.mercy-preview+json"},
        )
        items = res.get("items", []) if res else []

        for item in items:
            name = item.get("name", "")
            if not name or name in collected:
                continue

            append_jsonl(
                {
                    "name": name,
                    "short_description": item.get("short_description") or "",
                    "description": item.get("description") or "",
                    "created_by": item.get("created_by") or "",
                    "released": item.get("released") or "",
                    "featured": item.get("featured", False),
                    "curated": item.get("curated", False),
                    "query_keyword": keyword,
                },
                OUTPUT_PATH,
            )
            collected.add(name)
            cnt += 1

        print(f"[TopicCollector] 토픽 {cnt}개 수집 완료")
        return cnt
