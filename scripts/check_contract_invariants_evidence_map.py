#!/usr/bin/env python3
"""Validate contract-invariant traceability, corpus facts and raw locked blobs.

Stdlib only. Textual test/anchor checks do not establish semantic coverage or
independence. Self-tests mutate memory only; cited Rust is never executed.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md'
SOURCES = {'contract': 'docs/contracts/CONTRACT_INVARIANTS.md',
           'open': 'docs/contracts/FIRST_BATCH_OPEN_INPUTS.md'}
LOCKED_BLOBS = {
    'runtime/crates/kix-kernel/src/lib.rs':
        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs':
        'b607996c83a119c349f1cc90469ac1ba82764e20',
}
ANCHOR_PATHS = {
    'L': 'docs/contracts/STATE_LIFECYCLE.md',
    'A': 'docs/adr/0001-ktx-authority-commit-recovery.md',
    'R': 'runtime/crates/kix-kernel/README.md',
}
ANCHOR_HEADER = ['ID', 'Path', 'Historical blob', 'Current blob']
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED', 'OPEN')
MUST_BE_OPEN = {'S5-SHARED-ERROR', 'S5-PERSISTENCE'}
HEADER = ['ID', 'Section', 'Contract-path tests', 'Source-informed tests',
          'Status', 'Gap', 'Owner']
CLAUSE, CONTRACT_TESTS, SOURCE_TESTS, STATUS, GAP, OWNER = range(1, 7)
V4 = 'runtime/crates/kix-kernel/tests/'
V5 = 'runtime/crates/kix-kernel-v5/tests/'
CONTRACT_PATHS = {V4 + name + '.rs' for name in
                  ('contract_invariants', 'contract_edge_cases',
                   'transitions', 'observation_slots')}
SOURCE_PATHS = {V4 + 'e4_state_model.rs', V5 + 'lifecycle_model.rs',
                V5 + 'v4_differential.rs'}
MAIN_FN = 'five_contract_invariants_on_kernel_only_generated_histories'
INVARIANTS = V4 + 'contract_invariants.rs'
E4 = V4 + 'e4_state_model.rs'
CITATION = re.compile(r'`([^`]+)`')
TEST_FN = r'^\s*#\[test\]\s*\n\s*fn\s+%s\b'
TEST_CELL = re.compile(r'`[^`]+`(?:,\s*`[^`]+`)*')
OPEN_ID = re.compile(r'\bI\d{2}\b')
OPEN_TABLE_ID = re.compile(r'^\|\s*(I\d{2})\s*\|', re.M)
INV_TABLE_ID = re.compile(r'^\|\s*(INV-\d+)\s*\|', re.M)
MAP_HEAD = '## 2. Map'
CORPUS_HEAD = '## 3. Corpus check'
CORPUS_HEADER = ['Key', 'Contract statement', 'Source fact', 'Result']
COUNTS_LINE = 'Counts:'
# Each id has one or more literal contract anchors (whitespace normalized).
EXPECTED = {
    'S1-MODEL-PROVENANCE': ('NOT independently derived specification provenance',),
    'S1-ORACLE-PATH': ('independent oracle PATH',),
    'S2-ANCHORS': ('## 2. Exact existing contract anchors',),
    'INV-1': ('| INV-1 |',),
    'INV-2': ('| INV-2 |',),
    'INV-3': ('| INV-3 |',),
    'INV-4': ('| INV-4 |',),
    'INV-5': ('| INV-5 |',),
    'S3-OBS-BOUNDARY': ('All attempted order IDs are recorded',),
    'S3-CAPTURE-SCOPE': ('It is NOT independently verified bank settlement',),
    'S4-CORPUS': ('4 fixture configurations × 64 seeds × 96 main calls = 24,576',),
    'S4-FIXTURES': ('Two seat fixtures use actual segments [65,5]',),
    'S4-INIT': ('Six known input actions initialize',),
    'S4-PROBES': ('Read-only replay probes are reported separately',),
    'S4-SENS-OVERLAP': ('overlap, exceeded budget, missing capture, double transition count',),
    'S4-SENS-BUDGET': ('overlap, exceeded budget, missing capture, double transition count',),
    'S4-SENS-CAPTURE': ('overlap, exceeded budget, missing capture, double transition count',),
    'S4-SENS-DOUBLE': ('overlap, exceeded budget, missing capture, double transition count',),
    'S4-CI-HEAD': ('Execution results are attached to their exact later CI head',),
    'S5-SAFE-REJECT': ('incorrect but safe rejections',),
    'S5-PRECEDENCE': ('wrong', 'error precedence'),
    'S5-STICKY-HOLD': ('unnecessarily sticky hold',),
    'S5-PHASE-REVIEW': ('exact phase/review semantics',),
    'S5-SHARED-ERROR': ('it cannot resolve shared errors by itself',),
    'S5-FINITE': ('No finite test proves all inputs',),
    'S5-PERSISTENCE': ('Single-process tests do not establish',),
    'S5-E4-RETAINED': ('complementary regression asset',),
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

    contract = sources.get('contract', '')
    for ident, anchors in EXPECTED.items():
        if any(' '.join(anchor.split()) not in ' '.join(contract.split())
               for anchor in anchors):
            problems.append('%s: contract anchor is gone' % ident)
    open_ids = set(OPEN_TABLE_ID.findall(sources.get('open', '')))
    for token in sorted(set(OPEN_ID.findall(map_text)) - open_ids):
        problems.append('unknown open input: ' + token)
    inv_ids = set(INV_TABLE_ID.findall(contract))

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

    for ident in sorted(inv_ids - set(ids)):
        problems.append('missing INV row: ' + ident)
    for section in re.findall(r'^## (\d+)\.', contract, re.M):
        if not any(ident.startswith('S' + section + '-') or
                   (section == '3' and ident in inv_ids) for ident in ids):
            problems.append('unmapped contract section: ' + section)

    by_status = dict.fromkeys(STATUSES, 0)
    for cells in rows:
        ident = cells[0]
        if len(cells) != len(HEADER):
            problems.append('%s: expected seven cells' % ident)
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

    lines = [line for line in map_text.splitlines() if line.startswith(COUNTS_LINE)]
    want = COUNTS_LINE + ' rows=%d ' % len(rows) + ' '.join(
        '%s=%d' % (s, by_status[s]) for s in STATUSES)
    if lines != [want]:
        problems.append('counts mismatch: expected ' + want)
    anchor_blob_problems(map_text, contract, read, problems)
    corpus_problems(map_text, contract, read, problems)
    return problems


def _row_line(text, ident):
    return next(line for line in text.splitlines()
                if line.startswith('|') and split_row(line)[0] == ident)


def _with_cell(text, ident, col, value):
    line = _row_line(text, ident)
    cells = split_row(line)
    cells[col] = value
    return text.replace(line, '| ' + ' | '.join(cells) + ' |', 1)


def section_text(text, heading):
    """Require one heading; return only its contents through the next section."""
    if text.splitlines().count(heading) != 1:
        return None
    return re.split(r'^## ', text.split(heading, 1)[1].removeprefix('\n'), maxsplit=1,
                    flags=re.M)[0]


def function_slice(text, name):
    match = re.search(r'^fn ' + re.escape(name) + r'\b', text, re.M)
    return re.split(r'^#\[test\]', text[match.start():], maxsplit=1,
                    flags=re.M)[0] if match else ''


def capture(pattern, text):
    match = re.search(pattern, text, re.S)
    return match.groups() if match else ()


def anchor_blob_problems(map_text, contract, read, problems):
    """F-B1 provenance pin, independent of the map's Rust-test vocabulary."""
    findings = section_text(map_text, '## 4. Findings') or ''
    lines = [split_row(line) for line in findings.splitlines() if line.startswith('|')]
    if lines.count(ANCHOR_HEADER) != 1:
        problems.append('F-B1: expected one anchor blob header')
    rows = [r for r in lines if r != ANCHOR_HEADER and
            not all(re.fullmatch(r'[-:]+', c) for c in r)]
    if sorted(r[0] for r in rows) != sorted(ANCHOR_PATHS):
        problems.append('F-B1: anchor row set mismatch')
    historical_section = section_text(contract, '## 2. Exact existing contract anchors') or ''
    historical_rows = [split_row(line) for line in historical_section.splitlines()
                       if line.startswith('|')]
    for row in rows:
        if len(row) != 4 or row[0] not in ANCHOR_PATHS:
            problems.append('F-B1: malformed anchor row')
            continue
        ident, path, historical, current = row
        if path != ANCHOR_PATHS[ident]:
            problems.append('F-B1: anchor path mismatch: ' + ident)
            continue
        expected = [r for r in historical_rows if r[0] == ident]
        if (len(expected) != 1 or len(expected[0]) != 4 or
                expected[0][1:3] != [path, historical]):
            problems.append('F-B1: historical anchor mismatch: ' + ident)
        if not all(re.fullmatch(r'[0-9a-f]{40}', value) for value in (historical, current)):
            problems.append('F-B1: malformed blob: ' + ident)
        data = read(path)
        if data is None:
            problems.append('F-B1: current document missing: ' + ident)
        elif git_blob_sha(data) != current:
            problems.append('F-B1: current blob mismatch: ' + ident)
        if current == historical:
            problems.append('F-B1: current equals historical: ' + ident)


