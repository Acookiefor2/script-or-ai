"""Experiment 6: does pinning the impersonator's temperature to 0 make it harder to catch?

PLAN (written before the run)
- Why: in exp5 the unprepared "minimal" impersonator was exposed mainly by changing its reply to a
  repeated message (9 of 29 games; 0 of 30 for the hardened impersonator and the real rule bot).
  Sampling randomness could be a cause, and temperature 0 is the cheapest possible fix.
- Arms, 30 games each, shuffled order, same A, A prompt, rounds and settings as exp5:
    rule                      the keyword RuleBot (real script baseline)
    impersonator-hardened-t0  B_SYSTEM, B at temperature 0
    impersonator-minimal-t0   B_SYSTEM_MINIMAL, B at temperature 0
    impersonator-minimal      B_SYSTEM_MINIMAL, B at the API default temperature (fresh control)
- Primary comparison: mean final suspicion, minimal (default temperature) minus minimal-t0, with a 95%
  bootstrap CI and a permutation p-value. Also reported: how many games had a changed reply on a repeat.
- Secondary: minimal-t0 minus hardened-t0, minimal-t0 minus rule, hardened-t0 minus rule.
- Decision rule: report the gap and its interval whichever way it goes. If the CI includes 0, the honest
  statement is "no reliable difference".
- Expect a caveat either way: B sees the whole conversation, so even at temperature 0 its reply to "hello"
  can differ between round 1 and round 5 because the context differs. A real script is stateless.

Usage:
  python run_experiment6.py                                   # 30 games per arm, 3 at a time
  python run_experiment6.py --games 3 --log runs/exp6_test.jsonl --budget 0.6   # cheap trial
Rough cost: about $3.3 for the full run (estimated from exp5; cap below is $4.50).
If a run stops early (crash, Ctrl+C), finish it with --resume: it counts the games already in the
log and plays only the missing ones. Without --resume it refuses to touch a log that has games.
"""
import argparse
import json
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from run_experiment5 import compare, mean
from src.agents.agent_a import Interrogator
from src.agents.agent_b import ScriptImpersonator
from src.agents.prompts import A_SYSTEM_INFORMED, B_SYSTEM, B_SYSTEM_MINIMAL
from src.analysis import repeat_inconsistency
from src.game import Round, play
from src.logger import log_result
from src.models.meta import BudgetExceeded, MetaModel, total_spent
from src.scripts.rule_bot import RuleBot

sys.stdout.reconfigure(encoding="utf-8")

MAX_ROUNDS = 8
RULE = "rule"
HARD_T0 = "impersonator-hardened-t0"
MIN_T0 = "impersonator-minimal-t0"
MIN_DEF = "impersonator-minimal"
ARMS = [RULE, HARD_T0, MIN_T0, MIN_DEF]

# arm -> (system prompt, temperature). temperature None means the API default.
IMPERSONATORS = {
    HARD_T0: (B_SYSTEM, 0),
    MIN_T0: (B_SYSTEM_MINIMAL, 0),
    MIN_DEF: (B_SYSTEM_MINIMAL, None),
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=30, help="games per opponent")
    p.add_argument("--budget", type=float, default=4.50, help="stop starting new games past this spend (USD)")
    p.add_argument("--workers", type=int, default=3, help="games played at the same time")
    p.add_argument("--log", default="runs/exp6.jsonl")
    p.add_argument("--effort", default="minimal", help="reasoning_effort for A and B (minimal matches exp2 to exp5)")
    p.add_argument("--resume", action="store_true",
                   help="continue a run: count games already in the log and play only the missing ones")
    return p.parse_args()


def make_opponent(name: str, effort: str):
    if name == RULE:
        return RuleBot(), False
    system, temperature = IMPERSONATORS[name]
    model = MetaModel("muse-spark-1.3", reasoning_effort=effort, temperature=temperature)
    return ScriptImpersonator(model, system=system), True


def game_record(rounds: list, final_verdict: str) -> dict:
    return {
        "final": rounds[-1].suspicion,
        "tell": repeat_inconsistency(rounds),
        "called_ai": final_verdict == "llm",
    }


