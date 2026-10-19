#!/usr/bin/env python3
"""Check the TL predicate evidence map against the three source documents.

Compares ``docs/status/TL_PREDICATE_EVIDENCE_MAP.md`` with the identifier
sets derived from:

- ``docs/blueprints/optional-native-token-v1/README.md`` section 3.2
  (TK-1..TK-12) and section 6.3 (V1..V6)
- ``docs/contracts/TOKEN_ROLE_AND_SUPPLY.md`` section 8
  (TL0-TK01-T1..TL0-TK12-T1)
- ``docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md`` section 8
  (TL1-TK02-T1..T6, TL1-TK03-T1..T2, TL1-TK06-T1..T6,
  TL1-TK10-T1..T3, TL1-LC-T1..T2)

Checks:

1. IDs. The derived set equals the map row IDs, each exactly once.
2. Row width. Six cells per row.
3. Status. One of HARNESS_AUTHOR_SIDE, REVIEWED_RECORD,
   NOT_VERIFIABLE_NO_PACKAGE, PARTIAL.
4. Coverage. A row with a citation must not be NOT_VERIFIABLE_NO_PACKAGE;
   a row without a citation must be NOT_VERIFIABLE_NO_PACKAGE.
5. Owner. Every NOT_VERIFIABLE_NO_PACKAGE or PARTIAL row has an owner
   string and that string occurs in the applicable source document.
6. Citations. Each citation is ``path::symbol`` in backticks. The path is
   repo-relative and one of the six allowed files; the file exists; the
   symbol is defined (Python ``def``/``class`` for ``.py`` files, exact
   text present for ``.md`` files).
7. Counts. The single ``Counts:`` line matches the recomputed totals.

``--self-test`` mutates in-memory copies and requires each break to be
caught (dropped ID, invented ID, missing path, missing symbol, stale
Counts line).

Standard library only. It reads the cited files as text and executes none
of them.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/TL_PREDICATE_EVIDENCE_MAP.md'
BLUEPRINT = 'docs/blueprints/optional-native-token-v1/README.md'
TL0 = 'docs/contracts/TOKEN_ROLE_AND_SUPPLY.md'
TL1 = 'docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md'

STATUSES = ('HARNESS_AUTHOR_SIDE', 'REVIEWED_RECORD',
            'NOT_VERIFIABLE_NO_PACKAGE', 'PARTIAL')
NEEDS_MISSING = ('NOT_VERIFIABLE_NO_PACKAGE', 'PARTIAL')

ALLOWED_PATHS = (
    'reference/token_reward/test_reward_model.py',
    'reference/token_reward/test_reward_fsm.py',
    'reference/token_reward/test_tl4_model_properties.py',
    'reference/token_reward/test_tl4_fsm_properties.py',
    'reference/token_reward/test_tl4_fuzz_boundaries.py',
    'docs/decisions/TL4_THREAT_MODEL_20261009.md',
)

ID_CELL = re.compile(
    r'^\|\s*(TK-\d\d?|V[1-6]|TL0-TK\d\d-T\d|TL1-(?:TK\d\d?|LC)-T\d)\s*\|')
CITATION = re.compile(r'`([^`]+)`')
STATUS_WORD = re.compile(r'^[A-Z_]+$')
COUNTS_LINE = 'Counts:'

DEF_PATTERNS = {
    '.py': r'^\s*(?:(?:async\s+)?def|class)\s+%s\b',
}


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def _expand_range(start, end):
    """Expand TL1-style ranges like TL1-TK02-T1 .. TL1-TK02-T6."""
    ids = []
    prefix = '-'.join(start.split('-')[:-1])  # e.g. TL1-TK02
    lo = int(start.split('-')[-1][1:])        # e.g. 1
    hi = int(end.split('-')[-1][1:])           # e.g. 6
    for n in range(lo, hi + 1):
        ids.append('%s-T%d' % (prefix, n))
    return ids


def _extract_tl1_ids(text):
    """Return {id: owner_cell} from the TL1 section 8 predicate table."""
    ids = {}
    in_section = False
    for line in text.splitlines():
        if line.startswith('## 8.'):
            in_section = True
            continue
        if in_section and line.startswith('## '):
            break
        if not in_section or not line.startswith('|'):
            continue
        cells = split_row(line)
        if len(cells) < 3:
            continue
        first = cells[0]
        owner = cells[2]
        # range rows: `TL1-TK02-T1`부터 `TL1-TK02-T6`
        m = re.search(r'`(TL1-(?:TK\d\d?|LC)-T\d+)`부터 `(TL1-(?:TK\d\d?|LC)-T\d+)`',
                      first)
        if m:
            for ident in _expand_range(m.group(1), m.group(2)):
                ids[ident] = owner
        else:
            for m2 in re.finditer(r'TL1-(?:TK\d\d?|LC)-T\d+', first):
                ids[m2.group(0)] = owner
    return ids


def source_ids():
    """Return (expected_set, id_to_source) for the three source docs."""
    blueprint_text = (ROOT / BLUEPRINT).read_text(encoding='utf-8')
    tl0_text = (ROOT / TL0).read_text(encoding='utf-8')
    tl1_text = (ROOT / TL1).read_text(encoding='utf-8')

    expected = set()
    id_to_source = {}

    # Blueprint: TK-1..TK-12 (section 3.2 table) and V1..V6 (section 6.3)
    for ident in re.findall(r'^\|\s*(TK-\d\d?)\s*\|', blueprint_text, re.M):
        expected.add(ident)
        id_to_source[ident] = (BLUEPRINT, blueprint_text)
    for ident in re.findall(r'^\|\s*(V[1-6])\s*\|', blueprint_text, re.M):
        expected.add(ident)
        id_to_source[ident] = (BLUEPRINT, blueprint_text)

    # TL-0: TL0-TK01-T1 .. TL0-TK12-T1 from section 8
    for ident in re.findall(r'(TL0-TK\d\d-T\d)', tl0_text):
        expected.add(ident)
        id_to_source[ident] = (TL0, tl0_text)

    # TL-1: ranges and explicit IDs from section 8
    for ident, owner in _extract_tl1_ids(tl1_text).items():
        expected.add(ident)
        id_to_source[ident] = (TL1, tl1_text)

    return expected, id_to_source


def map_rows(map_text):
    return [(m.group(1), split_row(line))
            for line in map_text.splitlines()
            for m in [ID_CELL.match(line)] if m]


def parse_cell(cell):
    out = []
    for match in CITATION.finditer(cell):
        path, _, symbol = match.group(1).partition('::')
        out.append((path.strip(), symbol.strip() or None))
    return out


def symbol_defined(text, suffix, symbol):
    if suffix == '.md':
        return symbol in text
    pattern = DEF_PATTERNS.get(suffix)
    if pattern is None:
        return False
    return re.search(pattern.replace('%s', re.escape(symbol)), text,
                     re.M) is not None


def find_problems(map_text, expected, id_to_source, files=None, root=ROOT):
    files = files or {}
    problems = []
    cache = {}

    def read(path):
        if path in files:
            return files[path]
        if path not in cache:
            target = root / path
            cache[path] = target.read_text(encoding='utf-8') if target.is_file() else None
        return cache[path]

    rows = map_rows(map_text)
    counts = {}
    for ident, _ in rows:
        counts[ident] = counts.get(ident, 0) + 1
    for ident in expected:
        if counts.get(ident, 0) == 0:
            problems.append('missing in map: %s' % ident)
        elif counts[ident] != 1:
            problems.append('duplicated in map: %s (%d)' % (ident, counts[ident]))
    for ident in sorted(counts):
        if ident not in expected:
            problems.append('invented id: %s' % ident)

    seen = set()
    by_status = {s: 0 for s in STATUSES}
    for ident, cells in rows:
        if ident in seen:
            continue
        seen.add(ident)

        if len(cells) != 6:
            problems.append('%s: expected 6 cells, found %d' % (ident, len(cells)))
            continue

        status = cells[3]
        if not STATUS_WORD.fullmatch(status) or status not in STATUSES:
            problems.append('%s: unknown status %r' % (ident, status))
        else:
            by_status[status] += 1

        cites = parse_cell(cells[2])
        if status == 'NOT_VERIFIABLE_NO_PACKAGE' and cites:
            problems.append('%s: NOT_VERIFIABLE_NO_PACKAGE row carries a citation' % ident)
        elif status != 'NOT_VERIFIABLE_NO_PACKAGE' and not cites:
            problems.append('%s: %s row has no citation' % (ident, status))

        if status in NEEDS_MISSING:
            if not cells[4]:
                problems.append('%s: empty missing-or-open cell' % ident)
            elif cells[4].lower().startswith('none'):
                problems.append('%s: %s row must say what is missing' % (ident, status))
            if not cells[5]:
                problems.append('%s: %s row must have an owner' % (ident, status))
            else:
                source_path, source_text = id_to_source.get(ident, (None, None))
                if source_text is None:
                    problems.append('%s: no applicable source document for owner check' % ident)
                elif cells[5] not in source_text:
                    problems.append('%s: owner %r not found in %s' % (ident, cells[5], source_path))

        for path, symbol in cites:
            where = '%s: citation %s' % (ident, path)
            if path.startswith('/') or '..' in path.split('/'):
                problems.append('%s is not repo-relative' % where)
                continue
            if path not in ALLOWED_PATHS:
                problems.append('%s is not an allowed evidence path' % where)
                continue
            text = read(path)
            if text is None:
                problems.append('%s does not exist' % where)
                continue
            if symbol is None:
                problems.append('%s needs a ::symbol' % where)
                continue
            if not symbol_defined(text, Path(path).suffix, symbol):
                problems.append('%s::%s is not defined in the file' % (where, symbol))

    lines = [l for l in map_text.splitlines() if l.startswith(COUNTS_LINE)]
    want = COUNTS_LINE + ' ' + ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)
    if len(lines) != 1:
        problems.append('%r line appears %d times' % (COUNTS_LINE, len(lines)))
    elif lines[0].strip() != want:
        problems.append('counts line %r differs from %r' % (lines[0].strip(), want))

    return problems


def _row_line(text, ident):
    for line in text.splitlines():
        match = ID_CELL.match(line)
        if match and match.group(1) == ident:
            return line
    return None


def _with_cell(text, ident, col, new):
    line = _row_line(text, ident)
    cells = split_row(line)
    cells[col] = new
    return text.replace(line, '| ' + ' | '.join(cells) + ' |', 1)


def self_test(map_text):
    expected, id_to_source = source_ids()
    base = find_problems(map_text, expected, id_to_source)
    if base:
        print('self-test: unmodified map already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1

    rows = {i: _row_line(map_text, i) for i in ('TK-4', 'V6', 'TL0-TK04-T1')}
    if None in rows.values():
        print('self-test: could not find rows to mutate', file=sys.stderr)
        return 1

    tk4_ev = split_row(rows['TK-4'])[2]
    counts_line = next(l for l in map_text.splitlines() if l.startswith(COUNTS_LINE))
    cases = [
        ('removed TK-4 row', map_text.replace(rows['TK-4'] + '\n', '', 1),
         'missing in map: TK-4'),
        ('duplicated TK-4 row', map_text.replace(rows['TK-4'], rows['TK-4'] + '\n' + rows['TK-4'], 1),
         'duplicated in map: TK-4'),
        ('invented id', map_text + '| TK-99 | paraphrase | none | NOT_VERIFIABLE_NO_PACKAGE | no source | n/a |\n',
         'invented id: TK-99'),
        ('dangling path', _with_cell(map_text, 'TK-4', 2, tk4_ev + ' `reference/token_reward/no_such_file.py::x`'),
         'not an allowed evidence path'),
        ('dangling symbol', _with_cell(map_text, 'TK-4', 2, tk4_ev + ' `reference/token_reward/test_reward_model.py::no_such_fn_9f3a`'),
         'is not defined in the file'),
        ('unknown status', _with_cell(map_text, 'TK-4', 3, 'SUFFICIENT'),
         'unknown status'),
        ('uncited row that is not NOT_VERIFIABLE_NO_PACKAGE',
         _with_cell(_with_cell(map_text, 'V1', 2, 'none'), 'V1', 3, 'HARNESS_AUTHOR_SIDE'),
         'has no citation'),
        ('empty missing cell', _with_cell(map_text, 'V1', 4, ''),
         'empty missing-or-open cell'),
        ('owner not in source', _with_cell(map_text, 'V1', 5, 'Nobody Else'),
         'owner'),
        ('stale counts line', map_text.replace(counts_line, counts_line.replace('NOT_VERIFIABLE_NO_PACKAGE=', 'NOT_VERIFIABLE_NO_PACKAGE=99', 1), 1),
         'counts line'),
    ]
    for name, mutated, marker in cases:
        found = find_problems(mutated, expected, id_to_source)
        hit = [item for item in found if marker in item]
        if not hit:
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        print('self-test: detected %s (%s)' % (name, hit[0]))
    print('self-test: pass')
    return 0


def main(argv):
    map_path = ROOT / MAP
    if not map_path.is_file():
        print('missing ' + str(map_path), file=sys.stderr)
        return 1
    map_text = map_path.read_text(encoding='utf-8')
    expected, id_to_source = source_ids()
    if '--self-test' in argv:
        return self_test(map_text)
    problems = find_problems(map_text, expected, id_to_source)
    if problems:
        print('tl predicate evidence map check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    rows = map_rows(map_text)
    by_status = {s: 0 for s in STATUSES}
    cites = 0
    for _, cells in rows:
        by_status[cells[3]] += 1
        cites += len(parse_cell(cells[2]))
    print('tl predicate evidence map ok: rows=%d expected=%d citations=%d %s'
          % (len(rows), len(expected), cites,
             ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
