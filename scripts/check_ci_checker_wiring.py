#!/usr/bin/env python3
"""Check protocol.yml wiring and checker citations using only the stdlib.

Every scripts/check_*.py must run plain and with --self-test. The fixed
stage-5 exception must run only its self-test: CI is not the pinned host.
Status evidence maps, matrices and review packs must cite existing, run
checkers. Invocations are standalone `python3 scripts/check_*.py` lines,
optionally followed by `--self-test`, matching the workflow's convention.
This is a textual wiring check, not a YAML/shell evaluator or a claim that
the checkers' assertions are semantically adequate. --self-test uses only
synthetic workflow/document inputs and temporary file fixtures.
"""
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = '.github/workflows/protocol.yml'
SCRIPT_GLOB = 'scripts/check_*.py'
DOC_GLOBS = (
    'docs/status/*EVIDENCE_MAP*.md',
    'docs/status/*MATRIX*.md',
    'docs/status/*REVIEW_PACK*.md',
)
SELF_TEST_ONLY = {
    'check_stage5_host.py':
        'CI runner is not the pinned stage-5 host; '
        'a plain run would report the runner host',
}
INVOKE = re.compile(
    r'^\s*python3\s+scripts/(check_[A-Za-z0-9_]+\.py)(\s+--self-test)?\s*$')
CITE = re.compile(r'\bcheck_[A-Za-z0-9_]+\.py\b')


def parse_invocations(text):
    """Return plain and self-test script basenames; comments do not count."""
    plain, selftest = set(), set()
    for line in text.splitlines():
        if line.lstrip().startswith('#'):
            continue
        match = INVOKE.fullmatch(line)
        if match:
            target = selftest if match.group(2) else plain
            target.add(match.group(1))
    return plain, selftest


def check(scripts, workflow_text, docs):
    """Return deterministic errors from the supplied file/workflow snapshot."""
    plain, selftest = parse_invocations(workflow_text)
    run = plain | selftest
    errors = []
    if not scripts:
        errors.append('sanity: no checker scripts')
    if not run:
        errors.append('sanity: no workflow invocations')
    if not docs:
        errors.append('sanity: no status documents')

    for name in sorted(scripts - SELF_TEST_ONLY.keys()):
        if name not in run:
            errors.append('unwired: ' + name)
        elif name not in selftest:
            errors.append('plain-only: ' + name)
        elif name not in plain:
            errors.append('self-test-only (unlisted): ' + name)
    for name in sorted(SELF_TEST_ONLY):
        if name not in scripts:
            errors.append('allowlist names missing script: ' + name)
        if name in plain:
            errors.append('allowlisted but wired plain: ' + name)
        if name not in selftest:
            errors.append('allowlisted but missing self-test: ' + name)
    for name in sorted(run - scripts):
        errors.append('wired but missing: ' + name)
    for doc, text in sorted(docs.items()):
        for name in sorted(set(CITE.findall(text))):
            if name not in scripts:
                errors.append('doc cites missing checker: %s: %s' % (doc, name))
            if name not in run:
                errors.append('doc cites unrun checker: %s: %s' % (doc, name))
    return errors


def collect(root):
    """Read only matching regular files; de-duplicate overlapping doc globs."""
    scripts = {path.name for path in root.glob(SCRIPT_GLOB) if path.is_file()}
    paths = {path for pattern in DOC_GLOBS for path in root.glob(pattern)
             if path.is_file()}
    docs = {path.relative_to(root).as_posix(): path.read_text(encoding='utf-8')
            for path in sorted(paths)}
    return scripts, (root / WORKFLOW).read_text(encoding='utf-8'), docs


