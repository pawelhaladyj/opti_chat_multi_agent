from organizer.core import say_hello


def test_say_hello():
    assert say_hello("World") == "Hello, World!"
