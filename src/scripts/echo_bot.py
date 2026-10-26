class EchoBot:
    """Rung 2 of the script ladder: repeats the message back verbatim.

    Slightly more interactive than the clock, but still fully deterministic.
    It can't be argued with, persuaded, or injected.
    """

    name = "echo"

    def respond(self, message: str) -> str:
        return message