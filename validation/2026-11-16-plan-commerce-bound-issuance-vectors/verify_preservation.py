"""Verify original tracked bytes and inventory this node's allowed changes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ALLOWED_ORIGINAL_CHANGE = 'reference/booking_resale_admission/README.md'
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}

def pin(path):
    raw = (ROOT / path).read_bytes()
    return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest(),
            'gitBlob': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}

if __name__ == '__main__':
    before = json.loads((HERE / 'preservation-before.json').read_text())
    after = {p: pin(p)['sha256'] for p in before}
    changed = [p for p in before if before[p] != after[p]]
    assert changed == [ALLOWED_ORIGINAL_CHANGE], changed
    locks = [pin(p) for p in LOCKS]
    assert all(p['gitBlob'] == LOCKS[p['path']] for p in locks)
    frozen = [p for p in before if p.startswith('reference/v0.3-rc1/')]
    assert frozen and all(before[p] == after[p] for p in frozen)
    report = dict(original_tracked_files=len(before), original_changed_paths=changed,
                  unchanged_original_files=len(before)-len(changed),
                  frozen_v03_rc1_files=len(frozen), frozen_v03_rc1_byte_identical=True,
                  locked_blobs=locks, violations=[])
    (HERE / 'preservation-after.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    artifacts = [ALLOWED_ORIGINAL_CHANGE,
                 'reference/booking_resale_admission/test_commerce_bound_issuance_vectors.py',
                 'reference/booking_resale_admission/fixtures/commerce_bound_issuance_inputs_v1.json',
                 'reference/booking_resale_admission/fixtures/commerce_bound_issuance_receipts_v1.json',
                 str((HERE / 'run_checks.py').relative_to(ROOT)),
                 str(Path(__file__).resolve().relative_to(ROOT)),
                 str((HERE / 'coverage.md').relative_to(ROOT))]
    (HERE / 'artifacts.json').write_text(json.dumps([pin(p) for p in artifacts], sort_keys=True, indent=2)+'\n')
    print(json.dumps(report, sort_keys=True))
