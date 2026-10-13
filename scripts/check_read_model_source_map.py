#!/usr/bin/env python3
"""Check the read-model source map's anchors against the cited source.

Checks ``docs/contracts/READ_MODEL_SOURCE_MAP.md``:

1. Each of the 13 owner-decided query names (READ_MODEL_QUERIES.md:15)
   appears exactly once as a first-column table key. The status cell is
   the expectation: it must be SOURCE_FOUND or SOURCE_MISSING and agree
   with the section-6 anchors — SOURCE_FOUND needs a label row of the
   `` `name` 원천 `` shape and no ``-`` anchor whose token holds
   ``def name(``; SOURCE_MISSING needs at least one such ``-`` anchor
   and no 원천 row. A row whose kind cell is ``list`` or ``point`` but
   whose name is not one of the 13 is an unknown query row, so a
   fourteenth query cannot slip in silently.
2. Every anchor row in the section-6 check table,
   ``| id | label | file | line | token |``, holds: the file exists,
   a positive integer line contains the token, and ``-`` means the
   token does not appear anywhere in the file. A failure means the
   anchor is stale, not that the source is wrong.
3. Every ``path:line`` citation in the document (bare filenames resolve
   by unique suffix, like check_status_register.py) is in range.
4. The git blob id the document cites for READ_MODEL_QUERIES.md matches
   the file's current blob.
5. The section-5 catalogue table, ``| id | label | file | expectation |``,
   carries one row per catalogue file: ``ABSENT`` forbids all 13 names
   in ``commands``; ``PRESENT: a, b`` requires exactly the listed names
   there and the rest absent. Each file in CATALOGUES must appear
   exactly once; a successor node adds a row for a new catalogue file.

Existence is checked against the checked-out working tree, which is what
CI tests. Standard library only. Wired into
``.github/workflows/protocol.yml`` as a step with no docs_only or
verified-tree guard: it runs on every non-draft execution including
docs-only and same-tree-skip runs. ``--self-test`` mutates in-memory
copies of the document and injected file contents, and requires each
check to catch its break.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_DOC = ROOT / 'docs/contracts/READ_MODEL_SOURCE_MAP.md'
QUERIES_DOC = ROOT / 'docs/contracts/READ_MODEL_QUERIES.md'
CORE_CONTRACT = 'reference/v0.3-rc1/protocol_contract.json'
FSM_CONTRACT = 'docs/contracts/openapi/fsm-command-contract.json'
CATALOGUES = (CORE_CONTRACT, FSM_CONTRACT)

# The 13 names are closed by user decision (READ_MODEL_QUERIES.md:15) and
# pinned by the blob check below. Statuses are document data, not code.
QUERY_NAMES = (
    'list_shows',
    'get_show',
    'get_booking',
    'list_bookings',
    'get_right',
    'get_presentation',
    'list_open_listings',
    'get_listing',
    'get_admission',
    'get_credential',
    'get_settlement',
    'get_credit_advance',
    'get_credit_claim',
)
QUERY_NAME_SET = frozenset(QUERY_NAMES)
QUERY_KINDS = frozenset(('list', 'point'))
STATUSES = frozenset(('SOURCE_FOUND', 'SOURCE_MISSING'))
SOURCE_LABEL = '원천'

FIRST_CELL = re.compile(r'^\|\s*([^|]+?)\s*\|')
ANCHOR_ID = re.compile(r'^[APGR]\d{2}$')
CATALOGUE_ID = re.compile(r'^C\d{2}$')
FILE_LINE = re.compile(r'([A-Za-z0-9_/.-]+\.(?:py|mjs|json|md)):(\d+(?:[-,]\d+)*)')
BLOB_CITE = re.compile(r'git blob `([0-9a-f]{40})`')


def _cells(line):
    if not line.startswith('|'):
        return None
    parts = [cell.strip() for cell in line.split('|')]
    if len(parts) < 3 or parts[0] or parts[-1]:
        return None
    return parts[1:-1]


def _unbacktick(value):
    return value.replace('`', '').strip()


def _resolve(token, root, files):
    """Find the repo-relative path for a citation token."""
    if (root / token).is_file() or (files is not None and token in files):
        return token
    matches = set()
    if files:
        matches |= {rel for rel in files if rel == token or rel.endswith('/' + token)}
    matches |= {
        str(path.relative_to(root))
        for path in root.glob('**/' + token)
        if path.is_file()
    }
    if len(matches) == 1:
        return matches.pop()
    return None


def _read(rel, root, files):
    if files is not None and rel in files:
        return files[rel]
    try:
        return (root / rel).read_text(encoding='utf-8')
    except OSError:
        return None


def _git_blob_id(data):
    header = b'blob ' + str(len(data)).encode('ascii') + b'\0'
    return hashlib.sha1(header + data).hexdigest()


def find_problems(text, root, files=None):
    """Return a list of problem strings; empty means the map passes."""
    problems = []

    queries_seen = {}
    declared = {}
    anchors = []
    catalogue_rows = []
    for line in text.splitlines():
        cells = _cells(line)
        if not cells:
            continue
        key = _unbacktick(cells[0])
        if key in QUERY_NAME_SET:
            queries_seen[key] = queries_seen.get(key, 0) + 1
            if len(cells) < 3:
                problems.append('query row has no status cell: ' + key)
                continue
            if _unbacktick(cells[1]) not in QUERY_KINDS:
                problems.append('bad kind cell for %s: %s' % (key, cells[1]))
            status = _unbacktick(cells[2])
            if status not in STATUSES:
                problems.append('unknown status for %s: %s' % (key, status))
                continue
            declared[key] = status
        elif len(cells) > 1 and _unbacktick(cells[1]) in QUERY_KINDS:
            problems.append('unknown query row: ' + key)
        elif ANCHOR_ID.match(key) and len(cells) >= 5:
            anchors.append((key, cells))
        elif CATALOGUE_ID.match(key):
            if len(cells) < 4:
                problems.append('catalogue row has no expectation cell: ' + key)
            else:
                catalogue_rows.append((key, cells))

    for name in QUERY_NAMES:
        count = queries_seen.get(name, 0)
        if count == 0:
            problems.append('missing query row: ' + name)
        elif count != 1:
            problems.append('duplicated query row: %s (%d)' % (name, count))

    seen_ids = set()
    source_labels = {name: [] for name in QUERY_NAMES}
    absence_anchors = {name: [] for name in QUERY_NAMES}
    for anchor_id, cells in anchors:
        if anchor_id in seen_ids:
            problems.append('duplicated anchor id: ' + anchor_id)
            continue
        seen_ids.add(anchor_id)
        label = _unbacktick(cells[1])
        marker = cells[3].strip()
        token = _unbacktick(cells[4])
        for name in QUERY_NAMES:
            if label == name + ' ' + SOURCE_LABEL:
                source_labels[name].append(anchor_id)
            if marker == '-' and 'def ' + name + '(' in token:
                absence_anchors[name].append(anchor_id)
        rel = _resolve(_unbacktick(cells[2]), root, files)
        if rel is None:
            problems.append(anchor_id + ': unresolved file ' + cells[2])
            continue
        body = _read(rel, root, files)
        if body is None:
            problems.append(anchor_id + ': unreadable file ' + rel)
            continue
        if marker == '-':
            if token in body:
                problems.append(
                    '%s: %s must not appear in %s' % (anchor_id, token, rel))
            continue
        if not marker.isdigit():
            problems.append(anchor_id + ': bad line field ' + marker)
            continue
        lines = body.splitlines()
        number = int(marker)
        if number < 1 or number > len(lines):
            problems.append(
                '%s: %s has %d lines, cited %d'
                % (anchor_id, rel, len(lines), number))
            continue
        if token not in lines[number - 1]:
            found = [str(i + 1) for i, row in enumerate(lines) if token in row]
            hint = ' (token at lines ' + ','.join(found) + ')' if found else ''
            problems.append(
                '%s: %s:%d lacks %s%s'
                % (anchor_id, rel, number, token, hint))

    for name in QUERY_NAMES:
        status = declared.get(name)
        if status == 'SOURCE_FOUND':
            if absence_anchors[name]:
                problems.append(
                    'status drift for %s: declared SOURCE_FOUND but absence '
                    'anchors remain: %s'
                    % (name, ','.join(absence_anchors[name])))
            if not source_labels[name]:
                problems.append(
                    'status drift for %s: declared SOURCE_FOUND but no '
                    '`%s %s` anchor' % (name, name, SOURCE_LABEL))
        elif status == 'SOURCE_MISSING':
            if source_labels[name]:
                problems.append(
                    'status drift for %s: declared SOURCE_MISSING but '
                    '`%s %s` anchors exist: %s'
                    % (name, name, SOURCE_LABEL,
                       ','.join(source_labels[name])))
            if not absence_anchors[name]:
                problems.append(
                    'status drift for %s: declared SOURCE_MISSING but no '
                    'def %s( absence anchor' % (name, name))

    for match in FILE_LINE.finditer(text):
        token, span = match.group(1), match.group(2)
        rel = _resolve(token, root, files)
        if rel is None:
            problems.append('unresolved citation file: ' + token)
            continue
        body = _read(rel, root, files)
        if body is None:
            problems.append('unreadable citation file: ' + rel)
            continue
        total = len(body.splitlines())
        for piece in re.split(r'[-,]', span):
            number = int(piece)
            if number < 1 or number > total:
                problems.append(
                    'citation out of range: %s:%d (%d lines)'
                    % (rel, number, total))

    blob = BLOB_CITE.search(text)
    if blob is None:
        problems.append('no git blob citation for READ_MODEL_QUERIES.md')
    else:
        try:
            actual = _git_blob_id(QUERIES_DOC.read_bytes())
        except OSError:
            actual = None
        if actual is None:
            problems.append('unreadable ' + str(QUERIES_DOC))
        elif blob.group(1) != actual:
            problems.append(
                'READ_MODEL_QUERIES.md blob drift: doc cites %s, actual %s'
                % (blob.group(1), actual))

    catalogue_seen = {}
    for catalogue_id, cells in catalogue_rows:
        rel = _resolve(_unbacktick(cells[2]), root, files)
        if rel is None:
            problems.append(
                catalogue_id + ': unresolved catalogue file ' + cells[2])
            continue
        catalogue_seen.setdefault(rel, []).append(catalogue_id)
        raw = _read(rel, root, files)
        if raw is None:
            problems.append('unreadable contract ' + rel)
            continue
        try:
            commands = json.loads(raw).get('commands', {})
        except json.JSONDecodeError:
            problems.append('invalid JSON: ' + rel)
            continue
        expectation = _unbacktick(cells[3])
        if expectation == 'ABSENT':
            listed = []
        elif expectation.startswith('PRESENT:'):
            listed = [piece.strip() for piece
                      in expectation[len('PRESENT:'):].split(',')
                      if piece.strip()]
            if not listed or any(n not in QUERY_NAME_SET for n in listed):
                problems.append(
                    'catalogue %s: bad PRESENT names: %s'
                    % (catalogue_id, expectation))
                continue
        else:
            problems.append(
                'catalogue %s: unknown expectation %s'
                % (catalogue_id, expectation))
            continue
        for name in QUERY_NAMES:
            present = name in commands
            if present and name not in listed:
                problems.append(
                    'catalogue %s: query name now in %s commands: %s'
                    % (catalogue_id, rel, name))
            elif not present and name in listed:
                problems.append(
                    'catalogue %s: query name %s must be in %s commands'
                    % (catalogue_id, name, rel))
    for rel, ids in catalogue_seen.items():
        if len(ids) != 1:
            problems.append(
                'duplicated catalogue expectation for %s: %s'
                % (rel, ','.join(ids)))
    for rel in CATALOGUES:
        if rel not in catalogue_seen:
            problems.append('missing catalogue expectation for ' + rel)
    return problems


def _anchor_row(text, anchor_id):
    for line in text.splitlines():
        cells = _cells(line)
        if cells and _unbacktick(cells[0]) == anchor_id:
            return line
    return None


def _query_row(text, name):
    for line in text.splitlines():
        cells = _cells(line)
        if cells and _unbacktick(cells[0]) == name:
            return line
    return None


def self_test(text):
    """Require each check to catch a deliberately broken copy."""
    base = find_problems(text, ROOT)
    if base:
        print('self-test: unmodified map already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1
    cases = []

    a01 = _anchor_row(text, 'A01')
    a03 = _anchor_row(text, 'A03')
    a04 = _anchor_row(text, 'A04')
    a05 = _anchor_row(text, 'A05')
    a06 = _anchor_row(text, 'A06')
    c01 = _anchor_row(text, 'C01')
    c02 = _anchor_row(text, 'C02')
    get_show = _query_row(text, 'get_show')
    list_shows = _query_row(text, 'list_shows')
    for label, row in (('A01', a01), ('A03', a03), ('A04', a04),
                       ('A05', a05), ('A06', a06), ('C01', c01),
                       ('C02', c02), ('get_show', get_show),
                       ('list_shows', list_shows)):
        if row is None:
            print('self-test: could not find the %s row to mutate' % label,
                  file=sys.stderr)
            return 1

    cases.append(('anchor line moved', text.replace(a01, a01.replace('| 97 |', '| 96 |'), 1),
                  'A01', None))
    cases.append(('anchor line out of range',
                  text.replace(a01, a01.replace('| 97 |', '| 99999 |'), 1),
                  'A01', None))
    cases.append(('anchor token changed',
                  text.replace(a01, a01.replace('`self._shows`', '`self._nope`'), 1),
                  'A01', None))
    cases.append(('query row dropped', text.replace(get_show + '\n', '', 1),
                  'missing query row: get_show', None))
    cases.append(('query row duplicated',
                  text.replace(get_show, get_show + '\n' + get_show, 1),
                  'duplicated query row: get_show', None))
    cases.append(('unknown query row',
                  text.replace(get_show, get_show + '\n' + get_show.replace(
                      '`get_show`', '`get_zilch`', 1), 1),
                  'unknown query row: get_zilch', None))
    cases.append(('status flipped',
                  text.replace(list_shows, list_shows.replace('SOURCE_MISSING', 'SOURCE_FOUND'), 1),
                  'status drift for list_shows', None))
    cases.append(('source label on missing query',
                  text.replace(a03, a03.replace('`list_shows` FSM 등록 id',
                                                '`list_shows` ' + SOURCE_LABEL), 1),
                  'status drift for list_shows', None))
    cases.append(('absence anchors dropped',
                  text.replace(a04 + '\n', '', 1).replace(a05 + '\n', '', 1),
                  'no def list_shows( absence anchor', None))
    cases.append(('catalogue expectation flipped',
                  text.replace(c02, c02.replace('`ABSENT`',
                                                '`PRESENT: get_show`'), 1),
                  'get_show', None))
    cases.append(('catalogue row dropped', text.replace(c01 + '\n', '', 1),
                  'missing catalogue expectation', None))
    cases.append(('rmq cite out of range', text + '\nREAD_MODEL_QUERIES.md:99999\n',
                  'out of range', None))
    blob = BLOB_CITE.search(text)
    if blob is None:
        print('self-test: no blob citation to mutate', file=sys.stderr)
        return 1
    cases.append(('blob id mismatch', text.replace(blob.group(1), '0' * 40, 1),
                  'blob drift', None))

    res = 'reference/booking_resale_admission/reservation_fsm.py'
    gates = 'reference/booking_resale_admission/mock_gates.py'
    moved = (ROOT / res).read_text(encoding='utf-8').splitlines()
    moved[704] = '    def view_gone(self, show_id: object) -> dict:'
    cases.append(('cited surface renamed', text, 'A06',
                  {res: '\n'.join(moved) + '\n'}))
    grown = (ROOT / gates).read_text(encoding='utf-8') + '\n    def list_shows(self):\n'
    cases.append(('absent surface added', text, 'A04', {gates: grown}))
    core = json.loads((ROOT / CORE_CONTRACT).read_text(encoding='utf-8'))
    core['commands']['get_show'] = {}
    cases.append(('query in core catalogue', text, 'get_show',
                  {CORE_CONTRACT: json.dumps(core)}))

    for name, mutated, marker, files in cases:
        found = find_problems(mutated, ROOT, files)
        if not any(marker in item for item in found):
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        caught = next(item for item in found if marker in item)
        print('self-test: detected %s (%s)' % (name, caught))
    print('self-test: pass')
    return 0


def main(argv):
    if not MAP_DOC.is_file():
        print('missing ' + str(MAP_DOC), file=sys.stderr)
        return 1
    text = MAP_DOC.read_text(encoding='utf-8')
    if '--self-test' in argv:
        return self_test(text)
    problems = find_problems(text, ROOT)
    if problems:
        print('read model source map check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    anchors = sum(
        1 for line in text.splitlines()
        for cells in [_cells(line)]
        if cells and ANCHOR_ID.match(_unbacktick(cells[0])))
    catalogues = sum(
        1 for line in text.splitlines()
        for cells in [_cells(line)]
        if cells and CATALOGUE_ID.match(_unbacktick(cells[0])))
    cites = len(list(FILE_LINE.finditer(text)))
    print('read model source map ok: queries=%d anchors=%d catalogues=%d citations=%d'
          % (len(QUERY_NAMES), anchors, catalogues, cites))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
