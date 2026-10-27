from src.agents.agent_a import Interrogator


class Recorder:
    name = "rec"

    def __init__(self, reply="ok"):
        self.seen = None
        self.reply = reply

    def complete(self, system, messages):
        self.seen = system
        return self.reply


def test_interrogator_uses_its_system_prompt():
    rec = Recorder()
    assert Interrogator(rec, system="SYS").complete("", []) == "ok"
    assert rec.seen == "SYS"


def test_strips_commentary_before_question_tag():
    rec = Recorder("Switching to a nonsense probe.\nQUESTION: xqzblorp 123")
    assert Interrogator(rec).complete("", []) == "xqzblorp 123"


def test_verdict_lines_pass_through():
    rec = Recorder("VERDICT: script | SUSPICION: 0.2")
    assert Interrogator(rec).complete("", []) == "VERDICT: script | SUSPICION: 0.2"


def test_strips_commentary_on_same_line():
    rec = Recorder("Probing rigidity now.QUESTION: HELLO!!")
    assert Interrogator(rec).complete("", []) == "HELLO!!"