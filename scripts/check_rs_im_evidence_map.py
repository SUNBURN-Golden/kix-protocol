#!/usr/bin/env python3
"""Check the RS impact-table evidence map against the profile and the cited sources.

Compares two inputs:

- ``docs/contracts/RIGHTS_SCALE_PROFILE.md``: the impact table of section 12,
  rows IM-01..IM-30 with three cells (id, treatment word, policy sentence).
- ``docs/status/RS_IM_EVIDENCE_MAP.md``: the builder-authored map, one row per
  id, eleven cells per row (id, treatment word, paraphrase, Move tests, Python
  model tests, Rust tests, localnet script or validation record,
  unchanged-file evidence, status, missing or open, owner).

Checks, each reported on failure:

1. Ids. The profile ids equal the map first cells, each exactly once; missing,
   duplicated, extra and not-in-profile ids are reported. Each row has eleven
   cells.
2. Treatment. Cell 2 equals the profile treatment cell and is one of the four
   profile words.
3. Status. It is one of COVERED_LOCALNET, COVERED_MODEL_OR_MEMORY, PARTIAL,
   NOT_COVERED, MEASUREMENT_ONLY, UNCHANGED_BY_DESIGN and agrees with the
   citations: NOT_COVERED carries no citation, every other status carries at
   least one; a covered status needs a Move, Python or Rust citation;
   COVERED_LOCALNET needs a localnet citation; UNCHANGED_BY_DESIGN needs the
   treatment word for "untouched" and an unchanged-file citation, and a row
   with that treatment is never COVERED_*; MEASUREMENT_ONLY names RS-4 as
   owner. A PARTIAL, NOT_COVERED or MEASUREMENT_ONLY row has a missing sentence
   other than ``none`` and an owner. The impact table has no owner column, so
   each ``;``-separated owner part is a substring of the profile or the
   reserved literal ``none stated in profile``.
4. Citations. A citation is ``path::symbol`` in backticks. Each path exists, is
   repo-relative, lies under its column's allowed patterns and is never under
   ``reference/v0.3-rc1/``. A symbol is a defined ``fun``/``struct``/``const``
   (Move), ``def``/``class``/module constant (Python) or ``fn``/``const``
   (Rust) in the cited file; for ``.mjs``, ``.json``, ``.md`` and ``.yml`` it
   must appear as text.
5. Counts. The ``Counts:`` line equals the statuses recomputed from the table.
6. Supplemental offline evidence. Section 5 has its own five-column table,
   identifiers and exact path allowlist. IM ids refer to the profile; test
   symbols are complete literal top-level test names and record anchors are
   whole Markdown heading lines. These citations never contribute to primary
   statuses, counts or localnet requirements.

Standard library only. Convenience check, not a contract gate. It reads the
cited files as text and executes none of them; it proves that a cited name
exists, not that the test asserts the predicate. ``--self-test`` mutates
in-memory copies of the map and requires each break to be caught.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/RS_IM_EVIDENCE_MAP.md'
PROFILE = 'docs/contracts/RIGHTS_SCALE_PROFILE.md'

STATUSES = ('COVERED_LOCALNET', 'COVERED_MODEL_OR_MEMORY', 'PARTIAL',
            'NOT_COVERED', 'MEASUREMENT_ONLY', 'UNCHANGED_BY_DESIGN')
NEEDS_MISSING = ('PARTIAL', 'NOT_COVERED', 'MEASUREMENT_ONLY')
TREATMENTS = ('유지', '변경', '새 프로파일', '손대지 않음')
UNTOUCHED = '손대지 않음'
NO_OWNER = 'none stated in profile'
CELLS = 11
STATUS_CELL, MISSING_CELL, OWNER_CELL = 8, 9, 10
# column index -> (name, allowed path patterns)
COLUMNS = {
    3: ('move', (r'reference/rights_scale/sui/tests/[a-z_]+\.move',)),
    4: ('python', (r'reference/(?:rights_scale|booking_resale_admission)/test_[a-z_]+\.py',)),
    5: ('rust', (r'runtime/crates/(?:kix-delegated-exec|kix-kernel-v5)/tests/[a-z0-9_]+\.rs',)),
    6: ('local', (r'reference/rights_scale/client/[a-z0-9-]+\.mjs',
                  r'reference/rights_scale/vectors/[a-z_]+\.json',
                  r'scripts/run_[a-z0-9_]*rights_scale[a-z0-9_]*\.py',
                  r'validation/2026-10-1[0-9]-[a-z0-9-]+/[A-Za-z0-9._-]+')),
    7: ('unchanged', (r'runtime/crates/kix-kernel/(?:src/lib|tests/[a-z0-9_]+)\.rs',
                      r'runtime/crates/kix-kernel-v5/src/lib\.rs',
                      r'reference/booking_resale_admission/[a-z_]+\.py',
                      r'docs/contracts/[A-Z0-9_]+\.md',
                      r'docs/[A-Z0-9_]+\.md',
                      r'\.github/workflows/[a-z-]+\.yml')),
}
FORBIDDEN_PREFIX = 'reference/v0.3-rc1/'
TEXT_SUFFIXES = ('.mjs', '.json', '.md', '.yml')
SUPPLEMENTAL_SECTION = '## 5. Supplemental offline evidence'
SUPPLEMENTAL_HEADER = ['Supplemental ID', 'IM IDs', 'Offline tests',
                       'Validation records', 'Scope and limitations']
OFFLINE_TEST_PATHS = (
    'reference/rights_scale/client/witness-reconstruction.test.mjs',
    'reference/rights_scale/client/spend-witness.test.mjs',
)
OFFLINE_RECORD_PATHS = (
    'validation/2026-10-21-plan-rs-witness-offline-regressions/README.md',
    'validation/2026-10-21-plan-rs-witness-ci-wiring/README.md',
    'validation/2026-10-21-plan-rs-spend-witness-offline-tests/README.md',
)
SUPPLEMENTAL_IDS = {'RS-OFFLINE-01': ('IM-19',),
                    'RS-OFFLINE-02': ('IM-14',),
                    'RS-OFFLINE-03': ('IM-15',)}

ID_CELL = re.compile(r'^\|\s*(IM-\d\d)\s*\|')
CITATION = re.compile(r'`([^`]+)`')
STATUS_WORD = re.compile(r'[A-Z_]+')
COUNTS_LINE = 'Counts:'

DEF_PATTERNS = {
    '.py': r'^\s*(?:(?:async\s+)?def|class)\s+%s\b|^%s\s*=',
    '.rs': r'^\s*(?:pub(?:\([^)]*\))?\s+)?(?:fn|struct|enum|const)\s+%s\b',
    '.move': (r'(?:^|\])\s*(?:public(?:\([a-z]+\))?\s+)?(?:entry\s+)?'
              r'(?:fun|struct|const)\s+%s\b'),
}


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def profile_rows(profile_text):
    """Return {id: treatment_cell} from the three-cell impact table rows."""
    rows = {}
    for line in profile_text.splitlines():
        match = ID_CELL.match(line)
        if not match:
            continue
        cells = split_row(line)
        if len(cells) == 3:
            rows[match.group(1)] = cells[1]
    return rows


def map_rows(map_text):
    return [(m.group(1), split_row(line)) for line in map_text.splitlines()
            for m in [ID_CELL.match(line)] if m]


def parse_cell(cell):
    """Return [(path, symbol_or_None), ...] for the backticked citations."""
    out = []
    for match in CITATION.finditer(cell):
        path, _, symbol = match.group(1).partition('::')
        out.append((path.strip(), symbol.strip() or None))
    return out


def symbol_defined(text, suffix, symbol):
    if suffix in TEXT_SUFFIXES:
        return symbol in text
    pattern = DEF_PATTERNS.get(suffix)
    if pattern is None:
        return False
    return re.search(pattern.replace('%s', re.escape(symbol)), text, re.M) is not None


def literal_test_names(text):
    """Recognize direct top-level test('literal', ...) statements, without JS.

    Bounded lexer for the cited suites, not a JavaScript parser. Initial hashbangs,
    comments, strings, non-interpolated templates and expression-position regex
    literals are opaque. Template interpolation is unsupported and fails closed
    for the whole source. Outside the explicit regex-opener contexts, a second
    slash on the same line makes regex/division ambiguous: fail closed for the whole source.
    A lone slash on its line cannot open a valid regex and remains division.
    Names support plain single/double quotes and escaped quotes/backslashes;
    computed names, other escapes, nested calls and test modifiers are outside
    this grammar. A name must be the complete first argument, followed by a
    comma. No cited source or dependency is imported or executed.
    """
    token = re.compile(
        r'(?P<space>\s+)|(?P<comment>\A#![^\r\n\u2028\u2029]*|//[^\n]*|/\*[\s\S]*?\*/)|'
        r'''(?P<string>'(?:\\[\s\S]|[^'\\\r\n])*'|"(?:\\[\s\S]|[^"\\\r\n])*")|'''
        r'(?P<template>`(?:\\[\s\S]|[^`\\$]|\$(?!\{))*`)|'
        r'(?P<word>[A-Za-z_$][\w$]*)|(?P<punct>=>|\?\.|[^\s])')
    regex_literal = re.compile(r'/((?:\\[^\r\n]|\[(?:\\.|[^\]\\\r\n])*\]|[^/\\\[\r\n])+)/[a-z]*')
    tokens = []
    pos = 0
    while pos < len(text):
        match = token.match(text, pos)
        if not match:
            return set()  # Unsupported/unterminated input: fail closed.
        kind, value = match.lastgroup, match.group()
        if kind == 'punct' and value in ("'", '"', '`'):
            return set()  # Unterminated literal.
        if value == '/':
            if tokens and tokens[-1][1] not in (
                    '(', '[', '=', ',', ':', 'return', '=>', '!', '?'):
                # A slash may start a regex even after an unsupported token
                # (e.g. the second pipe in ||). Never expose its body as code.
                # Regex literals cannot cross a physical line terminator.
                if '/' in re.match(r'[^\r\n\u2028\u2029]*', text[pos + 1:]).group():
                    return set()
            else:
                regex = regex_literal.match(text, pos)
                if not regex:
                    return set()
                tokens.append(('regex', regex.group()))
                pos = regex.end()
                continue
        pos = match.end()
        if kind not in ('space', 'comment'):
            tokens.append((kind, value))

    names = set()
    stack = []
    for i, (kind, value) in enumerate(tokens):
        if (not stack and kind == 'word' and value == 'test'
                and (i == 0 or tokens[i - 1][1] in (';', '}'))
                and i + 3 < len(tokens) and tokens[i + 1][1] == '('
                and tokens[i + 2][0] == 'string' and tokens[i + 3][1] == ','):
            literal = tokens[i + 2][1][1:-1]
            if re.fullmatch(r'''(?:[^\\]|\\[\\'"])*''', literal):
                names.add(re.sub(r'''\\([\\'"])''', r'\1', literal))
        if kind != 'punct':
            continue
        if value in ('(', '[', '{'):
            stack.append(value)
        elif value in (')', ']', '}'):
            if not stack or stack.pop() != {')': '(', ']': '[', '}': '{'}[value]:
                return set()
    return names if not stack else set()


def supplemental_rows(map_text):
    """Return (rows, problems) for the designated section only."""
    lines = map_text.splitlines()
    starts = [i for i, line in enumerate(lines) if line == SUPPLEMENTAL_SECTION]
    if len(starts) != 1:
        return [], ['supplemental section: expected exactly one, found %d' % len(starts)]
    start = starts[0] + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith('## ')), len(lines))
    table = [line for line in lines[start:end] if line.lstrip().startswith('|')]
    problems = []
    if not table or split_row(table[0]) != SUPPLEMENTAL_HEADER:
        problems.append('supplemental table: missing or malformed header')
    if len(table) < 2 or len(split_row(table[1])) != 5 or not all(
            re.fullmatch(r':?-{3,}:?', cell) for cell in split_row(table[1])):
        problems.append('supplemental table: missing or malformed separator')
    rows = []
    for line in table[2:]:
        cells = split_row(line)
        ident = cells[0]
        if not line.rstrip().endswith('|') or len(cells) != 5:
            problems.append('%s: supplemental expected 5 cells, found %d' % (ident, len(cells)))
            continue
        rows.append((ident, cells))
    # A damaged row must not disappear just because its opening pipe was lost.
    for line in lines[start:end]:
        if line.lstrip().startswith('RS-OFFLINE-'):
            problems.append('supplemental table: malformed row: %s' % line)
    return rows, problems


def find_supplemental_problems(map_text, expected, root, read):
    rows, problems = supplemental_rows(map_text)
    seen = set()
    for ident, cells in rows:
        if ident in seen:
            problems.append('%s: duplicate supplemental identifier' % ident)
        seen.add(ident)
        if ident not in SUPPLEMENTAL_IDS:
            problems.append('%s: unknown supplemental identifier' % ident)
        im_ids = tuple(part.strip() for part in cells[1].split(','))
        for im_id in im_ids:
            if im_id not in expected:
                problems.append('%s: unknown IM identifier: %s' % (ident, im_id))
        if ident in SUPPLEMENTAL_IDS and im_ids != SUPPLEMENTAL_IDS[ident]:
            problems.append('%s: expected IM IDs: %s' % (ident, ', '.join(SUPPLEMENTAL_IDS[ident])))
        if not cells[4]:
            problems.append('%s: empty scope and limitations' % ident)
        for col, name, allowed in ((2, 'offline tests', OFFLINE_TEST_PATHS),
                                   (3, 'validation records', OFFLINE_RECORD_PATHS)):
            cell = cells[col]
            # Validate all members, even when valid citations surround bad text.
            if not re.fullmatch(r'`[^`]+`(?:\s*,\s*`[^`]+`)*', cell):
                problems.append('%s: %s cell needs comma-separated backticked citations' % (ident, name))
            for path, symbol in parse_cell(cell):
                where = '%s: %s citation %s' % (ident, name, path)
                if (not path or path.startswith('/') or '\\' in path
                        or '..' in path.split('/') or re.match(r'^[A-Za-z][\w+.-]*:', path)):
                    problems.append('%s is not repo-relative (absolute, traversal, backslash or URL)' % where)
                    continue
                if path == FORBIDDEN_PREFIX.rstrip('/') or path.startswith(FORBIDDEN_PREFIX):
                    problems.append('%s is under reference/v0.3-rc1' % where)
                    continue
                if path not in allowed:
                    problems.append('%s is outside the supplemental %s paths' % (where, name))
                    continue
                try:
                    target = (root / path).resolve()
                    target.relative_to(root.resolve())
                    if target.is_relative_to((root / FORBIDDEN_PREFIX).resolve()):
                        problems.append('%s resolves under reference/v0.3-rc1' % where)
                        continue
                except (ValueError, OSError, RuntimeError):
                    problems.append('%s resolves outside the repository or cannot be resolved' % where)
                    continue
                text = read(path)
                if text is None:
                    problems.append('%s does not exist' % where)
                elif symbol is None:
                    problems.append('%s needs a ::symbol' % where)
                elif col == 2 and symbol not in literal_test_names(text):
                    problems.append('%s::%s: test name not declared' % (where, symbol))
                elif col == 3 and (not re.fullmatch(r'#{1,6} .+', symbol)
                                   or symbol not in text.splitlines()):
                    problems.append('%s::%s: record anchor not found' % (where, symbol))
    for ident in SUPPLEMENTAL_IDS:
        if ident not in seen:
            problems.append('missing supplemental identifier: %s' % ident)
    return problems


def find_problems(map_text, profile_text, root=ROOT, files=None):
    """Return a list of problem strings; empty means the map passes.

    ``files`` optionally maps a repo-relative path to replacement text.
    """
    files = files or {}
    problems = []
    cache = {}

    def read(path):
        if path in files:
            return files[path]
        if path not in cache:
            target = root / path
            cache[path] = (target.read_text(encoding='utf-8')
                           if target.is_file() else None)
        return cache[path]

    expected = profile_rows(profile_text)
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
            problems.append('not in profile section 12: %s' % ident)

    seen = set()
    by_status = {s: 0 for s in STATUSES}
    for ident, cells in rows:
        if ident in seen:
            continue
        seen.add(ident)
        if len(cells) != CELLS:
            problems.append('%s: expected %d cells, found %d' % (ident, CELLS, len(cells)))
            continue
        treatment = cells[1]
        if treatment not in TREATMENTS:
            problems.append('%s: treatment %r is not one of the profile words' % (ident, treatment))
        if ident in expected and treatment != expected[ident]:
            problems.append('%s: treatment %r differs from the profile %r'
                            % (ident, treatment, expected[ident]))
        if not cells[2]:
            problems.append('%s: empty paraphrase' % ident)

        status_cell = cells[STATUS_CELL]
        match = STATUS_WORD.fullmatch(status_cell)
        status = match.group(0) if match else ''
        if status not in STATUSES:
            problems.append('%s: unknown status %r' % (ident, status_cell))
        else:
            by_status[status] += 1

        parsed = {}
        total = 0
        for col, (name, patterns) in COLUMNS.items():
            cell = cells[col]
            cites = parse_cell(cell)
            if not cites and cell != 'none':
                problems.append('%s: %s cell is neither none nor a citation' % (ident, name))
            parsed[name] = cites
            total += len(cites)
            for path, symbol in cites:
                where = '%s: %s citation %s' % (ident, name, path)
                if path.startswith('/') or '..' in path.split('/'):
                    problems.append('%s is not repo-relative' % where)
                    continue
                if path.startswith(FORBIDDEN_PREFIX):
                    problems.append('%s is under reference/v0.3-rc1' % where)
                    continue
                if not any(re.fullmatch(p, path) for p in patterns):
                    problems.append('%s is outside the %s column paths' % (where, name))
                text = read(path)
                if text is None:
                    problems.append('%s does not exist' % where)
                    continue
                if symbol is None:
                    problems.append('%s needs a ::symbol' % where)
                elif not symbol_defined(text, Path(path).suffix, symbol):
                    problems.append('%s::%s is not defined in the file' % (where, symbol))

        if status == 'NOT_COVERED' and total:
            problems.append('%s: NOT_COVERED row carries a citation' % ident)
        elif status in STATUSES and status != 'NOT_COVERED' and not total:
            problems.append('%s: %s row has no citation, so it must be NOT_COVERED'
                            % (ident, status))
        if status in ('COVERED_LOCALNET', 'COVERED_MODEL_OR_MEMORY') and not (
                parsed['move'] or parsed['python'] or parsed['rust']):
            problems.append('%s: %s needs a Move, Python or Rust citation' % (ident, status))
        if status == 'COVERED_LOCALNET' and not parsed['local']:
            problems.append('%s: COVERED_LOCALNET needs a localnet citation' % ident)
        if status == 'UNCHANGED_BY_DESIGN':
            if treatment != UNTOUCHED:
                problems.append('%s: UNCHANGED_BY_DESIGN is only for %s rows' % (ident, UNTOUCHED))
            if not parsed['unchanged']:
                problems.append('%s: UNCHANGED_BY_DESIGN needs an unchanged-file citation' % ident)
        if treatment == UNTOUCHED and status in ('COVERED_LOCALNET', 'COVERED_MODEL_OR_MEMORY'):
            problems.append('%s: a %s row is never %s' % (ident, UNTOUCHED, status))
        if status == 'MEASUREMENT_ONLY' and 'RS-4' not in cells[OWNER_CELL]:
            problems.append('%s: MEASUREMENT_ONLY must name RS-4 as owner' % ident)
        if not cells[MISSING_CELL]:
            problems.append('%s: empty missing-or-open cell' % ident)
        elif status in NEEDS_MISSING and cells[MISSING_CELL].lower().startswith('none'):
            problems.append('%s: %s row must say what is missing' % (ident, status))
        if status in NEEDS_MISSING:
            for part in (p.strip() for p in cells[OWNER_CELL].split(';')):
                if part != NO_OWNER and (not part or part not in profile_text):
                    problems.append('%s: owner part %r is not written in the profile' % (ident, part))

    lines = [l for l in map_text.splitlines() if l.startswith(COUNTS_LINE)]
    want = COUNTS_LINE + ' ' + ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)
    if len(lines) != 1:
        problems.append('%r line appears %d times' % (COUNTS_LINE, len(lines)))
    elif lines[0].strip() != want:
        problems.append('counts line %r differs from the table %r' % (lines[0].strip(), want))
    problems.extend(find_supplemental_problems(map_text, expected, root, read))
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


def _with_cells(text, ident, changes):
    for col, new in changes:
        text = _with_cell(text, ident, col, new)
    return text


def supplemental_self_test(map_text, profile_text):
    """Positive fixtures and mutations stay in memory; assert each diagnostic."""
    probe = r'''
// test('comment only', () => {});
/* test('block comment only', () => {}); */
const unrelated = "test('string only', () => {})";
const template = `test('template only', () => {})`;
const escapedInterpolation = `\${;test('escaped interpolation only', x);}`;
const escapedBacktick = `\`;test('escaped backtick only', x);`;
const dollars = `$ $word test('dollar template only', x);`;
const pattern = /test\('regex only', [}]/;
const opaque = /;test('assignment regex ghost', x);/;
const fallback = null ?? /;test('nullish regex ghost', x);/;
const ratio = Math.floor(index / 2);
function nested() { test('nested only', () => {}); }
other.test('property only', () => {});
test('computed' + suffix, () => {});
test(`template name`, () => {});
test('valid reconstruction', () => { test('callback only', () => {}); });
test("valid spend", () => {});
test('escaped \'quote\' and \\ slash', () => {});
'''
    want = {'valid reconstruction', 'valid spend', "escaped 'quote' and \\ slash"}
    if literal_test_names(probe) != want:
        print('self-test: bounded test-name recognizer failed positive/negative controls', file=sys.stderr)
        return 1
    for broken in ("test('unterminated", "test('x', () => {", "test('x', () => {}]);"):
        if literal_test_names(broken):
            print('self-test: malformed source accepted', file=sys.stderr)
            return 1
    rows = [
        ['RS-OFFLINE-01', 'IM-19', '`%s::valid reconstruction`' % OFFLINE_TEST_PATHS[0],
         '`%s::## Reconstruction`' % OFFLINE_RECORD_PATHS[0]
         + ', `%s::## Wiring`' % OFFLINE_RECORD_PATHS[1], 'synthetic only'],
        ['RS-OFFLINE-02', 'IM-14', '`%s::valid spend`' % OFFLINE_TEST_PATHS[1],
         '`%s::## Spend`' % OFFLINE_RECORD_PATHS[2], 'synthetic only'],
        ['RS-OFFLINE-03', 'IM-15', '`%s::valid spend`' % OFFLINE_TEST_PATHS[1],
         '`%s::## Spend`' % OFFLINE_RECORD_PATHS[2], 'synthetic only'],
    ]
    def render(cells):
        return '| ' + ' | '.join(cells) + ' |'

    prefix = map_text.split(SUPPLEMENTAL_SECTION)[0]
    fixture = prefix + SUPPLEMENTAL_SECTION + '\n\n' + render(SUPPLEMENTAL_HEADER) + '\n'
    fixture += '|---|---|---|---|---|\n' + '\n'.join(render(row) for row in rows) + '\n'
    files = {path: probe for path in OFFLINE_TEST_PATHS}
    files.update(dict(zip(OFFLINE_RECORD_PATHS,
                          ('## Reconstruction\n', '## Wiring\n', '## Spend\n'))))
    found = find_problems(fixture, profile_text, files=files)
    if found or map_rows(fixture) != map_rows(map_text):
        print('self-test: supplemental positive fixture failed: %r' % found, file=sys.stderr)
        return 1
    print('self-test: supplemental positive fixture accepted; primary rows/counts unchanged')

    def cell(col, new):
        changed = rows[0][:]
        changed[col] = new
        return fixture.replace(render(rows[0]), render(changed), 1)

    path = OFFLINE_TEST_PATHS[0]
    where = 'RS-OFFLINE-01: offline tests citation ' + path
    record = OFFLINE_RECORD_PATHS[0]
    cases = [
        ('missing section', prefix, {}, 'supplemental section: expected exactly one, found 0'),
        ('duplicate section', fixture + '\n' + SUPPLEMENTAL_SECTION, {}, 'found 2'),
        ('missing identifier', fixture.replace(render(rows[0]) + '\n', ''), {},
         'missing supplemental identifier: RS-OFFLINE-01'),
        ('duplicate identifier', fixture + render(rows[0]) + '\n', {},
         'RS-OFFLINE-01: duplicate supplemental identifier'),
        ('unknown supplemental ID', cell(0, 'RS-OFFLINE-99'), {}, 'unknown supplemental identifier'),
        ('unknown IM', cell(1, 'IM-99'), {}, 'unknown IM identifier: IM-99'),
        ('wrong IM association', cell(1, 'IM-14'), {}, 'RS-OFFLINE-01: expected IM IDs: IM-19'),
        ('missing file', fixture, {path: None}, where + ' does not exist'),
        ('missing record', fixture, {record: None}, 'validation records citation ' + record + ' does not exist'),
        ('missing anchor', fixture, {record: '## Other\n'}, 'record anchor not found'),
        ('heading substring', fixture, {record: '## Reconstruction extra\n'}, 'record anchor not found'),
        ('heading in prose', fixture, {record: 'prose ## Reconstruction\n'}, 'record anchor not found'),
        ('empty limitations', cell(4, ''), {}, 'empty scope and limitations'),
        ('empty citations', cell(2, ''), {}, 'needs comma-separated backticked citations'),
        ('missing symbol', cell(2, '`%s`' % path), {}, where + ' needs a ::symbol'),
        ('bad width', fixture.replace(render(rows[0]), render(rows[0]) + ' extra |'), {},
         'supplemental expected 5 cells, found 6'),
        ('missing opening pipe', fixture.replace(render(rows[0]), render(rows[0])[2:]), {}, 'malformed row'),
        ('bad header', fixture.replace('Supplemental ID |', 'Wrong ID |'), {}, 'malformed header'),
        ('bad separator', fixture.replace('|---|---|---|---|---|', '|---|oops|---|---|---|'), {},
         'malformed separator'),
        ('localnet isolation', _with_cell(fixture, 'IM-15', 6, 'none'), {},
         'IM-15: COVERED_LOCALNET needs a localnet citation'),
    ]
    # An initial hashbang is a comment through EOF or the first JS line terminator.
    for ending in ('', '\n', '\r', '\r\n', '\u2028', '\u2029'):
        source = "#!node;test('ghost', x);" + ending
        if ending:
            source += "test('valid reconstruction', () => {});"
            found = find_problems(fixture, profile_text, files={**files, path: source})
            if found:
                print('self-test: real test after hashbang rejected: %r' % found, file=sys.stderr)
                return 1
        cases.append(('hashbang comment ending ' + repr(ending),
                      cell(2, '`%s::ghost`' % path), {path: source},
                      where + '::ghost: test name not declared'))
    # Interpolations are outside the bounded template grammar. In particular,
    # an inner backtick must never expose template contents as declarations.
    for name, source in (
            ('reviewer nested template', "const text = `${`;test('ghost', x);`}`;"),
            ('interpolated call', "const text = `${test('ghost', x)}`;"),
            ('deeper nested template', "const text = `${`${`;test('ghost', x);`}`}`;"),
            ('escaped backslash before interpolation', r"const text = `\\${`;test('ghost', x);`}`;")):
        for suffix in ('', "\ntest('valid reconstruction', () => {});"):
            rejected = source + suffix
            if literal_test_names(rejected):
                print('self-test: unsupported template interpolation accepted: %s' % name,
                      file=sys.stderr)
                return 1
            cases.append((name + (' with real test' if suffix else ''),
                          cell(2, '`%s::ghost`' % path), {path: rejected},
                          where + '::ghost: test name not declared'))
    # These contexts are deliberately outside the bounded regex grammar. The
    # entire source must fail closed, including otherwise supported test calls.
    for context in ('false || ', 'true && ', '0 | ', '0 & ', '0 ^ '):
        source = "const pattern = %s/;test('ghost', x);/;" % context
        source += "\ntest('valid reconstruction', () => {});"
        if literal_test_names(source):
            print('self-test: unsupported regex context accepted: %r' % context, file=sys.stderr)
            return 1
        cases.append(('opaque regex after ' + repr(context), cell(2, '`%s::ghost`' % path),
                      {path: source}, where + '::ghost: test name not declared'))
    for name in ('absent', 'valid', 'comment only', 'block comment only', 'string only',
                 'template only', 'escaped interpolation only', 'escaped backtick only',
                 'dollar template only', 'regex only', 'assignment regex ghost', 'nullish regex ghost', 'nested only',
                 'callback only', 'property only', 'computed'):
        cases.append(('undeclared ' + name, cell(2, '`%s::%s`' % (path, name)), {},
                      where + '::' + name + ': test name not declared'))
    # The spend record abbreviates this name; only the full declaration counts.
    cases.append(('short spend name', cell(2, '`%s::domain_mismatch`' % OFFLINE_TEST_PATHS[1]),
                  {OFFLINE_TEST_PATHS[1]: "test('domain_mismatch: full name', () => {});"},
                  '::domain_mismatch: test name not declared'))
    for bad in ('../outside.test.mjs', '/tmp/outside.test.mjs', 'C:/outside.test.mjs',
                'reference\\rights_scale\\x.test.mjs', 'https://example.invalid/test.mjs'):
        cases.append(('unsafe path ' + bad, cell(2, '`%s::x`' % bad), {}, 'is not repo-relative'))
    for bad, marker in (('reference/v0.3-rc1/client/offline.test.mjs', 'is under reference/v0.3-rc1'),
                        ('reference/rights_scale/client/other.test.mjs', 'outside the supplemental offline tests paths'),
                        (record, 'outside the supplemental offline tests paths')):
        cases.append(('forbidden path ' + bad, cell(2, '`%s::x`' % bad), {}, marker))
    valid = rows[0][2]
    for bad in ('unquoted', '`%s`' % path, '`%s::absent`' % path):
        marker = ('needs comma-separated' if bad == 'unquoted' else
                  'needs a ::symbol' if '::' not in bad else 'test name not declared')
        for members in ((bad, valid), (valid, bad), (valid, bad, valid)):
            cases.append(('mixed citations ' + ', '.join(members), cell(2, ', '.join(members)), {}, marker))
    for name, mutated, overrides, marker in cases:
        found = find_problems(mutated, profile_text, files={**files, **overrides})
        hit = [item for item in found if marker in item]
        if not hit:
            print('self-test: %s missed diagnostic %r (found %r)' % (name, marker, found), file=sys.stderr)
            return 1
        if map_rows(mutated) != map_rows(fixture) and name != 'localnet isolation':
            print('self-test: supplemental mutation changed primary rows', file=sys.stderr)
            return 1
        print('self-test: detected %s (%s)' % (name, hit[0]))
    # Model symlink resolution in memory and prove rejection precedes any read.
    from unittest.mock import patch
    resolve = Path.resolve
    for destination, marker in ((ROOT.parent / 'escaped.test.mjs', 'resolves outside the repository'),
                                (ROOT / FORBIDDEN_PREFIX / 'client/offline.test.mjs',
                                 'resolves under reference/v0.3-rc1')):
        reads = []

        def resolved(candidate):
            return destination if candidate == ROOT / path else resolve(candidate)

        def read_fixture(candidate):
            reads.append(candidate)
            return files.get(candidate)

        with patch.object(Path, 'resolve', resolved):
            found = find_supplemental_problems(fixture, profile_rows(profile_text), ROOT, read_fixture)
        if path in reads or not any(marker in item for item in found):
            print('self-test: resolved-path fence failed: %r' % found, file=sys.stderr)
            return 1
        print('self-test: detected symlink target (%s); target not read' % marker)
    return 0


def self_test(map_text, profile_text):
    """Require each check to catch a deliberately broken copy."""
    base = find_problems(map_text, profile_text)
    if base:
        print('self-test: unmodified map already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1

    move_probe = ('#[test] fun c_probe() {}\n#[test, expected_failure(abort_code = 1)]\nfun d_probe() {}\n'
                  'public fun e_probe() {}\nfun f_probe_extra() {}\n')
    controls = [symbol_defined(move_probe, '.move', n) for n in ('c_probe', 'd_probe', 'e_probe')]
    if not all(controls) or symbol_defined(move_probe, '.move', 'f_probe'):
        print('self-test: Move symbol pattern failed its positive control', file=sys.stderr)
        return 1
    py_probe = 'CAP_PROBE = 16\ndef test_probe():\n    pass\n'
    if not (symbol_defined(py_probe, '.py', 'CAP_PROBE') and symbol_defined(py_probe, '.py', 'test_probe')
            and not symbol_defined(py_probe, '.py', 'CAP')):
        print('self-test: Python symbol pattern failed its positive control', file=sys.stderr)
        return 1

    rows = {i: _row_line(map_text, i) for i in ('IM-01', 'IM-03', 'IM-25')}
    if None in rows.values():
        print('self-test: could not find the rows to mutate', file=sys.stderr)
        return 1
    move01 = split_row(rows['IM-01'])[3]
    py01 = split_row(rows['IM-01'])[4]
    counts_line = next(l for l in map_text.splitlines() if l.startswith(COUNTS_LINE))
    partial = [(STATUS_CELL, 'PARTIAL'), (MISSING_CELL, 'a sentence'), (OWNER_CELL, NO_OWNER)]
    cases = [
        ('removed IM-01 row', map_text.replace(rows['IM-01'] + '\n', '', 1),
         'missing in map: IM-01'),
        ('duplicated IM-01 row', map_text.replace(rows['IM-01'], rows['IM-01'] + '\n' + rows['IM-01'], 1),
         'duplicated in map: IM-01'),
        ('dangling path',
         _with_cell(map_text, 'IM-01', 3, move01 + ' `reference/rights_scale/sui/tests/no_such_file.move::x`'),
         'does not exist'),
        ('dangling symbol',
         _with_cell(map_text, 'IM-01', 3,
                    move01 + ' `reference/rights_scale/sui/tests/predicate_tests.move::no_such_fn_9f3a`'),
         'is not defined in the file'),
        ('unknown status', _with_cell(map_text, 'IM-01', STATUS_CELL, 'SUFFICIENT'), 'unknown status'),
        ('altered treatment word', _with_cell(map_text, 'IM-01', 1, '유지'), 'differs from the profile'),
        ('treatment word that is not a profile word', _with_cell(map_text, 'IM-01', 1, 'keep'),
         'not one of the profile words'),
        ('NOT_COVERED row that carries a citation', _with_cell(map_text, 'IM-01', STATUS_CELL, 'NOT_COVERED'),
         'NOT_COVERED row carries a citation'),
        ('PARTIAL row with an empty missing cell',
         _with_cells(map_text, 'IM-03', partial[:1] + [(MISSING_CELL, 'none'), (OWNER_CELL, NO_OWNER)]),
         'must say what is missing'),
        ('PARTIAL row with an owner the profile does not write',
         _with_cells(map_text, 'IM-03', partial[:2] + [(OWNER_CELL, 'Nobody Else')]),
         'is not written in the profile'),
        ('citation under reference/v0.3-rc1',
         _with_cell(map_text, 'IM-01', 4, py01 + ' `reference/v0.3-rc1/x.py::y`'),
         'reference/v0.3-rc1'),
        ('UNCHANGED_BY_DESIGN on a changed row', _with_cell(map_text, 'IM-01', STATUS_CELL, 'UNCHANGED_BY_DESIGN'),
         'UNCHANGED_BY_DESIGN is only for'),
        ('COVERED status on an untouched row',
         _with_cell(map_text, 'IM-25', STATUS_CELL, 'COVERED_MODEL_OR_MEMORY'), 'is never COVERED_MODEL_OR_MEMORY'),
        ('wrong cell count', map_text.replace(rows['IM-01'], rows['IM-01'] + ' extra |', 1),
         'expected 11 cells'),
        ('wrong counts line', map_text.replace(counts_line, counts_line.replace('PARTIAL=', 'PARTIAL=9', 1), 1),
         'counts line'),
    ]
    for name, mutated, marker in cases:
        found = find_problems(mutated, profile_text)
        hit = [item for item in found if marker in item]
        if not hit:
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        print('self-test: detected %s (%s)' % (name, hit[0]))
    if supplemental_self_test(map_text, profile_text):
        return 1
    print('self-test: pass')
    return 0


def main(argv):
    texts = []
    for rel in (MAP, PROFILE):
        path = ROOT / rel
        if not path.is_file():
            print('missing ' + str(path), file=sys.stderr)
            return 1
        texts.append(path.read_text(encoding='utf-8'))
    map_text, profile_text = texts
    if '--self-test' in argv:
        return self_test(map_text, profile_text)
    problems = find_problems(map_text, profile_text)
    if problems:
        print('rs im evidence map check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    rows = map_rows(map_text)
    by_status = {s: 0 for s in STATUSES}
    cites = 0
    for _, cells in rows:
        by_status[cells[STATUS_CELL]] += 1
        for col in COLUMNS:
            cites += len(parse_cell(cells[col]))
    print('rs im evidence map ok: rows=%d expected=%d citations=%d %s'
          % (len(rows), len(profile_rows(profile_text)), cites,
             ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)))
    supplement, _ = supplemental_rows(map_text)
    print('supplemental offline evidence ok: rows=%d citations=%d'
          % (len(supplement), sum(len(parse_cell(cells[col]))
                                   for _, cells in supplement for col in (2, 3))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
