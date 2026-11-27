"""Compare current protected bytes against the session-start manifest and Git."""

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
required = {'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
            'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20'}
paths = [ROOT / p for p in required]
paths += sorted((ROOT / 'reference/v0.3-rc1').rglob('*'))
after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in paths if p.is_file()}
before = json.loads((HERE / 'protected-before.json').read_text())
assert after == before, 'protected file set or bytes changed'
(HERE / 'protected-after.json').write_text(json.dumps(after, indent=2) + '\n')
for path, expected in required.items():
    blob = subprocess.check_output(['git', 'hash-object', path], cwd=ROOT, text=True).strip()
    assert blob == expected, (path, blob)
    print(path, blob, 'matches before/after and required lock')
protected = ['.aiops', '.github', 'docs/tasks', 'reference/v0.3-rc1',
             'reference/token_reward/supply_cli.py', 'reference/token_reward/supply_reconciliation.py',
             'reference/token_reward/token_reward_model.py', *required]
subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', *protected], cwd=ROOT, check=True)
print(f'{len(after)} protected files: identical SHA-256 manifest and file set before/after')
print('CLI, service, model, CI, .aiops, task documents and locked paths unchanged from HEAD')
