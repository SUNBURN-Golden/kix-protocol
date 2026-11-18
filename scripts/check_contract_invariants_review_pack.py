#!/usr/bin/env python3
"""Check the builder's A2 review pack against its sources using only stdlib."""
import re
import sys
from functools import cache

from check_contract_invariants_evidence_map import (
    CONTRACT_TESTS, GAP, HEADER, MAP, MAP_HEAD, OWNER, ROOT, SOURCES, SOURCE_TESTS,
    STATUS, TEST_FN, parse_cell, section_text,
)

PACK = 'docs/status/CONTRACT_INVARIANTS_REVIEW_PACK.md'
ROWS_HEADING = '## 1. A2-owned map rows'
FINDINGS_HEADING = '## 2. A2-owned findings'
A2_OWNER = 'non-author A2 reviewer'
A2_OWNER_NAME = re.compile(r'\b' + re.escape(A2_OWNER) + r'\b')
CAVEAT_START = 'Test cells are literal none or comma-separated'
CAVEAT_HEADING = '**Map provenance caveat**\n\n'

# Start at the named line and quote through the end of its paragraph.
MODEL = 'The author read the kernel source while writing'
ORACLE = 'The new `tests/contract_invariants.rs` imports neither'
PROBES = 'Read-only replay probes are reported separately'
DEFECTS = 'These five predicates detect visible overlap/accounting breaks'
FINITE = 'No finite test proves all inputs.'
CLAUSE_STARTS = {
    'S1-MODEL-PROVENANCE': (MODEL,),
    'S1-ORACLE-PATH': (ORACLE,),
    'INV-2': ('| INV-2 | ',),
    'INV-3': ('| INV-3 | ',),
    'S3-OBS-BOUNDARY': ('All attempted order IDs are recorded',),
    'S4-PROBES': (PROBES,),
    'S4-CI-HEAD': ('Execution results are attached to their exact later CI head',),
    'S5-SAFE-REJECT': (DEFECTS,),
    'S5-PRECEDENCE': (DEFECTS,),
    'S5-SHARED-ERROR': (DEFECTS,),
    'S5-FINITE': (FINITE,),
    'S5-E4-RETAINED': (FINITE,),
    'F-B2': ('| INV-3 | ', 'Separate predicate sensitivity feeds'),
    'F-B3': (PROBES,),
    'F-B4': (MODEL, FINITE),
    'F-B5': (DEFECTS, FINITE),
    'F-B6': (DEFECTS,),
}
FINDING_EVIDENCE = {
    'F-B2': 'INV-3',
    'F-B3': 'S4-PROBES',
    'F-B4': 'S1-MODEL-PROVENANCE',
    'F-B5': 'S5-SAFE-REJECT',
    'F-B6': 'S5-PRECEDENCE',
}

FIELD = re.compile(r'^\*\*([A-Za-z -]+)\*\*\n\n', re.M)
TEXT_BLOCK = re.compile(r'^```text\n(.*?)\n```$', re.M | re.S)
FINDING = re.compile(r'^- \*\*(F-B\d+) — [^\n]+$', re.M)
VERDICT = r'\b(?:ACCEPTED|APPROVED|PASS)\b'
CITATION = re.compile(
    r'(?P<path>runtime/crates/(?P<crate>kix-kernel(?:-v5)?)/tests/'
    r'(?P<target>[a-z0-9_]+)\.rs)::(?P<symbol>[a-z0-9_]+)')
EVIDENCE_ITEM = re.compile(
    r'- (Contract path|Source-informed) `([^`]+)`\n  - `([^`\n]+)`')


def read_text(path):
    # Path.read_text would collapse CRLF into LF before verbatim comparisons.
    return (ROOT / path).read_bytes().decode('utf-8')


def excerpt(text, start):
    if start.startswith('|'):
        pattern = r'^' + re.escape(start) + r'[^\n]*'
    else:
        pattern = r'^' + re.escape(start) + r'.*?(?=\n\n|\n?\Z)'
    matches = re.findall(pattern, text, re.M | re.S)
    if len(matches) != 1:
        raise ValueError('expected one source excerpt beginning ' + start)
    return matches[0]


def text_block(value):
    return '```text\n' + value + '\n```'


