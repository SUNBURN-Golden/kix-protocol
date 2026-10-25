#!/usr/bin/env python3
"""Validate F04 credit heading/open-item completeness and test citations, without imports.

Standard library only; local-only (no workflow changes). This checks structure
and test existence, not semantic adequacy, independent review or acceptance.
Only direct test_* methods of explicit TestCase subclasses count; helpers,
inherited and dynamically installed methods deliberately do not. --self-test
first validates the real map, then uses in-memory mutations, including missing
clauses and dangling citations.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md'
CONTRACT = 'docs/contracts/CREDIT_ADVANCE_F04.md'
TEST_DIR = 'reference/credit_advance_f04'
TEST_GLOB = TEST_DIR + '/test_*.py'
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED', 'OPEN')
REQUIRED_SUBSET = ({str(n) for n in range(8)}
                   | {'5.%d' % n for n in range(1, 6)}
                   | {'7.%d' % n for n in range(1, 10)})
MUST_BE_OPEN = {'5', '5.1', '5.2'}
MUST_BE_NOT_COVERED = {'5.4'}
REQUIRED_ITEMS = {'legal-parties', 'interest-apr-schedule', 'seniority',
                  'perfection', 'limit-recalculation'}
BANNERS = ('Builder-authored map, not a review or an acceptance', 'no grade change')
HEADING = re.compile(r'^#{2,3} (\d+(?:\.\d+)?)\.? (.+)$', re.M)
ID_CELL = re.compile(r'^\|\s*§(\d+(?:\.\d+)?)\s*\|')
ITEM_ROW = re.compile(r'^\|\s*`([a-z0-9-]+)`\s*\|')
CITATION = re.compile(r'`([^`\n]+)::([^`\n]+)`')
EVIDENCE_CELL = re.compile(r'`[^`\n]+::[^`\n]+`(?:; `[^`\n]+::[^`\n]+`)*')


def split_row(line):
    return [cell.strip() for cell in line.strip().strip('|').split('|')]


def rows_matching(text, pattern):
    return [(match.group(1), split_row(line)) for line in text.splitlines()
            for match in [pattern.match(line)] if match]


def map_rows(text):
    return rows_matching(text, ID_CELL)


def open_item_block(text):
    match = re.search(r'^### 5\.2 [^\n]+\n(.*?)(?=^#{1,6} |\Z)', text, re.M | re.S)
    return match.group(1) if match else ''


def parse_cell(cell):
    return CITATION.findall(cell)


def test_symbols(source):
    """Read direct tests on explicit TestCase subclasses without executing code."""
    symbols = set()
    for node in ast.parse(source).body:
        if not isinstance(node, ast.ClassDef):
            continue
        case = any((isinstance(base, ast.Name) and base.id == 'TestCase') or
                   (isinstance(base, ast.Attribute) and base.attr == 'TestCase'
                    and isinstance(base.value, ast.Name) and base.value.id == 'unittest')
                   for base in node.bases)
        if case:
            symbols.update(node.name + '.' + method.name for method in node.body
                           if isinstance(method, ast.FunctionDef)
                           and method.name.startswith('test_'))
    return symbols


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
                or target.parent.as_posix() != TEST_DIR or not target.match(TEST_GLOB)):
            problems.append(ident + ': not an allowed test path: ' + path)
            continue
        if path not in symbols_by_path:
            if path in files:
                source = files[path]
            else:
                full = ROOT / path
                # Refuse symlinks resolving outside the allowed test subtree.
                try:
                    source = (full.read_text(encoding='utf-8')
                              if full.is_file() and full.resolve().is_relative_to(ROOT / TEST_DIR)
                              else None)
                except (OSError, UnicodeError, RuntimeError):
                    source = None
            if source is None:
                problems.append(ident + ': cited file does not exist: ' + path)
                symbols_by_path[path] = set()
            else:
                try:
                    symbols_by_path[path] = test_symbols(source)
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


def find_problems(map_text, contract_text, files=None):
    files = {} if files is None else files
    problems = []
    headings = {}
    for ident, title in HEADING.findall(contract_text):
        if ident in headings:
            problems.append('duplicated contract heading: ' + ident)
        headings[ident] = title
    for ident in sorted(REQUIRED_SUBSET - headings.keys()):
        problems.append('required contract heading missing: ' + ident)
    for phrase in BANNERS:
        if phrase not in map_text:
            problems.append('banner phrase missing: ' + phrase)
    rows = map_rows(map_text)
    problems += completeness(rows, headings, 'clause')
    counts = dict.fromkeys(STATUSES, 0)
    symbols_by_path = {}
    for ident, cells in rows:
        if len(cells) != 7:
            problems.append(ident + ': expected 7 cells')
            continue
        _, title, paraphrase, evidence, status, gap, owner = cells
        if title != headings.get(ident):
            problems.append(ident + ': heading title drift')
        if not paraphrase or paraphrase == 'none':
            problems.append(ident + ': missing paraphrase')
        if status not in STATUSES:
            problems.append(ident + ': unknown status ' + status)
        else:
            counts[status] += 1
        if status in ('COVERED', 'PARTIAL') and not parse_cell(evidence):
            problems.append(ident + ': ' + status + ' needs a citation')
        if status == 'COVERED' and gap != 'none':
            problems.append(ident + ': COVERED gap must be none')
        if status == 'NOT_COVERED' and evidence != 'none':
            problems.append(ident + ': NOT_COVERED evidence must be none')
        if status in ('PARTIAL', 'NOT_COVERED') and (not gap or gap.lower() == 'none'):
            problems.append(ident + ': ' + status + ' needs a named gap')
        if ident in MUST_BE_OPEN and status != 'OPEN':
            problems.append(ident + ': must remain OPEN')
        if ident in MUST_BE_NOT_COVERED and status != 'NOT_COVERED':
            problems.append(ident + ': must remain NOT_COVERED')
        if status == 'OPEN':
            if 'UNDETERMINED' not in gap:
                problems.append(ident + ': OPEN needs UNDETERMINED')
            if not owner or owner == 'none':
                problems.append(ident + ': OPEN needs an owner')
        if not owner:
            problems.append(ident + ': empty owner cell (use none)')
        elif owner != 'none':
            for part in owner.split(';'):
                if not part.strip() or part.strip() not in contract_text:
                    problems.append(ident + ': owner not in contract: ' + part.strip())
        problems += citation_problems(ident, evidence, files, symbols_by_path)
    expected = 'Counts: ' + ' '.join('%s=%d' % (s, counts[s]) for s in STATUSES)
    problems += check_count(map_text, 'Counts:', expected)

    block = open_item_block(contract_text)
    contract_items = rows_matching(block, ITEM_ROW)
    item_ids = {ident for ident, _ in contract_items}
    if not item_ids:
        problems.append('contract has no §5.2 open items')
    if len(item_ids) != len(contract_items):
        problems.append('duplicated contract open item')
    for ident in sorted(REQUIRED_ITEMS - item_ids):
        problems.append('required contract item missing: ' + ident)
    item_rows = rows_matching(map_text, ITEM_ROW)
    problems += completeness(item_rows, item_ids, 'item')
    # Extract the entire verbatim owner after the contract's named-owner marker.
    owners = {}
    for ident, cells in contract_items:
        if len(cells) != 5:
            problems.append(ident + ': contract item expected 5 cells')
            continue
        if cells[2] != 'A' or cells[3] != '`UNDETERMINED`':
            problems.append(ident + ': contract item must keep A and UNDETERMINED')
        owners[ident] = cells[-1].partition('담당은 ')[2]
    for ident, cells in rows:
        if ident in MUST_BE_OPEN and len(cells) == 7:
            expected_owners = {'Astra'} if ident == '5' else set(owners.values())
            if set(cells[6].split('; ')) != expected_owners:
                problems.append(ident + ': clause owner drift')
    for ident, cells in item_rows:
        if len(cells) != 6:
            problems.append(ident + ': expected 6 cells')
            continue
        _, adopted, evidence, status, gap, owner = cells
        if adopted != 'A':
            problems.append(ident + ': adopted must be A')
        if status != 'OPEN':
            problems.append(ident + ': item must remain OPEN')
        if 'UNDETERMINED' not in gap:
            problems.append(ident + ': OPEN needs UNDETERMINED')
        if not owner or owner == 'none':
            problems.append(ident + ': OPEN needs an owner')
        if owner != owners.get(ident):
            problems.append(ident + ': item owner drift from §5.2')
        for part in owner.split(';'):
            if not part.strip() or part.strip() not in block:
                problems.append(ident + ': owner not in §5.2: ' + part.strip())
        problems += citation_problems(ident, evidence, files, symbols_by_path)
    problems += check_count(map_text, 'Open items:', 'Open items: OPEN=%d' % len(item_ids))
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
    row = row_line(map_text, '7.8')
    fsm = TEST_DIR + '/test_credit_fsm.py'
    atomicity = TEST_DIR + '/test_credit_rejection_atomicity.py'
    item = 'legal-parties'
    item_line = row_line(map_text, item, ITEM_ROW)
    counts = next(line for line in map_text.splitlines() if line.startswith('Counts:'))

    def cell(ident, column, value):
        return with_cell(map_text, ident, column, value)

    def item_cell(column, value):
        return with_cell(map_text, item, column, value, ITEM_ROW)

    def cite(path, symbol):
        return cell('7.8', 3, '`' + path + '::' + symbol + '`')

    cases = [
        ('missing clause', map_text.replace(row + '\n', '', 1), contract_text, {}, 'missing in map: 7.8'),
        ('new contract heading', map_text, contract_text + '\n### 7.10 X\n', {}, 'missing in map: 7.10'),
        ('removed required heading', map_text, contract_text.replace('### 7.8 이 기계가 더하는 코드', '### 이 기계가 더하는 코드'), {}, 'required contract heading missing: 7.8'),
        ('duplicate heading', map_text, contract_text + '\n### 7.8 X\n', {}, 'duplicated contract heading'),
        ('duplicate row', map_text + row + '\n', contract_text, {}, 'duplicated in map'),
        ('invented row', map_text + row.replace('§7.8', '§12', 1) + '\n', contract_text, {}, 'invented id: 12'),
        ('dangling path', cite(TEST_DIR + '/test_no_such_9f3a.py', 'A.test_x'), contract_text, {}, 'cited file does not exist'),
        ('dangling symbol', cite(fsm, 'CreditFsmTests.test_no_such_9f3a'), contract_text, {}, 'symbol is missing or not a test'),
        ('helper symbol', cite(atomicity, 'StubView.view'), contract_text, {}, 'symbol is missing or not a test'),
        ('non-test method', cite(atomicity, 'CreditRejectionAtomicityTests.offer_adv'), contract_text, {}, 'symbol is missing or not a test'),
        ('protected path', cite('reference/v0.3-rc1/test_x.py', 'A.test_x'), contract_text, {}, 'not an allowed test path'),
        ('absolute path', cite('/tmp/test_x.py', 'A.test_x'), contract_text, {}, 'path must be repo-relative'),
        ('parent path', cite(TEST_DIR + '/../test_x.py', 'A.test_x'), contract_text, {}, 'path must be repo-relative'),
        ('backslash path', cite(TEST_DIR + '\\test_x.py', 'A.test_x'), contract_text, {}, 'path must be repo-relative'),
        ('closed open clause', cell('5.1', 4, 'COVERED'), contract_text, {}, 'must remain OPEN'),
        ('closed options', cell('5.2', 4, 'COVERED'), contract_text, {}, 'must remain OPEN'),
        ('closed policy clause', cell('5', 4, 'COVERED'), contract_text, {}, 'must remain OPEN'),
        ('promoted real gaps', cell('5.4', 4, 'COVERED'), contract_text, {}, 'must remain NOT_COVERED'),
        ('unknown owner', cell('5.1', 6, 'Nobody-9f3a'), contract_text, {}, 'owner not in contract'),
        ('incomplete owners', cell('5.1', 6, 'Astra'), contract_text, {}, 'clause owner drift'),
        ('missing owner', cell('5.1', 6, 'none'), contract_text, {}, 'OPEN needs an owner'),
        ('empty owner', cell('5.1', 6, ''), contract_text, {}, 'empty owner cell'),
        ('missing UNDETERMINED', cell('5.1', 5, 'decided'), contract_text, {}, 'OPEN needs UNDETERMINED'),
        ('open item missing', map_text.replace(item_line + '\n', '', 1), contract_text, {}, 'item missing in map'),
        ('open item invented', map_text + item_line.replace(item, 'invented-9f3a', 1) + '\n', contract_text, {}, 'item invented id'),
        ('open item duplicate', map_text + item_line + '\n', contract_text, {}, 'item duplicated in map'),
        ('open item adopted', item_cell(1, 'B'), contract_text, {}, 'adopted must be A'),
        ('open item status', item_cell(3, 'COVERED'), contract_text, {}, 'item must remain OPEN'),
        ('open item owner drift', item_cell(5, '사용자와 세무·회계 담당'), contract_text, {}, 'item owner drift'),
        ('open item shortened owner', item_cell(5, '사용자'), contract_text, {}, 'item owner drift'),
        ('open item missing owner', item_cell(5, 'none'), contract_text, {}, 'OPEN needs an owner'),
        ('open item missing UNDETERMINED', item_cell(4, 'decided'), contract_text, {}, 'OPEN needs UNDETERMINED'),
        ('open item row width', map_text.replace(item_line, item_line + ' extra |', 1), contract_text, {}, 'expected 6 cells'),
        ('open item dangling citation', item_cell(2, '`' + fsm + '::A.test_x`'), contract_text, {}, 'symbol is missing or not a test'),
        ('title drift', cell('7.8', 1, 'wrong title'), contract_text, {}, 'heading title drift'),
        ('row width', map_text.replace(row, row + ' extra |', 1), contract_text, {}, 'expected 7 cells'),
        ('unknown status', cell('7.8', 4, 'PASS'), contract_text, {}, 'unknown status'),
        ('missing paraphrase', cell('7.8', 2, 'none'), contract_text, {}, 'missing paraphrase'),
        ('uncited COVERED', cell('2', 3, 'none'), contract_text, {}, 'COVERED needs a citation'),
        ('uncited PARTIAL', cell('6', 3, 'none'), contract_text, {}, 'PARTIAL needs a citation'),
        ('COVERED gap', cell('2', 5, 'missing'), contract_text, {}, 'COVERED gap must be none'),
        ('PARTIAL missing gap', cell('6', 5, 'none'), contract_text, {}, 'PARTIAL needs a named gap'),
        ('NOT_COVERED missing gap', cell('5.4', 5, 'none'), contract_text, {}, 'NOT_COVERED needs a named gap'),
        ('NOT_COVERED citation', cell('5.4', 3, '`' + fsm + '::CreditFsmTests.test_offer_approve_draw_repay_and_close_are_mock_ledger_only`'), contract_text, {}, 'NOT_COVERED evidence must be none'),
        ('bare citation', cell('7.8', 3, fsm + '::CreditFsmTests.test_offer_approve_draw_repay_and_close_are_mock_ledger_only'), contract_text, {}, 'malformed evidence'),
        ('stale counts', map_text.replace(counts, counts + '0', 1), contract_text, {}, 'Counts: line'),
        ('duplicate counts', map_text + counts + '\n', contract_text, {}, 'Counts: line'),
        ('stale open-items count', map_text.replace('Open items: OPEN=5', 'Open items: OPEN=4'), contract_text, {}, 'Open items: line'),
        ('duplicate open-items count', map_text + 'Open items: OPEN=5\n', contract_text, {}, 'Open items: line'),
        ('missing banner', map_text.replace(BANNERS[0], '', 1), contract_text, {}, 'banner phrase missing'),
        ('missing grade banner', map_text.replace(BANNERS[1], '', 1), contract_text, {}, 'banner phrase missing'),
        ('both banners missing', map_text.replace(BANNERS[0], '').replace(BANNERS[1], ''), contract_text, {}, 'banner phrase missing'),
        ('contract policy drift', map_text, contract_text.replace('| A | `UNDETERMINED` |', '| B | `UNDETERMINED` |', 1), {}, 'contract item must keep A'),
        ('ordinary class', map_text, contract_text, {fsm: 'class CreditFsmTests:\n    def test_offer_approve_draw_repay_and_close_are_mock_ledger_only(self): pass\n'}, 'symbol is missing or not a test'),
        ('invalid Python', map_text, contract_text, {fsm: 'class ('}, 'invalid Python'),
    ]
    for name, mutated, contract, files, marker in cases:
        found = find_problems(mutated, contract, files)
        if not any(marker in problem for problem in found):
            print('self-test: failed to detect ' + name, file=sys.stderr)
            return 1
        print('self-test: detected ' + name)
    source = ('class Helper:\n    def test_fake(self): pass\n'
              'class Base(unittest.TestCase):\n    def test_direct(self): pass\n'
              '    def helper(self): pass\n'
              'class Derived(Base):\n    def test_inherited_case(self): pass\n'
              'class Plain(TestCase):\n    def test_direct(self): pass\n')
    if test_symbols(source) != {'Base.test_direct', 'Plain.test_direct'}:
        print('self-test: direct TestCase selection failed', file=sys.stderr)
        return 1
    print('self-test: direct TestCase selection pass')
    print('self-test: pass (%d negative controls)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_credit_evidence_map.py [--self-test]', file=sys.stderr)
        return 2
    try:
        map_text = (ROOT / MAP).read_text(encoding='utf-8')
        contract_text = (ROOT / CONTRACT).read_text(encoding='utf-8')
    except OSError as error:
        print(str(error), file=sys.stderr)
        return 1
    if argv:
        return self_test(map_text, contract_text)
    problems = find_problems(map_text, contract_text)
    if problems:
        print('credit evidence map check failed:\n' + '\n'.join(problems), file=sys.stderr)
        return 1
    rows = map_rows(map_text)
    items = rows_matching(map_text, ITEM_ROW)
    counts = {s: sum(cells[4] == s for _, cells in rows) for s in STATUSES}
    print('credit evidence map ok: rows=%d headings=%d items=%d citations=%d %s' % (
        len(rows), len(HEADING.findall(contract_text)), len(items),
        sum(len(parse_cell(cells[3])) for _, cells in rows)
        + sum(len(parse_cell(cells[2])) for _, cells in items),
        ' '.join('%s=%d' % (s, counts[s]) for s in STATUSES)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
