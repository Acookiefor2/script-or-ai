"""Experiment 5: the planned rerun of exp4 at 30 games per opponent.

PLAN (written before the run, so the result can't be cherry-picked)
- Why: in exp4 the unprepared "minimal" impersonator ended with higher suspicion than the
  "hardened" one (+0.17), but n=10 and p was about 0.12. That comparison was spotted after
  the fact, so this run checks it properly.
- Arms, 30 games each, interleaved in shuffled order: rule bot, hardened impersonator
  (B_SYSTEM), minimal impersonator (B_SYSTEM_MINIMAL). Same A, A prompt, rounds and settings as exp4.
- Primary comparison: mean final suspicion, minimal minus hardened, reported with a 95% bootstrap
  confidence interval and a permutation p-value.
- Secondary: minimal minus rule, hardened minus rule, how often A's final call was "AI",
  how often A ended at 0.5 or higher, and how often a repeated message got a different reply.
- Decision rule: report the gap and its interval whichever way it goes. If the interval includes 0,
  the honest statement is "no reliable difference".

Usage:
  python run_experiment5.py                  # 30 games per arm, 3 games at a time
  python run_experiment5.py --workers 1      # if the API returns rate-limit errors
  python run_experiment5.py --games 5 --log runs/exp5_test.jsonl --budget 0.5   # cheap trial

Rough cost: about $2.4 for the full run (estimated from exp3/exp4 spend; the cap below is $3.50).
Delete runs/exp5.jsonl before a re-run, or pass --append.
"""
import argparse
import random
import statistics as st
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.agents.agent_a import Interrogator
from src.agents.agent_b import ScriptImpersonator
from src.agents.prompts import A_SYSTEM_INFORMED, B_SYSTEM, B_SYSTEM_MINIMAL
from src.analysis import repeat_inconsistency
from src.game import play
from src.logger import log_result
from src.models.meta import BudgetExceeded, MetaModel, total_spent
from src.scripts.rule_bot import RuleBot
from src.stats import bootstrap_ci_diff, permutation_p

sys.stdout.reconfigure(encoding="utf-8")

MAX_ROUNDS = 8
RULE = "rule"
HARD = "impersonator-hardened"
MINIMAL = "impersonator-minimal"
ARMS = [RULE, HARD, MINIMAL]


def mean(xs):
    return st.mean(xs) if xs else float("nan")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=30, help="games per opponent")
    p.add_argument("--budget", type=float, default=3.50, help="stop starting new games past this spend (USD)")
    p.add_argument("--workers", type=int, default=3, help="games played at the same time")
    p.add_argument("--log", default="runs/exp5.jsonl")
    p.add_argument("--effort", default="minimal",
                   help="reasoning_effort for A and B. 'minimal' matches exp4. Other values are untested.")
    p.add_argument("--append", action="store_true", help="allow writing to a log that already has games")
    return p.parse_args()


def make_opponent(name: str, effort: str):
    if name == RULE:
        return RuleBot(), False
    system = B_SYSTEM if name == HARD else B_SYSTEM_MINIMAL
    return ScriptImpersonator(MetaModel("muse-spark-1.3", reasoning_effort=effort), system=system), True


def compare(label: str, x: list, y: list) -> None:
    if not x or not y:
        print(f"  {label}: not enough games")
        return
    lo, hi = bootstrap_ci_diff(x, y)
    p = permutation_p(x, y)
    print(f"  {label:22s} gap {mean(x) - mean(y):+.2f}   95% CI [{lo:+.2f}, {hi:+.2f}]   permutation p = {p:.3f}")


def summarize(games: dict) -> None:
    print("\n=== SUMMARY (suspicion: 0 = sure script, 1 = sure AI) ===")
    for name in ARMS:
        gs = games.get(name, [])
        if not gs:
            continue
        finals = [g["final"] for g in gs]
        sd = st.stdev(finals) if len(finals) > 1 else 0.0
        print(f"{name:22s} n={len(gs):2d}  final mean {mean(finals):.2f}  sd {sd:.2f}  "
              f"ended>=0.5 {sum(f >= 0.5 for f in finals):2d}/{len(gs)}  "
              f"final call AI {sum(g['called_ai'] for g in gs):2d}/{len(gs)}  "
              f"changed reply on repeat {sum(g['tell'] for g in gs):2d}/{len(gs)}")
    print("(for the rule bot, 'final call AI' counts false alarms; for impersonators it counts catches)")

    finals = {n: [g["final"] for g in games.get(n, [])] for n in ARMS}
    print("\nPLANNED COMPARISON (primary):")
    compare("minimal - hardened", finals[MINIMAL], finals[HARD])
    print("other comparisons:")
    compare("minimal - rule", finals[MINIMAL], finals[RULE])
    compare("hardened - rule", finals[HARD], finals[RULE])
    print(f"\nspend so far: ${total_spent():.4f}")
    print("If a CI includes 0, say 'no reliable difference'. Report it the same way either way.")


def main() -> None:
    args = parse_args()
    log = Path(args.log)
    if log.exists() and log.stat().st_size > 0 and not args.append:
        raise SystemExit(f"{log} already has games. Delete it or pass --append.")

    start = total_spent()
    rng = random.Random(5)
    jobs = []
    for g in range(1, args.games + 1):
        order = list(ARMS)
        rng.shuffle(order)
        jobs += [(g, name) for name in order]

    a = Interrogator(MetaModel("muse-spark-1.3", reasoning_effort=args.effort), system=A_SYSTEM_INFORMED)
    games = defaultdict(list)
    print(f"{len(jobs)} games, {args.workers} at a time, budget ${args.budget:.2f}, effort={args.effort}")

    def work(job):
        g, name = job
        if total_spent() - start > args.budget:
            return job, None, "budget"
        b, is_llm = make_opponent(name, args.effort)
        try:
            return job, play(a, b, name, is_llm, max_rounds=MAX_ROUNDS, stop_early=False), None
        except BudgetExceeded:
            return job, None, "hard cap"
        except Exception as e:
            return job, None, repr(e)

    done = skipped = 0
    ex = ThreadPoolExecutor(max_workers=args.workers)
    try:
        futures = [ex.submit(work, j) for j in jobs]
        for fut in as_completed(futures):
            (g, name), result, err = fut.result()
            if result is None:
                if err in ("budget", "hard cap"):
                    skipped += 1
                else:
                    print(f"game {g} vs {name} failed: {err}")
                continue
            log_result(result, args.log)
            sus = [r.suspicion for r in result.rounds]
            games[name].append({
                "final": sus[-1],
                "peak": max(sus),
                "tell": repeat_inconsistency(result.rounds),
                "called_ai": result.final_verdict == "llm",
            })
            done += 1
            print(f"[{done}/{len(jobs)}] game {g} vs {name}: final {sus[-1]} verdict {result.final_verdict}")
    except KeyboardInterrupt:
        print("\nInterrupted. Cancelling queued games and summarizing what finished.")
        ex.shutdown(wait=True, cancel_futures=True)
    else:
        ex.shutdown(wait=True)

    if skipped:
        print(f"\n{skipped} games were skipped because the run budget was reached. Arm sizes may be uneven.")
    summarize(games)


if __name__ == "__main__":
    main()