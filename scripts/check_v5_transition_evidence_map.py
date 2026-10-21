#!/usr/bin/env python3
"""Check the v5 transition evidence map against the contract, decision and test tree.

Compares four inputs:

- ``docs/contracts/STATE_LIFECYCLE.md`` and
  ``docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md``: the anchor
  strings each hardcoded row id keys on (sections 5-6 transitions/commands as
  narrowed by the design decision's option O1 and the section-6 stop gates);
- ``docs/contracts/FIRST_BATCH_OPEN_INPUTS.md``: the open-input id table every
  I-numbered token in the map must resolve to;
- ``docs/status/V5_TRANSITION_EVIDENCE_MAP.md``: the builder-authored map,
  one row per id, eight cells per row (id, contract item, v5 surface,
  v5 tests, stop guard, status, missing or open, decision/owner);
- ``validation/2026-10-13-k-stage2-v5-impl/README.md``: the record of the
  2026-10-13 owner residual-stops decision that STOPPED rows may cite.

Checks, each reported on failure:

1. Ids. The hardcoded row ids equal the map first cells, each exactly once;
   missing, duplicated and invented ids are reported. Every id's anchor
   string is still present in the document it is read from.
2. Row width. Eight cells per row; the contract-item cell is non-empty.
3. Cell grammar. ``v5 surface`` is ``no entry point`` or citations only to
   ``pub fn`` symbols of ``runtime/crates/kix-kernel-v5/src/lib.rs``;
   ``v5 tests`` and ``stop guard`` are ``none`` or citations only into
   ``runtime/crates/kix-kernel-v5/tests/[a-z0-9_]+.rs`` whose symbols are
   ``#[test]``-attributed ``fn`` definitions; ``missing or open`` carries no
   citations; ``decision / owner`` is ``none``, free text, and/or citations
   only to the contract, the design decision, the open-inputs file or the
   implementation record.
4. Status. TESTED when the v5-tests cell cites anything; otherwise STOPPED
   or OPEN. A STOPPED row needs a decision citation (the design decision or
   the implementation record) and a non-``none`` missing cell. An OPEN row
   needs a non-``none`` missing cell and a named owner.
5. Citations. Every backticked ``path::symbol`` span in the whole document:
   the path is repo-relative, exists, is never under ``reference/v0.3-rc1/``
   and lies in the allowed set; the symbol exists — a ``#[test]`` ``fn`` for
   test files, a ``pub`` definition for the v5 ``lib.rs``, verbatim text for
   the cited Markdown files.
6. Open inputs. Every I-numbered token in the map is an id in the open-inputs
   table, so no row can cite an open input that does not exist.
7. Locked blobs. The git-blob SHA-1 of the two locked kernel files is
   recomputed and must equal the values pinned in AGENTS.md section 4.
8. Counts. The ``Counts:`` line equals the statuses recomputed from the
   map section.

Standard library only. Convenience check, not a contract gate. It reads
the cited files as text and executes none of them; it proves that a cited
name exists, not that the surface implements the contract rule and not
what the test asserts. ``--self-test`` mutates in-memory copies and
requires each break to be caught.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/V5_TRANSITION_EVIDENCE_MAP.md'
CONTRACT = 'docs/contracts/STATE_LIFECYCLE.md'
DECISION = 'docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md'
IMPL = 'validation/2026-10-13-k-stage2-v5-impl/README.md'
OPEN_INPUTS = 'docs/contracts/FIRST_BATCH_OPEN_INPUTS.md'
V5_LIB = 'runtime/crates/kix-kernel-v5/src/lib.rs'
KERNEL_LIB = 'runtime/crates/kix-kernel/src/lib.rs'
KERNEL_QC = 'runtime/crates/kix-kernel/tests/quarantine_capacity.rs'
LOCKED_BLOBS = {
    KERNEL_LIB: '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    KERNEL_QC: 'b607996c83a119c349f1cc90469ac1ba82764e20',
}

STATUSES = ('TESTED', 'STOPPED', 'OPEN')
CELLS = 8
ITEM_CELL, SURFACE_CELL, TESTS_CELL, GUARD_CELL = 1, 2, 3, 4
STATUS_CELL, MISSING_CELL, DECISION_CELL = 5, 6, 7
V5_TEST_PATH = r'runtime/crates/kix-kernel-v5/tests/[a-z0-9_]+\.rs'
V4_TEST_PATH = r'runtime/crates/kix-kernel/tests/[a-z0-9_]+\.rs'
DECISION_DOCS = (CONTRACT, DECISION, OPEN_INPUTS, IMPL)
STOP_DECISION_DOCS = (DECISION, IMPL)
FORBIDDEN_PREFIX = 'reference/v0.3-rc1/'
TEXT_SUFFIXES = ('.md',)
# Row id -> (source key, anchor string that must still be in that source).
EXPECTED = {
    'TERM': ('contract', 'LC-TERM'),
    'TERM-LATE': ('contract', '종결 후 늦은 성공'),
    'RR-REVIEW': ('contract',
                  'ReturnRequired와 review_required의 우선순위·직교성'),
    'SLOT-RELEASE': ('contract', '슬롯 해제'),
    'REVIEW-RELEASE': ('contract', 'review 해제'),
    'RECLAIM-READ': ('decision', '읽기 전용** 자격 보고만 만든다'),
    'RECLAIM-APPLY': ('decision', '상태를 바꾸는 회수는 **정지**다'),
    'HOLD': ('contract', '법정 보존'),
    'CONFLICT-INDEX': ('contract', '색인 일관성'),
    'INDEX-UPKEEP': ('decision', '전이가 열리기 전까지 게이트에 둔다'),
}

CITATION = re.compile(r'`([^`]+)`')
STATUS_WORD = re.compile(r'[A-Z-]+')
MAP_HEAD = '## 2. Map'
COUNTS_LINE = 'Counts:'
OPEN_ID = re.compile(r'\bI\d{2}\b')
OPEN_TABLE_ID = re.compile(r'^\|\s*(I\d{2})\s*\|', re.M)

TEST_FN = r'#\[test\]\s*\n\s*fn\s+%s\b'
LIB_DEF = r'^\s*pub(?:\([^)]*\))?\s+(?:fn|struct|enum|const|type)\s+%s\b'
LIB_PUB_FN = r'^\s*pub(?:\([^)]*\))?\s+fn\s+%s\b'


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def map_rows(map_text, expected):
    """Rows inside the map section whose first cell is an expected id."""
    in_map = False
    rows = []
    others = []
    for line in map_text.splitlines():
        if line.startswith(MAP_HEAD):
            in_map = True
            continue
        if in_map and line.startswith('## '):
            break
        if not in_map or not line.startswith('|'):
            continue
        cells = split_row(line)
        if not cells or not cells[0] or cells[0] == 'ID' \
                or set(cells[0]) <= set('-:'):
            continue
        if cells[0] in expected:
            rows.append((cells[0], cells))
        else:
            others.append(cells[0])
    return rows, others


def parse_cell(cell):
    """Return [(path, symbol_or_None), ...] for the backticked citations."""
    out = []
    for match in CITATION.finditer(cell):
        path, _, symbol = match.group(1).partition('::')
        out.append((path.strip(), symbol.strip() or None))
    return out


def citations_of(text):
    """Every backticked ``path::symbol`` span in the text."""
    return [(p, s) for p, s in parse_cell(text) if s is not None]


def symbol_ok(path, text, symbol):
    """The symbol rule for a citation path: definition or verbatim text."""
    if path.endswith(TEXT_SUFFIXES):
        return symbol in text
    if re.fullmatch(V5_TEST_PATH, path) or re.fullmatch(V4_TEST_PATH, path):
        return re.search(TEST_FN % re.escape(symbol), text) is not None
    if path == V5_LIB:
        return re.search(LIB_DEF % re.escape(symbol), text,
                         re.M) is not None
    if path == KERNEL_LIB:
        return re.search(LIB_DEF % re.escape(symbol), text,
                         re.M) is not None
    return False


def citation_path_ok(path):
    """Paths a citation anywhere in the map may point at."""
    if path == V5_LIB or path == KERNEL_LIB:
        return True
    if re.fullmatch(V5_TEST_PATH, path) or re.fullmatch(V4_TEST_PATH, path):
        return True
    return path in DECISION_DOCS


def git_blob_sha(text):
    data = text.encode('utf-8')
    return hashlib.sha1(b'blob %d\x00' % len(data) + data).hexdigest()


def find_problems(map_text, sources, root=ROOT, files=None):
    """Return a list of problem strings; empty means the map passes.

    ``sources`` maps a source key (``contract``, ``decision``, ``impl``,
    ``open``) to that file's text. ``files`` optionally maps a
    repo-relative path to replacement text.
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

    # Locked-blob guard: the cited kernel files must stay byte-pinned.
    for rel, want in LOCKED_BLOBS.items():
        text = read(rel)
        if text is None:
            problems.append('locked file missing: %s' % rel)
        elif git_blob_sha(text) != want:
            problems.append('locked blob mismatch: %s (have %s, want %s)'
                            % (rel, git_blob_sha(text), want))

    for ident, (src, anchor) in EXPECTED.items():
        if anchor not in sources.get(src, ''):
            problems.append('%s: %s anchor %r is gone' % (ident, src, anchor))

    open_ids = set(OPEN_TABLE_ID.findall(sources.get('open', '')))
    for token in sorted(set(OPEN_ID.findall(map_text))):
        if token not in open_ids:
            problems.append('open input %s is not a row of %s'
                            % (token, OPEN_INPUTS))

    # Every citation in the document resolves.
    for path, symbol in citations_of(map_text):
        where = 'citation %s::%s' % (path, symbol)
        if path.startswith('/') or '..' in path.split('/'):
            problems.append('%s is not repo-relative' % where)
            continue
        if path.startswith(FORBIDDEN_PREFIX):
            problems.append('%s is under reference/v0.3-rc1' % where)
            continue
        if not citation_path_ok(path):
            problems.append('%s is outside the allowed citation paths'
                            % where)
            continue
        text = read(path)
        if text is None:
            problems.append('%s does not exist' % where)
            continue
        if not symbol_ok(path, text, symbol):
            problems.append('%s is not defined in the file' % where)

    expected = list(EXPECTED)
    rows, others = map_rows(map_text, set(expected))
    for ident in others:
        problems.append('invented id in map section: %s' % ident)

    counts = {}
    for ident, _ in rows:
        counts[ident] = counts.get(ident, 0) + 1
    for ident in expected:
        if counts.get(ident, 0) == 0:
            problems.append('missing in map: %s' % ident)
        elif counts[ident] != 1:
            problems.append('duplicated in map: %s (%d)' % (ident, counts[ident]))

    seen = set()
    by_status = {s: 0 for s in STATUSES}
    for ident, cells in rows:
        if ident in seen:
            continue
        seen.add(ident)
        if len(cells) != CELLS:
            problems.append('%s: expected %d cells, found %d'
                            % (ident, CELLS, len(cells)))
            continue
        if not cells[ITEM_CELL]:
            problems.append('%s: empty contract-item cell' % ident)

        surface = cells[SURFACE_CELL]
        surface_cites = parse_cell(surface)
        if not surface_cites:
            if surface != 'no entry point':
                problems.append('%s: v5 surface is neither no entry point '
                                'nor a lib.rs citation' % ident)
        else:
            for path, symbol in surface_cites:
                if path != V5_LIB:
                    problems.append('%s: v5 surface citation %s is not the '
                                    'v5 lib.rs' % (ident, path))
                elif symbol is None:
                    problems.append('%s: v5 surface citation %s needs a '
                                    '::symbol' % (ident, path))
                else:
                    text = read(path)
                    if text is not None and not re.search(
                            LIB_PUB_FN % re.escape(symbol), text, re.M):
                        problems.append('%s: v5 surface %s::%s is not a '
                                        'pub fn' % (ident, path, symbol))

        for col, name in ((TESTS_CELL, 'v5 tests'), (GUARD_CELL, 'stop guard')):
            cell = cells[col]
            cites = parse_cell(cell)
            if not cites:
                if cell != 'none':
                    problems.append('%s: %s cell is neither none nor a '
                                    'citation' % (ident, name))
                continue
            for path, symbol in cites:
                where = '%s: %s citation %s' % (ident, name, path)
                if symbol is not None:
                    where += '::' + symbol
                if not re.fullmatch(V5_TEST_PATH, path or ''):
                    problems.append('%s is not a v5 test file' % where)
                    continue
                if symbol is None:
                    problems.append('%s needs a nonempty ::symbol' % where)
                text = read(path)
                if text is None:
                    problems.append('%s does not exist' % where)
                elif symbol is not None and not symbol_ok(path, text, symbol):
                    problems.append('%s is not a #[test]-attributed fn' % where)

        missing_cites = [c for c in parse_cell(cells[MISSING_CELL])
                         if c[1] is not None]
        for path, symbol in missing_cites:
            problems.append('%s: citation %s::%s is inside the missing '
                            'cell' % (ident, path, symbol))

        decision = cells[DECISION_CELL]
        decision_cites = [c for c in parse_cell(decision) if c[1] is not None]
        for path, _ in decision_cites:
            if path not in DECISION_DOCS:
                problems.append('%s: decision citation %s is not a '
                                'decision document' % (ident, path))
        has_stop_decision = any(p in STOP_DECISION_DOCS
                                for p, _ in decision_cites)

        status_cell = cells[STATUS_CELL]
        match = STATUS_WORD.fullmatch(status_cell)
        status = match.group(0) if match else ''
        if status not in STATUSES:
            problems.append('%s: unknown status %r' % (ident, status_cell))
        else:
            has_tests = bool(parse_cell(cells[TESTS_CELL]))
            if has_tests:
                want = 'TESTED'
            elif has_stop_decision:
                want = 'STOPPED'
            else:
                want = 'OPEN'
            if status != want:
                problems.append('%s: status %s should be %s for these cells'
                                % (ident, status, want))
            by_status[status] += 1
            if status == 'STOPPED' and not has_stop_decision:
                problems.append('%s: STOPPED row must cite the design '
                                'decision or the implementation record'
                                % ident)
            if status in ('STOPPED', 'OPEN') \
                    and cells[MISSING_CELL].lower().startswith('none'):
                problems.append('%s: %s row must say what is missing or '
                                'open' % (ident, status))
            if status == 'OPEN' \
                    and (not decision or decision == 'none'):
                problems.append('%s: OPEN row must name an owner' % ident)

    lines = [l for l in map_text.splitlines() if l.startswith(COUNTS_LINE)]
    want = COUNTS_LINE + ' rows=%d ' % len(rows) \
        + ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)
    if len(lines) != 1:
        problems.append('%r line appears %d times'
                        % (COUNTS_LINE, len(lines)))
    elif lines[0].strip() != want:
        problems.append('counts line %r differs from the table %r'
                        % (lines[0].strip(), want))
    return problems


