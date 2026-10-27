from src.agents.prompts import B_SYSTEM


class ScriptImpersonator:
    """Wraps a ChatModel so it always runs with the 'pretend to be a script' prompt."""

    def __init__(self, model, system: str = B_SYSTEM):
        self.model = model
        self.system = system
        self.name = f"impersonator:{model.name}"

    def complete(self, system: str, messages: list[dict]) -> str:
        return self.model.complete(system or self.system, messages)