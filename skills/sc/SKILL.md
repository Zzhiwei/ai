---
name: sc
description: Expands shortcut codes into fixed instructions and runs them in order. Use when the user types `/sc <shortcut> [<shortcut>...]`, e.g. `/sc gcp vb`.
---

Run `python3 -I ~/.claude/skills/sc/scripts/sc.py <args>`. Execute the printed steps in order, stop at first failure. On script error, report it and stop. Do nothing else.

Shortcuts live in `map.json`.
