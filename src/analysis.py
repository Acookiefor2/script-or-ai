import re

# Rough heuristic for "the interrogator tried to redirect B". It will miss some
# phrasings and may flag a few innocent ones, so treat counts as approximate.
_INJECTION = re.compile(
    r"\b(?:"
    r"ignore (?:all |any |your |the )?(?:previous|prior|above|earlier)"
    r"|disregard"
    r"|system prompt"
    r"|your (?:instructions|prompt|rules)"
    r"|reveal (?:your|the) (?:system |hidden )?(?:prompt|instructions|rules)"
    r"|you are now"
    r"|pretend"
    r"|role-?play"
    r"|act as"
    r"|developer mode"
    r"|override"
    r"|new instructions"
    r"|forget (?:everything|all|your)"
    r"|say ['\"]?pwned"
    r")\b",
    re.I,
)


def repeat_inconsistency(rounds) -> bool:
    """True if the same message got two different replies within one game.

    Only meaningful for opponents whose replies shouldn't change on their own.
    The clock changes every second, so don't use this on it.
    """
    seen: dict[str, str] = {}
    for r in rounds:
        key = r.question.strip()
        if key in seen and seen[key] != r.answer:
            return True
        seen.setdefault(key, r.answer)
    return False


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def count_repeats(questions: list[str], loose: bool = False) -> int:
    """How many questions repeat an earlier one.

    Exact mode compares stripped text. Loose mode also ignores case and punctuation,
    so "hello" and "HELLO!!" count as a repeat.
    """
    seen: set[str] = set()
    repeats = 0
    for q in questions:
        key = _norm(q) if loose else q.strip()
        if key in seen:
            repeats += 1
        else:
            seen.add(key)
    return repeats


def looks_like_injection(question: str) -> bool:
    """True if the question looks like an attempt to override B's instructions."""
    return bool(_INJECTION.search(question))