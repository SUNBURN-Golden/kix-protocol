#!/usr/bin/env python3
"""Check that a disposable two-fault manifest fails at the profile hash first."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def canonical(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False).encode('utf-8')


def main():
    original = (ROOT / 'sdk/compat/manifests/manifest.bootstrap-2.json').read_bytes()
    document = json.loads(original)
    if canonical(document) != original:
        print('repro precondition failed: Python encoding differs from manifest bytes', file=sys.stderr)
        return 3
    document['profile_sha256'] = '0' * 64
    document['contract']['contract_only']['sha256'] = '0' * 64
    with tempfile.TemporaryDirectory(prefix='kix-c4-order-') as directory:
        manifest = Path(directory) / 'manifest.json'
        data = canonical(document)
        manifest.write_bytes(data)
        manifest.with_suffix('.json.sha256').write_text(
            hashlib.sha256(data).hexdigest() + '\n', encoding='ascii')
        result = subprocess.run(
            ['node', 'sdk/compat/verify_compat.mjs', '--manifest', str(manifest),
             '--expect-kind', 'BOOTSTRAP', '--expect-revision', 'bootstrap-2'],
            cwd=ROOT, capture_output=True, text=True, check=False)
    try:
        verdict = json.loads(result.stdout)
        errors = verdict['errors']
        contract_index = errors.index('contract_only bytes drift')
        profile_index = errors.index('profile bytes drift')
    except (ValueError, KeyError, TypeError, AttributeError):
        print('C4 expected two fault diagnostics: ' + result.stdout + result.stderr, file=sys.stderr)
        return 2
    if (result.returncode == 1 and verdict.get('ok') is False and
            profile_index == 0 and profile_index < contract_index):
        print(f'C4 profile hash first: profile index={profile_index} '
              f'contract_only index={contract_index} verifier exit=1')
        return 0
    print('C4 expected fail-closed with profile hash first: ' + result.stdout + result.stderr,
          file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
