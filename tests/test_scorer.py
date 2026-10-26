from src.game import GameResult
from src.scorer import score


def make(opponent, is_llm, verdict, correct, rtd=None):
    return GameResult(opponent=opponent, is_llm=is_llm, final_verdict=verdict,
                      correct=correct, rounds_to_detect=rtd)


def test_score_counts_errors_separately():
    results = [
        make("clock", False, "script", True, 2),
        make("echo", False, "llm", False),      # false positive
        make("muse", True, "script", False),    # false negative
        make("muse", True, "llm", True, 4),
    ]
    s = score(results)
    assert s["accuracy"] == 0.5
    assert s["false_positives"] == 1
    assert s["false_negatives"] == 1
    assert s["avg_rounds_to_detect"] == 3
    assert s["by_opponent"]["muse"] == 0.5


def test_score_empty():
    assert score([])["games"] == 0