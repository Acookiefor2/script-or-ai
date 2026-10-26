from collections import defaultdict


def score(results: list) -> dict:
    """Summarize games. Reports false positives/negatives separately so
    'always guess LLM' can't pass as skill."""
    out = {
        "games": len(results),
        "accuracy": 0.0,
        "false_positives": 0,   # script called an LLM
        "false_negatives": 0,   # LLM called a script
        "unsure": 0,
        "avg_rounds_to_detect": None,
        "by_opponent": {},
    }
    if not results:
        return out

    detect_rounds = []
    per = defaultdict(lambda: {"games": 0, "correct": 0})
    for r in results:
        per[r.opponent]["games"] += 1
        per[r.opponent]["correct"] += int(r.correct)
        if r.final_verdict == "unsure":
            out["unsure"] += 1
        elif r.final_verdict == "llm" and not r.is_llm:
            out["false_positives"] += 1
        elif r.final_verdict == "script" and r.is_llm:
            out["false_negatives"] += 1
        if r.rounds_to_detect is not None:
            detect_rounds.append(r.rounds_to_detect)

    out["accuracy"] = sum(r.correct for r in results) / len(results)
    if detect_rounds:
        out["avg_rounds_to_detect"] = sum(detect_rounds) / len(detect_rounds)
    out["by_opponent"] = {k: v["correct"] / v["games"] for k, v in per.items()}
    return out