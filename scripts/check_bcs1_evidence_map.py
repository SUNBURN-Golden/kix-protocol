#!/usr/bin/env python3
"""Validate BCS1 clause citations with stdlib and offline local text only.

Existence is not semantic coverage. Self-tests mutate in-memory inputs only.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md'
SOURCES = {'contract': 'runtime/CANONICAL_BINARY_BCS_V1.md'}
TEST_FILES = ('runtime/crates/kix-bcs1/src/lib.rs', 'runtime/crates/kix-bcs1/tests/golden_vectors.rs')
LOCKED_BLOBS = {
    'runtime/crates/kix-kernel/src/lib.rs':
        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs':
        'b607996c83a119c349f1cc90469ac1ba82764e20',
}
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED')
HEADER = ['ID', 'Section', 'Clause', 'Tests', 'Status', 'Gap', 'Owner']
FU_HEADER = ['FU', 'Row', 'Path', 'Candidate owner']
SECTION, CLAUSE, TESTS, STATUS, GAP, OWNER = range(1, 7)
MAP_HEAD = '## 2. Map'
FU_HEAD = '## 3. Follow-up candidates (NOT_COVERED, no tests added)'
MAPPED_SECTIONS = {'1', '2', '3', '5', '6', '7', '8'}
OWNERS = {'kix-bcs1 maintainer', 'KIX-BCS1 contract owner',
          'S08 Move/SDK schema owner', 'non-author A2 reviewer', 'none'}
NON_CLAIMS = ('no production schema registry', 'no Move/SDK equality',
              'no malformed-input corpus')
CITATION = re.compile(r'`([^`]+)`')
TEST_CELL = re.compile(r'`[^`]+`(?:,\s*`[^`]+`)*')
TEST_FN = r'^\s*#\[test\]\s*\n\s*fn\s+%s\b'

# Literal anchors are normalized only for whitespace within their section.
EXPECTED = {
    'S1-ENVELOPE-FIELDS': 'struct KixEnvelopeV1',
    'S1-CANONICAL-BYTES': 'canonical_bytes(T) = BCS(KixEnvelopeV1 { body: BCS(T), ... })',
    'S1-CANONICAL-HASH': 'canonical_hash(T) = SHA-256(canonical_bytes(T))',
    'S1-SCHEMA-PERMANENCE': '영구히 동일 schema를 뜻한다',
    'S1-VERSION-POSITIVE': 'schema_version: u16, // positive',
    'S2-TYPED-IDENTITY': 'caller-controlled schema negotiation을 허용하지 않는다',
    'S2-DECODE-ORDER': 'envelope 전체 길이를 schema bound와 비교한 뒤',
    'S2-ENVELOPE-BOUND': 'envelope 전체 길이를 schema bound와 비교한 뒤',
    'S2-BODY-BOUND-ENCODE': 'MAX_BODY_BYTES',
    'S2-BODY-BOUND-DECODE': 'body 길이를 다시 검증한다',
    'S2-SCHEMA-OWNS-BODY': 'schema-specific invariant를 검사한다',
    'S2-HASH-EXACT': '정확히 canonical envelope bytes의 SHA-256이다',
    'S2-BOUNDED-UTF8': 'UTF-8 byte length를 encode 전과 decode 시 모두 제한한다',
    'S2-UTF8-MULTIBYTE': 'UTF-8 byte length를 encode 전과 decode 시 모두 제한한다',
    'S2-TEST-DOMAIN-RESERVED': '65535/65535',
    'S3-AMOUNT-U128': 'u128 atoms',
    'S3-FIXED-WIDTH-IDS': '[u8;16]',
    'S3-BIGINT-FAST-LANE': 'online BIGINT fast lane',
    'S3-FIXED-INTEGERS-ENUMS': '안정된 numeric discriminant',
    'S3-BOUNDED-STRINGS': '외부 provider opaque id와 사용자 표시 문자열만',
    'S3-NO-MAP-SORTED': '명시된 binary key ordering',
    'S5-RUST-MOVE-EQUALITY': 'BCS field order와 integer width를 동일하게',
    'S5-CHAIN-BINDING': 'off-chain Order/Payment/SaleIntent와 exact binding',
    'S6-CE1-PRESERVED': '역사적 검증 자료로 유지한다',
    'S6-NO-PROMOTION': '암묵 승격하거나 같은 ID namespace에서 동일시하지 않는다',
    'S6-ORDER-SNAPSHOT': 'KIX-BCS1 snapshot을 새로 생성한다',
    'S6-CE1-FIXTURE-ROLE': '새 production runtime 설계권한이 아니다',
    'S7-GOLDEN-INPUTS': 'domainId = 65535',
    'S7-GOLDEN-BYTES': '고정 canonical bytes hex:',
    'S7-GOLDEN-HASH': '고정 SHA-256:',
    'S7-EXTERNAL-CONSTANT': '외부 고정 상수로 테스트한다',
    'S8-G1-FIXED-VALUES': 'Rust KIX-BCS1 encode/decode/hash 고정값.',
    'S8-G2-IDENTITY-MUTATION': 'magic/domain/schema/version 변이 거절.',
    'S8-G3-MALFORMED-TRAILING': 'malformed/trailing bytes 거절.',
    'S8-G3-TRUNCATED': 'malformed/trailing bytes 거절.',
    'S8-G4-U128': '`u128` zero/max lossless round-trip.',
    'S8-G5-BOUNDED-UTF8': 'bounded UTF-8 oversize encode/decode 거절.',
    'S8-G6-CE1-SEPARATION': 'CE1-like JSON bytes/hash와 KIX-BCS1 identity 분리.',
    'S8-MOVE-SDK-EQUALITY': 'Rust↔Move BCS equality golden vector를 추가한다',
}
FOLLOW_UP = {
    'S1-VERSION-POSITIVE': 'FU-ZERO-ID',
    'S2-ENVELOPE-BOUND': 'FU-ENVELOPE-TOO-LARGE',
    'S2-BODY-BOUND-ENCODE': 'FU-BODY-TOO-LARGE-ENCODE',
    'S2-BODY-BOUND-DECODE': 'FU-BODY-TOO-LARGE-DECODE',
    'S2-UTF8-MULTIBYTE': 'FU-UTF8-MULTIBYTE',
    'S5-RUST-MOVE-EQUALITY': 'FU-S08-MOVE-EQUALITY',
    'S8-G3-TRUNCATED': 'FU-TRUNCATED-ENVELOPE',
    'S8-MOVE-SDK-EQUALITY': 'FU-S08-SDK-EQUALITY',
}
MUST_BE_NOT_COVERED = set(FOLLOW_UP)
PRESERVED_PARTIAL = {
    'S2-BOUNDED-UTF8': 'runtime/crates/kix-bcs1/src/lib.rs::bounded_utf8_rejects_oversize_values',
    'S8-G3-MALFORMED-TRAILING':
        'runtime/crates/kix-bcs1/src/lib.rs::wrong_magic_schema_version_and_trailing_bytes_are_rejected',
    'S8-G5-BOUNDED-UTF8': 'runtime/crates/kix-bcs1/src/lib.rs::bounded_utf8_rejects_oversize_values',
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
    headings = list(re.finditer(r'^## (\d+)\.[^\n]*', contract, re.M))
    sections = {}
    for n, match in enumerate(headings):
        number = match[1]
        if number in sections:
            problems.append('duplicated contract section: ' + number)
        sections[number] = contract[match.end():
            headings[n + 1].start() if n + 1 < len(headings) else len(contract)]
    for ident, anchor in EXPECTED.items():
        if ' '.join(anchor.split()) not in ' '.join(sections.get(ident[1], '').split()):
            problems.append(ident + ': contract anchor is gone')
    for number in sorted(set(sections) - MAPPED_SECTIONS - {'4'}):
        problems.append('unmapped contract section: ' + number)

    rows = table_rows(map_text, MAP_HEAD, HEADER, problems)
    ids = [r[0] for r in rows]
    for ident in EXPECTED:
        if ident not in ids:
            problems.append('missing row: ' + ident)
        elif ids.count(ident) != 1:
            problems.append('duplicated row: ' + ident)
    for ident in sorted(set(ids) - set(EXPECTED)):
        problems.append('invented row: ' + ident)
    for number in sorted(MAPPED_SECTIONS):
        if not any(i.startswith('S' + number + '-') for i in ids):
            problems.append('unmapped contract section: ' + number)

    by_status = dict.fromkeys(STATUSES, 0)
    for cells in rows:
        ident = cells[0]
        if len(cells) != len(HEADER):
            problems.append(ident + ': expected seven cells')
            continue
        if ident not in EXPECTED:
            continue
        if cells[SECTION] != '§' + ident[1] or not cells[CLAUSE]:
            problems.append(ident + ': section/clause mismatch')
        cell = cells[TESTS]
        cites = parse_cell(cell)
        if cell != 'none' and not TEST_CELL.fullmatch(cell):
            problems.append(ident + ': bad test-cell grammar')
        for path, symbol in cites:
            where = ident + ': ' + path + '::' + (symbol or '')
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
            matches = list(re.finditer(TEST_FN % re.escape(symbol), text, re.M))
            if not matches:
                problems.append(where + ' is not a test function')
            elif path == TEST_FILES[0]:
                module = re.search(r'#\[cfg\(test\)\]\s*\nmod tests\s*\{', text)
                # Locate the closing brace, so a test after mod tests is rejected too.
                # This is a source-text check for these fixed files, not a Rust parser.
                end = None
                if module:
                    depth = 1
                    for pos in range(module.end(), len(text)):
                        depth += (text[pos] == '{') - (text[pos] == '}')
                        if depth == 0:
                            end = pos
                            break
                if not module or end is None or not any(
                        module.end() <= m.start() < end for m in matches):
                    problems.append(where + ' is not in mod tests')
        status, gap, owner = cells[STATUS:OWNER + 1]
        for value in (gap, owner):
            if not value or '`' in value:
                problems.append(ident + ': Gap/Owner must be nonempty text without backticks')
        for part in owner.split(';'):
            if part.strip() not in OWNERS:
                problems.append(ident + ': unknown owner: ' + part.strip())
        if 'none' in [p.strip() for p in owner.split(';')] and owner != 'none':
            problems.append(ident + ': none owner cannot be combined')
        if status not in STATUSES:
            problems.append(ident + ': bad status')
        else:
            by_status[status] += 1
            if status == 'COVERED' and (not cites or gap != 'none' or owner != 'none'):
                problems.append(ident + ': COVERED needs tests and no gap/owner')
            if status == 'PARTIAL' and (not cites or gap == 'none' or owner == 'none'):
                problems.append(ident + ': PARTIAL needs tests, gap and owner')
            if status == 'NOT_COVERED' and (cell != 'none' or gap == 'none' or owner == 'none'):
                problems.append(ident + ': NOT_COVERED needs no tests, gap and owner')
        if ident in MUST_BE_NOT_COVERED:
            if status != 'NOT_COVERED':
                problems.append(ident + ': must stay NOT_COVERED')
            if FOLLOW_UP[ident] not in gap:
                problems.append(ident + ': missing follow-up tag: ' + FOLLOW_UP[ident])
        if ident in PRESERVED_PARTIAL and (status != 'PARTIAL' or
                PRESERVED_PARTIAL[ident] not in [p + '::' + (s or '') for p, s in cites]):
            problems.append(ident + ': must stay PARTIAL with preserved citation')

    fu_rows = table_rows(map_text, FU_HEAD, FU_HEADER, problems)
    expected_fu = {(tag, ident) for ident, tag in FOLLOW_UP.items()}
    actual_fu = [(r[0], r[1]) for r in fu_rows if len(r) == 4]
    if len(fu_rows) != len(expected_fu) or len(actual_fu) != len(expected_fu) or set(actual_fu) != expected_fu:
        problems.append('follow-up table mismatch')
    for cells in fu_rows:
        if len(cells) != 4:
            continue
        if cells[2] not in TEST_FILES:
            problems.append('follow-up path outside test paths: ' + cells[0])
        if not cells[3] or any(p.strip() not in OWNERS - {'none'} for p in cells[3].split(';')):
            problems.append('unknown follow-up owner: ' + cells[0])
    want = 'Counts: rows=%d ' % len(rows) + ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)
    if [l for l in map_text.splitlines() if l.startswith('Counts:')] != [want]:
        problems.append('counts mismatch: expected ' + want)
    for phrase in NON_CLAIMS:
        if phrase not in (section_text(map_text, '## 5. Non-claims') or ''):
            problems.append('missing non-claim: ' + phrase)

    golden_data = read(TEST_FILES[1])
    try:
        golden = golden_data.decode('utf-8') if golden_data is not None else ''
    except UnicodeDecodeError:
        golden = ''
    for label, constant in (('고정 canonical bytes hex:', 'EXPECTED_BYTES'),
                            ('고정 SHA-256:', 'EXPECTED_HASH')):
        doc = re.search(re.escape(label) + r'\s*```text\s*([0-9a-f]+)\s*```', sections.get('7', ''))
        rust = re.search(r'const ' + constant + r':\s*\[u8;\s*(\d+)\]\s*=\s*\[(.*?)\];', golden, re.S)
        values = re.findall(r'0x([0-9a-fA-F]{2})\b', rust[2]) if rust else []
        if (not doc or not rust or len(values) != int(rust[1]) or
                ''.join(values).lower() != doc[1]):
            problems.append('golden constant mismatch: ' + constant)
    return problems


def self_test(map_text, sources):
    """Require valid injection to pass and each negative fixture to be rejected."""
    cases = []
    ident = 'S7-GOLDEN-BYTES'
    path = TEST_FILES[1]
    original = (ROOT / path).read_bytes()
    probe_files = {path: original + b'\n#[test]\nfn probe() {}\nfn helper() {}\n'}
    good = '`' + path + '::probe`'
    if find_problems(_with_cell(map_text, ident, TESTS, good), sources, files=probe_files):
        print('self-test: valid injected test rejected', file=sys.stderr)
        return 1

    def cell(label, row, col, value, reason, files=None):
        cases.append((label, _with_cell(map_text, row, col, value), sources, files, reason))

    for label, value, reason in (
        ('missing test citation', '`%s::absent`' % path, 'is not a test function'),
        ('non-test helper', '`%s::helper`' % path, 'is not a test function'),
        ('bare path', '`%s`' % path, 'needs a nonempty test symbol'),
        ('empty symbol', '`%s::`' % path, 'needs a nonempty test symbol'),
        ('blank symbol', '`%s::  `' % path, 'needs a nonempty test symbol'),
        ('prose after citation', good + ' prose', 'bad test-cell grammar'),
    ):
        for suffix, val in (('alone', value), ('mixed', good + ', ' + value)):
            cell(label + ' ' + suffix, ident, TESTS, val, reason, probe_files)
    for label, wrong, reason in (
        ('kernel path', 'runtime/crates/kix-kernel/src/lib.rs', 'outside test paths'),
        ('absolute path', '/tmp/probe.rs', 'not repo-relative'),
        ('traversal', 'runtime/../probe.rs', 'not repo-relative'),
        ('reference path', 'reference/v0.3-rc1/probe.rs', 'forbidden reference'),
    ):
        cell(label, ident, TESTS, '`%s::probe`' % wrong, reason)
    for label, data, reason in (('missing file', None, 'file missing'),
                                ('non-UTF8 file', b'\xff', 'not UTF-8')):
        cell(label, ident, TESTS, good, reason, {path: data})
    lib = TEST_FILES[0]
    for label, data in (
        ('before module', b'#[test]\nfn probe() {}\n' + (ROOT / lib).read_bytes()),
        ('after module', (ROOT / lib).read_bytes() + b'\n#[test]\nfn probe() {}\n'),
    ):
        cell(label, ident, TESTS, '`%s::probe`' % lib, 'not in mod tests', {lib: data})
    line = _row_line(map_text, ident)
    for label, changed, reason in (
        ('removed row', map_text.replace(line + '\n', ''), 'missing row'),
        ('duplicate row', map_text.replace(line, line + '\n' + line), 'duplicated row'),
        ('invented row', map_text.replace(ident, 'S7-INVENTED'), 'invented row'),
        ('row width', map_text.replace(line, line + ' extra |'), 'expected seven cells'),
        ('header', map_text.replace('| Tests |', '| Wrong |'), 'bad table header'),
        ('counts', re.sub(r'Counts: rows=\d+', 'Counts: rows=999', map_text), 'counts mismatch'),
        ('duplicate section', map_text + '\n' + MAP_HEAD + '\n', 'expected one section'),
        ('FU row removed', map_text.replace(_row_line(map_text, next(iter(FOLLOW_UP.values()))) + '\n', ''), 'follow-up table mismatch'),
        ('non-claim removed', map_text.replace(NON_CLAIMS[0], 'omitted'), 'missing non-claim'),
    ):
        cases.append((label, changed, sources, None, reason))
    for label, row, col, value, reason in (
        ('section field', ident, SECTION, '§2', 'section/clause mismatch'),
        ('OPEN status', ident, STATUS, 'OPEN', 'bad status'),
        ('SUFFICIENT status', ident, STATUS, 'SUFFICIENT', 'bad status'),
        ('covered gap', ident, GAP, 'gap', 'COVERED needs'),
        ('covered without tests', ident, TESTS, 'none', 'COVERED needs'),
        ('partial without tests', 'S2-BOUNDED-UTF8', TESTS, 'none', 'PARTIAL needs'),
        ('partial without gap', 'S2-BOUNDED-UTF8', GAP, 'none', 'PARTIAL needs'),
        ('partial without owner', 'S2-BOUNDED-UTF8', OWNER, 'none', 'PARTIAL needs'),
        ('not covered with tests', 'S1-VERSION-POSITIVE', TESTS, good, 'NOT_COVERED needs'),
        ('FU flipped', 'S1-VERSION-POSITIVE', STATUS, 'PARTIAL', 'must stay NOT_COVERED'),
        ('FU tag dropped', 'S1-VERSION-POSITIVE', GAP, 'zero ids', 'missing follow-up tag'),
        ('preserved partial citation lost', 'S2-BOUNDED-UTF8', TESTS, good, 'must stay PARTIAL'),
        ('preserved partial promoted', 'S8-G3-MALFORMED-TRAILING', STATUS, 'COVERED', 'must stay PARTIAL'),
        ('bad owner', ident, OWNER, 'someone', 'unknown owner'),
        ('empty gap', ident, GAP, '', 'Gap/Owner must be nonempty'),
    ):
        cell(label, row, col, value, reason, probe_files)
    for label, contract, reason in (
        ('anchor removed', re.sub(r'\s+'.join(map(re.escape, EXPECTED['S1-VERSION-POSITIVE'].split())), 'gone', sources['contract']), 'contract anchor is gone'),
        ('new numbered section', sources['contract'] + '\n## 9. New\n', 'unmapped contract section'),
        ('contract hex drift', sources['contract'].replace('4b495831', '4a495831'), 'golden constant mismatch'),
    ):
        cases.append((label, map_text, dict(sources, contract=contract), None, reason))
    cases.append(('golden byte drift', map_text, sources,
                  {path: original.replace(b'0x4b', b'0x4a', 1)}, 'golden constant mismatch'))
    for locked in LOCKED_BLOBS:
        cases.append(('locked-blob drift', map_text, sources,
                      {locked: b'drift'}, 'locked blob mismatch'))
    for label, changed, mutated_sources, files, reason in cases:
        found = find_problems(changed, mutated_sources, files=files)
        if not any(reason in item for item in found):
            print('self-test: %s accepted or wrong diagnostic: %s' % (label, found), file=sys.stderr)
            return 1
        print('self-test: detected %s (%s)' % (label, reason))
    print('self-test: pass (2 positive controls, %d negative fixtures)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_bcs1_evidence_map.py [--self-test]', file=sys.stderr)
        return 2
    try:
        map_text = (ROOT / MAP).read_text(encoding='utf-8')
        sources = {key: (ROOT / path).read_text(encoding='utf-8') for key, path in SOURCES.items()}
    except (OSError, UnicodeDecodeError) as error:
        print('BCS1 evidence map input error: ' + str(error), file=sys.stderr)
        return 1
    problems = find_problems(map_text, sources)
    if problems:
        print('BCS1 evidence map check failed:', file=sys.stderr)
        for problem in problems:
            print('- ' + problem, file=sys.stderr)
        return 1
    if argv:
        return self_test(map_text, sources)
    print('BCS1 evidence map ok: ' + next(l for l in map_text.splitlines() if l.startswith('Counts:')))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
