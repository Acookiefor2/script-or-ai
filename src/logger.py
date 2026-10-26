import json
from dataclasses import asdict
from pathlib import Path


def log_result(result, path: str = "runs/results.jsonl") -> None:
    """Append one GameResult as a JSON line."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(result)) + "\n")