#!/usr/bin/env python3
"""Deterministic helpers for the chapter-study-notes skill (formats: REFERENCE.md, "Machine-checkable formats").

  outline <src> [--mark A-B]              heading outline: line number + verbatim heading ('*' marks headings in lines A-B)
  plan    <src> [--cap 700]               chunk plan as JSON (one chunk = one agent)
  check   <src> [--base P] [--lines A-B]  mechanical step-4 checks on <P>-{checklist,notes,quiz,answers}.md; exit 1 on FAIL
  merge   <src> [--base P] [--parts D]    merge D/<X>-{checklist,notes,quiz,answers}.md parts into the four outputs
  clean   <src> [--base P] [--parts D]    move <P>-checklist.md and D to the macOS Trash (only if notes, quiz, answers exist)

Output names: with an explicit --base P, files are <P>-{checklist,notes,quiz,answers,trunks}.md. Without it they sit next to <src>:
"chNN title.md" -> "chNN {checklist,notes,quiz,answers,trunks}.md" and "chNN parts"; any other name -> "<name>-{...}.md" and "<name>-parts".
(trunks = chapter summary + one short summary per heading; written from the final notes, whole file only, never in chunk parts.)
D defaults to the parts dir. Run: python3 -I chapter_tools.py ...
"""
import argparse
import difflib
import json
import re
import string
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HEAD = re.compile(r'^(#{1,6})\s+(.*?)(?:\s+#+)?\s*$')
FENCE = re.compile(r'^\s*(```|~~~)')
CID = r'(?:[A-Z]+-)?C\d+'
HID = r'(?:[A-Z]+-)?H\d+(?:\.\d+)*-\d+'
QSTART = re.compile(r'^\*\*Q(\d+)\.\*\*\s*')
KEYHEAD = re.compile(r'^###\s+Q(\d+)\b')
TYPES = [('mc', 'Multiple choice', 'multiple'),
         ('sa', 'Short answer', 'short'), ('sc', 'Scenarios', 'scenario')]
QUIZ_HEADER = 'Attempt closed-book; write a confidence (1-3) beside each answer, then compare with the key.'
REATTEMPT = 'Re-attempt missed or low-confidence items after 2 days and again after 1 week.'
IMG = re.compile(r'^\s*(?:[-*+]\s+)?!\[[^\]]*\]\(([^)\s]+)')
CROSS = 'Cross-section'
BANNED = re.compile(r'according to the (chapter|book|text)|the (chapter|book|text) '
                    r'(says|advises|concludes|presents|claims)|examples from the chapter', re.I)


def norm(t):
    return re.sub(r'\s+', ' ', t).strip()


def read(p):
    return Path(p).read_text(encoding='utf-8')


def headings(text):
    """[(line, level, text)], 1-based lines; skips front matter and fenced code."""
    lines, out, fence, start = text.splitlines(), [], False, 0
    if lines and lines[0].strip() == '---':
        start = next((i + 1 for i in range(1, len(lines)) if lines[i].strip() == '---'), 0)
    for i in range(start, len(lines)):
        if FENCE.match(lines[i]):
            fence = not fence
        elif not fence and (m := HEAD.match(lines[i])):
            out.append((i + 1, len(m[1]), norm(m[2])))
    return out


def figures(text, lo=0, hi=10**9):
    """{image url: section heading}, from image-only lines in lines lo-hi (callout icons inside links are skipped)."""
    out, sec, fence = {}, None, False
    for i, l in enumerate(text.splitlines(), 1):
        if FENCE.match(l):
            fence = not fence
        elif not fence and (m := HEAD.match(l)):
            sec = norm(m[2])
        elif not fence and lo <= i <= hi and (m := IMG.match(l)):
            out.setdefault(m[1], sec)  # ponytail: markdown images only, not <img> tags
    return out


