from src.analysis import repeat_inconsistency
from src.game import Round


def rd(n, q, a):
    return Round(n, q, a, "unsure", 0.5)


def test_flags_same_message_different_reply():
    assert repeat_inconsistency([rd(1, "hello", "Hi."), rd(2, "x", "No."), rd(3, "hello", "Input received.")])


def test_consistent_repeats_are_fine():
    assert not repeat_inconsistency([rd(1, "hello", "Hi."), rd(2, "hello", "Hi.")])


def test_no_repeats_is_fine():
    assert not repeat_inconsistency([rd(1, "a", "x"), rd(2, "b", "y")])