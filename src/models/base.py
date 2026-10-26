from typing import Protocol


class ChatModel(Protocol):
    """Anything that can take a conversation and return the next reply."""

    name: str

    def complete(self, system: str, messages: list[dict]) -> str:
        """messages look like [{"role": "user" | "assistant", "content": "..."}]"""
        ...