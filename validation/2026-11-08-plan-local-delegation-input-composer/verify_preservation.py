"""Verify protected path/byte equality against initial manifest and unchanged HEAD."""
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
initial = json.loads((OUT / 'preservation-before.json').read_text())
paths = [Path('runtime/crates/kix-kernel/src/lib.rs'),
         Path('runtime/crates/kix-kernel/tests/quarantine_capacity.rs')]
paths += sorted(p.relative_to(ROOT) for base in ('reference/v0.3-rc1', '.aiops', 'docs/tasks')
                for p in (ROOT / base).rglob('*') if p.is_file())
final = {}
for path in paths:
    raw = (ROOT / path).read_bytes()
    committed = subprocess.check_output(['git', 'show', 'HEAD:' + str(path)], cwd=ROOT)
    assert raw == committed, str(path) + ' differs from HEAD'
    final[str(path)] = {'sha256': hashlib.sha256(raw).hexdigest(),
                       'blob': subprocess.check_output(['git', 'hash-object', str(path)],
                                                       cwd=ROOT, text=True).strip()}
assert final == initial, 'protected paths or bytes changed'
assert final[str(paths[0])]['blob'] == '69564b166f0c27f9af5d8422f0a466b18d74c20f'
assert final[str(paths[1])]['blob'] == 'b607996c83a119c349f1cc90469ac1ba82764e20'
(OUT / 'preservation-after.json').write_text(json.dumps(final, indent=2) + '\n')
print(f'PASS: {len(final)} protected files match initial paths/bytes and Git HEAD; both locked blobs match')
