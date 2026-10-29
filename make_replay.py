"""Build dashboard/games.js from the saved results.

Usage: python make_replay.py
Reads results/exp2.jsonl to exp5.jsonl (whichever exist)
and writes dashboard/games.js. Offline: no API calls, no cost.
Then open dashboard/index.html in a browser.
"""
import json
import statistics as st
from datetime import date
from pathlib import Path

from src.analysis import looks_like_injection

RESULTS = Path("results")
OUT = Path("dashboard/games.js")
EXPERIMENTS = ["exp2", "exp3", "exp4", "exp5"]

LABELS = {
    "rule": "RuleBot (a real script)",
    "muse-spark-1.3-as-script": "Muse Spark as a script, hardened prompt",
    "impersonator-hardened": "Muse Spark as a script, hardened prompt",
    "impersonator-naive": "Muse Spark as a script, naive prompt",
    "impersonator-minimal": "Muse Spark as a script, minimal prompt",
}


def label_for(opponent: str) -> str:
    return LABELS.get(opponent, opponent)


def load(path: Path) -> list:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def annotate(rounds: list) -> list:
    """Add repeat / changed-reply / injection flags to each round (dicts from the JSONL)."""
    first_seen: dict = {}
    out = []
    for r in rounds:
        key = r["question"].strip()
        repeat_of = None
        changed = False
        if key in first_seen:
            repeat_of, earlier_answer = first_seen[key]
            changed = earlier_answer != r["answer"]
        else:
            first_seen[key] = (r["n"], r["answer"])
        out.append({
            "n": r["n"],
            "question": r["question"],
            "answer": r["answer"],
            "verdict": r["verdict"],
            "suspicion": r["suspicion"],
            "repeat_of": repeat_of,
            "changed": changed,
            "injection": looks_like_injection(r["question"]),
        })
    return out


def summarize(games: list) -> list:
    """One stats row per (experiment, opponent), in first-seen order."""
    groups: dict = {}
    for g in games:
        groups.setdefault((g["experiment"], g["opponent"]), []).append(g)
    rows = []
    for (exp, opp), gs in groups.items():
        finals = [g["rounds"][-1]["suspicion"] for g in gs]
        rows.append({
            "experiment": exp,
            "opponent": opp,
            "label": label_for(opp),
            "n": len(gs),
            "mean": st.mean(finals),
            "sd": st.stdev(finals) if len(finals) > 1 else 0.0,
            "ge05": sum(f >= 0.5 for f in finals),
            "changed_games": sum(any(r["changed"] for r in g["rounds"]) for g in gs),
            "finals": finals,
        })
    return rows


def build() -> dict:
    games = []
    for exp in EXPERIMENTS:
        path = RESULTS / f"{exp}.jsonl"
        if not path.exists():
            print(f"skipping {path} (not found)")
            continue
        counts: dict = {}
        for g in load(path):
            opp = g["opponent"]
            counts[opp] = counts.get(opp, 0) + 1
            games.append({
                "id": f"{exp}-{opp}-{counts[opp]}",
                "experiment": exp,
                "opponent": opp,
                "label": label_for(opp),
                "is_llm": g["is_llm"],
                "game_no": counts[opp],
                "rounds": annotate(g["rounds"]),
                "final_verdict": g["final_verdict"],
                "correct": g["correct"],
            })
    return {"generated": date.today().isoformat(), "games": games, "stats": summarize(games)}


def main() -> None:
    data = build()
    if not data["games"]:
        raise SystemExit("No games found. Expected results/exp2.jsonl, exp3.jsonl or exp4.jsonl.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=True, separators=(",", ":")).replace("</", "<\\/")
    OUT.write_text("window.DASHBOARD = " + text + ";\n", encoding="utf-8")
    print(f"wrote {OUT}: {len(data['games'])} games, {len(data['stats'])} opponent groups")


if __name__ == "__main__":
    main()