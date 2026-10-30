import json
import os
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_URL = "https://api.meta.ai/v1"
USAGE_LOG = "runs/usage.jsonl"
BUDGET_USD = 100.0  # hard stop, well under the $150 credit

# Games can run in several threads. This lock keeps usage-log reads and writes from interleaving.
_LOG_LOCK = threading.Lock()

# USD per 1M tokens (input, output). Copied from the models page; verify on Model specs.
PRICES = {
    "muse-spark-1.3": (1.25, 4.25),
    "muse-spark-1.2": (1.25, 4.25),
    "muse-wonder-1.0": (4.00, 20.00),
}


class BudgetExceeded(RuntimeError):
    pass


class EmptyReply(RuntimeError):
    pass


def _line_cost(line: str) -> float:
    """Sum cost_usd over the JSON objects in one log line.

    A line normally holds one object. If writes ever collide, a line can hold several objects
    glued together or be cut short, so salvage whatever parses and skip the rest.
    """
    decoder = json.JSONDecoder()
    text = line.strip()
    i, total = 0, 0.0
    while i < len(text):
        try:
            obj, i = decoder.raw_decode(text, i)
        except json.JSONDecodeError:
            break
        if isinstance(obj, dict):
            try:
                total += float(obj.get("cost_usd", 0.0) or 0.0)
            except (TypeError, ValueError):
                pass
        while i < len(text) and text[i].isspace():
            i += 1
    return total


def total_spent(path: str = USAGE_LOG) -> float:
    p = Path(path)
    if not p.exists():
        return 0.0
    with _LOG_LOCK:
        with p.open(encoding="utf-8", errors="replace") as f:
            return sum(_line_cost(line) for line in f)


class MetaModel:
    """ChatModel backed by the Meta Model API (OpenAI-compatible Chat Completions).

    max_tokens covers reasoning + visible output, so keep it generous.
    reasoning_effort: "minimal" is the lowest Spark supports ("none" returns HTTP 400).
    """

    def __init__(self, model_id: str = "muse-spark-1.3", client=None,
                 usage_log: str = USAGE_LOG, budget_usd: float = BUDGET_USD,
                 temperature: float | None = None, max_tokens: int = 1500,
                 reasoning_effort: str = "minimal"):
        self.name = model_id
        self.model_id = model_id
        self.usage_log = usage_log
        self.budget_usd = budget_usd
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.client = client or OpenAI(base_url=BASE_URL, api_key=os.environ["MODEL_API_KEY"])

    def complete(self, system: str, messages: list[dict]) -> str:
        if total_spent(self.usage_log) >= self.budget_usd:
            raise BudgetExceeded(f"Spent >= ${self.budget_usd}; refusing to call the API.")

        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        kwargs = {
            "model": self.model_id,
            "messages": msgs,
            "max_tokens": self.max_tokens,
            "reasoning_effort": self.reasoning_effort,
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        resp = self.client.chat.completions.create(**kwargs)
        self._log_usage(resp)

        choice = resp.choices[0]
        text = choice.message.content
        if not text:
            raise EmptyReply(
                f"Empty reply from {self.model_id} "
                f"(finish_reason={getattr(choice, 'finish_reason', None)}). "
                "Raise max_tokens or lower reasoning_effort."
            )
        return text

    def _log_usage(self, resp) -> None:
        u = resp.usage
        in_tok, out_tok = u.prompt_tokens, u.completion_tokens
        details = getattr(u, "completion_tokens_details", None)
        reasoning = getattr(details, "reasoning_tokens", 0) or 0
        pin, pout = PRICES.get(self.model_id, (0.0, 0.0))
        cost = (in_tok * pin + out_tok * pout) / 1_000_000  # ignores cache discount, so it overestimates
        line = json.dumps({
            "ts": time.time(), "model": self.model_id,
            "input_tokens": in_tok, "output_tokens": out_tok,
            "reasoning_tokens": reasoning, "cost_usd": cost,
        }) + "\n"
        p = Path(self.usage_log)
        with _LOG_LOCK:
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8") as f:
                f.write(line)