COVER = 0.6  # DDIA ch04: intact notes all >= 0.62; flags 65% of single-line drops (see doc/coverage-check.md)
WIN = 4  # an item is scored against its best run of WIN consecutive non-empty note lines
NUM = re.compile(r'\d+\.\d+|\d{2,}')  # numbers an item must find in that same run
CSTOP = set('''about above after again against all also although among and another any are around because been
before being below between both but can cannot could does doing done down during each either else even ever every few
for from further had has have having here how however into its itself just less like many may might more most much must
near need needs never not now off often once one only onto other others our out over own per rather same should since
some such than that the their them then there these they this those though through thus too under until upon use used
uses using very via was were what when where whether which while who whom whose why will with within without would yet
you your'''.split())


def stems(t):
    """Content-word stems for the coverage check: lowercased, stopwords and short words dropped, plural s cut, first 5 letters."""
    ws = (w[:-1] if w.endswith('s') and len(w) > 3 else w for w in re.findall(r'[a-z0-9]+', t.lower())
          if w not in CSTOP and (len(w) >= 3 or (w.isdigit() and len(w) >= 2)))
    return {w[:5] if w.isalpha() else w for w in ws}


def coverage(checklist, notes):
    """[(item id, heading, score, missing)]: score = share of the item's stems in its best WIN-line window under the same
    heading; only windows holding all its multi-digit/decimal numbers count (none -> 0, missing = those numbers)."""
    body, cur, fence = defaultdict(list), None, False
    for l in notes.splitlines():
        if FENCE.match(l):
            fence = not fence
        elif not fence and (m := HEAD.match(l)):
            cur = norm(m[2])
        elif cur and l.strip():
            body[cur].append(l)
    wins, out, sec = {}, [], None
    for l in checklist.splitlines():
        if m := re.match(r'^## (.*)', l):
            sec = norm(m[1])
        elif sec != 'Core concepts' and (m := re.match(rf'^\s*[-*]\s*({HID})\s+(.*)', l)):
            if sec not in wins:
                ls = body[sec]
                wins[sec] = [(stems(w), set(NUM.findall(w))) for w in
                             ('\n'.join(ls[j:j + WIN]) for j in range(max(1, len(ls) - WIN + 1)))]
            it, nums = stems(m[2]), set(NUM.findall(m[2]))
            ok = [it & s for s, n in wins[sec] if nums <= n]
            got = max(ok, key=len, default=set())
            miss = sorted(it - got) if ok else sorted(nums)
            out.append((m[1], sec, len(got) / len(it) if it else 1.0, miss))
    return out


def outp(a, k):
    """Path of output kind k (checklist|notes|quiz|answers|parts) per the naming rule in the module docstring."""
    if a.base:
        return Path(f'{a.base}-{k}' + ('' if k == 'parts' else '.md'))
    src = Path(a.src)
    m = re.match(r'(ch\d+)\s', src.stem)
    return src.with_name((f'{m[1]} {k}' if m else f'{src.stem}-{k}') + ('' if k == 'parts' else '.md'))


# ---------- outline / plan ----------

def outline(a):
    lo, hi = map(int, a.mark.split('-')) if a.mark else (0, -1)
    for ln, lv, t in headings(read(a.src)):
        mark = ('* ' if lo <= ln <= hi else '  ') if a.mark else ''
        print(f'{mark}L{ln} {"#" * lv} {t}')


def divide(hs, s, e, cap):
    """Split lines s..e at the shallowest heading level inside it until every piece fits cap."""
    inner = [h for h in hs if s < h[0] <= e]
    if e - s + 1 <= cap or not inner:
        return [(s, e)]
    m = min(h[1] for h in inner)
    cuts = [h[0] for h in inner if h[1] == m]
    return [p for x, y in zip([s] + cuts, [c - 1 for c in cuts] + [e]) for p in divide(hs, x, y, cap)]


