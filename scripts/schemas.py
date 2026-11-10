#!/usr/bin/env python3
"""Writes Schema/blackjack.input.schema.json from the package's input, as a model is shown it (no `directory`).

  GRANITE_PYTHON=<GranitePython clone> scripts/schemas.py
"""

import json
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
granite = os.environ.get("GRANITE_PYTHON")
if not granite:
    sys.exit("set GRANITE_PYTHON to a GranitePython clone")
sys.path[:0] = [os.path.join(root, "src"), os.path.join(granite, "src")]

import granite as g  # noqa: E402

from blackjack_agent import roster  # noqa: E402

package = roster.find("blackjack")
shape = g.schema.of(package.Input).json_schema(hide_directory=True)
document = {
    "$id": "https://github.com/rao-craft/BlackjackAgent/blob/main/Schema/blackjack.input.schema.json",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "What blackjack takes",
    "description": package.summary,
    **shape,
}
path = os.path.join(root, "Schema", "blackjack.input.schema.json")
with open(path, "w") as out:
    json.dump(document, out, indent=2, sort_keys=True, ensure_ascii=False)
    out.write("\n")
print(f"wrote {path}")
