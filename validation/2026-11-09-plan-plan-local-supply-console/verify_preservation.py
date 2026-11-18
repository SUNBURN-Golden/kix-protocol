"""Read-only protected-path checks; write the final evidence beside this file."""

import hashlib
import json
from pathlib import Path
import subprocess


evidence = Path(__file__).resolve().parent
before = json.loads((evidence / 'preservation-before.json').read_text())
after = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in before}
assert after == before, 'protected bytes differ from pre-edit inventory'
assert {str(path) for path in Path('reference/v0.3-rc1').rglob('*') if path.is_file()} == {
    path for path in before if path.startswith('reference/v0.3-rc1/')}
locked = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}
actual = {path: subprocess.check_output(['git', 'hash-object', path], text=True).strip()
          for path in locked}
assert actual == locked, 'locked Git blobs differ'
preserved = [*locked, 'reference/v0.3-rc1', '.aiops', 'docs/tasks', '.github',
             'docs/contracts', 'reference/token_reward/token_reward_model.py',
             'reference/token_reward/supply_cli.py', 'reference/token_reward/supply_reconciliation.py',
             'reference/token_reward/test_supply_cli.py',
             'reference/token_reward/test_supply_reconciliation.py',
             'reference/token_reward/test_reward_model.py',
             'reference/token_reward/test_tl4_model_properties.py']
subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', *preserved], check=True)
result = {'protected_file_count': len(after), 'sha256_matches_before': True,
          'locked_git_blobs': actual, 'unchanged_against_HEAD': preserved,
          'post_merge': 'not applicable; no merge'}
(evidence / 'preservation-after.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
