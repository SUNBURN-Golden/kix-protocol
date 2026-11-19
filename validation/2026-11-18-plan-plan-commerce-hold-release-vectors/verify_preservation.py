"""Read-only checks of protected bytes, prior packs and the authorized write set."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TRACKED_CHANGES = {
    'docs/README.md',
    'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json',
    'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md',
    'docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md',
    'reference/booking_resale_admission/README.md',
    'reference/booking_resale_admission/test_commerce_companion_evidence_index.py',
}
NEW_PATHS = {
    'reference/booking_resale_admission/fixtures/commerce_hold_release_inputs_v1.json',
    'reference/booking_resale_admission/fixtures/commerce_hold_release_receipts_v1.json',
    'reference/booking_resale_admission/test_commerce_hold_release_vectors.py',
}
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def pin(path):
    raw = (ROOT / path).read_bytes()
    return dict(path=path, sha256=hashlib.sha256(raw).hexdigest(),
                gitBlob=hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest())


def main():
    before = json.loads((HERE / 'preserved-before.json').read_bytes())
    assert [pin(p['path']) for p in before] == before, 'preservation inventory drift'
    for path, blob in LOCKS.items():
        assert pin(path)['gitBlob'] == blob, 'locked blob drift: ' + path
    changed = set(git('diff', 'HEAD', '--name-only').decode().splitlines())
    assert changed == TRACKED_CHANGES, 'unexpected tracked change: ' + str(changed ^ TRACKED_CHANGES)
    untracked = set(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    report_prefix = HERE.relative_to(ROOT).as_posix() + '/'
    assert NEW_PATHS <= untracked, 'missing new artifact'
    assert all(p in NEW_PATHS or p.startswith(report_prefix) for p in untracked), 'out-of-scope new path'
    path = 'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json'
    original = git('show', 'HEAD:' + path)
    current = (ROOT / path).read_bytes()
    assert current.startswith(original[:-len(b'\n  ]\n}\n')] + b',\n'), 'original serialized packs/metadata changed'
    old, new = json.loads(original), json.loads(current)
    assert len(old['packs']) == 8 and len(new['packs']) == 9
    assert old['packs'] == new['packs'][:-1], 'prior pack records changed'
    assert {k: v for k, v in old.items() if k != 'packs'} == {
        k: v for k, v in new.items() if k != 'packs'}, 'qualification metadata changed'
    assert sum(len(p['entries']) for p in old['packs']) == 293
    assert len(new['packs'][-1]['entries']) == 30
    tracked = git('ls-files').decode().splitlines()
    frozen = [p for p in tracked if p.startswith('reference/v0.3-rc1/')]
    assert not changed.intersection(frozen), 'frozen reference changed'
    print(json.dumps(dict(
        inventory_paths_unchanged=len(before), frozen_reference_files_unchanged=len(frozen),
        tracked_paths_unchanged=len(tracked) - len(changed), locked_blobs=LOCKS,
        original_families_preserved=8, original_entries_preserved=293,
        qualification_metadata_unchanged=True, changed_paths=sorted(changed | untracked),
        head=git('rev-parse', 'HEAD').decode().strip(),
        local_origin_main=git('rev-parse', 'origin/main').decode().strip(),
    ), indent=2))


if __name__ == '__main__':
    main()
