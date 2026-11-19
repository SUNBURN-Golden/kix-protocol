#!/usr/bin/env python3
"""Validate integration-gate clause citations statically using only the stdlib.

Existence is not semantic coverage. Never imports the gate, opens sockets or
runs cited checks/tests. Self-test inputs are bytes/text injected in memory.
"""
import ast
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md'
CONTRACT = 'docs/contracts/openapi/README.md'
WORKFLOW = '.github/workflows/protocol.yml'
SELF = 'scripts/check_integration_gate_contract_evidence_map.py'
WRAPPER = 'scripts/check_integration_gate_openapi.py'
TEST_PATH = 'integration_gate/test_http_gate.py'
OFFLINE_TEST_PATH = 'integration_gate/test_offline_limits.py'
CHECKER_PATHS = ('scripts/check_openapi_contract.py', 'integration_gate/openapi_doc.py')
HOST_OWNER = 'Supervisor / repository owner controlling the execution host'
HEADINGS = {
    'pins': '핀', 'call': '문서가 따르는 호출',
    'fail-closed': '유지한 fail-closed 규칙', 'commands': '명령 집합',
    'read': '상거래 앱이 나중에 읽는 방법', 'checks': '검사',
    'gate': '비운영 통합 관문',
}
EXPECTED = {
    'I-NO-PROD': ('intro', '운영 엔드포인트는 없다. 공개 호스트는 없다.'),
    'I-CONTRACT-ONLY-MARKERS': ('intro', '`x-kix-live-http-server`는 `false`'),
    'I-GATE-ROUTING': ('intro', 'FSM 44개 명령은 같은 워커의 인프로세스 기계로 넘긴다'),
    'I-READINESS-DIR': ('intro', '`--readiness-dir`를 주면 커밋된 로컬 호출을'),
    'P-CORE-SOURCE': ('pins', '원본 경로'),
    'P-FSM-SOURCE': ('pins', 'FSM 원본 경로'),
    'P-CONTRACT-STATUS': ('pins', '`x-kix-contract-status`'),
    'P-INFO-VERSION-SUMMARY': ('pins', '`info.version`은 `0.3-rc1+sha256:`'),
    'P-README-TABLE-MIRROR': ('pins', 'README의 이 표는 그 핀을 사람이 읽도록 옮긴 것이다'),
    'C-ENVELOPE': ('call', 'Core.execute(operationId, actor, action, body)'),
    'C-ACTOR-NO-AUTH': ('call', '이 문서는 인증 스킴을 만들지 않는다.'),
    'C-PLACEHOLDER-PATH': ('call', '`operationId: invokeLocalCall`'),
    'C-OPERATION-MAP': ('call', '`x-kix-action-body-map`'),
    'F-ADDITIONAL-PROPERTIES': ('fail-closed', '각 명령 스키마의 `additionalProperties: false`'),
    'F-UNKNOWN-FIELDS': ('fail-closed', '`unknownFields: REJECT`'),
    'F-FIXTURE-ONLY': ('fail-closed', '`sourceAuthentication: FIXTURE_ONLY`'),
    'F-HANDLER-CONSTRAINTS': ('fail-closed', '`handlerConstraints` 문장 전체'),
    'F-REFERENCE-OBSERVED': ('fail-closed', '`x-kix-reference-model-observed`'),
    'K-CORE-40': ('commands', 'v0.3-rc1 `commands` 키 40개'),
    'K-FSM-44': ('commands', 'FSM `REPLAYABLE` 44개'),
    'K-TOTAL-84-OMITTED-EMPTY': ('commands', '`x-kix-omitted-commands`는 빈 배열이다.'),
    'K-WIRE-NAMES': ('commands', '`consume_admission`은 카탈로그 이름이 아니다.'),
    'K-READINESS-FSM-REFUSED': ('commands', '`READINESS_FSM_REFUSED`로 거절한다.'),
    'K-FSM-NO-OPID-REMAP': ('commands', '봉투 `operationId`는 FSM `idempotency_key`로 다시 쓰지 않는다.'),
    'K-OUT-OF-SCOPE': ('commands', '이 카탈로그의 범위 밖이다.'),
    'R-1': ('read', '파일 경로와 `x-kix-source.sha256`을'),
    'R-2': ('read', '계약 전용 파일의 경로를 공개 서비스 주소로 쓰지 않는다.'),
    'R-3': ('read', '로컬 호출 준비 형태는'),
    'R-4': ('read', '본문의 알려지지 않은 필드는 거절한다'),
    'R-5': ('read', '`actor`를 인증 결과로 믿지 않는다.'),
    'R-6': ('read', '재시도, 전송 성공, 운영 엔드포인트를'),
    'R-7': ('read', '브라우저 전송은 `--browser-origin'),
    'CHK-COMMAND-LIST': ('checks', 'python3 scripts/check_openapi_contract.py'),
    'CHK-CONTRACT-FAILS': ('checks', '명령이 늘거나 줄거나'),
    'CHK-SELF-TEST-IN-MEMORY': ('checks', '`--self-test`는 그 실패 경로를 메모리에서 확인한다.'),
    'CHK-HTTP-SUITE': ('checks',
        'python3 -m unittest integration_gate.test_http_gate readiness.test_faults'),
    'G-LOOPBACK-BIND': ('gate', '기본 바인드는 `127.0.0.1`과 포트 `8765`다.'),
    'G-NO-PUBLIC': ('gate', '운영 준비가 아니다'),
    'G-POST-LOCAL-CALL': ('gate', '`POST /x-kix-contract-only/local-call`'),
    'G-HEALTH': ('gate', '`GET /health`'),
    'G-READY': ('gate', '`GET /ready`'),
    'G-OPTIONS-FLAG': ('gate', '`OPTIONS` (플래그가 켜진 경우만)'),
    'G-OTHER-FAIL-CLOSED': ('gate', '그 밖 경로·메서드'),
    'G-BROWSER-OPTIN-DEFAULT-OFF': ('gate', '기본은 꺼져 있다.'),
    'G-BROWSER-HOST': ('gate', '없거나 두 개인 `Host`는 400'),
    'G-CORS-HEADERS': ('gate', '`Access-Control-Allow-Origin`과 `Vary: Origin`만'),
    'G-PRE-PARSE-NO-CORS': ('gate', '헤더를 파싱하기 전에 만든 응답'),
    'G-OPENAPI-NO-CORS-CHANGE': ('gate', '서버 URL, 보안 스킴, `OPTIONS` 오퍼레이션은 없다.'),
    'G-REJECT-NOT-200': ('gate', '거절은 HTTP 200으로 숨기지 않는다.'),
    'G-LIMITS': ('gate', '본문 상한은 65536바이트'),
    'G-SAME-PROCESS-REPLAY': ('gate', '같은 `operationId`와 같은 actor·action·body 지문이면'),
    'G-RESTART-LOSS': ('gate', '기본 프로세스를 다시 시작하면 인메모리 상태와 그 재생은 사라진다.'),
    'G-READINESS-REPLAY-ONCE': ('gate', '재생은 효과를 다시 적용하지 않는다.'),
    'G-ACTOR-NO-ADAPTERS': ('gate', '외부 PG·KYC·공연장·은행 어댑터는 붙이지 않는다.'),
}
LOCKED_BLOBS = {
    'runtime/crates/kix-kernel/src/lib.rs':
        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs':
        'b607996c83a119c349f1cc90469ac1ba82764e20',
}
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED')
OWNERS = {'integration_gate maintainer', HOST_OWNER, 'Astra', 'User', 'none'}
PINNED = ('I-GATE-ROUTING', 'CHK-HTTP-SUITE')
REQUIRED_CITES = {
    'K-READINESS-FSM-REFUSED':
        TEST_PATH + '::TransportTests.test_readiness_directory_refuses_fsm_commands',
    'R-7': TEST_PATH + '::BrowserAccessTests.test_flag_off_keeps_today_including_origin_and_hostile_host',
    'G-LOOPBACK-BIND': TEST_PATH + '::OpenApiAndSchemaTests.test_refuses_non_loopback_bind',
    'G-NO-PUBLIC': 'integration_gate/openapi_doc.py::validate',
}
REQUIRED_OFFLINE_CITES = {
    'G-OPENAPI-NO-CORS-CHANGE': (
        OFFLINE_TEST_PATH + '::OfflineGapTests.test_gate_openapi_rendered_bytes_are_pinned',
        OFFLINE_TEST_PATH + '::OfflineGapTests.test_browser_origin_is_transport_only_statically',
    ),
    'G-SAME-PROCESS-REPLAY': (
        OFFLINE_TEST_PATH + '::OfflineGapTests.test_core_actor_only_conflict_preserves_receipt',
        OFFLINE_TEST_PATH + '::OfflineGapTests.test_core_action_only_conflict_preserves_receipt',
    ),
    'K-WIRE-NAMES': (
        OFFLINE_TEST_PATH + '::OfflineGapTests.test_unprefixed_admission_names_are_not_dispatchable',
    ),
}
HEADER = ['ID', 'Section', 'Clause', 'Tests', 'Checkers', 'Status', 'Gap', 'Owner']
SECTION, CLAUSE, TESTS, CHECKERS, STATUS, GAP, OWNER = range(1, 8)
MAP_HEAD = '## 2. Map'
GAPS_HEAD = '## 3. Open gaps'
CHAR_HEAD = '## 4. Characterizations (AGENTS §8)'
NON_CLAIMS = ('runs only where loopback is permitted', 'no production endpoint',
              'no gate behavior change', 'no grade change')
