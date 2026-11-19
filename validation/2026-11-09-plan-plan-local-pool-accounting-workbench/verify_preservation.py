"""Read-only comparison to the pre-edit inventory; no Git/network mutation."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent
ALLOWED_MODIFICATIONS = {'docs/README.md', 'reference/token_reward/README.md'}
LOCKS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}


def main():
    before = json.loads((EVIDENCE / 'before-sha256.json').read_text())
    after = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
             if (ROOT / path).is_file() else None for path in before}
    changed = sorted(path for path in before if before[path] != after[path])
    unexpected = sorted(set(changed) - ALLOWED_MODIFICATIONS)
    blobs = {path: subprocess.check_output(['git', 'hash-object', path], cwd=ROOT,
                                         text=True).strip() for path in LOCKS}
    reference = [path for path in before if path.startswith('reference/v0.3-rc1/')]
    report = {
        'tracked_paths_compared': len(before),
        'tracked_paths_changed': changed,
        'unexpected_tracked_changes': unexpected,
        'locked_blobs': blobs,
        'locked_blobs_match': blobs == LOCKS,
        'protected_reference_paths_compared': len(reference),
        'protected_reference_identical': all(before[path] == after[path] for path in reference),
        'cached_origin_main': subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=ROOT,
                                                      text=True).strip(),
        'branch_head_uncommitted_implementation': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                                        cwd=ROOT, text=True).strip(),
    }
    (EVIDENCE / 'after-sha256.json').write_text(json.dumps(after, indent=2, sort_keys=True) + '\n')
    (EVIDENCE / 'preservation.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report, indent=2, sort_keys=True))
    assert not unexpected
    assert report['locked_blobs_match'] and report['protected_reference_identical']


if __name__ == '__main__':
    main()
