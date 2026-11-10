"""Usage: sc.py <shortcut>... — print mapped instructions in order (map.json). Exit 1 on unknown."""
import json, sys
from pathlib import Path

m = json.loads((Path(__file__).resolve().parent.parent / "map.json").read_text())
args = sys.argv[1:]
bad = [a for a in args if a not in m]
if not args or bad:
    sys.exit(f"unknown: {' '.join(bad) or '(none given)'}. known: {' '.join(m)}")
for i, a in enumerate(args, 1):
    print(f"{i}. [{a}] {m[a]}")
