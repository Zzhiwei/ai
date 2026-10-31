# Reference

## Note format

- Headings: copy verbatim from source, same `#` levels, same order. Include every heading, even short ones. No renaming, merging, or reordering.
- Body: bullets and nested bullets only; no prose paragraphs.
  - Level 1: the point. Level 2+: reasons, examples, numbers, caveats, trade-offs.
  - **Bold** each term on first definition. Keep exact figures, names, and system/paper citations.
  - Tables in source: keep as md tables.
  - Code in source: copy every important multiline code block verbatim as a fenced block (same language tag), plus bullets on what it shows; skip only trivial or repeated snippets. Place it under the top-level bullet it belongs to, indented as that bullet's child, after the bullet's nested children. If a nested bullet is what the code illustrates, that bullet says so (`(code below)`), so the block never sits deep in the tree.
  - Figures (`![alt](url)` lines in source): describe each in one bullet, then embed it as the next child bullet `- ![Figure N](<same url as source>)`, under the bullet that cites it, in the same section as in the source. Never drop, rewrite or localise the URL. `check` fails on any source figure missing from, or in a different section of, the notes.
- Keep: definitions, "why", comparisons, pros/cons, failure modes, examples, edge cases, formulas, chapter summary points.
- Skip only: pure filler, transitions, repeated restatements. When unsure, keep.
- Add no sections beyond the original headings, except a final `## Key trade-offs at a glance` table if the chapter compares 3+ options.

## Trunks

`<trunks>` is a skim layer: enough to see the shape of the chapter and decide what to read closely, and to give later detail something to attach to. Written after the notes are final, from the notes.

- Top, above the first heading: a chapter gist headed `**Chapter in one view**`, 4-8 bullets: what the chapter is about, its main threads, the key trade-off or lesson of each.
- Then every heading of the source, verbatim, same `#` levels, same order (including Summary). `check` enforces this.
- Under each heading: 1-3 short bullets with the core idea of that section (the "trunk"): what it is mainly about and why it matters, plus the one trade-off or distinction a reader should not miss. A heading that only introduces subsections gets one bullet.
- Not a shortened copy of the notes: no figures, tables, code, numbers or examples unless one is the section's point; no quiz material. Use plain terms, names the reader will meet again, and no new facts beyond the source.
- Keep it to a few lines per section; the whole file should be skimmable in a couple of minutes.

## Checklist format

```
## <original heading>
- H1.2-01 Single-leader replication: all writes go via leader; followers apply log.
- H1.2-02 ...
```

Put a `## Core concepts` section at the top of the checklist file, before the heading sections:

```
## Core concepts
- C1 <name>: <the principle, trade-off or mechanism in one line>
- C2 ...
Interactions: C1+C3 (<the tension or dependency>), C2+C4 (...)
```

- A concept qualifies only if understanding it changes a decision or prediction, and a student could plausibly misapply it or confuse it with a neighbour. Definitions, examples, figures and numbers are not concepts; they support one.
- Typically 10-20 concepts. List the interactions: pairs or triples where one concept constrains, trades off against, or breaks another.

## Quiz spec

Test understanding of the core concepts the chapter teaches, not recall of what the book says.

