---
name: chapter-study-notes
description: Turns a tech-book chapter (markdown file, e.g. from Designing Data-Intensive Applications) into a comprehensive nested-bullet study note that keeps the original headings, plus a one-page "trunks" overview (chapter gist and a short summary per heading), and a concept-focused quiz (grouped by question type) and answer key. Use when the user gives a chapter .md and asks for study notes, a summary, a quiz, or an exam for a book chapter.
---

# Chapter Study Notes

Input: path to one chapter `.md`. Outputs next to the input. Source `chNN title.md` gives `chNN notes.md`, `chNN trunks.md`, `chNN quiz.md`, `chNN answers.md` (final) and `chNN checklist.md`, `chNN parts/` (working); any other source `name.md` gives `name-notes.md`, `name-trunks.md`, `name-quiz.md`, `name-answers.md`, `name-checklist.md`, `name-parts/`. Below, `<notes>`, `<trunks>`, `<quiz>`, `<answers>`, `<checklist>`, `<parts>` are those paths:

- `<notes>` — study note (final)
- `<trunks>` — high-level overview: chapter gist plus a short summary per heading, to hang detail on or decide what to read (final)
- `<quiz>` — questions only (final)
- `<answers>` — answer key (final)
- `<checklist>` — atomic key points extracted from source (working file; moved to Trash at the end, with `<parts>` for long files)

Formats and quiz spec: [REFERENCE.md](REFERENCE.md). Read it before step 2.

Scripts (deterministic work; never do these by hand): `python3 -I ~/.claude/skills/chapter-study-notes/scripts/chapter_tools.py <outline|plan|check|merge|clean> <src> ...` (usage in the script's docstring; called `TOOLS` below).

## Workflow

1. **Read & checklist.** Read the whole source. Run `TOOLS outline <src>` for the heading list (verbatim text, order, level); do not retype headings. Under each, write the checklist: one line per atomic point (definition, claim, number, trade-off, example, algorithm step, caveat, cited system), ID'd `H3.2-07`-style. Also write the `## Core concepts` section at the top of the checklist (C-IDs plus interactions; format and selection test in REFERENCE.md). If the file is over ~700 lines, use [Long files](#long-files) instead of doing steps 1-4 yourself (steps 5-6 are always yours, after the merge).
2. **Write notes.** Keep all original headings. Nested bullets only. Embed every source figure (external image URL) in its section, and copy every important multiline code block verbatim, per REFERENCE.md. Every checklist item must appear. Do not add facts not in the source; mark own clarifications `[note]`.
3. **Write quiz + key.** Work from the checklist's C-IDs and interactions, not from note sentences. Write questions that test reasoning, not recall: most apply a concept to a fresh situation (A) or integrate several concepts (I). Every C-ID gets at least one A/I question; every interaction gets an I question. The quiz is NOT meant to cover every checklist item or heading. Follow the quiz spec in REFERENCE.md (what to ask, what never to ask, R/A/I rules, split by section with a final cross-section part, then by type, slim key format). Each key's `Review:` lists the note headings it draws on; they decide the question's section.
4. **Self-check.** Run `TOOLS check <src>` and fix every `FAIL` (headings vs source, checklist/key/quiz consistency, quiz section vs `Review:` headings, C-ID and interaction coverage, R/A/I mix, MCQ option length, banned stems, numbering); read each `WARN`. A `coverage:` WARN means no 4-line passage of the notes under the item's heading holds most of its words and all its multi-digit numbers: add the point to the notes (or ignore it if the notes carry it in other words); do not re-read the notes to check coverage yourself. The script does not judge: also check by hand that no question's stem or options give away another's answer, no "never ask" topics, and each A/I question fails the one-bullet test (no single note bullet answers it). Rewrite failures around new situations, re-run `check` until clean, before reporting.
5. **Trunks (once notes are final).** Write `<trunks>` per "Trunks" in REFERENCE.md: same headings as the source, a chapter gist above the first heading, 1-3 bullets of core ideas under every heading. Write it from the notes, not from memory. Run `TOOLS check <src>` and fix every `FAIL` and `WARN`.
6. **Clean up, then report.** Once `check` has no FAIL, run `TOOLS clean <src>`: it moves the working files (`<checklist>`, `<parts>`) to the macOS Trash (never `rm`) and refuses unless notes, trunks, quiz and answers exist. Then report to user: file paths, counts (the `INFO` line of `check`: headings, checklist items, questions by type), remaining `WARN`s, anything unresolved. Reviewer-agent quiz auditing is disabled: see [temporarily-disabled-quiz-auditing.md](temporarily-disabled-quiz-auditing.md).

## Long files

Applies when the source is over ~700 lines (~8-10k tokens). Output, not input, limits quality: one agent writing checklist + notes + quiz + key for a long chapter drops items.

1. **Chunk.** `TOOLS plan <src>` prints JSON: chunk ids (A, B, ...), line ranges and headings. It splits at H1 (single H1 = chapter title → H2), merges small sections and splits oversized ones, capped at 700 lines (`--cap`). One chunk in the plan means the file is short: use the normal workflow. An `oversize: true` chunk has no finer heading to split on; tell the user.
2. **Spawn one `general-purpose` agent per chunk, all in a single message.** Each agent runs workflow steps 1-4 for its chunk only. Pass every agent:
   - source path, its line range, and `<parts>`
   - chapter title and the output of `TOOLS outline <src> --mark <start>-<end>` (full heading outline; `*` marks its own chunk) so it sees what comes before/after and which terms are defined elsewhere
   - the workflow steps 1-4 text, REFERENCE.md path (read first, incl. "Machine-checkable formats"), and the `check` command to run as `TOOLS check <src> --base <parts>/X --lines <start>-<end>`
   - chunk letter `X`: prefix checklist IDs `X-H3.2-07` and C-IDs `X-C1` so IDs stay unique after the merge
   - output paths `<parts>/X-checklist.md`, `X-notes.md`, `X-quiz.md`, `X-answers.md`
   - instruction: write only about its chunk and do not duplicate or assume content from other chunks; no `Key trade-offs at a glance` or `Review map` sections
3. **Merge.** No cross-chunk agent: interactions spanning chunks are not quizzed. `TOOLS merge <src>` combines parts in order into the four output files (concepts, then interactions; notes without repeated headings; quiz grouped by section (cross-section last) then type, round-robin across parts; quiz and key renumbered together; `Review map` rebuilt). Then `TOOLS check <src>` on the whole and fix `FAIL`s by editing the merged files.
4. **Key trade-offs (you, not an agent).** If the chapter compares 3+ options, read the merged `<notes>` once and append `## Key trade-offs at a glance` (md table: option, strengths, costs and limits) at its end, built only from facts in the notes. Reuse this read for the trunks.
5. Trunks, then clean up and report (workflow steps 5-6) on the merged whole. Chunk agents never write trunks.
