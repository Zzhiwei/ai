"""Usage: sc.py <shortcut> [flags] [<shortcut> [flags]]... — print mapped instructions in order (map.json).
A token starting with '-' is a flag of the preceding shortcut; a non-shortcut token after a flag is that flag's value
(quote values that equal a shortcut name). Exit 1 on unknown."""
import json, shlex, sys
from pathlib import Path

m = json.loads((Path(__file__).resolve().parent.parent / "map.json").read_text())
steps = []  # [shortcut, [flag tokens]]
for t in sys.argv[1:]:
    if t.startswith("-") and steps:
        steps[-1][1].append(t)
    elif t in m:
        steps.append([t, []])
    elif steps and steps[-1][1]:
        steps[-1][1].append(t)
    else:
        sys.exit(f"unknown: {t}. known: {' '.join(m)}")
if not steps:
    sys.exit(f"none given. known: {' '.join(m)}")
for i, (k, f) in enumerate(steps, 1):
    print(f"{i}. [{k}] {m[k]}" + (f" Flags: {shlex.join(f)}" if f else ""))
