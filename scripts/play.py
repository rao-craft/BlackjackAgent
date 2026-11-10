#!/usr/bin/env python3
"""Play blackjack in a terminal, without Craft: the runner installed by GranitePython's installer, each move a call
through `granite run`, the table's `screen` printed. Moves come from the keyboard, or from stdin when it is not one
(each echoed, so a transcript reads as a game).

  GRANITE_PYTHON=<GranitePython clone> scripts/play.sh [--container] [--seed <n>] [--folder <dir>]

  deal [bet] · hit · stand · double · show · new [chips] · quit

--container installs and calls the runner in Apple's container (GranitePython's check image), the folder mounted at
/scratch; the picture of the table is written to <folder>/table/blackjack/table.png either way.
"""

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv: list[str]) -> int:
    granite = os.environ.get("GRANITE_PYTHON")
    if not granite:
        print("set GRANITE_PYTHON to a GranitePython clone", file=sys.stderr)
        return 2
    granite = os.path.abspath(granite)
    container_mode, seed, folder = False, None, None
    i = 0
    while i < len(argv):
        if argv[i] == "--container":
            container_mode = True
        elif argv[i] == "--seed" and i + 1 < len(argv):
            seed, i = int(argv[i + 1]), i + 1
        elif argv[i] == "--folder" and i + 1 < len(argv):
            folder, i = argv[i + 1], i + 1
        else:
            print(__doc__, file=sys.stderr)
            return 2
        i += 1
    folder = os.path.realpath(folder or tempfile.mkdtemp(prefix="blackjack-play."))
    os.makedirs(os.path.join(folder, "table"), exist_ok=True)
    shelf = os.path.join(folder, "shelf")

    if container_mode:
        container = shutil.which("container") or next(iter(sorted(glob.glob(os.path.expanduser(
            "~/.local/apple-container/*/bin/container")), reverse=True)), None)
        if not container:
            print("Apple's container is not installed", file=sys.stderr)
            return 2
        if subprocess.run([container, "system", "status"], capture_output=True).returncode != 0:
            subprocess.run([container, "system", "start"], check=True)
        commit = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=granite, capture_output=True,
                                text=True).stdout.strip() or "unknown"
        subprocess.run([container, "build", "--tag", "granitepython:check", "--build-arg", f"GRANITE_COMMIT={commit}",
                        "--file", os.path.join(granite, "containers", "Dockerfile"), granite], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        agent = os.path.join(folder, "agent")
        shutil.rmtree(agent, ignore_errors=True)
        shutil.copytree(root, agent, ignore=shutil.ignore_patterns(".git", "__pycache__", "build"))

        def granite_cmd(*arguments: str, stdin: str | None = None) -> subprocess.CompletedProcess:
            flags = ["--interactive"] if stdin is not None else []
            return subprocess.run([container, "run", "--rm", *flags, "--volume", f"{folder}:/scratch",
                                   "granitepython:check", *arguments], input=stdin, capture_output=True, text=True)

        def inside(path: str) -> str:
            return "/scratch" + path[len(folder):]

        source = inside(agent)
        where = "Apple's container (Linux arm64)"
    else:
        cli = os.path.join(folder, "granite")
        subprocess.run([sys.executable, os.path.join(granite, "scripts", "build-cli.py"), "--out", cli, "--python",
                        sys.executable], check=True, stdout=subprocess.DEVNULL)

        def granite_cmd(*arguments: str, stdin: str | None = None) -> subprocess.CompletedProcess:
            return subprocess.run([cli, *arguments], input=stdin, capture_output=True, text=True)

        def inside(path: str) -> str:
            return path

        source = root
        where = "this machine"

    installed = granite_cmd("agents", "add", source, "--shelf", inside(shelf))
    if installed.returncode != 0:
        print(installed.stderr, file=sys.stderr)
        return 1
    record = json.loads(installed.stdout)
    runner = inside(os.path.join(shelf, record["name"], "agent"))
    print(f"blackjack, installed by GranitePython ({record['granite']}) and played on {where}")
    print("say: deal [bet] · hit · stand · double · show · new [chips] · quit")

    interactive = sys.stdin.isatty()
    first = True
    while True:
        if interactive:
            try:
                said = input("\n> ").strip()
            except EOFError:
                break
        else:
            said = sys.stdin.readline()
            if not said:
                break
            said = said.strip()
            print(f"\n> {said}")
        if not said:
            continue
        words = said.split()
        if words[0] in ("quit", "exit"):
            break
        call: dict = {"move": words[0]}
        if len(words) > 1 and words[1].isdigit():
            call["bet" if words[0] == "deal" else "chips"] = int(words[1])
        if first and seed is not None and words[0] in ("deal", "new"):
            call["seed"] = seed
        first = False
        perform = json.dumps({"word": "blackjack", "input": call})
        done = granite_cmd("run", runner, "-", "--directory", inside(os.path.join(folder, "table")), stdin=perform)
        try:
            line = json.loads(done.stdout)
        except json.JSONDecodeError:
            print(done.stderr.strip() or done.stdout.strip(), file=sys.stderr)
            continue
        if "output" in line:
            print("\n".join(line["output"]["screen"]))
        else:
            print(f"  {line.get('failed', 'the call failed')}")
    print(f"\nthe table's picture: {os.path.join(folder, 'table', 'blackjack', 'table.png')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