def self_test():
    """Require each negative control to report its own rule, not just fail."""
    scripts = {'check_example.py', 'check_stage5_host.py'}
    workflow = ('name: synthetic\nsteps:\n  - run: |\n'
                '      python3 scripts/check_example.py\n'
                '      python3 scripts/check_example.py --self-test\n'
                '      python3 scripts/check_stage5_host.py --self-test\n'
                '      # python3 scripts/check_commented.py\n')
    docs = {
        'docs/status/TEST_EVIDENCE_MAP.md': '`scripts/check_example.py`',
        'docs/status/TEST_MATRIX.md': '`check_stage5_host.py`',
        'docs/status/TEST_REVIEW_PACK.md': '`check_example.py`',
        'docs/status/TEST_EVIDENCE_MAP_MATRIX.md': '`check_example.py`',
    }
    baseline = check(scripts, workflow, docs)
    if baseline:
        print('self-test: synthetic baseline failed: ' + repr(baseline),
              file=sys.stderr)
        return 1
    plain = '      python3 scripts/check_example.py\n'
    selftest = '      python3 scripts/check_example.py --self-test\n'
    stage5 = '      python3 scripts/check_stage5_host.py --self-test\n'
    cases = [
        ('unwired checker', scripts | {'check_unwired.py'}, workflow, docs,
         'unwired: check_unwired.py'),
        ('plain-only wiring', scripts, workflow.replace(selftest, ''), docs,
         'plain-only: check_example.py'),
        ('unlisted self-test-only checker', scripts,
         workflow.replace(plain, ''), docs,
         'self-test-only (unlisted): check_example.py'),
        ('missing cited checker', scripts, workflow,
         dict(docs, **{'docs/status/MISSING_MATRIX.md': '`check_missing.py`'}),
         'doc cites missing checker: docs/status/MISSING_MATRIX.md: check_missing.py'),
        ('document cites unrun checker', scripts | {'check_unrun.py'}, workflow,
         {'docs/status/UNRUN_REVIEW_PACK.md': '`check_unrun.py`'},
         'doc cites unrun checker: docs/status/UNRUN_REVIEW_PACK.md: check_unrun.py'),
        ('allowlisted script wired plain', scripts,
         workflow + 'python3 scripts/check_stage5_host.py\n', docs,
         'allowlisted but wired plain: check_stage5_host.py'),
        ('allowlisted script missing self-test', scripts,
         workflow.replace(stage5, ''), docs,
         'allowlisted but missing self-test: check_stage5_host.py'),
        ('missing allowlisted script', scripts - {'check_stage5_host.py'},
         workflow, docs, 'allowlist names missing script: check_stage5_host.py'),
        ('workflow invokes missing file', scripts,
         workflow + 'python3 scripts/check_missing.py\n', docs,
         'wired but missing: check_missing.py'),
        ('commented-out invocation', scripts | {'check_commented.py'},
         workflow, docs, 'unwired: check_commented.py'),
        ('no scripts', set(), workflow, docs, 'sanity: no checker scripts'),
        ('no invocations', scripts, '', docs, 'sanity: no workflow invocations'),
        ('no documents', scripts, workflow, {}, 'sanity: no status documents'),
    ]
    for label, files, text, documents, marker in cases:
        errors = check(files, text, documents)
        if not any(error.startswith(marker) for error in errors):
            print('self-test: failed to detect ' + label, file=sys.stderr)
            return 1
        print('self-test: detected ' + label)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        fixtures = {**docs, WORKFLOW: workflow}
        fixtures.update({'scripts/' + name: '# synthetic checker\n'
                         for name in scripts})
        # Neither an unrelated doc nor a directory matching the script glob
        # belongs in the collected file snapshot.
        fixtures['docs/status/IGNORED.md'] = '`check_nonexistent.py`'
        for name, text in fixtures.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        (root / 'scripts/check_directory.py').mkdir()
        collected = collect(root)
        if collected != (scripts, workflow, docs) or check(*collected):
            print('self-test: temporary file fixtures failed', file=sys.stderr)
            return 1
    print('self-test: pass (%d negative controls)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_ci_checker_wiring.py [--self-test]', file=sys.stderr)
        return 2
    if argv:
        return self_test()
    try:
        scripts, workflow, docs = collect(ROOT)
    except (OSError, UnicodeError) as error:
        print('ci checker wiring input error: ' + str(error), file=sys.stderr)
        return 1
    errors = check(scripts, workflow, docs)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    plain, selftest = parse_invocations(workflow)
    print('ci checker wiring ok: scripts=%d plain=%d self_test=%d '
          'self_test_only=%d docs=%d citations=%d'
          % (len(scripts), len(plain), len(selftest), len(SELF_TEST_ONLY),
             len(docs), sum(len(CITE.findall(text)) for text in docs.values())))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
