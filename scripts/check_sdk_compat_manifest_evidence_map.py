#!/usr/bin/env python3
"""Check bootstrap SDK manifest clause citations offline, using only stdlib.

Citation existence is not semantic coverage. Self-test mutations stay in memory;
this checker never invokes Node, generators, git or network services.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md'
CONTRACT = 'docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md'
VERIFIER = 'sdk/compat/verify_compat.mjs'
REPRO = 'validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py'
TEST = 'sdk/conformance/conformance.test.mjs'
CHECK = 'scripts/check_sdk_client.py'
ORDER_TEST = TEST + '::manifest verifier reports failures in contract order'
ORDER_ANCHORS = (
    b'manifest = parseStrict(manifestBytes)',
    b'errors.push("manifest field set drift")',
    b'errors.push("unknown profile_kind")',
    b'errors.push("profile bytes drift")',
    b'errors.push(`${label} bytes drift`)',
    b'errors.push("toolchain drift")',
    b'errors.push("generator bytes drift")',
    b'errors.push("sdk_output bytes drift")',
    b'errors.push(`vector bytes drift: ${vector.name}`)',
    b'errors.push("manifest sidecar digest drift")',
)
VECTORS = {f'sdk/conformance/vectors/{name}.vectors.json'
           for name in ('canonical-encoding', 'mixed-input')}
CODE = {VERIFIER, 'sdk/generate/generate_client.mjs',
        'sdk/generate/generate_manifest.mjs', 'sdk/package.json'}
JSON_FILES = {f'sdk/compat/{folder}/{name}.json'
              for rev in ('bootstrap-1', 'bootstrap-2')
              for folder, name in (('manifests', f'manifest.{rev}'),
                                   ('profiles', f'{rev}.profile'))}
EXPECTED = {'C1-PROFILE-NAME': (1, 'kix-canonical-json/1'),
 'C1-OBJECT-FORM': (1, '키를 유니코드 코드 포인트 순으로 정렬'),
 'C1-ARRAY-ORDER': (1, '요소 순서는 유지'),
 'C1-STRING-ESCAPE': (1, '`JSON.stringify` 이스케이프'),
 'C1-NUMBER-FORM': (1, '선행 0, `-0`, 소수, 지수 표기 없음'),
 'C1-INT-RANGE-BOUNDS': (1, '`-9007199254740991` 이상 `9007199254740991` 이하'),
 'C1-NO-FINAL-NEWLINE': (1, '마지막 newline 없음'),
 'C1-DEPTH-LIMIT': (1, '검증기 구현 한도 32'),
 'C1-APPLIES-TO': (1, '정규 형식은 manifest, profile, golden vector에 적용'),
 'C1-PARSESTRICT-BODIES': (1, '명령 본문을 바이트로 읽을 때는 `parseStrict`'),
 'C1-R-DUPLICATE-KEY': (1, '`duplicate-key`'),
 'C1-R-UNSORTED-KEYS': (1, '`unsorted-keys`'),
 'C1-R-NON-INTEGER': (1, '`non-integer`'),
 'C1-R-INTEGER-RANGE': (1, '`integer-range`'),
 'C1-R-TRUNCATED': (1, '`truncated`'),
 'C1-R-TRAILING-BYTES': (1, '`trailing-bytes`'),
 'C1-R-WHITESPACE': (1, '`whitespace`'),
 'C1-R-INVALID-UTF8': (1, '`invalid-utf8`'),
 'C2-SCHEMA-VERSION': (2, 'kix-compat-manifest/1'),
 'C2-FIELD-SET-CLOSED': (2, '다른 키는 거부'),
 'C2-PROFILE-KIND': (2, '`BOOTSTRAP` 또는 `SEMANTIC_CONFORMANCE`'),
 'C2-PROFILE-REVISION': (2, '프로파일 파일을 찾지 못하면 거절'),
 'C2-PROFILE-SHA256': (2, 'profile 파일 바이트의 SHA-256'),
 'C2-PRODUCER': (2,
                 '`repository`, `source_commit`, `source_tree`, `protocol_domain`, '
                 '`contract_schema_version`'),
 'C2-CONTRACT-REFS': (2, '각각 `path`, `gitBlob`, `sha256`'),
 'C2-GENERATOR': (2, '`toolchain` (`node-24`)'),
 'C2-SDK-OUTPUT': (2, '생성 카탈로그의 `path`, `sha256`'),
 'C2-VECTORS': (2, '`{name, path, sha256}` 배열'),
 'C2-SOURCE-REFS': (2, '`bootstrap-1`의 `extension_profile`은 `false`'),
 'C2-B1-SOURCE-PIN': (2, '7481b0e16ce9b903abbffa62249bb91cd9e63cfe'),
 'C2-B2-SOURCE-PIN': (2, 'c2cde86e21a6e5ba6f24a56548636db6d0a34c6f'),
 'C2-SIDECAR': (2, '소문자 hex와 newline으로만 둔다'),
 'C2-FORBIDDEN-KEYS': (2,
                       '`manifest_digest`, `manifest_sha256`, `final_commit`, `delivery_head`, '
                       '`consumer_head`'),
 'C3-PROFILE-PATH': (3, 'sdk/compat/profiles/<profile_revision>.profile.json'),
 'C3-PROFILE-FIELDS': (3, '`catalogue`, `vectors`, `grants`, `non_claims`만 가진다'),
 'C3-GRANTS': (3, '`catalogue-schema-binding only`'),
 'C3-CATALOGUE-COUNTS': (3, '정렬한 84개 명령'),
 'C3-SCHEMA-DIGESTS': (3, '명령별 스키마 digest와 OpenAPI 경로·sha256'),
 'C3-PROFILE-NO-SELF-REF': (3, 'profile에 `profile_sha256`, commit, 최종 HEAD를 넣지 않는다'),
 'C3-NON-CLAIMS': (3, '감사·승인을 부여하지 않는다고 적는다'),
 'C3-SEMANTIC-KIND-DEFERRED': (3, '후속 `contract-compatibility-profile`의 일'),
 'C4-CLI': (4, '[--expect-kind K] [--expect-revision R]'),
 'C4-CHECK-ORDER': (4, 'profile 바이트 해시, 두 OpenAPI 파일'),
 'C4-FAIL-CLOSED-EXIT': (4, '0이 아닌 상태로 끝난다'),
 'C4-JSON-ONE-LINE': (4, '판정은 JSON 한 줄이다'),
 'C4-READ-ONLY-NO-ANCESTRY': (4, '검증기는 읽기 전용이다'),
 'C5-GENERATE-CLIENT': (5, 'sdk/generate/generate_client.mjs'),
 'C5-GENERATE-MANIFEST-B2': (5, '`bootstrap-2` profile·manifest·sidecar를 만든다'),
 'C5-B1-NOT-REGENERATED': (5, '역사 핀으로 두고 다시 생성하지 않는다'),
 'C5-SOURCE-PIN-GUARD': (5, 'ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e'),
 'C5-NO-REWRITE-OLD-MANIFEST': (5, '새 바이트에 이전 manifest를 다시 쓰지 않는다')}

LOCKED_BLOBS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}
HEADINGS = ('## 1. Scope', '## 2. Map',
            '## 3. Contract discrepancies (AGENTS §8 class C)',
            '## 4. Characterizations (AGENTS §8 class B)', '## 5. Non-claims')
HEADER = ['ID', 'Section', 'Clause', 'Evidence', 'Status', 'Gap', 'Owner']
SECTION, CLAUSE, EVIDENCE, STATUS, GAP, OWNER = range(1, 7)
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED')
OWNERS = {'p-sdk follow-up', 'contract-compatibility-profile', 'User', 'none'}
NON_CLAIMS = ('no semantic conformance', 'no N/N−1', 'no production fitness',
              'catalogue-schema-binding only', 'no regeneration')
CITATION = re.compile(r'`([^`]+)`')
CITE_CELL = re.compile(r'`[^`]+`(?:,\s*`[^`]+`)*')


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


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


def table_rows(text, problems):
    section = section_text(text, HEADINGS[1])
    if section is None:
        return []
    cells = [split_row(line) for line in section.splitlines() if line.startswith('|')]
    if cells.count(HEADER) != 1:
        problems.append('bad table header')
    return [r for r in cells if r != HEADER and
            not all(re.fullmatch(r'[-:]+', c) for c in r)]


def normalized(text):
    return ' '.join(text.split())


def git_blob_sha(data):
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def find_problems(map_text, contract, root=ROOT, files=None):
    """Inject repo-relative bytes/None via files without any disk mutation."""
    files = {} if files is None else files
    cache, problems = {}, []

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
    for heading in HEADINGS:
        if map_text.splitlines().count(heading) != 1:
            problems.append('expected one section: ' + heading)
    headings = list(re.finditer(r'^## ([^\n]+)', contract, re.M))
    numbers, sections = [], {}
    for index, match in enumerate(headings):
        number = re.fullmatch(r'(\d+)\. .+', match[1])
        if number is None:
            problems.append('unmapped contract heading: ' + match[1])
            continue
        number = int(number[1])
        numbers.append(number)
        sections[number] = contract[match.end():
            headings[index + 1].start() if index + 1 < len(headings) else len(contract)]
    if numbers != list(range(1, 6)):
        problems.append('contract headings must be exactly 1..5 in order')
    for ident, (number, anchor) in EXPECTED.items():
        if normalized(anchor) not in normalized(sections.get(number, '')):
            problems.append(ident + ': contract anchor is gone')

    def citations(ident, cell):
        if cell != 'none' and not CITE_CELL.fullmatch(cell):
            problems.append(ident + ': bad evidence-cell grammar')
        cites = CITATION.findall(cell)
        executable = False
        for cite in cites:
            path, sep, name = cite.partition('::')
            where = ident + ': ' + cite
            if (Path(path).is_absolute() or '\\' in path or
                    any(p in ('', '.', '..') for p in path.split('/'))):
                problems.append(where + ' is not repo-relative')
                continue
            if path.startswith('reference/'):
                problems.append(where + ' is forbidden reference')
                continue
            if path not in {TEST, CHECK} | VECTORS | CODE | JSON_FILES:
                problems.append(where + ' is outside evidence paths')
                continue
            if not sep or not name.strip():
                problems.append(where + ' needs a nonempty symbol')
                continue
            data = read(path)
            if data is None:
                problems.append(where + ' file missing')
                continue
            try:
                source = data.decode('utf-8')
            except UnicodeDecodeError:
                problems.append(where + ' is not UTF-8')
                continue
            valid = False
            if path == TEST:
                valid = bool(re.search(r'^test\(' + re.escape(json.dumps(name)) + r'\s*,', source, re.M))
                diagnostic = 'missing cited test'
                executable |= valid
            elif path == CHECK:
                valid = bool(re.fullmatch(r'[A-Za-z_]\w*', name) and
                             re.search(r'^def ' + re.escape(name) + r'\(', source, re.M))
                diagnostic = 'missing cited def'
                executable |= valid
            elif path in VECTORS or path in JSON_FILES:
                try:
                    document = json.loads(source)
                    if path in VECTORS:
                        valid = name in [case['name'] for case in document['cases']]
                        executable |= valid
                    else:
                        valid = isinstance(document, dict) and name in document
                except (ValueError, KeyError, TypeError):
                    valid = False
                diagnostic = 'missing vector case' if path in VECTORS else 'missing JSON key'
            else:
                valid = name in source
                diagnostic = 'missing code anchor'
            if not valid:
                problems.append(where + ': ' + diagnostic)
        return cites, executable

    rows = table_rows(map_text, problems)
    ids = [r[0] for r in rows]
    for ident in EXPECTED:
        if ident not in ids:
            problems.append('missing row: ' + ident)
        elif ids.count(ident) != 1:
            problems.append('duplicated row: ' + ident)
    for ident in sorted(set(ids) - EXPECTED.keys()):
        problems.append('invented row: ' + ident)
    present = {r[SECTION] for r in rows if len(r) == len(HEADER)}
    for number in range(1, 6):
        if '§' + str(number) not in present:
            problems.append('missing section coverage: §' + str(number))
    counts = dict.fromkeys(STATUSES, 0)
    for cells in rows:
        ident = cells[0]
        if len(cells) != len(HEADER):
            problems.append(ident + ': expected seven cells')
            continue
        if ident not in EXPECTED:
            continue
        if cells[SECTION] != '§' + str(EXPECTED[ident][0]) or not cells[CLAUSE]:
            problems.append(ident + ': section/clause mismatch')
        cites, executable = citations(ident, cells[EVIDENCE])
        status, gap, owner = cells[STATUS:OWNER + 1]
        if not gap or '`' in gap:
            problems.append(ident + ': Gap must be nonempty text without backticks')
        if owner not in OWNERS:
            problems.append(ident + ': unknown owner: ' + owner)
        if status not in STATUSES:
            problems.append(ident + ': bad status')
        else:
            counts[status] += 1
            if status == 'COVERED' and (not executable or gap != 'none' or owner != 'none'):
                problems.append(ident + ': COVERED needs executable evidence and no gap/owner')
            if status == 'PARTIAL' and (not cites or gap == 'none' or owner == 'none'):
                problems.append(ident + ': PARTIAL needs citations, gap and owner')
            if status == 'NOT_COVERED' and (cells[EVIDENCE] != 'none' or gap == 'none' or owner == 'none'):
                problems.append(ident + ': NOT_COVERED needs no evidence, gap and owner')
        if ident == 'C4-CHECK-ORDER' and (status != 'COVERED' or ORDER_TEST not in cites):
            problems.append(ident + ': requires COVERED and the order regression citation')
        if ident == 'C3-SEMANTIC-KIND-DEFERRED' and owner != 'contract-compatibility-profile':
            problems.append(ident + ': owner must stay contract-compatibility-profile')
    want = 'Counts: rows=%d ' % len(rows) + ' '.join('%s=%d' % (s, counts[s]) for s in STATUSES)
    if [line for line in map_text.splitlines() if line.startswith('Counts:')] != [want]:
        problems.append('counts mismatch: expected ' + want)
    class_c = section_text(map_text, HEADINGS[2]) or ''
    for cite in (VERIFIER, REPRO):
        if '`' + cite + '`' not in class_c:
            problems.append('missing check-order resolution citation: ' + cite)
        if read(cite) is None:
            problems.append('check-order resolution file missing: ' + cite)
    source = read(VERIFIER) or b''
    offsets = [source.find(anchor) for anchor in ORDER_ANCHORS]
    if offsets[0] < 0 or any(a >= b for a, b in zip(offsets, offsets[1:])):
        problems.append('C4-CHECK-ORDER: verifier stage anchors missing or out of order')
    class_b = section_text(map_text, HEADINGS[3]) or ''
    for reason in ('depth', 'non-canonical', 'invalid-string', 'unsupported-value'):
        if '`' + reason + '`' not in class_b:
            problems.append('missing class-B reason: ' + reason)
    for phrase in NON_CLAIMS:
        if phrase not in (section_text(map_text, HEADINGS[4]) or ''):
            problems.append('missing non-claim: ' + phrase)
    return problems


def self_test(map_text, contract):
    """Each negative must produce its own diagnostic, not merely fail."""
    ident = 'C1-PROFILE-NAME'
    good = '`' + TEST + '::injected positive title`'
    injected = {TEST: (ROOT / TEST).read_bytes() + b'\ntest("injected positive title", () => {});\n'}
    if find_problems(_with_cell(map_text, ident, EVIDENCE, good), contract, files=injected):
        print('self-test: injected positive rejected', file=sys.stderr)
        return 1
    cases = []

    def case(label, text=map_text, source=contract, files=None, reason=''):
        cases.append((label, text, source, files, reason))

    def cell(label, row, col, value, reason):
        case(label, _with_cell(map_text, row, col, value), reason=reason)

    line = _row_line(map_text, ident)
    for label, text, reason in (
        ('duplicate clause ID', map_text.replace(line, line + '\n' + line), 'duplicated row: ' + ident),
        ('missing clause', map_text.replace(line + '\n', ''), 'missing row: ' + ident),
        ('invented clause', map_text.replace(ident, 'C1-INVENTED'), 'invented row: C1-INVENTED'),
        ('wrong count', re.sub(r'Counts: rows=\d+', 'Counts: rows=999', map_text), 'counts mismatch'),
        ('bad header', map_text.replace('| Evidence |', '| Tests |'), 'bad table header'),
        ('wrong row width', map_text.replace(line, line + ' extra |'), 'expected seven cells'),
        ('duplicate counts', map_text + '\nCounts: rows=999\n', 'counts mismatch'),
    ):
        case(label, text, reason=reason)
    for label, value, reason in (
        ('missing cited test', '`' + TEST + '::fabricated title`', 'missing cited test'),
        ('non-test helper', '`' + TEST + '::runVerifier`', 'missing cited test'),
        ('missing vector case', '`sdk/conformance/vectors/canonical-encoding.vectors.json::absent`', 'missing vector case'),
        ('missing def', '`' + CHECK + '::absent`', 'missing cited def'),
        ('missing JSON key', '`sdk/compat/profiles/bootstrap-2.profile.json::absent`', 'missing JSON key'),
        ('missing code anchor', '`' + VERIFIER + '::absent anchor`', 'missing code anchor'),
        ('absolute path', '`/tmp/probe::test`', 'not repo-relative'),
        ('traversal path', '`sdk/../probe::test`', 'not repo-relative'),
        ('reference path', '`reference/v0.3-rc1/probe::test`', 'forbidden reference'),
        ('outside path', '`scripts/other.py::test`', 'outside evidence paths'),
        ('bare path', '`' + TEST + '`', 'needs a nonempty symbol'),
        ('empty symbol', '`' + TEST + '::`', 'needs a nonempty symbol'),
        ('prose in citations', '`' + TEST + '::canonical encoding vectors` extra', 'bad evidence-cell grammar'),
        ('covered anchors only', '`' + VERIFIER + '::profile bytes drift`', 'COVERED needs executable'),
    ):
        cell(label, ident, EVIDENCE, value, reason)
    for label, row, col, value, reason in (
        ('NOT_COVERED cites tests', 'C3-SEMANTIC-KIND-DEFERRED', EVIDENCE,
         '`' + TEST + '::canonical encoding vectors`', 'NOT_COVERED needs no evidence'),
        ('PARTIAL without owner', 'C1-APPLIES-TO', OWNER, 'none', 'PARTIAL needs'),
        ('PARTIAL without gap', 'C1-APPLIES-TO', GAP, 'none', 'PARTIAL needs'),
        ('PARTIAL without evidence', 'C1-APPLIES-TO', EVIDENCE, 'none', 'PARTIAL needs'),
        ('unknown owner', ident, OWNER, 'Somebody', 'unknown owner'),
        ('covered gap', ident, GAP, 'unfinished', 'COVERED needs'),
        ('covered owner', ident, OWNER, 'User', 'COVERED needs'),
        ('covered no evidence', ident, EVIDENCE, 'none', 'COVERED needs'),
        ('uncovered no gap', 'C3-SEMANTIC-KIND-DEFERRED', GAP, 'none', 'NOT_COVERED needs'),
        ('uncovered no owner', 'C3-SEMANTIC-KIND-DEFERRED', OWNER, 'none', 'NOT_COVERED needs'),
        ('empty gap', ident, GAP, '', 'Gap must be nonempty'),
        ('gap citation', ident, GAP, '`unfinished`', 'Gap must be nonempty'),
        ('wrong section', ident, SECTION, '§5', 'section/clause mismatch'),
        ('empty clause', ident, CLAUSE, '', 'section/clause mismatch'),
        ('unknown status', ident, STATUS, 'OPEN', 'bad status'),
        ('order status pin', 'C4-CHECK-ORDER', STATUS, 'PARTIAL', 'requires COVERED'),
        ('order regression citation', 'C4-CHECK-ORDER', EVIDENCE,
         '`' + TEST + '::canonical encoding vectors`', 'requires COVERED and the order regression citation'),
        ('semantic owner pin', 'C3-SEMANTIC-KIND-DEFERRED', OWNER, 'User', 'owner must stay'),
    ):
        cell(label, row, col, value, reason)
    for heading in HEADINGS:
        case('missing heading ' + heading, map_text.replace(heading, 'omitted'), reason='expected one section: ' + heading)
        case('duplicate heading ' + heading, map_text + '\n' + heading + '\n', reason='expected one section: ' + heading)
    for path in (VERIFIER, REPRO):
        case('check-order resolution citation ' + path,
             map_text.replace('`' + path + '`', 'omitted'),
             reason='missing check-order resolution citation: ' + path)
    for phrase in NON_CLAIMS:
        # Mutate only the non-claims section, preserving scope/table references.
        prefix, tail = map_text.split(HEADINGS[4], 1)
        case('non-claim ' + phrase, prefix + HEADINGS[4] + tail.replace(phrase, 'omitted'), reason='missing non-claim: ' + phrase)
    for reason in ('depth', 'non-canonical', 'invalid-string', 'unsupported-value'):
        case('class B reason ' + reason, map_text.replace('`' + reason + '`', 'omitted'), reason='missing class-B reason: ' + reason)
    for label, source, reason in (
        ('new contract heading', contract + '\n## 6. New\n', 'contract headings must be exactly'),
        ('missing contract heading', contract.replace('## 1.', '## Missing'), 'contract headings must be exactly'),
        ('duplicate contract heading', contract + '\n## 5. Duplicate\n', 'contract headings must be exactly'),
        ('contract anchor drift', contract.replace(EXPECTED[ident][1], 'changed'), ident + ': contract anchor is gone'),
    ):
        case(label, source=source, reason=reason)
    source = (ROOT / VERIFIER).read_bytes()
    profile = b'errors.push("profile bytes drift")'
    output = b'errors.push("sdk_output bytes drift")'
    reordered = source.replace(profile, b'').replace(output, output + b'\n' + profile)
    anchor_error = 'C4-CHECK-ORDER: verifier stage anchors missing or out of order'
    case('profile hash reordered after output', files={VERIFIER: reordered}, reason=anchor_error)
    case('missing sidecar stage anchor', files={VERIFIER: source.replace(ORDER_ANCHORS[-1], b'')},
         reason=anchor_error)
    for path in LOCKED_BLOBS:
        case('locked blob ' + path, files={path: b'changed in memory'}, reason='locked blob mismatch: ' + path)
    for label, data, reason in (('missing file', None, 'file missing'),
                                ('non-UTF8 file', b'\xff', 'is not UTF-8')):
        case(label, files={TEST: data}, reason=reason)
    path = 'sdk/conformance/vectors/canonical-encoding.vectors.json'
    case('invalid vector JSON', files={path: b'{'}, reason='missing vector case')
    for label, text, source, files, reason in cases:
        problems = find_problems(text, source, files=files)
        if not any(reason in p for p in problems):
            print('self-test FAILED: ' + label + ': expected ' + reason, file=sys.stderr)
            return 1
        print('self-test: detected ' + label)
    print('self-test: pass (%d negative fixtures, injected positive control; memory only)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_sdk_compat_manifest_evidence_map.py [--self-test]', file=sys.stderr)
        return 2
    try:
        map_text = (ROOT / MAP).read_text(encoding='utf-8')
        contract = (ROOT / CONTRACT).read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        print('sdk compat evidence map: ' + str(error), file=sys.stderr)
        return 1
    problems = find_problems(map_text, contract)
    if problems:
        print('sdk compat evidence map failed:', file=sys.stderr)
        for problem in problems:
            print('- ' + problem, file=sys.stderr)
        return 1
    if argv == ['--self-test']:
        return self_test(map_text, contract)
    counts = next(line for line in map_text.splitlines() if line.startswith('Counts:'))
    print('sdk compat evidence map ok: ' + counts)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
