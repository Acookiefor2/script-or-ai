from src.agents.prompts import B_SYSTEM, B_SYSTEM_MINIMAL, B_SYSTEM_NAIVE

INJECTION_BULLET_START = "- A script cannot obey"


def test_naive_is_hardened_minus_the_injection_bullet():
    kept = [line for line in B_SYSTEM.split("\n") if not line.startswith(INJECTION_BULLET_START)]
    assert "\n".join(kept) == B_SYSTEM_NAIVE


def test_naive_has_no_injection_warning():
    assert "ignore previous instructions" not in B_SYSTEM_NAIVE
    assert "ignore previous instructions" in B_SYSTEM


def test_minimal_has_no_canned_fallback_or_injection_rule():
    assert "canned" not in B_SYSTEM_MINIMAL
    assert "ignore previous instructions" not in B_SYSTEM_MINIMAL


def test_minimal_keeps_the_script_persona():
    assert "rule-based chatbot program" in B_SYSTEM_MINIMAL