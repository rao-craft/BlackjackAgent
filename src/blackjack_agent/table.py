"""The table drawn as a picture: felt, the dealer's cards and yours, what happened, and what may be said next. Pixels
in a byte buffer, letters from a 5x7 bitmap font, suits from 9x9 bitmaps, each scaled up: the standard library only.
"""

from __future__ import annotations

from blackjack_agent import png
from blackjack_agent.cards import RED, SYMBOLS, is_blackjack, rank, suit, total
from blackjack_agent.game import Table

WIDTH, HEIGHT = 1200, 800
CARD_W, CARD_H, CARD_GAP = 128, 180, 20

WOOD = (92, 56, 30)
FELT = (22, 108, 58)
FELT_LINE = (40, 132, 78)
CREAM = (238, 228, 200)
GOLD = (240, 198, 84)
CARD = (250, 249, 244)
EDGE = (160, 160, 150)
INK_RED = (196, 32, 46)
INK_BLACK = (28, 28, 34)
BACK = (34, 66, 150)
BACK_LINE = (60, 98, 186)

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": (".....",) * 7,
    "·": (".....", ".....", ".....", "..#..", ".....", ".....", "....."),
    ":": (".....", "..#..", ".....", ".....", ".....", "..#..", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..#..", ".#..."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
}

SUIT_BITMAPS = {
    "S": ("....#....", "...###...", "..#####..", ".#######.", "#########", "#########", ".##.#.##.", "....#....",
          "...###..."),
    "H": (".##...##.", "####.####", "#########", "#########", ".#######.", "..#####..", "...###...", "....#....",
          "........."),
    "D": ("....#....", "...###...", "..#####..", ".#######.", "#########", ".#######.", "..#####..", "...###...",
          "....#...."),
    "C": ("...###...", "...###...", ".#.###.#.", "#########", "#########", ".#..#..#.", "....#....", "...###...",
          "........."),
}


class Canvas:
    """An RGB picture in a byte buffer, drawn with clipped rectangles."""

    def __init__(self, width: int, height: int, color: tuple[int, int, int]) -> None:
        self.width, self.height = width, height
        self.pixels = bytearray(bytes(color) * (width * height))

    def rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int]) -> None:
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.width, x + w), min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            at = (yy * self.width + x0) * 3
            self.pixels[at:at + len(row)] = row

    def rounded(self, x: int, y: int, w: int, h: int, r: int, color: tuple[int, int, int]) -> None:
        """A rectangle with corners of radius ``r``."""
        for row in range(h):
            dy = r - row - 0.5 if row < r else (row - (h - r) + 0.5 if row >= h - r else 0)
            inset = int(round(r - (r * r - dy * dy) ** 0.5)) if dy > 0 else 0
            self.rect(x + inset, y + row, w - 2 * inset, 1, color)

    def bitmap(self, rows: tuple[str, ...], x: int, y: int, scale: int, color: tuple[int, int, int]) -> None:
        for j, line in enumerate(rows):
            for i, cell in enumerate(line):
                if cell == "#":
                    self.rect(x + i * scale, y + j * scale, scale, scale, color)

    def text(self, said: str, x: int, y: int, scale: int, color: tuple[int, int, int]) -> int:
        """``said`` in capitals from ``x``; the x it ends at."""
        for c in said.upper():
            self.bitmap(FONT.get(c, FONT["?"]), x, y, scale, color)
            x += 6 * scale
        return x

    def png(self, text: dict[str, str] | None = None) -> bytes:
        return png.write(self.width, self.height, self.pixels, text)


def text_width(said: str, scale: int) -> int:
    return max(0, len(said) * 6 * scale - scale)


