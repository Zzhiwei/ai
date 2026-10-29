"""python3 -I -m unittest test_chapter_tools  (run from this directory)"""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import chapter_tools as ct

SRC = """# Book Chapter

## Alpha
alpha text
```bash
# not a heading
```

## Beta
beta text
"""


def mcq(n, right, level, cids):
    q = f"**Q{n}.** Pick one.\n- A. {'x' * 9 if right == 'A' else 'y' * 20}\n- B. {'x' * 9 if right == 'B' else 'y' * 20}\n" \
        f"- C. {'z' * 20}\n- D. {'w' * 20}\n"
    wrong = ''.join(f'Wrong {w}: misconception\n' for w in 'ABCD' if w != right)
    return q, f"### Q{n}\nAnswer: {right}\n{wrong}Level: {level}\nDifficulty: M\nC-IDs: {cids}\nReview: Alpha\n"


def sc(n, level, cids):
    return (f"**Q{n}.** Scenario.\n",
            f"### Q{n}\nAnswer: because\nLevel: {level}\nDifficulty: M\nC-IDs: {cids}\nReview: Beta\n")


def part(letter, qs):
    """Quiz grouped as `# <section>` / `## <type>` by each key's Review heading; scenario/MCQ type from the stem."""
    quiz = ''
    for sec in ('Alpha', 'Beta', 'Alpha; Beta'):
        for typ, tag in (('Multiple choice', 'Pick one.'), ('Scenarios', 'Scenario.')):
            got = [q for q, k in qs if f'Review: {sec}\n' in k and tag in q]
            if got:
                quiz += (f'# {sec}\n\n' if f'# {sec}\n' not in quiz else '') + f'## {typ}\n\n' + '\n'.join(got) + '\n'
    quiz = quiz.replace('# Alpha; Beta\n', '# Cross-section\n')
    return quiz, '## Answers\n\n' + '\n'.join(k for _, k in qs)