- **Ask about**: principles, trade-offs, cause and effect, why a technique exists, how to apply a concept to a new scenario, and how to tell similar concepts apart.
- **Never ask about**: how the book is structured or what it "presents" or "claims"; figures, diagrams or their style; incidental case-study details (table names, schema, query text); plain arithmetic (unless calculation is the chapter's lesson; a tiny calculation that applies a concept is fine); tool, library or product names; specific statistics and cited-study numbers; historical anecdotes and incident details; minor terminology the chapter itself calls flawed or secondary. Also banned as question forms: stems containing "according to the chapter", "the chapter says/advises/concludes", "list", "define", or "give N examples from the chapter"; MCQs that only match labels to definitions; "list N ways" short answers where any N correct items earn credit.
- **Size**: roughly 1.5-2.5 questions per core concept (C-ID); the total scales with the concept count (no fixed cap). Stop when every C-ID has at least one A or I question and each listed interaction has an I question. Never add questions to reach a count or to fill a type slot; skip a heading with no core concept.
- **Cognitive level** (tag every question R / A / I in the key). Not a recall exam:
  - **R, recall** (state or recognize a definition or fact; also any question whose answer is found by matching one note bullet): at most ~20% of questions, only for foundation terms later questions rely on.
  - **A, apply/analyze** (use ONE concept on a new situation: predict an outcome, diagnose a cause, choose between options and justify, spot the flaw in a proposal, explain why a design fails; a trade-off within a single concept is A): at least ~40%.
  - **I, integrate** (needs two or more distinct C-IDs, from different parts of the chapter, where removing either changes the answer; the key's principle line must name the interaction being resolved, and `Review:` must cite at least two source headings): at least ~30%. Every scenario question must be A or I.
  - Tags are verified, not self-reported: the Auditor re-tags independently (see Auditor prompt). If the verified mix misses the targets, rewrite the offending questions around new situations; do not just relabel or delete them.
- **How to write A/I questions**
  - Invent a fresh situation (different system, numbers or domain than the chapter's own examples) whose answer follows from the chapter's reasoning; do not replay the chapter's example. Fresh-domain rule: each chapter example appears in at most one question; all other scenarios use a different domain.
  - Anti-lookup: describe symptoms and constraints, not the concept's name or the note's key terms; the student must infer which concept applies. Test: strip the question of shared keywords; if one note bullet still identifies the answer, rewrite it.
  - Counterfactual test: changing one stated fact in the scenario should change the answer; if not, the scenario is decoration.
  - Use stems such as: "what would happen if...", "which explains this symptom", "which proposal is flawed and why", "choose X or Y given these constraints and justify", "what changes if requirement Z is added", "why does fix F not help here".
  - Make MCQs scenario-based where possible: a short situation, then options that are plausible diagnoses or decisions; distractors are real misconceptions or right ideas applied to the wrong situation.
  - Integrate by combining concepts that interact (e.g. a metric choice with a failure mode, a scaling choice with an operations cost, a fault-tolerance limit with a maintenance procedure). Ask the student to resolve the tension, not list the parts.
  - Short answers ask "explain why" or "compare", not "define" or "list".
  - Prefer, for at least a quarter of MCQs, "choose + one-sentence reason" (pick the option and say why), which cuts guessing.
  - Everything must be answerable from the note by reasoning. Do not require outside facts, and do not introduce concepts the chapter does not teach.
- **Mix** (guidance only; adjust to chapter): about 35% MCQ (4 options, one correct), 25% short answer, 40% scenario/design (given a system and requirements, choose and justify). No true/false questions. If a type cannot hold A/I questions for this chapter, use fewer of it; a type slot never justifies a recall question.
- **Structure**: split by top-level section of the source (H1; H2 if the source has a single H1), in source order, each under `# <heading verbatim>`; omit sections with no questions. Inside a section, group by question type under `## ` headings in this order: multiple choice, short answer, scenarios; interleave concepts within a type. A question whose `Review:` headings fall under 2+ top-level sections is cross-section: it goes in a final `# Cross-section` part (same type sub-groups), never in a section; a question whose headings fall under one section never goes there. Number questions continuously from 1 across the whole quiz.
- **Form (MCQ)**: each wrong option encodes one real misconception or a right idea applied to the wrong situation; options are parallel in grammar and level of detail. Count characters: the correct option may be the longest in at most 1 of 4 MCQs. Spread correct letters across A-D. No "all/none of the above", no absurd distractors. No hints in wording.
- **No leakage**: a question's stem or options must not state the answer to another question (e.g. an MCQ defining a term that a short-answer question asks you to define). When two questions test the same idea, keep the better one or ask about different aspects.
- `<quiz>`: header line "Attempt closed-book; write a confidence (1-3) beside each answer, then compare with the key." Then `# <section>` headings, `## <type>` part headings, question number, text, options. Nothing else.
- `<answers>`: per question:
  - answer, and a 1-2 line principle in your own words (do not restate a note sentence);
  - concept IDs (C-IDs), checklist IDs touched, `Review: <note heading>` (one or more, separated by `; `; list every section the question draws on, since the headings decide its quiz section);
  - level R/A/I; difficulty E = one step from one note passage, M = one inference or two concepts, H = two or more inferences or competing constraints;
  - Slim: nothing else. No per-distractor lines, reasoning chain or rubric.
  - End the file with a `## Review map` table: C-ID, question numbers, note heading to reread, and a line "Re-attempt missed or low-confidence items after 2 days and again after 1 week."

## Machine-checkable formats

`scripts/chapter_tools.py` parses these; follow them exactly.

- Checklist: `## Core concepts` first (`- C1 name: ...` lines, then `Interactions: C1+C3 (...), ...`), then one `## <heading text>` per source heading (all at `##`, text only) with `- H1.2-01 point` items.
- Notes: headings identical to the source (same level and text, same order).
- Trunks: headings identical to the source (same level, text, order); non-empty text above the first heading and under each heading (`check` warns on empty sections).
- `<quiz>`: line 1 is the closed-book header; sections as `# <top-level source heading>` in source order, then optionally `# Cross-section`; inside each, parts as `## Multiple choice`, `## Short answer`, `## Scenarios` (in that order; omit empty ones); each question starts with `**Q<n>.** <text>`; MCQ options on their own lines `- A. text` ... `- D. text`.
- `<answers>`: `## Answers`, then per question `### Q<n>` followed by field lines (bullets/bold allowed): `Answer:` (MCQ: starts with the letter), `Level:` R|A|I, `Difficulty:` E|M|H, `C-IDs:` C1, C4, `Checklist:` H1.2-01, ..., `Review:` <note heading>[; <note heading>...]. Then `## Review map`.
- Chunk parts (long files): same formats, files `<parts>/<X>-{checklist,notes,quiz,answers}.md` (no trunks in parts), IDs prefixed with the chunk letter (`X-H3.2-07`, `X-C1`), questions numbered from 1 within the part. Do not add `## Key trade-offs at a glance` or `## Review map` in parts. Chunk quizzes use the same `# <section>` / `## <type>` headings.

## Taker prompt (template)

> You are a student who has studied ONLY this note: `<notes path>`. Read it fully, then answer every question in `<quiz path>`. Do not read other files. Write answers to `<scratch path>` as `Q#: answer`, a confidence (low/med/high), and one line of reasoning; add `MATCHED: "<quoted note sentence>"` when you answered by finding a sentence rather than inferring, and `Steps: <n>` for the number of inferences you made. Then give feedback: unclear/ambiguous questions, questions the note doesn't let you answer, questions with multiple defensible answers, difficulty balance, multiple-choice questions where you could guess the answer from form alone (length, qualifiers) or from another question, questions that test trivia or plain recall instead of understanding (which questions did you answer by matching wording to the note instead of reasoning?), which questions needed you to combine several concepts, anything in the note that confused you or seemed wrong. Be specific, cite Q#. Do not edit the note or quiz.

## Auditor prompt (template)

> You audit a study note and exam against the source. Read `<source>`, `<checklist>`, `<notes>`, `<quiz>`, `<answers>`. Report, citing IDs/Q#: (1) source points missing or distorted in notes; (2) C-IDs in the checklist's Core concepts section with no A/I question, C-IDs tested only by R, interactions with no I question, and core concepts missing from that list; (3) key answers that are wrong or disputable per the source (recompute any arithmetic); (4) ambiguous questions, questions that leak another question's answer, MCQs with more than one defensible option or a correct option that stands out by length; (5) trivia: questions about book structure, figures, incidental details, plain arithmetic, tool names, or cited statistics; (6) recall-heavy design: questions tagged A or I that are really recall (answerable by matching a sentence in the notes), scenarios that merely replay the chapter's own example, "integrate" questions that only list parts, and any A/I question that needs facts or concepts not in the notes; re-tag every question R/A/I independently of the key's tags (for each A/I question, quote the single note bullet that would answer it; if one bullet suffices, it is R; I needs two or more distinct C-IDs), and report the re-tagged mix against the targets, listing disagreements with the key; also flag banned stem forms ("the chapter says", "list", "define"), MCQs whose correct option is the longest, and key principles that merely restate a note sentence; (7) headings changed/missing in the notes vs source. Rank by severity. Quote the source line for each claim. Do not edit files.

## Assessment hints

- Taker score <70% on a well-supported question set usually means unclear questions or note gaps, not a weak taker.
- Taker score 100% with all-high confidence suggests the exam is too easy; add harder scenario questions that combine concepts, not more recall.
- A Taker who answers A/I questions correctly by quoting a note sentence means the question is recall in disguise; rewrite it around a new situation.
- A Taker who misses an A/I question: if the note contains the needed concepts and the key's principle follows from them, keep the question (it is doing its job); if a needed concept is absent from the note, fix the note.
- Taker score reflects clarity, key correctness and note coverage, not human difficulty or discrimination; do not report it as a difficulty measure.
- Optional blind pass: a third agent gets the quiz only (no notes). Questions it answers correctly with high confidence are answerable by common sense or test-wiseness; rewrite or drop them unless they are R foundation items.
- Reject Auditor requests to add questions merely to cover an unused checklist item; add one only if it tests a C-ID.
- Reject feedback that asks for facts not in the source.
