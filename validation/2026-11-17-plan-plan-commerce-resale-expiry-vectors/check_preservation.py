"""Verify preserved inputs and original companion entries against before pins."""
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
BASE = '3a119fcfa9b784f67082a667ee499a018fc4e7ce'
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}
ALLOWED_TRACKED = {
    'docs/README.md',
    'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json',
    'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md',
    'docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md',
    'reference/booking_resale_admission/README.md',
    'reference/booking_resale_admission/test_commerce_companion_evidence_index.py',
}

def pin(path):
    raw = (ROOT / path).read_bytes()
    return dict(path=path, sha256=hashlib.sha256(raw).hexdigest(),
                gitBlob=hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest())

before = json.loads((OUT / 'preservation-before.json').read_text())
after = [pin(r['path']) for r in before]
for old, new in zip(before, after):
    assert old == new or old['path'] in ALLOWED_TRACKED, old['path']
for path, blob in LOCKS.items():
    assert pin(path)['gitBlob'] == blob, path
changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT).decode().splitlines()
allowed_new = {
    'reference/booking_resale_admission/test_commerce_resale_expiry_vectors.py',
    'reference/booking_resale_admission/fixtures/commerce_resale_expiry_inputs_v1.json',
    'reference/booking_resale_admission/fixtures/commerce_resale_expiry_receipts_v1.json',
}
assert ALLOWED_TRACKED <= set(changed), changed
assert all(path in ALLOWED_TRACKED | allowed_new or path.startswith(
    'validation/2026-11-17-plan-plan-commerce-resale-expiry-vectors/') for path in changed), changed
index_path = 'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json'
old = json.loads(subprocess.check_output(['git', 'show', BASE + ':' + index_path], cwd=ROOT))
new = json.loads((ROOT / index_path).read_bytes())
assert new['packs'][:-1] == old['packs']
assert {k: v for k, v in new.items() if k != 'packs'} == {k: v for k, v in old.items() if k != 'packs'}
assert len(old['packs']) == 6 and sum(len(p['entries']) for p in old['packs']) == 240
assert new['packs'][-1]['id'] == 'resale_expiry' and len(new['packs'][-1]['entries']) == 27
# Existing serialized entry blocks retain byte identity, including key order.
old_raw = subprocess.check_output(['git', 'show', BASE + ':' + index_path], cwd=ROOT)
new_raw = (ROOT / index_path).read_bytes()
old_packs = json.dumps(old['packs'], ensure_ascii=False, indent=2)
assert old_packs == json.dumps(new['packs'][:-1], ensure_ascii=False, indent=2)
assert old_raw[:-len(b'\n  ]\n}\n')] == new_raw[:len(old_raw) - len(b'\n  ]\n}\n')]
v03 = [r for r in after if r['path'].startswith('reference/v0.3-rc1/')]
summary = dict(base=BASE, inventory_files=len(after), unchanged_files=sum(a == b for a, b in zip(before, after)),
               locked_blobs=LOCKS, v03_files=len(v03),
               v03_inventory_sha256=hashlib.sha256(json.dumps(v03, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
               original_packs=6, original_entries=240, added_entries=27,
               qualification_metadata_unchanged=True, changed_tracked_paths=changed)
(OUT / 'preservation-after.json').write_text(json.dumps(after, indent=2) + '\n')
(OUT / 'preservation-results.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