def make_plan(text, cap):
    hs, total = headings(text), len(text.splitlines())
    lvl = next((l for l in range(1, 7) if sum(h[1] == l for h in hs) >= 2), None)
    if total <= cap or lvl is None:
        secs = [(1, total)]
    else:  # first section also owns any preamble before the first split heading
        starts = [1] + [h[0] for h in hs if h[1] == lvl and h[0] > 1]
        secs = [p for x, y in zip(starts, [s - 1 for s in starts[1:]] + [total]) for p in divide(hs, x, y, cap)]
    chunks = []
    for s, e in secs:
        if chunks and e - chunks[-1][0] + 1 <= cap:
            chunks[-1][1] = e
        else:
            chunks.append([s, e])
    if len(chunks) > 26:
        sys.exit('plan: more than 26 chunks; raise --cap')
    return dict(title=hs[0][2] if hs else 'untitled', total_lines=total, cap=cap, chunks=[
        dict(id=string.ascii_uppercase[i], start=s, end=e, lines=e - s + 1, oversize=e - s + 1 > cap,
             headings=[t for ln, _, t in hs if s <= ln <= e]) for i, (s, e) in enumerate(chunks)])


def plan(a):
    print(json.dumps(make_plan(read(a.src), a.cap), indent=2, ensure_ascii=False))


# ---------- parsers ----------

def parse_checklist(text):
    """-> (concept ids, interactions [[ids]], sections [(heading, [item ids])])"""
    concepts, inter, secs, core = [], [], [], False
    for l in text.splitlines():
        if m := re.match(r'^## (.*)', l):
            core = norm(m[1]) == 'Core concepts'
            if not core:
                secs.append((norm(m[1]), []))
        elif core:
            if m := re.match(rf'^\s*[-*]\s*({CID})\b', l):
                concepts.append(m[1])
            elif re.match(r'^\s*Interactions\s*:', l):
                inter += [re.findall(CID, g) for g in re.findall(rf'{CID}(?:\s*\+\s*{CID})+', l)]
        elif secs and (m := re.match(rf'^\s*[-*]\s*({HID})\b', l)):
            secs[-1][1].append(m[1])
    return concepts, inter, secs


def sections(src):
    """(top-level headings in order, {heading: its top-level heading}); top level = H1, or H2 when the source has a single H1."""
    hs = headings(src)
    tl = 1 if sum(lv == 1 for _, lv, _ in hs) > 1 else 2
    tops, of, cur = [], {}, None
    for _, lv, t in hs:
        if lv == tl:
            tops.append(t)
            cur = t
        if lv >= tl:
            of.setdefault(t, cur)
    return tops, of


def ptype(h):
    return next((k for k, _, kw in TYPES if kw in h.lower()), None)


def parse_quiz(text):
    """-> [{n, sec, type, lines, opts}]; `# <section>` sets sec, `## <type>` sets type; a question runs to the next question/heading."""
    qs, sec, typ, cur = [], None, None, None
    for l in text.splitlines():
        if m := HEAD.match(l):
            if len(m[1]) == 1:
                sec, typ = norm(m[2]), None
            else:
                typ = ptype(m[2]) or typ
            cur = None
        elif m := QSTART.match(l):
            cur = dict(n=int(m[1]), sec=sec, type=typ, lines=[l], opts={})
            qs.append(cur)
        elif cur is not None:
            cur['lines'].append(l)
            if o := re.match(r'^\s*[-*]?\s*\(?([A-D])[.)]\s+(.*)', l):
                cur['opts'][o[1]] = o[2]
    return qs


def parse_key(text):
    """-> {n: lines} for `### Q<n>` entries, ending at the next heading of level <= 3."""
    ents, cur = {}, None
    for l in text.splitlines():
        if m := KEYHEAD.match(l):
            cur = ents.setdefault(int(m[1]), [])
            cur.append(l)
        elif re.match(r'^#{1,3}\s', l):
            cur = None
        elif cur is not None:
            cur.append(l)
    return ents


