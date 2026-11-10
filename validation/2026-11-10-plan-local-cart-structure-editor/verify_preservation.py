"""Read-only Git/index checks plus task-local preservation evidence outputs."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = '8a1ee64fa84557355ffd1c8f174ebcbd8fd2ece2'
BRANCH = 'agent/kix-plan-local-cart-structure-editor'
SOURCE = [
    'docs/README.md', 'reference/booking_resale_admission/README.md',
    'reference/booking_resale_admission/commerce_calculation_console.py',
    'reference/booking_resale_admission/test_commerce_calculation_console.py',
]
FIXTURES = sorted(str(p.relative_to(ROOT)) for p in
                  (ROOT / 'reference/booking_resale_admission/fixtures').glob('commerce_console_structure_*.txt'))
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def blob(payload):
    return hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()


assert git('rev-parse', 'HEAD').decode().strip() == BASE
assert git('rev-parse', 'origin/main').decode().strip() == BASE
assert git('branch', '--show-current').decode().strip() == BRANCH
before = json.loads((HERE / 'preservation-before.json').read_text())
after = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in before}
assert before == after
frozen = {str(p.relative_to(ROOT)) for p in (ROOT / 'reference/v0.3-rc1').rglob('*') if p.is_file()}
assert frozen == {p for p in before if p.startswith('reference/v0.3-rc1/')}
for path, expected in LOCKS.items():
    assert blob((ROOT / path).read_bytes()) == expected
unchanged = 0
for entry in git('ls-files', '--stage', '-z').split(b'\0'):
    if not entry:
        continue
    metadata, raw_path = entry.split(b'\t', 1)
    mode, expected, stage = metadata.decode().split()
    assert stage == '0'
    path = os.fsdecode(raw_path)
    if path in SOURCE:
        continue
    content = os.fsencode(os.readlink(ROOT / path)) if mode == '120000' else (ROOT / path).read_bytes()
    assert blob(content) == expected, path
    unchanged += 1
subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
for path in SOURCE:
    if path.endswith('.py'):
        ast.parse((ROOT / path).read_text())
(HERE / 'preservation-after.json').write_text(json.dumps(after, indent=2) + '\n')
(HERE / 'locked-blobs.json').write_text(json.dumps(LOCKS, indent=2) + '\n')
(HERE / 'implementation-sha256.json').write_text(json.dumps({
    path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in SOURCE + FIXTURES
}, indent=2) + '\n')
summary = dict(head=BASE, cached_origin_main=BASE, branch=BRANCH, locked_blobs=LOCKS,
               frozen_files=len(frozen), non_task_tracked_files_unchanged=unchanged,
               changed_python_syntax='PASS', whitespace='PASS')
(HERE / 'preservation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
inventory = HERE / 'changed-paths.txt'
inventory.touch()
changed = set(os.fsdecode(p) for p in git('diff', '--name-only', '-z').split(b'\0') if p)
changed.update(os.fsdecode(p) for p in git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if p)
allowed = set(SOURCE + FIXTURES)
assert all(p in allowed or p.startswith(str(HERE.relative_to(ROOT)) + '/') for p in changed), sorted(changed)
inventory.write_text('\n'.join(sorted(changed)) + '\n')
print(json.dumps(summary, sort_keys=True))
print('Complete changed-path inventory:', len(changed), 'paths')
