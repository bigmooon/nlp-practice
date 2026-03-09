from pathlib import Path

from tqdm import tqdm

from src.utils.file_io import append_jsonl, load_existing_ids, load_jsonl

_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = _ROOT / "data/raw"
README_DIR = RAW_DIR / "readmes"
INDEX_PATH = README_DIR / "index.jsonl"
REPO_PATH = RAW_DIR / "repositories.jsonl"

MAX_README_BYTES = 200_000  # 200KB 초과 시 스킵


def collect_readmes(client, top_n=1000, resume=True):
    """
    상위 N개 저장소(star 기준) README 수집
    """
    README_DIR.mkdir(parents=True, exist_ok=True)

    repos = load_jsonl(REPO_PATH)
    if not repos:
        print(
            "[ReadmeCollector] 저장소 목록이 없습니다. 먼저 repo_collector를 실행하세요."
        )
        return 0

    # star 내림차순 정렬
    repos_sorted = sorted(repos, key=lambda r: r.get("stars", 0), reverse=True)[:top_n]

    # 기존 수집 건 스킵
    collected = set()
    if resume and INDEX_PATH.exists():
        collected = load_existing_ids(INDEX_PATH, "full_name")

    cnt = 0

    for repo in tqdm(repos_sorted, desc="README 수집"):
        full_name = repo.get("full_name", "")
        if not full_name or full_name in collected:
            continue

        content = client.get(f"/repos/{full_name}/readme", raw=True)
        if content is None:
            continue

        if len(content.encode("utf-8")) > MAX_README_BYTES:
            continue

        # 파일명: owner_repo.md
        # "/" -> "_"
        file_name = full_name.replace("/", "_") + ".md"
        file_path = README_DIR / file_name
        file_path.write_text(content, encoding="utf-8")

        append_jsonl(
            {
                "full_name": full_name,
                "file": file_name,
                "stars": repo.get("stars", 0),
                "language": repo.get("language", ""),
                "topics": repo.get("topics", []),
            },
            INDEX_PATH,
        )
        collected.add(full_name)
        cnt += 1

    print(f"[ReadmeCollector] README {cnt}개 수집 완료")
    return cnt
