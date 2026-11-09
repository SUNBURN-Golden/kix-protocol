"""Compare captured protected bytes and Git HEAD; list the complete patch scope."""

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent
BEFORE = json.loads((EVIDENCE / 'protected-before.json').read_text())
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}
ALLOWED = {
    'reference/token_reward/pool_client.py',
    'reference/token_reward/pool_console.py',
    'reference/token_reward/test_pool_client.py',
    'reference/token_reward/test_pool_console_subprocess.py',
    'reference/token_reward/test_pool_session.py',
    'reference/token_reward/README.md',
    'docs/README.md',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    for path, expected in BEFORE.items():
        data = (ROOT / path).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, path
        assert git('show', f'HEAD:{path}') == data, path
    for path, expected in LOCKS.items():
        assert git('hash-object', path).decode().strip() == expected, path
        print(f'{path}: {expected} MATCH')
    changed = set(git('diff', '--name-only', '-z', 'HEAD').decode().strip('\0').split('\0'))
    changed |= set(git('ls-files', '--others', '--exclude-standard', '-z').decode().strip('\0').split('\0'))
    changed.discard('')
    evidence_prefix = EVIDENCE.relative_to(ROOT).as_posix() + '/'
    assert all(p in ALLOWED or p.startswith(evidence_prefix) for p in changed), sorted(changed)
    (EVIDENCE / 'changed-paths.txt').write_text('\n'.join(sorted(changed)) + '\n')
    print(f'{len(BEFORE)} protected files: captured bytes and HEAD MATCH')
    print('reference/v0.3-rc1, .aiops, docs/tasks and workflows unchanged')
    print('PoolLedger, pool_session.py, pool_cli.py and fixtures unchanged (scope check)')
    print('All changed paths within node scope; complete list in changed-paths.txt')


if __name__ == '__main__':
    main()
