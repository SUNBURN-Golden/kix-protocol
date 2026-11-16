"""Run named offline checks in the foreground and retain actual results.

No fixture/golden writes. The document checker block is read verbatim from CI.
"""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent
PYTHON = 'python3.12'

def unit(suite, pattern=None, verbose=False):
    args = [PYTHON, '-B', '-m', 'unittest', 'discover', '-s', 'reference/' + suite,
            '-t', 'reference/' + suite]
    if pattern:
        args += ['-p', pattern]
    if verbose:
        args += ['-v']
    return args

GROUPS = {
    'narrow': [unit('booking_resale_admission', p, True) for p in
               ('test_reservation_fsm.py', 'test_commerce_bound_issuance_vectors.py', 'test_commerce_*.py')],
    'suites': [unit(s) for s in ('settlement_f01_f03', 'booking_resale_admission',
               'credit_advance_f04', 'ai_delegation', 'token_reward', 'provider_facts',
               'payment_effects', 'economics')],
    'contracts': [[PYTHON, '-B', 'scripts/' + c + '.py'] + flag
                  for c in ('check_openapi_contract', 'check_integration_gate_openapi', 'check_sdk_client')
                  for flag in ([], ['--self-test'])] +
                 [[PYTHON, '-B', '-m', 'unittest', 'integration_gate.test_offline_limits']],
    'kernel': [[PYTHON, '-B', 'scripts/verify_runtime_architecture.py'],
               [PYTHON, '-B', 'scripts/test_runtime_architecture.py'],
               ['cargo', 'test', '--manifest-path', 'runtime/Cargo.toml', '-p', 'kix-kernel', '--locked', '--offline'],
               ['cargo', 'clippy', '--manifest-path', 'runtime/Cargo.toml', '-p', 'kix-kernel', '--all-targets', '--locked', '--offline', '--', '-D', 'warnings'],
               ['cargo', 'fmt', '--manifest-path', 'runtime/Cargo.toml', '--all', '--', '--check']],
}
workflow = (ROOT / '.github/workflows/protocol.yml').read_text()
block = workflow.split('      - name: Stdlib offline document checks\n', 1)[1].split('        run: |\n', 1)[1]
commands = []
for line in block.splitlines():
    if line and not line.startswith('          '):
        break
    if line.strip():
        commands.append(shlex.split(line.strip()))
GROUPS['documents'] = commands  # unchanged python3 invocations and self-test-only exception

if __name__ == '__main__':
    for group in sys.argv[1:]:
        for index, args in enumerate(GROUPS[group]):
            name = f'{group}-{index:02d}'
            with (EVIDENCE / 'results.jsonl').open('a') as results:
                prior = results.tell()
            # Unique log names keep failed attempts instead of overwriting them.
            log = EVIDENCE / f'{name}-{prior}.log'
            print(shlex.join(args), flush=True)
            started = time.monotonic()
            with log.open('wb') as output:
                result = subprocess.run(args, cwd=ROOT, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                                        stdout=output, stderr=subprocess.STDOUT)
            record = dict(group=group, command=shlex.join(args), exit_code=result.returncode,
                          duration_seconds=round(time.monotonic()-started, 3), log=log.name)
            with (EVIDENCE / 'results.jsonl').open('a') as results:
                results.write(json.dumps(record, sort_keys=True) + '\n')
            print(f'  exit={result.returncode} log={log.name}', flush=True)
            if result.returncode:
                print(log.read_text()[-7000:], flush=True)
                sys.exit(result.returncode)
