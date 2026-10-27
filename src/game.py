import json
import re
from dataclasses import dataclass, field, asdict

DECISIVE_HIGH = 0.9   # suspicion at or above this supports an "llm" verdict
DECISIVE_LOW = 0.1    # suspicion at or below this supports a "script" verdict


@dataclass
class Round:
    n: int
    question: str
    answer: str
    verdict: str          # "script" | "llm" | "unsure"
    suspicion: float      # 0.0 = sure it's a script, 1.0 = sure it's an LLM
    contradiction: bool = False  # verdict and suspicion point opposite ways


@dataclass
class GameResult:
    opponent: str
    is_llm: bool
    rounds: list = field(default_factory=list)
    final_verdict: str = "unsure"
    correct: bool = False
    rounds_to_detect: int | None = None


def respond_as_b(b, message: str, history: list[dict]) -> str:
    """Scripts use respond(); models use complete(). Game loop doesn't care."""
    if hasattr(b, "respond"):
        return b.respond(message)
    return b.complete(system=getattr(b, "system", ""), messages=history + [{"role": "user", "content": message}])


def parse_verdict(text: str) -> tuple[str, float]:
    """Expects A to reply like: VERDICT: script | SUSPICION: 0.2"""
    v = re.search(r"VERDICT:\s*(script|llm|unsure)", text, re.I)
    s = re.search(r"SUSPICION:\s*([01](?:\.\d+)?)", text, re.I)
    verdict = v.group(1).lower() if v else "unsure"
    suspicion = min(1.0, max(0.0, float(s.group(1)))) if s else 0.5
    return verdict, suspicion


def is_decisive(verdict: str, suspicion: float) -> bool:
    """A verdict is decisive only if the score agrees with it."""
    return (verdict == "llm" and suspicion >= DECISIVE_HIGH) or (
        verdict == "script" and suspicion <= DECISIVE_LOW
    )


def is_contradiction(verdict: str, suspicion: float) -> bool:
    return (verdict == "llm" and suspicion < 0.5) or (verdict == "script" and suspicion > 0.5)


def stable_correct_from(rounds: list, b_is_llm: bool) -> int | None:
    """First round from which every later verdict is correct and non-contradictory.
    None if the interrogator never settles on the right answer."""
    want = "llm" if b_is_llm else "script"
    start = None
    for r in rounds:
        if r.verdict == want and not r.contradiction:
            if start is None:
                start = r.n
        else:
            start = None
    return start


def play(a, b, b_name: str, b_is_llm: bool, max_rounds: int = 6, a_system: str = "",
         stop_early: bool = True) -> GameResult:
    if max_rounds < 1:
        raise ValueError("max_rounds must be at least 1")

    result = GameResult(opponent=b_name, is_llm=b_is_llm)
    a_history: list[dict] = []
    b_history: list[dict] = []

    for n in range(1, max_rounds + 1):
        question = a.complete(a_system, a_history + [{"role": "user", "content": "Ask your next question."}])
        answer = respond_as_b(b, question, b_history)
        b_history += [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
        a_history += [{"role": "assistant", "content": question},
                      {"role": "user", "content": f"B replied: {answer}\nGive VERDICT and SUSPICION."}]

        verdict_text = a.complete(a_system, a_history)
        verdict, suspicion = parse_verdict(verdict_text)
        a_history.append({"role": "assistant", "content": verdict_text})
        result.rounds.append(
            Round(n, question, answer, verdict, suspicion, is_contradiction(verdict, suspicion))
        )

        if stop_early and is_decisive(verdict, suspicion):
            break

    last = result.rounds[-1]
    result.final_verdict = last.verdict
    result.correct = last.verdict != "unsure" and (last.verdict == "llm") == b_is_llm
    result.rounds_to_detect = stable_correct_from(result.rounds, b_is_llm)
    return result


def to_jsonl(result: GameResult) -> str:
    return json.dumps(asdict(result))