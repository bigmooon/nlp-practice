from pathlib import Path

from tqdm import tqdm

from src.utils.file_io import append_jsonl, load_existing_ids, load_jsonl

RAW_DIR = Path("data/raw")
OUTPUT_PATH = RAW_DIR / "releases.jsonl"
REPO_PATH = RAW_DIR / "repositories.jsonl"

RELEASES_PER_REPO = 5  # 저장소당 최근 릴리스 수


def collect_releases(client, top_n=500, resume=True):
    """
    상위 N개 저장소의 릴리스 노트 수집
    """
    repos = load_jsonl(REPO_PATH)
    if not repos:
        print(
            "[ReleaseCollector] 저장소 목록이 없습니다. 먼저 repo_collector를 실행하세요."
        )
        return 0

    # star 내림차순 정렬
    repos_sorted = sorted(repos, key=lambda r: r.get("stars", 0), reverse=True)[:top_n]

    # 기존 수집된 저장소 스킵 (full_name 기준)
    collected = set()
    if resume and OUTPUT_PATH.exists():
        collected = load_existing_ids(OUTPUT_PATH, "full_name")

    cnt = 0

    for repo in tqdm(repos_sorted, desc="릴리스 수집"):
        full_name = repo.get("full_name", "")
        if not full_name or full_name in collected:
            continue

        items = client.get(
            f"/repos/{full_name}/releases",
            params={"per_page": RELEASES_PER_REPO},
        )
        if not items:
            continue

        for item in items:
            tag_name = item.get("tag_name", "")
            if not tag_name:
                continue

            append_jsonl(
                {
                    "full_name": full_name,
                    "tag_name": tag_name,
                    "name": item.get("name") or "",
                    "body": item.get("body") or "",
                    "published_at": item.get("published_at") or "",
                    "html_url": item.get("html_url") or "",
                },
                OUTPUT_PATH,
            )
            cnt += 1

        collected.add(full_name)

    print(f"[ReleaseCollector] 릴리스 {cnt}개 수집 완료")
    return cnt
