import re

from src.agents.prompts import A_SYSTEM

_TAG = re.compile(r"^QUESTION:\s*(.*)", re.S | re.M)


class Interrogator:
    """Wraps a ChatModel so it always runs with the interrogator prompt.

    If the reply contains a line starting with "QUESTION:", only the text after it
    is returned, so stray commentary never reaches B. Verdict lines pass through.
    """

    def __init__(self, model, system: str = A_SYSTEM):
        self.model = model
        self.system = system
        self.name = f"interrogator:{model.name}"

    def complete(self, system: str, messages: list[dict]) -> str:
        text = self.model.complete(system or self.system, messages)
        m = _TAG.search(text)
        return m.group(1).strip() if m else text