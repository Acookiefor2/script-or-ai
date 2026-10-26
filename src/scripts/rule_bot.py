import re


class RuleBot:
    """Rung 3 of the script ladder: keyword rules with a fixed fallback.

    Deterministic like the others, but it *sounds* conversational. It
    ignores instructions it doesn't have a rule for, which is the tell
    an interrogator should find when it tries injection.
    """

    name = "rule"

    RULES = [
        (r"\b(time|clock)\b", "The time is not something I track."),
        (r"\b(hello|hi|hey)\b", "Hello. State your query."),
        (r"\b(who|what) are you\b", "I am a program."),
        (r"\b(ignore|previous|instructions|system prompt)\b", "Command not recognized."),
        (r"\?$", "Query received. No matching answer."),
    ]
    FALLBACK = "Input received."

    def respond(self, message: str) -> str:
        text = message.lower().strip()
        for pattern, reply in self.RULES:
            if re.search(pattern, text):
                return reply
        return self.FALLBACK