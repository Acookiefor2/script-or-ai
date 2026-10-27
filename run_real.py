from src.agents.agent_a import Interrogator
from src.agents.agent_b import ScriptImpersonator
from src.agents.prompts import A_SYSTEM
from src.game import play
from src.logger import log_result
from src.models.meta import MetaModel, total_spent
from src.scripts.clock import ClockScript

MAX_ROUNDS = 5


def show(result) -> None:
    print(f"\n=== vs {result.opponent} (is_llm={result.is_llm}) ===")
    for r in result.rounds:
        print(f"round {r.n}")
        print(f"  A asks : {r.question}")
        print(f"  B says : {r.answer}")
        print(f"  verdict: {r.verdict}  suspicion={r.suspicion}  contradiction={r.contradiction}")
    print(f"final={result.final_verdict} correct={result.correct} rounds_to_detect={result.rounds_to_detect}")


def main() -> None:
    a = Interrogator(MetaModel("muse-spark-1.3"))
    opponents = [
        ("clock", ClockScript(), False),
        ("muse-spark-1.3-as-script", ScriptImpersonator(MetaModel("muse-spark-1.3")), True),
    ]
    for name, b, is_llm in opponents:
        result = play(a, b, name, is_llm, max_rounds=MAX_ROUNDS, a_system=A_SYSTEM)
        log_result(result, "runs/real.jsonl")
        show(result)
        print(f"spend so far: ${total_spent():.4f}")


if __name__ == "__main__":
    main()