"""Read-only byte/scope comparison against the observed starting commit."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = 'd087cfa0bc77ee6e3969eb3354422f2c3ce5d1e8'
EVIDENCE = Path(__file__).resolve().parent.relative_to(ROOT).as_posix()
ALLOWED = {
    'reference/booking_resale_admission/fixtures/commerce_admission_cancellation_inputs_v1.json',
    'reference/booking_resale_admission/fixtures/commerce_admission_cancellation_receipts_v1.json',
    'reference/booking_resale_admission/test_commerce_admission_cancellation_vectors.py',
    'reference/booking_resale_admission/test_commerce_companion_evidence_index.py',
    'reference/booking_resale_admission/README.md',
    'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json',
    'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md',
    'docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md',
    'docs/README.md',
}
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def main():
    before = json.loads((ROOT / EVIDENCE / 'preservation-before.json').read_bytes())
    for path, pin in before.items():
        raw = (ROOT / path).read_bytes()
        assert {'sha256': hashlib.sha256(raw).hexdigest(), 'gitBlob': blob(raw)} == pin, path
    for path, wanted in LOCKS.items():
        assert blob((ROOT / path).read_bytes()) == wanted, path
    tree = subprocess.check_output(['git', 'ls-tree', '-rz', BASE], cwd=ROOT)
    changed, preserved = [], []
    for record in tree.split(b'\0'):
        if not record:
            continue
        meta, encoded_path = record.split(b'\t', 1)
        _mode, kind, oid = meta.split()
        assert kind == b'blob', record
        path = encoded_path.decode()
        target = ROOT / path
        if target.is_file() and blob(target.read_bytes()) == oid.decode():
            preserved.append(path)
        else:
            assert path in ALLOWED, 'protected/unauthorized byte drift: ' + path
            changed.append(path)
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT)
    for encoded_path in untracked.split(b'\0'):
        if encoded_path:
            path = encoded_path.decode()
            assert path in ALLOWED or path.startswith(EVIDENCE + '/'), 'unauthorized new path: ' + path
    index = 'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json'
    old_raw = subprocess.check_output(['git', 'show', BASE + ':' + index], cwd=ROOT)
    new_raw = (ROOT / index).read_bytes()
    old, new = json.loads(old_raw), json.loads(new_raw)
    assert new_raw.startswith(old_raw.rsplit(b'\n  ]\n}', 1)[0] + b',\n'), 'prior serialized pack drift'
    assert new['packs'][:7] == old['packs'] and len(new['packs']) == 8
    assert sum(len(p['entries']) for p in old['packs']) == 267
    assert sum(len(p['entries']) for p in new['packs']) == 293
    assert {k: v for k, v in new.items() if k != 'packs'} == {k: v for k, v in old.items() if k != 'packs'}
    print(json.dumps(dict(base=BASE, preserved_tracked_paths=len(preserved),
                          reference_v03_rc1_files=sum(p.startswith('reference/v0.3-rc1/') for p in preserved),
                          protected_inventory_paths=len(before), locked_blobs=LOCKS,
                          prior_packs=7, prior_entries=267, current_packs=8, current_entries=293,
                          prior_serialized_pack_prefix_preserved=True,
                          qualification_metadata_unchanged=True, changed_tracked_paths=sorted(changed)), indent=2))


if __name__ == '__main__':
    main()
