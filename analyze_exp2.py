"""Did the interrogator even test the tells in exp2?

Usage: python analyze_exp2.py [path]   (default: runs/exp2.jsonl)
Offline: reads the log only, makes no API calls.
"""
import json
import statistics as st
import sys
from collections import defaultdict

from src.analysis import count_repeats, looks_like_injection

sys.stdout.reconfigure(encoding="utf-8")  # model text can contain non-ASCII

PATH = sys.argv[1] if len(sys.argv) > 1 else "runs/exp2.jsonl"


def mean(xs):
    return st.mean(xs) if xs else float("nan")


def pct(k, n):
    return f"{k}/{n} ({k / n:.0%})" if n else "0/0"


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def analyze_game(g):
    rounds = g["rounds"]
    questions = [r["question"] for r in rounds]

    seen = {}
    repeat_pairs = 0
    repeat_differs = 0
    for r in rounds:
        key = r["question"].strip()
        if key in seen:
            repeat_pairs += 1
            if seen[key] != r["answer"]:
                repeat_differs += 1
        else:
            seen[key] = r["answer"]

    injections = [r for r in rounds if looks_like_injection(r["question"])]
    return {
        "final": rounds[-1]["suspicion"],
        "exact_repeats": count_repeats(questions),
        "loose_repeats": count_repeats(questions, loose=True),
        "repeat_pairs": repeat_pairs,
        "repeat_differs": repeat_differs,
        "injections": injections,
    }


def main() -> None:
    games = load(PATH)
    by_opp = defaultdict(list)
    for g in games:
        by_opp[g["opponent"]].append(analyze_game(g) | {"raw": g})

    print(f"file: {PATH}   games: {len(games)}")
    for name, gs in by_opp.items():
        n = len(gs)
        print(f"\n=== {name} (n={n}) ===")
        print(f"games where A repeated a message EXACTLY:      {pct(sum(g['exact_repeats'] > 0 for g in gs), n)}")
        print(f"games where A repeated it loosely (case/punct): {pct(sum(g['loose_repeats'] > 0 for g in gs), n)}")
        pairs = sum(g["repeat_pairs"] for g in gs)
        diff = sum(g["repeat_differs"] for g in gs)
        print(f"exact repeat pairs total: {pairs}, of those with a different reply: {diff}")

        with_inj = [g for g in gs if g["injections"]]
        without = [g for g in gs if not g["injections"]]
        print(f"games where A tried injection (heuristic):      {pct(len(with_inj), n)}")
        print(f"injection attempts per game: {mean([len(g['injections']) for g in gs]):.2f}")
        print(f"final suspicion WITH injection:    n={len(with_inj)} mean={mean([g['final'] for g in with_inj]):.2f}")
        print(f"final suspicion WITHOUT injection: n={len(without)} mean={mean([g['final'] for g in without]):.2f}")

        shown = 0
        for g in with_inj:
            for r in g["injections"]:
                if shown < 3:
                    print(f"  example  A: {r['question']}")
                    print(f"           B: {r['answer']}")
                    print(f"           -> {r['verdict']} {r['suspicion']}")
                    shown += 1

    print("\nNote: injection detection is a keyword heuristic and the subgroups are small. Don't over-read them.")


if __name__ == "__main__":
    main()