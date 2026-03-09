from pathlib import Path

from tqdm import tqdm

from src.utils.file_io import append_jsonl, load_existing_ids, load_json

_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = _ROOT / "data/raw"
OUTPUT_PATH = RAW_DIR / "repositories.jsonl"
QUERIES_PATH = _ROOT / "config/search_queries.json"


def collect_repositories(client, resume=True):
    """
    미리 정의한 검색 쿼리로 GitHub 저장소 정보를 수집
    """
    config = load_json(QUERIES_PATH)
    queries = config.get("queries", [])

    collected = set()
    if resume and OUTPUT_PATH.exists():
        collected = load_existing_ids(OUTPUT_PATH, "full_name")

    results = []

    for query_cfg in tqdm(queries, desc="저장소 수집"):
        name = query_cfg["name"]
        q = query_cfg["q"]
        sort = query_cfg.get("sort", "stars")
        order = query_cfg.get("order", "desc")
        max_pages = query_cfg.get("max_pages", 5)

        for page_items in client.pagination(
            "/search/repositories",
            is_search=True,
            max_pages=max_pages,
            params={"q": q, "sort": sort, "order": order},
        ):
            for item in page_items:
                full_name = item.get("full_name", "")
                if not full_name or full_name in collected:
                    continue

                record = {
                    "full_name": full_name,
                    "description": item.get("description") or "",
                    "topics": item.get("topics", []),
                    "language": item.get("language") or "",
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "open_issues": item.get("open_issues_count", 0),
                    "license": (item.get("license") or {}).get("spdx_id", ""),
                    "created_at": item.get("created_at", ""),
                    "pushed_at": item.get("pushed_at", ""),
                    "html_url": item.get("html_url", ""),
                    "query_source": name,
                }
                append_jsonl(record, OUTPUT_PATH)
                collected.add(full_name)
                results.append(record)

    tqdm.write(f"[RepoCollector] 저장소 {len(results)}개 수집 완료")
    return results
