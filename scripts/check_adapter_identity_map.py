#!/usr/bin/env python3
"""Check the adapter identity evidence map against the contract and citations.

Compares two inputs:

- ``docs/contracts/ADAPTER_EVENT_IDENTITY.md``: the identity term table of
  section 2 (six first-cell names), the relation table of section 3 (four
  first cells), and the anchor strings the hardcoded rows key on (the
  ``observe_capture`` duplicate key, the operation-binding conflict rule,
  and the section-4 items).
- ``docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md``: the builder-authored
  map, one row per id, ten cells per row (id, contract item paraphrase,
  locked v4 kernel, reference mock, integration gate, readiness journal,
  Toss profile, status, missing or open, owner).

Checks, each reported on failure:

1. Ids. The contract-derived ids (section 2 terms + section 3 relations)
   plus the hardcoded rule/section-4 ids equal the map first cells, each
   exactly once; missing, duplicated and invented ids are reported. Every
   hardcoded id's contract anchor string is still present in the contract.
2. Row width. Ten cells per row.
3. Cell grammar. Each surface cell is ``none``, contains one or more
   backticked ``path::symbol`` citations with optional free text, and/or
   an ``UNDETERMINED (owner: X)`` marker. Bare ``UNDETERMINED`` without an
   owner is reported. Free-text-only cells are reported.
4. Status. One of CARRIED, PARTIAL, NO_SURFACE, UNDETERMINED, and it
   matches the cells: UNDETERMINED when any cell carries the marker;
   else CARRIED when citations exist and the missing cell is ``none``;
   PARTIAL when citations exist and a gap is named; NO_SURFACE when no
   surface cell cites anything.
5. Owner. Every ``(owner: X)`` marker and every non-CARRIED owner cell
   is non-empty; each ``;``-separated part appears verbatim in the
   contract or is the reserved literal ``k-stage5-durable-tx`` (its
   record is not on this base).
6. Citations. Each ``path::symbol`` is repo-relative, lies under its
   column's allowed patterns, is never under ``reference/v0.3-rc1/``, and
   the file exists. A symbol is a defined ``def``/``class``/module
   constant/dict key (Python), ``fn``/``struct``/``enum``/``const``/
   ``type`` (Rust), or exact text (Markdown).
7. Locked blobs. The git-blob SHA-1 of the two locked kernel files is
   recomputed and must equal the values pinned in AGENTS.md section 4.
8. Counts. The ``Counts:`` line equals the statuses recomputed from the
   map section.

Standard library only. Convenience check, not a contract gate. It reads
the cited files as text and executes none of them; it proves that a cited
name exists, not that the surface implements the contract rule.
``--self-test`` mutates in-memory copies and requires each break to be
caught.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = 'docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md'
CONTRACT = 'docs/contracts/ADAPTER_EVENT_IDENTITY.md'
KERNEL_LIB = 'runtime/crates/kix-kernel/src/lib.rs'
KERNEL_QC = 'runtime/crates/kix-kernel/tests/quarantine_capacity.rs'
LOCKED_BLOBS = {
    KERNEL_LIB: '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    KERNEL_QC: 'b607996c83a119c349f1cc90469ac1ba82764e20',
}

STATUSES = ('CARRIED', 'PARTIAL', 'NO_SURFACE', 'UNDETERMINED')
NEEDS_MISSING = ('PARTIAL', 'NO_SURFACE', 'UNDETERMINED')
EXTRA_OWNERS = {'k-stage5-durable-tx'}
CELLS = 10
STATUS_CELL, MISSING_CELL, OWNER_CELL = 7, 8, 9
# column index -> (name, allowed path patterns)
COLUMNS = {
    2: ('kernel', (r'runtime/crates/kix-kernel/(?:src/lib|tests/[a-z0-9_]+)\.rs',)),
    3: ('mock', (r'reference/(?:booking_resale_admission|settlement_f01_f03|'
                 r'credit_advance_f04|ai_delegation|provider_facts)/[a-z_]+\.py',)),
    4: ('gate', (r'integration_gate/[a-z_]+\.py',)),
    5: ('readiness', (r'readiness/[a-z_]+\.py',)),
    6: ('profile', (r'docs/contracts/PG_TOSS_CARD_PROFILE\.md',)),
}
FORBIDDEN_PREFIX = 'reference/v0.3-rc1/'
TEXT_SUFFIXES = ('.md',)
# Hardcoded row id -> anchor string that must still be in the contract.
EXTRA_ROWS = {
    'RULE-OBSERVE-KEY': 'observe_capture`의 중복 키는 `(provider, account, event_id)`다',
    'RULE-OP-BIND-CONFLICT': '결합 충돌',
    'S4-DERIVATION': '프로파일 버전',
    'S4-EVIDENCE-HASH': 'SHA-256',
    'S4-SOURCE': '의 원천',
    'S4-ALIAS': '별칭 표',
    'S4-DOMAIN-SCHEMA': '65535/65535',
}

CITATION = re.compile(r'`([^`]+)`')
STATUS_WORD = re.compile(r'[A-Z_]+')
UND_MARKER = re.compile(r'UNDETERMINED \(owner:\s*([^)]+)\)')
MAP_HEAD = '## 2. Map'
COUNTS_LINE = 'Counts:'

DEF_PATTERNS = {
    '.py': r'^\s*(?:(?:async\s+)?def|class)\s+%s\b|^\s*%s\s*[:=]',
    '.rs': r'^\s*(?:pub(?:\([^)]*\))?\s+)?(?:fn|struct|enum|const|type)\s+%s\b',
}


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def contract_ids(contract_text):
    """Expected row ids: section-2 term first cells + section-3 first cells."""
    ids = []
    section = None
    for line in contract_text.splitlines():
        if line.startswith('## '):
            section = line
            continue
        if not line.startswith('|') or section is None:
            continue
        cells = split_row(line)
        if len(cells) < 2 or not cells[0] or set(cells[0]) <= set('-:'):
            continue
        if section.startswith('## 2.'):
            m = re.match(r'`([^`]+)`', cells[0])
            if m:
                ids.append(m.group(1))
        elif section.startswith('## 3.') and cells[0] != '관계':
            ids.append(cells[0])
    return ids


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


def owner_parts_ok(parts, contract_text):
    for part in parts:
        part = part.strip()
        if not part:
            return 'empty owner part'
        if part not in EXTRA_OWNERS and part not in contract_text:
            return 'owner %r is not written in the contract' % part
    return None


def find_problems(map_text, contract_text, root=ROOT, files=None):
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

    # Locked-blob guard: the cited kernel files must stay byte-pinned.
    for rel, want in LOCKED_BLOBS.items():
        text = read(rel)
        if text is None:
            problems.append('locked file missing: %s' % rel)
        elif git_blob_sha(text) != want:
            problems.append('locked blob mismatch: %s (have %s, want %s)'
                            % (rel, git_blob_sha(text), want))

    for ident, anchor in EXTRA_ROWS.items():
        if anchor not in contract_text:
            problems.append('%s: contract anchor %r is gone' % (ident, anchor))

    expected = contract_ids(contract_text) + list(EXTRA_ROWS)
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
            problems.append('duplicated in map: %s (%d)' % (ident, counts[ident]))

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
            problems.append('%s: empty contract-item cell' % ident)

        has_und = False
        total = 0
        checked = list(COLUMNS) + [MISSING_CELL]
        for col in checked:
            cell = cells[col]
            if col != MISSING_CELL and not cell:
                problems.append('%s: empty %s cell' % (ident, COLUMNS[col][0]))
                continue
            remainder = UND_MARKER.sub('', cell)
            if 'UNDETERMINED' in remainder:
                problems.append('%s: %s cell has UNDETERMINED with no owner'
                                % (ident, COLUMNS.get(col, ('missing',))[0]))
            for m in UND_MARKER.finditer(cell):
                has_und = True
                err = owner_parts_ok(m.group(1).split(';'), contract_text)
                if err:
                    problems.append('%s: %s' % (ident, err))
            cites = parse_cell(cell)
            total += len(cites)
            if not cites and not UND_MARKER.search(cell) \
                    and cell != 'none' and col != MISSING_CELL:
                problems.append('%s: %s cell is neither none, a citation, '
                                'nor an owned UNDETERMINED'
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
                    problems.append('%s is under reference/v0.3-rc1' % where)
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
            problems.append('%s: unknown status %r' % (ident, status_cell))
        else:
            if has_und:
                want = 'UNDETERMINED'
            elif total:
                want = ('CARRIED'
                        if cells[MISSING_CELL].lower().startswith('none')
                        else 'PARTIAL')
            else:
                want = 'NO_SURFACE'
            if status != want:
                problems.append('%s: status %s should be %s for these cells'
                                % (ident, status, want))
            by_status[status] += 1

        if not cells[MISSING_CELL]:
            problems.append('%s: empty missing-or-open cell' % ident)
        elif status in NEEDS_MISSING \
                and cells[MISSING_CELL].lower().startswith('none'):
            problems.append('%s: %s row must say what is missing'
                            % (ident, status))
        if status != 'CARRIED':
            if not cells[OWNER_CELL] or cells[OWNER_CELL] == 'none':
                problems.append('%s: %s row must have an owner'
                                % (ident, status))
            else:
                err = owner_parts_ok(cells[OWNER_CELL].split(';'),
                                     contract_text)
                if err:
                    problems.append('%s: %s' % (ident, err))
        elif cells[OWNER_CELL] != 'none':
            err = owner_parts_ok(cells[OWNER_CELL].split(';'), contract_text)
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


def self_test(map_text, contract_text):
    """Require each check to catch a deliberately broken copy."""
    base = find_problems(map_text, contract_text)
    if base:
        print('self-test: unmodified map already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1

    rs_probe = 'pub fn a_probe() {}\ntype BProbe = u8;\n'
    if not (symbol_defined(rs_probe, '.rs', 'a_probe')
            and symbol_defined(rs_probe, '.rs', 'BProbe')):
        print('self-test: Rust symbol pattern failed its positive control',
              file=sys.stderr)
        return 1
    py_probe = "'x-probe': {\nKEY_PROBE = 1\ndef d_probe():\n    pass\n"
    if not (symbol_defined(py_probe, '.py', "'x-probe'")
            and symbol_defined(py_probe, '.py', 'KEY_PROBE')
            and symbol_defined(py_probe, '.py', 'd_probe')
            and not symbol_defined(py_probe, '.py', 'no_probe')):
        print('self-test: Python symbol pattern failed its positive control',
              file=sys.stderr)
        return 1

    term = 'TransmissionId'
    rule = 'RULE-OBSERVE-KEY'
    carried = 'RULE-OBSERVE-KEY'
    rows = {i: _row_line(map_text, i) for i in (term, rule, carried)}
    if None in rows.values():
        print('self-test: could not find the rows to mutate', file=sys.stderr)
        return 1
    counts_line = next(l for l in map_text.splitlines()
                       if l.startswith(COUNTS_LINE))
    kernel01 = split_row(rows[term])[2]
    cases = [
        ('removed %s row' % term,
         map_text.replace(rows[term] + '\n', '', 1),
         'missing in map: ' + term),
        ('duplicated %s row' % term,
         map_text.replace(rows[term],
                          rows[term] + '\n' + rows[term], 1),
         'duplicated in map: ' + term),
        ('invented id',
         map_text.replace(
             counts_line,
             '| FAKE-ID-9f3a | x | none | none | none | none | none '
             '| NO_SURFACE | x | TM04 |\n' + counts_line, 1),
         'invented id'),
        ('dangling path',
         _with_cell(map_text, term, 2,
                    kernel01 + ' `runtime/crates/kix-kernel/tests/no_such.rs::x`'),
         'does not exist'),
        ('dangling symbol',
         _with_cell(map_text, term, 2,
                    kernel01 + ' `runtime/crates/kix-kernel/src/lib.rs::no_such_fn_9f3a`'),
         'is not defined in the file'),
        ('citation in the wrong column',
         _with_cell(map_text, term, 3,
                    '`runtime/crates/kix-kernel/src/lib.rs::ProviderOperation`'),
         'outside the mock column paths'),
        ('citation under reference/v0.3-rc1',
         _with_cell(map_text, term, 3, '`reference/v0.3-rc1/core.py::execute`'),
         'reference/v0.3-rc1'),
        ('unknown status',
         _with_cell(map_text, term, STATUS_CELL, 'SUFFICIENT'),
         'unknown status'),
        ('status that does not match the cells',
         _with_cell(map_text, carried, STATUS_CELL, 'PARTIAL'),
         'should be'),
        ('UNDETERMINED cell with no owner',
         _with_cell(map_text, term, 6, 'UNDETERMINED; re-delivery invariance'),
         'has UNDETERMINED with no owner'),
        ('UNDETERMINED owner not in the contract',
         _with_cell(map_text, term, 6,
                    'UNDETERMINED (owner: Nobody Else); x'),
         'is not written in the contract'),
        ('non-CARRIED row with no owner',
         _with_cell(map_text, term, OWNER_CELL, 'none'),
         'must have an owner'),
        ('owner not in the contract',
         _with_cell(map_text, term, OWNER_CELL, 'Nobody Else'),
         'is not written in the contract'),
        ('NO_SURFACE row that carries a citation',
         _with_cells(map_text, 'S4-SOURCE',
                     [(2, '`runtime/crates/kix-kernel/src/lib.rs::EventKey`'),
                      (STATUS_CELL, 'NO_SURFACE')]),
         'should be'),
        ('missing citation under wrong prefix is not the only bug; '
         'free-text-only surface cell',
         _with_cell(map_text, term, 3, 'something vague but present'),
         'neither none, a citation, nor an owned UNDETERMINED'),
        ('wrong counts line',
         map_text.replace(counts_line,
                          counts_line.replace('PARTIAL=', 'PARTIAL=99', 1), 1),
         'counts line'),
        ('map cell that cites the missing cell',
         _with_cell(map_text, term, MISSING_CELL,
                    'a gap `runtime/crates/kix-kernel/src/lib.rs::ProviderOperation`'),
         'inside the missing cell'),
    ]
    for name, mutated, marker in cases:
        found = find_problems(mutated, contract_text)
        hit = [item for item in found if marker in item]
        if not hit:
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        print('self-test: detected %s (%s)' % (name, hit[0]))

    # Locked-blob guard via file injection.
    lib_text = (ROOT / KERNEL_LIB).read_text(encoding='utf-8')
    found = find_problems(map_text, contract_text,
                          files={KERNEL_LIB: lib_text + '\n// mutated\n'})
    hit = [item for item in found if 'locked blob mismatch' in item]
    if not hit:
        print('self-test: mutated kernel lib.rs was accepted',
              file=sys.stderr)
        return 1
    print('self-test: detected mutated locked blob (%s)' % hit[0])

    anchorless = contract_text.replace(EXTRA_ROWS['RULE-OBSERVE-KEY'], '(x)', 1)
    found = find_problems(map_text, anchorless)
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
    for rel in (MAP, CONTRACT):
        path = ROOT / rel
        if not path.is_file():
            print('missing ' + str(path), file=sys.stderr)
            return 1
        texts.append(path.read_text(encoding='utf-8'))
    map_text, contract_text = texts
    if '--self-test' in argv:
        return self_test(map_text, contract_text)
    problems = find_problems(map_text, contract_text)
    if problems:
        print('adapter identity evidence map check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    expected = contract_ids(contract_text) + list(EXTRA_ROWS)
    rows, _ = map_rows(map_text, set(expected))
    by_status = {s: 0 for s in STATUSES}
    cites = 0
    for _, cells in rows:
        by_status[cells[STATUS_CELL]] += 1
        for col in COLUMNS:
            cites += len(parse_cell(cells[col]))
    print('adapter identity evidence map ok: rows=%d expected=%d citations=%d %s'
          % (len(rows), len(expected), cites,
             ' '.join('%s=%d' % (s, by_status[s]) for s in STATUSES)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