GAP_LINK = ('OPEN_USER_DECISIONS_20261023_ADDENDUM.md'
            '#plan-plan-gate-fsm-seeded-journey-differentia')
CITATION = re.compile(r'`([^`]+)`')
CITE_CELL = re.compile(r'`[^`]+`(?:,\s*`[^`]+`)*')
ALLOWED_IMPORTS = {'ast', 'hashlib', 're', 'sys', 'pathlib'}


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


def count_line(rows):
    return 'Counts: rows=%d ' % len(rows) + ' '.join(
        '%s=%d' % (status, sum(len(r) == len(HEADER) and r[STATUS] == status
                              for r in rows)) for status in STATUSES)


def find_problems(map_text, contract, root=ROOT, files=None):
    """Read bytes only. Injection overrides never write or execute disk inputs."""
    files = {} if files is None else files
    cache, trees = {}, {}
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

    def tree(path):
        if path not in trees:
            data = read(path)
            trees[path] = None
            if data is None:
                problems.append(path + ': file missing')
            else:
                try:
                    trees[path] = ast.parse(data.decode('utf-8'), filename=path)
                except UnicodeDecodeError:
                    problems.append(path + ': not UTF-8')
                except (SyntaxError, ValueError):
                    problems.append(path + ': syntax error')
        return trees[path]

    for path, want in LOCKED_BLOBS.items():
        data = read(path)
        if data is None or git_blob_sha(data) != want:
            problems.append('locked blob mismatch: ' + path)

    headings = list(re.finditer(r'^## ([^\n]+)', contract, re.M))
    labels = [match[1] for match in headings]
    if set(labels) != set(HEADINGS.values()) | {'파일'} or len(labels) != len(HEADINGS) + 1:
        problems.append('contract headings must be exactly the mapped headings plus 파일')
    sections = {'intro': contract[:headings[0].start()] if headings else contract}
    for key, heading in HEADINGS.items():
        sections[key] = section_text(contract, '## ' + heading) or ''
    for ident, (key, anchor) in EXPECTED.items():
        if normalized(anchor) not in normalized(sections.get(key, '')):
            problems.append(ident + ': contract anchor is gone')
    if re.findall(r'^(\d+)\. ', sections['read'], re.M) != [str(n) for n in range(1, 8)]:
        problems.append('read guidance must have exactly items 1..7 in order')

    # Only literal standalone run lines count, never comments or prose.
    workflow = read(WORKFLOW)
    try:
        run_lines = {line.strip() for line in workflow.decode('utf-8').splitlines()}
    except (AttributeError, UnicodeDecodeError):
        problems.append('workflow missing or not UTF-8')
        run_lines = set()
    blocks = re.findall(r'^```[^\n]*\n(.*?)^```\s*$', sections['checks'], re.M | re.S)
    commands = [line.strip() for block in blocks for line in block.splitlines() if line.strip()]
    if len(commands) != 5:
        problems.append('checks section must list five commands')
    for command in commands:
        # protocol.yml uses both a multiline block and a scalar run for this list.
        if command not in run_lines and 'run: ' + command not in run_lines:
            problems.append('documented command missing from workflow: ' + command)

    wrapper = tree(WRAPPER)
    if wrapper is not None and not any(
            isinstance(node, ast.ImportFrom) and node.level == 0 and
            node.module == 'integration_gate.openapi_doc' and
            any(alias.name == 'main' and alias.asname in (None, 'main') for alias in node.names)
            for node in wrapper.body):
        problems.append('wrapper must import main from integration_gate.openapi_doc')
    own_tree = tree(SELF)
    if own_tree is not None:
        for node in ast.walk(own_tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [('.' * node.level) + (node.module or '')]
            for module in modules:
                if module not in ALLOWED_IMPORTS:
                    problems.append('forbidden checker import: ' + module)

    def citations(ident, cell, column):
        if cell == 'none':
            return []
        if not CITE_CELL.fullmatch(cell):
            problems.append(ident + ': bad citation-cell grammar')
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
            allowed = (TEST_PATH, OFFLINE_TEST_PATH) if column == TESTS else CHECKER_PATHS
            if path not in allowed:
                problems.append(where + ' is outside allowed citation paths')
                continue
            grammar = (r'[A-Za-z_]\w*\.test_\w+' if column == TESTS else r'[A-Za-z_]\w*')
            if not re.fullmatch(grammar, symbol, flags=re.ASCII):
                problems.append(where + ' needs a nonempty qualified test/checker symbol')
                continue
            parsed = tree(path)
            if parsed is None:
                continue
            if column == TESTS:
                symbols = {cls.name + '.' + method.name for cls in parsed.body
                           if isinstance(cls, ast.ClassDef) for method in cls.body
                           if isinstance(method, ast.FunctionDef) and method.name.startswith('test_')}
            else:
                symbols = {node.name for node in parsed.body if isinstance(node, ast.FunctionDef)}
            if symbol not in symbols:
                problems.append(where + ' is not a ' + ('test method' if column == TESTS else 'top-level checker function'))
        return cites

    for heading in ('## 0. Basis', '## 1. Vocabulary', CHAR_HEAD):
        if section_text(map_text, heading) is None:
            problems.append('expected one section: ' + heading)
    rows = table_rows(map_text, MAP_HEAD, HEADER, problems)
    ids = [r[0] for r in rows]
    for ident in EXPECTED:
        if ident not in ids:
            problems.append('missing row: ' + ident)
        elif ids.count(ident) != 1:
            problems.append('duplicated row: ' + ident)
    for ident in sorted(set(ids) - EXPECTED.keys()):
        problems.append('invented row: ' + ident)
    present = {r[SECTION] for r in rows if len(r) == len(HEADER)}
    for key in ('intro', *HEADINGS):
        if key not in present:
            problems.append('missing section coverage: ' + key)
    for cells in rows:
        ident = cells[0]
        if len(cells) != len(HEADER):
            problems.append(ident + ': expected eight cells')
            continue
        if ident not in EXPECTED:
            continue
        if cells[SECTION] != EXPECTED[ident][0] or not cells[CLAUSE]:
            problems.append(ident + ': section/clause mismatch')
        cites = (citations(ident, cells[TESTS], TESTS) +
                 citations(ident, cells[CHECKERS], CHECKERS))
        status, gap, owner = cells[STATUS:OWNER + 1]
        if not gap or '`' in gap:
            problems.append(ident + ': Gap must be nonempty text without backticks')
        if owner not in OWNERS:
            problems.append(ident + ': unknown owner: ' + owner)
        if status not in STATUSES:
            problems.append(ident + ': bad status')
        if status == 'COVERED' and (not cites or gap != 'none' or owner != 'none'):
            problems.append(ident + ': COVERED needs citations and no gap/owner')
        if status == 'PARTIAL' and (not cites or gap == 'none' or owner == 'none'):
            problems.append(ident + ': PARTIAL needs citations, gap and owner')
        if status == 'NOT_COVERED' and (cells[TESTS] != 'none' or cells[CHECKERS] != 'none' or
                                        gap == 'none' or owner == 'none'):
            problems.append(ident + ': NOT_COVERED needs no citations, gap and owner')
        if ident in PINNED:
            if status == 'COVERED':
                problems.append(ident + ': pinned gap must not be COVERED')
            if owner != HOST_OWNER:
                problems.append(ident + ': pinned owner must stay ' + HOST_OWNER)
        if ident in REQUIRED_CITES and REQUIRED_CITES[ident] not in cites:
            problems.append(ident + ': missing required citation: ' + REQUIRED_CITES[ident])
        for cite in REQUIRED_OFFLINE_CITES.get(ident, ()):
            if cite not in cites:
                problems.append(ident + ': missing required offline citation: ' + cite)
    want = count_line(rows)
    if [line for line in map_text.splitlines() if line.startswith('Counts:')] != [want]:
        problems.append('counts mismatch: expected ' + want)
    gaps = section_text(map_text, GAPS_HEAD) or ''
    for phrase in ('plan-plan-gate-fsm-seeded-journey-differentia', HOST_OWNER,
                   'not implemented in this node', GAP_LINK):
        if phrase not in gaps:
            problems.append('missing open-gap text: ' + phrase)
    for phrase in NON_CLAIMS:
        if phrase not in (section_text(map_text, '## 5. Non-claims') or ''):
            problems.append('missing non-claim: ' + phrase)
    return problems


def self_test(map_text, contract):
    """Require each in-memory negative's own diagnostic, with positive controls."""
    ident = 'G-HEALTH'
    good = '`' + TEST_PATH + '::InjectedTests.test_probe`'
    files = {TEST_PATH: (ROOT / TEST_PATH).read_bytes() +
             b'\nclass InjectedTests:\n    def test_probe(self): pass\n'}
    positive = _with_cell(map_text, ident, TESTS, good)
    if find_problems(positive, contract, files=files):
        print('self-test: valid injected test rejected', file=sys.stderr)
        return 1
    # Exercise valid status transitions independently of the map's live statuses.
    def recount(text):
        rows = table_rows(text, MAP_HEAD, HEADER, [])
        return re.sub(r'^Counts:.*$', count_line(rows), text, flags=re.M)

    partial = _with_cell(positive, ident, STATUS, 'PARTIAL')
    partial = _with_cell(partial, ident, GAP, 'Synthetic owned gap')
    partial = recount(_with_cell(partial, ident, OWNER, 'User'))
    uncovered = _with_cell(partial, ident, STATUS, 'NOT_COVERED')
    uncovered = _with_cell(uncovered, ident, TESTS, 'none')
    uncovered = recount(_with_cell(uncovered, ident, CHECKERS, 'none'))
    for control in (partial, uncovered):
        if find_problems(control, contract, files=files):
            print('self-test: valid synthetic status rejected', file=sys.stderr)
            return 1
    cases = []

    def case(label, text=map_text, source=contract, injected=None, reason=''):
        cases.append((label, text, source, injected, reason))

    def cell(label, row, col, value, reason, base=map_text, injected=None):
        case(label, _with_cell(base, row, col, value), injected=injected, reason=reason)

    line = _row_line(map_text, ident)
    for label, changed, reason in (
        ('missing row', map_text.replace(line + '\n', ''), 'missing row: ' + ident),
        ('duplicate row', map_text.replace(line, line + '\n' + line), 'duplicated row: ' + ident),
        ('invented row', map_text.replace(ident, 'G-INVENTED'), 'invented row: G-INVENTED'),
        ('row width', map_text.replace(line, line + ' extra |'), 'expected eight cells'),
        ('table header', map_text.replace('| Tests |', '| Wrong |'), 'bad table header'),
        ('counts', re.sub(r'Counts: rows=\d+', 'Counts: rows=999', map_text), 'counts mismatch'),
        ('duplicate map heading', map_text + '\n' + MAP_HEAD + '\n', 'expected one section'),
        ('section coverage', map_text.replace('| gate |', '| intro |'), 'missing section coverage: gate'),
    ):
        case(label, changed, reason=reason)
    for label, value, reason in (
        ('fabricated method', '`' + TEST_PATH + '::TransportTests.test_fabricated`', 'is not a test method'),
        ('fabricated offline method', '`' + OFFLINE_TEST_PATH + '::OfflineLimitsTests.test_fabricated`',
         'is not a test method'),
        ('module helper', '`' + TEST_PATH + '::assert_gate_headers`', 'needs a nonempty qualified'),
        ('wrong class', '`' + TEST_PATH + '::BrowserAccessTests.test_health_is_not_readiness`', 'is not a test method'),
        ('bare path', '`' + TEST_PATH + '`', 'needs a nonempty qualified'),
        ('empty symbol', '`' + TEST_PATH + '::`', 'needs a nonempty qualified'),
        ('absolute path', '`/tmp/probe.py::Probe.test_probe`', 'not repo-relative'),
        ('traversal', '`integration_gate/../probe.py::Probe.test_probe`', 'not repo-relative'),
        ('backslash path', '`integration_gate\\probe.py::Probe.test_probe`', 'not repo-relative'),
        ('reference path', '`reference/v0.3-rc1/probe.py::Probe.test_probe`', 'forbidden reference'),
        ('outside path', '`scripts/other.py::Probe.test_probe`', 'outside allowed citation paths'),
        ('wrong column', '`scripts/check_openapi_contract.py::validate`', 'outside allowed citation paths'),
        ('prose', good + ' prose', 'bad citation-cell grammar'),
    ):
        for suffix, val in (('alone', value), ('mixed', good + ', ' + value)):
            cell(label + ' ' + suffix, ident, TESTS, val, reason, injected=files)
    for label, data, reason in (
        ('missing file', None, 'file missing'),
        ('non-UTF8 file', b'\xff', 'not UTF-8'),
        ('syntax error', b'def broken(:\n', 'syntax error'),
    ):
        cell(label, ident, TESTS, good, TEST_PATH + ': ' + reason, injected={TEST_PATH: data})
    for label, value, reason in (
        ('fabricated checker', '`scripts/check_openapi_contract.py::fabricated`', 'is not a top-level checker function'),
        ('nested checker', '`scripts/check_openapi_contract.py::need`', 'is not a top-level checker function'),
        ('bare checker', '`scripts/check_openapi_contract.py`', 'needs a nonempty qualified'),
        ('checker wrong column', '`' + TEST_PATH + '::TransportTests.test_health_is_not_readiness`', 'outside allowed citation paths'),
    ):
        cell(label, ident, CHECKERS, value, reason)
    case('wrapper import removed', injected={WRAPPER: b'# from integration_gate.openapi_doc import main\n'},
         reason='wrapper must import main')
    for label, col, value, reason, base in (
        ('section cell', SECTION, 'read', 'section/clause mismatch', map_text),
        ('empty clause', CLAUSE, '', 'section/clause mismatch', map_text),
        ('bad status', STATUS, 'OPEN', 'bad status', map_text),
        ('covered gap', GAP, 'gap', 'COVERED needs', positive),
        ('covered owner', OWNER, 'User', 'COVERED needs', positive),
        ('partial no gap', GAP, 'none', 'PARTIAL needs', partial),
        ('partial no owner', OWNER, 'none', 'PARTIAL needs', partial),
        ('uncovered has tests', TESTS, good, 'NOT_COVERED needs', uncovered),
        ('uncovered has checkers', CHECKERS, '`integration_gate/openapi_doc.py::validate`', 'NOT_COVERED needs', uncovered),
        ('uncovered no gap', GAP, 'none', 'NOT_COVERED needs', uncovered),
        ('uncovered no owner', OWNER, 'none', 'NOT_COVERED needs', uncovered),
        ('unknown owner', OWNER, 'Someone', 'unknown owner', map_text),
        ('empty gap', GAP, '', 'Gap must be nonempty', map_text),
        ('backticks gap', GAP, '`gap`', 'Gap must be nonempty', map_text),
    ):
        cell(label, ident, col, value, reason, base=base, injected=files)
    for label, base, reason in (('covered no citations', positive, 'COVERED needs'),
                                ('partial no citations', partial, 'PARTIAL needs')):
        changed = _with_cell(_with_cell(base, ident, TESTS, 'none'), ident, CHECKERS, 'none')
        case(label, changed, reason=reason)
    for row in PINNED:
        cell('pinned status ' + row, row, STATUS, 'COVERED', 'pinned gap must not be COVERED')
        cell('pinned owner ' + row, row, OWNER, 'User', 'pinned owner must stay')
    for row, cite in REQUIRED_CITES.items():
        col = TESTS if cite.startswith(TEST_PATH) else CHECKERS
        cell('required citation ' + row, row, col, 'none', 'missing required citation: ' + cite)
    for row, cites in REQUIRED_OFFLINE_CITES.items():
        for cite in cites:
            original = split_row(_row_line(map_text, row))[TESTS]
            remaining = [item for item in CITATION.findall(original) if item != cite]
            cell('deleted offline citation ' + cite, row, TESTS,
                 ', '.join('`' + item + '`' for item in remaining) or 'none',
                 'missing required offline citation: ' + cite)
            cell('fabricated offline citation ' + cite, row, TESTS,
                 original.replace(cite, cite + '_fabricated'), 'is not a test method')
            method = cite.split('::')[1].split('.')[1]
            case('deleted offline method ' + cite, injected={OFFLINE_TEST_PATH:
                 (ROOT / OFFLINE_TEST_PATH).read_bytes().replace(
                     ('def ' + method + '(').encode(), ('def removed_' + method + '(').encode())},
                 reason=cite + ' is not a test method')
    case('anchor drift', source=contract.replace(EXPECTED['I-GATE-ROUTING'][1], 'changed'),
         reason='I-GATE-ROUTING: contract anchor is gone')
    case('added heading', source=contract + '\n## New\n', reason='contract headings must be exactly')
    case('duplicate heading', source=contract + '\n## 핀\n', reason='contract headings must be exactly')
    case('read item 7 removed', source=re.sub(r'^7\. .*\n', '', contract, flags=re.M),
         reason='read guidance must have exactly items 1..7')
    workflow = (ROOT / WORKFLOW).read_bytes()
    case('workflow command missing', injected={WORKFLOW: workflow.replace(
        b'python3 scripts/check_openapi_contract.py --self-test', b'# omitted')},
         reason='documented command missing from workflow: python3 scripts/check_openapi_contract.py --self-test')
    for phrase in ('not implemented in this node', GAP_LINK):
        case('open gap ' + phrase, map_text.replace(phrase, 'omitted'), reason='missing open-gap text: ' + phrase)
    case('open gap owner', map_text.replace('Owner: ' + HOST_OWNER, 'Owner: omitted'),
         reason='missing open-gap text: ' + HOST_OWNER)
    for phrase in NON_CLAIMS:
        case('non-claim ' + phrase, map_text.replace(phrase, 'omitted'), reason='missing non-claim: ' + phrase)
    for path in LOCKED_BLOBS:
        case('locked blob ' + path, injected={path: b'changed'}, reason='locked blob mismatch: ' + path)
    for module in ('socket', 'subprocess', 'http', 'integration_gate'):
        case('forbidden import ' + module,
             injected={SELF: (ROOT / SELF).read_bytes() + ('\nimport ' + module + '\n').encode()},
             reason='forbidden checker import: ' + module)
    case('forbidden from import', injected={SELF: (ROOT / SELF).read_bytes() + b'\nfrom socket import socket\n'},
         reason='forbidden checker import: socket')
    for label, text, source, injected, reason in cases:
        errors = find_problems(text, source, files=injected)
        if not any(reason in error for error in errors):
            print('self-test: failed to detect ' + label + ': ' + repr(errors), file=sys.stderr)
            return 1
        print('self-test: detected ' + label)
    print('self-test: pass (%d negative controls; injected positive and valid status controls)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_integration_gate_contract_evidence_map.py [--self-test]', file=sys.stderr)
        return 2
    try:
        map_text = (ROOT / MAP).read_text(encoding='utf-8')
        contract = (ROOT / CONTRACT).read_text(encoding='utf-8')
        problems = find_problems(map_text, contract)
        if problems:
            for problem in problems:
                print(problem, file=sys.stderr)
            return 1
        if argv:
            return self_test(map_text, contract)
    except (OSError, UnicodeError) as error:
        print('integration gate evidence input error: ' + str(error), file=sys.stderr)
        return 1
    print('integration gate contract evidence map ok: ' +
          next(line for line in map_text.splitlines() if line.startswith('Counts:')))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
