#!/usr/bin/env python3
"""Check the evidence-map index with stdlib-only, read-only snapshots.

Counts retain each map's vocabulary. This checks textual consistency, not
semantic test coverage, review, acceptance, grades or production readiness.
"""
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLLUP = 'docs/status/EVIDENCE_MAP_ROLLUP.md'
CONTRACT_GLOBS = ('docs/contracts/**/*', 'runtime/*_V1.md')
COUNTS = 'Counts:'
TOKEN = re.compile(r'([A-Za-z0-9_-]+)=(\d+)')
CONTRACT_HEADER = ['Contract', 'Evidence map', 'Checker', 'Counts (verbatim)',
                   'Open-row owners', 'No-map reason']
CROSS_HEADER = ['Map', 'Checker', 'Counts (verbatim)', 'Open-row owners',
                'Contracts read']
# The BRA-RES9 rows sit in the earlier key table, outside the final table.
# Mirror check_contract_error_codes.py's ROW_START, without importing it.
ROW_SCOPE_OVERRIDES = {
    'docs/status/CONTRACT_ERROR_CODE_COVERAGE.md': re.compile(
        r'^\|\s*(SET|BRA-RES9|BRA-RES|BRA-ADM|BRA|F04-FSM|F04|AID)'
        r'\s*\|\s*`[A-Z][A-Z0-9_]+`\s*\|'),
}
SOURCE_PATH = re.compile(r'`((?:docs/status/|scripts/)[A-Za-z0-9_./-]+)`')


def cells(line):
    return [cell.strip() for cell in line.strip().strip('|').split('|')]


def tables(lines):
    """Return contiguous pipe tables, preserving cell contents."""
    result, block = [], []
    for line in [*lines, '']:
        if line.startswith('|'):
            block.append(cells(line))
        elif block:
            result.append(block)
            block = []
    return result


def clean(value):
    return value.replace('`', '').replace('**', '').strip()


def map_snapshot(path, text):
    """Return the exact Counts line, distinct owner cells, and errors."""
    errors = []
    lines = text.splitlines()
    positions = [i for i, line in enumerate(lines) if line.startswith(COUNTS)]
    if len(positions) != 1:
        return None, [], ['map Counts line count: %s: %d' % (path, len(positions))]
    position = positions[0]
    count_line = lines[position]
    preceding = tables(lines[:position])
    if not preceding or 'Status' not in preceding[-1][0]:
        return count_line, [], ['counts disagree with table: %s: no Status table' % path]
    table = preceding[-1]
    header = table[0]
    if path in ROW_SCOPE_OVERRIDES:
        rows = [cells(line) for line in lines
                if ROW_SCOPE_OVERRIDES[path].match(line)]
    else:
        rows = table[2:]
    if (len(table) < 2 or not all(re.fullmatch(r':?-+:?', cell)
                                for cell in table[1])
            or not rows or any(len(row) != len(header) for row in rows)):
        return count_line, [], ['counts disagree with table: %s: malformed table' % path]

    status_index = header.index('Status')
    statuses = Counter(clean(row[status_index]) for row in rows)
    tokens = TOKEN.findall(count_line[len(COUNTS):])
    values = {key: int(value) for key, value in tokens}
    if (not tokens or len(values) != len(tokens)
            or TOKEN.sub('', count_line[len(COUNTS):]).strip()):
        errors.append('counts disagree with table: %s: malformed Counts tokens' % path)
    for status, tally in sorted(statuses.items()):
        if values.get(status) != tally:
            errors.append('counts disagree with table: %s: %s=%d is required'
                          % (path, status, tally))
    for key, value in tokens:
        value = int(value)
        if key == 'rows':
            candidates = {len(rows)}
        elif key in statuses:
            candidates = {statuses[key]}
        else:
            candidates = set()
            for i, name in enumerate(header):
                if i == status_index:
                    continue
                column = [clean(row[i]) for row in rows]
                tally = column.count(key)
                if tally:
                    candidates.add(tally)
                if key == name.upper():
                    candidates.add(sum(cell.lower() not in ('no', 'none')
                                       for cell in column))
            if not candidates:
                candidates = {0}
        if value not in candidates:
            errors.append('counts disagree with table: %s: %s=%d, expected %s'
                          % (path, key, value, sorted(candidates)))

    owner_columns = [i for i, name in enumerate(header)
                     if re.search(r'\bowner\b', name, re.I)]
    if not owner_columns:
        owners = ['no owner column']
    else:
        owners = list(dict.fromkeys(row[owner_columns[-1]] for row in rows
                                    if row[owner_columns[-1]] != 'none'))
        if any('<br>' in owner for owner in owners):
            errors.append('owners mismatch: %s: source owner contains <br>' % path)
    return count_line, owners, errors


