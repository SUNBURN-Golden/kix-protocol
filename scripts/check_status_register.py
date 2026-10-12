#!/usr/bin/env python3
"""Check that repo paths named in the capability register exist.

Runs three checks on docs/status/CURRENT_CAPABILITY_REGISTER.md:

1. Every repository path named inside backticks or in a markdown link
   target exists. A token is treated as a path candidate when it contains
   '/' or ends in a known source/document extension; command flags,
   pure hex ids (SHAs), placeholders like <base>:<path>, and bare words
   such as ``python3`` or ``readiness.test_faults`` are skipped.
   ``{a,b}`` brace lists are expanded, a trailing ``:NNN`` line number is
   stripped, glob patterns (``test_*.py``) are matched, and a token that
   is not root-relative may resolve by unique suffix anywhere in the
   tree (e.g. ``support/model_v4.rs``). A suffix match that resolves to
   more than one location fails as ambiguous; a bare filename only needs
   to exist somewhere.
2. Every ``EV-*`` id referenced anywhere in the document is defined as a
   first-column key of the shared evidence index table.
3. Each of the 32 original requirement ids (E01-E06, P01-P06, B01-B05,
   R01-R05, F01-F05, M01-M05) appears exactly once as a first-column
   table-row key.

Existence is checked against the checked-out working tree, which is what
CI tests. Standard library only. Not wired into CI; that is a follow-up
candidate. ``--self-test`` mutates an in-memory copy of the register and
requires each check to catch its break.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / 'docs/status/CURRENT_CAPABILITY_REGISTER.md'

PATH_EXTENSIONS = frozenset({
    '.py', '.md', '.rs', '.move', '.json', '.ts', '.mjs', '.circom',
    '.h', '.sh', '.yml', '.yaml', '.toml', '.txt', '.csv', '.patch',
})
GLOB_CHARS = frozenset('*?[')
ORIGINAL32 = (
    ['E0%d' % i for i in range(1, 7)]
    + ['P0%d' % i for i in range(1, 7)]
    + ['B0%d' % i for i in range(1, 6)]
    + ['R0%d' % i for i in range(1, 6)]
    + ['F0%d' % i for i in range(1, 6)]
    + ['M0%d' % i for i in range(1, 6)]
)
EV_REFERENCE = re.compile(r'EV-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*')
EV_DEFINITION = re.compile(r'^\|\s*(EV-[A-Z0-9-]+)\s*\|', re.MULTILINE)
HEX_ID = re.compile(r'[0-9a-fA-F]{7,}')


def _expand_braces(token):
    """Expand one ``{a,b}`` group at a time into a list of variants."""
    start = token.find('{')
    if start == -1:
        return [token]
    depth = 0
    for index in range(start, len(token)):
        if token[index] == '{':
            depth += 1
        elif token[index] == '}':
            depth -= 1
            if depth == 0:
                head = token[:start]
                tail = token[index + 1:]
                variants = []
                for part in token[start + 1:index].split(','):
                    variants += _expand_braces(head + part + tail)
                return variants
    return [token]


def _candidate_tokens(text):
    """Raw path-looking tokens from backtick spans and link targets."""
    tokens = []
    for span in re.findall(r'`([^`\n]+)`', text):
        tokens += span.split()
    for target in re.findall(r'\]\(([^)\s]+)\)', text):
        tokens.append(target.split('#', 1)[0])
    return tokens


def _is_path_candidate(token):
    """Decide whether a raw token should be checked as a repo path."""
    if not token or token.startswith('-'):
        return False
    if '://' in token or any(ch in token for ch in '<>=$'):
        return False
    if HEX_ID.fullmatch(token):
        return False
    if '/' in token:
        return True
    return Path(token).suffix.lower() in PATH_EXTENSIONS


def _resolve(token, root):
    """Return (found, matches) for one expanded token under ``root``."""
    if any(ch in token for ch in GLOB_CHARS):
        matches = set(root.glob(token)) | set(root.glob('**/' + token))
        return bool(matches), matches
    if (root / token).exists():
        return True, {root / token}
    matches = set(root.glob('**/' + token))
    return bool(matches), matches


def find_problems(text, root):
    """Return a list of problem strings; empty means the register passes."""
    problems = []

    seen = set()
    for raw in _candidate_tokens(text):
        token = re.sub(r':\d+$', '', raw).rstrip('/')
        if not _is_path_candidate(token):
            continue
        for variant in _expand_braces(token):
            if variant in seen:
                continue
            seen.add(variant)
            found, matches = _resolve(variant, root)
            if not found:
                problems.append('path not found: ' + variant)
            elif (
                not any(ch in variant for ch in GLOB_CHARS)
                and '/' in variant
                and not (root / variant).exists()
                and len(matches) > 1
            ):
                locations = ', '.join(
                    sorted(str(item.relative_to(root)) for item in matches))
                problems.append('ambiguous path ' + variant + ' matches: ' + locations)

    defined = set(EV_DEFINITION.findall(text))
    for reference in sorted(set(EV_REFERENCE.findall(text)) - defined):
        problems.append('undefined evidence id referenced: ' + reference)

    counts = {item: 0 for item in ORIGINAL32}
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        cells = line.split('|')
        if len(cells) < 2:
            continue
        first = cells[1].strip().split()
        if first and first[0] in counts:
            counts[first[0]] += 1
    for item in ORIGINAL32:
        if counts[item] != 1:
            problems.append(
                'original id %s appears %d times as a row key (want 1)'
                % (item, counts[item]))
    return problems


def self_test(text):
    """Require each check to catch a deliberately broken register copy."""
    base = find_problems(text, ROOT)
    if base:
        print('self-test: unmodified register already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1
    cases = []

    broken_path = text + '\n`docs/status/NO_SUCH_FILE_9f3a.md`\n'
    cases.append(('missing path', broken_path, 'NO_SUCH_FILE_9f3a.md'))

    broken_ev = text + '\nEV-XXX\n'
    cases.append(('undefined EV id', broken_ev, 'EV-XXX'))

    e01_row = None
    for line in text.splitlines():
        cells = line.split('|')
        if line.startswith('|') and len(cells) > 1 and cells[1].strip().split()[:1] == ['E01']:
            e01_row = line
            break
    if e01_row is None:
        print('self-test: could not find the E01 row to mutate', file=sys.stderr)
        return 1
    cases.append(('dropped original id', text.replace(e01_row + '\n', '', 1), 'E01'))
    cases.append(('duplicated original id', text.replace(e01_row, e01_row + '\n' + e01_row, 1), 'E01'))

    for name, mutated, marker in cases:
        found = find_problems(mutated, ROOT)
        if not any(marker in item for item in found):
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        caught = next(item for item in found if marker in item)
        print('self-test: detected %s (%s)' % (name, caught))
    print('self-test: pass')
    return 0


def main(argv):
    if not REGISTER.is_file():
        print('missing ' + str(REGISTER), file=sys.stderr)
        return 1
    text = REGISTER.read_text(encoding='utf-8')
    if '--self-test' in argv:
        return self_test(text)
    problems = find_problems(text, ROOT)
    if problems:
        print('capability register check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    print(
        'capability register ok: paths=%d ev_ids=%d original32=%d'
        % (len([t for t in _candidate_tokens(text) if _is_path_candidate(re.sub(r":\d+$", "", t).rstrip("/"))]),
           len(set(EV_DEFINITION.findall(text))),
           len(ORIGINAL32))
    )
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
