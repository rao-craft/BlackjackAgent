"""The package as a host calls it: a whole hand in one folder, the screen and the picture it answers, the state the
picture carries, and each refusal by kind."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import granite
from granite import agentjson
from granite.package import entry

from blackjack_agent import png, roster
from blackjack_agent import table as drawing
from blackjack_agent.cards import WIDTH
from blackjack_agent.game import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.folder = os.path.realpath(tempfile.mkdtemp(prefix="blackjack-"))
        self.notes = []
        self.host = granite.Host(self.folder, "deal me in", None, self.notes.append)
        self.blackjack = roster.find("blackjack")

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def call(self, **input):
        return granite.perform_value(self.blackjack, input, self.host)

    def refused(self, **input):
        with self.assertRaises(granite.Refusal) as refused:
            self.call(**input)
        return refused.exception

    def test_a_hand_is_dealt_hit_and_stood_and_the_table_drawn_each_time(self):
        dealt = self.call(move="deal", bet=10, seed=3)
        self.assertEqual((dealt["state"], dealt["player"]["cards"], dealt["dealer"]["cards"], dealt["dealer"]["hidden"]),
                         ("playing", ["6♠", "4♠"], ["10♥"], 1))
        self.assertEqual(dealt["made"], [{"kind": "table", "name": "table", "path": "blackjack/table.png",
                                          "state": "written"}])
        self.assertEqual((dealt["path"], dealt["paths"], dealt["format"]), ("blackjack/table.png",
                                                                           ["blackjack/table.png"], "granite-answer/1"))
        self.assertNotIn("6♥", json.dumps(dealt))  # the hole card
        hit = self.call(move="hit")
        self.assertEqual((hit["player"]["total"], hit["moves"], hit["made"][0]["state"]), (19, ["hit", "stand"],
                                                                                          "rewritten"))
        stood = self.call()  # a hand in play: show
        self.assertEqual(stood["said"], "You draw 9♠. You have 19.")
        stood = self.call(move="stand")
        self.assertEqual((stood["state"], stood["chips"], stood["net"], stood["dealer"]["cards"]),
                         ("won", 110, 10, ["10♥", "6♥", "9♣"]))
        self.assertIn("the dealer draws 9♣", self.notes)
        for answer in (dealt, hit, stood):
            self.assertTrue(all(len(line) <= WIDTH for line in answer["screen"]))
        self.assertEqual(stood["screen"][-2], "  You stand on 19. The dealer busts with 25: you win 10.")

        picture = Path(self.folder, "blackjack", "table.png").read_bytes()
        self.assertEqual(png.size(picture), (drawing.WIDTH, drawing.HEIGHT))
        carried = Table.read(json.loads(drawing.carried(picture)))
        self.assertEqual((carried.state, carried.chips, carried.player), ("won", 110, ["6S", "4S", "9S"]))

        again = self.call()  # no hand in play: deal, at the last bet
        self.assertEqual((again["hand"], again["bet"], again["chips"] + again["bet"]), (2, 10, 110))

    def test_a_new_table_and_one_kept_elsewhere(self):
        fresh = self.call(move="new", chips=50, table="tables/one.png")
        self.assertEqual((fresh["state"], fresh["chips"], fresh["moves"], fresh["path"]),
                         ("ready", 50, ["deal", "new"], "tables/one.png"))
        self.assertTrue(os.path.exists(os.path.join(self.folder, "tables", "one.png")))

    def test_each_refusal_is_said_with_its_kind(self):
        self.assertEqual(self.refused(move="fold").kind, "input")
        self.assertEqual(self.refused(bet="ten").said,
                         "blackjack could not read its input: invalid type: string \"ten\", expected u32")
        self.assertEqual(self.refused(move="hit").said, "no hand is in play to hit: say deal to start one")
        self.call(move="deal", seed=3)
        self.assertEqual(self.refused(move="deal").said, "a hand is in play: hit, stand or double before you deal "
                                                         "again")
        with open(os.path.join(self.folder, "not-a-table.png"), "wb") as out:
            out.write(png.write(1, 1, b"\0\0\0"))
        refusal = self.refused(table="not-a-table.png")
        self.assertEqual((refusal.kind, refusal.said), ("call", "not-a-table.png is not a table blackjack drew (it "
                                                                "carries no table): move it aside, or give another "
                                                                "`table`"))
        nowhere = granite.perform_value
        with self.assertRaises(granite.Refusal) as refused:
            nowhere(self.blackjack, {"move": "deal"}, granite.Host.none())
        self.assertEqual(refused.exception.kind, "host")

    def test_the_entry_and_the_schemas_kept_beside_it_agree(self):
        said = entry(self.blackjack)
        self.assertEqual((said["word"], said["module"], said["type"], said["makes"][0]["kind"]),
                         ("blackjack", "blackjack_agent", "blackjack_agent.Blackjack", "table"))
        kept = agentjson.read(Path(ROOT, "Schema", "blackjack.input.schema.json").read_bytes())
        shape = granite.schema.of(self.blackjack.Input).json_schema(hide_directory=True)
        self.assertEqual({k: v for k, v in kept.items() if k in shape}, shape)
        self.assertIn("#canvas", said["guide"])
        self.assertIn("```text", said["guide"])


if __name__ == "__main__":
    unittest.main()