def field(lines, name):
    for l in lines:
        if m := re.match(rf'^[-*\s]*\**{name}\**\s*:\**\s*(.*)', l):
            return m[1].strip()
    return ''


# ---------- check ----------

def seqdiff(label, want, got, F):
    ops = [o for o in difflib.SequenceMatcher(None, want, got, autojunk=False).get_opcodes() if o[0] != 'equal']
    for _, i1, i2, j1, j2 in ops[:8]:
        F(f'{label}: expected {want[i1:i2]} got {got[j1:j2]}')


def check(a):
    src = read(a.src)
    lo, hi = map(int, a.lines.split('-')) if a.lines else (0, 10**9)
    chunk = bool(a.lines)
    expect = [(lv, t) for ln, lv, t in headings(src) if lo <= ln <= hi]
    out, txt = [], {}
    F = lambda m: out.append('FAIL ' + m)
    W = lambda m: out.append('WARN ' + m)
    I = lambda m: out.append('INFO ' + m)

    def done():
        print('\n'.join(out))
        return int(any(o.startswith('FAIL') for o in out))

    for k in ('checklist', 'notes', 'quiz', 'answers'):
        p = outp(a, k)
        if p.exists():
            txt[k] = read(p)
        else:
            F(f'missing {p}')
    if len(txt) < 4:
        return done()

    # notes + checklist vs source headings
    got = [(lv, t) for _, lv, t in headings(txt['notes'])]
    if got and got[-1][1] == 'Key trade-offs at a glance' and expect[-1:] != got[-1:]:
        got.pop()
    seqdiff('notes headings', expect, got, F)
    if not chunk:
        tp = outp(a, 'trunks')
        if not tp.exists():
            F(f'missing {tp}')
        else:
            trunks = read(tp)
            seqdiff('trunks headings', expect, [(lv, t) for _, lv, t in headings(trunks)], F)
            first = next((ln for ln, _, _ in headings(trunks)), 0)
            if not ''.join(trunks.splitlines()[:max(first - 1, 0)]).strip():
                F('trunks: chapter summary missing above the first heading')
            tl, hl = trunks.splitlines(), [ln for ln, _, _ in headings(trunks)] + [len(trunks.splitlines()) + 1]
            for (ln, _, t), nxt in zip(headings(trunks), hl[1:]):
                if not ''.join(tl[ln:nxt - 1]).strip():
                    W(f'trunks: no summary under "{t}"')
    have = figures(txt['notes'])
    for u, sec in figures(src, lo, hi).items():
        if u not in have:
            F(f'notes: figure missing under "{sec}": {u}')
        elif have[u] != sec:
            F(f'notes: figure under "{have[u]}" but source has it under "{sec}": {u}')
    concepts, inter, secs = parse_checklist(txt['checklist'])
    seqdiff('checklist headings', [t for _, t in expect], [h for h, _ in secs], F)
    ids = [i for _, s in secs for i in s]
    for h, s in secs:
        if not s:
            F(f'checklist: no items under "{h}"')
    for i, c in Counter(ids).items():
        if c > 1:
            F(f'checklist: duplicate ID {i}')
    in_notes = set(re.findall(HID, txt['notes']))
    if in_notes:
        for i in ids:
            if i not in in_notes:
                F(f'notes: checklist ID {i} not in notes')
    else:  # ponytail: word overlap, not meaning; a reworded item can pass or a heavy paraphrase can warn
        cov = coverage(txt['checklist'], txt['notes'])
        for i, h, s, miss in cov:
            if s < COVER:
                W(f'coverage: {i} under "{h}": {s:.0%} of its words in the best {WIN}-line window; missing {miss[:8]}')
        I(f'coverage: {sum(s >= COVER for _, _, s, _ in cov)}/{len(cov)} checklist items matched (>={COVER:.0%} word overlap)')
    if not concepts:
        F('checklist: no C-IDs under "## Core concepts"')
    for p in inter:
        for c in p:
            if c not in concepts:
                F(f'checklist: interaction uses unknown {c}')
    if not chunk and not 10 <= len(concepts) <= 20:
        W(f'{len(concepts)} core concepts (typical 10-20)')

    # quiz + key
    qs, key = parse_quiz(txt['quiz']), parse_key(txt['answers'])
    if 'Attempt closed-book' not in txt['quiz']:
        W('quiz: header line missing')
    if not qs:
        F('quiz: no questions matched "**Q<n>.** text" (see REFERENCE.md, Machine-checkable formats)')
        return done()
    nums = [q['n'] for q in qs]
    if nums != list(range(1, len(qs) + 1)):
        F(f'quiz numbering is not 1..{len(qs)}: {nums}')
    if set(key) != set(nums):
        F(f'quiz/key mismatch: only in quiz {sorted(set(nums) - set(key))}, only in key {sorted(set(key) - set(nums))}')
    tops, h1_of = sections(src)
    rank = {t: i for i, t in enumerate(tops + [CROSS])}
    order = [next((i for i, (k, _, _) in enumerate(TYPES) if k == q['type']), -1) for q in qs]
    if -1 in order:
        F('quiz: a question sits outside a recognised part heading (multiple choice/short answer/scenarios)')
    for sec in sorted({q['sec'] for q in qs if q['sec'] not in rank}, key=str):
        F(f'quiz: question(s) under "{sec}", which is not a top-level source heading or "{CROSS}" (use "# <heading>" per section)')
    if -1 not in order and all(q['sec'] in rank for q in qs):
        keys = [(rank[q['sec']], o) for q, o in zip(qs, order)]
        if keys != sorted(keys):
            F(f'quiz: sections must follow source order with "{CROSS}" last, and parts within a section '
              'must be multiple choice, short answer, scenarios')

    info = {}
    for q in qs:
        n, k = q['n'], key.get(q['n'])
        if not k:
            continue
        lvl, dif = (re.match(rf'\W*([{x}])\b', field(k, f)) for x, f in (('RAI', 'Level'), ('EMH', 'Difficulty')))
        cids = re.findall(CID, field(k, 'C-IDs'))
        if not lvl:
            F(f'Q{n}: key Level must be R, A or I')
        if not dif:
            F(f'Q{n}: key Difficulty must be E, M or H')
        if not cids:
            F(f'Q{n}: key has no C-IDs')
        for c in cids:
            if c not in concepts:
                F(f'Q{n}: unknown C-ID {c}')
        if lvl and lvl[1] == 'I' and len(set(cids)) < 2:
            F(f'Q{n}: level I needs >=2 C-IDs')
        for i in re.findall(HID, field(k, 'Checklist')):
            if i not in ids:
                W(f'Q{n}: unknown checklist ID {i}')
        revs = [norm(r) for r in field(k, 'Review').split(';') if r.strip()]
        if not revs:
            W(f'Q{n}: key has no Review heading')
        for r in revs:
            if r not in h1_of:
                W(f'Q{n}: Review heading "{r}" is not a source heading')
        found = {h1_of[r] for r in revs if h1_of.get(r)}
        want = CROSS if len(found) > 1 else next(iter(found), None)
        if want and q['sec'] in rank and q['sec'] != want:
            F(f'Q{n}: Review headings {revs} belong in "{want}", but the quiz has it under "{q["sec"]}"')
        info[n] = (lvl[1] if lvl else '?', set(cids))

    for c in concepts:
        if not any(c in cs and l in 'AI' for l, cs in info.values()):
            F(f'{c}: no A/I question')
    for p in inter:
        if not any(l == 'I' and set(p) <= cs for l, cs in info.values()):
            F(f'interaction {"+".join(p)}: no I question')
    lv, tot = Counter(l for l, _ in info.values()), max(len(info), 1)
    p = {k: 100 * lv[k] / tot for k in 'RAI'}
    msg = f'level mix R {p["R"]:.0f}% A {p["A"]:.0f}% I {p["I"]:.0f}% (targets R<=20, A>=40, I>=30)'
    (F if p['R'] > 22 or p['A'] < 38 or p['I'] < 28 else I)(msg)
    per = len(qs) / max(len(concepts), 1)
    if not 1.5 <= per <= 2.5:
        W(f'{per:.1f} questions per core concept (target 1.5-2.5)')

    mc = [q for q in qs if q['type'] == 'mc']
    letters, longest = [], []
    for q in mc:
        n, k = q['n'], key.get(q['n'], [])
        if set(q['opts']) != set('ABCD'):
            F(f'Q{n}: MCQ needs options A-D')
            continue
        m = re.match(r'\W*([A-D])\b', field(k, 'Answer'))
        if not m:
            F(f'Q{n}: key Answer must start with a letter A-D')
            continue
        letters.append(m[1])
        if len(q['opts'][m[1]]) >= max(map(len, q['opts'].values())):
            longest.append(n)
    if len(longest) > len(mc) / 4:
        F(f'correct option is the longest in {len(longest)}/{len(mc)} MCQs (max 1 of 4): Q{longest}')
    if len(letters) >= 8 and max(Counter(letters).values()) > 0.4 * len(letters):
        W(f'correct letters poorly spread: {dict(Counter(letters))}')

    for q in qs:
        body = '\n'.join(q['lines'])
        if m := BANNED.search(body):
            F(f'Q{q["n"]}: banned stem form "{m[0]}"')
        if re.search(r'\b(list|define)\b', q['lines'][0], re.I):
            W(f'Q{q["n"]}: stem uses list/define (banned form unless it is the data structure)')
    if not chunk and 'Re-attempt' not in txt['answers']:
        W('answers: missing the re-attempt line')

    I(f'{len(expect)} headings, {len(ids)} checklist items, {len(concepts)} concepts, {len(qs)} questions '
      + ', '.join(f'{n} {c}' for k, n, _ in TYPES if (c := sum(q["type"] == k for q in qs))))
    return done()


