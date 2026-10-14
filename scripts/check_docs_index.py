#!/usr/bin/env python3
"""Check that active documentation files are referenced by the doc index.

Every regular file under the active document subtrees

- ``docs/contracts/**``
- ``docs/decisions/**``
- ``docs/status/*.md``            (top level only; release-bodies and the
                                  sui-commit evidence snapshots stay out)
- ``docs/operations/**``
- ``docs/adr/**``
- ``docs/reviews/**``
- ``docs/blueprints/**/README.md``
- ``validation/*/README.md``          (record pointers only; the evidence
                                      artifacts beside them stay out)

must be the target of at least one markdown link (``](target)``) in
``docs/README.md`` or ``docs/DEVELOPMENT_PLAN.md``, unless it is named in
``ALLOWLIST`` below. Link targets are resolved relative to ``docs/``
(both index files live there); ``#fragments`` and external URLs are
ignored, and matching is exact-file only — a link to a directory or a
bare name in prose does not index a file. The index files themselves are
not in the scanned subtrees. Intentionally unindexed material
(historical root docs, ``docs/tasks/``, ``docs/status/release-bodies/``,
evidence snapshots, and the artifacts beside a validation README) sits
outside the scan patterns rather than in the allowlist; the allowlist
additionally holds the validation records that predate the scan itself
(KIX audit #6, 2026-10) as preserved evidence instead of retroactive
index entries.

Reports each of: a scanned file no index link reaches, an allowlist
entry that names a file outside the scanned set, and a resolved index
link that points into a scanned subtree at a target that does not exist
(a renamed or deleted document).

Exits 0 when there is nothing to report; exits 1 printing each problem
otherwise. Standard library only. Wired into the ``Stdlib offline
document checks`` step of ``.github/workflows/protocol.yml``, which has
no docs_only or verified-tree guard: it runs on every non-draft
execution including docs-only and same-tree-skip runs. ``--self-test``
mutates in-memory copies and requires each check to catch its break (a
removed index link must be reported).
"""
import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_FILES = (
    ROOT / 'docs/README.md',
    ROOT / 'docs/DEVELOPMENT_PLAN.md',
)
SCAN_PATTERNS = (
    'docs/contracts/**/*',
    'docs/decisions/**/*',
    'docs/status/*.md',
    'docs/operations/**/*',
    'docs/adr/**/*',
    'docs/reviews/**/*',
    'docs/blueprints/**/README.md',
    'validation/*/README.md',
)
# Scanned files deliberately not index-linked: machine-readable pins
# reached through the linked human-readable docs/contracts/openapi/README.md
# and checked mechanically by scripts/check_openapi_contract.py and
# scripts/check_integration_gate_openapi.py.
# Validation records that predate the validation-record scan (KIX audit
# #6, 2026-10) are kept below as preserved evidence rather than
# retroactively indexed; a later index-sync node that links one of them
# from an index file must also drop its entry here.
ALLOWLIST = {
    'docs/contracts/openapi/fsm-command-contract.json':
        'machine-readable command pin next to the linked openapi README',
    'docs/contracts/openapi/kix-protocol.contract-only.openapi.json':
        'machine-readable OpenAPI pin next to the linked openapi README',
    'docs/contracts/openapi/kix-protocol.integration-gate.openapi.json':
        'machine-readable OpenAPI pin next to the linked openapi README',
    'validation/2026-09-11/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-13/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-14/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-14-archive/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-14-commerce/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-14-foundation/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-14-recovery/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-14-storage/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-15-audit-fix/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-15-ktx-r1-audit-fix/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-15-r1-observation-slots/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-18-contract-edge-cases/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-19-task-002-lifecycle-precedence/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-19-task-003a-e4-model-schema/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-19-task-003b-e4-property-expansion/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-21-task-003c1-evidence-gates/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-23-cp-boundary-003/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-26-prod-readiness-infra/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-26-wave2-rights-issuance/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-26-wave3-settlement-f01-f03/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-26-wave4-booking-resale-admission/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-26-wave5-credit-f04-mock/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-09-28-main-state-catchup/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-10-05-k1-e4-residual-review/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-10-09-audit3-tl-docs-plan-index-sync/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-10-09-audit4-audit4-plan-s5-index-f04-criteria-toss-p/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-10-09-audit4-tl-plan-index-register-sync/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-10-12-register-nontl-rows-sync/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-10-12-rs0-review-pack/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-10-13-astra-decision-sheets-listvalues-v5-rs0/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-10-13-i12-review-pack/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-10-13-offline-doc-checks-ci/README.md':
        'historical record pre-dating the validation-record scan '
        '(KIX audit #6); not retroactively indexed',
    'validation/2026-10-14-audit6-plan-index-sync/README.md':
        'merged audit6 fix-node record; plan/index sync row belongs to '
        'a later index-sync node',
    'validation/2026-10-14-register-sync-v5-rs/README.md':
        'merged audit6 fix-node record; plan/index sync row belongs to '
        'a later index-sync node',
    'validation/2026-10-14-rs-profile-revision-log-0-2/README.md':
        'merged audit6 fix-node record; plan/index sync row belongs to '
        'a later index-sync node',
    'validation/2026-10-14-rs1-state-answer-archive/README.md':
        'merged audit6 fix-node record; plan/index sync row belongs to '
        'a later index-sync node',
}
# Prefixes a resolved link target must sit under for the missing-target
# (broken index link) check.
SCANNED_PREFIXES = (
    'docs/contracts/', 'docs/decisions/', 'docs/status/',
    'docs/operations/', 'docs/adr/', 'docs/reviews/', 'docs/blueprints/',
    'validation/',
)
LINK_TARGET = re.compile(r'\]\(([^)\s]+)\)')


