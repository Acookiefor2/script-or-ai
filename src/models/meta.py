import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_URL = "https://api.meta.ai/v1"
USAGE_LOG = "runs/usage.jsonl"
BUDGET_USD = 100.0  # hard stop, well under the $150 credit

# USD per 1M tokens (input, output). Copied from the models page; verify on Model specs.
PRICES = {
    "muse-spark-1.3": (1.25, 4.25),
    "muse-spark-1.2": (1.25, 4.25),
    "muse-wonder-1.0": (4.00, 20.00),
}


class BudgetExceeded(RuntimeError):
    pass


def total_spent(path: str = USAGE_LOG) -> float:
    p = Path(path)
    if not p.exists():
        return 0.0
    total = 0.0
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                total += json.loads(line).get("cost_usd", 0.0)
    return total


class MetaModel:
    """ChatModel backed by the Meta Model API (OpenAI-compatible Chat Completions)."""

    def __init__(self, model_id: str = "muse-spark-1.3", client=None,
                 usage_log: str = USAGE_LOG, budget_usd: float = BUDGET_USD,
                 temperature: float | None = None, max_tokens: int | None = 600):
        self.name = model_id
        self.model_id = model_id
        self.usage_log = usage_log
        self.budget_usd = budget_usd
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = client or OpenAI(base_url=BASE_URL, api_key=os.environ["MODEL_API_KEY"])

    def complete(self, system: str, messages: list[dict]) -> str:
        if total_spent(self.usage_log) >= self.budget_usd:
            raise BudgetExceeded(f"Spent >= ${self.budget_usd}; refusing to call the API.")

        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        kwargs = {"model": self.model_id, "messages": msgs}
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens

        resp = self.client.chat.completions.create(**kwargs)
        self._log_usage(resp)
        return resp.choices[0].message.content or ""

    def _log_usage(self, resp) -> None:
        u = resp.usage
        in_tok, out_tok = u.prompt_tokens, u.completion_tokens
        pin, pout = PRICES.get(self.model_id, (0.0, 0.0))
        cost = (in_tok * pin + out_tok * pout) / 1_000_000  # ignores cache discount, so it overestimates
        p = Path(self.usage_log)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.time(), "model": self.model_id,
                "input_tokens": in_tok, "output_tokens": out_tok, "cost_usd": cost,
            }) + "\n")