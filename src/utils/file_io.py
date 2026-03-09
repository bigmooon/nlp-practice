import json
from pathlib import Path


def save_jsonl(records, path, mode="w"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode, encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_jsonl(record, path):
    save_jsonl([record], path, mode="a")


def load_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []

    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def load_json(path):
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def load_existing_ids(path, id_field="full_name"):
    """중복 수집 방지용 jsonl id 로드"""
    return {r[id_field] for r in load_jsonl(path) if id_field in r}