def collect_referenced(texts):
    """Repo-relative paths the index links point at; fragments/URLs out."""
    referenced = set()
    for text in texts:
        for match in LINK_TARGET.finditer(text):
            target = match.group(1).split('#', 1)[0]
            if not target or '://' in target or target.startswith('mailto:'):
                continue
            referenced.add(
                posixpath.normpath(posixpath.join('docs', target)))
    return referenced


def scanned_files():
    """Repo-relative paths of the scanned files present on disk."""
    files = set()
    for pattern in SCAN_PATTERNS:
        for path in ROOT.glob(pattern):
            if path.is_file():
                files.add(path.relative_to(ROOT).as_posix())
    return files


def broken_targets(referenced):
    """Index link targets under scanned subtrees that do not exist."""
    broken = set()
    for target in referenced:
        if target.startswith(SCANNED_PREFIXES) \
                and not (ROOT / target).exists():
            broken.add(target)
    return broken


def find_problems(scanned, referenced, broken_links, allowlist):
    """Return a list of problem strings; empty means the index passes."""
    problems = []
    for path in sorted(scanned - referenced - allowlist):
        problems.append('not indexed: ' + path)
    for path in sorted(allowlist - scanned):
        problems.append(
            'allowlist names a file outside the scanned set: ' + path)
    for path in sorted(broken_links):
        problems.append('broken index link: ' + path)
    return problems


def self_test(scanned, referenced):
    """Require each check to catch a deliberately broken copy."""
    base = find_problems(scanned, referenced, broken_targets(referenced),
                         set(ALLOWLIST))
    if base:
        print('self-test: unmodified index already fails', file=sys.stderr)
        for item in base:
            print('- ' + item, file=sys.stderr)
        return 1
    indexed = sorted(scanned & referenced)
    if not indexed:
        print('self-test: no indexed scanned file to mutate',
              file=sys.stderr)
        return 1

    cases = []
    victim = indexed[0]
    cases.append(('removed index link to ' + victim,
                  scanned, referenced - {victim}, set(ALLOWLIST),
                  'not indexed: ' + victim))
    injected = 'docs/status/SELFTEST_UNINDEXED.md'
    grown = set(scanned)
    grown.add(injected)
    cases.append(('unindexed scanned file ' + injected,
                  grown, referenced, set(ALLOWLIST),
                  'not indexed: ' + injected))
    record = 'validation/SELFTEST_UNINDEXED/README.md'
    grown = set(scanned)
    grown.add(record)
    cases.append(('unindexed validation record ' + record,
                  grown, referenced, set(ALLOWLIST),
                  'not indexed: ' + record))
    dropped = sorted(ALLOWLIST)[0]
    cases.append(('dropped allowlist entry ' + dropped,
                  scanned, referenced, set(ALLOWLIST) - {dropped},
                  'not indexed: ' + dropped))
    cases.append(('removed scanned file ' + dropped,
                  scanned - {dropped}, referenced, set(ALLOWLIST),
                  'allowlist names a file outside the scanned set: '
                  + dropped))
    fake_link = 'docs/status/SELFTEST_MISSING_TARGET.md'
    cases.append(('broken index link ' + fake_link,
                  scanned, referenced | {fake_link}, set(ALLOWLIST),
                  'broken index link: ' + fake_link))

    for name, mutated_scanned, mutated_referenced, mutated_allowlist, \
            marker in cases:
        found = find_problems(mutated_scanned, mutated_referenced,
                              broken_targets(mutated_referenced),
                              mutated_allowlist)
        if not any(marker in item for item in found):
            print('self-test: %s was accepted' % name, file=sys.stderr)
            return 1
        caught = next(item for item in found if marker in item)
        print('self-test: detected %s (%s)' % (name, caught))
    print('self-test: pass')
    return 0


def main(argv):
    for path in INDEX_FILES:
        if not path.is_file():
            print('missing ' + str(path), file=sys.stderr)
            return 1
    texts = [path.read_text(encoding='utf-8') for path in INDEX_FILES]
    scanned = scanned_files()
    referenced = collect_referenced(texts)
    if '--self-test' in argv:
        return self_test(scanned, referenced)
    problems = find_problems(scanned, referenced,
                             broken_targets(referenced), set(ALLOWLIST))
    if problems:
        print('docs index coverage check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    print('docs index ok: scanned=%d indexed=%d allowlisted=%d'
          % (len(scanned), len(scanned & referenced),
             len(scanned & set(ALLOWLIST))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
