"""Run one foreground local check, recording its exact command/output; no retries.

Invoke sequentially from the repository root with the command as arguments.
"""
import datetime
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
command = sys.argv[1:]
if not command:
    raise SystemExit('usage: python3.12 run_check.py COMMAND [ARG ...]')
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
start = time.monotonic()
environment = {'PYTHONDONTWRITEBYTECODE': '1', 'CARGO_NET_OFFLINE': 'true', 'PYTHONPATH': '.'}
result = subprocess.run(command, cwd=ROOT, env=dict(os.environ, **environment),
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
record_path = HERE / 'commands.json'
records = json.loads(record_path.read_text()) if record_path.exists() else []
log = f'{len(records) + 1:02d}-{Path(command[0]).name}.log'
(HERE / log).write_text(result.stdout)
records.append(dict(command=shlex.join(command), environment=environment,
                    started_utc=started, seconds=round(time.monotonic() - start, 3),
                    exit_code=result.returncode, log=log))
record_path.write_text(json.dumps(records, indent=2) + '\n')
print(shlex.join(command))
print('exit:', result.returncode, 'log:', log)
print(result.stdout[-5500:])
sys.exit(result.returncode)