def code_items(cell, label, errors):
    if cell == 'none':
        return []
    parts = cell.split('<br>')
    if any(not re.fullmatch(r'`[^`]+`', part.strip()) for part in parts):
        errors.append('arity mismatch: %s: expected backticked entries' % label)
        return []
    # Only the outside table padding is stripped; Counts bytes are preserved.
    return [part.strip()[1:-1] for part in parts]


def check(contracts, files):
    """Return deterministic errors over a contract set and path/text snapshot."""
    errors = []
    rollup = files.get(ROLLUP, '')
    parsed = tables(rollup.splitlines())
    selected = []
    for header in (CONTRACT_HEADER, CROSS_HEADER):
        matches = [table for table in parsed if table[0] == header]
        if len(matches) != 1:
            errors.append('arity mismatch: roll-up requires exactly one %s table' % header[0])
        selected.append(matches[0][2:] if len(matches) == 1 else [])
    contract_rows, cross_rows = selected
    listed = []
    cache = {}

    def check_maps(label, map_cell, checker_cell, copies_cell, owner_cell, reason=None):
        maps = code_items(map_cell, label, errors)
        checkers = code_items(checker_cell, label, errors)
        copies = code_items(copies_cell, label, errors)
        for checker in checkers:
            if checker not in files:
                errors.append('missing checker: %s: %s' % (label, checker))
        if not maps:
            if reason is None or not reason.strip() or reason == 'none':
                errors.append('no-map row lacks reason: ' + label)
            if copies or owner_cell != 'none':
                errors.append('arity mismatch: %s: no-map row has Counts/owners' % label)
            return
        if reason is not None and reason != 'none':
            errors.append('arity mismatch: %s: mapped row has a no-map reason' % label)
        if len(maps) != len(checkers) or len(maps) != len(copies):
            errors.append('arity mismatch: ' + label)
        owners = []
        all_owners_known = True
        for i, path in enumerate(maps):
            if path not in files:
                errors.append('missing map: %s: %s' % (label, path))
                all_owners_known = False
                continue
            if path not in cache:
                count_line, map_owners, map_errors = map_snapshot(path, files[path])
                cache[path] = (count_line, map_owners)
                errors.extend(map_errors)
            count_line, map_owners = cache[path]
            if count_line is not None and (i >= len(copies) or copies[i] != count_line):
                errors.append('stale Counts copy: %s: %s' % (label, path))
            owners.extend(map_owners)
        expected = set(owners) or {'none'}
        actual = {part.strip() for part in owner_cell.split('<br>')}
        if all_owners_known and actual != expected:
            errors.append('owners mismatch: ' + label)

    for row in contract_rows:
        if len(row) != len(CONTRACT_HEADER):
            errors.append('arity mismatch: contract row')
            continue
        paths = code_items(row[0], 'Contract', errors)
        if len(paths) != 1:
            errors.append('arity mismatch: Contract must name one file')
        listed.extend(paths)
        check_maps(row[0], *row[1:])
    tallies = Counter(listed)
    for path in sorted(contracts - tallies.keys()):
        errors.append('contract missing from roll-up: ' + path)
    for path, tally in sorted(tallies.items()):
        if tally > 1:
            errors.append('contract listed more than once: ' + path)
        if path not in contracts:
            errors.append('roll-up lists non-contract: ' + path)
    for row in cross_rows:
        if len(row) != len(CROSS_HEADER):
            errors.append('arity mismatch: cross-contract row')
            continue
        check_maps(row[0], *row[:4])
        for path in code_items(row[4], 'Contracts read', errors):
            if path not in contracts:
                errors.append('roll-up lists non-contract: ' + path)
    # Also check prose citations, including the maps deliberately not rolled up.
    for path in sorted(set(SOURCE_PATH.findall(rollup))):
        if path.startswith('scripts/') and path not in files:
            message = 'missing checker: roll-up: ' + path
            errors.append(message)
    return errors


