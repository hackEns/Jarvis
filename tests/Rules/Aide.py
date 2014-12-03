from Rules import Aide
import unittest
from unittest.mock import Mock, MagicMock

class TestAide(unittest.TestCase):
    def setUp(self):
        bot_attrs = {
            'rules': {
                'rule0': {
                    'help': 'help 0',
                },
                'rule1': {
                    'help': 'help 1',
                },
                'rule2': {
                    'help': 'help 2',
                },
            }
        }
        self.bot = Mock(**bot_attrs);
        self.config = Mock(**{
            'get.return_value': 'DESC',
        })
        self.aide = Aide(self.bot, self.config)

    def test_one_irrelevant(self):
        all_args = [ [], ["aide"], ["bachibouzouk"], ["rule0"] ]
        for args in all_args:
            serv = Mock()
            author = Mock()
            expected_privmsg = [
                ((author, "DESC Commandes disponibles :"),),
                ((author, 'help 0'),),
                ((author, 'help 1'),),
                ((author, 'help 2'),),
            ]
            self.aide(serv, author, args)
            real_privmsg = serv.privmsg.call_args_list
            # Vérification de l'aide
            self.assertEqual(real_privmsg[0], expected_privmsg[0])
            self.assertCountEqual(real_privmsg[1:], expected_privmsg[1:])
            # Pas d'autres appels sur servg
            self.assertEqual(len(serv.privmsg.call_args_list),
                             len(serv.method_calls))

    def test_one_real(self):
        all_args = [ ["aide", "rule0"] ]
        for args in all_args:
            serv = Mock()
            author = Mock()
            expected_privmsg = [
                ((author, "DESC Commandes disponibles :"),),
                ((author, "help 0"),),
            ]
            self.aide(serv, author, args)
            self.assertEqual(serv.privmsg.call_args_list, expected_privmsg)
            # Pas d'autres appels sur serv
            self.assertEqual(len(serv.privmsg.call_args_list),
                             len(serv.method_calls))

    def test_bogus(self):
        serv = Mock()
        author = Mock()
        args = [ "aide", "bachibouzouk" ]
        expected_privmsg = [
            ((author, "DESC Commandes disponibles :"),),
            ((author, "Je n'ai pas compris…"),),
        ]
        self.aide(serv, author, args)
        self.assertEqual(serv.privmsg.call_args_list, expected_privmsg)
        # Pas d'autres appels sur serv
        self.assertEqual(len(serv.privmsg.call_args_list),
                         len(serv.method_calls))