def _row_line(text, ident):
    for line in text.splitlines():
        if line.startswith('|'):
            cells = split_row(line)
            if cells and cells[0] == ident:
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


def _fixture_citation_self_test(map_text, sources):
    """Exercise every fixture citation, including ones citations_of omits."""
    probe_path = 'runtime/crates/kix-kernel-v5/tests/citation_probe.rs'
    missing_path = 'runtime/crates/kix-kernel-v5/tests/citation_missing.rs'
    existing_path = 'runtime/crates/kix-kernel-v5/tests/termination.rs'
    files = {
        probe_path: '#[test]\nfn first() {}\n#[test]\nfn second() {}\n'
                    'fn helper() {}\n',
        missing_path: None,
    }
    valid = '`%s::first`' % probe_path
    multiple = valid + ', `%s::second`' % probe_path
    needs_symbol = 'needs a nonempty ::symbol'
    not_test = 'is not a #[test]-attributed fn'
    # Each expected diagnostic names the row, column and offending citation.
    negatives = [
        ('bare existing path', existing_path, [needs_symbol]),
        ('bare missing path', missing_path,
         [needs_symbol, 'does not exist']),
        ('bare injected path', probe_path, [needs_symbol]),
        ('empty symbol', probe_path + '::', [needs_symbol]),
        ('spaces-only symbol', probe_path + '::   ', [needs_symbol]),
        ('tabs-only symbol', probe_path + '::\t\t', [needs_symbol]),
        ('missing file', missing_path + '::first', ['does not exist']),
        ('missing function', probe_path + '::absent', [not_test]),
        ('helper function', probe_path + '::helper', [not_test]),
        ('invalid test path', V5_LIB + '::terminate', ['is not a v5 test file']),
    ]
    failed = False
    for col, name in ((TESTS_CELL, 'v5 tests'), (GUARD_CELL, 'stop guard')):
        for label, citation, reasons in negatives:
            path, _, symbol = citation.partition('::')
            identity = path + ('::' + symbol.strip() if symbol.strip() else '')
            expected = ['TERM: %s citation %s %s' % (name, identity, reason)
                        for reason in reasons]
            bad = '`%s`' % citation
            for cell in (bad, valid + ', ' + bad, bad + ', ' + valid):
                found = find_problems(
                    _with_cell(map_text, 'TERM', col, cell), sources,
                    files=files)
                missing = [message for message in expected if message not in found]
                if missing:
                    print('self-test: %s %s missed %r in %r'
                          % (name, label, missing, cell), file=sys.stderr)
                    failed = True
            print('self-test: exercised %s %s (alone and mixed lists)'
                  % (name, label))

        # All invalid members must be diagnosed, even after a valid citation.
        cell = multiple + ', `%s`, `%s::absent`, `%s::helper`' % (
            missing_path, probe_path, probe_path)
        found = find_problems(_with_cell(map_text, 'TERM', col, cell),
                              sources, files=files)
        for identity, reason in ((missing_path, needs_symbol),
                                 (missing_path, 'does not exist'),
                                 (probe_path + '::absent', not_test),
                                 (probe_path + '::helper', not_test)):
            expected = 'TERM: %s citation %s %s' % (name, identity, reason)
            if expected not in found:
                print('self-test: mixed invalid members missed ' + expected,
                      file=sys.stderr)
                failed = True

    positives = [
        ('none tests on stopped row',
         _with_cell(map_text, 'SLOT-RELEASE', TESTS_CELL, 'none')),
        ('none guard on tested row',
         _with_cell(map_text, 'TERM', GUARD_CELL, 'none')),
        ('none guard on stopped row',
         _with_cell(map_text, 'SLOT-RELEASE', GUARD_CELL, 'none')),
    ]
    for cell in (valid, multiple):
        positives.append(('valid test and guard citations', _with_cells(
            map_text, 'TERM', [(TESTS_CELL, cell), (GUARD_CELL, cell)])))
        positives.append(('valid stopped guard citations', _with_cell(
            map_text, 'SLOT-RELEASE', GUARD_CELL, cell)))
    for name, text in positives:
        found = find_problems(text, sources, files=files)
        if found:
            print('self-test: %s positive control failed: %r' % (name, found),
                  file=sys.stderr)
            failed = True
    return failed