class Tools(unittest.TestCase):
    def test_plan_skips_fenced_hash_and_splits_at_h2(self):
        p = ct.make_plan(SRC, cap=8)
        self.assertEqual([c['headings'] for c in p['chunks']], [['Book Chapter', 'Alpha'], ['Beta']])
        self.assertEqual(ct.make_plan(SRC, cap=700)['chunks'][0]['lines'], 10)

    def test_merge_then_check(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / 'ch.md').write_text(SRC)
            d = t / 'ch-parts'
            d.mkdir()
            for L, head, notes in (('A', ['Book Chapter', 'Alpha'], '# Book Chapter\n\n## Alpha\n- a\n'),
                                   ('B', ['Beta'], '## Beta\n- b\n')):
                cs = ''.join(f'- {L}-C{i} name: x\n' for i in (1, 2))
                items = ''.join(f'## {h}\n- {L}-H{i}.1-01 point\n' for i, h in enumerate(head, 1))
                (d / f'{L}-checklist.md').write_text(
                    f'## Core concepts\n{cs}Interactions: {L}-C1+{L}-C2 (tension)\n\n{items}')
                (d / f'{L}-notes.md').write_text(notes)
                q = [mcq(1, 'A', 'A', f'{L}-C1'), sc(2, 'I', f'{L}-C1, {L}-C2'), sc(3, 'A', f'{L}-C2')]
                quiz, key = part(L, q)
                (d / f'{L}-quiz.md').write_text(quiz)
                (d / f'{L}-answers.md').write_text(key)
            # cross-chunk part: interaction + one I question, no notes
            (d / 'Z-checklist.md').write_text('## Core concepts\nInteractions: A-C1+B-C1 (cross)\n')
            q = sc(1, 'I', 'A-C1, B-C1')
            q = (q[0], q[1].replace('Review: Beta', 'Review: Alpha; Beta'))
            quiz, key = part('Z', [q])
            (d / 'Z-quiz.md').write_text(quiz)
            (d / 'Z-answers.md').write_text(key)

            ct.main(['merge', str(t / 'ch.md')])
            (t / 'ch-trunks.md').write_text('Chapter gist.\n\n# Book Chapter\n- t\n\n## Alpha\n- a\n\n## Beta\n- b\n')
            quiz = (t / 'ch-quiz.md').read_text()
            self.assertEqual([m for m in ct.re.findall(r'\*\*Q(\d+)\.', quiz)], list('1234567'))
            self.assertEqual(quiz.count('## Multiple choice'), 1)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = ct.main(['check', str(t / 'ch.md')])
            self.assertEqual(rc, 0, buf.getvalue())

            # clean refuses (and trashes nothing) while a final file is missing
            (t / 'ch-quiz.md').rename(t / 'ch-quiz.bak')
            with self.assertRaises(SystemExit):
                ct.main(['clean', str(t / 'ch.md')])
            self.assertTrue(d.exists() and (t / 'ch-checklist.md').exists())
            (t / 'ch-quiz.bak').rename(t / 'ch-quiz.md')

            # break it: drop a heading from the notes -> FAIL
            (t / 'ch-notes.md').write_text((t / 'ch-notes.md').read_text().replace('## Beta\n', ''))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ct.main(['check', str(t / 'ch.md')]), 1)

    def test_trunks_headings_and_chapter_summary(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / 'ch.md').write_text(SRC)
            for k in ('checklist', 'notes', 'quiz', 'answers'):
                (t / f'ch-{k}.md').write_text('x')

            def run(trunks=None):
                if trunks is not None:
                    (t / 'ch-trunks.md').write_text(trunks)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    ct.main(['check', str(t / 'ch.md')])
                return buf.getvalue()

            self.assertIn('missing', run())
            good = 'Gist.\n\n# Book Chapter\n- t\n\n## Alpha\n- a\n\n## Beta\n- b\n'
            self.assertNotIn('trunks', run(good))
            self.assertIn('trunks headings', run(good.replace('## Beta\n- b\n', '')))
            self.assertIn('chapter summary missing', run(good.replace('Gist.\n\n', '')))
            self.assertIn('no summary under "Beta"', run(good.replace('- b\n', '')))

    def test_coverage_flags_checklist_items_missing_from_their_section(self):
        cl = ('## Core concepts\n- C1 x: y\n\n## Alpha\n- H1-01 Bloom filters give 1% false positives at 10 bits per key\n'
              '- H1-02 Compaction merges segments in the background\n')
        notes = '## Alpha\n- A **Bloom filter** with 10 bits per key gives ~1% false positives\n\n## Beta\n- compaction merges segments\n'
        got = {i: s for i, _, s, _ in ct.coverage(cl, notes)}
        self.assertGreaterEqual(got['H1-01'], ct.COVER)
        self.assertLess(got['H1-02'], ct.COVER)  # its words are only under Beta
        # numbers must be in the matching window; fences don't split headings; wordless items pass
        cl2 = '## Alpha\n- H1-03 Bloom filters give 1% false positives at 12 bits per key\n- H1-04 `ls -l`\n'
        notes2 = '## Alpha\n```\n# not a heading\n```\n- A **Bloom filter** with 10 bits per key gives ~1% false positives\n'
        got = {i: (s, m) for i, _, s, m in ct.coverage(cl2, notes2)}
        self.assertEqual(got['H1-03'], (0, ['12']))
        self.assertEqual(got['H1-04'][0], 1.0)
        self.assertGreaterEqual(ct.coverage(cl2, notes2.replace('10 bits', '12 bits'))[0][2], ct.COVER)

    def test_figures_must_be_in_notes_under_same_section(self):
        src = SRC.replace('alpha text', 'alpha text\n![Fig 1](http://x/a.png)\n[![1](http://x/icon.png)](http://x/#n)')
        self.assertEqual(ct.figures(src), {'http://x/a.png': 'Alpha'})
        self.assertEqual(ct.figures('## A\n```\n![f](http://x/c.png)\n```\n'), {})
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / 'ch.md').write_text(src)
            for k in ('checklist', 'quiz', 'answers'):
                (t / f'ch-{k}.md').write_text('x')

            def run(notes):
                (t / 'ch-notes.md').write_text(notes)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    ct.main(['check', str(t / 'ch.md')])
                return buf.getvalue()

            base = '# Book Chapter\n\n## Alpha\n- a\n  - ![Fig 1](http://x/a.png)\n\n## Beta\n- b\n'
            self.assertNotIn('figure', run(base))
            self.assertIn('figure missing under "Alpha"', run(base.replace('http://x/a.png', 'http://x/z.png')))
            moved = base.replace('  - ![Fig 1](http://x/a.png)\n', '').replace('- b\n', '- b\n  - ![Fig 1](http://x/a.png)\n')
            self.assertIn('figure under "Beta" but source has it under "Alpha"', run(moved))

    def test_keyword_table_rejects_heading_words_and_unknown_sections(self):
        src = '# One\n\ntext\n\n# Two Things\n\ntext\n'
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / 'ch.md').write_text(src)
            for k in ('checklist', 'quiz', 'answers'):
                (t / f'ch-{k}.md').write_text('x')

            def run(table):
                (t / 'ch-notes.md').write_text(table + '# One\n\n- a\n\n# Two Things\n\n- b\n')
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    ct.main(['check', str(t / 'ch.md')])
                return buf.getvalue()

            head = '| Section | Keywords |\n| --- | --- |\n'
            self.assertNotIn('keywords:', run(''))
            ok = run(head + '| One | alpha, beta, gamma, delta, epsilon |\n| Two Things | zeta, eta, theta, iota, kappa |\n\n')
            self.assertNotIn('keywords:', ok)
            bad = run(head + '| One | alpha, thing, gamma, delta, epsilon |\n| Nope | a, b, c, d, e |\n\n')
            self.assertIn('"thing" (One) uses heading words', bad)
            self.assertIn('row "Nope" is not a top-level', bad)
            self.assertIn('no row for "Two Things"', bad)
            self.assertEqual(ct.keyword_table('x\n| Section | Keywords |\n'), [])

    def test_output_names_drop_title_for_chnn_sources(self):
        mk = lambda src, base=None: type('A', (), {'src': src, 'base': base})
        self.assertEqual(ct.outp(mk('/d/ch03 Data models.md'), 'notes'), Path('/d/ch03 notes.md'))
        self.assertEqual(ct.outp(mk('/d/ch03 Data models.md'), 'parts'), Path('/d/ch03 parts'))
        self.assertEqual(ct.outp(mk('/d/ch.md'), 'quiz'), Path('/d/ch-quiz.md'))
        self.assertEqual(ct.outp(mk('/d/ch03 x.md', '/p/X'), 'answers'), Path('/p/X-answers.md'))

    def test_quiz_sections_follow_review_headings(self):
        parse = ct.parse_quiz('Attempt.\n\n# Alpha\n\n## Scenarios\n\n**Q1.** x\n\n# Cross-section\n\n## Multiple choice\n\n**Q2.** y\n- A. a\n')
        self.assertEqual([(q['n'], q['sec'], q['type']) for q in parse], [(1, 'Alpha', 'sc'), (2, 'Cross-section', 'mc')])
        tops, of = ct.sections(SRC)
        self.assertEqual((tops, of['Alpha']), (['Alpha', 'Beta'], 'Alpha'))
        tops, of = ct.sections('# A\n## a1\n# B\n## b1\n### b2\n')
        self.assertEqual((tops, of['b2'], 'A' in of), (['A', 'B'], 'B', True))

        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / 'ch.md').write_text(SRC)
            for k in ('checklist', 'notes'):
                (t / f'ch-{k}.md').write_text('x')

            def run(quiz, review):
                (t / 'ch-quiz.md').write_text(quiz)
                (t / 'ch-answers.md').write_text(f'## Answers\n\n### Q1\nReview: {review}\n')
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    ct.main(['check', str(t / 'ch.md')])
                return buf.getvalue()

            q = '# {}\n\n## Scenarios\n\n**Q1.** x\n'
            self.assertNotIn('belong in', run(q.format('Alpha'), 'Alpha'))
            self.assertIn('belong in "Beta", but the quiz has it under "Alpha"', run(q.format('Alpha'), 'Beta'))
            self.assertIn('belong in "Cross-section"', run(q.format('Alpha'), 'Alpha; Beta'))
            self.assertIn('belong in "Alpha"', run(q.format('Cross-section'), 'Alpha'))
            self.assertIn('not a top-level source heading', run(q.format('Nowhere'), 'Alpha'))
            self.assertIn('sections must follow source order', run(q.format('Beta') + '\n# Alpha\n\n## Scenarios\n\n**Q2.** y\n', 'Beta'))


if __name__ == '__main__':
    unittest.main()
