"""Run a foreground verification command, retaining its actual exit and output."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'validation/2026-11-13-k-stage7-cpu-analytics-sql-audit'
LOGS = ROOT / '.local/analytics-audit'


def main():
    label, *command = sys.argv[1:]
    LOGS.mkdir(parents=True, exist_ok=True)
    path = LOGS / (label + '.log')
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with path.open('w') as handle:
        result = subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
    output = path.read_bytes()
    record = {'label': label, 'command': command, 'startedUtc': started,
              'exitCode': result.returncode, 'log': str(path.relative_to(ROOT)),
              'logSha256': hashlib.sha256(output).hexdigest(),
              'tail': output.decode(errors='replace').splitlines()[-12:]}
    target = EVIDENCE / 'commands.jsonl'
    with target.open('a') as handle:
        handle.write(json.dumps(record, sort_keys=True) + '\n')
    print(json.dumps(record, sort_keys=True), flush=True)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