def self_test(map_text, sources):
    """Require each check to catch a deliberately broken copy."""
    base = find_problems(map_text, sources)
    if base:
        print('self-test: unmodified map already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1

    probe = '#[test]\nfn a_probe() {}\nfn helper() {}\n'
    if not symbol_ok('runtime/crates/kix-kernel-v5/tests/probe.rs',
                     probe, 'a_probe') \
            or symbol_ok('runtime/crates/kix-kernel-v5/tests/probe.rs',
                         probe, 'helper'):
        print('self-test: #[test] symbol rule failed its control',
              file=sys.stderr)
        return 1

    tested = 'TERM'
    stopped = 'SLOT-RELEASE'
    rows = {i: _row_line(map_text, i) for i in (tested, stopped, 'OPEN',
                                              'CONFLICT-INDEX')}
    if rows[tested] is None or rows[stopped] is None:
        print('self-test: could not find the rows to mutate', file=sys.stderr)
        return 1
    if _fixture_citation_self_test(map_text, sources):
        return 1
    counts_line = next(l for l in map_text.splitlines()
                       if l.startswith(COUNTS_LINE))
    cases = [
        ('removed %s row' % tested,
         map_text.replace(rows[tested] + '\n', '', 1),
         'missing in map: ' + tested),
        ('duplicated %s row' % tested,
         map_text.replace(rows[tested],
                          rows[tested] + '\n' + rows[tested], 1),
         'duplicated in map: ' + tested),
        ('invented id',
         map_text.replace(
             counts_line,
             '| FAKE-ID-9f3a | x | no entry point | none | none | OPEN '
             '| gap | someone |\n' + counts_line, 1),
         'invented id'),
        ('dangling path',
         _with_cell(map_text, tested, TESTS_CELL,
                    '`runtime/crates/kix-kernel-v5/tests/no_such.rs::x`'),
         'does not exist'),
        ('helper fn cited as a test',
         _with_cell(map_text, tested, TESTS_CELL,
                    '`runtime/crates/kix-kernel-v5/tests/termination.rs::unchanged`'),
         'is not defined in the file'),
        ('dangling test symbol',
         _with_cell(map_text, tested, TESTS_CELL,
                    '`runtime/crates/kix-kernel-v5/tests/termination.rs::no_such_test_9f3a`'),
         'is not defined in the file'),
        ('test citation in the surface column',
         _with_cell(map_text, tested, SURFACE_CELL,
                    '`runtime/crates/kix-kernel-v5/tests/termination.rs::termination_records_once_and_blocks_only_the_next_send`'),
         'is not the v5 lib.rs'),
        ('citation under reference/v0.3-rc1',
         _with_cell(map_text, tested, TESTS_CELL,
                    '`reference/v0.3-rc1/core.py::execute`'),
         'reference/v0.3-rc1'),
        ('STOPPED row carrying a test',
         _with_cell(map_text, stopped, TESTS_CELL,
                    '`runtime/crates/kix-kernel-v5/tests/termination.rs::failed_termination_does_not_change_state`'),
         'should be'),
        ('TESTED row with none tests',
         _with_cell(map_text, tested, TESTS_CELL, 'none'),
         'should be'),
        ('STOPPED without a decision citation',
         _with_cell(map_text, stopped, DECISION_CELL, 'none'),
         'must cite the design decision or the implementation record'),
        ('STOPPED with a none missing cell',
         _with_cell(map_text, stopped, MISSING_CELL, 'none'),
         'must say what is missing'),
        ('unknown status',
         _with_cell(map_text, tested, STATUS_CELL, 'SUFFICIENT'),
         'unknown status'),
        ('citation inside the missing cell',
         _with_cell(map_text, tested, MISSING_CELL,
                    'gap `docs/contracts/STATE_LIFECYCLE.md::LC-TERM`'),
         'inside the missing cell'),
        ('decision citation to a non-decision file',
         _with_cell(map_text, tested, DECISION_CELL,
                    '`runtime/crates/kix-kernel-v5/src/lib.rs::terminate`'),
         'is not a decision document'),
        ('open input not in the open-inputs file',
         _with_cell(map_text, stopped, MISSING_CELL,
                    'No release; opens I99.'),
         'open input I99 is not a row of'),
        ('free-text-only surface cell',
         _with_cell(map_text, tested, SURFACE_CELL, 'something vague'),
         'neither no entry point nor a lib.rs citation'),
        ('wrong counts line',
         map_text.replace(counts_line,
                          counts_line.replace('TESTED=6', 'TESTED=99'), 1),
         'counts line'),
    ]
    for name, mutated, marker in cases:
        found = find_problems(mutated, sources)
        hit = [item for item in found if marker in item]
        if not hit:
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        print('self-test: detected %s (%s)' % (name, hit[0]))

    # Locked-blob guard via file injection.
    lib_text = (ROOT / KERNEL_LIB).read_text(encoding='utf-8')
    found = find_problems(map_text, sources,
                          files={KERNEL_LIB: lib_text + '\n// mutated\n'})
    hit = [item for item in found if 'locked blob mismatch' in item]
    if not hit:
        print('self-test: mutated kernel lib.rs was accepted',
              file=sys.stderr)
        return 1
    print('self-test: detected mutated locked blob (%s)' % hit[0])

    ident, (src, anchor) = next(iter(EXPECTED.items()))
    anchorless = dict(sources)
    anchorless[src] = sources[src].replace(anchor, '(x)')
    found = find_problems(map_text, anchorless)
    hit = [item for item in found if 'anchor' in item]
    if not hit:
        print('self-test: removed contract anchor was accepted',
              file=sys.stderr)
        return 1
    print('self-test: detected removed anchor (%s)' % hit[0])

    print('self-test: pass')
    return 0


def main(argv):
    paths = {'contract': CONTRACT, 'decision': DECISION, 'impl': IMPL,
             'open': OPEN_INPUTS}
    sources = {}
    for key, rel in paths.items():
        path = ROOT / rel
        if not path.is_file():
            print('missing ' + str(path), file=sys.stderr)
            return 1
        sources[key] = path.read_text(encoding='utf-8')
    map_path = ROOT / MAP
    if not map_path.is_file():
        print('missing ' + str(map_path), file=sys.stderr)
        return 1
    map_text = map_path.read_text(encoding='utf-8')
    if '--self-test' in argv:
        return self_test(map_text, sources)
    problems = find_problems(map_text, sources)
    if problems:
        print('v5 transition evidence map check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    rows, _ = map_rows(map_text, set(EXPECTED))
    by_status = {s: 0 for s in STATUSES}
    cites = 0
    for _, cells in rows:
        by_status[cells[STATUS_CELL]] += 1
        for col in (SURFACE_CELL, TESTS_CELL, GUARD_CELL, DECISION_CELL):
            cites += len(parse_cell(cells[col]))
    print('v5 transition evidence map ok: rows=%d expected=%d citations=%d %s'
          % (len(rows), len(EXPECTED), cites,
             ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
