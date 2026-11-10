---
name: sc
description: Expands shortcut codes into fixed instructions and runs them in order. Use when the user types `/sc <shortcut> [flags] [<shortcut> [flags]...]`, e.g. `/sc gc -m "fix typo" gp vb`.
---

Run `python3 -I ~/.claude/skills/sc/scripts/sc.py <args>` (quote args as given). Execute the printed steps in order, stop at first failure. Interpret each step's `Flags:` yourself and apply them to that step only. On script error, report it and stop. Do nothing else.

Shortcuts live in `map.json`.
