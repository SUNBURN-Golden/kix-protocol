"""Read-only protected-source check; writes only this node's evidence manifest."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent
before = json.loads((EVIDENCE / 'preservation-before.json').read_text())
paths = sorted({str(p.relative_to(ROOT)) for p in (ROOT / 'reference/v0.3-rc1').rglob('*')
                if p.is_file()} | {'runtime/crates/kix-kernel/src/lib.rs',
                                   'runtime/crates/kix-kernel/tests/quarantine_capacity.rs'})
after = {p: {'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest(),
             'git_blob': subprocess.check_output(['git', 'hash-object', p], cwd=ROOT,
                                                 text=True).strip()} for p in paths}
assert before == after, 'protected membership or bytes changed'
assert after['runtime/crates/kix-kernel/src/lib.rs']['git_blob'] == '69564b166f0c27f9af5d8422f0a466b18d74c20f'
assert after['runtime/crates/kix-kernel/tests/quarantine_capacity.rs']['git_blob'] == 'b607996c83a119c349f1cc90469ac1ba82764e20'
protected = ['reference/v0.3-rc1', 'runtime/crates/kix-kernel/src/lib.rs',
             'runtime/crates/kix-kernel/tests/quarantine_capacity.rs', '.aiops', 'docs/tasks',
             '.github', 'docs/contracts', 'reference/token_reward/reward_client.py',
             'reference/token_reward/reward_cli.py', 'reference/token_reward/reward_session.py',
             'reference/token_reward/reward_fixture.py', 'reference/token_reward/reward_fsm.py',
             'reference/token_reward/token_reward_model.py']
assert not subprocess.check_output(['git', 'diff', '--name-only', 'HEAD', '--', *protected], cwd=ROOT)
assert not subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', *protected], cwd=ROOT)
(EVIDENCE / 'preservation-after.json').write_text(json.dumps(after, indent=2) + '\n')
for name in ('journey', 'boundaries'):
    assert (EVIDENCE / f'in-process-{name}.stdout.txt').read_bytes() == (EVIDENCE / f'subprocess-{name}.stdout.txt').read_bytes()
    assert not (EVIDENCE / f'in-process-{name}.stderr.txt').read_bytes()
    assert not (EVIDENCE / f'subprocess-{name}.stderr.txt').read_bytes()
print(f'PASS: {len(paths)} protected files match before/after (108 preserved reference files, both required kernel blobs).')
print('PASS: protected path Git diff and untracked additions empty; guided CLI modes have byte-identical stdout and empty stderr.')
