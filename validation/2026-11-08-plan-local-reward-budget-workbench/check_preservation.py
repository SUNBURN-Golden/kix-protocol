"""Verify protected bytes and confine this node's changed paths."""

import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LOCKS = {
    "runtime/crates/kix-kernel/src/lib.rs": "69564b166f0c27f9af5d8422f0a466b18d74c20f",
    "runtime/crates/kix-kernel/tests/quarantine_capacity.rs": "b607996c83a119c349f1cc90469ac1ba82764e20",
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).splitlines()


def main():
    before = json.loads((HERE / "preservation-before.json").read_text())
    paths = [*LOCKS, *(str(path.relative_to(ROOT))
                       for path in sorted((ROOT / "reference/v0.3-rc1").rglob("*"))
                       if path.is_file())]
    after = {path: {"sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                    "git_blob": git("hash-object", path)[0]} for path in paths}
    (HERE / "preservation-after.json").write_text(json.dumps(after, indent=2) + "\n")
    assert before == after, "protected bytes or membership changed"
    for path, blob in LOCKS.items():
        assert after[path]["git_blob"] == blob, path

    changed = sorted(set(git("diff", "--name-only", "HEAD")) |
                     set(git("ls-files", "--others", "--exclude-standard")))
    allowed_files = {"reference/token_reward/reward_budget_workbench.py",
                     "reference/token_reward/test_reward_budget_workbench.py",
                     "reference/token_reward/README.md", "docs/README.md"}
    allowed_dirs = ("reference/token_reward/fixtures/reward_budget/",
                    str(HERE.relative_to(ROOT)) + "/")
    unexpected = [path for path in changed
                  if path not in allowed_files and not path.startswith(allowed_dirs)]
    assert not unexpected, unexpected
    # Include the manifest itself so the path list is complete on its first run.
    changed = sorted(set(changed) | {str(HERE.relative_to(ROOT) / "changed-paths.txt")})
    (HERE / "changed-paths.txt").write_text("\n".join(changed) + "\n")

    records = json.loads((HERE / "commands.json").read_text())
    transcripts = [row for row in records if "--request" in row["argv"]]
    assert len(transcripts) == 6
    for file_run, stdin_run in zip(transcripts[::2], transcripts[1::2]):
        assert file_run["exit_status"] == stdin_run["exit_status"] == 0
        assert (HERE / file_run["stdout"]).read_bytes() == (HERE / stdin_run["stdout"]).read_bytes()
        assert not (HERE / file_run["stderr"]).read_bytes()
        assert not (HERE / stdin_run["stderr"]).read_bytes()
    print(f"PASS: {len(after)} protected files byte-identical before/after; locked blobs match.")
    print("PASS: complete changed-path list confined to tool/tests/fixtures/docs/evidence.")
    print("PASS: file/stdin transcripts byte-identical; no stderr.")


if __name__ == "__main__":
    main()
