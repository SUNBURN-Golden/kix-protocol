"""Read-only checks of protected bytes and this node's allowed changed paths."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

before = json.loads((HERE / 'protected-before.json').read_text())
for path, expected in LOCKS.items():
    actual = git('hash-object', path).decode().strip()
    assert actual == before[path] == expected, (path, actual)
    assert git('rev-parse', f'HEAD:{path}').decode().strip() == expected
    print(f'{path}: {actual} MATCH before/after/HEAD')
for root in ('reference/v0.3-rc1', '.aiops', 'docs/tasks'):
    actual = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((ROOT / root).rglob('*')) if p.is_file()}
    assert actual == before[root], f'{root}: protected inventory drift'
    head_paths = {p.decode() for p in git('ls-tree', '-r', '--name-only', '-z', 'HEAD', '--', root).split(b'\0') if p}
    assert set(actual) == head_paths, f'{root}: path drift from HEAD'
    for path, digest in actual.items():
        assert hashlib.sha256(git('show', f'HEAD:{path}')).hexdigest() == digest, path
    print(f'{root}: {len(actual)} paths and SHA-256 bytes MATCH before/after/HEAD')
allowed = {'docs/README.md'} | {
    'reference/token_reward/' + name for name in (
        'README.md', 'pool_session.py', 'pool_cli.py', 'pool_client.py', 'pool_console.py',
        'test_pool_session.py', 'test_pool_cli.py', 'test_pool_client.py', 'test_pool_console_subprocess.py')}
changed = {p.decode() for data in (git('diff', '--name-only', '-z', 'HEAD'),
                                  git('ls-files', '--others', '--exclude-standard', '-z'))
           for p in data.split(b'\0') if p}
evidence_prefix = str(HERE.relative_to(ROOT)) + '/'
assert all(path in allowed or path.startswith(evidence_prefix) for path in changed), changed
print('Changed-path scope: MATCH; model, fixtures, reward machinery and workflows unchanged')
print('HEAD:', git('rev-parse', 'HEAD').decode().strip())
