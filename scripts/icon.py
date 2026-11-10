#!/usr/bin/env python3
"""Draws Assets/icon.png, the store's icon: an ace of spades and a king of hearts on the felt, 1024x1024, with the
table's own canvas and bitmaps.

  GRANITE_PYTHON=<GranitePython clone> scripts/icon.py
"""

import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(root, "src"), os.path.join(os.environ.get("GRANITE_PYTHON", ""), "src")]

from blackjack_agent.table import (CARD, EDGE, FELT, FELT_LINE, INK_BLACK, INK_RED, SUIT_BITMAPS, WOOD,  # noqa: E402
                                   Canvas, text_width)

SIZE = 1024
W, H = 420, 588


def card(canvas: Canvas, x: int, y: int, rank: str, suit: str) -> None:
    ink = INK_RED if suit in ("H", "D") else INK_BLACK
    canvas.rounded(x - 6, y - 6, W + 12, H + 12, 44, EDGE)
    canvas.rounded(x, y, W, H, 40, CARD)
    canvas.text(rank, x + 36, y + 36, 12, ink)
    canvas.bitmap(SUIT_BITMAPS[suit], x + 36, y + 136, 6, ink)
    canvas.bitmap(SUIT_BITMAPS[suit], x + (W - 9 * 24) // 2, y + (H - 9 * 24) // 2 + 30, 24, ink)
    canvas.text(rank, x + W - 36 - text_width(rank, 12), y + H - 36 - 84, 12, ink)


canvas = Canvas(SIZE, SIZE, WOOD)
canvas.rounded(40, 40, SIZE - 80, SIZE - 80, 160, FELT)
canvas.rounded(84, 84, SIZE - 168, SIZE - 168, 124, FELT_LINE)
canvas.rounded(92, 92, SIZE - 184, SIZE - 184, 116, FELT)
card(canvas, 120, 150, "A", "S")
card(canvas, 484, 286, "K", "H")
path = os.path.join(root, "Assets", "icon.png")
with open(path, "wb") as out:
    out.write(canvas.png())
print(f"wrote {path}")
