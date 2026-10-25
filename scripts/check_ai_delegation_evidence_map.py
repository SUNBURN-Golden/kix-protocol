#!/usr/bin/env python3
"""Stdlib structure/citation checks for the AI delegation contract evidence map.

Source-informed, not a semantic adequacy or acceptance check. Never imports tests
or reads the frozen reference tree. Negative controls mutate in-memory inputs.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md'
CONTRACT = 'docs/contracts/AI_DELEGATION_AUTHORITY.md'
MATRIX = 'docs/status/AI_DELEGATION_LAYER_MATRIX.md'
ECC = 'docs/status/CONTRACT_ERROR_CODE_COVERAGE.md'
MOCK = 'reference/ai_delegation/ai_delegation_mock.py'
ARCH = 'runtime/ARCHITECTURE.toml'
TEST_DIRS = ('reference/ai_delegation',)
READINESS_TESTS = {'readiness/test_faults.py', 'readiness/conformance.py'}
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED', 'OPEN')
MUST_BE_OPEN = {'§9'}
MUST_BE_NOT_COVERED = {'§10'}
BANNERS = ('Builder-authored map, not a review or an acceptance', 'no grade change',
           '`delegated_execution_enabled` stays `false`')
HEADING = re.compile(r'^## (\d+)\. (.+)$', re.M)
ID_CELL = re.compile(r'^\|\s*(§\d+)\s*\|')
ITEM_ROW = re.compile(r'^\|\s*(O\d+)\s*\|')
CODE_ROW = re.compile(r'^\|\s*`([^`]+)`\s*\|')
CITATION = re.compile(r'`([^`\n]+)::([^`\n]+)`')
EVIDENCE_CELL = re.compile(r'`[^`\n]+::[^`\n]+`(?:; `[^`\n]+::[^`\n]+`)*')


def split_row(line):
    return [cell.strip() for cell in line.strip().strip('|').split('|')]


def rows_matching(text, pattern):
    return [(match.group(1), split_row(line)) for line in text.splitlines()
            for match in [pattern.match(line)] if match]


def map_rows(text):
    return rows_matching(text, ID_CELL)


def parse_cell(cell):
    return CITATION.findall(cell)


def is_case_base(base):
    return ((isinstance(base, ast.Name) and base.id == 'TestCase') or
            (isinstance(base, ast.Attribute) and base.attr == 'TestCase'
             and isinstance(base.value, ast.Name) and base.value.id == 'unittest'))


def test_symbols(source, mixin=False):
    """Accept direct methods on classes with a transitive in-module TestCase base."""
    classes = {n.name: n for n in ast.parse(source).body if isinstance(n, ast.ClassDef)}
    cases = {name for name, node in classes.items() if any(is_case_base(b) for b in node.bases)}
    while True:
        derived = {name for name, node in classes.items()
                   if any(isinstance(b, ast.Name) and b.id in cases for b in node.bases)}
        if derived <= cases:
            break
        cases |= derived
    if mixin:
        cases.add('BackendConformance')
    return {name + '.' + method.name for name, node in classes.items() if name in cases
            for method in node.body if isinstance(method, ast.FunctionDef)
            and method.name.startswith('test_')}


def read_source(path, files):
    if path in files:
        return files[path]
    full = ROOT / path
    try:
        # Resolve before reading. No escaped symlink or frozen-tree reads.
        resolved = full.resolve()
        parent = ROOT / Path(path).parent
        if not resolved.is_relative_to(parent) or resolved.is_relative_to(ROOT / 'reference/v0.3-rc1'):
            return None
        return full.read_text(encoding='utf-8') if full.is_file() else None
    except (OSError, UnicodeError, RuntimeError):
        return None


def mixin_is_used(files):
    source = read_source('readiness/test_faults.py', files)
    if source is None:
        return False
    try:
        return any(isinstance(n, ast.ClassDef)
                   and any(isinstance(b, ast.Name) and b.id == 'BackendConformance' for b in n.bases)
                   and any(is_case_base(b) for b in n.bases) for n in ast.parse(source).body)
    except SyntaxError:
        return False


def citation_problems(ident, evidence, files, symbols_by_path):
    problems = []
    if evidence != 'none' and not EVIDENCE_CELL.fullmatch(evidence):
        problems.append(ident + ': malformed evidence cell')
    for path, symbol in parse_cell(evidence):
        target = Path(path)
        if (target.is_absolute() or '..' in target.parts
                or path != target.as_posix() or '\\' in path):
            problems.append(ident + ': path must be repo-relative: ' + path)
            continue
        if (path.startswith('reference/v0.3-rc1/')
                or not ((target.parent.as_posix() in TEST_DIRS and target.match('test_*.py'))
                        or path in READINESS_TESTS)):
            problems.append(ident + ': not an allowed test path: ' + path)
            continue
        if path not in symbols_by_path:
            source = read_source(path, files)
            if source is None:
                problems.append(ident + ': cited file does not exist: ' + path)
                symbols_by_path[path] = set()
            else:
                try:
                    mixin = path == 'readiness/conformance.py' and mixin_is_used(files)
                    symbols_by_path[path] = test_symbols(source, mixin)
                except SyntaxError:
                    problems.append(ident + ': cited file has invalid Python: ' + path)
                    symbols_by_path[path] = set()
        if symbol not in symbols_by_path[path]:
            problems.append(ident + ': symbol is missing or not a test: ' + path + '::' + symbol)
    return problems


def completeness(rows, expected, label):
    occurrences = {}
    for ident, _ in rows:
        occurrences[ident] = occurrences.get(ident, 0) + 1
    problems = [label + ' missing in map: ' + ident for ident in expected if ident not in occurrences]
    for ident, count in occurrences.items():
        if count != 1:
            problems.append(label + ' duplicated in map: ' + ident)
        if ident not in expected:
            problems.append(label + ' invented id: ' + ident)
    return problems


def check_count(text, prefix, expected):
    lines = [line for line in text.splitlines() if line.startswith(prefix)]
    return ([] if lines == [expected] else
            [prefix + ' line must occur once and equal ' + expected])


def open_marker(gap):
    return any(marker in gap for marker in ('DECISION_REQUIRED · Astra', 'UNDETERMINED', '이 노드 밖'))


def owner_problems(ident, owner, contract_text):
    if not owner:
        return [ident + ': empty owner cell (use none)']
    return [ident + ': owner not in contract: ' + part.strip()
            for part in owner.split(';') if owner != 'none'
            and (not part.strip() or part.strip() not in contract_text)]


def section(text, number):
    match = re.search(r'^## ' + str(number) + r'\. [^\n]+\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    return match.group(1) if match else ''


def table_rows(text):
    return [split_row(line) for line in text.splitlines() if line.startswith('| ')
            and not all(re.fullmatch(r':?-+:?', c) for c in split_row(line))]


def false_flags(source):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FALSE_FLAGS'
                                               for t in node.targets):
            return ast.literal_eval(node.value)
    return ()


def contract_flags(text):
    match = re.search(r'다음 플래그는 항상 거짓이다[^\n]*\n\s*\n(.*?)(?:\n\s*\n|\Z)', section(text, 8), re.S)
    return re.findall(r'`([^`]+)`', match.group(1)) if match else []


def dlg_ids(text):
    return re.findall(r'^\|\s*(DLG-\d+)\s*\|', text, re.M)


def expand_dlg(pointer):
    if pointer == 'none':
        return []
    prefix = 'AI_DELEGATION_LAYER_MATRIX.md: '
    if not pointer.startswith(prefix):
        raise ValueError('DLG pointer format')
    ids = []
    for part in pointer[len(prefix):].split(', '):
        match = re.fullmatch(r'DLG-(\d{2})(?:\.\.DLG-(\d{2}))?', part)
        if not match:
            raise ValueError('DLG pointer format')
        start, end = int(match[1]), int(match[2] or match[1])
        if start > end or end > 99:
            raise ValueError('DLG pointer range')
        ids += ['DLG-%02d' % n for n in range(start, end + 1)]
    if len(ids) != len(set(ids)):
        raise ValueError('DLG pointer duplicate')
    return ids


def status_problems(ident, evidence, status, gap, owner=None):
    problems = []
    if status not in STATUSES:
        problems.append(ident + ': unknown status')
    if status in ('COVERED', 'PARTIAL') and not parse_cell(evidence):
        problems.append(ident + ': ' + status + ' needs a citation')
    if status == 'COVERED' and gap != 'none':
        problems.append(ident + ': COVERED gap must be none')
    if status == 'NOT_COVERED' and evidence != 'none':
        problems.append(ident + ': NOT_COVERED evidence must be none')
    if status in ('PARTIAL', 'NOT_COVERED') and (not gap or gap.lower() == 'none'):
        problems.append(ident + ': ' + status + ' needs a named gap')
    if status == 'OPEN':
        if not open_marker(gap):
            problems.append(ident + ': OPEN needs an open marker')
        if not owner or owner == 'none':
            problems.append(ident + ': OPEN needs an owner')
    return problems


def count_line(text, prefix, rows, status_column):
    counts = {s: sum(len(c) > status_column and c[status_column] == s for _, c in rows)
              for s in STATUSES}
    # Clause counts include zeros; the detail tables use compact nonzero counts.
    expected = prefix + ' ' + ' '.join('%s=%d' % (s, counts[s]) for s in STATUSES
                                      if prefix == 'Counts:' or counts[s])
    return check_count(text, prefix, expected)


def find_problems(map_text, contract_text, files=None):
    files = {} if files is None else files
    problems = []
    sources = {path: read_source(path, files) for path in (MATRIX, ECC, MOCK, ARCH)}
    if any(source is None for source in sources.values()):
        return ['required source missing or unreadable']
    headings = {'§' + n: t for n, t in HEADING.findall(contract_text)}
    if len(headings) != len(HEADING.findall(contract_text)):
        problems.append('duplicated contract heading')
    for n in range(11):
        if '§' + str(n) not in headings:
            problems.append('required contract heading missing: §' + str(n))
    for phrase in BANNERS:
        if phrase not in map_text:
            problems.append('banner phrase missing: ' + phrase)
    if not re.search(r'^delegated_execution_enabled = false\s*$', sources[ARCH], re.M):
        problems.append('execution must stay disabled')
    if re.search(r'^\|\s*DLG-', map_text, re.M):
        problems.append('copied DLG row is forbidden')
    predicates = dlg_ids(section(contract_text, 6))
    matrix_ids = dlg_ids(sources[MATRIX])
    if predicates != ['DLG-%02d' % n for n in range(1, 37)]:
        problems.append('contract must have 36 DLG predicates in order')
    items = {'O%d' % i: cells for i, cells in enumerate(table_rows(section(contract_text, 9))[1:], 1)}
    if len(items) != 8 or any(len(c) != 3 for c in items.values()):
        problems.append('contract must have 8 open items of 3 cells')
    owners = '; '.join(dict.fromkeys(c[2] for c in items.values() if len(c) == 3))
    symbols = {}
    rows = map_rows(map_text)
    problems += completeness(rows, headings, 'clause')
    for ident, cells in rows:
        if len(cells) != 8:
            problems.append(ident + ': expected 8 cells')
            continue
        _, title, para, evidence, pointer, status, gap, owner = cells
        if title != headings.get(ident):
            problems.append(ident + ': heading title drift')
        if not para or para == 'none':
            problems.append(ident + ': missing paraphrase')
        problems += status_problems(ident, evidence, status, gap, owner)
        problems += owner_problems(ident, owner, contract_text)
        if ident in MUST_BE_OPEN and status != 'OPEN':
            problems.append(ident + ': must remain OPEN')
        if ident in MUST_BE_NOT_COVERED and status != 'NOT_COVERED':
            problems.append(ident + ': must remain NOT_COVERED')
        if ident == '§9' and owner != owners:
            problems.append(ident + ': clause owner drift')
        try:
            refs = expand_dlg(pointer)
            if any(ref not in predicates or ref not in matrix_ids for ref in refs):
                problems.append(ident + ': unknown DLG id')
            if ident == '§6' and refs != predicates:
                problems.append('§6: must point to all DLG predicates in order')
        except ValueError as error:
            problems.append(ident + ': ' + str(error))
        problems += citation_problems(ident, evidence, files, symbols)
    problems += count_line(map_text, 'Counts:', rows, 5)

    codes = [ident for ident, _ in rows_matching(section(contract_text, 8), CODE_ROW)]
    code_rows = rows_matching(section(map_text, 3), CODE_ROW)
    if len(codes) != 26 or len(set(codes)) != 26:
        problems.append('contract must have 26 unique codes')
    problems += completeness(code_rows, codes, 'code')
    if [ident for ident, _ in code_rows] != codes:
        problems.append('code order must follow contract §8')
    for ident, cells in code_rows:
        if len(cells) != 5:
            problems.append(ident + ': expected 5 cells')
            continue
        _, evidence, coverage, status, gap = cells
        expected = 'excluded' if ident == 'MOCK_INVARIANT' else 'AID'
        if coverage != expected:
            problems.append(ident + ': coverage-map row must be ' + expected)
        if expected == 'AID' and not re.search(r'^\| AID \| `' + re.escape(ident) + r'` \|', sources[ECC], re.M):
            problems.append(ident + ': code missing from ECC')
        problems += status_problems(ident, evidence, status, gap)
        problems += citation_problems(ident, evidence, files, symbols)
    problems += count_line(map_text, 'Codes:', code_rows, 3)

    flags = contract_flags(contract_text)
    try:
        mock_flags = list(false_flags(sources[MOCK]))
    except (SyntaxError, ValueError, TypeError):
        mock_flags = []
    if len(flags) != 11 or len(set(flags)) != 11:
        problems.append('contract must have 11 unique flags')
    if flags != mock_flags:
        problems.append('flag drift against FALSE_FLAGS')
    flag_rows = rows_matching(section(map_text, 4), CODE_ROW)
    problems += completeness(flag_rows, flags, 'flag')
    if [ident for ident, _ in flag_rows] != flags:
        problems.append('flag order must follow contract §8')
    for ident, cells in flag_rows:
        if len(cells) != 4:
            problems.append(ident + ': expected 4 cells')
            continue
        _, evidence, status, gap = cells
        problems += status_problems(ident, evidence, status, gap)
        problems += citation_problems(ident, evidence, files, symbols)
    problems += count_line(map_text, 'Flags:', flag_rows, 2)

    item_rows = rows_matching(map_text, ITEM_ROW)
    problems += completeness(item_rows, items, 'item')
    if [ident for ident, _ in item_rows] != list(items):
        problems.append('item labels/order must follow contract §9')
    for ident, cells in item_rows:
        if len(cells) != 7:
            problems.append(ident + ': expected 7 cells')
            continue
        _, name, contract_status, evidence, status, gap, owner = cells
        expected = items.get(ident, [])
        for actual, want, label in zip((name, contract_status, owner), expected, ('title', 'status', 'owner')):
            if actual != want:
                problems.append(ident + ': item ' + label + ' drift')
        if status != 'OPEN':
            problems.append(ident + ': item must remain OPEN')
        if evidence != 'none':
            problems.append(ident + ': open-item evidence must be none')
        problems += status_problems(ident, evidence, status, gap, owner)
        if ident == 'O8' and 'delegated_execution_enabled = false' not in gap:
            problems.append('O8: execution-off posture missing')
        problems += citation_problems(ident, evidence, files, symbols)
    problems += check_count(map_text, 'Open items:', 'Open items: OPEN=%d' % len(items))
    return problems


def row_line(text, ident, pattern=ID_CELL):
    return next(line for line in text.splitlines()
                if pattern.match(line) and pattern.match(line).group(1) == ident)


def with_cell(text, ident, column, value, pattern=ID_CELL):
    line = row_line(text, ident, pattern)
    cells = split_row(line)
    cells[column] = value
    return text.replace(line, '| ' + ' | '.join(cells) + ' |', 1)
def self_test(map_text, contract_text):
    baseline = find_problems(map_text, contract_text)
    if baseline:
        print('self-test: unmodified map fails:\n' + '\n'.join(baseline), file=sys.stderr)
        return 1
    cases = []

    def add(name, marker, mutated=None, contract=None, files=None):
        cases.append((name, marker, map_text if mutated is None else mutated,
                      contract_text if contract is None else contract, files or {}))

    def cell(ident, column, value, pattern=ID_CELL):
        return with_cell(map_text, ident, column, value, pattern)

    path = TEST_DIRS[0] + '/test_ai_delegation_mock.py'
    symbol = 'AiDelegationMockTests.test_flags_remain_false'
    citation = '`' + path + '::' + symbol + '`'

    def cite(path_, symbol_=symbol):
        return cell('§3', 3, '`' + path_ + '::' + symbol_ + '`')

    for ident, pattern, label in [('§3', ID_CELL, 'clause'),
                                  ('AI_CANNOT_DECIDE', CODE_ROW, 'code'),
                                  ('execution_enabled', CODE_ROW, 'flag'),
                                  ('O1', ITEM_ROW, 'item')]:
        line = row_line(map_text, ident, pattern)
        invented = {'clause': '§99', 'code': 'INVENTED', 'flag': 'invented_flag', 'item': 'O99'}[label]
        add('missing ' + label, label + ' missing in map', map_text.replace(line + '\n', '', 1))
        add('duplicate ' + label, label + ' duplicated in map', map_text.replace(line, line + '\n' + line, 1))
        add('invented ' + label, label + ' invented id', map_text.replace(line, line + '\n' + line.replace(ident, invented, 1), 1))
        add(label + ' row width', 'expected %d cells' % len(split_row(line)), map_text.replace(line, line + ' extra |', 1))
        if label != 'clause':
            block = section(map_text, {'code': 3, 'flag': 4, 'item': 5}[label])
            moved = block.replace(line + '\n', '', 1) + line + '\n'
            marker = 'item labels/order' if label == 'item' else label + ' order'
            add(label + ' order', marker, map_text.replace(block, moved))
    add('new contract heading', 'clause missing in map: §11', contract=contract_text + '\n## 11. New\n')
    add('removed heading', 'required contract heading missing: §0', contract=contract_text.replace('## 0. ', '## ', 1))
    add('duplicate contract heading', 'duplicated contract heading', contract=contract_text + '\n## 0. Other\n')
    add('title drift', 'heading title drift', cell('§3', 1, 'wrong'))
    add('missing paraphrase', 'missing paraphrase', cell('§3', 2, 'none'))
    for name, target, marker in [
        ('dangling path', TEST_DIRS[0] + '/test_no_such_9f3a.py', 'cited file does not exist'),
        ('protected path', 'reference/v0.3-rc1/test_x.py', 'not an allowed test path'),
        ('absolute path', '/tmp/test_x.py', 'path must be repo-relative'),
        ('parent path', TEST_DIRS[0] + '/../test_x.py', 'path must be repo-relative'),
        ('backslash path', TEST_DIRS[0] + '\\test_x.py', 'path must be repo-relative'),
        ('noncanonical path', TEST_DIRS[0] + '/./test_x.py', 'path must be repo-relative'),
        ('nested path', TEST_DIRS[0] + '/nested/test_x.py', 'not an allowed test path'),
        ('non-test file', MOCK, 'not an allowed test path'),
        ('unapproved readiness file', 'readiness/test_other.py', 'not an allowed test path'),
    ]:
        add(name, marker, cite(target))
    for name, sym in [('dangling symbol', 'AiDelegationMockTests.test_no_such_9f3a'),
                      ('helper symbol', 'limits'), ('non-test method', 'AiDelegationMockTests.issue')]:
        add(name, 'symbol is missing or not a test', cite(path, sym))
    add('bare citation', 'malformed evidence', cell('§3', 3, path + '::' + symbol))
    add('ordinary class', 'symbol is missing or not a test', files={path: 'class AiDelegationMockTests:\n    def test_flags_remain_false(self): pass\n'})
    add('invalid Python', 'invalid Python', files={path: 'class ('})
    add('orphan readiness mixin', 'symbol is missing or not a test', files={'readiness/test_faults.py': 'class Helper: pass\n'})
    for prefix in ('Counts:', 'Codes:', 'Flags:', 'Open items:'):
        line = next(line for line in map_text.splitlines() if line.startswith(prefix))
        add('stale ' + prefix, prefix + ' line', map_text.replace(line, line + '0', 1))
        add('duplicate ' + prefix, prefix + ' line', map_text + line + '\n')
    add('closed §9', 'must remain OPEN', cell('§9', 5, 'COVERED'))
    add('promoted §10', 'must remain NOT_COVERED', cell('§10', 5, 'PARTIAL'))
    add('clause owner drift', 'clause owner drift', cell('§9', 7, 'Astra'))
    add('unknown owner', 'owner not in contract', cell('§3', 7, 'Nobody-9f3a'))
    add('empty owner', 'empty owner cell', cell('§3', 7, ''))
    add('missing owner', 'OPEN needs an owner', cell('§9', 7, 'none'))
    add('missing open marker', 'OPEN needs an open marker', cell('§9', 6, 'decided'))
    for ident, column, value, marker in [
        ('§3', 5, 'PASS', 'unknown status'),
        ('§1', 3, 'none', 'COVERED needs a citation'),
        ('§3', 3, 'none', 'PARTIAL needs a citation'),
        ('§1', 6, 'missing', 'COVERED gap must be none'),
        ('§3', 6, 'none', 'PARTIAL needs a named gap'),
        ('§10', 6, 'none', 'NOT_COVERED needs a named gap'),
        ('§10', 3, citation, 'NOT_COVERED evidence must be none'),
        ('§3', 4, 'AI_DELEGATION_LAYER_MATRIX.md: DLG-99', 'unknown DLG id'),
        ('§6', 4, 'AI_DELEGATION_LAYER_MATRIX.md: DLG-01..DLG-35', 'must point to all DLG'),
        ('§3', 4, 'DLG-03', 'DLG pointer format'),
        ('§3', 4, 'AI_DELEGATION_LAYER_MATRIX.md: DLG-03..DLG-01', 'DLG pointer range'),
        ('§3', 4, 'AI_DELEGATION_LAYER_MATRIX.md: DLG-03, DLG-03', 'DLG pointer duplicate'),
    ]:
        add(ident + ' ' + marker, marker, cell(ident, column, value))
    add('copied DLG row', 'copied DLG row', map_text + '\n| DLG-01 | copied |\n')
    add('missing matrix id', 'unknown DLG id', files={MATRIX: (ROOT / MATRIX).read_text().replace('| DLG-03 |', '| DLG-99 |')})
    add('code absent from ECC', 'code missing from ECC', files={ECC: (ROOT / ECC).read_text().replace('| AID | `AI_CANNOT_DECIDE` |', '| AID | `REMOVED` |')})
    add('constructor exclusion', 'coverage-map row must be excluded', cell('MOCK_INVARIANT', 2, 'AID', CODE_ROW))
    add('AID pointer drift', 'coverage-map row must be AID', cell('AI_CANNOT_DECIDE', 2, 'excluded', CODE_ROW))
    add('contract flag drift', 'flag missing in map', contract=contract_text.replace('`execution_enabled`,', '`changed_flag`,', 1))
    add('mock flag drift', 'flag drift against FALSE_FLAGS', files={MOCK: (ROOT / MOCK).read_text().replace('"execution_enabled",', '"changed_flag",', 1)})
    add('execution enabled', 'execution must stay disabled', files={ARCH: (ROOT / ARCH).read_text().replace('delegated_execution_enabled = false', 'delegated_execution_enabled = true')})
    for column, value, marker in [(1, 'wrong', 'item title drift'), (2, 'DECIDED', 'item status drift'),
                                   (3, citation, 'open-item evidence must be none'),
                                   (4, 'COVERED', 'item must remain OPEN'),
                                   (5, 'decided', 'OPEN needs an open marker'),
                                   (6, 'none', 'OPEN needs an owner')]:
        add('open item ' + marker, marker, cell('O1', column, value, ITEM_ROW))
    add('O8 owner drift', 'item owner drift', cell('O8', 6, 'Astra', ITEM_ROW))
    add('O8 execution posture', 'execution-off posture missing', cell('O8', 5, '이 노드 밖', ITEM_ROW))
    for phrase in BANNERS:
        add('missing banner ' + phrase, 'banner phrase missing', map_text.replace(phrase, ''))
    for name, marker, mutated, contract, files in cases:
        found = find_problems(mutated, contract, files)
        if not any(marker in problem for problem in found):
            print('self-test: failed to detect ' + name, file=sys.stderr)
            return 1
        print('self-test: detected ' + name)
    source = ('class Helper:\n    def test_x(self): pass\n'
              'class Base(unittest.TestCase): pass\n'
              'class Middle(Base): pass\n'
              'class Derived(Middle):\n    def test_y(self): pass\n'
              'class Plain(TestCase):\n    def test_z(self): pass\n'
              'class BackendConformance:\n    def test_bare(self): pass\n')
    if test_symbols(source) != {'Derived.test_y', 'Plain.test_z'}:
        print('self-test: transitive TestCase selection failed', file=sys.stderr)
        return 1
    # Exercise real on-disk symlink escape fencing without touching repo files.
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        (base / 'allowed').mkdir()
        (base / 'outside.py').write_text(source, encoding='utf-8')
        (base / 'allowed/link.py').symlink_to(base / 'outside.py')
        original = globals()['ROOT']
        try:
            globals()['ROOT'] = base
            if read_source('allowed/link.py', {}) is not None:
                print('self-test: symlink escape accepted', file=sys.stderr)
                return 1
        finally:
            globals()['ROOT'] = original
    print('self-test: transitive TestCase selection and symlink fencing pass')
    print('self-test: pass (%d negative controls)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_ai_delegation_evidence_map.py [--self-test]', file=sys.stderr)
        return 2
    try:
        map_text = (ROOT / MAP).read_text(encoding='utf-8')
        contract_text = (ROOT / CONTRACT).read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if argv:
        return self_test(map_text, contract_text)
    problems = find_problems(map_text, contract_text)
    if problems:
        print('ai delegation evidence map check failed:\n' + '\n'.join(problems), file=sys.stderr)
        return 1
    rows = map_rows(map_text)
    codes = rows_matching(section(map_text, 3), CODE_ROW)
    flags = rows_matching(section(map_text, 4), CODE_ROW)
    items = rows_matching(map_text, ITEM_ROW)
    citations = (sum(len(parse_cell(c[3])) for _, c in rows)
                 + sum(len(parse_cell(c[1])) for _, c in codes + flags))
    print('ai delegation evidence map ok: rows=%d headings=%d codes=%d flags=%d items=%d dlg_refs=%d citations=%d %s' % (
        len(rows), len(HEADING.findall(contract_text)), len(codes), len(flags), len(items),
        sum(len(expand_dlg(c[4])) for _, c in rows), citations,
        ' '.join('%s=%d' % (s, sum(c[5] == s for _, c in rows)) for s in STATUSES)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
