"""Read-only verification of this session's pinned artifacts/protected inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

folder = Path(__file__).resolve().parent
root = folder.parents[1]


def pin(path):
    raw = (root / path).read_bytes()
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "gitBlob": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
    }


preserved = json.loads((folder / "preserved-inputs.json").read_text())
for path, expected in preserved.items():
    assert pin(path) == expected, "protected bytes changed: " + path
print("Protected tracked inputs unchanged:", len(preserved))
for path, blob in (
    ("runtime/crates/kix-kernel/src/lib.rs", "69564b166f0c27f9af5d8422f0a466b18d74c20f"),
    ("runtime/crates/kix-kernel/tests/quarantine_capacity.rs", "b607996c83a119c349f1cc90469ac1ba82764e20"),
):
    assert pin(path)["gitBlob"] == blob
    print(path, blob, "MATCH")
for path, expected in json.loads((folder / "artifacts.json").read_text()).items():
    assert pin(path) == {key: expected[key] for key in ("sha256", "gitBlob")}, path
    assert (root / path).stat().st_size == expected["bytes"], path
    print(path, "artifact MATCH")
for ref in ("HEAD", "origin/main"):
    sha = subprocess.check_output(["git", "rev-parse", ref], cwd=root, text=True).strip()
    assert sha == "4722072b98c7ab4692bafffbb3f2eeefe6e3a142", (ref, sha)
    print(ref, sha, "(origin/main not refreshed)")
new_paths = subprocess.check_output(
    ["git", "ls-files", "--others", "--exclude-standard"], cwd=root, text=True).splitlines()
assert not any(path.startswith(("reference/v0.3-rc1/", ".aiops/", "docs/tasks/"))
               for path in new_paths), "unexpected protected-tree addition"
changed = subprocess.check_output(
    ["git", "diff", "--name-only"], cwd=root, text=True).splitlines()
assert set(changed) <= {"docs/README.md", "reference/booking_resale_admission/README.md"}, changed
subprocess.run(["git", "diff", "--check"], cwd=root, check=True)
print("No protected-tree additions; git diff --check PASS")
