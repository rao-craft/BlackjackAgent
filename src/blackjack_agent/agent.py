"""``blackjack``: a hand of blackjack a call at a time, the table answered as text for the chat and drawn as a picture
for Canvas. The game's state rides inside the picture, so the next call plays on from it.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Literal

import granite

from blackjack_agent import table as drawing
from blackjack_agent.game import Refused, Table
from blackjack_agent.screen import screen

TABLE = "blackjack/table.png"

GUIDE = (
    "Play blackjack with the person, one call per move. Call blackjack with the move they say: deal (with bet when "
    "they name one), hit, stand, double, show to see the table, or new to sit down again with fresh chips. Reply with "
    "the answer's `screen` copied exactly, line for line, inside a ```text fence, then `said` in your own words and the "
    "moves on offer (`moves`). Never invent, guess or reveal a card the answer does not show: the dealer's face-down "
    "card stays hidden until the hand ends. The table is drawn to blackjack/table.png as well, which Canvas (#canvas) "
    "shows."
)


@dataclass
class BlackjackInput:
    move: Literal["deal", "hit", "stand", "double", "show", "new"] | None = granite.field(
        default=None, note="deal, hit, stand, double, show, or new; left out, deal when no hand is in play, else show")
    bet: granite.u32 | None = granite.field(
        default=None, note="chips to bet on a deal; the last bet when left out, 10 at a new table")
    seed: granite.u64 | None = granite.field(
        default=None, note="a number that fixes the shuffle, so a game plays again card for card; a fresh shuffle "
                           "when left out")
    chips: granite.u32 | None = granite.field(
        default=None, note="chips to sit down with at a new table; 100 when left out")
    table: str | None = granite.field(
        default=None, note="where the table's picture is kept, in the folder; blackjack/table.png when left out")
    directory: str | None = None


class Blackjack(granite.AgentPackage):
    word = "blackjack"
    summary = "deals blackjack a move at a time: the table as text for the chat, and as a picture for Canvas."
    guide = GUIDE
    module = "blackjack_agent"
    type = "blackjack_agent.Blackjack"
    makes = [granite.Make("table", "the blackjack table as a PNG, the game's state inside it", ["blackjack/"],
                          never="a card the shoe did not deal")]
    Input = BlackjackInput

    def run(self, input: BlackjackInput, context: granite.Context) -> None:
        folder = input.directory or context.directory
        if not folder:
            raise granite.Refusal("host", "blackjack keeps its table in a folder, and this call offers none: give "
                                          "`directory`")
        said_path = input.table or TABLE
        path = os.path.normpath(os.path.join(folder, said_path))
        existing = _read(path, said_path)
        table = existing or Table.new(input.seed, input.chips)
        move = input.move or ("show" if table.in_play else "deal")
        notes: list[str] = []
        try:
            if move == "new":
                table = Table.new(input.seed, input.chips)
            elif move == "deal":
                notes = table.deal(input.bet, input.seed if existing is not None else None)
            elif move == "hit":
                notes = table.hit()
            elif move == "stand":
                notes = table.stand()
            elif move == "double":
                notes = table.double()
        except Refused as refused:
            raise granite.Refusal("call", str(refused)) from None
        for note in notes:
            context.note(note)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = drawing.picture(table, json.dumps(table.json(), sort_keys=True, separators=(",", ":")))
        temporary = f"{path}.{os.getpid()}.writing"
        with open(temporary, "wb") as out:
            out.write(data)
        os.replace(temporary, path)
        context.note(f"drew the table to {said_path}")

        shown = _shown_path(path, context.directory)
        answer = granite.Answer(table.view(), screen=screen(table))
        answer.path(shown).made("table", "table", shown, "rewritten" if existing is not None else "written")
        answer.note(table.said)
        context.deliver(answer)


def _read(path: str, said_path: str) -> Table | None:
    """The table its picture carries; None when there is no picture yet. A picture that is not a table refuses."""
    try:
        with open(path, "rb") as opened:
            data = opened.read()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise granite.Refusal("call", f"{said_path} could not be read ({error.strerror}): give another `table`")
    try:
        state = drawing.carried(data)
        if state is None:
            raise ValueError("it carries no table")
        return Table.read(json.loads(state))
    except ValueError as error:
        raise granite.Refusal("call", f"{said_path} is not a table blackjack drew ({error}): move it aside, or give "
                                      "another `table`") from None


def _shown_path(path: str, directory: str | None) -> str:
    """The picture's path as the answer names it: relative to the host's folder when it is inside it."""
    if directory:
        relative = os.path.relpath(path, directory)
        if not relative.startswith(".."):
            return relative
    return path
