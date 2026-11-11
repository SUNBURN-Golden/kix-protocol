#!/usr/bin/env python3
"""Check docs/status/CLASS_B_CHARACTERIZATION_INDEX.md using only the stdlib.

The index lists class B (contract-undefined, AGENTS.md §8 B) characterizations
recorded in validation/*/README.md and docs/status/*EVIDENCE_MAP*.md. For each
row this checks that the source path exists and is in scope; the quote appears
byte-for-byte in that source; each cited test symbol is defined in its file
(Python def/class, Rust fn, Move fun, node:test name, following the map
checkers); the contract and owner cells are verbatim substrings of the source;
a superseded status quotes a later record that says so; ids are unique; and the
Counts line matches the table. This is a textual citation check: it does not
classify, review or decide any characterization, and it reads no network.
--self-test uses an in-memory fixture and a temporary-directory reader.
"""
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = 'docs/status/CLASS_B_CHARACTERIZATION_INDEX.md'
HEADER = ['ID', 'Source record', 'Quote', 'Test', 'Contract / clause', 'Owner',
          'Status']
NOT_NAMED = 'not named in source'
UNRESOLVED = 'unresolved: see validation record'
NO_STATUS = 'none'
FORBIDDEN_PREFIX = 'reference/v0.3-rc1/'
MIN_QUOTE = 24
COUNTS = 'Counts:'
COUNT_KEYS = ('rows', 'validation', 'evidence_map', 'test_cited',
              'owner_named', 'superseded')

ID = re.compile(r'CB-\d{3}')
VALIDATION_SOURCE = re.compile(r'validation/[^/]+/README\.md')
MAP_SOURCE = re.compile(r'docs/status/[^/]*EVIDENCE_MAP[^/]*\.md')
LATER_RECORD = re.compile(r'validation/[^/]+/README\.md|docs/status/[^/]+\.md')
PATH_CELL = re.compile(r'`([^`]+)`')
QUOTE_CELL = re.compile(r'"(.*)"')
CITATION = re.compile(r'`([^`]+)::([^`]+)`')
SUPERSEDED = re.compile(r'superseded by #(\d+): `([^`]+)` "(.*)"')
COUNT_TOKEN = re.compile(r'([a-z_]+)=(\d+)')

# Mirrors scripts/check_rs_im_evidence_map.py, without importing it.
TEST_SUFFIX = '.test.mjs'  # symbol is a node:test name, not a text string
DEF_PATTERNS = {
    '.py': r'^\s*(?:(?:async\s+)?def|class)\s+%s\b',
    '.rs': r'^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+%s\b',
    '.move': (r'(?:^|\])\s*(?:public(?:\([a-z]+\))?\s+)?(?:entry\s+)?'
              r'fun\s+%s\b'),
}


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def suffix_of(path):
    return TEST_SUFFIX if path.endswith(TEST_SUFFIX) else Path(path).suffix


def test_named(text, name):
    """True when ``test('name'`` or ``test("name"`` appears."""
    return "test('%s'" % name in text or 'test("%s"' % name in text


def symbol_defined(text, suffix, symbol):
    if suffix == TEST_SUFFIX:
        return test_named(text, symbol)
    pattern = DEF_PATTERNS.get(suffix)
    if pattern is None:
        return False
    parts = symbol.split('.') if suffix == '.py' else [symbol]
    return all(part and re.search(pattern.replace('%s', re.escape(part)),
                                  text, re.M) for part in parts)


def safe_path(path):
    return (bool(path) and not path.startswith('/') and '\\' not in path
            and '..' not in path.split('/')
            and not path.startswith(FORBIDDEN_PREFIX))


