from src.models.fake import FakeModel


def test_cycles_through_replies():
    m = FakeModel(["a", "b"])
    assert [m.complete("", []) for _ in range(3)] == ["a", "b", "a"]