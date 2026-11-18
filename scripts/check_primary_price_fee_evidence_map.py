#!/usr/bin/env python3
"""Check primary price/fee clause, chain and open-item evidence using only stdlib.

Modelled on check_credit_evidence_map.py. No imports of cited tests, no frozen
reference reads. Only direct test_* methods on explicit TestCase subclasses
count. Structural coverage and symbol existence do not establish semantic
adequacy, independent review or acceptance. --self-test validates the real map
then requires in-memory negative controls to fail for their intended reason.
PF-C05 permits Python-only PARTIAL evidence; the chain baseline has 3 rows.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/PRIMARY_PRICE_FEE_CONTRACT_EVIDENCE_MAP.md'
CONTRACT = 'docs/contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md'
TEST_DIRS = ('reference/settlement_f01_f03', 'reference/booking_resale_admission')
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED', 'OPEN')
REQUIRED_HEADINGS = {str(n) for n in range(9)}
REQUIRED_PFC = {'PF-C%02d' % n for n in range(1, 6)}
MUST_BE_OPEN = {'§4', '§6', 'PF-C03'}
MUST_BE_UNCOVERED = {'PF-C03', 'PF-C04'}
PYTHON_ONLY = {'PF-C05'}
MUST_BE_NOT_COVERED_CHAIN = {'PF-C01', 'PF-C02', 'PF-C05'}
BANNERS = ('Builder-authored map, not a review or an acceptance', 'no grade change')
# Accept future numeric ids for detection of drift/invented rows, not authorization.
HEADING = re.compile(r'^## (\d+)\. (.+)$', re.M)
PFC_HEADING = re.compile(r'^### (PF-C\d{2}) (.+)$', re.M)
ID_CELL = re.compile(r'^\|\s*(§\d+|PF-C\d{2})\s*\|')
CHAIN_ROW = re.compile(r'^\|\s*chain:(PF-C\d{2})\s*\|')
ITEM_ROW = re.compile(r'^\|\s*(O\d+)\s*\|')
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
    match = re.search(r'^## 6\. [^\n]+\n(.*?)(?=^## |\Z)', text, re.M | re.S)
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
                or target.parent.as_posix() not in TEST_DIRS
                or not target.match('test_*.py')):
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
                              if full.is_file() and full.resolve().is_relative_to(
                                  ROOT / target.parent)
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


def open_marker(gap):
    return 'DECISION_REQUIRED · Astra' in gap or 'UNDETERMINED' in gap


def owner_problems(ident, owner, contract_text):
    if not owner:
        return [ident + ': empty owner cell (use none)']
    return [ident + ': owner not in contract: ' + part.strip()
            for part in owner.split(';') if owner != 'none'
            and (not part.strip() or part.strip() not in contract_text)]


def find_problems(map_text, contract_text, files=None):
    files = {} if files is None else files
    problems = []
    numbered = HEADING.findall(contract_text)
    predicates = PFC_HEADING.findall(contract_text)
    headings = {}
    for ident, title in [('§' + n, t) for n, t in numbered] + predicates:
        if ident in headings:
            problems.append('duplicated contract heading: ' + ident)
        headings[ident] = title
    required = {'§' + n for n in REQUIRED_HEADINGS} | REQUIRED_PFC
    for ident in sorted(required - headings.keys()):
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
        if ident in MUST_BE_UNCOVERED:
            if status not in ('NOT_COVERED', 'OPEN'):
                problems.append(ident + ': must remain NOT_COVERED or OPEN')
            if owner != 'Astra' or 'DECISION_REQUIRED · Astra' not in gap:
                problems.append(ident + ': must retain DECISION_REQUIRED · Astra and owner Astra')
        if ident in PYTHON_ONLY:
            if status not in ('PARTIAL', 'NOT_COVERED'):
                problems.append(ident + ': must remain PARTIAL or NOT_COVERED')
            if owner != 'Astra' or 'DECISION_REQUIRED · Astra' not in gap:
                problems.append(ident + ': must retain DECISION_REQUIRED · Astra and owner Astra')
        if status == 'OPEN':
            if not open_marker(gap):
                problems.append(ident + ': OPEN needs DECISION_REQUIRED · Astra or UNDETERMINED')
            if not owner or owner == 'none':
                problems.append(ident + ': OPEN needs an owner')
        expected_owners = {'§0': 'Astra', '§4': 'Astra',
                           '§6': 'Astra; 사용자, 법률·회계 담당; 토스, 사용자'}
        if ident in expected_owners and owner != expected_owners[ident]:
            problems.append(ident + ': clause owner drift')
        problems += owner_problems(ident, owner, contract_text)
        problems += citation_problems(ident, evidence, files, symbols_by_path)
    problems += check_count(map_text, 'Counts:', 'Counts: ' + ' '.join(
        '%s=%d' % (s, counts[s]) for s in STATUSES))

    chain_rows = rows_matching(map_text, CHAIN_ROW)
    problems += completeness(chain_rows, MUST_BE_NOT_COVERED_CHAIN, 'chain')
    for ident, cells in chain_rows:
        if len(cells) != 5:
            problems.append('chain:' + ident + ': expected 5 cells')
            continue
        _, evidence, status, gap, owner = cells
        if status != 'NOT_COVERED':
            problems.append('chain:' + ident + ': must remain NOT_COVERED')
        if evidence != 'none':
            problems.append('chain:' + ident + ': evidence must be none')
        if 'DECISION_REQUIRED · Astra' not in gap or owner != 'Astra':
            problems.append('chain:' + ident + ': must retain DECISION_REQUIRED · Astra and owner Astra')
        problems += citation_problems('chain:' + ident, evidence, files, symbols_by_path)
    problems += check_count(map_text, 'On-chain:', 'On-chain: NOT_COVERED=%d' % len(chain_rows))

    block = open_item_block(contract_text)
    contract_items = []
    for line in block.splitlines():
        if not line.startswith('|'):
            continue
        cells = split_row(line)
        if cells[0] == '항목' or all(re.fullmatch(r':?-+:?', c) for c in cells):
            continue
        if len(cells) != 3:
            problems.append('contract open item expected 3 cells')
            continue
        contract_items.append(cells)
    if len(contract_items) != 9:
        problems.append('contract must have 9 §6 open items')
    items = {'O%d' % i: (name.partition('. ')[0].rstrip('.'), status, owner)
             for i, (name, status, owner) in enumerate(contract_items, 1)}
    item_rows = rows_matching(map_text, ITEM_ROW)
    problems += completeness(item_rows, items, 'item')
    if [ident for ident, _ in item_rows] != list(items):
        problems.append('item labels/order must follow contract §6')
    for ident, cells in item_rows:
        if len(cells) != 7:
            problems.append(ident + ': expected 7 cells')
            continue
        _, name, contract_status, evidence, status, gap, owner = cells
        expected = items.get(ident)
        if expected:
            if name != expected[0]:
                problems.append(ident + ': item title drift from §6')
            if contract_status != expected[1]:
                problems.append(ident + ': contract status drift from §6')
            if owner != expected[2]:
                problems.append(ident + ': item owner drift from §6')
        if status != 'OPEN':
            problems.append(ident + ': item must remain OPEN')
        if evidence != 'none':
            problems.append(ident + ': open-item evidence must be none')
        if not open_marker(gap):
            problems.append(ident + ': OPEN needs DECISION_REQUIRED · Astra or UNDETERMINED')
        if not owner or owner == 'none':
            problems.append(ident + ': OPEN needs an owner')
        problems += owner_problems(ident, owner, block)
        problems += citation_problems(ident, evidence, files, symbols_by_path)
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
    row = row_line(map_text, 'PF-C01')
    item_line = row_line(map_text, 'O1', ITEM_ROW)
    chain_line = row_line(map_text, 'PF-C01', CHAIN_ROW)
    counts = next(line for line in map_text.splitlines() if line.startswith('Counts:'))
    price = TEST_DIRS[1] + '/test_primary_price_binding.py'
    symbol = 'PrimaryPriceBindingPfC01Tests.test_seeded_prices'
    citation = '`' + price + '::' + symbol + '`'

    def cell(ident, column, value):
        return with_cell(map_text, ident, column, value)

    def chain_cell(column, value):
        return with_cell(map_text, 'PF-C01', column, value, CHAIN_ROW)

    def item_cell(column, value):
        return with_cell(map_text, 'O1', column, value, ITEM_ROW)

    def cite(path, name):
        return cell('PF-C01', 3, '`' + path + '::' + name + '`')

    cases = [
        ('missing clause', map_text.replace(row + '\n', '', 1), contract_text, {}, 'clause missing in map: PF-C01'),
        ('duplicate clause', map_text + row + '\n', contract_text, {}, 'clause duplicated in map'),
        ('invented clause', map_text + row.replace('PF-C01', '§10', 1) + '\n', contract_text, {}, 'clause invented id: §10'),
        ('new contract heading', map_text, contract_text + '\n## 9. New\n', {}, 'clause missing in map: §9'),
        ('removed PF-C heading', map_text, contract_text.replace('### PF-C01 ', '### ', 1), {}, 'required contract heading missing: PF-C01'),
        ('removed numbered heading', map_text, contract_text.replace('## 0. ', '## ', 1), {}, 'required contract heading missing: §0'),
        ('duplicate contract heading', map_text, contract_text + '\n### PF-C01 New\n', {}, 'duplicated contract heading'),
        ('title drift', cell('PF-C01', 1, 'wrong'), contract_text, {}, 'heading title drift'),
        ('dangling path', cite(TEST_DIRS[1] + '/test_no_such_9f3a.py', 'A.test_x'), contract_text, {}, 'cited file does not exist'),
        ('dangling symbol', cite(price, 'PrimaryPriceBindingPfC01Tests.test_no_such_9f3a'), contract_text, {}, 'symbol is missing or not a test'),
        ('helper symbol', cite(price, 'code_of'), contract_text, {}, 'symbol is missing or not a test'),
        ('non-test method', cite(price, 'PrimaryPriceBindingPfC01Tests.open_show'), contract_text, {}, 'symbol is missing or not a test'),
        ('protected path', cite('reference/v0.3-rc1/test_x.py', 'A.test_x'), contract_text, {}, 'not an allowed test path'),
        ('absolute path', cite('/tmp/test_x.py', 'A.test_x'), contract_text, {}, 'path must be repo-relative'),
        ('parent path', cite(TEST_DIRS[1] + '/../test_x.py', 'A.test_x'), contract_text, {}, 'path must be repo-relative'),
        ('backslash path', cite(TEST_DIRS[1] + '\\test_x.py', 'A.test_x'), contract_text, {}, 'path must be repo-relative'),
        ('noncanonical path', cite(TEST_DIRS[1] + '/./test_primary_price_binding.py', symbol), contract_text, {}, 'path must be repo-relative'),
        ('nested path', cite(TEST_DIRS[1] + '/nested/test_x.py', 'A.test_x'), contract_text, {}, 'not an allowed test path'),
        ('non-test file', cite(TEST_DIRS[1] + '/mock_gates.py', 'A.test_x'), contract_text, {}, 'not an allowed test path'),
        ('bare citation', cell('PF-C01', 3, price + '::' + symbol), contract_text, {}, 'malformed evidence'),
        ('stale counts', map_text.replace(counts, counts + '0', 1), contract_text, {}, 'Counts: line'),
        ('duplicate counts', map_text + counts + '\n', contract_text, {}, 'Counts: line'),
        ('closed PF-C03', cell('PF-C03', 4, 'COVERED'), contract_text, {}, 'must remain OPEN'),
        ('closed §4', cell('§4', 4, 'COVERED'), contract_text, {}, 'must remain OPEN'),
        ('closed §6', cell('§6', 4, 'COVERED'), contract_text, {}, 'must remain OPEN'),
        ('promoted PF-C04', cell('PF-C04', 4, 'PARTIAL'), contract_text, {}, 'must remain NOT_COVERED or OPEN'),
        ('promoted PF-C05', cell('PF-C05', 4, 'COVERED'), contract_text, {}, 'must remain PARTIAL or NOT_COVERED'),
        ('PF-C05 opened', cell('PF-C05', 4, 'OPEN'), contract_text, {}, 'must remain PARTIAL or NOT_COVERED'),
        ('PF-C05 owner drift', cell('PF-C05', 6, '사용자'), contract_text, {}, 'must retain DECISION_REQUIRED · Astra'),
        ('PF-C05 missing marker', cell('PF-C05', 5, 'On-chain not executed'), contract_text, {}, 'must retain DECISION_REQUIRED · Astra'),
        ('PF-C owner drift', cell('PF-C04', 6, '사용자'), contract_text, {}, 'must retain DECISION_REQUIRED · Astra'),
        ('unknown owner', cell('§2', 6, 'Nobody-9f3a'), contract_text, {}, 'owner not in contract'),
        ('clause owner drift', cell('§6', 6, 'Astra'), contract_text, {}, 'clause owner drift'),
        ('missing owner', cell('§4', 6, 'none'), contract_text, {}, 'OPEN needs an owner'),
        ('empty owner', cell('§2', 6, ''), contract_text, {}, 'empty owner cell'),
        ('missing open marker', cell('§6', 5, 'decided'), contract_text, {}, 'OPEN needs DECISION_REQUIRED'),
        ('closed chain row', chain_cell(2, 'COVERED'), contract_text, {}, 'must remain NOT_COVERED'),
        ('cited chain row', chain_cell(1, citation), contract_text, {}, 'evidence must be none'),
        ('missing chain row', map_text.replace(chain_line + '\n', '', 1), contract_text, {}, 'chain missing in map'),
        ('missing chain PF-C05', map_text.replace(row_line(map_text, 'PF-C05', CHAIN_ROW) + '\n', '', 1), contract_text, {}, 'chain missing in map: PF-C05'),
        ('duplicate chain row', map_text + chain_line + '\n', contract_text, {}, 'chain duplicated in map'),
        ('invented chain row', map_text + chain_line.replace('PF-C01', 'PF-C03', 1) + '\n', contract_text, {}, 'chain invented id'),
        ('chain owner drift', chain_cell(4, '사용자'), contract_text, {}, 'must retain DECISION_REQUIRED · Astra'),
        ('chain missing marker', chain_cell(3, 'none'), contract_text, {}, 'must retain DECISION_REQUIRED · Astra'),
        ('chain row width', map_text.replace(chain_line, chain_line + ' extra |', 1), contract_text, {}, 'expected 5 cells'),
        ('stale chain count', map_text.replace('On-chain: NOT_COVERED=3', 'On-chain: NOT_COVERED=2'), contract_text, {}, 'On-chain: line'),
        ('duplicate chain count', map_text + 'On-chain: NOT_COVERED=3\n', contract_text, {}, 'On-chain: line'),
        ('open item owner drift', item_cell(6, '사용자'), contract_text, {}, 'item owner drift'),
        ('open item shortened owner', with_cell(map_text, 'O4', 6, 'Astra', ITEM_ROW), contract_text, {}, 'item owner drift'),
        ('open item status drift', item_cell(4, 'COVERED'), contract_text, {}, 'item must remain OPEN'),
        ('contract status drift', item_cell(2, '`DECIDED`'), contract_text, {}, 'contract status drift'),
        ('open item title drift', item_cell(1, 'wrong'), contract_text, {}, 'item title drift'),
        ('missing open item', map_text.replace(item_line + '\n', '', 1), contract_text, {}, 'item missing in map'),
        ('duplicate open item', map_text + item_line + '\n', contract_text, {}, 'item duplicated in map'),
        ('invented open item', map_text + item_line.replace('O1', 'O10', 1) + '\n', contract_text, {}, 'item invented id'),
        ('O-label order drift', map_text.replace(item_line + '\n', '', 1) + item_line + '\n', contract_text, {}, 'item labels/order'),
        ('open item missing marker', item_cell(5, 'decided'), contract_text, {}, 'OPEN needs DECISION_REQUIRED'),
        ('open item missing owner', item_cell(6, 'none'), contract_text, {}, 'OPEN needs an owner'),
        ('cited open item', item_cell(3, citation), contract_text, {}, 'open-item evidence must be none'),
        ('open item row width', map_text.replace(item_line, item_line + ' extra |', 1), contract_text, {}, 'expected 7 cells'),
        ('stale open count', map_text.replace('Open items: OPEN=9', 'Open items: OPEN=8'), contract_text, {}, 'Open items: line'),
        ('duplicate open count', map_text + 'Open items: OPEN=9\n', contract_text, {}, 'Open items: line'),
        ('missing contract open item', map_text, contract_text.replace(next(line for line in open_item_block(contract_text).splitlines() if line.startswith('| `primary_price`')), ''), {}, 'contract must have 9'),
        ('row width', map_text.replace(row, row + ' extra |', 1), contract_text, {}, 'expected 7 cells'),
        ('unknown status', cell('PF-C01', 4, 'PASS'), contract_text, {}, 'unknown status'),
        ('missing paraphrase', cell('PF-C01', 2, 'none'), contract_text, {}, 'missing paraphrase'),
        ('uncited COVERED', cell('§5', 3, 'none'), contract_text, {}, 'COVERED needs a citation'),
        ('uncited PARTIAL', cell('PF-C01', 3, 'none'), contract_text, {}, 'PARTIAL needs a citation'),
        ('COVERED gap', cell('§5', 5, 'missing'), contract_text, {}, 'COVERED gap must be none'),
        ('PARTIAL missing gap', cell('PF-C01', 5, 'none'), contract_text, {}, 'PARTIAL needs a named gap'),
        ('NOT_COVERED missing gap', cell('§8', 5, 'none'), contract_text, {}, 'NOT_COVERED needs a named gap'),
        ('NOT_COVERED citation', cell('§8', 3, citation), contract_text, {}, 'NOT_COVERED evidence must be none'),
        ('missing banner', map_text.replace(BANNERS[0], '', 1), contract_text, {}, 'banner phrase missing'),
        ('missing grade banner', map_text.replace(BANNERS[1], '', 1), contract_text, {}, 'banner phrase missing'),
        ('ordinary class', map_text, contract_text, {price: 'class PrimaryPriceBindingPfC01Tests:\n    def test_seeded_prices(self): pass\n'}, 'symbol is missing or not a test'),
        ('invalid Python', map_text, contract_text, {price: 'class ('}, 'invalid Python'),
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
        print('usage: check_primary_price_fee_evidence_map.py [--self-test]', file=sys.stderr)
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
        print('primary price fee evidence map check failed:\n' + '\n'.join(problems), file=sys.stderr)
        return 1
    rows = map_rows(map_text)
    chain = rows_matching(map_text, CHAIN_ROW)
    items = rows_matching(map_text, ITEM_ROW)
    counts = {s: sum(cells[4] == s for _, cells in rows) for s in STATUSES}
    print('primary price fee evidence map ok: rows=%d headings=%d chain=%d items=%d citations=%d %s' % (
        len(rows), len(HEADING.findall(contract_text)) + len(PFC_HEADING.findall(contract_text)),
        len(chain), len(items), sum(len(parse_cell(cells[3])) for _, cells in rows),
        ' '.join('%s=%d' % (s, counts[s]) for s in STATUSES)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
