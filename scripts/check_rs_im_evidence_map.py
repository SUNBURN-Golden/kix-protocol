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
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
