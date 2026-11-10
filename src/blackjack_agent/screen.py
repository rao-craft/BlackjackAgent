"""The table as text, line by line: what the host's model copies into the chat, inside a ``text`` fence.

Every line is at most ``WIDTH`` columns, every character one column wide in a monospace font, so the cards line up
wherever the chat is shown.
"""

from __future__ import annotations

import textwrap

from blackjack_agent.cards import WIDTH, hand_lines, is_blackjack, total
from blackjack_agent.game import Table


def _header(table: Table) -> str:
    stake = f" · stake {table.stake}" if table.in_play and table.stake != table.bet else ""
    right = f"hand {table.hands} · chips {table.chips} · bet {table.bet}{stake}"
    left = "  BLACKJACK"
    return left + " " * max(1, WIDTH - len(left) - len(right)) + right


def _total(cards: list[str]) -> str:
    value, soft = total(cards)
    if is_blackjack(cards):
        return "blackjack"
    return f"{value}, soft" if soft else str(value)


def screen(table: Table) -> list[str]:
    """The table's lines: who holds what, what just happened, and what may be said next."""
    lines = [_header(table), ""]
    if table.state == "ready" or not table.player:
        lines.append("  The table is ready. Say deal, with a bet if you like.")
    else:
        dealer = table.dealer_shown()
        visible = [c for c in dealer if c is not None]
        if None in dealer:
            lines.append(f"  Dealer shows {_total(visible)}")
        elif total(visible)[0] > 21:
            lines.append(f"  Dealer busts with {total(visible)[0]}")
        else:
            lines.append(f"  Dealer has {_total(visible)}")
        lines += hand_lines(dealer)
        lines.append("")
        if total(table.player)[0] > 21:
            lines.append(f"  You bust with {total(table.player)[0]}")
        else:
            lines.append(f"  You have {_total(table.player)}")
        lines += hand_lines(table.player)
    lines.append("")
    for line in textwrap.wrap(table.said, WIDTH - 4) or [""]:
        lines.append(f"  {line}")
    lines.append("  " + " · ".join(table.moves()))
    return lines
