"""Capture complete existing terminal fixtures in both modes; synthetic only."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
names = ('match', 'holder_burn', 'unexplained', 'unapproved_mint', 'unapproved_path',
         'both_causes', 'duplicate', 'conservation', 'boundaries')
for mode in ('in-process', 'subprocess'):
    transcript = []
    for name in names:
        source = ROOT / 'reference/token_reward/fixtures' / f'supply_console_{name}.txt'
        command = [sys.executable, 'reference/token_reward/supply_console.py', '--mode', mode]
        if mode == 'subprocess':
            command += ['--cleanup-timeout', '1']
        completed = subprocess.run(command, cwd=ROOT, input=source.read_bytes(), capture_output=True,
                                   timeout=10, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        transcript.append({'command': shlex.join(command), 'stdin_path': str(source.relative_to(ROOT)),
                           'returncode': completed.returncode,
                           'stdout': completed.stdout.decode('utf-8'),
                           'stderr': completed.stderr.decode('utf-8')})
        expected = 1 if name in ('duplicate', 'conservation') else 0
        assert completed.returncode == expected, transcript[-1]
    path = HERE / f'transcripts-{mode}.jsonl'
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in transcript), encoding='utf-8')
    print(f'{path.relative_to(ROOT)}: {len(transcript)} complete journeys; exits match fixtures')