def corpus_problems(map_text, contract, read, problems):
    """Recompute source facts, compare the contract, and fence unrecorded drift.

    Narrow source patterns intentionally fail closed on unfamiliar source shapes.
    A recorded B/C finding permits diagnostics, never implies merge readiness.
    """
    texts = []
    for path in (INVARIANTS, E4):
        data = read(path)
        try:
            texts.append(data.decode('utf-8') if data is not None else '')
        except UnicodeDecodeError:
            texts.append('')
    inv, e4 = texts
    if not inv or not e4:
        problems.append('corpus source missing or not UTF-8')
    if re.search(r'^\s*#\[path\s*=\s*"[^"\n]*(?:model_v4|evidence_gates)[^"\n]*"', inv, re.M) or re.search(
            r'^\s*(?:pub\s+)?mod\s+reference\b', inv, re.M):
        problems.append('oracle path imports source-informed reference')
    body = function_slice(inv, MAIN_FN)
    fixtures = body.count('Fixture {')
    seats = len(re.findall(r'ga:\s*false', body))
    ga = len(re.findall(r'ga:\s*true', body))
    seed = capture(r'for seed in 1\.\.=(\d+)_u64', body)
    generated = capture(r'for index in 0\.\.(\d+)_u64', body)
    initial = capture(r'let mut inputs = vec!\[(.*?)\];', body)
    init_count = initial[0].count('(ctx(') if initial else None
    assertion = capture(r'assert_eq!\(primary,\s*(\d+)\s*\*\s*(\d+)\s*\*\s*(\d+)\)', body)
    layout = capture(r'Inventory::seats\(&\[([\d,\s]+)\]\)', inv)
    capacity = capture(r'Inventory::general_admission\((\d+)\)', inv)
    cases = capture(r'const CASES: u64 = (\d+);', e4)
    steps = capture(r'const STEPS: usize = (\d+);', e4)
    configs = capture(r'fn baseline_cases\(\) -> \[Case; (\d+)\]', e4)
    baseline = function_slice(e4, 'baseline_cases')
    baseline_count = len(re.findall(r'\bCase\s*\{', baseline))
    corpus = capture(r'(\d+) fixture configurations × (\d+) seeds × (\d+) main calls = ([\d,]+)', contract)
    e4_total = capture(r'The ([\d,]+) prior comparisons', contract)
    contract_layout = capture(r'actual segments \[([\d,\s]+)\]', contract)
    contract_capacity = capture(r'two GA fixtures use\s+capacity (\d+)', contract)
    # Unknown source/document syntax is observable rather than guessed.
    shape = all((seed, generated, initial, assertion, layout, capacity,
                 cases, steps, configs, corpus, e4_total, contract_layout,
                 contract_capacity))
    if not shape:
        problems.append('corpus mismatch: cannot extract corpus source/contract shape')
        return
    seed, generated = int(seed[0]), int(generated[0])
    main_calls = init_count + generated
    product = fixtures * seed * main_calls
    cfixtures, cseed, ccalls, cproduct = (int(n.replace(',', '')) for n in corpus)
    ecases, esteps, econfigs = int(cases[0]), int(steps[0]), int(configs[0])
    comparisons = econfigs * ecases * esteps
    layout = [int(n.strip()) for n in layout[0].split(',')]
    contract_layout = [int(n.strip()) for n in contract_layout[0].split(',')]
    capacity, contract_capacity = int(capacity[0]), int(contract_capacity[0])
    # Keep the original design's required literal forms as well as derived math.
    facts = {
        'C-FIXTURES': (f'{cfixtures} fixtures; seats=2; GA=2',
                       f'{fixtures} fixtures; seats={seats}; GA={ga}',
                       fixtures == cfixtures == 4 and seats == ga == 2),
        'C-SEEDS': (f'{cseed} seeds', f'{seed} seeds', seed == cseed == 64),
        'C-MAIN-CALLS': (f'6 + 90 = {ccalls} calls',
                         f'{init_count} + {generated} = {main_calls} calls',
                         init_count == 6 and generated == 90 and main_calls == ccalls == 96
                         and 'Six known input actions initialize' in contract
                         and '90 seeded stimuli follow' in contract),
        'C-PRODUCT': (f'{cproduct} main calls', f'{product} main calls',
                      product == cproduct == 24576 and tuple(map(int, assertion)) == (4, 64, 96)),
        'C-SEAT-SEGMENTS': (str(contract_layout), str(layout), layout == contract_layout == [65, 5]),
        'C-GA-CAPACITY': (f'{contract_capacity} capacity', f'{capacity} capacity',
                          capacity == contract_capacity == 6),
        'P-E4-COMPARISONS': (f'{int(e4_total[0].replace(",", ""))} comparisons',
                             f'{econfigs} * {ecases} * {esteps} = {comparisons} comparisons',
                             comparisons == int(e4_total[0].replace(',', '')) == 131072
                             and econfigs == baseline_count == 4 and ecases == 256 and esteps == 128),
    }
    section = section_text(map_text, CORPUS_HEAD)
    if section is None:
        problems.append('expected one corpus section')
        return
    lines = [split_row(line) for line in section.splitlines() if line.startswith('|')]
    if lines.count(CORPUS_HEADER) != 1:
        problems.append('bad corpus header')
    rows = [r for r in lines if r != CORPUS_HEADER and
            not all(re.fullmatch(r'[-:]+', c) for c in r)]
    if sorted(r[0] for r in rows) != sorted(facts):
        problems.append('corpus row set mismatch')
    findings = section_text(map_text, '## 4. Findings')
    if findings is None:
        problems.append('expected one findings section')
        findings = ''
    for cells in rows:
        if len(cells) != 4 or cells[0] not in facts:
            problems.append('bad corpus row: ' + cells[0])
            continue
        key, stated, observed, result = cells
        want_stated, want_observed, matches = facts[key]
        if stated != want_stated or observed != want_observed:
            problems.append('corpus table fact mismatch: ' + key)
        if matches:
            if result != 'MATCH':
                problems.append('corpus result must MATCH: ' + key)
        elif result not in ('FINDING-B', 'FINDING-C') or not re.search(
                r'^.*\b' + re.escape(key) + r'\b.*\bclass ' +
                ('B' if result == 'FINDING-B' else 'C') + r'\b', findings, re.M):
            problems.append('corpus mismatch: ' + key)


