from src.agents.prompts import A_SYSTEM


class Interrogator:
    """Wraps a ChatModel so it always runs with the interrogator prompt.

    If the reply contains "QUESTION:" anywhere, only the text after the last one is
    returned, so stray commentary never reaches B. Verdict lines pass through.
    """

    def __init__(self, model, system: str = A_SYSTEM):
        self.model = model
        self.system = system
        self.name = f"interrogator:{model.name}"

    def complete(self, system: str, messages: list[dict]) -> str:
        text = self.model.complete(system or self.system, messages)
        if "QUESTION:" in text:
            question = text.rsplit("QUESTION:", 1)[1].strip()
            if question:
                return question
        return text