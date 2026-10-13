#!/usr/bin/env python3
"""Check P/A id and section traceability between the I12 proof and its pack.

Compares two documents:

- ``docs/decisions/CUT_PROOF_I12_20261008.md`` — the I12 cut-proof draft.
  Each proposition P1..P4 must be defined exactly once as a ``### P<n>``
  heading, and each assumption A1..A10 exactly once as the first cell of a
  markdown table row (its section-4 assumption table).
- ``docs/status/I12_REVIEW_PACK.md`` — the builder-authored review pack,
  which must carry each id exactly once as a first-column key of its
  coverage table.

A proposition counts when it is a ``### P`` heading. An assumption counts
when its id is the first cell of a markdown table row (``| A5 | ...``).
Anchoring on headings and first cells keeps in-text mentions such as
``P1–P4`` or ``the A8 list`` out of the count. Expected sets are P1..P4 and
A1..A10 on both sides.

Section references written ``proof §N`` inside the pack must resolve to a
``## N.`` heading in the proof. References to other documents carry a
document qualifier (``profile §10``, ``blueprint §6``, ``contract §4``) and
are not checked.

Reports each of: missing in proof, duplicated in proof, extra in proof,
missing in pack, duplicated in pack, extra in pack, and unresolved
``proof §N`` references in the pack. Exits 0 when every expected id appears
exactly once on both sides, no extra ids are present, and every section
reference resolves; exits 1 printing each discrepancy otherwise.

Standard library only. Convenience check, not a contract gate; not wired
into CI — wiring is a follow-up candidate (the RS-profile checker was wired
by a separate merged node). ``--self-test`` mutates in-memory copies and
requires each check to catch its break (a removed id or a dangling section
reference must be reported).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'docs/decisions/CUT_PROOF_I12_20261008.md'
PACK = ROOT / 'docs/status/I12_REVIEW_PACK.md'

EXPECTED_P = ['P%d' % i for i in range(1, 5)]
EXPECTED_A = ['A%d' % i for i in range(1, 11)]
EXPECTED = EXPECTED_P + EXPECTED_A

P_HEADING = re.compile(r'^###\s+(P\d+)\b')
ID_KEY = re.compile(r'^(P\d+|A\d+)$')
FIRST_CELL = re.compile(r'^\|\s*([^|]+?)\s*\|')
SECTION_HEADING = re.compile(r'^##\s+(\d+)\.')
PROOF_SECTION_REF = re.compile(r'proof\s+§(\d+)')


def heading_counts(text):
    """Count each P<n> id used as a '### P' heading."""
    counts = {item: 0 for item in EXPECTED_P}
    extras = {}
    for line in text.splitlines():
        match = P_HEADING.match(line)
        if not match:
            continue
        key = match.group(1)
        if key in counts:
            counts[key] += 1
        else:
            extras[key] = extras.get(key, 0) + 1
    return counts, extras


def row_key_counts(text, expected):
    """Count each expected id used as a first-column table-row key."""
    counts = {item: 0 for item in expected}
    extras = {}
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        match = FIRST_CELL.match(line)
        if not match:
            continue
        first = match.group(1).strip().split()
        if not first or not ID_KEY.match(first[0]):
            continue
        key = first[0]
        if key in counts:
            counts[key] += 1
        else:
            extras[key] = extras.get(key, 0) + 1
    return counts, extras


def find_problems(proof_text, pack_text):
    """Return a list of problem strings; empty means both sides pass."""
    problems = []

    p_counts, p_extras = heading_counts(proof_text)
    for item in EXPECTED_P:
        if p_counts[item] == 0:
            problems.append('missing in proof: %s' % item)
        elif p_counts[item] != 1:
            problems.append(
                'duplicated in proof: %s (%d)' % (item, p_counts[item]))
    for key in sorted(p_extras):
        problems.append('extra in proof: %s (%d)' % (key, p_extras[key]))

    a_counts, a_extras = row_key_counts(proof_text, EXPECTED_A)
    for item in EXPECTED_A:
        if a_counts[item] == 0:
            problems.append('missing in proof: %s' % item)
        elif a_counts[item] != 1:
            problems.append(
                'duplicated in proof: %s (%d)' % (item, a_counts[item]))
    for key in sorted(a_extras):
        problems.append('extra in proof: %s (%d)' % (key, a_extras[key]))

    pack_counts, pack_extras = row_key_counts(pack_text, EXPECTED)
    for item in EXPECTED:
        if pack_counts[item] == 0:
            problems.append('missing in pack: %s' % item)
        elif pack_counts[item] != 1:
            problems.append(
                'duplicated in pack: %s (%d)' % (item, pack_counts[item]))
    for key in sorted(pack_extras):
        problems.append('extra in pack: %s (%d)' % (key, pack_extras[key]))

    sections = set()
    for line in proof_text.splitlines():
        match = SECTION_HEADING.match(line)
        if match:
            sections.add(match.group(1))
    for lineno, line in enumerate(pack_text.splitlines(), 1):
        for ref in PROOF_SECTION_REF.finditer(line):
            if ref.group(1) not in sections:
                problems.append(
                    'unresolved section reference in pack line %d: proof §%s'
                    % (lineno, ref.group(1)))

    return problems


def _row_line(text, key):
    """First table-row line whose first cell is exactly ``key``."""
    for line in text.splitlines():
        match = FIRST_CELL.match(line)
        if match and match.group(1).strip() == key:
            return line
    return None


def _heading_line(text, key):
    """First '### P' heading line for ``key``."""
    for line in text.splitlines():
        match = P_HEADING.match(line)
        if match and match.group(1) == key:
            return line
    return None


def self_test(proof_text, pack_text):
    """Require each check to catch a deliberately broken copy."""
    base = find_problems(proof_text, pack_text)
    if base:
        print('self-test: unmodified pair already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1
    cases = []

    heading = _heading_line(proof_text, 'P1')
    a_row = _row_line(proof_text, 'A5')
    pack_row = _row_line(pack_text, 'A9')
    if heading is None or a_row is None or pack_row is None:
        print('self-test: could not find the lines to mutate', file=sys.stderr)
        return 1

    cases.append(('removed P1 heading from proof',
                  proof_text.replace(heading + '\n', '', 1), pack_text,
                  'missing in proof: P1'))
    cases.append(('removed A5 row from proof',
                  proof_text.replace(a_row + '\n', '', 1), pack_text,
                  'missing in proof: A5'))
    cases.append(('removed A9 row from pack',
                  proof_text, pack_text.replace(pack_row + '\n', '', 1),
                  'missing in pack: A9'))
    cases.append(('extra A11 row in pack',
                  proof_text,
                  pack_text + '\n| A11 | proof §4 | none | extra | none |\n',
                  'extra in pack: A11'))
    cases.append(('extra P9 heading in proof',
                  proof_text + '\n### P9. injected\n', pack_text,
                  'extra in proof: P9'))
    cases.append(('unresolved proof §9 citation in pack',
                  proof_text, pack_text + '\nSee proof §9 for details.\n',
                  'unresolved section reference'))

    for name, mutated_proof, mutated_pack, marker in cases:
        found = find_problems(mutated_proof, mutated_pack)
        if not any(marker in item for item in found):
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        caught = next(item for item in found if marker in item)
        print('self-test: detected %s (%s)' % (name, caught))
    print('self-test: pass')
    return 0


def main(argv):
    for path in (PROOF, PACK):
        if not path.is_file():
            print('missing ' + str(path), file=sys.stderr)
            return 1
    proof_text = PROOF.read_text(encoding='utf-8')
    pack_text = PACK.read_text(encoding='utf-8')
    if '--self-test' in argv:
        return self_test(proof_text, pack_text)
    problems = find_problems(proof_text, pack_text)
    if problems:
        print('i12 proof id check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    p_counts, _ = heading_counts(proof_text)
    a_counts, _ = row_key_counts(proof_text, EXPECTED_A)
    pack_counts, _ = row_key_counts(pack_text, EXPECTED)
    print('i12 proof ids ok: proof_headings=%d proof_keys=%d pack_keys=%d expected=%d'
          % (sum(p_counts.values()), sum(a_counts.values()),
             sum(pack_counts.values()), len(EXPECTED)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
