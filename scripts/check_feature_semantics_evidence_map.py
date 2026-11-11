#!/usr/bin/env python3
"""Check Feature Semantics clause/test citations offline with the stdlib only.

Adapted from check_performance_measurement_evidence_map.py. Citation existence
is not semantic coverage. All self-test mutations are in memory, never on Rust,
contracts, reference evidence or locked files. This checker never runs Cargo.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md'
CONTRACT = 'runtime/FEATURE_SEMANTICS_V1.md'
TEST_FILES = (
    'runtime/crates/kix-feature-semantics/src/lib.rs',
    'runtime/crates/kix-feature-semantics/tests/semantics_v1_edges.rs',
    'runtime/crates/kix-feature-ir/src/lib.rs',
    'runtime/crates/kix-feature-ir/tests/audit_regressions.rs',
    'runtime/crates/kix-feature-ir/tests/plan_limits.rs',
    'runtime/crates/kix-feature-ir/tests/schema_bound.rs',
    'runtime/crates/kix-feature-ir/tests/validator_matrix.rs',
    'runtime/crates/kix-feature-ir/tests/api_boundaries.rs',
)
EXPECTED = {
    'S1-AUTHORITY': (1, 'backend adapter는 upstream default를 사용하지 않고 KIX policy를 명시적으로 전달한다.'),
    'S2-FILTER-NULL': (2, 'Filter predicate가 `NULL`이면 행은 탈락한다.'),
    'S2-JOIN-NULL-EQUALITY': (2, 'Join은 `nullEquality`를 IR에 명시한다.'),
    'S2-GROUP-NULL-KEYS': (2, 'GroupBy는 null key 포함 여부를 IR에 명시한다.'),
    'S2-AGG-NULL-IGNORE': (2, 'Aggregate null value는 v1에서 `IGNORE`를 기본 계약으로 사용한다.'),
    'S2-SORT-NULL-ORDER': (2, 'Sort는 null 위치를 `FIRST` 또는 `LAST`로 명시한다.'),
    'S3-SORT-FIELDS-STABLE': (3, '동일 키의 상대 순서를 보장해야 하는 계획은 `stable=true`여야 한다.'),
    'S4-EMPTY-AGGREGATES': (4, '`SUM(empty/all-null) = NULL`'),
    'S4-OVERFLOW-ERROR': (4, '정수 overflow는 wrap/saturate하지 않고 `ERROR`'),
    'S4-NO-FLOAT-MONEY': (4, '경제적 금액은 float aggregate로 계산하지 않는다.'),
    'S5-F64-KEYS-FOLLOWON': (5, 'F64 identity/equality key'),
    'S5-DIVIDE-TO-F64': (5, 'DIVIDE_TO_F64(numerator, denominator)'),
    'S5-MEAN-PATH': (5, 'MEAN(integer-like input)'),
    'S5-FINITE-ONLY': (5, '생성된 F64는 finite여야 하며 NaN 또는 +/-Inf가 발견되면 conformance/export failure다.'),
    'S6-FAST64-RANGE-IDENTITY': (6, 'atoms <= executionMaxAtoms(registry_version) <= i64::MAX'),
    'S6-EXPORT-BOUNDARY': (6, 'Rust 변환 경계는 `export_amount(AssetAmount)`이며 raw `u128` 변환 API를 제공하지 않는다.'),
    'S6-MONEYWIDE128': (6, '`MoneyWide128`은 lossless export만 허용한다.'),
    'S7-CATEGORY-IDENTITY': (7, 'decoded logical value'),
    'S8-EXACT-AND-ORDER-COMPARISON': (8, 'integer, fixed ID, money atoms: exact equality'),
    'S8-F64-TOLERANCE': (8, 'terminal F64: finite-only + versioned tolerance policy'),
    'S8-REF-VS-POLARS-CI': (8, '최소 CI는 pure-Rust reference semantics와 Polars Rust backend를 항상 비교한다.'),
    'G9-1': (9, 'Semantics v1 fixture 전체 통과'),
    'G9-2': (9, 'upstream default를 참조하는 adapter 코드가 없음'),
    'G9-3': (9, 'null/join/group/sort/aggregate edge fixture 통과'),
    'G9-4': (9, 'Fast64 registry-version fixture 통과'),
    'G9-5': (9, 'F64 NaN/Inf 생성 거절 fixture 통과'),
    'G9-6': (9, 'category dictionary 재인코딩 fixture 통과'),
    'S9-V2-RULE': (9, 'Feature semantics를 바꾸려면 engine upgrade가 아니라 `KIX Feature Semantics v2`를 만든다.'),
    'S10-STRUCTURAL-ONLY': (10, '`validate()`는 구조 및 추론 가능한 타입의 사전 검사다.'),
    'S10-CATALOG-AUTH': (10, 'catalog는 plan 요청과 별도로 신뢰할 수 있는 export/catalog 경계에서 공급한다.'),
    'S10-SCHEMA-BOUND': (10, 'source 및 join-right dataset id/schema version'),
    'S10-EXPR-RULES': (10, '모든 표현식은 같은 재귀 검사를 거친다.'),
    'S10-PROJECT-SCOPE': (10, 'Project 항목은 모두 stage 입력을 참조한다.'),
    'S10-GROUP-OUTPUT': (10, 'GroupBy 출력은 key + aggregate다.'),
    'S10-JOIN-OUTPUT': (10, 'Inner/Left join은 양쪽 컬럼을 출력하며 충돌하는 ColumnId는 거절한다.'),
    'S10-LIMITS': (10, 'plan은 최대 1,024 stages, 표현식은 깊이 64 및 총 100,000 nodes를 허용한다.'),
    'X-JOIN-EXEC': (2, 'Join은'),
    'X-GROUP-EXEC': (2, 'GroupBy는'),
    'X-SORT-EXEC': (3, 'Sort는'),
    'X-AGG-EXEC': (4, 'v1 기본 규칙:'),
    'X-BACKEND-CONFORMANCE': (8, '최소 CI는'),
}
LOCKED_BLOBS = {
    'runtime/crates/kix-kernel/src/lib.rs':
        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs':
        'b607996c83a119c349f1cc90469ac1ba82764e20',
}
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED')
OWNERS = {'k-stage7-cpu-analytics-sql-audit', 'k-stage7-authenticated-export',
          'kix-feature-ir maintainer', 'User', 'none'}
MUST_STATUS = {ident: 'NOT_COVERED' for ident in (
    'X-JOIN-EXEC', 'X-GROUP-EXEC', 'X-SORT-EXEC', 'X-AGG-EXEC',
    'X-BACKEND-CONFORMANCE')}
CHARACTERIZATIONS = (
    TEST_FILES[4] + '::characterize_depth_limit_for_filter_predicate',
    TEST_FILES[1] + '::characterize_zero_over_negative_denominator_is_negative_zero',
)
HEADER = ['ID', 'Section', 'Clause', 'Tests', 'Status', 'Gap', 'Owner']
SECTION, CLAUSE, TESTS, STATUS, GAP, OWNER = range(1, 7)
MAP_HEAD = '## 2. Map'
CHAR_HEAD = '## 3. Characterizations (AGENTS §8)'
NON_CLAIMS = ('no Polars, DuckDB or GPU execution', 'no tolerance policy chosen',
              'UNDETERMINED (owner: User)', 'no grade change')
CITATION = re.compile(r'`([^`]+)`')
CITE_CELL = re.compile(r'`[^`]+`(?:,\s*`[^`]+`)*')
TEST_FN = r'^\s*#\[test\]\s*\n\s*fn\s+%s\b'


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def git_blob_sha(data):
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def _row_line(text, ident):
    return next(line for line in text.splitlines()
                if line.startswith('|') and split_row(line)[0] == ident)


def _with_cell(text, ident, col, value):
    line = _row_line(text, ident)
    cells = split_row(line)
    cells[col] = value
    return text.replace(line, '| ' + ' | '.join(cells) + ' |', 1)


def section_text(text, heading):
    if text.splitlines().count(heading) != 1:
        return None
    return re.split(r'^## ', text.split(heading, 1)[1].removeprefix('\n'),
                    maxsplit=1, flags=re.M)[0]


def table_rows(text, heading, header, problems):
    section = section_text(text, heading)
    if section is None:
        problems.append('expected one section: ' + heading)
        return []
    cells = [split_row(line) for line in section.splitlines() if line.startswith('|')]
    if cells.count(header) != 1:
        problems.append('bad table header: ' + heading)
    return [r for r in cells if r != header and
            not all(re.fullmatch(r'[-:]+', c) for c in r)]


def normalized(text):
    return ' '.join(text.split())


def find_problems(map_text, contract, root=ROOT, files=None):
    """files injects repo-relative bytes/None without mutating any disk inputs."""
    files = {} if files is None else files
    cache = {}
    problems = []

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
        if data is None or git_blob_sha(data) != want:
            problems.append('locked blob mismatch: ' + path)

    headings = list(re.finditer(r'^## ([^\n]+)', contract, re.M))
    numbers = []
    sections = {}
    for index, match in enumerate(headings):
        number = re.fullmatch(r'(\d+)\. .+', match[1])
        if number is None:
            problems.append('unmapped contract heading: ' + match[1])
            continue
        number = int(number[1])
        numbers.append(number)
        sections[number] = contract[match.end():
            headings[index + 1].start() if index + 1 < len(headings) else len(contract)]
    if numbers != list(range(1, 11)):
        problems.append('contract headings must be exactly 1..10 in order, without duplicates')
    gates = re.findall(r'^(\d+)\. (.+)$', sections.get(9, ''), re.M)
    if [n for n, _ in gates] != [str(n) for n in range(1, 7)]:
        problems.append('contract gates must be exactly 1..6 in order')
    for n, gate in gates:
        expected = EXPECTED.get('G9-' + n)
        if expected is None or normalized(gate) != normalized(expected[1]):
            problems.append('G9-' + n + ': contract gate anchor drift')
    for ident, (number, anchor) in EXPECTED.items():
        if normalized(anchor) not in normalized(sections.get(number, '')):
            problems.append(ident + ': contract anchor is gone')

    def citations(ident, cell):
        if cell != 'none' and not CITE_CELL.fullmatch(cell):
            problems.append(ident + ': bad test-cell grammar')
        cites = CITATION.findall(cell)
        for cite in cites:
            path, _, symbol = cite.partition('::')
            where = ident + ': ' + cite
            if (Path(path).is_absolute() or '\\' in path or
                    any(p in ('', '.', '..') for p in path.split('/'))):
                problems.append(where + ' is not repo-relative')
                continue
            if path.startswith('reference/v0.3-rc1/'):
                problems.append(where + ' is forbidden reference')
                continue
            if path not in TEST_FILES:
                problems.append(where + ' is outside test paths')
                continue
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', symbol):
                problems.append(where + ' needs a nonempty test symbol')
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
                problems.append(where + ' is not a test function')
        return cites

    rows = table_rows(map_text, MAP_HEAD, HEADER, problems)
    ids = [r[0] for r in rows]
    for ident in EXPECTED:
        if ident not in ids:
            problems.append('missing row: ' + ident)
        elif ids.count(ident) != 1:
            problems.append('duplicated row: ' + ident)
    for ident in sorted(set(ids) - EXPECTED.keys()):
        problems.append('invented row: ' + ident)
    present_sections = {r[SECTION] for r in rows if len(r) == len(HEADER)}
    for n in range(1, 11):
        if '§' + str(n) not in present_sections:
            problems.append('missing section coverage: §' + str(n))
    by_status = dict.fromkeys(STATUSES, 0)
    for cells in rows:
        ident = cells[0]
        if len(cells) != len(HEADER):
            problems.append(ident + ': expected seven cells')
            continue
        if ident not in EXPECTED:
            continue
        if cells[SECTION] != '§' + str(EXPECTED[ident][0]) or not cells[CLAUSE]:
            problems.append(ident + ': section/clause mismatch')
        tests = citations(ident, cells[TESTS])
        status, gap, owner = cells[STATUS:OWNER + 1]
        if not gap or '`' in gap:
            problems.append(ident + ': Gap must be nonempty text without backticks')
        if owner not in OWNERS:
            problems.append(ident + ': unknown owner: ' + owner)
        if status not in STATUSES:
            problems.append(ident + ': bad status')
        else:
            by_status[status] += 1
            if status == 'COVERED' and (not tests or gap != 'none' or owner != 'none'):
                problems.append(ident + ': COVERED needs tests and no gap/owner')
            if status == 'PARTIAL' and (not tests or gap == 'none' or owner == 'none'):
                problems.append(ident + ': PARTIAL needs tests, gap and owner')
            if status == 'NOT_COVERED' and (cells[TESTS] != 'none' or gap == 'none' or owner == 'none'):
                problems.append(ident + ': NOT_COVERED needs no tests, gap and owner')
        if ident in MUST_STATUS and status != MUST_STATUS[ident]:
            problems.append(ident + ': must stay NOT_COVERED')
        if ident in MUST_STATUS and owner != 'k-stage7-cpu-analytics-sql-audit':
            problems.append(ident + ': execution owner must stay k-stage7-cpu-analytics-sql-audit')
        if ident in ('S10-LIMITS', 'S8-F64-TOLERANCE') and status == 'COVERED':
            problems.append(ident + ': characterization/open policy must not be COVERED')
        if ident in ('S10-LIMITS', 'S8-F64-TOLERANCE') and owner != 'User':
            problems.append(ident + ': characterization/open policy owner must stay User')

    want = 'Counts: rows=%d ' % len(rows) + ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)
    if [line for line in map_text.splitlines() if line.startswith('Counts:')] != [want]:
        problems.append('counts mismatch: expected ' + want)
    characterizations = section_text(map_text, CHAR_HEAD) or ''
    for cite in CHARACTERIZATIONS:
        if '`' + cite + '`' not in characterizations:
            problems.append('missing class-B citation: ' + cite)
    # Check all Rust test citations in the characterization prose as well.
    for cite in CITATION.findall(characterizations):
        if '::' in cite:
            citations('characterization', '`' + cite + '`')
    for phrase in NON_CLAIMS:
        if phrase not in (section_text(map_text, '## 4. Non-claims') or ''):
            problems.append('missing non-claim: ' + phrase)
    return problems


def self_test(map_text, contract):
    """Require each negative fixture's own diagnostic; use an injected positive."""
    ident = 'S5-DIVIDE-TO-F64'
    path = TEST_FILES[1]
    files = {path: (ROOT / path).read_bytes() + b'\n#[test]\nfn probe() {}\n'}
    good = '`' + path + '::probe`'
    if find_problems(_with_cell(map_text, ident, TESTS, good), contract, files=files):
        print('self-test: valid injected citation rejected', file=sys.stderr)
        return 1
    cases = []

    def case(label, text=map_text, source=contract, injected=None, reason=''):
        cases.append((label, text, source, injected, reason))

    def cell(label, row, col, value, reason, injected=None):
        case(label, _with_cell(map_text, row, col, value), injected=injected, reason=reason)

    boundary_row = 'S6-EXPORT-BOUNDARY'
    harness = TEST_FILES[-1]
    harness_symbol = 'fast64_external_consumer_api_boundaries'
    harness_cite = harness + '::' + harness_symbol
    if find_problems(_with_cell(map_text, boundary_row, TESTS, '`' + harness_cite + '`'), contract):
        print('self-test: valid external-consumer harness citation rejected', file=sys.stderr)
        return 1
    cell('boundary missing harness', boundary_row, TESTS, '`' + harness_cite + '`',
         boundary_row + ': ' + harness_cite + ' file missing', {harness: None})
    for label, symbol in (('fabricated symbol', 'fabricated_test'),
                          ('non-test helper', 'compile_consumer')):
        cite = harness + '::' + symbol
        cell('boundary ' + label, boundary_row, TESTS, '`' + cite + '`',
             boundary_row + ': ' + cite + ' is not a test function')
    fixture_cite = 'runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/checked_export.rs::main'
    cell('boundary fixture outside allowlist', boundary_row, TESTS, '`' + fixture_cite + '`',
         boundary_row + ': ' + fixture_cite + ' is outside test paths')

    line = _row_line(map_text, ident)
    for label, changed, reason in (
        ('missing row', map_text.replace(line + '\n', ''), 'missing row: ' + ident),
        ('duplicate row', map_text.replace(line, line + '\n' + line), 'duplicated row: ' + ident),
        ('invented row', map_text.replace(ident, 'S5-INVENTED'), 'invented row: S5-INVENTED'),
        ('row width', map_text.replace(line, line + ' extra |'), 'expected seven cells'),
        ('table header', map_text.replace('| Tests |', '| Wrong |'), 'bad table header'),
        ('counts', re.sub(r'Counts: rows=\d+', 'Counts: rows=999', map_text), 'counts mismatch'),
        ('duplicate map heading', map_text + '\n' + MAP_HEAD + '\n', 'expected one section'),
        ('section coverage', map_text.replace(_row_line(map_text, 'S1-AUTHORITY') + '\n', ''), 'missing section coverage: §1'),
        ('gate row', map_text.replace(_row_line(map_text, 'G9-4') + '\n', ''), 'missing row: G9-4'),
    ):
        case(label, changed, reason=reason)
    for label, value, reason in (
        ('fabricated symbol', '`%s::fabricated_test`' % path, 'is not a test function'),
        ('non-test helper', '`%s::cat`' % path, 'is not a test function'),
        ('nested non-test helper', '`%s::expected`' % path, 'is not a test function'),
        ('bare path', '`%s`' % path, 'needs a nonempty test symbol'),
        ('empty symbol', '`%s::`' % path, 'needs a nonempty test symbol'),
        ('blank symbol', '`%s::  `' % path, 'needs a nonempty test symbol'),
        ('prose', good + ' prose', 'bad test-cell grammar'),
        ('absolute path', '`/tmp/probe.rs::probe`', 'not repo-relative'),
        ('traversal', '`runtime/../probe.rs::probe`', 'not repo-relative'),
        ('reference path', '`reference/v0.3-rc1/probe.rs::probe`', 'forbidden reference'),
        ('outside path', '`scripts/other.rs::probe`', 'outside test paths'),
    ):
        for suffix, val in (('alone', value), ('mixed', good + ', ' + value)):
            cell(label + ' ' + suffix, ident, TESTS, val, reason, files)
    for label, data, reason in (('missing file', None, 'file missing'),
                                ('non-UTF8 file', b'\xff', 'not UTF-8')):
        cell(label, ident, TESTS, good, reason, {path: data})
    for label, row, col, value, reason in (
        ('section cell', ident, SECTION, '§4', 'section/clause mismatch'),
        ('empty clause', ident, CLAUSE, '', 'section/clause mismatch'),
        ('bad status', ident, STATUS, 'OPEN', 'bad status'),
        ('covered gap', ident, GAP, 'gap', 'COVERED needs'),
        ('covered owner', ident, OWNER, 'User', 'COVERED needs'),
        ('covered no tests', ident, TESTS, 'none', 'COVERED needs'),
        ('partial no tests', 'S1-AUTHORITY', TESTS, 'none', 'PARTIAL needs'),
        ('partial no gap', 'S1-AUTHORITY', GAP, 'none', 'PARTIAL needs'),
        ('partial no owner', 'S1-AUTHORITY', OWNER, 'none', 'PARTIAL needs'),
        ('uncovered has tests', 'S2-GROUP-NULL-KEYS', TESTS, good, 'NOT_COVERED needs'),
        ('uncovered no gap', 'S2-GROUP-NULL-KEYS', GAP, 'none', 'NOT_COVERED needs'),
        ('uncovered no owner', 'S2-GROUP-NULL-KEYS', OWNER, 'none', 'NOT_COVERED needs'),
        ('unknown owner', ident, OWNER, 'Someone', 'unknown owner'),
        ('empty gap', ident, GAP, '', 'Gap must be nonempty'),
    ):
        cell(label, row, col, value, reason, files)
    for row in MUST_STATUS:
        cell('pinned status ' + row, row, STATUS, 'PARTIAL', 'must stay NOT_COVERED')
        cell('pinned owner ' + row, row, OWNER, 'User', 'execution owner must stay')
    for row in ('S10-LIMITS', 'S8-F64-TOLERANCE'):
        cell('characterization status ' + row, row, STATUS, 'COVERED', 'must not be COVERED')
        cell('characterization owner ' + row, row, OWNER, 'none', 'owner must stay User')
    for cite in CHARACTERIZATIONS:
        case('class-B citation', map_text.replace('`' + cite + '`', 'omitted'), reason='missing class-B citation: ' + cite)
    for phrase in NON_CLAIMS:
        case('non-claim', map_text.replace(phrase, 'omitted'), reason='missing non-claim: ' + phrase)
    for label, source, reason in (
        ('new heading', contract + '\n## 11. New\n', 'contract headings must be exactly'),
        ('duplicate heading', contract + '\n## 10. Duplicate\n', 'contract headings must be exactly'),
        ('missing heading', contract.replace('## 3. Sort semantics', 'Sort semantics'), 'contract headings must be exactly'),
        ('unnumbered heading', contract + '\n## New\n', 'unmapped contract heading'),
        ('gate removed', contract.replace('4. ' + EXPECTED['G9-4'][1], ''), 'contract gates must be exactly'),
        ('gate reordered', contract.replace('4. ' + EXPECTED['G9-4'][1], '3. ' + EXPECTED['G9-4'][1]), 'contract gates must be exactly'),
        ('gate anchor drift', contract.replace(EXPECTED['G9-4'][1], 'changed gate'), 'contract gate anchor drift'),
        ('anchor drift', contract.replace(EXPECTED['S4-OVERFLOW-ERROR'][1], 'changed'), 'S4-OVERFLOW-ERROR: contract anchor is gone'),
    ):
        case(label, source=source, reason=reason)
    for path in LOCKED_BLOBS:
        case('locked blob drift', injected={path: b'not the locked blob'}, reason='locked blob mismatch: ' + path)
    for label, text, source, injected, reason in cases:
        problems = find_problems(text, source, files=injected)
        if not any(reason in problem for problem in problems):
            print('self-test: failed to detect ' + label + ': ' + repr(problems), file=sys.stderr)
            return 1
        print('self-test: detected ' + label)
    print('self-test: pass (%d negative controls, injected positive control)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_feature_semantics_evidence_map.py [--self-test]', file=sys.stderr)
        return 2
    try:
        map_text = (ROOT / MAP).read_text(encoding='utf-8')
        contract = (ROOT / CONTRACT).read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        print('feature semantics evidence map input error: ' + str(error), file=sys.stderr)
        return 1
    problems = find_problems(map_text, contract)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    if argv:
        return self_test(map_text, contract)
    print('feature semantics evidence map ok: ' + next(
        line for line in map_text.splitlines() if line.startswith('Counts:')))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
