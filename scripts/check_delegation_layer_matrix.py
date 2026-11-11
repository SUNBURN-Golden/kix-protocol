#!/usr/bin/env python3
"""Check the AI delegation layer matrix against its contract and its sources.

Compares three inputs:

- ``docs/contracts/AI_DELEGATION_AUTHORITY.md`` section 6: the predicates
  DLG-01..DLG-36, each the first cell of a table row.
- ``docs/status/AI_DELEGATION_LAYER_MATRIX.md``: the builder-authored matrix,
  one row per predicate, seven cells per row (id, paraphrase, mock test,
  chain analogue, executor-map analogue, readiness wrap, status).
- ``reference/ai_delegation/test_ai_delegation_mock.py``: the mock tests whose
  docstrings cite the predicates.

Checks, each reported on failure:

1. Ids. Every contract DLG id appears exactly once as a matrix first cell;
   missing, duplicated, extra and not-in-contract ids are reported. Each row
   has seven cells and a non-empty paraphrase.
2. Status. It is one of MOCK_ONLY, ANALOGUE_NOT_BOUND, NO_LAYER,
   NOT_APPLICABLE_BY_DESIGN, and agrees with the citations: MOCK_ONLY has
   ``none`` in the chain and executor cells; ANALOGUE_NOT_BOUND has at least
   one non-``absent:`` chain or executor citation; NO_LAYER has an
   ``absent:`` citation and no other; NOT_APPLICABLE_BY_DESIGN has ``none``
   in both and names a ``contract §N`` that exists.
3. Paths. A citation is ``path::symbol``, ``absent: path::symbol`` or a bare
   path for ``.md``/``.toml``. Each path exists, is repo-relative and lies in
   its column's allowed prefix. Each row cites at least one source.
4. Symbols. Each symbol is defined (``def``/``class``/module-level name,
   ``fn``/``struct``/``enum``/``const``, ``fun``/``struct``/``const``) in the
   cited file; for ``.md``/``.toml`` it must appear as text.
5. Mock agreement. A row's mock-test cell equals, in both directions, the set
   of ``test_*`` functions whose own docstring cites the id.
6. Gap summary. The three lines ``No chain analogue``, ``No executor
   analogue`` and ``Neither`` equal the sets recomputed from the table. A
   cell is "no analogue" when it is ``none`` or holds only ``absent:``.

Standard library only. Convenience check, not a contract gate. It reads the
cited files as text and executes none of them. ``--self-test`` mutates
in-memory copies of the matrix and requires each break to be caught.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = 'docs/status/AI_DELEGATION_LAYER_MATRIX.md'
CONTRACT = 'docs/contracts/AI_DELEGATION_AUTHORITY.md'
MOCK_TEST = 'reference/ai_delegation/test_ai_delegation_mock.py'

STATUSES = ('MOCK_ONLY', 'ANALOGUE_NOT_BOUND', 'NO_LAYER',
            'NOT_APPLICABLE_BY_DESIGN')
# column index -> (name, allowed path prefixes)
COLUMNS = {
    2: ('mock', (MOCK_TEST,)),
    3: ('chain', ('reference/rights_scale/',)),
    4: ('executor', ('runtime/crates/kix-delegated-exec/',)),
    5: ('readiness', ('readiness/ai_delegation_wrap.py',)),
}
TEXT_SUFFIXES = ('.md', '.toml')

STATUS_WORD = re.compile(r'[A-Z_]+')
DLG = re.compile(r'DLG-\d\d')
FIRST_CELL = re.compile(r'^\|\s*(DLG-\d\d)\s*\|')
CITATION = re.compile(r'(absent:\s*)?`([^`]+)`')
CONTRACT_REF = re.compile(r'contract §(\d+)')
SECTION_HEADING = re.compile(r'^##\s+(\d+)\.')
GAP_LINES = (('chain', '- No chain analogue:'),
             ('executor', '- No executor analogue:'),
             ('neither', '- Neither:'))

DEF_PATTERNS = {
    '.py': r'^\s*(?:(?:async\s+)?def|class)\s+%s\b|^%s\s*[:=]',
    '.rs': r'^\s*(?:pub(?:\([^)]*\))?\s+)?(?:fn|struct|enum|const)\s+%s\b',
    '.move': (r'^\s*(?:public(?:\([a-z]+\))?\s+)?(?:entry\s+)?'
              r'(?:fun|struct|const)\s+%s\b'),
}


def split_row(line):
    cells = [c.strip() for c in line.strip().strip('|').split('|')]
    return cells


def contract_ids(contract_text):
    ids = []
    in_section = False
    for line in contract_text.splitlines():
        if line.startswith('## '):
            in_section = line.startswith('## 6.')
            continue
        if in_section:
            match = FIRST_CELL.match(line)
            if match:
                ids.append(match.group(1))
    return ids


def matrix_rows(matrix_text):
    """Return a list of (id, cells) for every DLG first-column row."""
    rows = []
    for line in matrix_text.splitlines():
        match = FIRST_CELL.match(line)
        if match:
            rows.append((match.group(1), split_row(line)))
    return rows


def mock_citations(mock_text):
    """Map DLG id -> set of test function names whose docstring cites it."""
    cites = {}
    for node in ast.walk(ast.parse(mock_text)):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test'):
            for ident in DLG.findall(ast.get_docstring(node) or ''):
                cites.setdefault(ident, set()).add(node.name)
    return cites


def parse_cell(cell):
    """Return (is_none, [(absent, path, symbol_or_None), ...])."""
    cites = []
    for match in CITATION.finditer(cell):
        path, _, symbol = match.group(2).partition('::')
        cites.append((bool(match.group(1)), path.strip(), symbol.strip() or None))
    return (not cites and cell.strip() == 'none'), cites


def symbol_defined(text, suffix, symbol):
    if suffix in TEXT_SUFFIXES:
        return symbol in text
    pattern = DEF_PATTERNS.get(suffix)
    if pattern is None:
        return False
    name = re.escape(symbol)
    return re.search(pattern.replace('%s', name), text, re.M) is not None


def find_problems(matrix_text, contract_text, mock_text, root=ROOT, files=None):
    """Return a list of problem strings; empty means the matrix passes.

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

    expected = contract_ids(contract_text)
    expected_set = set(expected)
    rows = matrix_rows(matrix_text)
    counts = {}
    for ident, _ in rows:
        counts[ident] = counts.get(ident, 0) + 1
    for ident in expected:
        if counts.get(ident, 0) == 0:
            problems.append('missing in matrix: %s' % ident)
        elif counts[ident] != 1:
            problems.append('duplicated in matrix: %s (%d)' % (ident, counts[ident]))
    for ident in sorted(counts):
        if ident not in expected_set:
            problems.append('not in contract section 6: %s' % ident)
    if len(expected) != len(expected_set):
        problems.append('contract section 6 repeats an id')

    contract_sections = {m.group(1) for m in (
        SECTION_HEADING.match(l) for l in contract_text.splitlines()) if m}
    mock_cites = mock_citations(mock_text)
    for ident in sorted(set(mock_cites) - expected_set):
        problems.append('mock test cites an id not in contract: %s' % ident)

    no_chain, no_exec = set(), set()
    seen = set()
    for ident, cells in rows:
        if ident in seen:
            continue
        seen.add(ident)
        if len(cells) != 7:
            problems.append('%s: expected 7 cells, found %d' % (ident, len(cells)))
            continue
        if not cells[1]:
            problems.append('%s: empty paraphrase' % ident)
        status_cell = cells[6]
        status = STATUS_WORD.match(status_cell).group(0) if STATUS_WORD.match(status_cell) else ''
        if status not in STATUSES:
            problems.append('%s: unknown status %r' % (ident, status))

        parsed = {}
        total = 0
        for col, (name, prefixes) in COLUMNS.items():
            is_none, cites = parse_cell(cells[col])
            if not is_none and not cites:
                problems.append('%s: %s cell is neither none nor a citation'
                                % (ident, name))
            parsed[name] = (is_none, cites)
            total += len(cites)
            for absent, path, symbol in cites:
                where = '%s: %s citation %s' % (ident, name, path)
                if path.startswith('/') or '..' in path.split('/'):
                    problems.append('%s is not repo-relative' % where)
                    continue
                if not any(path == p or (p.endswith('/') and path.startswith(p))
                           for p in prefixes):
                    problems.append('%s is outside the %s column paths' % (where, name))
                text = read(path)
                if text is None:
                    problems.append('%s does not exist' % where)
                    continue
                suffix = Path(path).suffix
                if symbol is None:
                    if suffix not in TEXT_SUFFIXES:
                        problems.append('%s needs a ::symbol' % where)
                elif not symbol_defined(text, suffix, symbol):
                    problems.append('%s::%s is not defined in the file' % (where, symbol))
        if total == 0:
            problems.append('%s: no cited source' % ident)

        mock_cell = parsed['mock'][1]
        cited_tests = {symbol for _, _, symbol in mock_cell if symbol}
        if cited_tests != mock_cites.get(ident, set()):
            problems.append('%s: mock tests %s differ from docstring citations %s'
                            % (ident, sorted(cited_tests),
                               sorted(mock_cites.get(ident, set()))))
        if any(absent for absent, _, _ in mock_cell):
            problems.append('%s: mock cell may not use absent:' % ident)

        def analogue(name):
            return [c for c in parsed[name][1] if not c[0]]

        def absent(name):
            return [c for c in parsed[name][1] if c[0]]

        chain_real, exec_real = analogue('chain'), analogue('executor')
        any_real = bool(chain_real or exec_real)
        any_absent = bool(absent('chain') or absent('executor'))
        both_none = parsed['chain'][0] and parsed['executor'][0]
        if status == 'MOCK_ONLY' and not both_none:
            problems.append('%s: MOCK_ONLY needs none in chain and executor cells' % ident)
        elif status == 'ANALOGUE_NOT_BOUND' and not any_real:
            problems.append('%s: ANALOGUE_NOT_BOUND needs a non-absent chain or executor citation' % ident)
        elif status == 'NO_LAYER' and (any_real or not any_absent):
            problems.append('%s: NO_LAYER needs an absent: citation and no other chain or executor citation' % ident)
        elif status == 'NOT_APPLICABLE_BY_DESIGN':
            if not both_none:
                problems.append('%s: NOT_APPLICABLE_BY_DESIGN needs none in chain and executor cells' % ident)
            ref = CONTRACT_REF.search(status_cell)
            if not ref:
                problems.append('%s: NOT_APPLICABLE_BY_DESIGN must name a contract §N' % ident)
            elif ref.group(1) not in contract_sections:
                problems.append('%s: contract §%s does not resolve' % (ident, ref.group(1)))

        if not chain_real:
            no_chain.add(ident)
        if not exec_real:
            no_exec.add(ident)

    computed = {'chain': no_chain, 'executor': no_exec,
                'neither': no_chain & no_exec}
    lines = matrix_text.splitlines()
    for key, prefix in GAP_LINES:
        found = [l for l in lines if l.startswith(prefix)]
        if len(found) != 1:
            problems.append('gap summary line %r appears %d times' % (prefix, len(found)))
            continue
        body = found[0][len(prefix):].strip()
        listed = set(DLG.findall(body))
        if not listed and body.strip('`. ') != 'none':
            problems.append('gap summary line %r is neither ids nor none' % prefix)
        if listed != computed[key]:
            problems.append('gap summary %r lists %s but the table gives %s'
                            % (prefix, sorted(listed), sorted(computed[key])))
    return problems


