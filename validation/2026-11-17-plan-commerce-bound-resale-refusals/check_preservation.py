#!/usr/bin/env python3
"""Read-only builder evidence check; never rewrites a fixture or inventory."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LOCKS = {
    "runtime/crates/kix-kernel/src/lib.rs": "69564b166f0c27f9af5d8422f0a466b18d74c20f",
    "runtime/crates/kix-kernel/tests/quarantine_capacity.rs": "b607996c83a119c349f1cc90469ac1ba82764e20",
}
ALLOWED = {
    "docs/README.md",
    "reference/booking_resale_admission/README.md",
    "reference/booking_resale_admission/test_commerce_bound_resale_vectors.py",
    "reference/booking_resale_admission/fixtures/commerce_bound_resale_inputs_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_bound_resale_receipts_v1.json",
}


def identity(path):
    raw = (ROOT / path).read_bytes()
    return {
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "gitBlob": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
    }


def main():
    before = json.loads((HERE / "preservation-before.json").read_bytes())
    after = json.loads((HERE / "preservation-after.json").read_bytes())
    assert before == after, "preservation inventory drift"
    for row in before:
        assert identity(row["path"]) == row, "protected bytes changed: " + row["path"]
    for path, expected in LOCKS.items():
        assert identity(path)["gitBlob"] == expected, "locked blob changed: " + path
        print(path + ": " + expected + " MATCH")
    artifacts = json.loads((HERE / "artifacts.json").read_bytes())["artifacts"]
    for row in artifacts:
        assert identity(row["path"]) == {k: row[k] for k in ("path", "sha256", "gitBlob")}, "artifact drift"
        assert len((ROOT / row["path"]).read_bytes()) == row["bytes"], "artifact size drift"
    print("Detached artifact identities match: %d files" % len(artifacts))
    paths = set(subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines())
    paths.update(subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())
    evidence = str(HERE.relative_to(ROOT)) + "/"
    assert all(p in ALLOWED or p.startswith(evidence) for p in paths), "out-of-scope changed path"
    frozen = [r for r in before if r["path"].startswith("reference/v0.3-rc1/")]
    print("Preserved %d existing tracked files, including %d frozen reference files" %
          (len(before), len(frozen)))
    print("Changed paths remain inside the node allowlist")


if __name__ == "__main__":
    main()
