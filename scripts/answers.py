#!/usr/bin/env python3
"""What only blackjack answers, read from a check's kept folder: the cards seed 3 deals, the hole card hidden, every
screen line inside 60 columns, the table's picture and the state it carries, and each answer against blackjack's own
answer schema.

  scripts/answers.py <the check's --out folder> <GranitePython clone>
"""

import json
import os
import subprocess
import sys

out, granite = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(root, "src"), os.path.join(granite, "src")]

from blackjack_agent import png  # noqa: E402
from blackjack_agent import table as drawing  # noqa: E402
from blackjack_agent.cards import WIDTH  # noqa: E402
from blackjack_agent.game import Table  # noqa: E402


def failed(said: str) -> None:
    print(f"FAILED: {said}", file=sys.stderr)
    sys.exit(1)


def answer(label: str) -> dict:
    with open(os.path.join(out, f"{label}.answer.json")) as opened:
        return json.load(opened)


dealt, hit, stood = answer("1-deal.perform"), answer("2-hit.perform"), answer("3-stand.perform")
if (dealt["player"]["cards"], dealt["dealer"]["cards"], dealt["dealer"]["hidden"]) != (["6♠", "4♠"], ["10♥"], 1):
    failed(f"seed 3 deals 6♠ 4♠ against 10♥ and a hidden card: {dealt['player']} {dealt['dealer']}")
if "6♥" in json.dumps(dealt) or "6♥" in json.dumps(hit):
    failed("the dealer's hole card is in an answer while the hand is in play")
if (hit["player"]["total"], hit["moves"]) != (19, ["hit", "stand"]):
    failed(f"a hit gives 9♠ for 19: {hit['player']}")
if (stood["state"], stood["chips"], stood["net"], stood["dealer"]["cards"]) != ("won", 110, 10, ["10♥", "6♥", "9♣"]):
    failed(f"the dealer busts with 25 and the hand pays 10: {stood['state']} {stood['chips']} {stood['dealer']}")
for label, said in (("1-deal", dealt), ("2-hit", hit), ("3-stand", stood)):
    wide = [line for line in said["screen"] if len(line) > WIDTH]
    if wide:
        failed(f"{label}'s screen has a line over {WIDTH} columns: {wide[0]!r}")
print("seed 3: 6♠ 4♠ against 10♥ and a hidden card; 9♠ for 19; the dealer busts with 25; 110 chips", flush=True)

picture_path = os.path.join(out, "work", "blackjack", "table.png")
with open(picture_path, "rb") as opened:
    picture = opened.read()
if png.size(picture) != (drawing.WIDTH, drawing.HEIGHT):
    failed(f"the table is {png.size(picture)}")
carried = Table.read(json.loads(drawing.carried(picture)))
if (carried.state, carried.chips, carried.player) != ("won", 110, ["6S", "4S", "9S"]):
    failed(f"the picture carries {carried.state} {carried.chips} {carried.player}")
print(f"the table is {drawing.WIDTH}x{drawing.HEIGHT}, {len(picture)} bytes, and carries the hand it shows", flush=True)

cli = os.path.join(out, "granite-cli")
subprocess.run([sys.executable, os.path.join(granite, "scripts", "build-cli.py"), "--out", cli, "--python",
                sys.executable], check=True, stdout=subprocess.DEVNULL)
schemas = ["--schemas", os.path.join(root, "Schema"), "--schemas", os.path.join(granite, "Schema"),
           "--schemas", os.path.join(granite, "containers", "schemas")]
for label in ("1-deal.perform", "2-hit.perform", "3-stand.perform"):
    done = subprocess.run([cli, "check", *schemas, "--schema", "blackjack.answer.schema.json",
                           os.path.join(out, f"{label}.answer.json")])
    if done.returncode != 0:
        failed(f"{label}'s answer does not keep blackjack.answer.schema.json")