def map_rows(map_text):
    rows = {}
    for line in (section_text(map_text, MAP_HEAD) or '').split('\n'):
        if not line.startswith('|') or not line.endswith('|'):
            continue
        # Remove the table's separator padding, preserving the cell contents.
        cells = [cell.removeprefix(' ').removesuffix(' ')
                 for cell in line[1:-1].split('|')]
        if len(cells) != len(HEADER):
            raise ValueError('malformed map row: ' + cells[0])
        if not A2_OWNER_NAME.search(cells[OWNER]):
            continue
        ident = cells[0]
        if ident in rows:
            raise ValueError('duplicate A2 map row: ' + ident)
        rows[ident] = cells
    if not rows:
        raise ValueError('no A2-owned map rows found')
    return rows


def pack_entries(pack, heading, expected, errors):
    section = section_text(pack, heading)
    if section is None:
        errors.append('expected one pack section: ' + heading)
        return {}
    intro, *parts = re.split(r'^### ([^\n]+)\n', section, flags=re.M)
    if intro.strip():
        errors.append('unexpected text before entries in ' + heading)
    entries = {}
    for ident, body in zip(parts[::2], parts[1::2]):
        if ident in entries:
            errors.append('duplicate entry: ' + ident)
        entries[ident] = body
    for ident in sorted(expected.keys() - entries.keys()):
        errors.append('missing entry: ' + ident)
    for ident in sorted(entries.keys() - expected.keys()):
        errors.append('extra entry: ' + ident)
    return entries


def map_evidence(cells):
    return [
        (kind, path + '::' + symbol)
        for kind, column in (('Contract path', CONTRACT_TESTS),
                             ('Source-informed', SOURCE_TESTS))
        for path, symbol in parse_cell(cells[column])
    ]


def cargo_command(citation):
    return ('cargo test --manifest-path runtime/Cargo.toml -p {crate} '
            '--test {target} --locked {symbol} -- --exact').format(
                **citation.groupdict())


@cache
def rust_tests(path):
    # The source map uses this same #[test] declaration convention.
    return set(re.findall(TEST_FN % r'([a-z0-9_]+)', read_text(path), re.M))


def check_evidence(ident, evidence, expected, errors):
    actual = []
    if evidence != 'None.':
        for item in re.split(r'\n(?=- )', evidence):
            field = EVIDENCE_ITEM.fullmatch(item)
            if field is None:
                errors.append(ident + ': malformed test citation or command')
                continue
            kind, reference, command = field.groups()
            actual.append((kind, reference))
            citation = CITATION.fullmatch(reference)
            if citation is None:
                errors.append(ident + ': invalid test citation: ' + reference)
                continue
            if citation['symbol'] not in rust_tests(citation['path']):
                errors.append(ident + ': unknown test symbol: ' + reference)
            if command != cargo_command(citation):
                errors.append(ident + ': incorrect cargo command: ' + reference)
    if actual != expected:
        errors.append(ident + ': test citations differ from the map evidence')


def check_entry(ident, body, quotes, evidence, map_fields, errors):
    intro, *parts = FIELD.split(body)
    labels = parts[::2]
    expected = ['Contract clauses', *map_fields, 'Test evidence',
                'Caveat', 'Reviewer questions']
    if intro.strip() or labels != expected:
        errors.append(ident + ': expected fields ' + ', '.join(expected))
        return
    fields = {label: value.rstrip('\n') for label, value in zip(labels, parts[1::2])}
    if fields['Contract clauses'] != '\n\n'.join(map(text_block, quotes)):
        errors.append(ident + ': contract quote differs from its source')
    for label, value in map_fields.items():
        if fields[label] != value:
            errors.append(ident + ': ' + label + ' differs from the map')
    check_evidence(ident, fields['Test evidence'], evidence, errors)
    if not fields['Caveat'].strip():
        errors.append(ident + ': missing caveat')
    for number, question in enumerate(fields['Reviewer questions'].split('\n'), 1):
        if not re.fullmatch(rf'{number}\. .+\?', question):
            errors.append(ident + ': reviewer questions must be an unanswered numbered list')
            break


