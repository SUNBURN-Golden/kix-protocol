"""Foreground, offline evidence capture for this node; no publication actions."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def run(argv, *, stdin=None):
    started = time.monotonic()
    with (open(ROOT / stdin, "rb") if stdin else open(os.devnull, "rb")) as source:
        result = subprocess.run(argv, cwd=ROOT, env=ENV, stdin=source, capture_output=True)
    path = HERE / "commands.json"
    records = json.loads(path.read_text()) if path.exists() else []
    number = len(records) + 1
    stem = f"{number:02d}"
    (HERE / (stem + ".stdout.txt")).write_bytes(result.stdout)
    (HERE / (stem + ".stderr.txt")).write_bytes(result.stderr)
    records.append({"argv": argv, "cwd": str(ROOT), "stdin": stdin,
                    "environment": {"PYTHONDONTWRITEBYTECODE": "1"},
                    "exit_status": result.returncode,
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "stdout": stem + ".stdout.txt", "stderr": stem + ".stderr.txt"})
    path.write_text(json.dumps(records, indent=2) + "\n")
    print(f"{stem}: exit {result.returncode}: {' '.join(argv)}", flush=True)
    print((result.stdout + result.stderr).decode(errors="replace")[-1200:], flush=True)


def main():
    phase = sys.argv[1]
    suite = ["python3.12", "-m", "unittest", "discover", "-s", "reference/token_reward",
             "-t", "reference/token_reward"]
    if phase == "focused":
        run(suite + ["-p", "test_reward_budget_workbench.py"])
    elif phase == "suite":
        run(suite)
    elif phase == "checks":
        for check in ("check_docs_index", "check_status_register", "check_tl_predicate_evidence_map",
                      "check_class_b_index", "check_ci_test_discovery", "check_ci_checker_wiring",
                      "check_openapi_contract", "check_integration_gate_openapi"):
            run(["python3.12", f"scripts/{check}.py"])
            run(["python3.12", f"scripts/{check}.py", "--self-test"])
        for check in ("verify_runtime_architecture", "test_runtime_architecture"):
            run(["python3.12", f"scripts/{check}.py"])
    elif phase == "rust":
        run(["cargo", "fmt", "--manifest-path", "runtime/Cargo.toml", "--all", "--", "--check"])
        for scope in (["-p", "kix-kernel"], ["--workspace"]):
            run(["cargo", "test", "--manifest-path", "runtime/Cargo.toml", *scope, "--locked", "--offline"])
            run(["cargo", "clippy", "--manifest-path", "runtime/Cargo.toml", *scope,
                 "--all-targets", "--locked", "--offline", "--", "-D", "warnings"])
    elif phase == "transcripts":
        cli = ["python3.12", "reference/token_reward/reward_budget_workbench.py"]
        fixtures = "reference/token_reward/fixtures/reward_budget/"
        for name in ("residual", "budget_floor", "budget_cap"):
            fixture = fixtures + name + ".json"
            run(cli + ["--request", fixture])
            run(cli + ["--request", "-"], stdin=fixture)
        for name in ("guided_floor", "guided_cap", "guided_decline"):
            run(cli + ["--guided"], stdin=fixtures + name + ".txt")
    else:
        raise SystemExit("unknown phase")


if __name__ == "__main__":
    main()
