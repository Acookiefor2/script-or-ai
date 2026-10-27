from src.agents.agent_b import ScriptImpersonator
from src.game import respond_as_b


class Recorder:
    name = "rec"

    def __init__(self):
        self.seen = None

    def complete(self, system, messages):
        self.seen = system
        return "ok"


def test_impersonator_uses_its_system_prompt():
    rec = Recorder()
    b = ScriptImpersonator(rec, system="SYS")
    assert respond_as_b(b, "hello", []) == "ok"
    assert rec.seen == "SYS"


def test_impersonator_is_not_treated_as_a_script():
    assert not hasattr(ScriptImpersonator(Recorder()), "respond")