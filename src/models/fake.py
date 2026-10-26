class FakeModel:
    """Returns canned replies in order. Used to test the game loop offline."""

    def __init__(self, replies: list[str], name: str = "fake"):
        self.name = name
        self._replies = replies
        self._i = 0

    def complete(self, system: str, messages: list[dict]) -> str:
        reply = self._replies[self._i % len(self._replies)]
        self._i += 1
        return reply