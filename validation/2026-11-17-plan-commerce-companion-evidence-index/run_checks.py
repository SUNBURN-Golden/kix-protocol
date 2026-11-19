"""Foreground offline checks with exact argv, exit status and separate logs."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PYTHON = ['python3', '-B']

def discovery(suite, pattern=None, verbose=False):
    result = PYTHON + ['-m', 'unittest', 'discover', '-s', 'reference/' + suite,
                       '-t', 'reference/' + suite]
    if pattern:
        result += ['-p', pattern]
    if verbose:
        result += ['-v']
    return result

CHECKERS = [
    'scripts/check_producer_qualification_tuple.py',
    'validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py',
    'scripts/check_docs_index.py', 'scripts/check_status_register.py',
    'scripts/check_ci_test_discovery.py', 'scripts/check_ci_checker_wiring.py',
    'scripts/check_openapi_contract.py', 'scripts/check_integration_gate_openapi.py',
]
PHASES = {
    'narrow': [('companion', discovery('booking_resale_admission', 'test_commerce_companion_evidence_index.py', True))],
    'commerce': [('commerce', discovery('booking_resale_admission', 'test_commerce_*.py', True))],
    'checkers': [(Path(p).stem + ('-self-test' if mode else ''), PYTHON + [p] + mode)
                 for p in CHECKERS for mode in ([], ['--self-test'])],
    'reference': [(suite, discovery(suite)) for suite in (
        'settlement_f01_f03', 'booking_resale_admission', 'credit_advance_f04',
        'ai_delegation', 'token_reward', 'provider_facts', 'payment_effects', 'economics')],
    'ktx': [
        ('architecture', PYTHON + ['scripts/verify_runtime_architecture.py']),
        ('architecture-tests', PYTHON + ['scripts/test_runtime_architecture.py']),
        ('kernel-tests', ['cargo', 'test', '--manifest-path', 'runtime/Cargo.toml', '-p', 'kix-kernel', '--locked', '--offline']),
        ('kernel-clippy', ['cargo', 'clippy', '--manifest-path', 'runtime/Cargo.toml', '-p', 'kix-kernel', '--all-targets', '--locked', '--offline', '--', '-D', 'warnings']),
        ('rustfmt', ['cargo', 'fmt', '--manifest-path', 'runtime/Cargo.toml', '--all', '--', '--check']),
    ],
}

# Complete the same stdlib document-check step, avoiding commands already run
# in the required checker phase. No workflow mutation or shell evaluation.
workflow = (ROOT / '.github/workflows/protocol.yml').read_text()
doc_step = workflow.split('      - name: Stdlib offline document checks\n', 1)[1].split('      - ', 1)[0]
done = {tuple(argv) for _, argv in PHASES['checkers']}
doc_commands = [PYTHON + shlex.split(line.strip())[1:]
                for line in doc_step.splitlines() if line.strip().startswith('python3 ')]
PHASES['docs_remaining'] = [
    (Path(argv[2]).stem + ('-self-test' if '--self-test' in argv else ''), argv)
    for argv in doc_commands if tuple(argv) not in done
]
# The default python3 is 3.13 here; also verify the new module and required
# metadata checkers with the available CI-pinned Python minor explicitly.
PHASES['python312'] = [
    (label + '-python312', ['python3.12'] + argv[1:])
    for label, argv in PHASES['narrow'] + PHASES['checkers']
]
PHASES['final'] = [
    ('preservation', PYTHON + [str(HERE.relative_to(ROOT) / 'check_preservation.py')]),
    ('git-diff-check', ['git', 'diff', '--check']),
    ('head-base', ['git', 'rev-parse', 'HEAD', 'origin/main']),
    ('branch', ['git', 'branch', '--show-current']),
    ('python-version', ['python3', '--version']),
    ('python312-version', ['python3.12', '--version']),
    ('rust-version', ['rustc', '--version']),
]

if __name__ == '__main__':
    phase = sys.argv[1]
    results_path = HERE / 'results.json'
    results = json.loads(results_path.read_bytes()) if results_path.exists() else []
    failed = False
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CARGO_NET_OFFLINE='true', RUSTUP_OFFLINE='1')
    for label, argv in PHASES[phase]:
        log = '%02d-%s.log' % (len(results) + 1, label)
        start = time.monotonic()
        with (HERE / log).open('wb') as output:
            try:
                process = subprocess.run(argv, cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT)
                code = process.returncode
            except OSError as exc:
                output.write(str(exc).encode() + b'\n')
                code = 127
        result = dict(command=shlex.join(argv), exit_code=code, log=log,
                      elapsed_seconds=round(time.monotonic() - start, 3))
        results.append(result)
        results_path.write_text(json.dumps(results, indent=2) + '\n')
        print('%s: exit=%d (%s)' % (label, code, log), flush=True)
        if code:
            failed = True
            print((HERE / log).read_text(errors='replace')[-5000:], flush=True)
    raise SystemExit(1 if failed else 0)
