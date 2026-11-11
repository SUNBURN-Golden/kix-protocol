"""Compare protected membership/bytes with the pre-edit snapshot; read only."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}
paths = list(LOCKS)
for directory in ('reference/v0.3-rc1', '.aiops', 'docs/tasks', '.github/workflows'):
    paths.extend(str(p.relative_to(ROOT)) for p in (ROOT / directory).rglob('*') if p.is_file())
actual = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(paths)}
expected = json.loads((HERE / 'preservation-before.json').read_text())
assert actual == expected, 'Protected membership or bytes changed'
for path, blob in LOCKS.items():
    observed = subprocess.check_output(['git', 'hash-object', str(ROOT / path)], text=True).strip()
    assert observed == blob, (path, observed, blob)
    print(path, observed, 'MATCH')
print(f'{len(actual)} protected files: membership and SHA-256 bytes unchanged')
