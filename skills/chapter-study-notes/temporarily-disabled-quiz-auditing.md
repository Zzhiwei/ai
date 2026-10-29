# Temporarily disabled: quiz auditing (reviewer agents)

Removed from SKILL.md on request. To re-enable, paste these back into SKILL.md after step 4 of the workflow (renumber the Report step), and restore the long-files line below. Reviewer prompt templates and assessment hints are still in REFERENCE.md.

## Workflow steps (were 5-7)

5. **Spawn two reviewers in parallel** (single message, `general-purpose` agents), prompts in REFERENCE.md:
   - **Taker**: gets notes + quiz only. Studies, answers every question, reports feedback.
   - **Auditor**: gets source + checklist + notes + quiz + key. Hunts note omissions, wrong/ambiguous/leaking/trivia questions, untested C-IDs, wrong key, and independently re-tags R/A/I.
   - Optional **blind Taker** (quiz only, no notes, cheap): high-confidence correct answers mean a question is answerable without the chapter; see REFERENCE.md.
6. **Assess feedback (you, not the reviewers).**
   - Grade the Taker's answers with the key. Wrong answer on an R question → check clarity, fix the question. Wrong answer on an A/I question where the notes contain the needed concepts and the key's principle follows from them → keep the question (it is doing its job). A needed concept missing from the notes → fix the notes. Taker right, key wrong → fix the key. Taker right via a `MATCHED` note sentence on an A/I question → the question is recall in disguise; rewrite it.
   - Use the Auditor's re-tagged R/A/I mix, not the author's tags, against the targets; rewrite offending questions rather than relabeling them.
   - Verify each Auditor finding against the source before acting. Accept or reject with a one-line reason.
   - Apply accepted fixes to notes, quiz, key, checklist.
7. **Repeat 5-6 only if** fixes were substantive (new questions, rewritten notes, key corrections). Max 2 rounds total.

Report step additions: "reviewer score", "rejected feedback".

## Long files, last step (was step 5)

Run workflow steps 5-8 on the merged whole (Auditor and Taker get the whole thing; if too large for one reviewer, one pair per ~2 chunks).

## Rules (were in Rules)

- Never give the key to the Taker.
- Never trust reviewer claims about the source without checking it.
- Reviewers never edit files; only you do.
