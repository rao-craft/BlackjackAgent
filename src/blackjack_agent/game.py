"""Blackjack at one table: the shoe, the chips, the hand in play, and each move.

The rules: one deck, shuffled again when fewer than 15 cards are left at a deal; the dealer stands on every 17 and
draws to 16; a blackjack pays 3 to 2 (rounded down); a double takes one card on the first two; a player's 21 stands by
itself. No split, insurance or surrender.

PIN: A CARD IS DEALT, NEVER MADE UP. Every card comes off the shoe in order, and the shoe is a seed's shuffle, so a
seed and a list of moves play the same hand again card for card.

PIN: THE HOLE CARD IS HIDDEN WHILE THE HAND IS IN PLAY. What the table says (``view``) leaves the dealer's second card
out until the hand ends.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

from blackjack_agent.cards import is_blackjack, shown, shuffled, total

FORMAT = "blackjack-table/1"
CHIPS = 100
BET = 10
LOW = 15

MOVES = ("deal", "hit", "stand", "double", "show", "new")
#: How a hand stands: no hand yet, in play, or how it ended.
STATES = ("ready", "playing", "won", "lost", "push", "blackjack", "bust")


class Refused(Exception):
    """A move the table cannot make now, and the fix, said to the person."""


@dataclass
class Table:
    seed: int
    shuffles: int = 0
    shoe: list[str] = field(default_factory=list)
    chips: int = CHIPS
    bet: int = BET
    stake: int = 0
    player: list[str] = field(default_factory=list)
    dealer: list[str] = field(default_factory=list)
    state: str = "ready"
    doubled: bool = False
    hands: int = 0
    net: int = 0
    said: str = ""

    # --- reading and writing ----------------------------------------------------------------------------------------

    @classmethod
    def new(cls, seed: int | None = None, chips: int | None = None) -> "Table":
        seed = seed if seed is not None else secrets.randbelow(2**32)
        table = cls(seed=seed, chips=chips if chips is not None else CHIPS)
        table.shoe = shuffled(seed, 0)
        table.said = f"You sit down with {table.chips} chips. Say deal, with a bet if you like."
        return table

    def json(self) -> dict:
        return {"format": FORMAT, "seed": self.seed, "shuffles": self.shuffles, "shoe": self.shoe, "chips": self.chips,
                "bet": self.bet, "stake": self.stake, "player": self.player, "dealer": self.dealer, "state": self.state,
                "doubled": self.doubled, "hands": self.hands, "net": self.net, "said": self.said}

    @classmethod
    def read(cls, value: Any) -> "Table":
        """A table from what its picture carries; raises ``ValueError`` when it is not one."""
        if not isinstance(value, dict) or value.get("format") != FORMAT:
            raise ValueError(f"it carries no {FORMAT} table")
        try:
            table = cls(seed=int(value["seed"]), shuffles=int(value["shuffles"]), shoe=list(value["shoe"]),
                        chips=int(value["chips"]), bet=int(value["bet"]), stake=int(value.get("stake", 0)), player=list(value["player"]),
                        dealer=list(value["dealer"]), state=str(value["state"]), doubled=bool(value["doubled"]),
                        hands=int(value["hands"]), net=int(value.get("net", 0)), said=str(value.get("said", "")))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"its {FORMAT} table does not read: {error}") from None
        if table.state not in STATES:
            raise ValueError(f"its table is in no state blackjack knows: {table.state}")
        return table

    # --- what the table says ----------------------------------------------------------------------------------------

    @property
    def in_play(self) -> bool:
        return self.state == "playing"

    def moves(self) -> list[str]:
        """What may be said next."""
        if self.in_play:
            can_double = len(self.player) == 2 and not self.doubled and self.chips >= self.stake
            return ["hit", "stand"] + (["double"] if can_double else [])
        return (["deal"] if self.chips > 0 else []) + ["new"]

    def dealer_shown(self) -> list[str | None]:
        """The dealer's cards as the person sees them: the hole card face down while the hand is in play."""
        if self.in_play and len(self.dealer) == 2:
            return [self.dealer[0], None]
        return list(self.dealer)

    def view(self) -> dict:
        player_total, player_soft = total(self.player)
        visible = [c for c in self.dealer_shown() if c is not None]
        dealer_total, dealer_soft = total(visible)
        dealer = {"cards": [shown(c) for c in visible], "total": dealer_total, "soft": dealer_soft,
                  "hidden": len(self.dealer) - len(visible)}
        return {"state": self.state, "said": self.said, "chips": self.chips, "bet": self.bet, "stake": self.stake, "hand": self.hands,
                "net": self.net, "left": len(self.shoe), "moves": self.moves(),
                "player": {"cards": [shown(c) for c in self.player], "total": player_total, "soft": player_soft},
                "dealer": dealer}

    # --- the moves --------------------------------------------------------------------------------------------------

    def draw(self) -> str:
        return self.shoe.pop(0)

    def deal(self, bet: int | None = None, seed: int | None = None) -> list[str]:
        """Starts a hand; what happened, a note each."""
        if self.in_play:
            raise Refused("a hand is in play: hit, stand or double before you deal again")
        if self.chips <= 0:
            raise Refused(f"you have no chips left: say new to sit down again with {CHIPS}")
        bet = self.bet if bet is None else bet
        if bet < 1:
            raise Refused("a bet is at least 1 chip")
        if bet > self.chips:
            raise Refused(f"you bet {bet} and hold {self.chips} chips: bet {self.chips} or less")
        notes = []
        if seed is not None:
            self.seed, self.shuffles, self.shoe = seed, 0, shuffled(seed, 0)
            notes.append(f"the dealer shuffles with seed {seed}")
        elif len(self.shoe) < LOW:
            self.shuffles += 1
            self.shoe = shuffled(self.seed, self.shuffles)
            notes.append("the dealer shuffles a fresh deck")
        self.bet, self.stake, self.chips, self.doubled, self.net = bet, bet, self.chips - bet, False, 0
        self.player, self.dealer = [], []
        for _ in range(2):
            self.player.append(self.draw())
            self.dealer.append(self.draw())
        self.hands += 1
        self.state = "playing"
        player, dealer = is_blackjack(self.player), is_blackjack(self.dealer)
        if player or dealer:
            if player and dealer:
                self._settle("push", f"You both have blackjack: a push, and your {bet} comes back.")
            elif player:
                self._settle("blackjack", f"Blackjack! You win {bet * 3 // 2}.")
            else:
                self._settle("lost", f"The dealer turns {shown(self.dealer[1])} for blackjack: you lose {bet}.")
            return notes
        self.said = (f"You bet {bet}. You have {self._said_total(self.player)}; the dealer shows "
                     f"{shown(self.dealer[0])}.")
        return notes

    def hit(self) -> list[str]:
        self._in_play("hit")
        card = self.draw()
        self.player.append(card)
        player_total, _ = total(self.player)
        if player_total > 21:
            self._settle("bust", f"You draw {shown(card)}: bust with {player_total}, and you lose {self.stake}.")
            return []
        if player_total == 21:
            notes = self._dealer_plays()
            self.said = f"You draw {shown(card)} for 21 and stand. " + self.said
            return notes
        self.said = f"You draw {shown(card)}. You have {self._said_total(self.player)}."
        return []

    def stand(self) -> list[str]:
        self._in_play("stand")
        player_total, _ = total(self.player)
        notes = self._dealer_plays()
        self.said = f"You stand on {player_total}. " + self.said
        return notes

    def double(self) -> list[str]:
        self._in_play("double")
        if len(self.player) != 2 or self.doubled:
            raise Refused("you double on your first two cards only: hit or stand")
        if self.chips < self.stake:
            raise Refused(f"doubling takes another {self.stake} and you hold {self.chips}: hit or stand")
        self.chips -= self.stake
        self.stake *= 2
        self.doubled = True
        card = self.draw()
        self.player.append(card)
        player_total, _ = total(self.player)
        if player_total > 21:
            self._settle("bust", f"You double and draw {shown(card)}: bust with {player_total}, and you lose "
                                 f"{self.stake}.")
            return []
        notes = self._dealer_plays()
        self.said = f"You double to {self.stake} and draw {shown(card)} for {player_total}. " + self.said
        return notes

    def _in_play(self, move: str) -> None:
        if not self.in_play:
            raise Refused(f"no hand is in play to {move}: say deal to start one")

    def _dealer_plays(self) -> list[str]:
        """The dealer turns the hole card and draws to 17, then the hand is settled."""
        notes = [f"the dealer turns {shown(self.dealer[1])}"]
        while total(self.dealer)[0] < 17:
            card = self.draw()
            self.dealer.append(card)
            notes.append(f"the dealer draws {shown(card)}")
        dealer_total, _ = total(self.dealer)
        player_total, _ = total(self.player)
        if dealer_total > 21:
            self._settle("won", f"The dealer busts with {dealer_total}: you win {self.stake}.")
        elif player_total > dealer_total:
            self._settle("won", f"The dealer stands on {dealer_total}: you win {self.stake}.")
        elif player_total < dealer_total:
            self._settle("lost", f"The dealer has {dealer_total}: you lose {self.stake}.")
        else:
            self._settle("push", f"The dealer has {dealer_total} too: a push, and your {self.stake} comes back.")
        return notes

    def _settle(self, state: str, said: str) -> None:
        stake = self.stake
        returned = {"won": 2 * stake, "blackjack": stake + stake * 3 // 2, "push": stake}.get(state, 0)
        self.chips += returned
        self.net = returned - stake
        self.state, self.said = state, said

    @staticmethod
    def _said_total(cards: list[str]) -> str:
        value, soft = total(cards)
        return f"{value}, soft" if soft else str(value)
