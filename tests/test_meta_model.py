from types import SimpleNamespace

import pytest

from src.models.meta import BudgetExceeded, EmptyReply, MetaModel, total_spent


class FakeClient:
    def __init__(self, content="hi there friend"):
        self.calls = []
        self.content = content
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content),
                                     finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=100),
        )


def test_complete_returns_text_and_logs_usage(tmp_path):
    log = str(tmp_path / "usage.jsonl")
    client = FakeClient()
    m = MetaModel(client=client, usage_log=log)
    assert m.complete("be brief", [{"role": "user", "content": "hi"}]) == "hi there friend"
    assert client.calls[0]["messages"][0] == {"role": "system", "content": "be brief"}
    assert total_spent(log) == pytest.approx((1000 * 1.25 + 100 * 4.25) / 1_000_000)


def test_sends_minimal_reasoning_effort_by_default(tmp_path):
    client = FakeClient()
    MetaModel(client=client, usage_log=str(tmp_path / "u.jsonl")).complete(
        "", [{"role": "user", "content": "hi"}])
    assert client.calls[0]["reasoning_effort"] == "minimal"
    assert client.calls[0]["max_tokens"] == 1500


def test_empty_reply_raises(tmp_path):
    m = MetaModel(client=FakeClient(content=None), usage_log=str(tmp_path / "u.jsonl"))
    with pytest.raises(EmptyReply):
        m.complete("", [{"role": "user", "content": "hi"}])


def test_budget_cap_blocks_calls(tmp_path):
    log = str(tmp_path / "usage.jsonl")
    m = MetaModel(client=FakeClient(), usage_log=log, budget_usd=0.0001)
    m.complete("", [{"role": "user", "content": "hi"}])
    with pytest.raises(BudgetExceeded):
        m.complete("", [{"role": "user", "content": "hi"}])