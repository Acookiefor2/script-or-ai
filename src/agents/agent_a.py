from src.agents.prompts import A_SYSTEM


class Interrogator:
    """Wraps a ChatModel so it always runs with the interrogator prompt."""

    def __init__(self, model, system: str = A_SYSTEM):
        self.model = model
        self.system = system
        self.name = f"interrogator:{model.name}"

    def complete(self, system: str, messages: list[dict]) -> str:
        return self.model.complete(system or self.system, messages)