def load_logged(path: Path) -> list:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def summarize(games: dict) -> None:
    print("\n=== SUMMARY (suspicion: 0 = sure script, 1 = sure AI) ===")
    for name in ARMS:
        gs = games.get(name, [])
        if not gs:
            continue
        finals = [g["final"] for g in gs]
        sd = st.stdev(finals) if len(finals) > 1 else 0.0
        print(f"{name:26s} n={len(gs):2d}  final mean {mean(finals):.2f}  sd {sd:.2f}  "
              f"ended>=0.5 {sum(f >= 0.5 for f in finals):2d}/{len(gs)}  "
              f"final call AI {sum(g['called_ai'] for g in gs):2d}/{len(gs)}  "
              f"changed reply on repeat {sum(g['tell'] for g in gs):2d}/{len(gs)}")
    print("(for the rule bot, 'final call AI' counts false alarms; for impersonators it counts catches)")

    f = {n: [g["final"] for g in games.get(n, [])] for n in ARMS}
    print("\nPLANNED COMPARISON (primary): does temperature 0 change how detectable the minimal impersonator is?")
    compare("minimal - minimal-t0", f[MIN_DEF], f[MIN_T0])
    print("other comparisons:")
    compare("minimal-t0 - hardened-t0", f[MIN_T0], f[HARD_T0])
    compare("minimal-t0 - rule", f[MIN_T0], f[RULE])
    compare("hardened-t0 - rule", f[HARD_T0], f[RULE])
    print(f"\nspend so far: ${total_spent():.4f}")
    print("If a CI includes 0, say 'no reliable difference'. Report it the same way either way.")


def main() -> None:
    args = parse_args()
    log = Path(args.log)
    games = defaultdict(list)
    done_counts = Counter()
    if log.exists() and log.stat().st_size > 0:
        if not args.resume:
            raise SystemExit(f"{log} already has games. Pass --resume to finish the run, "
                             "or delete the file to start over.")
        for g in load_logged(log):
            rounds = [Round(**r) for r in g["rounds"]]
            games[g["opponent"]].append(game_record(rounds, g["final_verdict"]))
            done_counts[g["opponent"]] += 1
        print(f"resuming: {sum(done_counts.values())} games already logged {dict(done_counts)}")

    start = total_spent()
    rng = random.Random(6)
    jobs = []
    for k in range(1, args.games + 1):
        names = [n for n in ARMS if done_counts[n] < k]
        rng.shuffle(names)
        jobs += [(k, n) for n in names]
    if not jobs:
        print("Nothing left to play.")
        summarize(games)
        return

    a = Interrogator(MetaModel("muse-spark-1.3", reasoning_effort=args.effort), system=A_SYSTEM_INFORMED)
    print(f"{len(jobs)} games, {args.workers} at a time, budget ${args.budget:.2f}, effort={args.effort}")

    def work(job):
        g, name = job
        try:
            if total_spent() - start > args.budget:
                return job, None, "budget"
            b, is_llm = make_opponent(name, args.effort)
            return job, play(a, b, name, is_llm, max_rounds=MAX_ROUNDS, stop_early=False), None
        except BudgetExceeded:
            return job, None, "hard cap"
        except Exception as e:  # one bad game must never kill the batch
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
            games[name].append(game_record(result.rounds, result.final_verdict))
            done += 1
            print(f"[{done}/{len(jobs)}] game {g} vs {name}: "
                  f"final {result.rounds[-1].suspicion} verdict {result.final_verdict}")
    except KeyboardInterrupt:
        print("\nInterrupted. Cancelling queued games and summarizing what finished.")
        ex.shutdown(wait=True, cancel_futures=True)
    else:
        ex.shutdown(wait=True)

    if skipped:
        print(f"\n{skipped} games were skipped because the run budget was reached. Arm sizes may be uneven.")
    failed = len(jobs) - done - skipped
    if failed > 0:
        print(f"{failed} games failed. Run again with --resume to replay just the missing ones.")
    summarize(games)


if __name__ == "__main__":
    main()