def collect(root):
    """Collect regular contract files and only the index's cited map/checker files."""
    contracts = {path.relative_to(root).as_posix()
                 for pattern in CONTRACT_GLOBS for path in root.glob(pattern)
                 if path.is_file()}
    files = {ROLLUP: (root / ROLLUP).read_bytes().decode('utf-8')}
    for name in set(SOURCE_PATH.findall(files[ROLLUP])):
        # Never follow a citation outside the repository.
        if '..' not in Path(name).parts and (root / name).is_file():
            files[name] = (root / name).read_bytes().decode('utf-8')
    return contracts, files


def self_test():
    contract = 'docs/contracts/EXAMPLE.md'
    map_path = 'docs/status/EXAMPLE_EVIDENCE_MAP.md'
    checker = 'scripts/check_example.py'
    count = 'Counts: rows=2 COVERED=1 OPEN=1 ABSENT=0'
    source = ('| ID | Status | Owner |\n|---|---|---|\n'
              '| X | `COVERED` | none |\n| Y | **OPEN** | User |\n\n' + count + '\n')
    row = '| `%s` | `%s` | `%s` | `%s` | User | none |' % (
        contract, map_path, checker, count)
    rollup = ('| ' + ' | '.join(CONTRACT_HEADER) + ' |\n'
              '|---|---|---|---|---|---|\n' + row + '\n\n'
              '| ' + ' | '.join(CROSS_HEADER) + ' |\n|---|---|---|---|---|\n')
    contracts = {contract}
    files = {ROLLUP: rollup, map_path: source, checker: '# fixture\n'}
    if check(contracts, files):
        print('self-test: baseline failed', check(contracts, files), file=sys.stderr)
        return 1

    def changed_rollup(text):
        return dict(files, **{ROLLUP: text})

    def changed_map(text):
        return dict(files, **{map_path: text})

    cases = [
        ('missing contract', contracts | {'runtime/EXTRA_V1.md'}, files,
         'contract missing from roll-up:'),
        ('stale copied Counts line', contracts,
         changed_rollup(rollup.replace('COVERED=1', 'COVERED=0')), 'stale Counts copy:'),
        ('Counts disagree with table', contracts,
         changed_map(source.replace('COVERED=1', 'COVERED=2')), 'counts disagree with table:'),
        ('missing map path', contracts, {k: v for k, v in files.items() if k != map_path},
         'missing map:'),
        ('duplicate contract', contracts, changed_rollup(rollup.replace(row, row + '\n' + row)),
         'contract listed more than once:'),
        ('non-contract row', set(), files, 'roll-up lists non-contract:'),
        ('missing checker', contracts, {k: v for k, v in files.items() if k != checker},
         'missing checker:'),
        ('unlisted status', contracts, changed_map(source.replace('**OPEN**', 'NEW_STATUS')),
         'counts disagree with table:'),
        ('nonzero unexplained token', contracts,
         changed_map(source.replace('ABSENT=0', 'ABSENT=1')), 'counts disagree with table:'),
        ('duplicate Counts line', contracts, changed_map(source + count + '\n'),
         'map Counts line count:'),
        ('owners mismatch', contracts, changed_rollup(rollup.replace('| User |', '| Astra |')),
         'owners mismatch:'),
        ('arity mismatch', contracts,
         changed_rollup(rollup.replace('`' + checker + '`', 'none')), 'arity mismatch:'),
        ('no-map row without reason', contracts,
         changed_rollup(rollup.replace(row, '| `%s` | none | none | none | none | none |' % contract)),
         'no-map row lacks reason:'),
        ('source owner has break', contracts, changed_map(source.replace('| User |', '| User<br>Astra |')),
         'owners mismatch:'),
        ('Counts trailing whitespace', contracts, changed_map(source.replace(count, count + ' ')),
         'stale Counts copy:'),
        ('missing Status table', contracts, changed_map(source.replace('Status', 'Result')),
         'counts disagree with table:'),
    ]
    for label, contract_set, snapshot, marker in cases:
        if not any(error.startswith(marker) for error in check(contract_set, snapshot)):
            print('self-test: failed to detect ' + label, file=sys.stderr)
            return 1
        print('self-test: detected ' + label)

    # Positive controls: multiple maps, no-map reason, alternate owner header,
    # ownerless cross-contract table, and the split error-code table layout.
    other = 'docs/status/OTHER_EVIDENCE_MAP.md'
    multi = changed_rollup(rollup.replace('`' + map_path + '`', '`%s`<br>`%s`' % (map_path, other))
                           .replace('`' + checker + '`', '`%s`<br>`%s`' % (checker, checker))
                           .replace('`' + count + '`', '`%s`<br>`%s`' % (count, count)))
    multi[other] = source.replace('Owner', 'Decision / owner')
    no_map = changed_rollup(rollup.replace(row, '| `%s` | none | `%s` | none | none | input sheet |'
                                         % (contract, checker)))
    cross_path = next(iter(ROW_SCOPE_OVERRIDES))
    cross_count = 'Counts: SET=1 BRA-RES9=1 rows=2 RAISED=2 ASSERTED=2 COVERED=2 CLASS_C=0'
    cross = ('| Key | Contract | Suite |\n|---|---|---|\n'
             '| BRA-RES9 | `INLINE_CODE` | x | y | COVERED | none |\n\n'
             '| Key | Code | Raised | Asserted | Status | Note |\n|---|---|---|---|---|---|\n'
             '| SET | `TABLE_CODE` | x | y | COVERED | none |\n\n' + cross_count + '\n')
    cross_files = changed_rollup(rollup + '| `%s` | `%s` | `%s` | no owner column | `%s` |\n'
                                 % (cross_path, checker, cross_count, contract))
    cross_files[cross_path] = cross
    for snapshot in (multi, no_map, cross_files):
        if check(contracts, snapshot):
            print('self-test: positive control failed', check(contracts, snapshot), file=sys.stderr)
            return 1
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        fixture = {**files, contract: '# contract\n', 'runtime/SECOND_V1.md': '# normative\n',
                   'docs/contracts/nested/pin.json': '{}\n'}
        for name, text in fixture.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode('utf-8'))
        (root / 'docs/contracts/directory.md').mkdir()
        (root / 'runtime/ignored.md').write_text('ignored', encoding='utf-8')
        expected = contracts | {'runtime/SECOND_V1.md', 'docs/contracts/nested/pin.json'}
        if collect(root) != (expected, files):
            print('self-test: collect fixture failed', file=sys.stderr)
            return 1
    print('self-test: pass (%d negative controls)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_evidence_map_rollup.py [--self-test]', file=sys.stderr)
        return 2
    if argv:
        return self_test()
    try:
        contracts, files = collect(ROOT)
    except (OSError, UnicodeError) as error:
        print('roll-up input error: ' + str(error), file=sys.stderr)
        return 1
    errors = check(contracts, files)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print('evidence map roll-up ok: contracts=%d; textual index only' % len(contracts))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
