"""Read-only final preservation check; writes nothing to protected paths."""
import hashlib
import json
from pathlib import Path
import subprocess

BASE = 'c2aa970f7d95bd569f2a8eb40218cbc4c5d33b6b'
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}

def git(*args):
    return subprocess.check_output(['git', *args])

protected = ['reference/v0.3-rc1', '.aiops', 'docs/tasks', *LOCKS]
paths = git('ls-tree', '-r', '-z', '--name-only', BASE, '--', *protected).decode().rstrip('\0').split('\0')
changed = [p for p in paths if Path(p).read_bytes() != git('show', f'{BASE}:{p}')]
current_reference = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(Path('reference/v0.3-rc1').rglob('*')) if p.is_file()}
before = json.loads(Path(__file__).with_name('reference-before-sha256.json').read_text())
blobs = {p: git('hash-object', p).decode().strip() for p in LOCKS}
assert not changed, changed
assert current_reference == before
assert blobs == LOCKS
print(json.dumps({'base': BASE, 'head': git('rev-parse', 'HEAD').decode().strip(),
                  'protected_tracked_files_compared_byte_for_byte': len(paths),
                  'changed_protected_paths': changed, 'reference_files_before_after': len(before),
                  'reference_manifest_sha256': hashlib.sha256(
                      json.dumps(before, sort_keys=True).encode()).hexdigest(),
                  'locked_blobs_before': LOCKS, 'locked_blobs_after': blobs}, indent=2))