def _row_line(text, ident):
    for line in text.splitlines():
        match = FIRST_CELL.match(line)
        if match and match.group(1) == ident:
            return line
    return None


def _with_cell(text, ident, col, new):
    line = _row_line(text, ident)
    cells = split_row(line)
    cells[col] = new
    return text.replace(line, '| ' + ' | '.join(cells) + ' |', 1)


def self_test(matrix_text, contract_text, mock_text):
    """Require each check to catch a deliberately broken copy."""
    base = find_problems(matrix_text, contract_text, mock_text)
    if base:
        print('self-test: unmodified matrix already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1

    def line_of(ident):
        return _row_line(matrix_text, ident)

    def cell_of(ident, col):
        return split_row(line_of(ident))[col]

    row17, row06 = line_of('DLG-17'), line_of('DLG-06')
    row_mock = line_of('DLG-01')
    if None in (row17, row06, row_mock):
        print('self-test: could not find the rows to mutate', file=sys.stderr)
        return 1
    gap_neither = next(l for l in matrix_text.splitlines()
                       if l.startswith('- Neither:'))
    first_neither = DLG.findall(gap_neither)[0]
    chain06 = cell_of('DLG-06', 3)

    cases = [
        ('removed DLG-17 row',
         matrix_text.replace(row17 + '\n', '', 1), 'missing in matrix: DLG-17'),
        ('dangling path',
         _with_cell(matrix_text, 'DLG-06', 3, chain06 + ' `reference/rights_scale/sui/sources/NO_SUCH_FILE.move::x`'),
         'does not exist'),
        ('dangling symbol',
         _with_cell(matrix_text, 'DLG-06', 3, chain06 + ' `reference/rights_scale/sui/sources/rights_scale.move::no_such_fn_9f3a`'),
         'is not defined in the file'),
        ('duplicated DLG-17 row',
         matrix_text.replace(row17, row17 + '\n' + row17, 1),
         'duplicated in matrix: DLG-17'),
        ('unknown status',
         _with_cell(matrix_text, 'DLG-01', 6, 'SUFFICIENT'), 'unknown status'),
        ('mock test that does not cite the id',
         _with_cell(matrix_text, 'DLG-01', 2,
                    '`%s::test_period_boundaries`' % MOCK_TEST),
         'differ from docstring citations'),
        ('MOCK_ONLY row with a chain citation',
         _with_cell(matrix_text, 'DLG-01', 3,
                    '`reference/rights_scale/sui/sources/rights_scale.move::check_grant`'),
         'MOCK_ONLY needs none'),
        ('id dropped from the Neither line',
         matrix_text.replace(gap_neither,
                             gap_neither.replace(first_neither, '', 1), 1),
         'gap summary'),
    ]
    for name, mutated, marker in cases:
        found = find_problems(mutated, contract_text, mock_text)
        hit = [item for item in found if marker in item]
        if not hit:
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        print('self-test: detected %s (%s)' % (name, hit[0]))
    print('self-test: pass')
    return 0


def main(argv):
    texts = []
    for rel in (MATRIX, CONTRACT, MOCK_TEST):
        path = ROOT / rel
        if not path.is_file():
            print('missing ' + str(path), file=sys.stderr)
            return 1
        texts.append(path.read_text(encoding='utf-8'))
    matrix_text, contract_text, mock_text = texts
    if '--self-test' in argv:
        return self_test(matrix_text, contract_text, mock_text)
    problems = find_problems(matrix_text, contract_text, mock_text)
    if problems:
        print('delegation layer matrix check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    rows = matrix_rows(matrix_text)
    by_status = {s: 0 for s in STATUSES}
    cites = 0
    for _, cells in rows:
        by_status[STATUS_WORD.match(cells[6]).group(0)] += 1
        for col in COLUMNS:
            cites += len(parse_cell(cells[col])[1])
    print('delegation layer matrix ok: rows=%d expected=%d citations=%d %s'
          % (len(rows), len(contract_ids(contract_text)), cites,
             ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