def parse_table(text):
    """Return (rows, errors); rows are (line_number, cells)."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines)
              if line.startswith('|') and split_row(line) == HEADER]
    if len(starts) != 1:
        return [], ['malformed table: expected exactly one index header, '
                    'found %d' % len(starts)]
    start = starts[0]
    if start + 1 >= len(lines) or not re.fullmatch(
            r'\|(?:\s*:?-+:?\s*\|)+', lines[start + 1].strip()):
        return [], ['malformed table: header is not followed by a separator']
    rows, errors = [], []
    for number in range(start + 2, len(lines)):
        line = lines[number]
        if not line.startswith('|'):
            break
        cells = split_row(line)
        if len(cells) != len(HEADER):
            errors.append('malformed table: line %d has %d cells'
                          % (number + 1, len(cells)))
            continue
        rows.append((number + 1, cells))
    if not rows and not errors:
        errors.append('malformed table: no rows')
    return rows, errors


def verbatim_parts(cell):
    return [part.strip() for part in cell.split('; ')]


def check_row(cells, read, symbols):
    rid, source_cell, quote_cell, test_cell, contract_cell, owner, status = cells
    errors = []
    where = rid
    match = PATH_CELL.fullmatch(source_cell)
    source = match.group(1) if match else None
    data = read(source) if source and safe_path(source) else None
    if data is None:
        errors.append('missing path: %s: source %s' % (where, source_cell))
        return errors, None
    if not (VALIDATION_SOURCE.fullmatch(source) or MAP_SOURCE.fullmatch(source)):
        errors.append('source out of scope: %s: %s' % (where, source))

    quote = QUOTE_CELL.fullmatch(quote_cell)
    inner = quote.group(1) if quote else None
    if (inner is None or len(inner) < MIN_QUOTE or inner != inner.strip()
            or inner.encode('utf-8') not in data):
        errors.append('quote not in source: %s: %s' % (where, quote_cell))

    if test_cell not in (NOT_NAMED, UNRESOLVED):
        parts = verbatim_parts(test_cell)
        for part in parts:
            cite = CITATION.fullmatch(part)
            if not cite:
                errors.append('unknown symbol: %s: malformed citation %s'
                              % (where, part))
                continue
            path, symbol = cite.group(1).strip(), cite.group(2).strip()
            blob = read(path) if safe_path(path) else None
            if blob is None:
                errors.append('missing path: %s: test %s' % (where, path))
                continue
            if not symbol_defined(blob.decode('utf-8'), suffix_of(path), symbol):
                errors.append('unknown symbol: %s: %s::%s' % (where, path, symbol))
                continue
            symbols.add((path, symbol))

    if contract_cell != NOT_NAMED:
        for part in verbatim_parts(contract_cell):
            if not part or part.encode('utf-8') not in data:
                errors.append('invented contract: %s: %r' % (where, part))
    if owner != NOT_NAMED and (not owner or owner.encode('utf-8') not in data):
        errors.append('invented owner: %s: %r' % (where, owner))

    if status != NO_STATUS:
        sup = SUPERSEDED.fullmatch(status)
        if not sup:
            errors.append('invented status: %s: %r' % (where, status))
        else:
            pr, later, said = sup.groups()
            later_data = read(later) if safe_path(later) else None
            if later_data is None:
                errors.append('missing path: %s: superseding %s' % (where, later))
            elif not LATER_RECORD.fullmatch(later) or later == source:
                errors.append('invented status: %s: superseding record %s is '
                              'not a later record' % (where, later))
            elif (len(said) < MIN_QUOTE or 'supersed' not in said.lower()
                  or said.encode('utf-8') not in later_data
                  or ('#' + pr).encode('utf-8') not in later_data):
                errors.append('invented status: %s: %s does not say so with #%s'
                              % (where, later, pr))
    return errors, source


def find_problems(index_text, read):
    """Return sorted problem strings; empty means the index passes.

    ``read(path)`` returns the bytes of a repo-relative path, or None.
    """
    rows, errors = parse_table(index_text)
    seen = set()
    symbols = set()
    sources = []
    tally = dict.fromkeys(COUNT_KEYS, 0)
    for _, cells in rows:
        rid = cells[0]
        if not ID.fullmatch(rid):
            errors.append('bad id: %r' % rid)
        elif rid in seen:
            errors.append('duplicate id: %s' % rid)
        seen.add(rid)
        row_errors, source = check_row(cells, read, symbols)
        errors.extend(row_errors)
        tally['rows'] += 1
        if source and VALIDATION_SOURCE.fullmatch(source):
            tally['validation'] += 1
        elif source and MAP_SOURCE.fullmatch(source):
            tally['evidence_map'] += 1
        if source:
            sources.append(source)
        tally['test_cited'] += cells[3] not in (NOT_NAMED, UNRESOLVED)
        tally['owner_named'] += cells[5] != NOT_NAMED
        tally['superseded'] += cells[6] != NO_STATUS

    counts = [line for line in index_text.splitlines() if line.startswith(COUNTS)]
    if len(counts) != 1:
        errors.append('counts mismatch: expected one Counts line, found %d'
                      % len(counts))
    else:
        tokens = COUNT_TOKEN.findall(counts[0][len(COUNTS):])
        expected = [(key, str(tally[key])) for key in COUNT_KEYS]
        if tokens != expected:
            errors.append('counts mismatch: %r, computed %s' % (
                counts[0], ' '.join('%s=%s' % pair for pair in expected)))
    return sorted(errors), len(rows), len(set(sources)), len(symbols)


def make_reader(root):
    root = Path(root).resolve()

    def read(path):
        target = (root / path).resolve()
        if root not in target.parents or not target.is_file():
            return None
        return target.read_bytes()
    return read


def self_test():
    files = {
        'validation/2026-01-01-a/README.md':
            'Class B: the widget reports zero when the queue is empty.\n'
            'Owner: User. Contract §4.2 does not say.\n',
        'validation/2026-01-02-b/README.md':
            'The widget item is superseded by #12 and the new contract text.\n',
        'docs/status/X_EVIDENCE_MAP.md':
            '- class B: a cut on a frame boundary is undetectable (Astra).\n',
        'docs/status/OTHER.md': 'Class B: an out-of-scope source line here.\n',
        'pkg/test_x.py': 'class WidgetTests:\n    def test_empty(self):\n'
                         '        pass\n',
        'pkg/tests/x.rs': '#[test]\nfn frame_cut_is_silent() {}\n',
        'pkg/sources/x.move': '#[test]\nfun widget_aborts() {}\n',
        'pkg/x.test.mjs': "test('widget is stable', () => {});\n",
    }
    blobs = {path: text.encode('utf-8') for path, text in files.items()}

    def read(path):
        return blobs.get(path)

    head = ('| ' + ' | '.join(HEADER) + ' |\n'
            '|' + '---|' * len(HEADER) + '\n')
    rows = [
        '| CB-001 | `validation/2026-01-01-a/README.md` | "the widget reports '
        'zero when the queue is empty" | `pkg/test_x.py::WidgetTests.test_empty`'
        '; `pkg/sources/x.move::widget_aborts`; `pkg/x.test.mjs::widget is '
        'stable` | §4.2 | User | superseded by #12: '
        '`validation/2026-01-02-b/README.md` "The widget item is superseded '
        'by #12" |',
        '| CB-002 | `docs/status/X_EVIDENCE_MAP.md` | "a cut on a frame boundary '
        'is undetectable" | `pkg/tests/x.rs::frame_cut_is_silent` | '
        'not named in source | Astra | none |',
        '| CB-003 | `docs/status/X_EVIDENCE_MAP.md` | "class B: a cut on a frame '
        'boundary" | unresolved: see validation record | not named in source '
        '| not named in source | none |',
    ]
    counts = ('Counts: rows=3 validation=1 evidence_map=2 test_cited=2 '
              'owner_named=2 superseded=1\n')

    def index(table_rows, counts_line=counts, header=head):
        return '# Index\n\n' + header + '\n'.join(table_rows) + '\n\n' + counts_line

    problems = find_problems(index(rows), read)[0]
    if problems:
        print('self-test FAIL: baseline has problems: %s' % problems)
        return 1

    def swap(i, old, new):
        changed = list(rows)
        assert old in changed[i], old
        changed[i] = changed[i].replace(old, new)
        return index(changed)

    cases = [
        ('missing path', swap(1, 'X_EVIDENCE_MAP', 'Y_EVIDENCE_MAP'),
         'missing path:'),
        ('missing test path', swap(1, 'pkg/tests/x.rs', 'pkg/tests/y.rs'),
         'missing path:'),
        ('altered quote', swap(1, 'is undetectable', 'is detectable'),
         'quote not in source:'),
        ('short quote', swap(2, '"class B: a cut on a frame boundary"',
                             '"class B: a cut"'), 'quote not in source:'),
        ('piped quote', swap(1, 'frame boundary is', 'frame | boundary is'),
         'malformed table:'),
        ('unknown symbol', swap(1, 'frame_cut_is_silent', 'frame_cut_is_loud'),
         'unknown symbol:'),
        ('unknown dotted part', swap(0, 'WidgetTests.test_empty',
                                     'WidgetTests.test_full'), 'unknown symbol:'),
        ('unknown node:test name', swap(0, 'widget is stable', 'widget is new'),
         'unknown symbol:'),
        ('duplicate id', swap(1, 'CB-002', 'CB-001'), 'duplicate id:'),
        ('bad id', swap(1, 'CB-002', 'CB-2'), 'bad id:'),
        ('wrong count', index(rows, counts.replace('rows=3', 'rows=4')),
         'counts mismatch:'),
        ('missing count token', index(rows, counts.replace(' superseded=1', '')),
         'counts mismatch:'),
        ('two counts lines', index(rows, counts + counts), 'counts mismatch:'),
        ('invented owner', swap(1, '| Astra |', '| Platform team |'),
         'invented owner:'),
        ('invented contract', swap(0, '| §4.2 |', '| §9.9 |'),
         'invented contract:'),
        ('out-of-scope source', swap(2, 'X_EVIDENCE_MAP.md` | "class B: a cut on'
                                     ' a frame boundary"',
                                     'OTHER.md` | "Class B: an out-of-scope '
                                     'source line"'), 'source out of scope:'),
        ('invented status', swap(1, '| none |', '| resolved |'),
         'invented status:'),
        ('superseded without supersession quote',
         swap(0, '"The widget item is superseded by #12"',
              '"and the new contract text."'), 'invented status:'),
        ('superseded with wrong PR', swap(0, '#12:', '#13:'), 'invented status:'),
        ('wrong header', index(rows, header=head.replace('| Owner |',
                                                         '| Steward |')),
         'malformed table:'),
    ]
    for name, text, marker in cases:
        found = find_problems(text, read)[0]
        if not any(p.startswith(marker) for p in found):
            print('self-test FAIL: %s not detected (%s); got %s'
                  % (name, marker, found))
            return 1
        print('self-test: detected %s' % name)

    with tempfile.TemporaryDirectory() as tmp:
        for path, blob in blobs.items():
            target = Path(tmp) / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
        (Path(tmp) / 'pkg' / 'dir.py').mkdir()
        disk = make_reader(tmp)
        if find_problems(index(rows), disk)[0]:
            print('self-test FAIL: temporary-directory reader rejects baseline')
            return 1
        if disk('pkg/dir.py') is not None or disk('../outside.md') is not None:
            print('self-test FAIL: reader follows a directory or escapes root')
            return 1
    print('self-test: pass (%d negative controls)' % len(cases))
    return 0


def main(argv):
    if argv == ['--self-test']:
        return self_test()
    if argv:
        print('usage: check_class_b_index.py [--self-test]')
        return 2
    read = make_reader(ROOT)
    text = read(INDEX)
    if text is None:
        print('missing path: %s' % INDEX)
        return 1
    problems, rows, sources, symbols = find_problems(text.decode('utf-8'), read)
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print('class B index ok: rows=%d sources=%d symbols=%d; textual index only'
          % (rows, sources, symbols))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
