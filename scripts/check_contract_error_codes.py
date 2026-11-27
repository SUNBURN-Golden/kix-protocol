#!/usr/bin/env python3
"""Check the contract error-code coverage doc against the contracts and the reference suites.

Compares three inputs:

- the first table after the error-code heading of seven contract tables
  (the first cell of each row holds one or more backticked codes;
  ``MOCK_INVARIANT`` is excluded as the contracts define it):
  ``SETTLEMENT_DISTRIBUTION_F01_F03.md`` section 6 (key SET),
  ``BOOKING_RESALE_ADMISSION_GATES.md`` section 6 (BRA), section 10.8
  (BRA-RES) and section 11.6 (BRA-ADM),
  ``CREDIT_ADVANCE_F04.md`` section 4 (F04) and section 7.8 (F04-FSM), and
  ``AI_DELEGATION_AUTHORITY.md`` section 8 (AID), plus the inline rejection
  tables in booking sections 9.2 (effect column) and 9.5 (code column), key
  BRA-RES9, excluding state/decision labels and six owner-scoped pass-throughs;
- the mock and FSM sources of each suite (an explicit allow-list), parsed with
  ``ast`` and never executed;
- the ``test_*.py`` files of the same suite directory.

``docs/status/CONTRACT_ERROR_CODE_COVERAGE.md`` has one row per key and code:
``| Key | `CODE` | Raised | Asserted | Status | Note |``.

Definitions, derived by this script and compared with the doc:

- RAISED: a non-docstring string constant equal to the code in an allow-listed
  source that has no ``Compare`` ancestor and is inside a ``def`` or ``lambda``
  (parameter defaults included) or is a value of a module-level dict.
- ASSERTED: a non-docstring string constant equal to the code inside the body
  of a ``test*`` function or method in a ``test_*.py`` file of the suite.

Checks, each reported on failure:

1. Keys and codes. The doc rows equal the contract table codes exactly, once
   each; missing, duplicated, extra and misspelled codes, a MOCK_INVARIANT row,
   an unknown key and a wrong cell count are reported.
2. Citations. The Raised and Asserted cells are ``no`` exactly when the derived
   site set is empty; every citation is ``path::symbol`` inside the suite
   directory, never under ``reference/v0.3-rc1/``, the file exists, the symbol
   is defined and the site is one the script derives.
3. Status. COVERED needs both sites; CLASS_B and CLASS_C need no assertion and
   a reasoned note (not ``none``); CLASS_C needs a raise site; a code asserted
   but not raised has no valid status.
4. Counts. The ``Counts:`` line equals the values recomputed from the table.

Standard library only. Convenience check, not a contract gate. It proves that
a name appears on a raise path or in a test body, not that the path is
reachable or what the test asserts. ``--self-test`` mutates in-memory copies
and requires each break to be caught; ``--emit`` prints candidate rows.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = 'docs/status/CONTRACT_ERROR_CODE_COVERAGE.md'
FORBIDDEN_PREFIX = 'reference/v0.3-rc1/'
EXCLUDED = 'MOCK_INVARIANT'
STATUSES = ('COVERED', 'CLASS_B', 'CLASS_C')
CELLS = 6
COUNTS_LINE = 'Counts:'

# key -> (contract path, heading line, suite dir, raise-source file names)
TABLES = {
    'SET': ('docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md', '## 6. 오류 코드',
            'reference/settlement_f01_f03', ('mock_settlement.py', 'settlement_fsm.py')),
    'BRA': ('docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md', '## 6. 오류 코드',
            'reference/booking_resale_admission',
            ('mock_gates.py', 'reservation_fsm.py', 'resale_fsm.py', 'admission_fsm.py')),
    'BRA-RES9': ('docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md', '### 9.2 전이',
                 'reference/booking_resale_admission', ('reservation_fsm.py',)),
    'BRA-RES': ('docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md', '### 10.8 거절',
                'reference/booking_resale_admission', ('resale_fsm.py',)),
    'BRA-ADM': ('docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md', '### 11.6 거절',
                'reference/booking_resale_admission', ('admission_fsm.py',)),
    'F04': ('docs/contracts/CREDIT_ADVANCE_F04.md', '## 4. 오류 코드',
            'reference/credit_advance_f04', ('mock_credit.py', 'credit_fsm.py')),
    'F04-FSM': ('docs/contracts/CREDIT_ADVANCE_F04.md', '### 7.8 이 기계가 더하는 코드',
                'reference/credit_advance_f04', ('credit_fsm.py',)),
    'AID': ('docs/contracts/AI_DELEGATION_AUTHORITY.md', '## 8. 오류 코드와 항상 거짓인 플래그',
            'reference/ai_delegation', ('ai_delegation_mock.py',)),
}
KEYS = tuple(TABLES)

CODE_TOKEN = re.compile(r'`([A-Z][A-Z0-9_]+)`')
CODE_SHAPE = re.compile(r'[A-Z][A-Z0-9_]+')
CITATION = re.compile(r'`([^`]+)`')
ROW_START = re.compile(
    r'^\|\s*(' + '|'.join(sorted(map(re.escape, TABLES), key=len, reverse=True))
    + r')\s*\|\s*`[A-Z][A-Z0-9_]+`\s*\|')
MAX_CITES = 2

# Owner-approved scope: pass-through codes keep their existing BRA/SET rows.
# Do not filter by derived raise sites: a newly documented code must be checked
# even when no source or assertion exists for it yet.
SECTION9_PASS_THROUGH = frozenset({
    'CLOCK_REGRESSION', 'SLOT_OCCUPIED', 'RESERVATION_EXPIRED',
    'ADMISSION_LOCKED', 'RIGHT_NOT_ACTIVE', 'UNKNOWN_SETTLEMENT',
})
SECTION9_NON_CODES = frozenset({
    'HELD', 'RELEASED', 'CONFIRMED', 'CANCELLED', 'PAYMENT_NOTED',
    'ISSUED', 'ADMISSION_AUTHORIZED', 'CONSUMED', 'FREE', 'RESERVED',
    'CONSUMED_ONCE',
})


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def contract_table(text, heading):
    """Return (data rows, problems) for the first table after ``heading``."""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip() == heading), None)
    if start is None:
        return [], ['heading %r not found' % heading]
    table = []
    for line in lines[start + 1:]:
        if line.startswith('#'):
            break
        if line.startswith('|'):
            table.append(line)
        elif table:
            break
    if len(table) < 3:
        return [], ['heading %r: table has no data rows' % heading]
    return [split_row(line) for line in table[2:]], []


def section9_codes(text):
    """Read §9.2 effects and §9.5 codes, de-duplicated in document order."""
    codes, problems = [], []
    excluded = SECTION9_NON_CODES | SECTION9_PASS_THROUGH | {EXCLUDED}
    for heading, column, width in (('### 9.2 전이', 3, 4), ('### 9.5 정산 게이트', 1, 2)):
        rows, errs = contract_table(text, heading)
        problems.extend(errs)
        for row in rows:
            if len(row) != width:
                problems.append('heading %r: expected %d cells, found %d' % (heading, width, len(row)))
                continue
            codes.extend(code for code in CODE_TOKEN.findall(row[column]) if code not in excluded)
    if not codes:
        problems.append('section 9 tables yield no codes')
    return list(dict.fromkeys(codes)), problems


def contract_codes(text, heading, key=None):
    """Return (codes in order, problems), with inline-table parsing for BRA-RES9."""
    if key == 'BRA-RES9':
        return section9_codes(text)
    rows, problems = contract_table(text, heading)
    if problems:
        return [], problems
    codes = []
    for row in rows:
        for code in CODE_TOKEN.findall(row[0]):
            if code != EXCLUDED:
                codes.append(code)
    if not codes:
        return [], ['heading %r: table yields no codes' % heading]
    return codes, []


def _is_docstring(node):
    return (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str))


def _is_code(node):
    return (isinstance(node, ast.Constant) and isinstance(node.value, str)
            and CODE_SHAPE.fullmatch(node.value) is not None)


def raise_sites(text):
    """Return ({code: {symbol}}, {defined symbols}) for one source text."""
    tree = ast.parse(text)
    found = {}
    defined = set()

    def walk(node, qual, in_func, in_cmp, dictname):
        if _is_docstring(node):
            return
        if isinstance(node, ast.ClassDef):
            name = (qual + '.' if qual else '') + node.name
            defined.add(name)
            for child in node.body:
                walk(child, name, in_func, in_cmp, dictname)
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = (qual + '.' if qual else '') + node.name
            defined.add(name)
            for child in ast.iter_child_nodes(node):
                walk(child, name, True, in_cmp, dictname)
            return
        if isinstance(node, ast.Lambda):
            for child in ast.iter_child_nodes(node):
                walk(child, qual, True, in_cmp, dictname)
            return
        if isinstance(node, ast.Compare):
            in_cmp = True
        if _is_code(node):
            if not in_cmp and (in_func or dictname):
                found.setdefault(node.value, set()).add(qual if in_func and qual else dictname)
            return
        for child in ast.iter_child_nodes(node):
            walk(child, qual, in_func, in_cmp, dictname)

    for stmt in tree.body:
        value = getattr(stmt, 'value', None)
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and isinstance(value, ast.Dict):
            target = stmt.targets[0] if isinstance(stmt, ast.Assign) else stmt.target
            if isinstance(target, ast.Name):
                defined.add(target.id)

                def values(d):
                    for v in d.values:
                        if isinstance(v, ast.Dict):
                            yield from values(v)
                        else:
                            yield v
                for v in values(value):
                    walk(v, None, False, False, target.id)
                continue
        walk(stmt, None, False, False, None)
    found = {c: {s for s in sites if s} for c, sites in found.items()}
    return {c: s for c, s in found.items() if s}, defined


def test_sites(text):
    """Return ({code: {Class.method}}, {defined symbols}) for one test file."""
    tree = ast.parse(text)
    found = {}
    defined = set()

    def collect(node, name):
        if _is_docstring(node):
            return
        if _is_code(node):
            found.setdefault(node.value, set()).add(name)
            return
        for child in ast.iter_child_nodes(node):
            collect(child, name)

    def visit(node, prefix):
        for child in node.body:
            if isinstance(child, ast.ClassDef):
                defined.add(prefix + child.name)
                visit(child, prefix + child.name + '.')
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + child.name
                defined.add(name)
                if child.name.startswith('test'):
                    for part in child.body:
                        collect(part, name)
    visit(tree, '')
    return found, defined


def load_sources(root=ROOT):
    """Return {repo-relative path: text} for every .py file of the four suites."""
    out = {}
    for _, _, suite, _ in TABLES.values():
        for path in sorted((root / suite).glob('*.py')):
            out[suite + '/' + path.name] = path.read_text(encoding='utf-8')
    return out


def derive(sources):
    """Return ({key: {code: (raised, asserted)}}, {path: defined symbols})."""
    result = {}
    symbols = {}
    for key, (_, _, suite, raise_files) in TABLES.items():
        raised, asserted = {}, {}
        for path, text in sources.items():
            if not path.startswith(suite + '/'):
                continue
            name = path[len(suite) + 1:]
            if name in raise_files:
                sites, defined = raise_sites(text)
                symbols[path] = defined
                for code, syms in sites.items():
                    raised.setdefault(code, set()).update(path + '::' + s for s in syms)
            elif name.startswith('test_'):
                sites, defined = test_sites(text)
                symbols[path] = defined
                for code, syms in sites.items():
                    asserted.setdefault(code, set()).update(path + '::' + s for s in syms)
        result[key] = (raised, asserted)
    return result, symbols


def parse_cell(cell):
    return [m.group(1).strip() for m in CITATION.finditer(cell)]


def doc_rows(doc_text):
    return [split_row(line) for line in doc_text.splitlines() if ROW_START.match(line)]


def find_problems(doc_text, contract_texts, sources):
    """Return a list of problem strings; empty means the doc passes."""
    problems = []
    derived, symbols = derive(sources)
    expected = {}
    for key, (_, heading, _, _) in TABLES.items():
        codes, errs = contract_codes(contract_texts[key], heading, key)
        problems += ['%s: %s' % (key, e) for e in errs]
        for code in sorted({c for c in codes if codes.count(c) > 1}):
            problems.append('%s: %s listed twice in the contract table' % (key, code))
        expected[key] = list(dict.fromkeys(codes))

    rows = doc_rows(doc_text)
    seen = {}
    for cells in rows:
        if len(cells) != CELLS:
            problems.append('%s: expected %d cells, found %d' % (cells[0], CELLS, len(cells)))
            continue
        match = CODE_TOKEN.fullmatch(cells[1])
        if not match:
            problems.append('%s: code cell %r is not one backticked code' % (cells[0], cells[1]))
            continue
        pair = (cells[0], match.group(1))
        seen[pair] = seen.get(pair, 0) + 1
    for key in KEYS:
        for code in expected[key]:
            if (key, code) not in seen:
                problems.append('%s: %s missing in doc' % (key, code))
            elif seen[(key, code)] != 1:
                problems.append('%s: %s duplicated in doc (%d)' % (key, code, seen[(key, code)]))
    for key, code in sorted(seen):
        if code == EXCLUDED:
            problems.append('%s: %s is excluded and must not have a row' % (key, code))
        elif code not in expected[key]:
            problems.append('%s: %s is not in the contract table' % (key, code))

    totals = {k: 0 for k in ('rows', 'RAISED', 'ASSERTED') + STATUSES}
    by_key = {k: 0 for k in KEYS}
    done = set()
    for cells in rows:
        if len(cells) != CELLS or not CODE_TOKEN.fullmatch(cells[1]):
            continue
        key, code = cells[0], CODE_TOKEN.fullmatch(cells[1]).group(1)
        if (key, code) in done or code == EXCLUDED or code not in expected[key]:
            continue
        done.add((key, code))
        label = '%s %s' % (key, code)
        suite = TABLES[key][2]
        raised, asserted = (derived[key][0].get(code, set()), derived[key][1].get(code, set()))
        totals['rows'] += 1
        by_key[key] += 1
        got = {}
        for name, cell, want in (('Raised', cells[2], raised), ('Asserted', cells[3], asserted)):
            cites = parse_cell(cell)
            got[name] = bool(want)
            if not cites and cell != 'no':
                problems.append('%s: %s cell is neither no nor a citation' % (label, name))
            if cites and cell == 'no':
                problems.append('%s: %s cell mixes no and citations' % (label, name))
            if not cites and want:
                problems.append('%s: %s is no but the sources have %d site(s)' % (label, name, len(want)))
            if cites and not want:
                problems.append('%s: %s cites a site but none is derived' % (label, name))
            for cite in cites:
                path, _, symbol = cite.partition('::')
                where = '%s: %s citation %s' % (label, name, cite)
                if path.startswith('/') or '..' in path.split('/'):
                    problems.append('%s is not repo-relative' % where)
                elif path.startswith(FORBIDDEN_PREFIX):
                    problems.append('%s is under reference/v0.3-rc1' % where)
                elif not path.startswith(suite + '/'):
                    problems.append('%s is outside the suite directory %s' % (where, suite))
                elif path not in sources:
                    problems.append('%s: file does not exist' % where)
                elif not symbol:
                    problems.append('%s needs a ::symbol' % where)
                elif symbol not in symbols.get(path, ()):
                    problems.append('%s: symbol is not defined in the file' % where)
                elif cite not in want:
                    problems.append('%s is not a derived site' % where)
        status, note = cells[4], cells[5]
        if got['Raised']:
            totals['RAISED'] += 1
        if got['Asserted']:
            totals['ASSERTED'] += 1
        if status not in STATUSES:
            problems.append('%s: unknown status %r' % (label, status))
            continue
        totals[status] += 1
        if not note:
            problems.append('%s: empty note' % label)
        if status == 'COVERED' and not (got['Raised'] and got['Asserted']):
            problems.append('%s: COVERED needs both a raise site and an asserting test' % label)
        if status in ('CLASS_B', 'CLASS_C'):
            if got['Asserted']:
                problems.append('%s: %s row is asserted by a test, so it is COVERED' % (label, status))
            if note.lower().startswith('none'):
                problems.append('%s: %s row needs a reasoned note' % (label, status))
        if status == 'CLASS_C' and not got['Raised']:
            problems.append('%s: CLASS_C needs a raise site; use CLASS_B for an unreachable code' % label)
        if got['Asserted'] and not got['Raised']:
            problems.append('%s: asserted by a test but no raise site is derived' % label)

    want = counts_line(by_key, totals)
    lines = [l for l in doc_text.splitlines() if l.startswith(COUNTS_LINE)]
    if len(lines) != 1:
        problems.append('%r line appears %d times' % (COUNTS_LINE, len(lines)))
    elif lines[0].strip() != want:
        problems.append('counts line %r differs from the table %r' % (lines[0].strip(), want))
    return problems


def counts_line(by_key, totals):
    parts = ['%s=%d' % (k, by_key[k]) for k in KEYS]
    parts += ['%s=%d' % (k, totals[k]) for k in ('rows', 'RAISED', 'ASSERTED') + STATUSES]
    return COUNTS_LINE + ' ' + ' '.join(parts)


def read_inputs():
    contracts = {}
    for key, (rel, _, _, _) in TABLES.items():
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit('missing ' + str(path))
        contracts[key] = path.read_text(encoding='utf-8')
    return contracts, load_sources()


def emit(contracts, sources):
    derived, _ = derive(sources)
    for key, (_, heading, _, _) in TABLES.items():
        codes, _ = contract_codes(contracts[key], heading, key)
        raised, asserted = derived[key]
        for code in dict.fromkeys(codes):
            r, a = sorted(raised.get(code, ())), sorted(asserted.get(code, ()))
            cell = lambda sites: '; '.join('`%s`' % s for s in sites[:MAX_CITES]) or 'no'
            status = 'COVERED' if r and a else 'GAP'
            print('| %s | `%s` | %s | %s | %s | |' % (key, code, cell(r), cell(a), status))


def _row_line(text, key, code):
    for line in text.splitlines():
        if ROW_START.match(line):
            cells = split_row(line)
            if cells[0] == key and cells[1] == '`%s`' % code:
                return line
    return None


def _with_cell(text, key, code, col, new):
    line = _row_line(text, key, code)
    cells = split_row(line)
    cells[col] = new
    return text.replace(line, '| ' + ' | '.join(cells) + ' |', 1)


def _probe_controls():
    """Positive controls for source and inline-table extractors."""
    inline = (
        '### 9.2 전이\n\n'
        '| phase | command | next | effect |\n|---|---|---|---|\n'
        '| `HELD` | `not_a_code` | `IGNORED_PHASE` | `FREE`, `CONSUMED_ONCE`, '
        '`FIRST_PROBE`, `CLOCK_REGRESSION`, `SLOT_OCCUPIED`, `RESERVATION_EXPIRED`, '
        '`ADMISSION_LOCKED`, `RIGHT_NOT_ACTIVE`, `MOCK_INVARIANT` |\n'
        '| x | x | x | `FIRST_PROBE`, `SECOND_PROBE` |\n'
        '\n`OUTSIDE_TABLE`\n### 9.4 ignored\n`OUTSIDE_SECTION`\n'
        '### 9.5 정산 게이트\n\n'
        '| view | code |\n|---|---|\n'
        '| `COMMITTED` | `UNKNOWN_SETTLEMENT`, `THIRD_PROBE`, `FIRST_PROBE` |\n'
        '\n### 9.6 ignored\n`OUTSIDE_SECTION`\n'
    )
    codes, problems = section9_codes(inline)
    if codes != ['FIRST_PROBE', 'SECOND_PROBE', 'THIRD_PROBE'] or problems:
        return 'section 9 extractor: got %s, %s' % (codes, problems)
    src = (
        'RAISE_PROBE = "NOT_A_SITE_NAME"\n'
        'FROZEN = frozenset({"IN_SET"})\n'
        'TABLE = {"KEY_ONLY": "IN_DICT_VALUE"}\n'
        'def _ident(value, code="IN_DEFAULT"):\n'
        '    """DOC_STRING"""\n'
        '    if value == "IN_COMPARE":\n'
        '        pass\n'
        '    return _fail("IN_CALL" if value else "IN_TERNARY")\n'
        'class K:\n'
        '    ATTR = ("IN_CLASS_ATTR",)\n'
        '    def m(self):\n'
        '        f = lambda: "IN_LAMBDA"\n'
        '        return f\n'
    )
    sites, defined = raise_sites(src)
    counted = {'IN_DEFAULT', 'IN_CALL', 'IN_TERNARY', 'IN_DICT_VALUE', 'IN_LAMBDA'}
    refused = {'DOC_STRING', 'IN_COMPARE', 'IN_SET', 'IN_CLASS_ATTR', 'KEY_ONLY', 'NOT_A_SITE_NAME'}
    if set(sites) != counted or set(sites) & refused:
        return 'raise-site extractor: got %s' % sorted(sites)
    if sites['IN_DICT_VALUE'] != {'TABLE'} or sites['IN_LAMBDA'] != {'K.m'} or 'K.m' not in defined:
        return 'raise-site extractor: wrong symbols %s' % sites
    tsrc = (
        'HELPER_CODES = ("IN_ATTR",)\n'
        'def helper():\n    return "IN_HELPER"\n'
        'class T:\n'
        '    CODES = ("IN_CLASS_ATTR",)\n'
        '    def test_one(self):\n'
        '        """DOC_STRING"""\n'
        '        self.assertEqual(code(lambda: 1), "IN_TEST")\n'
        'def test_two():\n    assert x in ("IN_TUPLE",)\n'
    )
    tsites, tdefined = test_sites(tsrc)
    if set(tsites) != {'IN_TEST', 'IN_TUPLE'} or tsites['IN_TEST'] != {'T.test_one'} or 'T.test_one' not in tdefined:
        return 'test-site extractor: got %s' % sorted(tsites)
    return None


def self_test(doc_text, contracts, sources):
    """Require each check to catch a deliberately broken copy."""
    base = find_problems(doc_text, contracts, sources)
    if base:
        print('self-test: unmodified doc already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1
    failed = _probe_controls()
    if failed:
        print('self-test: ' + failed, file=sys.stderr)
        return 1

    derived, _ = derive(sources)
    # a COVERED code with a raise site in a non-test source and a test that names it
    probe = None
    for cells in doc_rows(doc_text):
        if cells[0] == 'SET' and cells[4] == 'COVERED' and cells[3] != 'no':
            probe = cells[1].strip('`')
            break
    if probe is None:
        print('self-test: no COVERED SET row to mutate', file=sys.stderr)
        return 1
    raised, asserted = derived['SET'][0][probe], derived['SET'][1][probe]
    src_path = sorted(raised)[0].partition('::')[0]
    cls_b = next((c[1].strip('`') for c in doc_rows(doc_text) if c[4] == 'CLASS_B'), None)

    def without_literal(path_set, code):
        out = dict(sources)
        for site in path_set:
            path = site.partition('::')[0]
            out[path] = out[path].replace('"%s"' % code, '"X_REMOVED_%s"' % code)
        return out

    def corrupt_row(key, code, col, new):
        return _with_cell(doc_text, key, code, col, new)

    counts = next(l for l in doc_text.splitlines() if l.startswith(COUNTS_LINE))
    line = _row_line(doc_text, 'SET', probe)
    first_set_code = split_row(line)[1].strip('`')
    cases = [
        ('removed doc row', doc_text.replace(line + '\n', '', 1), contracts, sources,
         'SET: %s missing in doc' % first_set_code),
        ('duplicated doc row', doc_text.replace(line, line + '\n' + line, 1), contracts, sources,
         'duplicated in doc'),
        ('misspelled code (missing side)', doc_text.replace(line, line.replace('`%s`' % probe, '`%sX`' % probe, 1), 1),
         contracts, sources, 'SET: %s missing in doc' % probe),
        ('misspelled code (extra side)', doc_text.replace(line, line.replace('`%s`' % probe, '`%sX`' % probe, 1), 1),
         contracts, sources, 'is not in the contract table'),
        ('stale counts line', doc_text.replace(counts, counts.replace('rows=', 'rows=9', 1), 1),
         contracts, sources, 'counts line'),
        ('wrong cell count', doc_text.replace(line, line + ' extra |', 1), contracts, sources,
         'expected 6 cells'),
        ('unknown status', corrupt_row('SET', probe, 4, 'SUFFICIENT'), contracts, sources, 'unknown status'),
        ('MOCK_INVARIANT row', doc_text.replace(line, line + '\n| SET | `MOCK_INVARIANT` | no | no | CLASS_B | x |', 1),
         contracts, sources, 'is excluded and must not have a row'),
        ('removed raise site', doc_text, contracts, without_literal(raised, probe),
         'cites a site but none is derived'),
        ('removed asserting test', doc_text, contracts, without_literal(asserted, probe),
         'Asserted cites a site but none is derived'),
        ('Raised cell set to no', corrupt_row('SET', probe, 2, 'no'), contracts, sources,
         'Raised is no but the sources have'),
        ('dangling path', corrupt_row('SET', probe, 2, split_row(line)[2] + ' `reference/settlement_f01_f03/no_such.py::x`'),
         contracts, sources, 'file does not exist'),
        ('dangling symbol', corrupt_row('SET', probe, 2, split_row(line)[2] + ' `%s::no_such_fn_9f3a`' % src_path),
         contracts, sources, 'symbol is not defined in the file'),
        ('citation outside the suite directory',
         corrupt_row('SET', probe, 2, split_row(line)[2] + ' `reference/ai_delegation/ai_delegation_mock.py::x`'),
         contracts, sources, 'outside the suite directory'),
        ('citation under reference/v0.3-rc1',
         corrupt_row('SET', probe, 2, split_row(line)[2] + ' `reference/v0.3-rc1/x.py::y`'),
         contracts, sources, 'reference/v0.3-rc1'),
        ('citation that is not a derived site',
         corrupt_row('SET', probe, 2, split_row(line)[2] + ' `%s::MockSettlement.__init__`' % src_path),
         contracts, sources, 'is not a derived site'),
        ('contract table with an added code',
         doc_text, dict(contracts, SET=contracts['SET'].replace(
             '| `INVALID_ID` |', '| `ADDED_PROBE_CODE` | probe |\n| `INVALID_ID` |', 1)), sources,
         'ADDED_PROBE_CODE missing in doc'),
        ('contract table with a removed heading',
         doc_text, dict(contracts, SET=contracts['SET'].replace('## 6. 오류 코드', '## 6. x', 1)), sources,
         'not found'),
        ('COVERED row without an asserting test', corrupt_row('SET', probe, 3, 'no'), contracts,
         without_literal(asserted, probe), 'COVERED needs both'),
    ]
    res_probe = next(
        (c[1].strip('`') for c in doc_rows(doc_text) if c[0] == 'BRA-RES' and c[4] == 'COVERED'),
        None)
    if res_probe is None:
        print('self-test: no COVERED BRA-RES row to mutate', file=sys.stderr)
        return 1
    res_line = _row_line(doc_text, 'BRA-RES', res_probe)
    res_src = sorted(derived['BRA-RES'][0][res_probe])[0].partition('::')[0]
    cases += [
        ('added code in the BRA-RES contract table',
         doc_text, dict(contracts, **{'BRA-RES': contracts['BRA-RES'].replace(
             '| `TICKET_NOT_ISSUED` |', '| `ADDED_PROBE_CODE` | probe |\n| `TICKET_NOT_ISSUED` |', 1)}),
         sources, 'BRA-RES: ADDED_PROBE_CODE missing in doc'),
        ('removed raise site on a BRA-RES row', doc_text, contracts,
         without_literal(derived['BRA-RES'][0][res_probe], res_probe),
         'cites a site but none is derived'),
        ('citation that is not a derived site on a BRA-RES row',
         corrupt_row('BRA-RES', res_probe, 2,
                     split_row(res_line)[2] + ' `%s::ResaleMachine._listing`' % res_src),
         contracts, sources, 'is not a derived site'),
    ]
    res9_probe = next(
        (c[1].strip('`') for c in doc_rows(doc_text) if c[0] == 'BRA-RES9' and c[4] == 'COVERED'),
        None)
    if res9_probe is None:
        print('self-test: no COVERED BRA-RES9 row to mutate', file=sys.stderr)
        return 1
    cases += [
        ('missing section 9 raise citation', corrupt_row('BRA-RES9', res9_probe, 2, 'no'),
         contracts, sources, 'BRA-RES9 %s: Raised is no but the sources have' % res9_probe),
        ('missing section 9 assertion citation', corrupt_row('BRA-RES9', res9_probe, 3, 'no'),
         contracts, sources, 'BRA-RES9 %s: Asserted is no but the sources have' % res9_probe),
        ('added code in the section 9.2 effect column',
         doc_text, dict(contracts, **{'BRA-RES9': contracts['BRA-RES9'].replace(
             '| 없음 | `set_clock` | 시계 | 감소는 `CLOCK_REGRESSION` |',
             '| 없음 | `set_clock` | 시계 | 감소는 `CLOCK_REGRESSION`, `ADDED_PROBE_CODE` |', 1)}),
         sources, 'BRA-RES9: ADDED_PROBE_CODE missing in doc'),
        ('added code in the section 9.5 code column',
         doc_text, dict(contracts, **{'BRA-RES9': contracts['BRA-RES9'].replace(
             '| `SETTLEMENT_SOURCE_REQUIRED` |', '| `SETTLEMENT_SOURCE_REQUIRED`, `ADDED_PROBE_CODE` |', 1)}),
         sources, 'BRA-RES9: ADDED_PROBE_CODE missing in doc'),
        ('removed section 9.5 heading',
         doc_text, dict(contracts, **{'BRA-RES9': contracts['BRA-RES9'].replace(
             '### 9.5 정산 게이트', '### 9.5 x', 1)}),
         sources, "BRA-RES9: heading '### 9.5 정산 게이트' not found"),
        ('malformed section 9.5 row',
         doc_text, dict(contracts, **{'BRA-RES9': contracts['BRA-RES9'].replace(
             '| `SETTLEMENT_SOURCE_REQUIRED` |', '| extra | `SETTLEMENT_SOURCE_REQUIRED` |', 1)}),
         sources, 'expected 2 cells, found 3'),
    ]
    cases.append(('CLASS_B status on an asserted code with a none note',
                  _with_cell(corrupt_row('SET', probe, 4, 'CLASS_B'), 'SET', probe, 5, 'none'),
                  contracts, sources, 'needs a reasoned note'))
    cases.append(('CLASS_C status on an asserted code', corrupt_row('SET', probe, 4, 'CLASS_C'),
                  contracts, sources, 'is asserted by a test, so it is COVERED'))
    if cls_b:
        cases += [
            ('CLASS_B row with a none note', corrupt_row(
                next(c[0] for c in doc_rows(doc_text) if c[4] == 'CLASS_B'), cls_b, 5, 'none'),
             contracts, sources, 'needs a reasoned note'),
        ]
    for name, text, cons, srcs, marker in cases:
        found = find_problems(text, cons, srcs)
        hit = [item for item in found if marker in item]
        if not hit:
            print('self-test: %s was accepted' % name, file=sys.stderr)
            for item in found[:5]:
                print('  saw: ' + item, file=sys.stderr)
            return 1
        print('self-test: detected %s (%s)' % (name, hit[0]))
    print('self-test: pass')
    return 0


def main(argv):
    path = ROOT / DOC
    contracts, sources = read_inputs()
    if '--emit' in argv:
        emit(contracts, sources)
        return 0
    if not path.is_file():
        print('missing ' + str(path), file=sys.stderr)
        return 1
    doc_text = path.read_text(encoding='utf-8')
    if '--self-test' in argv:
        return self_test(doc_text, contracts, sources)
    problems = find_problems(doc_text, contracts, sources)
    if problems:
        print('contract error code coverage check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    rows = doc_rows(doc_text)
    totals = {k: 0 for k in ('rows', 'RAISED', 'ASSERTED') + STATUSES}
    by_key = {k: 0 for k in KEYS}
    for cells in rows:
        by_key[cells[0]] += 1
        totals['rows'] += 1
        totals['RAISED'] += cells[2] != 'no'
        totals['ASSERTED'] += cells[3] != 'no'
        totals[cells[4]] += 1
    print('contract error code coverage ok: ' + counts_line(by_key, totals)[len(COUNTS_LINE) + 1:])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
