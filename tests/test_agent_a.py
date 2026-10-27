from src.agents.agent_a import Interrogator


class Recorder:
    name = "rec"

    def __init__(self):
        self.seen = None

    def complete(self, system, messages):
        self.seen = system
        return "ok"


def test_interrogator_uses_its_system_prompt():
    rec = Recorder()
    assert Interrogator(rec, system="SYS").complete("", []) == "ok"
    assert rec.seen == "SYS"