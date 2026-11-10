# BlackjackAgent reference

`blackjack` is a package agent (`granite-agent/1`) written in Python on
[GranitePython](https://github.com/riteshpakala/GranitePython). It plays one table of blackjack a move at a time:
each call is one move, the table's state rides inside the picture it draws, and the answer carries the table as text
for the chat.

## What it takes

| Field | Type | What it is |
| --- | --- | --- |
| `move` | `deal`, `hit`, `stand`, `double`, `show`, `new` | the move; left out, `deal` when no hand is in play, else `show` |
| `bet` | integer | chips to bet on a deal; the last bet when left out, 10 at a new table |
| `seed` | integer | fixes the shuffle, so a game plays again card for card; a fresh shuffle when left out |
| `chips` | integer | chips to sit down with at a new table; 100 when left out |
| `table` | string | where the table's picture is kept, in the folder; `blackjack/table.png` when left out |
| `directory` | string | the folder the table is kept in: filled by the host, never shown to a model |

[`Schema/blackjack.input.schema.json`](../Schema/blackjack.input.schema.json) is the JSON Schema a model is shown,
written from the package's input by `scripts/schemas.py`.

## The rules

One 52-card deck, shuffled again when fewer than 15 cards are left at a deal. Cards are dealt player, dealer, player,
dealer; the dealer's second card is face down. A blackjack (an ace and a ten on the first two cards) pays 3 to 2,
rounded down; the dealer's blackjack wins at once, and two blackjacks push. You may hit, stand, or double on your
first two cards (one more card, twice the stake). A 21 stands by itself; over 21 is a bust and loses at once. The
dealer then turns the hole card and draws to 17, standing on every 17, soft or hard. A higher total wins, a tie
pushes. No split, insurance or surrender.

Chips carry from hand to hand. `chips` in an answer is what you hold, not counting the stake in play; `bet` is what
the next deal takes when no bet is named; `stake` is what the hand in play has at risk.

## What it makes and answers

It makes one kind of thing, a `table`: the table as a PNG, 1200 by 800, its state inside, into `blackjack/` (never a
card the shoe did not deal). Its answer is `granite-answer/1` with the picture in `path`, `paths` and `made`
(`written` the first time, `rewritten` after), and its own keys beside them
([`Schema/blackjack.answer.schema.json`](../Schema/blackjack.answer.schema.json)):

| Key | What it is |
| --- | --- |
| `screen` | the table as text, one line each, at most 60 columns: cards in box-drawing characters, the hole card shaded |
| `state` | `ready`, `playing`, `won`, `lost`, `push`, `blackjack` or `bust` |
| `said` | what just happened, in a sentence or two (also in `notes`) |
| `player`, `dealer` | the cards face up (`10♥`, `A♠`), their best `total`, whether it is `soft`, and how many are `hidden` |
| `chips`, `bet`, `stake`, `net` | what you hold, your bet, what is at risk, what the last hand won or lost |
| `moves` | what may be said next: `hit`, `stand`, `double` while a hand is in play; `deal` and `new` once it ends |
| `hand`, `left` | how many hands have been dealt, and how many cards are left in the shoe |

The dealer's hole card is in no answer, note or screen while the hand is in play.

Refusals, each with a sentence that says the fix:

| Kind | When |
| --- | --- |
| `input` | a move it does not know, or a `bet`, `seed` or `chips` that is not a whole number |
| `call` | a hit, stand or double with no hand in play; a deal while one is; a bet over your chips or under 1; a double after a hit; no chips left; a `table` that is not a picture blackjack drew |
| `host` | a call that offers no folder to keep the table in |

## The table and its state

The picture is drawn with Python's standard library alone (`src/blackjack_agent/table.py` and `png.py`): felt, cards
lettered from a 5 by 7 bitmap font, suits from 9 by 9 bitmaps, written as an RGB PNG with `zlib`. The table's state
rides in the PNG's `iTXt` chunk under `blackjack-table` (`blackjack-table/1`: the seed, the shoe in order, the chips,
both hands), so every file the agent writes is a picture, and a later call needs nothing but the picture to play on.
The state is not hidden from someone who reads the file: it is a game, not a casino.

## How a host runs it

