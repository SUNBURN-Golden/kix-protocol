#!/usr/bin/env python3
"""Check lifecycle/ADR clause-map structure against current documents and tests.

Stdlib only; reads raw locked-file bytes without executing cited Rust. Anchors
and #[test] names prove textual existence, not semantic coverage or independence.
Self-test mutations and injected files exist only in memory, including wrong blobs.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md'
SOURCES = {
    'contract': 'docs/contracts/STATE_LIFECYCLE.md',
    'adr': 'docs/adr/0001-ktx-authority-commit-recovery.md',
    'inv': 'docs/contracts/CONTRACT_INVARIANTS.md',
    'open': 'docs/contracts/FIRST_BATCH_OPEN_INPUTS.md',
}
LOCKED_BLOBS = {
    'runtime/crates/kix-kernel/src/lib.rs':
        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs':
        'b607996c83a119c349f1cc90469ac1ba82764e20',
}
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED', 'OPEN')
MUST_BE_OPEN = {'L4-HANDOFF'}
HEADER = ['ID', 'Clause', 'Contract-path tests', 'Source-informed tests',
          'INV', 'Status', 'Gap', 'Owner']
CLAUSE, CONTRACT_TESTS, SOURCE_TESTS, INV, STATUS, GAP, OWNER = range(1, 8)
V4 = 'runtime/crates/kix-kernel/tests/'
V5 = 'runtime/crates/kix-kernel-v5/tests/'
CONTRACT_PATHS = {V4 + name + '.rs' for name in
                  ('contract_invariants', 'contract_edge_cases',
                   'transitions', 'observation_slots')}
SOURCE_PATHS = {V4 + 'e4_state_model.rs', V5 + 'lifecycle_model.rs',
                V5 + 'v4_differential.rs'}
INV_TEST = (V4 + 'contract_invariants.rs',
            'five_contract_invariants_on_kernel_only_generated_histories')
CITATION = re.compile(r'`([^`]+)`')
TEST_FN = r'^\s*#\[test\]\s*\n\s*fn\s+%s\b'
TEST_CELL = re.compile(r'`[^`]+`(?:,\s*`[^`]+`)*')
INV_CELL = re.compile(r'INV-[1-5](?:,\s*INV-[1-5])*')
OPEN_ID = re.compile(r'\bI\d{2}\b')
OPEN_TABLE_ID = re.compile(r'^\|\s*(I\d{2})\s*\|', re.M)
INV_TABLE_ID = re.compile(r'^\|\s*(INV-[1-5])\s*\|', re.M)
MAP_HEAD = '## 2. Map'
COUNTS_LINE = 'Counts:'
# Row id -> (source key, verbatim anchor in the current source document).
EXPECTED = {
    'L1-A4': ('contract', 'A-4와의 중복을 한 번만 정의'),
    'L2-UNKNOWN': ('contract', '| UNKNOWN operation |'),
    'L2-SLOT': ('contract', '| 예약 슬롯 |'),
    'L2-STORED': ('contract', '| 저장 event/conflict |'),
    'L2-REVIEW': ('contract', '| bound quarantine/review |'),
    'L2-UNBOUND': ('contract', '| unbound evidence |'),
    'L2-CMD': ('contract', '| command 최초 결과 |'),
    'L2-IDENTITY': ('contract', '| 주문·operation identity |'),
    'L3-PRESERVE': ('contract', '결합한 사실을 보존한다'),
    'L3-EVENT-ECON': ('contract', 'event identity와'),
    'L3-CAPACITY': ('contract', 'v4의 상충 Err(Capacity)는'),
    'L3-INBOX': ('contract', '수신 ACK 전에 내구성 있게 확보해야 한다'),
    'L4-GEN': ('contract', 'business epoch'),
    'L4-REPLAY': ('contract', 'historical replay에서 외부 호출을 실행하지 않는다'),
    'L4-HANDOFF': ('contract', '소비/재위임을 보류한다'),
    'L6-NOGC': ('contract', '시험에서도 가상 GC를 넣지 않는다'),
    'L6-REFS': ('contract', '회수 후보의 active order/operation'),
    'A3-IDENTITY': ('adr', 'Same identity + same business payload returns the original result'),
    'A3-FENCES': ('adr', 'ExecutionFence identifies the current writer'),
    'A3-RETENTION': ('adr', 'R1 has bounded records and no eviction'),
    'A4-ATOMIC': ('adr', 'Never independently ACK an in-memory HOLD'),
    'A5-READONLY': ('adr', 'Immutable reservation-result lookup is a read-only exception'),
    'A6-EVENT-ECON': ('adr', 'Event dedupe and economic-operation dedupe are distinct'),
    'A6-UNKNOWN': ('adr', 'Commit an in-flight/UNKNOWN transition before sending'),
    'A6-INBOX': ('adr', 'Unknown/unbound/oversize events need a bounded durable inbox'),
    'A8-INVENTORY': ('adr', 'R1 covers contiguous segment selection and GA capacity'),
    'A8-BOUNDS': ('adr', 'Admission is bounded per cell/shard/provider'),
}


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def parse_cell(cell):
    """Return every backticked path/symbol pair, including missing symbols."""
    out = []
    for match in CITATION.finditer(cell):
        path, _, symbol = match.group(1).partition('::')
        out.append((path.strip(), symbol.strip() or None))
    return out


def git_blob_sha(data):
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def contract_path_ok(path):
    return path in CONTRACT_PATHS or (
        re.fullmatch(re.escape(V5) + r'[a-z0-9_]+\.rs', path) is not None
        and path not in SOURCE_PATHS)


def find_problems(map_text, sources, root=ROOT, files=None):
    """Return diagnostics. files maps repo-relative names to injected bytes/None."""
    files = files or {}
    problems = []
    cache = {}

    def read(path):
        if path in files:
            return files[path]
        if path not in cache:
            try:
                cache[path] = (root / path).read_bytes()
            except OSError:
                cache[path] = None
        return cache[path]

    for path, want in LOCKED_BLOBS.items():
        data = read(path)
        if data is None:
            problems.append('locked file missing: ' + path)
        elif git_blob_sha(data) != want:
            problems.append('locked blob mismatch: ' + path)

    for ident, (source, anchor) in EXPECTED.items():
        if anchor not in sources.get(source, ''):
            problems.append('%s: %s anchor is gone' % (ident, source))
    open_ids = set(OPEN_TABLE_ID.findall(sources.get('open', '')))
    for token in sorted(set(OPEN_ID.findall(map_text)) - open_ids):
        problems.append('unknown open input: ' + token)
    inv_ids = set(INV_TABLE_ID.findall(sources.get('inv', '')))

    rows = []
    in_map = False
    headers = 0
    if map_text.splitlines().count(MAP_HEAD) != 1:
        problems.append('expected one map section')
    for line in map_text.splitlines():
        if line == MAP_HEAD:
            in_map = True
            continue
        if in_map and line.startswith('## '):
            in_map = False
        if not in_map or not line.startswith('|'):
            continue
        cells = split_row(line)
        if cells[0] == 'ID':
            headers += 1
            if cells != HEADER:
                problems.append('bad map header')
        elif all(re.fullmatch(r'[-:]+', c) for c in cells):
            continue
        else:
            rows.append(cells)
    if headers != 1:
        problems.append('expected one map header')
    ids = [cells[0] for cells in rows]
    for ident in EXPECTED:
        if ident not in ids:
            problems.append('missing row: ' + ident)
        elif ids.count(ident) != 1:
            problems.append('duplicated row: ' + ident)
    for ident in sorted(set(ids) - set(EXPECTED)):
        problems.append('invented row: ' + ident)

    by_status = dict.fromkeys(STATUSES, 0)
    for cells in rows:
        ident = cells[0]
        if len(cells) != len(HEADER):
            problems.append('%s: expected eight cells' % ident)
            continue
        if not cells[CLAUSE]:
            problems.append('%s: empty clause' % ident)
        tests = []
        for col, name in ((CONTRACT_TESTS, 'contract-path'),
                          (SOURCE_TESTS, 'source-informed')):
            cell = cells[col]
            cites = parse_cell(cell)
            tests.append(cites)
            if cell == 'none':
                continue
            if not TEST_CELL.fullmatch(cell):
                problems.append('%s: bad %s test-cell grammar' % (ident, name))
            for path, symbol in cites:
                where = '%s: %s %s::%s' % (ident, name, path, symbol or '')
                if path.startswith('/') or '..' in path.split('/'):
                    problems.append(where + ' is not repo-relative')
                    continue
                if path.startswith('reference/v0.3-rc1/'):
                    problems.append(where + ' is forbidden reference')
                    continue
                allowed = (contract_path_ok(path) if col == CONTRACT_TESTS
                           else path in SOURCE_PATHS)
                if not allowed:
                    problems.append(where + ' is outside column paths')
                    continue
                if symbol is None or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', symbol):
                    problems.append(where + ' needs a nonempty fn symbol')
                    continue
                data = read(path)
                if data is None:
                    problems.append(where + ' file missing')
                    continue
                try:
                    text = data.decode('utf-8')
                except UnicodeDecodeError:
                    problems.append(where + ' is not UTF-8')
                    continue
                if not re.search(TEST_FN % re.escape(symbol), text, re.M):
                    problems.append(where + ' is not a #[test] fn')

        inv = cells[INV]
        if inv != 'none':
            if not INV_CELL.fullmatch(inv):
                problems.append('%s: bad INV grammar' % ident)
            tokens = [v.strip() for v in inv.split(',')]
            if len(tokens) != len(set(tokens)) or any(v not in inv_ids for v in tokens):
                problems.append('%s: INV missing from contract or duplicated' % ident)
            if INV_TEST not in tests[0]:
                problems.append('%s: INV requires contract-path invariant test' % ident)
        for col in (GAP, OWNER):
            if not cells[col] or '`' in cells[col]:
                problems.append('%s: Gap/Owner must be nonempty text without backticks' % ident)
        status, gap, owner = cells[STATUS:OWNER + 1]
        has_tests = any(tests)
        if status not in STATUSES:
            problems.append('%s: bad status %s' % (ident, status))
        else:
            by_status[status] += 1
            if status == 'COVERED' and (not tests[0] or gap != 'none' or owner != 'none'):
                problems.append('%s: COVERED needs contract-path tests and no gap/owner' % ident)
            if status == 'PARTIAL' and (not has_tests or gap == 'none' or owner == 'none'):
                problems.append('%s: PARTIAL needs tests, gap and owner' % ident)
            if status in ('NOT_COVERED', 'OPEN') and (has_tests or gap == 'none' or owner == 'none'):
                problems.append('%s: %s needs no tests, a gap and owner' % (ident, status))
            if status == 'OPEN' and not re.search(
                    r'\b(?:I09|I10|I11|I12|I13|UNDETERMINED|DECISION_REQUIRED)\b', gap):
                problems.append('%s: OPEN needs an open input/decision gap' % ident)
        if ident in MUST_BE_OPEN and status != 'OPEN':
            problems.append('%s: must stay OPEN' % ident)
        if ident == 'L4-HANDOFF' and 'I12' not in OPEN_ID.findall(owner):
            problems.append('L4-HANDOFF: owner must name I12')

    lines = [line for line in map_text.splitlines() if line.startswith(COUNTS_LINE)]
    want = COUNTS_LINE + ' rows=%d ' % len(rows) + ' '.join(
        '%s=%d' % (s, by_status[s]) for s in STATUSES)
    if lines != [want]:
        problems.append('counts mismatch: expected ' + want)
    return problems


def _row_line(text, ident):
    return next(line for line in text.splitlines()
                if line.startswith('|') and split_row(line)[0] == ident)


def _with_cell(text, ident, col, value):
    line = _row_line(text, ident)
    cells = split_row(line)
    cells[col] = value
    return text.replace(line, '| ' + ' | '.join(cells) + ' |', 1)


def self_test(map_text, sources):
    """Require specific diagnostics, avoiding unrelated failures as a false pass."""
    cases = []

    def cell(label, ident, col, value, reason, files=None):
        cases.append((label, _with_cell(map_text, ident, col, value),
                      sources, files, reason))

    probe = V5 + 'citation_probe.rs'
    valid = '`%s::a`' % probe
    files = {probe: b'#[test]\nfn a() {}\nfn helper() {}\n'}
    positive = _with_cell(map_text, 'L2-UNKNOWN', CONTRACT_TESTS, valid)
    if find_problems(positive, sources, files=files):
        print('self-test: valid injected citation failed', file=sys.stderr)
        return 1
    for col in (CONTRACT_TESTS, SOURCE_TESTS):
        path = probe if col == CONTRACT_TESTS else V5 + 'lifecycle_model.rs'
        injected = {path: files[probe]}
        good = '`%s::a`' % path
        # Exercise both columns, each invalid member alone and in mixed lists.
        for label, value, reason in (
            ('missing symbol', '`%s::absent`' % path, 'is not a #[test] fn'),
            ('non-test helper', '`%s::helper`' % path, 'is not a #[test] fn'),
            ('bare path', '`%s`' % path, 'needs a nonempty fn symbol'),
            ('empty symbol', '`%s::`' % path, 'needs a nonempty fn symbol'),
            ('blank symbol', '`%s::  `' % path, 'needs a nonempty fn symbol'),
        ):
            for suffix, value in (('alone', value), ('mixed', good + ', ' + value)):
                cell('%s %s %s' % (col, label, suffix), 'L2-UNKNOWN', col,
                     value, reason, injected)
    cell('missing file', 'L2-UNKNOWN', CONTRACT_TESTS, valid,
         'file missing', {probe: None})
    cell('bad status', 'L2-UNKNOWN', STATUS, 'SUFFICIENT', 'bad status')
    for path in LOCKED_BLOBS:
        cases.append(('wrong blob ' + path, map_text, sources,
                      {path: (ROOT / path).read_bytes() + b'\n'}, 'locked blob mismatch'))
    cases.append(('removed anchor', map_text,
                  dict(sources, contract=sources['contract'].replace(
                      EXPECTED['L1-A4'][1], 'removed')), None, 'L1-A4: contract anchor is gone'))
    line = _row_line(map_text, 'L1-A4')
    for label, changed, reason in (
        ('invented row', map_text.replace(line, line.replace('L1-A4', 'EXTRA')), 'invented row'),
        ('duplicate row', map_text.replace(line, line + '\n' + line), 'duplicated row'),
        ('removed row', map_text.replace(line + '\n', ''), 'missing row'),
        ('wrong counts', map_text.replace('Counts: rows=27', 'Counts: rows=28'), 'counts mismatch'),
        ('bad header', map_text.replace('| ID | Clause |', '| ID | Wrong |'), 'bad map header'),
        ('wrong width', map_text.replace(line, line + ' extra |'), 'expected eight cells'),
    ):
        cases.append((label, changed, sources, None, reason))
    cell('source in contract column', 'L2-UNKNOWN', CONTRACT_TESTS,
         '`%s::a`' % (V5 + 'lifecycle_model.rs'), 'outside column paths')
    cell('contract in source column', 'L2-UNKNOWN', SOURCE_TESTS,
         '`%s::a`' % (V4 + 'transitions.rs'), 'outside column paths')
    cell('reference citation', 'L2-UNKNOWN', CONTRACT_TESTS,
         '`reference/v0.3-rc1/test.rs::a`', 'forbidden reference')
    cell('absolute path', 'L2-UNKNOWN', CONTRACT_TESTS,
         '`/tmp/test.rs::a`', 'not repo-relative')
    cell('traversal path', 'L2-UNKNOWN', CONTRACT_TESTS,
         '`runtime/../test.rs::a`', 'not repo-relative')
    cell('mixed prose', 'L2-UNKNOWN', CONTRACT_TESTS, valid + ' prose', 'test-cell grammar', files)
    cell('bad INV', 'L2-CMD', INV, 'INV-9', 'bad INV grammar')
    cell('INV without invariant test', 'L2-CMD', CONTRACT_TESTS, valid,
         'INV requires', files)
    cases.append(('removed INV anchor', map_text,
                  dict(sources, inv=sources['inv'].replace('| INV-3 |', '| removed |')),
                  None, 'INV missing from contract'))
    cell('covered with gap', 'L2-UNKNOWN', GAP, 'unverified', 'COVERED needs')
    cell('open without owner', 'L3-INBOX', OWNER, 'none', 'OPEN needs no tests')
    cell('handoff without I12', 'L4-HANDOFF', OWNER, 'User', 'owner must name I12')
    cell('handoff not open', 'L4-HANDOFF', STATUS, 'NOT_COVERED', 'must stay OPEN')
    cell('unknown open input', 'L3-INBOX', GAP, 'I99 absent', 'unknown open input: I99')
    cell('open without decision gap', 'L3-INBOX', GAP, 'unspecified', 'OPEN needs an open input')
    cell('gap with backticks', 'L3-INBOX', GAP, '`I13` absent', 'without backticks')
    cell('partial without tests', 'L1-A4', STATUS, 'PARTIAL', 'PARTIAL needs')
    cell('not covered with tests', 'L2-UNKNOWN', STATUS, 'NOT_COVERED', 'NOT_COVERED needs')
    failed = []
    for label, changed, src, injected, reason in cases:
        found = find_problems(changed, src, files=injected)
        if not any(reason in p for p in found):
            failed.append('%s: missed %r; got %r' % (label, reason, found))
    if failed:
        print('\n'.join(failed), file=sys.stderr)
        return 1
    print('self-test: positive injected citation and %d negative fixtures passed (memory only)' % len(cases))
    return 0


def main():
    if sys.argv[1:] not in ([], ['--self-test']):
        print('usage: check_lifecycle_adr_evidence_map.py [--self-test]', file=sys.stderr)
        return 2
    try:
        map_text = (ROOT / MAP).read_text(encoding='utf-8')
        sources = {key: (ROOT / path).read_text(encoding='utf-8')
                   for key, path in SOURCES.items()}
    except (OSError, UnicodeError) as exc:
        print('cannot read evidence inputs: %s' % exc, file=sys.stderr)
        return 1
    problems = find_problems(map_text, sources)
    if problems:
        print('\n'.join(problems), file=sys.stderr)
        return 1
    if '--self-test' in sys.argv:
        return self_test(map_text, sources)
    print('lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