# ---------- merge ----------

def merge(a):
    d = Path(a.parts or outp(a, 'parts'))
    letters = sorted({f.name.split('-')[0] for f in d.glob('*-*.md')})
    rd = lambda L, k: read(d / f'{L}-{k}.md') if (d / f'{L}-{k}.md').exists() else ''
    if not letters:
        sys.exit(f'merge: no parts in {d}')

    # checklist: concept lines, then interaction lines, then the per-heading sections
    concepts, inter, rest = [], [], []
    for L in letters:
        core = False
        for l in rd(L, 'checklist').splitlines():
            if m := re.match(r'^## (.*)', l):
                core = norm(m[1]) == 'Core concepts'
                if core:
                    continue
            if not core:
                rest.append(l)
            elif l.strip():
                (inter if re.match(r'^\s*Interactions\s*:', l) else concepts).append(l)
    outp(a, 'checklist').write_text(
        '\n'.join(['## Core concepts'] + concepts + inter) + '\n\n' + '\n'.join(rest).strip() + '\n', encoding='utf-8')

    # notes: concatenate in order; drop headings a later part repeats at its top (e.g. the chapter title)
    seen, parts = set(), []
    for i, L in enumerate(letters):
        t = rd(L, 'notes')
        if not t:
            continue
        ls, j = t.splitlines(), 0
        while i and j < len(ls) and (not ls[j].strip() or (
                (m := HEAD.match(ls[j])) and (len(m[1]), norm(m[2])) in seen)):
            j += 1
        seen |= {(lv, tx) for _, lv, tx in headings(t)}
        parts.append('\n'.join(ls[j:]).strip())
    outp(a, 'notes').write_text('\n\n'.join(parts) + '\n', encoding='utf-8')

    # quiz + key: group by section then type, round-robin across parts, renumber together, rebuild the review map
    tops, _ = sections(read(a.src))
    per = []
    for L in letters:
        qs, key = parse_quiz(rd(L, 'quiz')), parse_key(rd(L, 'answers'))
        for q in qs:
            if q['type'] is None or q['sec'] not in tops + [CROSS] or q['n'] not in key:
                sys.exit(f'merge: {L} Q{q["n"]} has no type/section heading ("# <top-level heading>" or "# {CROSS}") or no key entry')
            q['key'] = key[q['n']]
        per.append(qs)
    ql, kl, n, review = [QUIZ_HEADER, ''], ['## Answers', ''], 0, defaultdict(lambda: ([], []))
    for sec, (t, name, _) in ((sec, ty) for sec in tops + [CROSS] for ty in TYPES):
        lists = [[q for q in qs if q['sec'] == sec and q['type'] == t] for qs in per]
        items = [l[r] for r in range(max(map(len, lists), default=0)) for l in lists if r < len(l)]
        if items and f'# {sec}' not in ql:
            ql += [f'# {sec}', '']
        if items:
            ql += [f'## {name}', '']
        for q in items:
            n += 1
            ql += [QSTART.sub(f'**Q{n}.** ', q['lines'][0], 1)] + q['lines'][1:]
            ql += [''] if q['lines'][-1].strip() else []
            kl += [KEYHEAD.sub(f'### Q{n}', q['key'][0], 1)] + q['key'][1:]
            kl += [''] if q['key'][-1].strip() else []
            for c in re.findall(CID, field(q['key'], 'C-IDs')):
                review[c][0].append(str(n))
                if (r := field(q['key'], 'Review')) and r not in review[c][1]:
                    review[c][1].append(r)
    nat = lambda c: (re.sub(r'\d+$', '', c), int(re.search(r'\d+$', c)[0]))
    kl += ['## Review map', '', '| C-ID | Questions | Reread |', '|---|---|---|']
    kl += [f'| {c} | {", ".join(review[c][0])} | {"; ".join(review[c][1])} |' for c in sorted(review, key=nat)]
    kl += ['', REATTEMPT]
    outp(a, 'quiz').write_text('\n'.join(ql).strip() + '\n', encoding='utf-8')
    outp(a, 'answers').write_text('\n'.join(kl).strip() + '\n', encoding='utf-8')
    print(f'merged {len(letters)} parts ({", ".join(letters)}), {n} questions -> {outp(a, "notes").parent}; '
          f'run check, then clean')


