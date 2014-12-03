from Rules import Ping
import unittest
from unittest.mock import Mock, MagicMock

class TestPing(unittest.TestCase):
    def setUp(self):
        self.bot = Mock()
        self.ping = Ping(self.bot)

    def test_ping(self):
        all_args = [
            ["ping"],
            ["ping", "pong"],
            ["ping", "pang", "poung"]
        ]
        for args in all_args:
            self.bot.reset_mock()
            serv = Mock()
            author = 'author'
            self.ping(serv, author, args)
            self.bot.say.assert_called_once_with(serv, 'author: pong')

    def test_invalid(self):
        all_args = [
            ["pong"],
            [],
            [""],
            ["baltazar"],
        ]
        for args in all_args:
            serv = Mock()
            author = Mock()
            self.ping(serv, author, args)
            self.assertEqual(len(self.bot.mock_calls), 0)
