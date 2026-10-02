"""Run actual compilers and model tests. Does not publish or create ZK proofs."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'reference' / 'v0.3-rc1'
OUT = ROOT / '.local' / 'verification'
OUT.mkdir(parents=True, exist_ok=True)
env = dict(os.environ)
env['PATH'] = str(ROOT / '.local/bin') + os.pathsep + env['PATH']
env['KIX_SUI_CONFIG'] = str(ROOT / '.local/sui-config/client.yaml')
subprocess.run([sys.executable, str(ROOT / 'scripts/configure_local.py')], check=True)
checks = [
    ('python-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', str(PROTO), '-p', 'test*.py', '-v'], ROOT),
    ('node-offline', ['node', '--test', 'offline.test.mjs'], PROTO / 'client'),
    ('sdk-import', ['node', '--input-type=module', '-e', 'const m = await import("./independent.mjs"); if (typeof m.IndependentClient !== "function") throw new Error("SDK client unavailable"); console.log("SDK import and IndependentClient export OK");'], PROTO / 'client'),
    ('move-tests', ['sui', 'move', '--client.config', env['KIX_SUI_CONFIG'], '--build-env', 'mainnet', 'test', '--path', str(PROTO / 'sui')], ROOT),
    ('move-rights-scale-tests', ['sui', 'move', '--client.config', env['KIX_SUI_CONFIG'], '--build-env', 'mainnet', 'test', '--path', str(ROOT / 'reference/rights-scale-v1/sui'), '--gas-limit', '1000000000'], ROOT),
    ('circuit-build', ['node', 'compile-circuits.mjs'], PROTO / 'client'),
]
results = []
for name, args, cwd in checks:
    started = time.monotonic()
    with (OUT / (name + '.log')).open('w') as log:
        r = subprocess.run(args, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
    record = {'check': name, 'exitCode': r.returncode, 'seconds': round(time.monotonic() - started, 3)}
    results.append(record)
    print(json.dumps(record), flush=True)
    (OUT / 'build-verification.json').write_text(json.dumps({'checks': results, 'chainExecuted': False,
        'proofGenerated': False}, indent=2) + '\n')
    if r.returncode:
        print((OUT / (name + '.log')).read_text()[-10000:])
        raise SystemExit(r.returncode)

