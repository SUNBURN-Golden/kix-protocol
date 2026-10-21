#!/usr/bin/env python3
"""Check the readiness runtime evidence map against the contract and citations.

Compares three inputs:

- ``docs/contracts/READINESS_RUNTIME.md``: the clause anchor strings each
  hardcoded row id keys on (the marker table, the journal and recovery
  rules, the record rules, the version-migration clauses, the integration
  gate clauses, the six "이 경계가 보인 것" checks, and the 보류 items).
- ``docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md``: the builder-authored
  map, one row per id, ten cells per row (id, clause paraphrase, the four
  fixture columns ``readiness.test_faults`` / ``readiness.conformance`` /
  ``readiness.test_conformance_sensitivity`` /
  ``integration_gate.test_http_gate``, impl/record, status, missing or
  open, owner).
- The owner sources — the contract, ``readiness/CONFORMANCE.md`` and
  ``docs/decisions/PROGRAM_DECISIONS_20260928.md``: every owner part must
  appear verbatim in one of them or be a reserved literal.

Checks, each reported on failure:

1. Banner. The map carries the builder-authored-not-a-review phrase and
   the operational-count-stays-0 phrase.
2. Ids. The hardcoded row ids equal the map first cells, each exactly
   once; missing, duplicated and invented ids are reported. Every id's
   contract anchor string is still present in the contract.
3. Row width. Ten cells per row; the clause cell is non-empty.
4. Cell grammar. Each fixture or impl/record cell is ``none`` or carries
   one or more backticked ``path::symbol`` citations with optional free
   text; a free-text-only cell is reported. The missing-or-open cell
   carries no citations.
5. Status. One of EXERCISED, PARTIAL, NOT_EXERCISED, OPEN, and it matches
   the cells: OPEN only on the designated OPEN-*/HOLD-* rows; otherwise
   EXERCISED when a fixture column cites anything and the missing cell is
   ``none``; PARTIAL when a fixture column cites anything and a gap is
   named; NOT_EXERCISED when no fixture column cites anything.
6. Owner. Every non-``none`` owner cell splits on ``;`` into parts that
   appear verbatim in the owner sources or the reserved literals. PARTIAL,
   NOT_EXERCISED and OPEN rows must name an owner and a non-``none``
   missing cell; EXERCISED rows keep ``none`` in both.
7. Citations. Each ``path::symbol`` is repo-relative, lies under its
   column's allowed patterns, is never under ``reference/v0.3-rc1/``, and
   the file exists. A symbol is a defined ``def``/``class``/module
   constant/dict key (Python) or exact text (Markdown).
8. Locked blobs. The git-blob SHA-1 of the two locked kernel files is
   recomputed and must equal the values pinned in AGENTS.md section 4.
9. Counts. The ``Counts:`` line equals the statuses recomputed from the
   map section.

Standard library only. Convenience check, not a contract gate. It reads
the cited files as text and executes none of them; it proves that a cited
name exists, not that the fixture asserts the clause. ``--self-test``
mutates in-memory copies and requires each break to be caught.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md'
CONTRACT = 'docs/contracts/READINESS_RUNTIME.md'
OWNER_SOURCES = (
    CONTRACT,
    'readiness/CONFORMANCE.md',
    'docs/decisions/PROGRAM_DECISIONS_20260928.md',
)
KERNEL_LIB = 'runtime/crates/kix-kernel/src/lib.rs'
KERNEL_QC = 'runtime/crates/kix-kernel/tests/quarantine_capacity.rs'
LOCKED_BLOBS = {
    KERNEL_LIB: '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    KERNEL_QC: 'b607996c83a119c349f1cc90469ac1ba82764e20',
}

STATUSES = ('EXERCISED', 'PARTIAL', 'NOT_EXERCISED', 'OPEN')
NEEDS_MISSING_AND_OWNER = ('PARTIAL', 'NOT_EXERCISED', 'OPEN')
EXTRA_OWNERS = {'DECISION_REQUIRED · Astra'}
BANNER_PHRASES = (
    'Builder-authored map, not a review or an acceptance',
    'operational count stays 0',
)
CELLS = 10
STATUS_CELL, MISSING_CELL, OWNER_CELL = 7, 8, 9
# column index -> (name, allowed path patterns)
COLUMNS = {
    2: ('readiness.test_faults', (r'readiness/test_faults\.py',)),
    3: ('readiness.conformance', (r'readiness/conformance\.py',)),
    4: ('readiness.test_conformance_sensitivity',
        (r'readiness/test_conformance_sensitivity\.py',)),
    5: ('integration_gate.test_http_gate',
        (r'integration_gate/test_http_gate\.py',)),
    6: ('impl/record', (
        r'readiness/[a-z_]+\.py',
        r'integration_gate/[a-z_]+\.py',
        r'readiness/CONFORMANCE\.md',
        r'validation/2026-(?:09-26-prod-readiness-infra'
        r'|10-17-readiness-journal-byte-sweep'
        r'|10-18-readiness-crash-point-sweep'
        r'|10-18-audit8-readiness-conformance-sweep-limit-note'
        r'|10-20-ai-delegation-wrap-conformance'
        r'|10-20-token-reward-readiness-wrap'
        r'|10-21-reward-wrap-conformance)/README\.md',
    )),
}
FIXTURE_COLUMNS = (2, 3, 4, 5)
FORBIDDEN_PREFIX = 'reference/v0.3-rc1/'
TEXT_SUFFIXES = ('.md',)
# Row id -> anchor string that must still be in the contract.
EXPECTED_ROWS = {
    'FLAG-PROTOCOL-TRUTH': '`protocolTruth` | `false` | 저널 레코드는 프로토콜 명령이나 권위 있는 상태가 아니다',
    'FLAG-PROD-CONFORMANCE': '`productionConformance` | `false` | 로컬 재생은 운영 적합 선언이 아니다',
    'FLAG-PROD-READINESS': '`productionReadiness` | `false` | `/health`와 `/ready`는 프로세스 프로브다',
    'FLAG-PROD-ENDPOINT': '`productionEndpoint` | `false` | 공개 운영 엔드포인트가 아니다',
    'FLAG-FSM-DURABLE': 'FSM `durable` | `false` | 래퍼가 FSM 뷰의 이 플래그를 켜지 않는다',
    'JRN-FRAME-FSYNC': '헤더는 `KIXRDY01`과 버전이다. 레코드는 길이와 정규화 JSON, CRC32다. 한 레코드를 쓴 뒤 `fsync`한다',
    'JRN-SINGLE-WRITER': '한 디렉터리에는 작성자가 하나다. 잠금을 못 얻으면 `JOURNAL_LOCKED`로 닫는다',
    'RCV-TORN-TAIL': '끝의 불완전한 프레임은 찢긴 쓰기다. 그 꼬리만 버리고, 체크섬이 맞는 앞선 레코드는 재생한다',
    'RCV-CHECKSUM-CLOSED': '길이가 맞는 프레임의 체크섬이 틀리면 `CHECKSUM_MISMATCH`다',
    'REC-FSM-ENTRY': 'FSM 레코드는 그 기계의 `export_journal` 항목 하나다',
    'REC-CORE-COMMIT': '통합 관문의 `core_commit`은 `operationId`, `actor`, `action`, `body`와 영수증 다이제스트다',
    'REPLAY-IDEMPOTENT': '같은 멱등 키나 같은 `operationId` 지문은 저장된 결과를 다시 준다',
    'MIG-READ-PATH': '다른 원본 버전은 `UNSUPPORTED_SCHEMA`다',
    'MIG-EXPLICIT': '`migrate_explicit(1, 2, records)`는 `migrate_v1_to_v2`다',
    'GATE-LOOPBACK': '기본 바인드는 `127.0.0.1`이다',
    'GATE-CONCURRENCY': '동시 처리 상한은 기본 8이고, 넘치면 `OVERLOADED`로 거절하며 줄을 무한히 만들지 않는다',
    'GATE-DRAIN': '종료 중에는 `/health`만 살리고 명령은 `NOT_READY`다',
    'OBS-AUDIT': '요청에는 `X-Request-Id`와 `X-Correlation-Id`를 붙이고, 감사 줄은 stderr의 JSON이다',
    'GATE-RESTART-LOSS': '`--readiness-dir`가 없으면 재시작 뒤에 인메모리 상태는 사라진다',
    'BUDGET-LIMITS': '레코드는 4096, 바이트는 8388608, 동시 처리는 8이다',
    'GATE-BROWSER-OPTIN': '브라우저 전송은 `--browser-origin http://127.0.0.1:5173`일 때만 열린다',
    'SEEN-SETTLEMENT': '정산 커밋의 `confirmed_cash`와 한 번의 배분이 재시작과 찢긴 쓰기 뒤에 한 번만 남는다',
    'SEEN-RESERVATION': '예약 슬롯 점유는 동시에 두 요청이 들어와도 하나다',
    'SEEN-RESALE': '리셀 수락은 버전을 한 단계만 올린다',
    'SEEN-CREDIT': '신용 인출의 `outstanding_exposure`는 한 번만 늘어난다',
    'SEEN-ADMISSION': '입장 소비는 `CONSUMED` 한 번이고, 버전은 2에서 멈춘다',
    'SEEN-GATE-REKILL': '죽인 통합 관문 프로세스는 같은 `create_event`를 다시 적용하지 않는다',
    'OPEN-LENPREFIX-MIDFRAME': '끝의 불완전한 프레임은 찢긴 쓰기다',
    'OPEN-ZERO-BYTE-REINIT': '끝의 불완전한 프레임은 찢긴 쓰기다',
    'OPEN-FRAME-BOUNDARY-CUT': '끝의 불완전한 프레임은 찢긴 쓰기다',
    'HOLD-PUBLIC-DEPLOY': '공개 배포, DNS, TLS 제품화, `0.0.0.0` 기본 노출',
    'HOLD-REAL-EXTERNALS': '실 PG, 은행, KYC, 공연장, 체인 최종성, 외부 정확히 한 번',
    'HOLD-PROD-CLAIM': '운영 적합 또는 운영 준비 완료라는 주장',
    'HOLD-R2-STORAGE': 'R2, 복제, 합의, 자체 저장 엔진, 백엔드 선택',
    'HOLD-COMMERCE-APPS': '`kix-commerce-apps` 결합',
    'HOLD-NEW-COMMANDS': '프로토콜 계약에 없는 새 명령',
}
# Ids allowed to carry the OPEN status: the three class-B
# characterizations pending the Astra ruling on the recovery clause and
# the six 보류 items. No other row may claim OPEN.
OPENABLE = frozenset(
    ident for ident in EXPECTED_ROWS
    if ident.startswith('OPEN-') or ident.startswith('HOLD-'))

CITATION = re.compile(r'`([^`]+)`')
STATUS_WORD = re.compile(r'[A-Z_]+')
MAP_HEAD = '## 2. Map'
COUNTS_LINE = 'Counts:'

DEF_PATTERNS = {
    '.py': r'^\s*(?:(?:async\s+)?def|class)\s+%s\b|^\s*%s\s*[:=]',
}


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


def symbol_defined(text, suffix, symbol):
    if suffix in TEXT_SUFFIXES:
        return symbol in text
    pattern = DEF_PATTERNS.get(suffix)
    if pattern is None:
        return False
    return re.search(pattern.replace('%s', re.escape(symbol)),
                     text, re.M) is not None


def git_blob_sha(text):
    data = text.encode('utf-8')
    return hashlib.sha1(b'blob %d\x00' % len(data) + data).hexdigest()


def owner_parts_ok(parts, owner_text):
    for part in parts:
        part = part.strip()
        if not part:
            return 'empty owner part'
        if part not in EXTRA_OWNERS and part not in owner_text:
            return ('owner %r is not written in the owner sources'
                    % part)
    return None


def find_problems(map_text, contract_text, owner_text, root=ROOT,
                  files=None):
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

    head = map_text.split('## ', 1)[0]
    for phrase in BANNER_PHRASES:
        if phrase not in head:
            problems.append('banner phrase %r is gone' % phrase)

    # Locked-blob guard: the cited kernel files must stay byte-pinned.
    for rel, want in LOCKED_BLOBS.items():
        text = read(rel)
        if text is None:
            problems.append('locked file missing: %s' % rel)
        elif git_blob_sha(text) != want:
            problems.append('locked blob mismatch: %s (have %s, want %s)'
                            % (rel, git_blob_sha(text), want))

    for ident, anchor in EXPECTED_ROWS.items():
        if anchor not in contract_text:
            problems.append('%s: contract anchor %r is gone'
                            % (ident, anchor))

    expected = list(EXPECTED_ROWS)
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
            problems.append('duplicated in map: %s (%d)'
                            % (ident, counts[ident]))

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
        if not cells[1]:
            problems.append('%s: empty clause cell' % ident)

        fixture_total = 0
        checked = list(COLUMNS) + [MISSING_CELL]
        for col in checked:
            cell = cells[col]
            if col != MISSING_CELL and not cell:
                problems.append('%s: empty %s cell'
                                % (ident, COLUMNS[col][0]))
                continue
            cites = parse_cell(cell)
            if col in FIXTURE_COLUMNS:
                fixture_total += len(cites)
            if not cites and cell != 'none' and col != MISSING_CELL:
                problems.append('%s: %s cell is neither none nor a '
                                'citation'
                                % (ident, COLUMNS[col][0]))
            for path, symbol in cites:
                where = '%s: %s citation %s' % (
                    ident, COLUMNS.get(col, ('?',))[0], path)
                if col == MISSING_CELL:
                    problems.append('%s is inside the missing cell' % where)
                    continue
                if path.startswith('/') or '..' in path.split('/'):
                    problems.append('%s is not repo-relative' % where)
                    continue
                if path.startswith(FORBIDDEN_PREFIX):
                    problems.append('%s is under reference/v0.3-rc1'
                                    % where)
                    continue
                if not any(re.fullmatch(p, path)
                           for p in COLUMNS[col][1]):
                    problems.append('%s is outside the %s column paths'
                                    % (where, COLUMNS[col][0]))
                text = read(path)
                if text is None:
                    problems.append('%s does not exist' % where)
                    continue
                if symbol is None:
                    problems.append('%s needs a ::symbol' % where)
                elif not symbol_defined(text, Path(path).suffix, symbol):
                    problems.append('%s::%s is not defined in the file'
                                    % (where, symbol))

        status_cell = cells[STATUS_CELL]
        match = STATUS_WORD.fullmatch(status_cell)
        status = match.group(0) if match else ''
        if status not in STATUSES:
            problems.append('%s: unknown status %r'
                            % (ident, status_cell))
        else:
            if status == 'OPEN':
                if ident not in OPENABLE:
                    problems.append('%s: OPEN is reserved for the '
                                    'designated open or held rows' % ident)
            elif ident in OPENABLE:
                problems.append('%s: %s row is a designated open row and '
                                'must carry OPEN' % (ident, status))
            else:
                if fixture_total:
                    want = ('EXERCISED'
                            if cells[MISSING_CELL].lower().startswith('none')
                            else 'PARTIAL')
                else:
                    want = 'NOT_EXERCISED'
                if status != want:
                    problems.append('%s: status %s should be %s for these '
                                    'cells' % (ident, status, want))
            by_status[status] += 1

        if not cells[MISSING_CELL]:
            problems.append('%s: empty missing-or-open cell' % ident)
        elif status == 'EXERCISED' \
                and not cells[MISSING_CELL].lower().startswith('none'):
            problems.append('%s: EXERCISED row must keep the missing '
                            'cell none' % ident)
        elif status in NEEDS_MISSING_AND_OWNER \
                and cells[MISSING_CELL].lower().startswith('none'):
            problems.append('%s: %s row must say what is missing or open'
                            % (ident, status))
        if status in NEEDS_MISSING_AND_OWNER:
            if not cells[OWNER_CELL] or cells[OWNER_CELL] == 'none':
                problems.append('%s: %s row must have an owner'
                                % (ident, status))
            else:
                err = owner_parts_ok(cells[OWNER_CELL].split(';'),
                                     owner_text)
                if err:
                    problems.append('%s: %s' % (ident, err))
        elif status != 'OPEN' and cells[OWNER_CELL] != 'none':
            err = owner_parts_ok(cells[OWNER_CELL].split(';'), owner_text)
            if err:
                problems.append('%s: %s' % (ident, err))

    lines = [l for l in map_text.splitlines() if l.startswith(COUNTS_LINE)]
    want = COUNTS_LINE + ' ' + ' '.join('%s=%d' % (s, by_status[s])
                                      for s in STATUSES)
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


def self_test(map_text, contract_text, owner_text):
    """Require each check to catch a deliberately broken copy."""
    base = find_problems(map_text, contract_text, owner_text)
    if base:
        print('self-test: unmodified map already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1

    py_probe = "'x-probe': {\nKEY_PROBE = 1\ndef d_probe():\n    pass\n"
    if not (symbol_defined(py_probe, '.py', "'x-probe'")
            and symbol_defined(py_probe, '.py', 'KEY_PROBE')
            and symbol_defined(py_probe, '.py', 'd_probe')
            and not symbol_defined(py_probe, '.py', 'no_probe')):
        print('self-test: Python symbol pattern failed its positive control',
              file=sys.stderr)
        return 1

    torn = 'RCV-TORN-TAIL'
    exercised = 'JRN-SINGLE-WRITER'
    open_row = 'OPEN-LENPREFIX-MIDFRAME'
    partial = 'REC-CORE-COMMIT'
    rows = {i: _row_line(map_text, i)
            for i in (torn, exercised, open_row, partial)}
    if None in rows.values():
        print('self-test: could not find the rows to mutate', file=sys.stderr)
        return 1
    counts_line = next(l for l in map_text.splitlines()
                       if l.startswith(COUNTS_LINE))
    torn_faults = split_row(rows[torn])[2]
    cases = [
        ('removed %s row' % torn,
         map_text.replace(rows[torn] + '\n', '', 1),
         'missing in map: ' + torn),
        ('duplicated %s row' % torn,
         map_text.replace(rows[torn],
                          rows[torn] + '\n' + rows[torn], 1),
         'duplicated in map: ' + torn),
        ('invented id',
         map_text.replace(
             counts_line,
             '| FAKE-ID-9f3a | x | none | none | none | none | none '
             '| OPEN | gap | Astra |\n' + counts_line, 1),
         'invented id'),
        ('dangling path',
         _with_cell(map_text, torn, 4,
                    '`readiness/test_conformance_sensitivity.py::x`'),
         'does not exist'),
        ('dangling symbol',
         _with_cell(map_text, torn, 2,
                    torn_faults + ' `readiness/test_faults.py::no_such_test_9f3a`'),
         'is not defined in the file'),
        ('citation in the wrong column',
         _with_cell(map_text, torn, 2,
                    '`readiness/conformance.py::BackendConformance`'),
         'outside the readiness.test_faults column paths'),
        ('citation under reference/v0.3-rc1',
         _with_cell(map_text, torn, 2, '`reference/v0.3-rc1/core.py::execute`'),
         'reference/v0.3-rc1'),
        ('free-text-only fixture cell',
         _with_cell(map_text, torn, 3, 'something vague but present'),
         'is neither none nor a citation'),
        ('citation inside the missing cell',
         _with_cell(map_text, torn, MISSING_CELL,
                    'a gap `readiness/store.py::open`'),
         'inside the missing cell'),
        ('unknown status',
         _with_cell(map_text, torn, STATUS_CELL, 'SUFFICIENT'),
         'unknown status'),
        ('status that does not match the cells',
         _with_cell(map_text, exercised, STATUS_CELL, 'PARTIAL'),
         'should be'),
        ('EXERCISED row with no fixture citation',
         _with_cell(map_text, exercised, 2, 'none'),
         'should be'),
        ('NOT_EXERCISED row carrying a citation',
         _with_cell(map_text, torn, STATUS_CELL, 'NOT_EXERCISED'),
         'should be'),
        ('OPEN on a non-designated row',
         _with_cells(map_text, exercised,
                     [(STATUS_CELL, 'OPEN'), (MISSING_CELL, 'a gap'),
                      (OWNER_CELL, 'Astra')]),
         'OPEN is reserved'),
        ('designated open row reclassified',
         _with_cell(map_text, 'HOLD-NEW-COMMANDS', STATUS_CELL, 'EXERCISED'),
         'must carry OPEN'),
        ('OPEN row with no owner',
         _with_cell(map_text, open_row, OWNER_CELL, 'none'),
         'must have an owner'),
        ('owner not written in the owner sources',
         _with_cell(map_text, exercised, OWNER_CELL, 'Nobody Else'),
         'is not written in the owner sources'),
        ('EXERCISED row naming a gap',
         _with_cell(map_text, exercised, MISSING_CELL, 'a leftover gap'),
         'should be'),
        ('PARTIAL row without an owner',
         _with_cell(map_text, partial, OWNER_CELL, 'none'),
         'must have an owner'),
        ('wrong counts line',
         map_text.replace(counts_line,
                          counts_line.replace('OPEN=', 'OPEN=99', 1), 1),
         'counts line'),
        ('dropped banner phrase',
         map_text.replace('operational count stays 0',
                          'operational count rises to 1', 1),
         'banner phrase'),
    ]
    for name, mutated, marker in cases:
        found = find_problems(mutated, contract_text, owner_text)
        hit = [item for item in found if marker in item]
        if not hit:
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        print('self-test: detected %s (%s)' % (name, hit[0]))

    # Locked-blob guard via file injection.
    lib_text = (ROOT / KERNEL_LIB).read_text(encoding='utf-8')
    found = find_problems(map_text, contract_text, owner_text,
                          files={KERNEL_LIB: lib_text + '\n// mutated\n'})
    hit = [item for item in found if 'locked blob mismatch' in item]
    if not hit:
        print('self-test: mutated kernel lib.rs was accepted',
              file=sys.stderr)
        return 1
    print('self-test: detected mutated locked blob (%s)' % hit[0])

    ident, anchor = next(iter(EXPECTED_ROWS.items()))
    anchorless = contract_text.replace(anchor, '(x)', 1)
    found = find_problems(map_text, anchorless, owner_text)
    hit = [item for item in found if 'contract anchor' in item]
    if not hit:
        print('self-test: removed contract anchor was accepted',
              file=sys.stderr)
        return 1
    print('self-test: detected removed contract anchor (%s)' % hit[0])

    print('self-test: pass')
    return 0


def main(argv):
    texts = []
    for rel in (MAP,) + OWNER_SOURCES:
        path = ROOT / rel
        if not path.is_file():
            print('missing ' + str(path), file=sys.stderr)
            return 1
        texts.append(path.read_text(encoding='utf-8'))
    map_text = texts[0]
    contract_text = texts[1]
    owner_text = '\n'.join(texts[1:])
    if '--self-test' in argv:
        return self_test(map_text, contract_text, owner_text)
    problems = find_problems(map_text, contract_text, owner_text)
    if problems:
        print('readiness runtime evidence map check failed:',
              file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    rows, _ = map_rows(map_text, set(EXPECTED_ROWS))
    by_status = {s: 0 for s in STATUSES}
    cites = 0
    for _, cells in rows:
        by_status[cells[STATUS_CELL]] += 1
        for col in COLUMNS:
            cites += len(parse_cell(cells[col]))
    print('readiness runtime evidence map ok: rows=%d expected=%d '
          'citations=%d %s'
          % (len(rows), len(EXPECTED_ROWS), cites,
             ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
