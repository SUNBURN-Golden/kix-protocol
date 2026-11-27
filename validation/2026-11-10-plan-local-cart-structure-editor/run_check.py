"""Run one foreground local check and retain its actual command, output and exit."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
name, cwd, *command = sys.argv[1:]
stdin_path = None
if command[0] == '--stdin':
    _, stdin_path, *command = command
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH='')
start = time.monotonic()
with (HERE / (name + '.stdout.txt')).open('wb') as stdout, (HERE / (name + '.stderr.txt')).open('wb') as stderr:
    if stdin_path:
        with Path(stdin_path).open('rb') as stdin:
            result = subprocess.run(command, cwd=cwd, env=env, stdin=stdin, stdout=stdout, stderr=stderr)
    else:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr)
record = dict(name=name, cwd=cwd, command=command, environment=dict(PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=''),
              exit_code=result.returncode, seconds=round(time.monotonic() - start, 3))
if stdin_path:
    record['stdin'] = stdin_path
with (HERE / 'commands.jsonl').open('a') as stream:
    stream.write(json.dumps(record) + '\n')
print(json.dumps(record), flush=True)
for suffix in ('stdout', 'stderr'):
    text = (HERE / (name + '.' + suffix + '.txt')).read_text(errors='replace')
    if text:
        print(suffix + ':\n' + '\n'.join(text.splitlines()[-8:]), flush=True)
sys.exit(result.returncode)
