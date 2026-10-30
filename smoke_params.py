"""Which settings does muse-spark-1.3 accept? One tiny call per setting (a fraction of a cent each).

Usage: python smoke_params.py
Checks temperature=0 (for a temperature-0 impersonator run) and a few reasoning_effort values
(only "minimal" has been confirmed so far; "none" returned HTTP 400).
"""
import sys

from src.models.meta import MetaModel, total_spent

sys.stdout.reconfigure(encoding="utf-8")

PROMPT = [{"role": "user", "content": "Reply with exactly one word: ready"}]

CASES = [
    ("baseline (effort=minimal)", {}),
    ("temperature=0", {"temperature": 0}),
    ("temperature=0.7", {"temperature": 0.7}),
    ("reasoning_effort=low", {"reasoning_effort": "low"}),
    ("reasoning_effort=medium", {"reasoning_effort": "medium"}),
    ("reasoning_effort=high", {"reasoning_effort": "high"}),
]


def main() -> None:
    before = total_spent()
    for label, kwargs in CASES:
        try:
            reply = MetaModel("muse-spark-1.3", **kwargs).complete("", PROMPT)
            print(f"OK    {label:28s} -> {reply.strip()[:60]!r}")
        except Exception as e:  # report every failure, keep going
            print(f"FAIL  {label:28s} -> {type(e).__name__}: {str(e)[:200]}")
    print(f"\nspent on this check: about ${total_spent() - before:.4f}")


if __name__ == "__main__":
    main()