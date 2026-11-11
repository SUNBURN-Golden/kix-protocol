#!/usr/bin/env python3
"""Check Toss profile clause traceability using only local text and stdlib.

Symbol checks establish existence, not semantic coverage. No provider calls,
credentials, cited test execution or file mutations, including in --self-test.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md'
SOURCES = {
    'contract': 'docs/contracts/PG_TOSS_CARD_PROFILE.md',
    'adapter': 'docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md',
    'plan': 'docs/operations/TOSS_SANDBOX_CONFORMANCE_PLAN.md',
    'open': 'docs/contracts/FIRST_BATCH_OPEN_INPUTS.md',
}
LOCKED_BLOBS = {
    'runtime/crates/kix-kernel/src/lib.rs':
        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs':
        'b607996c83a119c349f1cc90469ac1ba82764e20',
}
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED', 'OPEN')
HEADER = ['ID', 'Section', 'Clause', 'Kernel tests', 'Python tests',
          'Related', 'Status', 'Gap', 'Owner']
SECTION, CLAUSE, KERNEL, PYTHON, RELATED, STATUS, GAP, OWNER = range(1, 9)
MAP_HEAD = '## 2. Map'
OPEN_HEAD = '## 3. Open items (verbatim)'
OPEN_HEADER = ['ID', '항목', '현재 상태·답할 주체', 'Owner', 'Map status']
OPEN_ROWS = ('S8-RESALE-SCOPE', 'S8-WEBHOOK-SIGNATURE', 'S8-SPLIT-PAYOUT')
OPEN_OWNERS = ('사용자; 토스 영업 담당자', '기존 담당자 질문지 5번', '토스')
RESERVED_OWNERS = {'k-provider-sandbox', 'k1-adapter-event-identity',
                   'k-stage5-durable-tx', 'DECISION_REQUIRED · Astra',
                   'not named in contract', 'none'}
CITATION = re.compile(r'`([^`]+)`')
TEST_CELL = re.compile(r'`[^`]+`(?:,\s*`[^`]+`)*')
TEST_FN = r'^\s*#\[test\]\s*\n\s*fn\s+%s\b'
PY_TEST_FN = r'^\s*def\s+%s\b'
LINKS = ('[ADAPTER_IDENTITY_EVIDENCE_MAP](ADAPTER_IDENTITY_EVIDENCE_MAP.md)',
         '[TOSS_SANDBOX_CONFORMANCE_PLAN](../operations/TOSS_SANDBOX_CONFORMANCE_PLAN.md)')
# Literal contract anchors, whitespace normalized within the numbered section.
EXPECTED = {
    'S1-SOURCES': 'S1~S6는 모두 토스 공식 문서',
    'S2-IDEMPOTENCY-15D': '처음 요청에 사용한 날부터',
    'S2-WEBHOOK-RETRY': '자동 재전송 최대',
    'S2-ADMIN-RETRY': "관리자 '다시 시도'",
    'S2-LOOKUP': '/v1/payments/orders/{orderId}',
    'S2-CUT': '체인 회수·구 writer 차단 증명은 없음',
    'S2-STATUS-STRING': 'DONE/ABORTED/CANCELED',
    'S3-INTERVAL-SUM': '5,461분',
    'S3-V4-UNKNOWN-TTL': 'TTL이 지난 UNKNOWN',
    'S3-V4-OLD-OPERATION': '오래된 원operation의 첫 일치 capture',
    'S3-V4-OWNER-CHANGE': 'owner가 교체됨',
    'S3-V4-BUDGET-FULL': '예산 만석',
    'S3-V4-OTHER-BUYER': '다른 구매자가 같은 좌석을 가짐',
    'S3-V4-DEDUPE': '동일 이벤트/같은 금액의 다른 이벤트',
    'S3-V4-CONFLICT': '상충·금액 불일치',
    'S3-NOW-MS': 'ctx.now_ms`로 만료를 판단한다',
    'S4-SIGNATURE': '확인 불가, 기존 질문지 5번 회신 대기',
    'S4-SIGNAL-NOT-FACT': '미검증 신호로 분류한다',
    'S4-LOOKUP-BINDING': '서버가 고정한 토스 API',
    'S4-NORMALIZE': '검증된 사실만',
    'S4-ACK': 'durable custody',
    'S5-NO-TEST-CARD': '국내 테스트 카드번호가 없고',
    'S5-FIXTURE-LABEL': '실제 토스 연동 검증이라고 라벨링하지 않는다',
    'S5-NO-RUN': '테스트 코드를 실행하지 않았다',
    'S6-CARD-ONLY': '일반 카드 한 경로만 둔다',
    'S6-ONE-PAYMENT': '다수 독립 결제의 batch로 취급하지 않는다',
    'S6-IDENTITY-SEPARATION': 'lastTransactionKey',
    'S6-SCOPE-BINDING': 'provider/MID/환경/API·계약 버전/상품',
    'S6-METHOD-SEPARATE': 'card 객체 하나가 있다는 이유로',
    'S7-BOUNDARY': '반환형/trait/schema는 미구현',
    'S7-INTEGER-KRW': '원 단위 정수를 기대한다',
    'S7-TIMEZONE': 'createdAt 표기에는 offset이',
    'S7-PG-SWITCH': '이미 보낸 UNKNOWN을',
    'S8-RESALE-SCOPE': '리셀·금융 대금의 가맹 범위',
    'S8-WEBHOOK-SIGNATURE': '일반 결제 웹훅 서명',
    'S8-SPLIT-PAYOUT': '「한 결제의 대금을 복수 수취인에게',
    'S8-RESIDUAL': '15일 만료 이후 계정 예외·상태/void 증거·조회 보존정책·자동 위임 한도·독립 cut은 계속 미정이다',
    'S8-APPROVER-DECLARATION': 'KIX-LC-TERM-HUMAN-AUTH/g0001',
    'S9-VERSION': 'LC-PRECEDENCE-returnrequired-review-20260919',
    'S9-CONDITIONS': '필수조건 실패를 구분한다',
    'S9-AUTO-ZERO': '실제 자동범위는 0',
}

PROVIDER_ROWS = {i for i in EXPECTED if i.startswith(('S1-', 'S2-'))} | {
    'S4-SIGNATURE', 'S4-LOOKUP-BINDING', 'S5-NO-RUN'}
MUST_BE_OPEN = {i for i in EXPECTED if i.startswith('S8-')} | {
    'S2-IDEMPOTENCY-15D', 'S2-CUT', 'S2-STATUS-STRING', 'S4-SIGNATURE',
    'S6-IDENTITY-SEPARATION', 'S6-SCOPE-BINDING'}


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
    """Return diagnostics; files injects repo-relative bytes/None for self-tests."""
    files = files or {}
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

    contract = sources.get('contract', '')
    sections = dict(re.findall(r'^## (\d+)\.([^\n]*(?:\n(?!## ).*)*)', contract, re.M))
    for ident, anchor in EXPECTED.items():
        section = sections.get(ident[1], '')
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
    for section in sections:
        if not any(i.startswith('S' + section + '-') for i in ids):
            problems.append('unmapped contract section: ' + section)

    adapter_rows = table_rows(sources.get('adapter', ''), MAP_HEAD,
        ['ID', 'Contract item', 'Locked v4 kernel', 'Reference mock',
         'Integration gate', 'Readiness journal', 'Toss profile', 'Status',
         'Missing or open', 'Owner'], problems)
    related_ids = {r[0] for r in adapter_rows}
    plan = sources.get('plan', '')
    related_ids.update(re.findall(r'^\|\s*(TS-[A-Z]\d*|TM\d{2})\s*\|', plan, re.M))
    open_ids = set(re.findall(r'^\|\s*(I\d{2})\s*\|', sources.get('open', ''), re.M))
    related_ids.update(open_ids)
    for token in sorted(set(re.findall(r'\bI\d{2}\b', map_text)) - open_ids):
        problems.append('unknown open input: ' + token)
    for link in LINKS:
        if link not in map_text:
            problems.append('missing cross-link: ' + link)
    if re.search(r'\b(?:PASS_SANDBOX|FIXTURE_PASS)\b', map_text):
        problems.append('provider result label forbidden')

    by_status = dict.fromkeys(STATUSES, 0)
    for cells in rows:
        ident = cells[0]
        if len(cells) != len(HEADER):
            problems.append(ident + ': expected nine cells')
            continue
        if ident not in EXPECTED:
            continue
        if cells[SECTION] != '§' + ident[1] or not cells[CLAUSE]:
            problems.append(ident + ': section/clause mismatch')
        tests = []
        for col in (KERNEL, PYTHON):
            cell = cells[col]
            cites = parse_cell(cell)
            tests.append(cites)
            if cell == 'none':
                continue
            if not TEST_CELL.fullmatch(cell):
                problems.append(ident + ': bad test-cell grammar')
            for path, symbol in cites:
                where = ident + ': ' + path + '::' + (symbol or '')
                if path.startswith('/') or '..' in path.split('/'):
                    problems.append(where + ' is not repo-relative')
                    continue
                if path.startswith('reference/v0.3-rc1/'):
                    problems.append(where + ' is forbidden reference')
                    continue
                pattern = (r'runtime/crates/kix-kernel(?:-v5)?/tests/[a-z0-9_]+\.rs'
                           if col == KERNEL else
                           r'(?:reference/(?:booking_resale_admission|settlement_f01_f03|provider_facts)|integration_gate|readiness)/test_[a-z0-9_]+\.py')
                if not re.fullmatch(pattern, path):
                    problems.append(where + ' is outside column paths')
                    continue
                if symbol is None or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', symbol):
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
                regex = TEST_FN if col == KERNEL else PY_TEST_FN
                if (col == PYTHON and not symbol.startswith('test_')) or not re.search(
                        regex % re.escape(symbol), text, re.M):
                    problems.append(where + ' is not a test function')
        if cells[RELATED] != 'none':
            for token in cells[RELATED].split(','):
                if token.strip() not in related_ids:
                    problems.append(ident + ': unknown related ID: ' + token.strip())
        status, gap, owner = cells[STATUS:OWNER + 1]
        for value in (gap, owner):
            if not value or '`' in value:
                problems.append(ident + ': Gap/Owner must be nonempty text without backticks')
        for part in owner.split(';'):
            part = part.strip()
            if not part or (part not in RESERVED_OWNERS and part not in contract):
                problems.append(ident + ': unknown owner: ' + part)
        has_tests = any(tests)
        if status not in STATUSES:
            problems.append(ident + ': bad status')
        else:
            by_status[status] += 1
            if status == 'COVERED' and (not tests[0] or tests[1] or gap != 'none' or owner != 'none'):
                problems.append(ident + ': COVERED needs kernel tests and no gap/owner')
            if status == 'PARTIAL' and (not has_tests or gap == 'none' or owner == 'none'):
                problems.append(ident + ': PARTIAL needs tests, gap and owner')
            if status in ('NOT_COVERED', 'OPEN') and (has_tests or gap == 'none' or owner == 'none'):
                problems.append(ident + ': ' + status + ' needs no tests, gap and owner')
            if status == 'OPEN' and not re.search(r'\b(?:UNDETERMINED|I\d{2}|DECISION_REQUIRED)\b', gap):
                problems.append(ident + ': OPEN needs an open input/decision gap')
        if tests[1] and ('analog' not in cells[CLAUSE].lower() or 'NOT Toss' not in cells[CLAUSE]):
            problems.append(ident + ': Python evidence must be labelled analog, NOT Toss')
        if ident in PROVIDER_ROWS and (has_tests or status not in ('NOT_COVERED', 'OPEN')):
            problems.append(ident + ': provider row cannot claim test coverage')
        if ident in MUST_BE_OPEN and status != 'OPEN':
            problems.append(ident + ': must stay OPEN')
        if ident in OPEN_ROWS and owner != OPEN_OWNERS[OPEN_ROWS.index(ident)]:
            problems.append(ident + ': open-item owner changed')

    want = 'Counts: rows=%d ' % len(rows) + ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)
    if [l for l in map_text.splitlines() if l.startswith('Counts:')] != [want]:
        problems.append('counts mismatch: expected ' + want)

    # Preserve the first two cells exactly: no whitespace/Markdown normalization.
    open_section = section_text(contract, '## 8. 미확정 사항·차단 범위·대안') or ''
    original = [split_row(l)[:2] for l in open_section.splitlines()
                if l.startswith('| ') and not l.startswith('| 항목')]
    copied = table_rows(map_text, OPEN_HEAD, OPEN_HEADER, problems)
    if len(original) != 3 or [r[0] for r in copied] != ['O1', 'O2', 'O3']:
        problems.append('open-item row set mismatch')
    for n, cells in enumerate(copied):
        if len(cells) != 5 or n >= len(original) or n >= len(OPEN_OWNERS):
            problems.append('bad open-item row')
            continue
        if cells[1:3] != original[n]:
            problems.append('open-item text changed: ' + cells[0])
        if cells[3] != OPEN_OWNERS[n] or any(
                p.strip() not in original[n][1] for p in cells[3].split(';')):
            problems.append('open-item owner changed: ' + cells[0])
        if cells[4] != 'UNDETERMINED/OPEN':
            problems.append('open-item status changed: ' + cells[0])

    intervals = re.search(r'간격 \*\*([\d,·]+)분\*\*', sections.get('2', ''))
    try:
        numbers = [int(n.replace(',', '')) for n in intervals[1].split('·')] if intervals else []
    except ValueError:
        numbers = []  # Unfamiliar/malformed schedule is a diagnostic, never a guessed value.
    total = sum(numbers)
    hours, minutes = divmod(total, 60)
    if numbers != [1, 4, 16, 64, 256, 1024, 4096] or total != 5461 or (
            f'{total:,}분' not in sections.get('3', '') or
            f'{hours}시간 {minutes}분' not in sections.get('3', '')):
        problems.append('retry interval arithmetic mismatch')
    return problems


def self_test(map_text, sources):
    """Mutate local inputs in memory; require specific negative diagnostics."""
    cases = []

    def cell(label, ident, col, value, reason, files=None):
        cases.append((label, _with_cell(map_text, ident, col, value), sources, files, reason))

    positive_count = 1  # main already checked the unmodified map
    probes = ((KERNEL, 'S3-V4-UNKNOWN-TTL', 'runtime/crates/kix-kernel-v5/tests/citation_probe.rs',
               b'#[test]\nfn test_probe() {}\nfn helper() {}\n'),
              (PYTHON, 'S4-SIGNAL-NOT-FACT', 'readiness/test_citation_probe.py',
               b'def test_probe(): pass\ndef helper(): pass\n'))
    for col, ident, path, data in probes:
        files = {path: data}
        good = '`%s::test_probe`' % path
        if find_problems(_with_cell(map_text, ident, col, good), sources, files=files):
            print('self-test: valid injected citation failed', file=sys.stderr)
            return 1
        positive_count += 1
        for label, value, reason in (
            ('missing symbol', '`%s::absent`' % path, 'is not a test function'),
            ('helper', '`%s::helper`' % path, 'is not a test function'),
            ('bare path', '`%s`' % path, 'needs a nonempty test symbol'),
            ('empty symbol', '`%s::`' % path, 'needs a nonempty test symbol'),
            ('blank symbol', '`%s::  `' % path, 'needs a nonempty test symbol'),
            ('prose', good + ' prose', 'test-cell grammar'),
        ):
            for suffix, val in (('alone', value), ('mixed', good + ', ' + value)):
                cell(label + suffix, ident, col, val, reason, files)
        cell('missing file', ident, col, good, 'file missing', {path: None})
        cell('non UTF8 file', ident, col, good, 'not UTF-8', {path: b'\xff'})
        for label, wrong, reason in (
            ('wrong column', 'integration_gate/test_probe.py' if col == KERNEL else
             'runtime/crates/kix-kernel/tests/probe.rs', 'outside column paths'),
            ('reference', 'reference/v0.3-rc1/test_probe.py', 'forbidden reference'),
            ('absolute', '/tmp/test_probe.py', 'not repo-relative'),
            ('traversal', 'readiness/../test_probe.py', 'not repo-relative'),
        ):
            cell(label, ident, col, '`%s::test_probe`' % wrong, reason)
    ident = 'S3-V4-UNKNOWN-TTL'
    line = _row_line(map_text, ident)
    for label, changed, reason in (
        ('removed row', map_text.replace(line + '\n', ''), 'missing row'),
        ('duplicate row', map_text.replace(line, line + '\n' + line), 'duplicated row'),
        ('invented row', map_text.replace(ident, 'S3-INVENTED'), 'invented row'),
        ('wrong width', map_text.replace(line, line + ' extra |'), 'expected nine cells'),
        ('header', map_text.replace('| Kernel tests |', '| Wrong |'), 'bad table header'),
        ('counts', re.sub(r'Counts: rows=\d+', 'Counts: rows=999', map_text), 'counts mismatch'),
        ('section', map_text + '\n' + MAP_HEAD + '\n', 'expected one section'),
        ('open dropped', map_text.replace(_row_line(map_text, 'O2') + '\n', ''), 'open-item row set mismatch'),
    ):
        cases.append((label, changed, sources, None, reason))
    for label, ident, col, value, reason in (
        ('section field', 'S3-V4-UNKNOWN-TTL', SECTION, '§2', 'section/clause mismatch'),
        ('bad status', 'S3-V4-UNKNOWN-TTL', STATUS, 'SUFFICIENT', 'bad status'),
        ('covered gap', 'S3-V4-UNKNOWN-TTL', GAP, 'unverified', 'COVERED needs'),
        ('partial without tests', 'S2-LOOKUP', STATUS, 'PARTIAL', 'PARTIAL needs'),
        ('not covered with tests', 'S3-V4-UNKNOWN-TTL', STATUS, 'NOT_COVERED', 'NOT_COVERED needs'),
        ('open without input', 'S2-CUT', GAP, 'unspecified', 'OPEN needs an open'),
        ('lost owner', 'S2-CUT', OWNER, 'none', 'OPEN needs no tests'),
        ('invented owner', 'S2-CUT', OWNER, 'invented_owner', 'unknown owner'),
        ('owner backticks', 'S2-CUT', OWNER, '`토스`', 'without backticks'),
        ('unknown input', 'S2-CUT', GAP, 'UNDETERMINED I99', 'unknown open input'),
        ('unknown related', 'S2-CUT', RELATED, 'TS-Z9', 'unknown related ID'),
        ('provider coverage', 'S2-LOOKUP', KERNEL,
         '`runtime/crates/kix-kernel/tests/transitions.rs::unknown_payment_is_not_released_by_ttl`',
         'provider row cannot claim'),
        ('Python label', 'S4-SIGNAL-NOT-FACT', CLAUSE, 'Payment fact.', 'labelled analog, NOT Toss'),
        ('open not OPEN', 'S8-RESIDUAL', STATUS, 'NOT_COVERED', 'must stay OPEN'),
        ('map open owner', 'S8-RESALE-SCOPE', OWNER, '토스', 'open-item owner changed'),
        ('altered text', 'O1', 1, 'changed', 'open-item text changed'),
        ('altered status text', 'O3', 2, 'confirmed', 'open-item text changed'),
        ('altered owner', 'O2', 3, '토스', 'open-item owner changed'),
        ('covered open item', 'O1', 4, 'COVERED', 'open-item status changed'),
    ):
        cell(label, ident, col, value, reason)
    for link in LINKS:
        cases.append(('missing link', map_text.replace(link, ''), sources, None, 'missing cross-link'))
    for token in ('PASS_SANDBOX', 'FIXTURE_PASS'):
        cases.append(('provider label', map_text + '\n' + token, sources, None, 'provider result label'))
    for path in LOCKED_BLOBS:
        cases.append(('locked blob', map_text, sources,
                      {path: (ROOT / path).read_bytes() + b'\n'}, 'locked blob mismatch'))
    for label, source, before, after, reason in (
        ('anchor removed', 'contract', EXPECTED['S1-SOURCES'], 'removed', 'contract anchor is gone'),
        ('new section', 'contract', '\n## 9.', '\n## 10.', 'unmapped contract section: 10'),
        ('interval drift', 'contract', '1·4·16·64·256·1,024·4,096분', '1·4·16·64·256·1,024·4,095분', 'retry interval arithmetic mismatch'),
        ('malformed intervals', 'contract', '1·4·16·64·256·1,024·4,096분', '1··4분', 'retry interval arithmetic mismatch'),
        ('total drift', 'contract', '5,461분', '5,462분', 'retry interval arithmetic mismatch'),
        ('hour drift', 'contract', '91시간 1분', '91시간 2분', 'retry interval arithmetic mismatch'),
        ('plan ID removed', 'plan', '| TS-B1 |', '| TS-Z9 |', 'unknown related ID: TS-B1'),
        ('adapter ID removed', 'adapter', '| RawEvidenceRef |', '| Removed |', 'unknown related ID: RawEvidenceRef'),
    ):
        changed = dict(sources)
        if before not in sources[source]:
            print('self-test fixture did not mutate: ' + label, file=sys.stderr)
            return 1
        changed[source] = sources[source].replace(before, after)
        cases.append((label, map_text, changed, None, reason))
    failed = []
    for label, changed, src, files, reason in cases:
        found = find_problems(changed, src, files=files)
        if not any(reason in p for p in found):
            failed.append('%s: missed %r; got %r' % (label, reason, found))
    if failed:
        print('\n'.join(failed), file=sys.stderr)
        return 1
    print('Toss profile self-test: %d positive controls and %d negative fixtures OK (memory only)' %
          (positive_count, len(cases)))
    return 0


def main():
    if sys.argv[1:] not in ([], ['--self-test']):
        print('usage: check_toss_card_profile_evidence_map.py [--self-test]', file=sys.stderr)
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
    print('Toss profile map: %d rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK' % len(EXPECTED))
    return 0


if __name__ == '__main__':
    sys.exit(main())
