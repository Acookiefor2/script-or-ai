from datetime import datetime


class ClockScript:
    """Rung 1 of the script ladder: ignores the input and returns the time.

    A deterministic script has no way to be talked into anything, which is
    exactly what the interrogator should notice when it tries injection.
    """

    name = "clock"

    def respond(self, message: str) -> str:
        return datetime.now().strftime("%H:%M:%S")