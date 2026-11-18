"""Run selected existing local CI equivalents sequentially, logging actual exits.

No network, retries, fixture updates or background jobs. Run at repository root.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
GROUP = sys.argv[1]
if GROUP == 'checkers':
    scripts = [
        'scripts/check_openapi_contract.py',
        'scripts/check_integration_gate_openapi.py',
        'scripts/check_docs_index.py',
        'scripts/check_ci_test_discovery.py',
        'scripts/check_ci_checker_wiring.py',
        'scripts/check_producer_qualification_tuple.py',
        'validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py',
        'scripts/verify_runtime_architecture.py',
        'scripts/test_runtime_architecture.py',
    ]
    commands = [[sys.executable, '-B', script, *args] for script in scripts
                for args in ([[], ['--self-test']] if 'check_' in Path(script).name else [[]])]
elif GROUP in ('offline', 'offline-ci', 'offline-tail'):
    suites = ['settlement_f01_f03', 'booking_resale_admission', 'credit_advance_f04',
              'ai_delegation', 'token_reward', 'provider_facts', 'payment_effects', 'economics']
    if GROUP == 'offline-tail':
        suites = suites[5:]
    commands = [[sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'reference/' + s,
                 '-t', 'reference/' + s] for s in suites]
    commands.append([sys.executable, '-B', '-m', 'unittest', 'integration_gate.test_offline_limits'])
elif GROUP == 'ktx':
    commands = [
        ['cargo', 'test', '--manifest-path', 'runtime/Cargo.toml', '-p', 'kix-kernel', '--locked', '--offline'],
        ['cargo', 'clippy', '--manifest-path', 'runtime/Cargo.toml', '-p', 'kix-kernel', '--all-targets', '--locked', '--offline', '--', '-D', 'warnings'],
        ['cargo', 'fmt', '--manifest-path', 'runtime/Cargo.toml', '--all', '--', '--check'],
    ]
else:
    raise SystemExit('Expected checkers, offline, offline-ci, offline-tail or ktx')

results_path = OUT / (GROUP + '-results.json')
results = []
for i, command in enumerate(commands):
    log = OUT / ('%s-%02d.log' % (GROUP, i + 1))
    start = time.monotonic()
    with log.open('wb') as stream:
        completed = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                                   env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    result = dict(command=command, exit_code=completed.returncode,
                  elapsed_seconds=round(time.monotonic() - start, 3), log=log.name,
                  environment={'PYTHONDONTWRITEBYTECODE': '1'})
    results.append(result)
    results_path.write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    if completed.returncode:
        print(log.read_text(errors='replace')[-5000:], flush=True)
        raise SystemExit(completed.returncode)
