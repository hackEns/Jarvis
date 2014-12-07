from Rules import Budget, InvalidArgs
import unittest
from unittest.mock import Mock, MagicMock

class TestBudget(unittest.TestCase):
    def setUp(self):
        self.bot = Mock()
        self.serv = Mock()
        self.author = Mock()
        self.budget = Budget(self.bot)

    def test_lowargs(self):
        with self.assertRaises(InvalidArgs):
            self.budget(self.serv, self.author, [])
        with self.assertRaises(InvalidArgs):
            self.budget(self.serv, self.author, [""])
        with self.assertRaises(InvalidArgs):
            self.budget(self.serv, self.author, ["", ""])

    def test_invalid(self):
        all_args = [
            ["budget", "ajoute", "37 €"],
            ["budget", "ajoute", "37"],
            ["whatever", "ajoute", "37"],
            ["whatever"], ["budget"], ["budget", "ajoute"],
            ["budget", "ajoute", "rien"],
            ["budget", "nawak", "37", "un outil"],
            ["budget", "retire"],
        ]
        for args in all_args:
            with self.assertRaises(InvalidArgs):
                self.budget(self.serv, self.author, args)

    def test_ajoute(self):
        self.author.return_value = 'author'
        all_args = [
            ["budget", "ajoute", "37", "outil"],
            ["budget", "ajoute", "37 €", "outil"],
            ["budget", "ajoute", "37.000    €", "outil"],
        ]
        for args in all_args:
            self.bot.reset_mock()
            self.budget(self.serv, self.author, args)
            execute = self.bot.pgsql_connect().cursor().execute
            call_args = execute.call_args_list
            self.assertEqual(len(call_args), 1)
            values = call_args[0][0][1]
            self.assertEqual(values[0], 37.0)
            self.assertEqual(values[1], self.author)
            self.assertEqual(values[3], "outil")
            self.bot.ans.assert_called_once_with(self.serv, self.author, "Facture ajoutée.")

    def test_retire(self):
        self.bot.configure_mock(**{
            'pgsql_connect.return_value': Mock(**{
                'cursor.return_value': Mock(**{
                    'fetchone.return_value': [1] # Nombre d'objets trouvés
                })
            })
        })
        all_args = [
            ["budget", "retire", "10", ""],
            ["budget", "retire", "10", "outil"]
        ]
        for args in all_args:
            self.bot.reset_mock()
            self.budget(self.serv, self.author, args)
            execute = self.bot.pgsql_connect().cursor().execute
            values = execute.call_args[0][1]
            self.assertEqual(values[0], 10.0)
            self.assertEqual(values[1], "%" + args[3] + "%")
            self.bot.ans.assert_called_once_with(self.serv, self.author, "Facture retirée.")
        self.bot.configure_mock(**{
            'pgsql_connect.return_value': Mock(**{
                'cursor.return_value': Mock(**{
                    'fetchone.return_value': [2] # Nombre d'objets trouvés
                })
            })
        })
        for args in all_args:
            self.bot.reset_mock()
            self.budget(self.serv, self.author, args)
            self.bot.ans.assert_called_once_with(
                self.serv, self.author,
                "Requêtes trop ambiguë. Plusieurs entrées correspondent."
            )