# ---------- clean ----------

def clean(a):
    """Move working files (checklist, parts dir) to the macOS Trash once the final files exist."""
    missing = [str(outp(a, k)) for k in ('notes', 'quiz', 'answers', 'trunks') if not outp(a, k).exists()]
    if missing:
        sys.exit(f'clean: final files missing {missing}; nothing trashed')
    work = [p for p in (outp(a, 'checklist'), Path(a.parts or outp(a, 'parts'))) if p.exists()]
    if work:
        subprocess.run(['/usr/bin/trash', *map(str, work)], check=True)  # Trash, not rm: recoverable
    print('trashed:', ', '.join(map(str, work)) or 'nothing to trash')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name, fn in (('outline', outline), ('plan', plan), ('check', check), ('merge', merge), ('clean', clean)):
        s = sub.add_parser(name)
        s.set_defaults(fn=fn)
        s.add_argument('src')
        if name == 'outline':
            s.add_argument('--mark')
        if name == 'plan':
            s.add_argument('--cap', type=int, default=700)
        if name in ('check', 'merge', 'clean'):
            s.add_argument('--base')
        if name == 'check':
            s.add_argument('--lines')
        if name in ('merge', 'clean'):
            s.add_argument('--parts')
    a = ap.parse_args(argv)
    return a.fn(a) or 0


if __name__ == '__main__':
    sys.exit(main())
