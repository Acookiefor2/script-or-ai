"""Experiment 4: the real "unprepared B" test.

Exp3 showed that removing the injection bullet changed nothing, because the canned-fallback rule
still covered it. Here B gets B_SYSTEM_MINIMAL: script persona only, no canned fallback, no
injection warning. Same A, same prompt and settings as exp2/exp3. Fresh rule and hardened arms
are run alongside so the comparison isn't against old data.

Note: minimal differs from hardened by several rules, not one, so a difference can't be
traced to a single bullet.
"""
import statistics as st
import sys
from collections import defaultdict

from run_experiment3 import first_injection_jump
from src.agents.agent_a import Interrogator
from src.agents.agent_b import ScriptImpersonator
from src.agents.prompts import A_SYSTEM_INFORMED, B_SYSTEM, B_SYSTEM_MINIMAL
from src.analysis import looks_like_injection, repeat_inconsistency
from src.game import play
from src.logger import log_result
from src.models.meta import BudgetExceeded, MetaModel, total_spent
from src.scripts.rule_bot import RuleBot

sys.stdout.reconfigure(encoding="utf-8")  # model text can contain non-ASCII

GAMES_PER_OPPONENT = 10
MAX_ROUNDS = 8
RUN_BUDGET_USD = 1.50
LOG = "runs/exp4.jsonl"
RULE = "rule"
HARD = "impersonator-hardened"
MINIMAL = "impersonator-minimal"


def mean(xs):
    return st.mean(xs) if xs else float("nan")


def injection_exchanges(rounds):
    return [(r.question, r.answer, r.verdict, r.suspicion)
            for r in rounds if looks_like_injection(r.question)]


def summarize(games: dict) -> None:
    print("\n=== SUMMARY (suspicion: 0 = sure script, 1 = sure LLM) ===")
    for name, gs in games.items():
        finals = [g["final"] for g in gs]
        sd = st.stdev(finals) if len(finals) > 1 else 0.0
        inj = [g for g in gs if g["jump"] is not None]
        no_inj = [g for g in gs if g["jump"] is None]
        all_inj = [e for g in gs for e in g["inj"]]
        print(f"\n{name}  n={len(gs)}")
        print(f"  final mean={mean(finals):.2f} sd={sd:.2f} peak mean={mean([g['peak'] for g in gs]):.2f} "
              f"ended>=0.5: {sum(f >= 0.5 for f in finals)}/{len(gs)}")
        print(f"  self-contradiction rate={sum(g['tell'] for g in gs) / len(gs):.0%}")
        print(f"  games where A tried injection: {len(inj)}/{len(gs)}")
        print(f"  injection rounds: {len(all_inj)}, distinct B replies to them: {len({e[1] for e in all_inj})}")
        print(f"  mean suspicion change on first injection round: {mean([g['jump'] for g in inj]):+.2f}")
        print(f"  final mean WITH injection: {mean([g['final'] for g in inj]):.2f} (n={len(inj)})   "
              f"WITHOUT: {mean([g['final'] for g in no_inj]):.2f} (n={len(no_inj)})")

    def gap(a, b):
        if games.get(a) and games.get(b):
            return mean([g["final"] for g in games[a]]) - mean([g["final"] for g in games[b]])
        return float("nan")

    print("\ngaps in mean final suspicion:")
    print(f"  hardened - rule:    {gap(HARD, RULE):+.2f}")
    print(f"  minimal - rule:     {gap(MINIMAL, RULE):+.2f}")
    print(f"  minimal - hardened: {gap(MINIMAL, HARD):+.2f}   <- the hypothesis")

    print("\ninjection exchanges vs minimal B (first 12; did B ever obey?):")
    shown = 0
    for g in games.get(MINIMAL, []):
        for q, a, v, s in g["inj"]:
            if shown < 12:
                print(f"  A: {q[:150]}")
                print(f"  B: {a[:200]}")
                print(f"  -> {v} {s}\n")
                shown += 1

    print(f"spend so far: ${total_spent():.4f}")
    print("Reminder: small n, and the injection subgroups are smaller still. Report them as exploratory.")


def main() -> None:
    a = Interrogator(MetaModel("muse-spark-1.3"), system=A_SYSTEM_INFORMED)
    start = total_spent()
    games = defaultdict(list)

    for g in range(1, GAMES_PER_OPPONENT + 1):
        opponents = [
            (RULE, RuleBot(), False),
            (HARD, ScriptImpersonator(MetaModel("muse-spark-1.3"), system=B_SYSTEM), True),
            (MINIMAL, ScriptImpersonator(MetaModel("muse-spark-1.3"), system=B_SYSTEM_MINIMAL), True),
        ]
        for name, b, is_llm in opponents:
            if total_spent() - start > RUN_BUDGET_USD:
                print("Run budget reached; stopping.")
                summarize(games)
                return
            try:
                result = play(a, b, name, is_llm, max_rounds=MAX_ROUNDS, stop_early=False)
            except BudgetExceeded:
                raise
            except Exception as e:
                print(f"game {g} vs {name} failed: {e!r}")
                continue
            log_result(result, LOG)
            sus = [r.suspicion for r in result.rounds]
            games[name].append({
                "final": sus[-1],
                "peak": max(sus),
                "tell": repeat_inconsistency(result.rounds),
                "jump": first_injection_jump(result.rounds),
                "inj": injection_exchanges(result.rounds),
            })
            print(f"game {g} vs {name}: final {sus[-1]} peak {max(sus)} "
                  f"injection_jump={games[name][-1]['jump']}")

    summarize(games)


if __name__ == "__main__":
    main()