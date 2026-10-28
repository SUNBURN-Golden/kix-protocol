#!/usr/bin/env python3
"""Validate performance clause citations using stdlib and offline local text only.

Adapted from check_bcs1_evidence_map.py. Existence is not semantic coverage;
self-tests mutate in-memory inputs only, never Rust or locked files.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md'
SOURCES = {'contract': 'docs/contracts/PERFORMANCE_MEASUREMENT.md',
           'baseline': 'docs/contracts/PERFORMANCE_BASELINE_V4.md'}
TEST_FILE = 'runtime/crates/kix-kernel/tests/performance_harness.rs'
SOURCE_FILES = ('runtime/crates/kix-kernel/tests/support/perf_probe.rs',
                'runtime/crates/kix-kernel/examples/r1_perf_probe.rs')
HISTORICAL_FILE = SOURCES['baseline']
LOCKED_BLOBS = {
    'runtime/crates/kix-kernel/src/lib.rs':
        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs':
        'b607996c83a119c349f1cc90469ac1ba82764e20',
}
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED', 'NOT_RUN')
HEADER = ['ID', 'Section', 'Clause', 'Tests', 'Source', 'Status', 'Gap', 'Owner']
SECTION, CLAUSE, TESTS, SOURCE, STATUS, GAP, OWNER = range(1, 8)
MAP_HEAD = '## 2. Map'
HIST_HEAD = '## 3. Historical reference'
PREFIX_SECTION = {'M': '측정 의미', 'L': '부하 구분', 'B': '부하 구분',
                  'I': '구현 범위', 'R': '구현 범위', 'C': '구현 범위',
                  'X': '실행과 자료', 'BD': '실행과 자료'}
MUST_STATUS = {'X-RELEASE-REPRO': 'NOT_RUN', 'X-OUTPUT-FILES': 'NOT_RUN',
               'BD-RUN-VALUES': 'NOT_RUN', 'BD-FAIL-CLOSED': 'NOT_COVERED'}
OWNERS = {'kix-kernel perf harness maintainer', 'User', 'none'}
NON_CLAIMS = ('no product TPS, p99 or failure-rate value',
              'UNDETERMINED (owner: User)', 'no benchmark claim',
              'release probe NOT_RUN')
HIST_PHRASE = 'historical, not current measurement'
CITATION = re.compile(r'`([^`]+)`')
CITE_CELL = re.compile(r'`[^`]+`(?:,\s*`[^`]+`)*')
TEST_FN = r'^\s*#\[test\]\s*\n\s*fn\s+%s\b'
SOURCE_SYMBOL = r'^\s*(?:pub\s+)?(?:fn|const|struct|enum)\s+%s\b'

# Literal contract anchors, whitespace-normalized within the named heading only.
EXPECTED = {
    'M-NEW-SUCCESS': 'JSON `new_success_count`와 `new_held`',
    'M-REPLAYED': 'JSON `replayed`',
    'M-BUSINESS-REJECTED': 'JSON `business_rejected`',
    'M-CAPACITY': 'JSON `capacity`',
    'M-CONFLICT-RETAINED': 'JSON `conflict_retained`. `other`에 넣지 않음',
    'M-OTHER': 'Capacity가 아닌 기타 오류와, Conflict가 아닌 기타 관측의 합',
    'M-SERVICE-NS': '개별 커널 호출과 결과 분류를 실행한 계측 구간',
    'M-SCHEDULED-LATENCY': '고정 예정 도착시각부터 완료까지',
    'M-ELAPSED': 'workload 루프 전체 시간',
    'M-FIRST-CAPACITY-INDEX': 'first_capacity_index',
    'M-SAMPLES-AFTER-FIRST-CAPACITY': '첫 고갈 표본 뒤의 호출 수',
    'M-MIXED-P99': '모든 outcome을 한 분포로 모은 nearest-rank p99',
    'M-MIXED-KEYS-NOT-SUCCESS':
        '표본이 모두 Held여도 혼합 p99 키 이름은 그대로다',
    'M-OUTCOMES': '개수가 0이면 p99는 null',
    'M-GOODPUT': '`new_held * 1000000000 / elapsed_ns` 정수',
    'M-CSV-ALL-CALLS': '현재 CSV는 모든 호출의 scheduled/start/end/service/latency/outcome을 저장한다',
    'L-LOW-LOAD': '표본 수 `min(32, command_limit-1)`',
    'L-UNIFORM': '좌석을 세그먼트 안에서 순환',
    'L-HOT-SEAT': '서로 다른 명령이 좌석 0만 반복',
    'L-SAME-COMMAND-RETRY': '동일 명령의 최초 Held와 이후 replay',
    'L-HISTORY-GROWTH': 'retained-conflict 입력이 관측 슬롯에 누적',
    'L-SATURATION': '`budget_phase`는 `includes-samples-after-first-capacity`',
    'B-ZERO-KERNEL-REBUILD': 'workload 도중 커널 재생성은 0회다',
    'B-FINITE-BUDGETS': '무한 예산으로 고갈을 숨기지 않는다',
    'B-INVENTORY-4096': '재고는 좌석 세그먼트 `[4096]`',
    'B-ORDER-BUDGET-4096': '주문 예산 4096',
    'B-OBSERVATION-BUDGET-128': '관측 예산 128이다',
    'B-CONFLICT-AT-OBSERVATION-LIMIT': '명령 한도를 올려도 관측 한도가 늘어나지는 않는다',
    'B-PREFILL-SLOT': '사전 관측 1건이 이미 슬롯 하나를 쓴다',
    'I-FOUR-WORKLOADS': '워크로드는 균등 좌석, hot seat, 동일 명령 재시도, retained conflict 증가의 네 개다',
    'I-PARAMS-IN-JSON': '명령 예산·주문 예산·관측 예산·요청 수·rate를 JSON에 명시한다',
    'R-RATE-ZERO': 'rate=0은 서비스 시간 microbenchmark이며 open-loop라고 부르지 않는다',
    'R-RATE-FIXED-ORIGIN': 'rate>0은 고정 origin의 i/rate 예정시각을 유지한다',
    'C-SMOKE-SHAPE': '4×512 호출과 16개 scheduled 호출을 debug 테스트로 수행한다',
    'C-SMOKE-NOT-PRODUCT': 'production p99/TPS 결과가 아니다',
    'C-SMOKE-V4-COUNTS': '논리 건수는 V4-SMOKE-001 표와 맞춘다',
    'X-RELEASE-REPRO': '마지막 명령은 로컬 재현 절차다',
    'X-OUTPUT-FILES': '파일은 네 workload의 CSV/JSON, `low-load-uniform.csv/json`, `binding.json`이다',
    'BD-FIELDS': '`binding.json`은 그 실행의 commit·tree, 잠금 blob 4개, 프로브 소스 blob',
    'BD-RUN-VALUES': '이 묶음은 그 한 번의 로컬 실행 설명이다',
    'BD-LOCAL-NOT-SLO': '전용 장비의 반복 캠페인이나 승인 SLO가 아니다',
    'BD-FAIL-CLOSED': '잠금 blob이 필요한 값과 다르면 예시는 증거 파일을 쓰지 않고 실패한다',
}


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def parse_cell(cell):
    out = []
    for match in CITATION.finditer(cell):
        path, _, symbol = match[1].partition('::')
        out.append((path, symbol or None))
    return out


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


def find_problems(map_text, sources, root=ROOT, files=None):
    """files injects repo-relative bytes/None, without changing disk contents."""
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

    def read_text(path, where):
        data = read(path)
        if data is None:
            problems.append(where + ' file missing')
            return ''
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            problems.append(where + ' is not UTF-8')
            return ''

    for path, want in LOCKED_BLOBS.items():
        data = read(path)
        if data is None or git_blob_sha(data) != want:
            problems.append('locked blob mismatch: ' + path)
    example = read_text(SOURCE_FILES[1], SOURCE_FILES[1])
    for constant, want in zip(('LOCKED_KERNEL', 'LOCKED_QUARANTINE'), LOCKED_BLOBS.values()):
        found = re.findall(r'^const ' + constant + r':\s*&str\s*=\s*"([0-9a-f]+)";', example, re.M)
        if found != [want]:
            problems.append('example constant mismatch: ' + constant)

    contract = sources.get('contract', '')
    sections = {}
    headings = list(re.finditer(r'^## ([^\n]+)', contract, re.M))
    for n, match in enumerate(headings):
        heading = match[1]
        if heading in sections:
            problems.append('duplicated contract section: ' + heading)
        sections[heading] = contract[match.end():
            headings[n + 1].start() if n + 1 < len(headings) else len(contract)]
    allowed = set(PREFIX_SECTION.values()) | {'비주장'}
    for heading in sorted(set(sections) - allowed):
        problems.append('unmapped contract section: ' + heading)
    for heading in sorted(allowed - set(sections)):
        problems.append('missing contract section: ' + heading)
    for ident, anchor in EXPECTED.items():
        section = sections.get(PREFIX_SECTION[ident.split('-')[0]], '')
        if ' '.join(anchor.split()) not in ' '.join(section.split()):
            problems.append(ident + ': contract anchor is gone')

    rows = table_rows(map_text, MAP_HEAD, HEADER, problems)
    ids = [r[0] for r in rows]
    for ident in EXPECTED:
        if ident not in ids:
            problems.append('missing row: ' + ident)
        elif ids.count(ident) != 1:
            problems.append('duplicated row: ' + ident)
    for ident in sorted(set(ids) - set(EXPECTED)):
        problems.append('invented row: ' + ident)

    def citations(ident, cell, is_test):
        kind = 'test' if is_test else 'source'
        cites = parse_cell(cell)
        if cell != 'none' and not CITE_CELL.fullmatch(cell):
            problems.append(ident + ': bad ' + kind + '-cell grammar')
        for path, symbol in cites:
            where = ident + ': ' + path + ('::' + symbol if symbol else '')
            if (Path(path).is_absolute() or '\\' in path or
                    any(p in ('', '.', '..') for p in path.split('/'))):
                problems.append(where + ' is not repo-relative')
                continue
            if path.startswith('reference/v0.3-rc1/'):
                problems.append(where + ' is forbidden reference')
                continue
            if not is_test and path == HISTORICAL_FILE:
                if ident != 'C-SMOKE-V4-COUNTS' or symbol is not None:
                    problems.append(where + ' historical file only allowed bare on C-SMOKE-V4-COUNTS')
                read_text(path, where)
                continue
            if path not in ((TEST_FILE,) if is_test else SOURCE_FILES):
                problems.append(where + ' is outside ' + kind + ' paths')
                continue
            if symbol is None or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', symbol):
                problems.append(where + ' needs a nonempty ' + kind + ' symbol')
                continue
            text = read_text(path, where)
            pattern = TEST_FN if is_test else SOURCE_SYMBOL
            if not re.search(pattern % re.escape(symbol), text, re.M):
                problems.append(where + (' is not a test function' if is_test else ' is not a source symbol'))
        return cites

    by_status = dict.fromkeys(STATUSES, 0)
    for cells in rows:
        ident = cells[0]
        if len(cells) != len(HEADER):
            problems.append(ident + ': expected eight cells')
            continue
        if ident not in EXPECTED:
            continue
        if cells[SECTION] != PREFIX_SECTION[ident.split('-')[0]] or not cells[CLAUSE]:
            problems.append(ident + ': section/clause mismatch')
        tests = citations(ident, cells[TESTS], True)
        source = citations(ident, cells[SOURCE], False)
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
            if status in ('NOT_COVERED', 'NOT_RUN') and (cells[TESTS] != 'none' or gap == 'none' or owner == 'none'):
                problems.append(ident + ': ' + status + ' needs no tests, gap and owner')
        if ident in MUST_STATUS and status != MUST_STATUS[ident]:
            problems.append(ident + ': must stay ' + MUST_STATUS[ident])
        if ident == 'C-SMOKE-V4-COUNTS' and (
                source != [(HISTORICAL_FILE, None)] or HIST_PHRASE not in gap):
            problems.append(ident + ': historical citation/phrase missing')

    want = 'Counts: rows=%d ' % len(rows) + ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)
    if [l for l in map_text.splitlines() if l.startswith('Counts:')] != [want]:
        problems.append('counts mismatch: expected ' + want)
    historical = section_text(map_text, HIST_HEAD) or ''
    if HIST_PHRASE not in historical:
        problems.append('historical reference phrase missing')
    # Keep the original date/commit/tree attribution explicitly historical.
    for token in ('V4-SMOKE-001', '2026-09-16',
                  '0394a36a655b86bacb568b055d377d4c4fd91185',
                  '38096dc849dc338f12aa69bce2200cda971a6d3c'):
        if token not in historical or token not in sources.get('baseline', ''):
            problems.append('historical attribution missing: ' + token)
    for phrase in NON_CLAIMS:
        if phrase not in (section_text(map_text, '## 5. Non-claims') or ''):
            problems.append('missing non-claim: ' + phrase)
    return problems


def self_test(map_text, sources):
    """A valid injected citation passes; each negative needs its own diagnostic."""
    ident = 'M-SAMPLES-AFTER-FIRST-CAPACITY'
    original = (ROOT / TEST_FILE).read_bytes()
    probe_files = {TEST_FILE: original + b'\n#[test]\nfn probe() {}\n'}
    good = '`' + TEST_FILE + '::probe`'
    if find_problems(_with_cell(map_text, ident, TESTS, good), sources, files=probe_files):
        print('self-test: valid injected test rejected', file=sys.stderr)
        return 1
    cases = []

    def cell(label, row, col, value, reason, files=None):
        cases.append((label, _with_cell(map_text, row, col, value), sources, files, reason))

    for label, value, reason in (
        ('fabricated test citation', '`%s::fabricated_test`' % TEST_FILE, 'is not a test function'),
        ('non-test helper', '`%s::assert_separated`' % TEST_FILE, 'is not a test function'),
        ('bare test path', '`%s`' % TEST_FILE, 'needs a nonempty test symbol'),
        ('empty test symbol', '`%s::`' % TEST_FILE, 'needs a nonempty test symbol'),
        ('blank test symbol', '`%s::  `' % TEST_FILE, 'needs a nonempty test symbol'),
        ('prose after citation', good + ' prose', 'bad test-cell grammar'),
    ):
        for suffix, val in (('alone', value), ('mixed', good + ', ' + value)):
            cell(label + ' ' + suffix, ident, TESTS, val, reason, probe_files)
    for col, path, symbol in ((TESTS, TEST_FILE, 'probe'), (SOURCE, SOURCE_FILES[0], 'run')):
        for label, wrong, reason in (
            ('outside allowed files', 'scripts/other.rs', 'outside'),
            ('absolute path', '/tmp/probe.rs', 'not repo-relative'),
            ('traversal', 'runtime/../probe.rs', 'not repo-relative'),
            ('reference path', 'reference/v0.3-rc1/probe.rs', 'forbidden reference'),
        ):
            cell(label, ident, col, '`%s::%s`' % (wrong, symbol), reason)
        for label, data, reason in (('missing file', None, 'file missing'),
                                    ('non-UTF8 file', b'\xff', 'not UTF-8')):
            cell(label, ident, col, '`%s::%s`' % (path, symbol), reason, {path: data})
    for value, reason in (
        ('`%s::fabricated_symbol`' % SOURCE_FILES[0], 'is not a source symbol'),
        ('`%s`' % SOURCE_FILES[0], 'needs a nonempty source symbol'),
        ('`%s::run` prose' % SOURCE_FILES[0], 'bad source-cell grammar'),
        ('`%s`' % HISTORICAL_FILE, 'historical file only allowed'),
    ):
        cell('source citation', ident, SOURCE, value, reason)
    line = _row_line(map_text, ident)
    for label, changed, reason in (
        ('removed row', map_text.replace(line + '\n', ''), 'missing row'),
        ('duplicate row', map_text.replace(line, line + '\n' + line), 'duplicated row'),
        ('invented row', map_text.replace(ident, 'M-INVENTED'), 'invented row'),
        ('row width', map_text.replace(line, line + ' extra |'), 'expected eight cells'),
        ('header', map_text.replace('| Tests |', '| Wrong |'), 'bad table header'),
        ('counts', re.sub(r'Counts: rows=\d+', 'Counts: rows=999', map_text), 'counts mismatch'),
        ('duplicate map heading', map_text + '\n' + MAP_HEAD + '\n', 'expected one section'),
        ('historical phrase', map_text.replace(HIST_PHRASE, 'omitted'), 'historical reference phrase missing'),
        ('historical attribution', map_text.replace('0394a36a655b86bacb568b055d377d4c4fd91185', 'omitted'), 'historical attribution missing'),
    ):
        cases.append((label, changed, sources, None, reason))
    for phrase in NON_CLAIMS:
        cases.append(('non-claim removed', map_text.replace(phrase, 'omitted'), sources, None, 'missing non-claim: ' + phrase))
    for label, row, col, value, reason in (
        ('section field', ident, SECTION, '실행과 자료', 'section/clause mismatch'),
        ('empty clause', ident, CLAUSE, '', 'section/clause mismatch'),
        ('OPEN status', ident, STATUS, 'OPEN', 'bad status'),
        ('covered gap', ident, GAP, 'gap', 'COVERED needs'),
        ('covered without tests', ident, TESTS, 'none', 'COVERED needs'),
        ('partial without tests', 'M-OTHER', TESTS, 'none', 'PARTIAL needs'),
        ('partial without gap', 'M-OTHER', GAP, 'none', 'PARTIAL needs'),
        ('partial without owner', 'M-OTHER', OWNER, 'none', 'PARTIAL needs'),
        ('unknown owner', ident, OWNER, 'Someone', 'unknown owner'),
        ('empty gap', 'M-OTHER', GAP, '', 'Gap must be nonempty'),
        ('not run with tests', 'X-RELEASE-REPRO', TESTS, good, 'NOT_RUN needs'),
        ('not covered with tests', 'BD-FAIL-CLOSED', TESTS, good, 'NOT_COVERED needs'),
        ('historical row source', 'C-SMOKE-V4-COUNTS', SOURCE, 'none', 'historical citation/phrase missing'),
    ):
        cell(label, row, col, value, reason, probe_files)
    for row, status in MUST_STATUS.items():
        cell('pinned status flipped', row, STATUS, 'COVERED', 'must stay ' + status)
    for label, contract, reason in (
        ('anchor removed', re.sub(r'\s+'.join(map(re.escape, EXPECTED['B-CONFLICT-AT-OBSERVATION-LIMIT'].split())), 'gone', sources['contract']), 'contract anchor is gone'),
        ('new heading', sources['contract'] + '\n## New\n', 'unmapped contract section'),
        ('duplicate heading', sources['contract'] + '\n## 측정 의미\n', 'duplicated contract section'),
        ('missing heading', sources['contract'].replace('## 비주장', '## omitted'), 'missing contract section'),
    ):
        cases.append((label, map_text, dict(sources, contract=contract), None, reason))
    for locked in LOCKED_BLOBS:
        cases.append(('locked-blob drift', map_text, sources, {locked: b'drift'}, 'locked blob mismatch: ' + locked))
    example = (ROOT / SOURCE_FILES[1]).read_bytes()
    for constant, sha in zip(('LOCKED_KERNEL', 'LOCKED_QUARANTINE'), LOCKED_BLOBS.values()):
        cases.append(('example constant drift', map_text, sources,
                      {SOURCE_FILES[1]: example.replace(sha.encode(), b'0' * 40, 1)},
                      'example constant mismatch: ' + constant))
    for label, changed, mutated_sources, files, reason in cases:
        found = find_problems(changed, mutated_sources, files=files)
        if not any(reason in item for item in found):
            print('self-test: %s accepted or wrong diagnostic: %s' % (label, found), file=sys.stderr)
            return 1
        print('self-test: detected %s (%s)' % (label, reason))
    print('self-test: pass (2 positive controls, %d negative fixtures; memory only)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_performance_measurement_evidence_map.py [--self-test]', file=sys.stderr)
        return 2
    try:
        map_text = (ROOT / MAP).read_text(encoding='utf-8')
        sources = {key: (ROOT / path).read_text(encoding='utf-8') for key, path in SOURCES.items()}
    except (OSError, UnicodeDecodeError) as error:
        print('performance evidence map input error: ' + str(error), file=sys.stderr)
        return 1
    problems = find_problems(map_text, sources)
    if problems:
        print('performance evidence map check failed:', file=sys.stderr)
        for problem in problems:
            print('- ' + problem, file=sys.stderr)
        return 1
    if argv:
        return self_test(map_text, sources)
    print('performance evidence map ok: ' + next(l for l in map_text.splitlines() if l.startswith('Counts:')))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
