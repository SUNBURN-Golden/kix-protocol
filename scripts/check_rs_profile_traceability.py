#!/usr/bin/env python3
"""Check RS-C/IM id traceability between the rights-scale blueprint and profile.

Compares two documents:

- ``docs/blueprints/rights-scale-v1/README.md`` — defines RS-C01..RS-C17
  (section 4 predicate table) and IM-01..IM-30 (section 2 impact map).
- ``docs/contracts/RIGHTS_SCALE_PROFILE.md`` — the RS-0 draft contract,
  which must carry each id exactly once (section 8 and section 12).

An id counts when it is the first cell of a markdown table row
(``| ID | ...``). Anchoring on the first cell keeps test ids such as
``RS-C01-T1`` and in-text mentions such as ``IM-01~IM-08`` out of the
count. Expected sets are RS-C01..RS-C17 and IM-01..IM-30 on both sides.

Reports each of: missing in blueprint, duplicated in blueprint, extra in
blueprint, missing in profile, duplicated in profile, extra in profile.
Exits 0 when every expected id appears exactly once on both sides and no
extra ids are present; exits 1 printing each discrepancy otherwise.

Standard library only. Wired into ``.github/workflows/protocol.yml`` as a
step with no docs_only or verified-tree guard: it runs on every non-draft
execution including docs-only and same-tree-skip runs. ``--self-test``
mutates in-memory copies and requires each check to catch its break (a
removed id must be reported).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / 'docs/blueprints/rights-scale-v1/README.md'
PROFILE = ROOT / 'docs/contracts/RIGHTS_SCALE_PROFILE.md'

EXPECTED = (
    ['RS-C%02d' % i for i in range(1, 18)]
    + ['IM-%02d' % i for i in range(1, 31)]
)
ID_KEY = re.compile(r'^(RS-C\d{2}|IM-\d{2})$')
FIRST_CELL = re.compile(r'^\|\s*([^|]+?)\s*\|')


def row_key_counts(text):
    """Count each RS-C/IM id used as a first-column table-row key."""
    counts = {item: 0 for item in EXPECTED}
    extras = {}
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        match = FIRST_CELL.match(line)
        if not match:
            continue
        first = match.group(1).strip().split()
        if not first or not ID_KEY.match(first[0]):
            continue
        key = first[0]
        if key in counts:
            counts[key] += 1
        else:
            extras[key] = extras.get(key, 0) + 1
    return counts, extras


def find_problems(blueprint_text, profile_text):
    """Return a list of problem strings; empty means both sides pass."""
    problems = []
    for label, text in (('blueprint', blueprint_text), ('profile', profile_text)):
        counts, extras = row_key_counts(text)
        for item in EXPECTED:
            if counts[item] == 0:
                problems.append('missing in %s: %s' % (label, item))
            elif counts[item] != 1:
                problems.append(
                    'duplicated in %s: %s (%d)' % (label, item, counts[item]))
        for key in sorted(extras):
            problems.append('extra in %s: %s (%d)' % (label, key, extras[key]))
    return problems


def _row_line(text, key):
    """First table-row line whose first cell is exactly ``key``."""
    for line in text.splitlines():
        match = FIRST_CELL.match(line)
        if match and match.group(1).strip() == key:
            return line
    return None


def self_test(blueprint_text, profile_text):
    """Require each check to catch a deliberately broken copy."""
    base = find_problems(blueprint_text, profile_text)
    if base:
        print('self-test: unmodified pair already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1
    cases = []

    for key, side in (('RS-C01', 'profile'), ('IM-01', 'profile'),
                      ('RS-C03', 'blueprint')):
        source = profile_text if side == 'profile' else blueprint_text
        row = _row_line(source, key)
        if row is None:
            print('self-test: could not find the %s row in %s to mutate'
                  % (key, side), file=sys.stderr)
            return 1
        removed = source.replace(row + '\n', '', 1)
        duplicated = source.replace(row, row + '\n' + row, 1)
        if side == 'profile':
            cases.append(('removed %s from profile' % key,
                          blueprint_text, removed, 'missing in profile: ' + key))
            cases.append(('duplicated %s in profile' % key,
                          blueprint_text, duplicated, 'duplicated in profile: ' + key))
        else:
            cases.append(('removed %s from blueprint' % key,
                          removed, profile_text, 'missing in blueprint: ' + key))
            cases.append(('duplicated %s in blueprint' % key,
                          duplicated, profile_text, 'duplicated in blueprint: ' + key))

    extra = profile_text + '\n| RS-C99 | extra row | RS-C99-T1 | RS-1 |\n' \
        + '| IM-99 | extra row | keep |\n'
    cases.append(('extra ids in profile', blueprint_text, extra,
                  'extra in profile: RS-C99'))

    for name, mutated_blueprint, mutated_profile, marker in cases:
        found = find_problems(mutated_blueprint, mutated_profile)
        if not any(marker in item for item in found):
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        caught = next(item for item in found if marker in item)
        print('self-test: detected %s (%s)' % (name, caught))
    print('self-test: pass')
    return 0


def main(argv):
    for path in (BLUEPRINT, PROFILE):
        if not path.is_file():
            print('missing ' + str(path), file=sys.stderr)
            return 1
    blueprint_text = BLUEPRINT.read_text(encoding='utf-8')
    profile_text = PROFILE.read_text(encoding='utf-8')
    if '--self-test' in argv:
        return self_test(blueprint_text, profile_text)
    problems = find_problems(blueprint_text, profile_text)
    if problems:
        print('rs profile traceability check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    blueprint_counts, _ = row_key_counts(blueprint_text)
    profile_counts, _ = row_key_counts(profile_text)
    print('rs profile traceability ok: blueprint=%d profile=%d expected=%d'
          % (sum(blueprint_counts.values()),
             sum(profile_counts.values()),
             len(EXPECTED)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