def self_test(map_text, sources):
    """Positive controls and specific-diagnostic negatives, all memory only."""
    cases = []

    def cell(label, ident, col, value, reason, files=None):
        cases.append((label, _with_cell(map_text, ident, col, value), sources, files, reason))

    probe = V5 + 'citation_probe.rs'
    valid = '`%s::a`' % probe
    files = {probe: b'#[test]\nfn a() {}\nfn helper() {}\n'}
    positive = _with_cell(map_text, 'INV-2', CONTRACT_TESTS, valid)
    if find_problems(positive, sources, files=files):
        print('self-test: valid injected citation failed', file=sys.stderr)
        return 1
    for col in (CONTRACT_TESTS, SOURCE_TESTS):
        path = probe if col == CONTRACT_TESTS else V5 + 'lifecycle_model.rs'
        injected = {path: files[probe]}
        good = '`%s::a`' % path
        for label, value, reason in (
            ('missing symbol', '`%s::absent`' % path, 'is not a #[test] fn'),
            ('non-test helper', '`%s::helper`' % path, 'is not a #[test] fn'),
            ('bare path', '`%s`' % path, 'needs a nonempty fn symbol'),
            ('empty symbol', '`%s::`' % path, 'needs a nonempty fn symbol'),
            ('blank symbol', '`%s::  `' % path, 'needs a nonempty fn symbol'),
        ):
            for suffix, value in (('alone', value), ('mixed', good + ', ' + value)):
                cell('%s %s %s' % (col, label, suffix), 'INV-2', col,
                     value, reason, injected)
    cell('missing file', 'INV-2', CONTRACT_TESTS, valid, 'file missing', {probe: None})
    cell('bad status', 'INV-2', STATUS, 'SUFFICIENT', 'bad status')
    for path in LOCKED_BLOBS:
        cases.append(('wrong blob ' + path, map_text, sources,
                      {path: (ROOT / path).read_bytes() + b'\n'}, 'locked blob mismatch'))
    cases.append(('removed anchor', map_text,
                  dict(sources, contract=sources['contract'].replace(
                      EXPECTED['S1-MODEL-PROVENANCE'][0], 'removed')), None, 'contract anchor is gone'))
    line = _row_line(map_text, 'S1-ORACLE-PATH')
    inv_line = _row_line(map_text, 'INV-3')
    for label, changed, reason in (
        ('invented row', map_text.replace(line, line.replace('S1-ORACLE-PATH', 'EXTRA')), 'invented row'),
        ('duplicate row', map_text.replace(line, line + '\n' + line), 'duplicated row'),
        ('removed row', map_text.replace(line + '\n', ''), 'missing row'),
        ('missing INV', map_text.replace(inv_line + '\n', ''), 'missing INV row: INV-3'),
        ('wrong counts', re.sub(r'Counts: rows=\d+', 'Counts: rows=999', map_text), 'counts mismatch'),
        ('bad header', map_text.replace('| ID | Section |', '| ID | Wrong |'), 'bad map header'),
        ('wrong width', map_text.replace(line, line + ' extra |'), 'expected seven cells'),
        ('duplicate section', map_text + '\n' + MAP_HEAD + '\n', 'expected one map section'),
        ('bad corpus header', map_text.replace('| Key | Contract statement |', '| Key | Wrong |'), 'bad corpus header'),
        ('duplicate corpus row', map_text.replace(_row_line(map_text, 'C-SEEDS'),
             (_row_line(map_text, 'C-SEEDS') + '\n') * 2), 'corpus row set mismatch'),
    ):
        cases.append((label, changed, sources, None, reason))
    for col, path in ((CONTRACT_TESTS, V5 + 'lifecycle_model.rs'),
                      (SOURCE_TESTS, V4 + 'transitions.rs')):
        cell('wrong column', 'INV-2', col, '`%s::a`' % path, 'outside column paths')
    for label, path, reason in (
        ('reference', 'reference/v0.3-rc1/test.rs', 'forbidden reference'),
        ('absolute', '/tmp/test.rs', 'not repo-relative'),
        ('traversal', 'runtime/../test.rs', 'not repo-relative'),
    ):
        for col in (CONTRACT_TESTS, SOURCE_TESTS):
            cell(label, 'INV-2', col, '`%s::a`' % path, reason)
    cell('prose in list', 'INV-2', CONTRACT_TESTS, valid + ' prose', 'test-cell grammar', files)
    cell('covered with gap', 'INV-1', GAP, 'unverified', 'COVERED needs')
    cell('open without decision', 'S5-SHARED-ERROR', GAP, 'unspecified', 'OPEN needs an open input')
    cell('unknown input', 'S5-PERSISTENCE', GAP, 'I99 absent', 'unknown open input: I99')
    cell('partial no tests', 'S2-ANCHORS', STATUS, 'PARTIAL', 'PARTIAL needs')
    cell('not covered with tests', 'INV-2', STATUS, 'NOT_COVERED', 'NOT_COVERED needs')
    cell('open lost owner', 'S5-SHARED-ERROR', OWNER, 'none', 'OPEN needs no tests')
    cell('open changed', 'S5-SHARED-ERROR', STATUS, 'NOT_COVERED', 'must stay OPEN')
    cell('gap backticks', 'INV-2', GAP, '`I13`', 'without backticks')
    inv = (ROOT / INVARIANTS).read_bytes()
    e4 = (ROOT / E4).read_bytes()
    altered = inv.replace(b'1..=64_u64', b'1..=63_u64')
    cases.append(('wrong seeds', map_text, sources, {INVARIANTS: altered}, 'corpus mismatch: C-SEEDS'))
    # Updating the diagnostic rows/finding records a mismatch without changing the
    # contract or source, and must pass. Both affected derived facts are recorded.
    recorded = map_text.replace('| C-SEEDS | 64 seeds | 64 seeds | MATCH |',
        '| C-SEEDS | 64 seeds | 63 seeds | FINDING-B |').replace(
        '| C-PRODUCT | 24576 main calls | 24576 main calls | MATCH |',
        '| C-PRODUCT | 24576 main calls | 24192 main calls | FINDING-B |').replace(
        '## 4. Findings\n', '## 4. Findings\n\n- C-SEEDS: class B source count drift.\n- C-PRODUCT: class B derived count drift.\n')
    if find_problems(recorded, sources, files={INVARIANTS: altered}):
        print('self-test: recorded B corpus mismatch failed', file=sys.stderr)
        return 1
    cases.append(('contract product drift', map_text,
        dict(sources, contract=sources['contract'].replace('24,576', '24,577')),
        None, 'corpus mismatch: C-PRODUCT'))
    cases.append(('E4 cases drift', map_text, sources,
        {E4: e4.replace(b'const CASES: u64 = 256;', b'const CASES: u64 = 255;')},
        'corpus mismatch: P-E4-COMPARISONS'))
    cases.append(('oracle import', map_text, sources,
        {INVARIANTS: b'#[path = "support/model_v4.rs"]\nmod model;\n' + inv}, 'oracle path imports'))
    for label, before, after, reason in (
        ('fixture count', b'        Fixture {\n            ga: false,',
         b'        Fixture {\n            ga: true,', 'C-FIXTURES'),
        ('initial action', b'                (ctx(6, 1), Input::Capture(conflicting)),\n',
         b'', 'C-MAIN-CALLS'),
        ('generated steps', b'0..90_u64', b'0..89_u64', 'C-MAIN-CALLS'),
        ('primary assertion', b'assert_eq!(primary, 4 * 64 * 96)',
         b'assert_eq!(primary, 4 * 64 * 95)', 'C-PRODUCT'),
        ('seat segments', b'Inventory::seats(&[65, 5])',
         b'Inventory::seats(&[64, 6])', 'C-SEAT-SEGMENTS'),
        ('GA capacity', b'Inventory::general_admission(6)',
         b'Inventory::general_admission(7)', 'C-GA-CAPACITY'),
    ):
        cases.append((label, map_text, sources,
                      {INVARIANTS: inv.replace(before, after)}, 'corpus mismatch: ' + reason))
    cases.append(('stale corpus fact', map_text.replace(
        '| C-SEEDS | 64 seeds | 64 seeds | MATCH |',
        '| C-SEEDS | 64 seeds | 63 seeds | MATCH |'), sources, None,
        'corpus table fact mismatch: C-SEEDS'))
    cases.append(('unrecorded finding', recorded.replace(
        '- C-SEEDS: class B source count drift.', ''), sources,
        {INVARIANTS: altered}, 'corpus mismatch: C-SEEDS'))
    cases.append(('reference module', map_text, sources,
                  {INVARIANTS: b'mod reference;\n' + inv}, 'oracle path imports'))
    cases.append(('new numbered section', map_text,
        dict(sources, contract=sources['contract'] + '\n## 6. Added\n'), None, 'unmapped contract section: 6'))
    for ident, path in ANCHOR_PATHS.items():
        line = _row_line(map_text, ident)
        row = split_row(line)
        def anchor_case(label, cells, reason):
            changed = map_text.replace(line, '| ' + ' | '.join(cells) + ' |', 1)
            cases.append((label + ' ' + ident, changed, sources, None, 'F-B1: ' + reason))
        cases.append(('document drift ' + ident, map_text, sources,
                      {path: (ROOT / path).read_bytes() + b'\n'},
                      'F-B1: current blob mismatch: ' + ident))
        cases.append(('document missing ' + ident, map_text, sources,
                      {path: None}, 'F-B1: current document missing: ' + ident))
        anchor_case('recorded current', row[:3] + ['0' * 40], 'current blob mismatch: ' + ident)
        anchor_case('historical hash', row[:2] + ['0' * 40, row[3]], 'historical anchor mismatch: ' + ident)
        anchor_case('same blobs', row[:3] + [row[2]], 'current equals historical: ' + ident)
        anchor_case('wrong path', [ident, 'wrong.md'] + row[2:], 'anchor path mismatch: ' + ident)
        anchor_case('malformed hash', row[:3] + ['xyz'], 'malformed blob: ' + ident)
        for label, changed in (
            ('missing anchor', map_text.replace(line + '\n', '')),
            ('duplicate anchor', map_text.replace(line, line + '\n' + line)),
        ):
            cases.append((label + ' ' + ident, changed, sources, None,
                          'F-B1: anchor row set mismatch'))
        cases.append(('contract anchor drift ' + ident, map_text,
                      dict(sources, contract=sources['contract'].replace(row[2], '0' * 40)),
                      None, 'F-B1: historical anchor mismatch: ' + ident))
    cases.append(('bad anchor header', map_text.replace(
        '| ID | Path | Historical blob | Current blob |',
        '| ID | Path | Historical blob | Wrong |'), sources, None,
        'F-B1: expected one anchor blob header'))
    failed = []
    for label, changed, src, injected, reason in cases:
        found = find_problems(changed, src, files=injected)
        if not any(reason in p for p in found):
            failed.append('%s: missed %r; got %r' % (label, reason, found))
    if failed:
        print('\n'.join(failed), file=sys.stderr)
        return 1
    print('contract invariants self-test: 2 positive controls and %d negative fixtures OK (memory only)' % len(cases))
    return 0


def main():
    if sys.argv[1:] not in ([], ['--self-test']):
        print('usage: check_contract_invariants_evidence_map.py [--self-test]', file=sys.stderr)
        return 2
    try:
        map_text = (ROOT / MAP).read_text(encoding='utf-8')
        sources = {key: (ROOT / path).read_text(encoding='utf-8') for key, path in SOURCES.items()}
    except (OSError, UnicodeError) as exc:
        print('cannot read evidence inputs: %s' % exc, file=sys.stderr)
        return 1
    problems = find_problems(map_text, sources)
    if problems:
        print('\n'.join(problems), file=sys.stderr)
        return 1
    if '--self-test' in sys.argv:
        return self_test(map_text, sources)
    print('contract invariants map: %d rows, corpus, anchors, test symbols, counts, locked blobs and F-B1 document pins OK' % len(EXPECTED))
    return 0


if __name__ == '__main__':
    sys.exit(main())
