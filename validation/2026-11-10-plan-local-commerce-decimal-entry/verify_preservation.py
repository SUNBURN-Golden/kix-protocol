"""Read-only preservation checks; write only this node's evidence manifest."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent
ALLOWED = {
    'docs/README.md', 'reference/booking_resale_admission/README.md',
    'reference/booking_resale_admission/commerce_calculation_console.py',
    'reference/booking_resale_admission/test_commerce_calculation_console.py',
}

def git(*args, **kwargs):
    return subprocess.check_output(['git', *args], cwd=ROOT, **kwargs)

before = json.loads((EVIDENCE / 'preservation-before.json').read_text())
paths = sorted(p for p in (ROOT / 'reference/v0.3-rc1').rglob('*') if p.is_file())
after = {
    'frozenReference': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    'lockedBlobs': {p: git('hash-object', p, text=True).strip() for p in before['lockedBlobs']},
}
assert after == before, 'Protected bytes or path set changed'
expected_head = 'e5b7927bca2ec78a0a6618d4ac3d1d5611a0b95d'
assert git('rev-parse', 'HEAD', text=True).strip() == expected_head
assert git('rev-parse', 'origin/main', text=True).strip() == expected_head
assert git('branch', '--show-current', text=True).strip() == 'agent/kix-plan-local-commerce-decimal-entry'
# Hash every non-task tracked working file against its original index blob.
entries = git('ls-files', '--stage', '-z').decode().split('\0')
unchanged = []
for entry in entries:
    if not entry:
        continue
    metadata, path = entry.split('\t', 1)
    mode, blob, stage = metadata.split()
    assert stage == '0'
    if path not in ALLOWED:
        unchanged.append((path, blob))
actual = git('hash-object', '--stdin-paths', input=''.join(path + '\n' for path, _ in unchanged).encode()).decode().splitlines()
assert actual == [blob for _, blob in unchanged], 'Non-task tracked file changed'
for path in ALLOWED:
    if path.endswith('.py'):
        ast.parse((ROOT / path).read_text())
subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
(EVIDENCE / 'preservation-after.json').write_text(json.dumps(after, indent=2) + '\n')
print(f'PASS: both required locked blobs match; all {len(paths)} protected reference files byte-identical; '
      f'{len(unchanged)} non-task tracked files unchanged; refs unchanged; changed Python ASTs valid; diff whitespace clean.')