def check(pack, map_text, contract):
    errors = []
    rows = map_rows(map_text)
    source_findings = section_text(map_text, '## 4. Findings') or ''
    findings = {}
    for match in FINDING.finditer(source_findings):
        if A2_OWNER_NAME.search(match[0]):
            if match[1] in findings:
                errors.append('duplicate A2 map finding: ' + match[1])
            findings[match[1]] = match[0]
    if findings.keys() != FINDING_EVIDENCE.keys():
        errors.append('expected the A2-owned F-B2–F-B6 findings in the map')

    caveat = excerpt(map_text, CAVEAT_START)
    if pack.count(CAVEAT_HEADING + text_block(caveat) + '\n') != 1:
        errors.append('map provenance caveat differs from its source')
    verbatim = {*findings.values(), caveat}
    row_entries = pack_entries(pack, ROWS_HEADING, rows, errors)
    finding_entries = pack_entries(pack, FINDINGS_HEADING, findings, errors)
    for ident, body in (row_entries | finding_entries).items():
        if ident not in rows and ident not in findings:
            continue
        starts = CLAUSE_STARTS.get(ident)
        if starts is None:
            errors.append('missing contract source locator: ' + ident)
            continue
        quotes = [excerpt(contract, start) for start in starts]
        verbatim.update(quotes)
        if ident in rows:
            cells = rows[ident]
            map_fields = {'Status': cells[STATUS], 'Gap': cells[GAP]}
        else:
            map_fields = {'Map finding': text_block(findings[ident])}
            cells = rows.get(FINDING_EVIDENCE[ident])
            if cells is None:
                errors.append(ident + ': linked evidence row is absent')
                continue
        check_entry(ident, body, quotes, map_evidence(cells), map_fields, errors)

    # The source finding uses lowercase "pass" for a test observation.
    # Only exact source excerpts qualify for that exemption.
    authored_text = TEXT_BLOCK.sub(
        lambda match: '' if match[1] in verbatim else match[0], pack)
    if re.search(VERDICT, pack) or re.search(VERDICT, authored_text, re.I):
        errors.append('review verdict word in pack')
    return errors


def self_test(pack, map_text, contract):
    first_entry = re.search(r'^### S1-MODEL-PROVENANCE\n.*?(?=^### )',
                            pack, re.M | re.S)[0]
    cases = [
        ('missing A2 row', pack.replace(first_entry, '', 1),
         'missing entry: S1-MODEL-PROVENANCE'),
        ('extra row', pack.replace(first_entry, first_entry + first_entry.replace(
            '### S1-MODEL-PROVENANCE', '### EXTRA-ROW', 1), 1),
         'extra entry: EXTRA-ROW'),
        ('altered quote', pack.replace(MODEL, MODEL.lower(), 1),
         'contract quote differs'),
        ('altered status', pack.replace('**Status**\n\nPARTIAL', '**Status**\n\nOPEN', 1),
         'Status differs'),
        ('altered gap', pack.replace('Finite-trace agreement only;',
                                     'Finite trace agreement only;', 1),
         'Gap differs'),
        ('unknown symbol', pack.replace('::locked_v4_matches_independent_state_model',
                                        '::unknown_a2_test_symbol', 1),
         'unknown test symbol'),
        ('wrong command', pack.replace(' -- --exact', '', 1), 'incorrect cargo command'),
        ('altered finding', pack.replace('Unmodified observations pass.',
                                         'Unmodified observations agree.', 1),
         'Map finding differs'),
    ]
    cases.extend(('inserted ' + word, pack + '\nReview result ' + word + '\n',
                  'review verdict word') for word in ('ACCEPTED', 'APPROVED', 'PASS'))
    for label, mutant, diagnostic in cases:
        if not any(diagnostic in error for error in check(mutant, map_text, contract)):
            print('self-test failed to detect ' + label, file=sys.stderr)
            return 1
        print('self-test: detected ' + label)
    print(f'contract invariants review pack self-test: {len(cases)} negative controls OK')
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_contract_invariants_review_pack.py [--self-test]',
              file=sys.stderr)
        return 2
    try:
        pack, map_text, contract = (read_text(path) for path in
                                    (PACK, MAP, SOURCES['contract']))
        errors = check(pack, map_text, contract)
        if errors:
            print('\n'.join(errors), file=sys.stderr)
            return 1
        if argv:
            return self_test(pack, map_text, contract)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print('contract invariants review pack: row and finding evidence checks OK')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
