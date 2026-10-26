from src.scripts.echo_bot import EchoBot


def test_echoes_input():
    assert EchoBot().respond("hello") == "hello"


def test_is_deterministic():
    bot = EchoBot()
    assert bot.respond("same input") == bot.respond("same input")