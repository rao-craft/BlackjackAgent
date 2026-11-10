#!/bin/sh
# BlackjackAgent's check: its own suite, then GranitePython's check on this repository (installed by GranitePython's
# installer and called over the wire as a host calls it, every answer held to granite-agent/1 and Craft's
# craft-agent/1), then what only blackjack answers.
#
#   GRANITE_PYTHON=<GranitePython clone> scripts/check.sh [--native]
#
# In Apple's container (Linux, arm64) by default; with --native on this machine. The check installs this repository's
# last commit.
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
: "${GRANITE_PYTHON:?set GRANITE_PYTHON to a GranitePython clone: its containers/check.sh is the check}"
granite=$(cd "$GRANITE_PYTHON" && pwd)
python=${PYTHON:-python3}
mode=container
[ "${1:-}" = --native ] && mode=native

echo "== the suite"
cd "$root"
PYTHONPATH="$root/src:$granite/src" "$python" -W error -m compileall -q src tests scripts
PYTHONPATH="$root/src:$granite/src" "$python" -W error -m unittest discover -s tests -t . 2>&1 | tail -3

out=$(mktemp -d "${TMPDIR:-/tmp}/blackjack-check.XXXXXX")
if [ $mode = native ]; then
  "$granite/containers/check.sh" "$root" --granite "$granite" --out "$out" --native
else
  "$granite/containers/check.sh" "$root" --granite "$granite" --out "$out"
fi

echo
echo "== what only blackjack answers"
"$python" "$root/scripts/answers.py" "$out" "$granite"
echo
echo "blackjack: check passed ($mode); kept in $out"
