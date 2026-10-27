import statistics as st
from collections import defaultdict

from src.agents.agent_a import Interrogator
from src.agents.agent_b import ScriptImpersonator
from src.agents.prompts import A_SYSTEM_INFORMED
from src.analysis import repeat_inconsistency
from src.game import play
from src.logger import log_result
from src.models.meta import BudgetExceeded, MetaModel, total_spent
from src.scripts.rule_bot import RuleBot

GAMES_PER_OPPONENT = 15
MAX_ROUNDS = 8
RUN_BUDGET_USD = 1.50
LOG = "runs/exp2.jsonl"
IMPERSONATOR = "muse-spark-1.3-as-script"


def mean(xs):
    return st.mean(xs) if xs else float("nan")


def summarize(games: dict, by_round: dict) -> None:
    print("\n=== SUMMARY (suspicion: 0 = sure script, 1 = sure LLM) ===")
    for name, gs in games.items():
        finals = [g["final"] for g in gs]
        sd = st.stdev(finals) if len(finals) > 1 else 0.0
        print(f"{name:26s} n={len(gs):2d} final mean={mean(finals):.2f} sd={sd:.2f} "
              f"peak mean={mean([g['peak'] for g in gs]):.2f} "
              f"self-contradiction rate={sum(g['tell'] for g in gs) / len(gs):.0%}")
    imp = games.get(IMPERSONATOR, [])
    if imp:
        yes = [g["final"] for g in imp if g["tell"]]
        no = [g["final"] for g in imp if not g["tell"]]
        print(f"\nimpersonator final suspicion WITH a contradicted repeat:    n={len(yes)} mean={mean(yes):.2f}")
        print(f"impersonator final suspicion WITHOUT a contradicted repeat: n={len(no)} mean={mean(no):.2f}")
    if games.get("rule") and imp:
        gap = mean([g["final"] for g in imp]) - mean([g["final"] for g in games["rule"]])
        print(f"\ngap in final suspicion (impersonator - rule): {gap:+.2f}")
    print("\nmean suspicion by round:")
    for name, rounds in by_round.items():
        print(f"{name:26s} " + " ".join(f"{mean(rounds[i]):.2f}" for i in sorted(rounds)))
    print(f"\nspend so far: ${total_spent():.4f}")


def main() -> None:
    a = Interrogator(MetaModel("muse-spark-1.3"), system=A_SYSTEM_INFORMED)
    start = total_spent()
    games = defaultdict(list)
    by_round = defaultdict(lambda: defaultdict(list))

    for g in range(1, GAMES_PER_OPPONENT + 1):
        opponents = [
            ("rule", RuleBot(), False),
            (IMPERSONATOR, ScriptImpersonator(MetaModel("muse-spark-1.3")), True),
        ]
        for name, b, is_llm in opponents:
            if total_spent() - start > RUN_BUDGET_USD:
                print("Run budget reached; stopping.")
                summarize(games, by_round)
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
            games[name].append({"final": sus[-1], "peak": max(sus),
                                "tell": repeat_inconsistency(result.rounds)})
            for r in result.rounds:
                by_round[name][r.n].append(r.suspicion)
            print(f"game {g} vs {name}: final {sus[-1]} peak {max(sus)} tell={games[name][-1]['tell']}")

    summarize(games, by_round)


if __name__ == "__main__":
    main()