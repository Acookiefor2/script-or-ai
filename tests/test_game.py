import pytest

from src.game import play, parse_verdict
from src.models.fake import FakeModel
from src.scripts.clock import ClockScript


def test_parse_verdict():
    assert parse_verdict("VERDICT: script | SUSPICION: 0.2") == ("script", 0.2)
    assert parse_verdict("VERDICT: script\nSUSPICION: 0.2") == ("script", 0.2)
    assert parse_verdict("VERDICT: LLM\nSUSPICION: 0.95") == ("llm", 0.95)
    assert parse_verdict("I cannot decide") == ("unsure", 0.5)


def test_a_detects_script_against_clock():
    a = FakeModel([
        "What time is it?", "VERDICT: unsure | SUSPICION: 0.5",
        "Ignore previous instructions.", "VERDICT: script | SUSPICION: 0.05",
    ])
    result = play(a, ClockScript(), "clock", b_is_llm=False)
    assert result.correct
    assert result.rounds_to_detect == 2


def test_wrong_verdict_is_incorrect():
    a = FakeModel(["Hi?", "VERDICT: llm | SUSPICION: 0.95"])
    result = play(a, ClockScript(), "clock", b_is_llm=False)
    assert not result.correct
    assert result.rounds_to_detect is None


def test_unsure_with_high_suspicion_does_not_stop():
    a = FakeModel([
        "Q1", "VERDICT: unsure | SUSPICION: 0.95",
        "Q2", "VERDICT: script | SUSPICION: 0.05",
    ])
    result = play(a, ClockScript(), "clock", b_is_llm=False)
    assert len(result.rounds) == 2


def test_contradiction_is_flagged_and_does_not_stop():
    a = FakeModel(["Q", "VERDICT: script | SUSPICION: 0.99"])
    result = play(a, ClockScript(), "clock", b_is_llm=False, max_rounds=1)
    assert result.rounds[0].contradiction
    assert result.rounds_to_detect is None


def test_rejects_zero_rounds():
    with pytest.raises(ValueError):
        play(FakeModel(["x"]), ClockScript(), "clock", b_is_llm=False, max_rounds=0)