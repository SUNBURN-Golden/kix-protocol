#!/usr/bin/env python3
"""Validate settlement clause coverage and test citations without executing tests.

Standard library only. --self-test requires the real map to pass, then checks
in-memory negative controls, including missing clauses and dangling citations.
This checks document structure and test existence, not semantic coverage or
independent review. It is local-only; no workflow is modified by this node.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md'
CONTRACT = 'docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md'
TEST_GLOB = 'reference/settlement_f01_f03/test_*.py'
CROSS_SUITE_CITATIONS = {'9.6': frozenset({
    'reference/credit_advance_f04/test_mock_credit.py',
})}
STATUSES = ('COVERED', 'PARTIAL', 'NOT_COVERED', 'OPEN')
REQUIRED_SUBSET = ({'0.1', '0.2', '0.3'} | {str(n) for n in range(1, 6)}
                   | {'7.%d' % n for n in range(1, 9)}
                   | {'9.%d' % n for n in range(1, 7)})
MUST_BE_OPEN = {'0.3'} | {'7.%d' % n for n in range(1, 8)}
BANNERS = ('Builder-authored map, not a review or an acceptance', 'no grade change')
HEADING = re.compile(r'^#{2,3} (\d+(?:\.\d+)?)\.? (.+)$', re.M)
ID_CELL = re.compile(r'^\|\s*§(\d+(?:\.\d+)?)\s*\|')
CITATION = re.compile(r'`([^`\n]+)::([^`\n]+)`')
EVIDENCE_CELL = re.compile(r'`[^`\n]+::[^`\n]+`(?:; `[^`\n]+::[^`\n]+`)*')


def split_row(line):
    return [cell.strip() for cell in line.strip().strip('|').split('|')]


def map_rows(text):
    return [(match.group(1), split_row(line)) for line in text.splitlines()
            for match in [ID_CELL.match(line)] if match]


def parse_cell(cell):
    return CITATION.findall(cell)


def test_symbols(source):
    """Only direct test methods on an explicitly declared unittest TestCase.

    No imports or source files are executed. Helpers, ordinary classes and
    nested functions are deliberately excluded from the accepted symbols.
    """
    tree = ast.parse(source)
    symbols = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any((isinstance(base, ast.Name) and base.id == 'TestCase') or
                   (isinstance(base, ast.Attribute) and base.attr == 'TestCase'
                    and isinstance(base.value, ast.Name)
                    and base.value.id == 'unittest') for base in node.bases):
            continue
        for method in node.body:
            if isinstance(method, ast.FunctionDef) and method.name.startswith('test_'):
                symbols.add(node.name + '.' + method.name)
    return symbols


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
    occurrences = {}
    for ident, _ in rows:
        occurrences[ident] = occurrences.get(ident, 0) + 1
    for ident in headings:
        if ident not in occurrences:
            problems.append('missing in map: ' + ident)
    for ident, count in occurrences.items():
        if count != 1:
            problems.append('duplicated in map: ' + ident)
        if ident not in headings:
            problems.append('invented id: ' + ident)

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
        cites = parse_cell(evidence)
        if evidence != 'none' and not EVIDENCE_CELL.fullmatch(evidence):
            problems.append(ident + ': malformed evidence cell')
        if status in ('COVERED', 'PARTIAL') and not cites:
            problems.append(ident + ': ' + status + ' needs a citation')
        if status == 'COVERED' and gap != 'none':
            problems.append(ident + ': COVERED gap must be none')
        if status == 'NOT_COVERED' and evidence != 'none':
            problems.append(ident + ': NOT_COVERED evidence must be none')
        if status in ('PARTIAL', 'NOT_COVERED') and (not gap or gap.lower() == 'none'):
            problems.append(ident + ': ' + status + ' needs a named gap')
        if ident in MUST_BE_OPEN and status != 'OPEN':
            problems.append(ident + ': must remain OPEN')
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

        for path, symbol in cites:
            target = Path(path)
            if (target.is_absolute() or '..' in target.parts
                    or path != target.as_posix() or '\\' in path):
                problems.append(ident + ': path must be repo-relative: ' + path)
                continue
            cross_suite = path in CROSS_SUITE_CITATIONS.get(ident, ())
            local_test = (target.parent.as_posix() == 'reference/settlement_f01_f03'
                          and target.match(TEST_GLOB))
            if not (local_test or cross_suite):
                problems.append(ident + ': not an allowed test path: ' + path)
                continue
            if path not in symbols_by_path:
                if path in files:
                    source = files[path]
                else:
                    full = ROOT / path
                    # Do not follow a test symlink outside the permitted subtree.
                    allowed = ROOT / ('reference/credit_advance_f04' if cross_suite
                                      else 'reference/settlement_f01_f03')
                    source = (full.read_text(encoding='utf-8')
                              if full.is_file() and full.resolve().is_relative_to(allowed)
                              else None)
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

    lines = [line for line in map_text.splitlines() if line.startswith('Counts:')]
    expected = 'Counts: ' + ' '.join('%s=%d' % (s, counts[s]) for s in STATUSES)
    if len(lines) != 1 or lines[0] != expected:
        problems.append('counts line must occur once and equal ' + expected)
    return problems


def row_line(text, ident):
    return next(line for line in text.splitlines()
                if ID_CELL.match(line) and ID_CELL.match(line).group(1) == ident)


def with_cell(text, ident, column, value):
    line = row_line(text, ident)
    cells = split_row(line)
    cells[column] = value
    return text.replace(line, '| ' + ' | '.join(cells) + ' |', 1)


def self_test(map_text, contract_text):
    baseline = find_problems(map_text, contract_text)
    if baseline:
        print('self-test: unmodified map fails:\n' + '\n'.join(baseline), file=sys.stderr)
        return 1
    row = row_line(map_text, '9.3')
    fsm = 'reference/settlement_f01_f03/test_settlement_fsm.py'
    fingerprint = 'reference/settlement_f01_f03/test_restore_fingerprint_equivalence.py'
    counts_line = next(line for line in map_text.splitlines() if line.startswith('Counts:'))
    cases = [
        ('missing clause', map_text.replace(row + '\n', '', 1), contract_text, {}, 'missing in map: 9.3'),
        ('new contract heading', map_text, contract_text + '\n### 9.7 X\n', {}, 'missing in map: 9.7'),
        ('removed required heading', map_text, contract_text.replace('### 9.3 멱등키', '### 멱등키'), {}, 'required contract heading missing: 9.3'),
        ('duplicate contract heading', map_text, contract_text + '\n### 9.3 X\n', {}, 'duplicated contract heading'),
        ('duplicate row', map_text + row + '\n', contract_text, {}, 'duplicated in map'),
        ('invented row', map_text + row.replace('§9.3', '§10', 1) + '\n', contract_text, {}, 'invented id: 10'),
        ('dangling path', with_cell(map_text, '9.3', 3, '`reference/settlement_f01_f03/test_no_such_9f3a.py::A.test_x`'), contract_text, {}, 'cited file does not exist'),
        ('dangling symbol', with_cell(map_text, '9.3', 3, '`' + fsm + '::SettlementFsmTests.test_no_such_9f3a`'), contract_text, {}, 'symbol is missing or not a test'),
        ('helper symbol', with_cell(map_text, '9.3', 3, '`' + fingerprint + '::SettlementRestoreFingerprintClassATests.check_variants`'), contract_text, {}, 'symbol is missing or not a test'),
        ('protected reference path', with_cell(map_text, '9.3', 3, '`reference/v0.3-rc1/test_x.py::A.test_x`'), contract_text, {}, 'not an allowed test path'),
        ('cross-suite on other row', with_cell(map_text, '9.3', 3, '`reference/credit_advance_f04/test_mock_credit.py::CreditAdvanceMockTests.test_note_reserves_unpaid_face_without_funds_or_license`'), contract_text, {}, 'not an allowed test path'),
        ('unlisted credit file', with_cell(map_text, '9.6', 3, '`reference/credit_advance_f04/test_credit_fsm.py::CreditFsmTests.test_direct_mock_credit_note_still_reserves_without_the_machine`'), contract_text, {}, 'not an allowed test path'),
        ('absolute path', with_cell(map_text, '9.3', 3, '`/tmp/test_x.py::A.test_x`'), contract_text, {}, 'path must be repo-relative'),
        ('parent path', with_cell(map_text, '9.3', 3, '`reference/settlement_f01_f03/../test_x.py::A.test_x`'), contract_text, {}, 'path must be repo-relative'),
        ('closed policy', with_cell(map_text, '7.3', 4, 'COVERED'), contract_text, {}, 'must remain OPEN'),
        ('unknown owner', with_cell(map_text, '7.3', 6, 'Nobody-9f3a'), contract_text, {}, 'owner not in contract'),
        ('missing owner', with_cell(map_text, '7.3', 6, 'none'), contract_text, {}, 'OPEN needs an owner'),
        ('missing UNDETERMINED', with_cell(map_text, '7.3', 5, 'decided'), contract_text, {}, 'OPEN needs UNDETERMINED'),
        ('heading drift', with_cell(map_text, '9.3', 1, 'wrong title'), contract_text, {}, 'heading title drift'),
        ('row width', map_text.replace(row, row + ' extra |', 1), contract_text, {}, 'expected 7 cells'),
        ('unknown status', with_cell(map_text, '9.3', 4, 'PASS'), contract_text, {}, 'unknown status'),
        ('uncited COVERED', with_cell(map_text, '1', 3, 'none'), contract_text, {}, 'COVERED needs a citation'),
        ('uncited PARTIAL', with_cell(map_text, '0.2', 3, 'none'), contract_text, {}, 'PARTIAL needs a citation'),
        ('COVERED gap', with_cell(map_text, '1', 5, 'missing'), contract_text, {}, 'COVERED gap must be none'),
        ('PARTIAL missing gap', with_cell(map_text, '0.2', 5, 'none'), contract_text, {}, 'PARTIAL needs a named gap'),
        ('NOT_COVERED citation', with_cell(map_text, '0.1', 3, '`' + fsm + '::SettlementFsmTests.test_illegal_transitions_do_not_move_the_phase`'), contract_text, {}, 'NOT_COVERED evidence must be none'),
        ('bare citation', with_cell(map_text, '9.3', 3, fsm + '::SettlementFsmTests.test_illegal_transitions_do_not_move_the_phase'), contract_text, {}, 'malformed evidence'),
        ('stale counts', map_text.replace(counts_line, counts_line + '0', 1), contract_text, {}, 'counts line'),
        ('duplicate counts', map_text + counts_line + '\n', contract_text, {}, 'counts line'),
        ('missing banner', map_text.replace(BANNERS[0], '', 1), contract_text, {}, 'banner phrase missing'),
        ('missing grade banner', map_text.replace(BANNERS[1], '', 1), contract_text, {}, 'banner phrase missing'),
        ('ordinary class', map_text, contract_text, {fsm: 'class SettlementFsmTests:\n    def test_illegal_transitions_do_not_move_the_phase(self): pass\n'}, 'symbol is missing or not a test'),
        ('invalid Python', map_text, contract_text, {fsm: 'class ('}, 'invalid Python'),
    ]
    for name, mutated, contract, files, marker in cases:
        found = find_problems(mutated, contract, files)
        if not any(marker in problem for problem in found):
            print('self-test: failed to detect ' + name, file=sys.stderr)
            return 1
        print('self-test: detected ' + name)
    print('self-test: pass (%d negative controls)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_settlement_evidence_map.py [--self-test]', file=sys.stderr)
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
        print('settlement evidence map check failed:\n' + '\n'.join(problems), file=sys.stderr)
        return 1
    rows = map_rows(map_text)
    counts = {s: sum(cells[4] == s for _, cells in rows) for s in STATUSES}
    print('settlement evidence map ok: rows=%d headings=%d citations=%d %s' % (
        len(rows), len(HEADING.findall(contract_text)),
        sum(len(parse_cell(cells[3])) for _, cells in rows),
        ' '.join('%s=%d' % (s, counts[s]) for s in STATUSES)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
