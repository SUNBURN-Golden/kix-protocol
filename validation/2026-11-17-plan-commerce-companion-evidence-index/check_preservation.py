"""Capture/check pre-existing tracked bytes; no Git mutation or network."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EXCLUDED = {'docs/README.md', 'docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md'}
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}

def inventory(paths):
    result = {}
    for path in paths:
        raw = (ROOT / path).read_bytes()
        result[path] = {
            'sha256': hashlib.sha256(raw).hexdigest(),
            'gitBlob': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
        }
    for path, blob in LOCKS.items():
        assert result[path]['gitBlob'] == blob, 'locked blob: ' + path
    return result

if __name__ == '__main__':
    if sys.argv[1:] == ['--capture']:
        paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
        before = inventory(sorted(p for p in paths if p and p not in EXCLUDED))
        (HERE / 'preservation-before.json').write_text(json.dumps(before, indent=2) + '\n')
        print('before: %d tracked files; both locked blobs match' % len(before))
    elif not sys.argv[1:]:
        before = json.loads((HERE / 'preservation-before.json').read_bytes())
        after = inventory(before)
        (HERE / 'preservation-after.json').write_text(json.dumps(after, indent=2) + '\n')
        assert after == before, 'pre-existing bytes changed'
        changed = set(subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT).decode().splitlines())
        changed.update(subprocess.check_output(
            ['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT).decode().splitlines())
        allowed = EXCLUDED | {
            'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json',
            'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md',
            'reference/booking_resale_admission/test_commerce_companion_evidence_index.py',
        }
        prefix = HERE.relative_to(ROOT).as_posix() + '/'
        assert all(path in allowed or path.startswith(prefix) for path in changed), 'out-of-scope changed path'
        print('after: %d tracked files byte-identical; both locked blobs match; frozen files=%d' % (
            len(after), sum(p.startswith('reference/v0.3-rc1/') for p in after)))
        print('changed paths remain inside node allowlist')
    else:
        raise SystemExit('usage: check_preservation.py [--capture]')
