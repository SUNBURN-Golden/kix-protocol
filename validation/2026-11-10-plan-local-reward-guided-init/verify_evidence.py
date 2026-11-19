"""Offline builder evidence checks; reads the worktree and saved transcripts only."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[1]
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}
paths = [ROOT / path for path in LOCKS]
paths += sorted(p for p in ROOT.joinpath('reference/v0.3-rc1').rglob('*') if p.is_file())
actual = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
expected = json.loads(EVIDENCE.joinpath('protected-before.json').read_text())
assert actual == expected, 'protected membership or contents changed'
EVIDENCE.joinpath('protected-after.json').write_text(json.dumps(actual, indent=2) + '\n')
for path, expected_blob in LOCKS.items():
    blob = subprocess.check_output(['git', 'hash-object', path], cwd=ROOT, text=True).strip()
    assert blob == expected_blob, (path, blob)
    print(f'{path}: {blob} (before/after match)')
print(f'Protected membership and SHA-256 match for {len(actual)} files')
subprocess.run(['git', 'diff', '--exit-code', '--', '.aiops/', 'docs/tasks/',
                'reference/v0.3-rc1/', *LOCKS], cwd=ROOT, check=True)
print('Protected task/policy/reference/lock tracked diff empty')

def transcript(prefix, path):
    return [json.loads(row) for row in re.findall(prefix + r'=(\{[^\n]+\})', path.read_text())]

commands = json.loads(EVIDENCE.joinpath('commands.json').read_text())
guided = next(row for row in commands if row['command'].endswith('/guided-heredoc.sh'))
file_mode = next(row for row in commands if row['command'].endswith('/file-mode.sh'))
assert guided['exit_code'] == file_mode['exit_code'] == 0
replies = transcript('desk', EVIDENCE / guided['log'])
assert replies == transcript('desk', EVIDENCE / file_mode['log'])
assert len(replies) == 11
fixture = json.loads(ROOT.joinpath('reference/token_reward/fixtures/reward_session.json').read_text())
assert transcript('initialization', EVIDENCE / guided['log']) == [fixture]
assert transcript('initialized', EVIDENCE / guided['log']) == [
    {'operation': 'initialize', 'provenance': 'MOCK_TOKEN_REWARD_ONLY', 'initialized': fixture}]
flags = ('token_issued', 'onchain_recorded', 'funds_executed', 'krw_paid',
         'chain_finality', 'durable', 'legal_authority')
for reply in replies:
    receipt = reply.get('receipt')
    reward = reply.get('view') or (receipt or {}).get('reward')
    for value in (receipt, reward):
        if value:
            assert all(value[flag] is False for flag in flags)
assert replies[-3]['view']['phase'] == 'ISSUED'
assert len(replies[-1]['pool_view']['spends']) == 1
print(f'{len(replies)} complete business replies equal between guided here-document and fixture mode')
print('Explicit final reward/pool views and all seven false flags match')
