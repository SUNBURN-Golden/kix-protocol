#!/usr/bin/env python3
"""Check the RS predicate evidence map against the profile and the cited sources.

Compares two inputs:

- ``docs/contracts/RIGHTS_SCALE_PROFILE.md``: the predicate rows RS-C01..RS-C17
  (section 8, test id in cell 3, owner in cell 4) and RR-1..RR-6 (section 9,
  test id in cell 5, owner in cell 6).
- ``docs/status/RS_PREDICATE_EVIDENCE_MAP.md``: the builder-authored map, one
  row per id, nine cells per row (id, proposed test id, Move test, Python
  model test, Rust in-memory test, localnet script or validation record,
  status, missing or open, owner).

Checks, each reported on failure:

1. Ids. The profile ids equal the map first cells, each exactly once; missing,
   duplicated, extra and not-in-profile ids are reported. Each row has nine
   cells.
2. Test id and owner. Cell 2 equals the profile test id cell. Cell 9 starts
   with the profile owner cell and every ``;``-separated part is a substring of
   the profile text.
3. Status. It is one of COVERED_LOCALNET, COVERED_MODEL_OR_MEMORY, PARTIAL,
   NOT_COVERED, MEASUREMENT_ONLY and agrees with the citations: NOT_COVERED
   carries no citation, every other status carries at least one; a covered
   status needs a Move, Python or Rust citation; COVERED_LOCALNET needs a
   localnet citation; MEASUREMENT_ONLY names RS-4 as owner. A NOT_COVERED,
   PARTIAL or MEASUREMENT_ONLY row has a missing sentence other than ``none``.
   The split rows keep their (a)/(b) or public/private/delegated labels.
4. Citations. A citation is ``path::symbol`` in backticks. Each path exists, is
   repo-relative, lies under its column's allowed prefixes and is never under
   ``reference/v0.3-rc1/``. A symbol is a defined ``fun``/``struct``/``const``
   (Move), ``def``/``class`` (Python) or ``fn`` (Rust) in the cited file; for
   ``.mjs``, ``.json`` and ``.md`` it must appear as text.
5. Counts. The ``Counts:`` line equals the statuses recomputed from the table.

Standard library only. Convenience check, not a contract gate. It reads the
cited files as text and executes none of them. ``--self-test`` mutates
in-memory copies of the map and requires each break to be caught.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/RS_PREDICATE_EVIDENCE_MAP.md'
PROFILE = 'docs/contracts/RIGHTS_SCALE_PROFILE.md'

STATUSES = ('COVERED_LOCALNET', 'COVERED_MODEL_OR_MEMORY', 'PARTIAL',
            'NOT_COVERED', 'MEASUREMENT_ONLY')
NEEDS_MISSING = ('PARTIAL', 'NOT_COVERED', 'MEASUREMENT_ONLY')
# column index -> (name, allowed path patterns)
COLUMNS = {
    2: ('move', (r'reference/rights_scale/sui/tests/[a-z_]+\.move',)),
    3: ('python', (r'reference/rights_scale/test_[a-z_]+\.py',)),
    4: ('rust', (r'runtime/crates/kix-delegated-exec/tests/[a-z_]+\.rs',)),
    5: ('local', (r'reference/rights_scale/client/[a-z0-9-]+\.mjs',
                  r'reference/rights_scale/vectors/[a-z_]+\.json',
                  r'scripts/run_[a-z0-9_]*rights_scale[a-z0-9_]*\.py',
                  r'validation/2026-10-1[0-9]-[a-z0-9-]+/[A-Za-z0-9._-]+')),
}
FORBIDDEN_PREFIX = 'reference/v0.3-rc1/'
TEXT_SUFFIXES = ('.mjs', '.json', '.md')
SPLIT_LABELS = {
    'RS-C03': ('(a)', '(b)'), 'RS-C06': ('(a)', '(b)'), 'RS-C07': ('(a)', '(b)'),
    'RS-C14': ('public', 'private', 'delegated'),
}

ID_CELL = re.compile(r'^\|\s*(RS-C\d\d|RR-\d)\s*\|')
CITATION = re.compile(r'`([^`]+)`')
STATUS_WORD = re.compile(r'[A-Z_]+')
COUNTS_LINE = 'Counts:'

DEF_PATTERNS = {
    '.py': r'^\s*(?:(?:async\s+)?def|class)\s+%s\b',
    '.rs': r'^\s*(?:pub(?:\([^)]*\))?\s+)?(?:fn|struct|enum|const)\s+%s\b',
    '.move': (r'(?:^|\])\s*(?:public(?:\([a-z]+\))?\s+)?(?:entry\s+)?'
              r'(?:fun|struct|const)\s+%s\b'),
}


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def profile_rows(profile_text):
    """Return {id: (test_id_cell, owner_cell)} from the profile tables."""
    rows = {}
    for line in profile_text.splitlines():
        match = ID_CELL.match(line)
        if not match:
            continue
        ident, cells = match.group(1), split_row(line)
        if ident.startswith('RS-C') and len(cells) == 4:
            rows[ident] = (cells[2], cells[3])
        elif ident.startswith('RR-') and len(cells) == 6:
            rows[ident] = (cells[4], cells[5])
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
            problems.append('not in profile sections 8 and 9: %s' % ident)

    seen = set()
    by_status = {s: 0 for s in STATUSES}
    for ident, cells in rows:
        if ident in seen:
            continue
        seen.add(ident)
        if len(cells) != 9:
            problems.append('%s: expected 9 cells, found %d' % (ident, len(cells)))
            continue
        if ident in expected:
            test_id, owner = expected[ident]
            if cells[1] != test_id:
                problems.append('%s: test id %r differs from the profile %r'
                                % (ident, cells[1], test_id))
            if not cells[8].startswith(owner):
                problems.append('%s: owner %r does not start with the profile owner %r'
                                % (ident, cells[8], owner))
            for part in (p.strip() for p in cells[8].split(';')):
                if not part or part not in profile_text:
                    problems.append('%s: owner part %r is not written in the profile'
                                    % (ident, part))

        status_cell = cells[6]
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
            if not cites and cell != 'none' and not re.fullmatch(r'none', cell):
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
        if status == 'MEASUREMENT_ONLY' and 'RS-4' not in cells[8]:
            problems.append('%s: MEASUREMENT_ONLY must name RS-4 as owner' % ident)
        if not cells[7]:
            problems.append('%s: empty missing-or-open cell' % ident)
        elif status in NEEDS_MISSING and cells[7].lower().startswith('none'):
            problems.append('%s: %s row must say what is missing' % (ident, status))
        for label in SPLIT_LABELS.get(ident, ()):
            if not any(label in cells[col] for col in (2, 3, 4, 5)):
                problems.append('%s: split label %r is missing' % (ident, label))

    lines = [l for l in map_text.splitlines() if l.startswith(COUNTS_LINE)]
    want = COUNTS_LINE + ' ' + ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)
    if len(lines) != 1:
        problems.append('%r line appears %d times' % (COUNTS_LINE, len(lines)))
    elif lines[0].strip() != want:
        problems.append('counts line %r differs from the table %r' % (lines[0].strip(), want))
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


def _without_labels(text, ident, labels):
    line = _row_line(text, ident)
    stripped = line
    for label in labels:
        stripped = stripped.replace(label, '')
    return text.replace(line, stripped, 1)


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

    rows = {i: _row_line(map_text, i) for i in ('RS-C01', 'RS-C02', 'RS-C07', 'RR-5')}
    if None in rows.values():
        print('self-test: could not find the rows to mutate', file=sys.stderr)
        return 1
    move01 = split_row(rows['RS-C01'])[2]
    pyc07 = split_row(rows['RS-C07'])[3]
    own02 = split_row(rows['RS-C02'])[8]
    counts_line = next(l for l in map_text.splitlines() if l.startswith(COUNTS_LINE))
    cases = [
        ('removed RS-C01 row', map_text.replace(rows['RS-C01'] + '\n', '', 1),
         'missing in map: RS-C01'),
        ('duplicated RS-C01 row', map_text.replace(rows['RS-C01'], rows['RS-C01'] + '\n' + rows['RS-C01'], 1),
         'duplicated in map: RS-C01'),
        ('dangling path',
         _with_cell(map_text, 'RS-C01', 2, move01 + ' `reference/rights_scale/sui/tests/no_such_file.move::x`'),
         'does not exist'),
        ('dangling symbol',
         _with_cell(map_text, 'RS-C01', 2,
                    move01 + ' `reference/rights_scale/sui/tests/predicate_tests.move::no_such_fn_9f3a`'),
         'is not defined in the file'),
        ('unknown status', _with_cell(map_text, 'RS-C01', 6, 'SUFFICIENT'), 'unknown status'),
        ('NOT_COVERED row that carries a citation', _with_cell(map_text, 'RS-C01', 6, 'NOT_COVERED'),
         'NOT_COVERED row carries a citation'),
        ('uncited row that is not NOT_COVERED',
         _with_cell(_with_cell(_with_cell(_with_cell(map_text, 'RS-C13', 2, 'none'), 'RS-C13', 3, 'none'),
                              'RS-C13', 4, 'none'), 'RS-C13', 5, 'none'),
         'so it must be NOT_COVERED'),
        ('altered test id', _with_cell(map_text, 'RS-C01', 1, 'RS-C01-T9'), 'differs from the profile'),
        ('owner not written in the profile',
         _with_cell(map_text, 'RS-C02', 8, own02 + '; Nobody Else'), 'is not written in the profile'),
        ('empty missing cell on a PARTIAL row', _with_cell(map_text, 'RS-C07', 7, 'none'),
         'must say what is missing'),
        ('citation under reference/v0.3-rc1',
         _with_cell(map_text, 'RS-C07', 3, pyc07 + ' `reference/v0.3-rc1/x.py::y`'),
         'reference/v0.3-rc1'),
        ('split label dropped', _without_labels(map_text, 'RS-C07', ('(a)', '(b)')),
         'split label'),
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
        print('rs predicate evidence map check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    rows = map_rows(map_text)
    by_status = {s: 0 for s in STATUSES}
    cites = 0
    for _, cells in rows:
        by_status[cells[6]] += 1
        for col in COLUMNS:
            cites += len(parse_cell(cells[col]))
    print('rs predicate evidence map ok: rows=%d expected=%d citations=%d %s'
          % (len(rows), len(profile_rows(profile_text)), cites,
             ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
