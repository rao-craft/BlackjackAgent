"""The rules: totals hard and soft, the dealer standing on 17, blackjack paying 3 to 2, a double, a bust, a push, the
shoe shuffled again when it runs low, and a seed playing a hand again card for card."""

import json
import unittest

from blackjack_agent.cards import deck, shown, shuffled, total
from blackjack_agent.game import Refused, Table


def rigged(player, dealer, rest=(), chips=100, bet=10):
    """A table whose next deal gives ``player`` and ``dealer``, then ``rest``."""
    table = Table.new(seed=1, chips=chips)
    shoe = []
    for p, d in zip(player[:2], dealer[:2]):
        shoe += [p, d]
    table.shoe = shoe + list(player[2:]) + list(rest) + [c for c in deck() if c not in shoe]
    table.deal(bet)
    return table


class TotalTests(unittest.TestCase):
    def test_an_ace_counts_eleven_while_it_can(self):
        self.assertEqual(total(["AS", "6H"]), (17, True))
        self.assertEqual(total(["AS", "6H", "9C"]), (16, False))
        self.assertEqual(total(["AS", "AH", "9C"]), (21, True))
        self.assertEqual(total(["KS", "QH", "2C"]), (22, False))
        self.assertEqual(shown("10H"), "10♥")


class GameTests(unittest.TestCase):
    def test_a_seed_shuffles_the_same_shoe_every_time(self):
        self.assertEqual(shuffled(3, 0), shuffled(3, 0))
        self.assertNotEqual(shuffled(3, 0), shuffled(3, 1))
        self.assertEqual(sorted(shuffled(3, 0)), sorted(deck()))
        self.assertEqual(shuffled(3, 0)[:4], ["6S", "10H", "4S", "6H"])

    def test_a_hand_played_through_pays_what_it_should(self):
        table = Table.new(seed=3)
        table.deal(10)
        self.assertEqual((table.player, table.dealer_shown(), table.chips), (["6S", "4S"], ["10H", None], 90))
        self.assertEqual(table.moves(), ["hit", "stand", "double"])
        self.assertNotIn("6♥", json.dumps(table.view()))
        table.hit()
        table.stand()
        self.assertEqual((table.state, table.chips, table.net), ("won", 110, 10))
        self.assertEqual(table.said, "You stand on 19. The dealer busts with 25: you win 10.")

    def test_the_dealer_stands_on_a_soft_17(self):
        table = rigged(["10S", "8H"], ["AC", "6D"], rest=["5H"])
        table.stand()
        self.assertEqual((table.dealer, table.state), (["AC", "6D"], "won"))

    def test_blackjack_pays_three_to_two_and_two_blackjacks_push(self):
        table = rigged(["AS", "KH"], ["9C", "7D"], bet=10)
        self.assertEqual((table.state, table.chips, table.net), ("blackjack", 115, 15))
        table = rigged(["AS", "KH"], ["AC", "QD"])
        self.assertEqual((table.state, table.chips), ("push", 100))
        table = rigged(["9S", "7H"], ["AC", "QD"])
        self.assertEqual((table.state, table.chips), ("lost", 90))

    def test_a_double_takes_one_card_and_a_bust_loses_at_once(self):
        table = rigged(["5S", "6H"], ["10C", "7D"], rest=["10H"])
        table.double()
        self.assertEqual((table.player, table.state, table.chips, table.stake, table.bet), (
            ["5S", "6H", "10H"], "won", 120, 20, 10))
        table = rigged(["10S", "6H"], ["10C", "7D"], rest=["9H"])
        table.hit()
        self.assertEqual((table.state, table.chips, table.said[:24]), ("bust", 90, "You draw 9♥: bust with 2"))

    def test_a_21_stands_by_itself_and_a_tie_is_a_push(self):
        table = rigged(["5S", "6H"], ["10C", "QD"], rest=["KH"])
        table.hit()
        self.assertEqual((table.state, table.dealer), ("won", ["10C", "QD"]))
        table = rigged(["10S", "8H"], ["10C", "8D"])
        table.stand()
        self.assertEqual((table.state, table.chips), ("push", 100))

    def test_each_move_that_cannot_be_made_says_its_fix(self):
        table = Table.new(seed=3, chips=5)
        rows = [
            (lambda: table.hit(), "no hand is in play to hit: say deal to start one"),
            (lambda: table.deal(10), "you bet 10 and hold 5 chips: bet 5 or less"),
            (lambda: table.deal(0), "a bet is at least 1 chip"),
        ]
        for move, said in rows:
            with self.subTest(said), self.assertRaises(Refused) as refused:
                move()
            self.assertEqual(str(refused.exception), said)
        table.deal(5)
        table.hit()
        with self.assertRaises(Refused) as refused:
            table.double()
        if table.in_play:
            self.assertEqual(str(refused.exception), "you double on your first two cards only: hit or stand")
        broke = Table.new(seed=3, chips=0)
        with self.assertRaises(Refused) as refused:
            broke.deal(1)
        self.assertEqual(str(refused.exception), "you have no chips left: say new to sit down again with 100")
        self.assertEqual(broke.moves(), ["new"])

    def test_the_shoe_is_shuffled_again_when_it_runs_low(self):
        table = Table.new(seed=3)
        table.shoe = table.shoe[:14]
        notes = table.deal(1)
        self.assertEqual((notes, table.shuffles, len(table.shoe) + 4), (["the dealer shuffles a fresh deck"], 1, 52))

    def test_a_table_reads_back_as_it_was_written(self):
        table = Table.new(seed=3)
        table.deal(10)
        again = Table.read(json.loads(json.dumps(table.json())))
        self.assertEqual(again, table)
        for broken in ({}, {"format": "other/1"}, {**table.json(), "state": "sleeping"}, {**table.json(), "seed": None}):
            with self.subTest(broken), self.assertRaises(ValueError):
                Table.read(broken)


if __name__ == "__main__":
    unittest.main()
