"""Cards, hands and their totals, and the table drawn as text: what the chat shows.

A card is a short string, its rank then its suit letter: ``AS``, ``10H``, ``KD``, ``7C``. Shown, the suit is its
symbol: ``A♠``, ``10♥``, ``K♦``, ``7♣``.
"""

from __future__ import annotations

import random

RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
SUITS = ("S", "H", "D", "C")
SYMBOLS = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
RED = ("H", "D")

#: Text a screen line holds at most, so the chat never wraps it.
WIDTH = 60
#: Cards drawn side by side before a hand wraps to another row.
PER_ROW = 6


def rank(card: str) -> str:
    return card[:-1]


def suit(card: str) -> str:
    return card[-1]


def shown(card: str) -> str:
    """``10H`` as a person reads it: ``10♥``."""
    return rank(card) + SYMBOLS[suit(card)]


def deck() -> list[str]:
    """One deck, in a fixed order: spades, hearts, diamonds, clubs, ace to king."""
    return [r + s for s in SUITS for r in RANKS]


def shuffled(seed: int, shuffle: int) -> list[str]:
    """A deck shuffled by ``seed``: the same seed and shuffle number give the same order on every Python."""
    cards = deck()
    random.Random(f"blackjack:{seed}:{shuffle}").shuffle(cards)
    return cards


def value(card: str) -> int:
    r = rank(card)
    if r == "A":
        return 1
    if r in ("J", "Q", "K"):
        return 10
    return int(r)


def total(cards: list[str]) -> tuple[int, bool]:
    """A hand's best total, and whether an ace counts eleven in it (a soft total)."""
    hard = sum(value(c) for c in cards)
    if any(rank(c) == "A" for c in cards) and hard + 10 <= 21:
        return hard + 10, True
    return hard, False


def is_blackjack(cards: list[str]) -> bool:
    return len(cards) == 2 and total(cards)[0] == 21


# --- the table as text ----------------------------------------------------------------------------------------------

def card_lines(card: str | None) -> list[str]:
    """One card as five lines, seven columns wide; None is a card face down."""
    if card is None:
        return ["╭─────╮", "│░░░░░│", "│░░░░░│", "│░░░░░│", "╰─────╯"]
    r, symbol = rank(card), SYMBOLS[suit(card)]
    return ["╭─────╮", f"│{r:<5}│", f"│  {symbol}  │", f"│{r:>5}│", "╰─────╯"]


def hand_lines(cards: list[str | None], indent: str = "  ") -> list[str]:
    """A hand's cards side by side, a row of six at most."""
    lines: list[str] = []
    for start in range(0, max(len(cards), 1), PER_ROW):
        row = [card_lines(c) for c in cards[start:start + PER_ROW]]
        if not row:
            break
        for line in range(5):
            lines.append(indent + " ".join(card[line] for card in row))
    return lines
