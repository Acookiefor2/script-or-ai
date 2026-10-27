from types import SimpleNamespace

import pytest

from src.models.meta import BudgetExceeded, MetaModel, total_spent


class FakeClient:
    def __init__(self):
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="hi there friend"))],
            usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=100),
        )


def test_complete_returns_text_and_logs_usage(tmp_path):
    log = str(tmp_path / "usage.jsonl")
    client = FakeClient()
    m = MetaModel(client=client, usage_log=log)
    assert m.complete("be brief", [{"role": "user", "content": "hi"}]) == "hi there friend"
    assert client.calls[0]["messages"][0] == {"role": "system", "content": "be brief"}
    assert total_spent(log) == pytest.approx((1000 * 1.25 + 100 * 4.25) / 1_000_000)


def test_budget_cap_blocks_calls(tmp_path):
    log = str(tmp_path / "usage.jsonl")
    m = MetaModel(client=FakeClient(), usage_log=log, budget_usd=0.0001)
    m.complete("", [{"role": "user", "content": "hi"}])
    with pytest.raises(BudgetExceeded):
        m.complete("", [{"role": "user", "content": "hi"}])