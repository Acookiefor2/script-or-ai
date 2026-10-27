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