GranitePython's installer bundles `src/` and GranitePython itself into one file, the runner, which a host starts once
per call:

```bash
granite agents add https://github.com/rao-craft/BlackjackAgent.git --shelf <shelf>
echo '{"word":"blackjack","input":{"move":"deal","bet":10}}' \
  | granite run <shelf>/BlackjackAgent/agent - --directory <project>
```

Craft reads such a shelf with `CRAFT_AGENTS_DIR=<shelf>`, and its model calls `blackjack` when the person says
`$blackjack`. The package's `guide` tells the model to copy `screen` exactly into a ```text fence, say what happened
and the moves on offer, and never invent or reveal a card the answer does not show.

## Opening Canvas from an agent

The person asked for an agent that opens Canvas itself. In Craft today (`riteshpakala/Craft` at 1f10b24) it cannot,
and `blackjack` does not pretend to:

- Canvas is a helper pane. A helper opens when the person's own message names it: `Chat+View` calls
  `WindowSelection.noteSent(_:)` with the sent text, which opens every `#word` a linked helper answers to
  (`HelperOps.opened(in:known:)`, then `HelperTabs.opening`). The toolbar and View ▸ Toggle Helper open it too.
- Nothing an agent says is read for `#`. `PackageTool.run` reads an answer's `path` and `paths`
  (`PackageTool.paths(in:under:)`) to note what it wrote, and the model's reply is its own Markdown. A `#canvas` in a
  guide, an answer or a note opens nothing.
- So the person types `#canvas` once (`$blackjack deal #canvas`), and Canvas shows `blackjack/table.png` from then on,
  since it shows the pictures a session writes and each move rewrites it.

The change that would let an agent open a helper, kept small and in Craft's layer (`craft-agent/1`), not in
`granite-agent/1`, since a pane is Craft's and other hosts have none:

1. **An answer key.** `craft-agent/1` adds `open`: the helper words an answer asks to be shown, for example
   `"open": ["canvas"]`. It is a request, never a command, and names helpers, not files: the files are already in
   `paths`. `craft-agent-output.schema.json` gains `"open": {"type": "array", "items": {"type": "string"}}`.
2. **PackageTool reads it.** Beside `paths(in:under:)`, `PackageTool.run` reads `open` from the output and returns it
   on its `ToolOutput`, as it returns the files written.
3. **The window opens it.** `WindowSelection` gains `noteAnswered(opening words: [String])`, the twin of
   `noteSent(_:)`: it keeps only words `HelperRoster.linked` knows and calls `set(tabs.opening(…))`. It opens, never
   closes or reorders what the person arranged, and a helper the person closed during this turn stays closed.
4. **The person decides.** A setting, *Agents may open helpers* (on by default, off per project), gates it, and the
   turn's activity line says "canvas opened by blackjack", as `MentionsAgent` already says "canvas opened" for a
   mention.

With that, `blackjack` would answer `"open": ["canvas"]` on a deal, and its guide would drop "Canvas (#canvas)". It is
written up, not made: Craft was not changed or run for this agent.

## Building and testing

```bash
GRANITE_PYTHON=<GranitePython clone> scripts/check.sh            # in Apple's container
GRANITE_PYTHON=<GranitePython clone> scripts/check.sh --native   # on this machine
GRANITE_PYTHON=<GranitePython clone> scripts/play.sh [--container] [--seed 3]
```

`check.sh` runs the suite (`tests/`: the rules, the screen, the picture and its state, the package as a host calls it,
every refusal), then GranitePython's `containers/check.sh` on this repository's last commit (installed, described,
and the five calls in `Schema/examples/` made in name order in one folder, so they play seed 3's hand through), then
what only blackjack answers (`scripts/answers.py`: the cards seed 3 deals, the hole card hidden, every screen line
inside 60 columns, the picture's size and the state it carries, each answer against blackjack's own schema).

`play.sh` installs the runner and plays in the terminal through `granite run`, moves from the keyboard or from stdin;
with `--container`, every call is made in Apple's container. `scripts/schemas.py` writes the input schema, and
`scripts/icon.py` draws the store icon.

## Licences

The source is MIT ([LICENSE](../LICENSE)). An installed runner bundles GranitePython (GPL-3.0), so it is a GPL-3.0
combined work.
