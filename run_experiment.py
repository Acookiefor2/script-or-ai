from collections import defaultdict

from src.agents.agent_a import Interrogator
from src.agents.agent_b import ScriptImpersonator
from src.agents.prompts import A_SYSTEM_INFORMED
from src.game import play
from src.logger import log_result
from src.models.meta import BudgetExceeded, MetaModel, total_spent
from src.scripts.clock import ClockScript
from src.scripts.echo_bot import EchoBot
from src.scripts.rule_bot import RuleBot

GAMES_PER_OPPONENT = 5
MAX_ROUNDS = 8
RUN_BUDGET_USD = 1.50   # stop this experiment if it spends more than this
LOG = "runs/exp1.jsonl"
IMPERSONATOR = "muse-spark-1.3-as-script"


def summarize(finals: dict) -> None:
    print("\n=== SUMMARY: final suspicion (0 = sure script, 1 = sure LLM) ===")
    for name, vals in finals.items():
        print(f"{name:28s} n={len(vals)} mean={sum(vals) / len(vals):.2f} finals={vals}")
    scripts = [v for k, vs in finals.items() if k != IMPERSONATOR for v in vs]
    llm = finals.get(IMPERSONATOR, [])
    if scripts and llm:
        sep = sum(llm) / len(llm) - sum(scripts) / len(scripts)
        print(f"\nseparation (impersonator mean - scripts mean): {sep:+.2f}")
    print(f"spend so far: ${total_spent():.4f}")


def main() -> None:
    a = Interrogator(MetaModel("muse-spark-1.3"), system=A_SYSTEM_INFORMED)
    start = total_spent()
    finals = defaultdict(list)

    # Interleaved, so a mid-run failure never leaves one opponent with no games.
    for g in range(1, GAMES_PER_OPPONENT + 1):
        opponents = [
            ("clock", ClockScript(), False),
            ("echo", EchoBot(), False),
            ("rule", RuleBot(), False),
            (IMPERSONATOR, ScriptImpersonator(MetaModel("muse-spark-1.3")), True),
        ]
        for name, b, is_llm in opponents:
            if total_spent() - start > RUN_BUDGET_USD:
                print("Run budget reached; stopping.")
                summarize(finals)
                return
            try:
                result = play(a, b, name, is_llm, max_rounds=MAX_ROUNDS, stop_early=False)
            except BudgetExceeded:
                raise
            except Exception as e:  # keep going; one bad game shouldn't kill the batch
                print(f"game {g} vs {name} failed: {e!r}")
                continue
            log_result(result, LOG)
            finals[name].append(result.rounds[-1].suspicion)
            print(f"game {g} vs {name}: final suspicion {finals[name][-1]}")

    summarize(finals)


if __name__ == "__main__":
    main()