#!/bin/sh
# Play blackjack in a terminal, without Craft (scripts/play.py says how).
#   GRANITE_PYTHON=<GranitePython clone> scripts/play.sh [--container] [--seed <n>] [--folder <dir>]
set -eu
exec "${PYTHON:-python3}" "$(dirname "$0")/play.py" "$@"