def draw_card(canvas: Canvas, card: str | None, x: int, y: int) -> None:
    canvas.rounded(x - 2, y - 2, CARD_W + 4, CARD_H + 4, 14, EDGE)
    if card is None:
        canvas.rounded(x, y, CARD_W, CARD_H, 12, CARD)
        canvas.rounded(x + 8, y + 8, CARD_W - 16, CARD_H - 16, 8, BACK)
        for stripe in range(0, CARD_W + CARD_H, 16):
            for t in range(CARD_H - 24):
                sx = x + 12 + stripe - t
                if x + 12 <= sx < x + CARD_W - 12:
                    canvas.rect(sx, y + 12 + t, 3, 1, BACK_LINE)
        return
    canvas.rounded(x, y, CARD_W, CARD_H, 12, CARD)
    ink = INK_RED if suit(card) in RED else INK_BLACK
    r = rank(card)
    canvas.text(r, x + 12, y + 12, 4, ink)
    canvas.bitmap(SUIT_BITMAPS[suit(card)], x + 12, y + 48, 2, ink)
    canvas.bitmap(SUIT_BITMAPS[suit(card)], x + (CARD_W - 63) // 2, y + (CARD_H - 63) // 2 + 8, 7, ink)
    canvas.text(r, x + CARD_W - 12 - text_width(r, 4), y + CARD_H - 12 - 28, 4, ink)


def draw_hand(canvas: Canvas, cards: list[str | None], y: int) -> None:
    count = len(cards)
    room = WIDTH - 120 - CARD_W
    step = CARD_W + CARD_GAP if count <= 1 else min(CARD_W + CARD_GAP, room // (count - 1))
    for index, card in enumerate(cards):
        draw_card(canvas, card, 60 + index * step, y)


def _said_total(cards: list[str]) -> str:
    if is_blackjack(cards):
        return "blackjack"
    value, soft = total(cards)
    return f"{value} soft" if soft else str(value)


def _label(cards: list[str], hidden: bool) -> str:
    if hidden:
        return f"shows {_said_total(cards)}"
    value, _ = total(cards)
    return f"busts with {value}" if value > 21 else f"has {_said_total(cards)}"


BANNERS = {
    "won": "you win {net}", "blackjack": "blackjack! you win {net}", "lost": "you lose {stake}",
    "bust": "bust: you lose {stake}", "push": "push: your {stake} comes back",
}


def draw(table: Table) -> Canvas:
    """The table as it stands."""
    canvas = Canvas(WIDTH, HEIGHT, WOOD)
    canvas.rounded(20, 20, WIDTH - 40, HEIGHT - 40, 44, FELT)
    canvas.rounded(36, 96, WIDTH - 72, 2, 1, FELT_LINE)
    canvas.text("blackjack", 60, 44, 5, CREAM)
    info = f"hand {table.hands} · chips {table.chips} · bet {table.bet}"
    canvas.text(info, WIDTH - 60 - text_width(info, 3), 56, 3, CREAM)
    if not table.player:
        canvas.text("the table is ready", 60, 330, 6, CREAM)
        canvas.text("say deal, with a bet if you like", 60, 410, 3, CREAM)
    else:
        dealer = table.dealer_shown()
        visible = [c for c in dealer if c is not None]
        canvas.text(f"dealer {_label(visible, None in dealer)}", 60, 122, 3, CREAM)
        draw_hand(canvas, dealer, 152)
        canvas.text(f"you {_label(table.player, False).replace('has', 'have').replace('busts', 'bust')}", 60, 380,
                    3, CREAM)
        draw_hand(canvas, table.player, 410)
    banner = BANNERS.get(table.state, "").format(net=table.net, stake=table.stake)
    moves = " · ".join(table.moves())
    if banner:
        canvas.text(banner, 60, 640, 5, GOLD)
        canvas.text(moves, 60, 708, 3, CREAM)
    else:
        canvas.text(moves, 60, 660, 4, GOLD)
    return canvas


KEYWORD = "blackjack-table"


def picture(table: Table, state: str) -> bytes:
    """The table's PNG, carrying ``state`` (the table's JSON) to play on."""
    return draw(table).png({KEYWORD: state})


def carried(data: bytes) -> str | None:
    """The state a table's PNG carries, or None."""
    return png.text(data, KEYWORD)
