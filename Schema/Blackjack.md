# craft-agent/1 · blackjack

Deals blackjack a move at a time: the table as text for the chat, and as a picture for Canvas, the game's state
inside the picture.

blackjack's copy of Craft's agent standard (`craft-agent/1`, Craft's `Schema/Agent.md`), in the layout
`craft agents schema` writes from an installed record. This one was written by hand from the package's entry (Craft
was not run for it); `craft agents schema blackjack` would write everything above **Changes** again. Changes is
blackjack's own log.

| File | What it holds |
| --- | --- |
| [`blackjack.input.schema.json`](blackjack.input.schema.json) | What it takes, as JSON Schema |
| [`blackjack.answer.schema.json`](blackjack.answer.schema.json) | What it answers: `granite-answer/1` with its own keys |

## What it takes

| Field | Required | What it is |
| --- | --- | --- |
| `move` | no | deal, hit, stand, double, show, or new; left out, deal when no hand is in play, else show |
| `bet` | no | chips to bet on a deal; the last bet when left out, 10 at a new table |
| `seed` | no | a number that fixes the shuffle, so a game plays again card for card; a fresh shuffle when left out |
| `chips` | no | chips to sit down with at a new table; 100 when left out |
| `table` | no | where the table's picture is kept, in the folder; blackjack/table.png when left out |

`directory` is filled by Craft with the project folder. The person's request and the host's model are offered beside
the call, never in it; blackjack asks no model.

## What it makes

| Kind | What | Into | Never |
| --- | --- | --- | --- |
| `table` | the blackjack table as a PNG, the game's state inside it | `blackjack/` | a card the shoe did not deal |

## What it answers

A `granite-answer/1` answer (Granite's `Schema/GraniteAgent.md` §4.2): `paths`, `made` against `expected` by kind and
name, and its own keys beside them: `screen` (the table as text, to copy into the chat), `state`, `said`, `player`,
`dealer`, `chips`, `bet`, `stake`, `net`, `moves`, `hand` and `left`.

## How it refuses

`input` for a move it does not know or a number that is not one; `call` for a move the table cannot make now, each
with the move to make instead; `host` for a call that offers no folder.

## Changes

### 2026-11-10: the first version

One table of blackjack a move at a time on GranitePython 0.1.0: deal, hit, stand, double, show and new; the table
answered as text and drawn as a PNG carrying its state.
