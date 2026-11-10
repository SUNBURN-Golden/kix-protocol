"""Capture real guided/file subprocess runs and compare their complete envelopes."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MODULE = ROOT / 'reference/token_reward'

def envelopes(data):
    values = []
    for line in data.decode('utf-8').splitlines():
        start = line.find('{"')
        if start >= 0:
            value = json.loads(line[start:])
            if 'provenance' in value:
                values.append(value)
    return values

for name, status in (('journey', 0), ('boundaries', 1)):
    captures = []
    for mode in ('guided', 'fixture'):
        if mode == 'guided':
            options, transcript = ['--guided-init'], f'pool_console_opening_{name}.txt'
        else:
            options = ['--fixture', str(MODULE / 'fixtures/pool_session.json')]
            transcript = f'pool_console_{name}.txt'
        command = [sys.executable, str(MODULE / 'pool_console.py'), *options,
                   '--mode', 'subprocess', '--cleanup-timeout', '1']
        result = subprocess.run(command, input=(MODULE / 'fixtures' / transcript).read_bytes(),
                                capture_output=True, timeout=15, cwd=ROOT,
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        (HERE / f'{mode}-{name}.stdout').write_bytes(result.stdout)
        (HERE / f'{mode}-{name}.stderr').write_bytes(result.stderr)
        print(f'{shlex.join(command)} < reference/token_reward/fixtures/{transcript} -> exit {result.returncode}')
        assert result.returncode == status, result.stderr
        assert result.stderr == b'', result.stderr
        captures.append(envelopes(result.stdout))
    assert captures[0] == captures[1]
    print(f'{name}: {len(captures[0])} complete envelopes MATCH')
    if name == 'boundaries':
        assert [item['error']['code'] for item in captures[0] if 'error' in item] == [
            'POOL_FORBIDDEN_FOR_TOKEN_SPEND'] * 3 + ['POOL_EXHAUSTED_PAUSED']
