# plan-plan-loopback-host-preflight

## Identity and base

Node: `plan-plan-loopback-host-preflight`. Issue: none. Depends on: none.
Audit floor A2, `astra_gate: None`, `user_merge: False`.
Source: KIX planner run 1793088666, loop-proposed node, not in
`.aiops/program.json`. Task input is the supervisor's node specification and
read-only design supplied in this session; there is no corresponding task
document under `docs/tasks/`. This is not an ASTRA program-mode session.

- Branch: `agent/kix-plan-plan-loopback-host-preflight`.
- Starting HEAD and observed cached `origin/main`:
  `b6e1f5dc84e4c65b3c5d6d218f81be57ac14ddc4`; starting worktree clean,
  no local base delta. The supervisor prohibits network actions, so
  `git fetch origin main` was NOT_RUN, overriding AGENTS.md §1 step 1.
  Remote freshness is unverified. No rebase or base change occurred.
- Implementation head and exact final task head: not assigned; delivery is
  uncommitted changes above the starting HEAD. Supervisor owns git/GitHub.
- Merge commit and post-merge main CI run ID/status/conclusion: not applicable.
- Exact-head KTX kernel verification and KIX protocol verification run
  ID/status/conclusion: unavailable, not queried or claimed. Both must be
  completed/success on the eventual published head before merge readiness.

No commit, push, reset, PR, issue, comment, tag/branch mutation, network action,
background job, polling or automatic retry was performed.
READY describes this local builder delivery, not merge readiness or A2 review.

## Locks

`git hash-object` before and after work matches both required blobs:

| Path | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`reference/v0.3-rc1` (108 tracked files) has no diff against `origin/main` and
no untracked files. Final-merge verification is not applicable; no merge took
place.

## What this change does

Adds `scripts/check_loopback_host.py`, a read-only, stdlib-only preflight. It
reports whether the host it runs on can do what
`integration_gate.test_http_gate` needs from the operating system before any
gate code runs:

- create `socket(AF_INET, SOCK_STREAM)`;
- bind it to `127.0.0.1` port `0`;
- listen, then connect a second socket to that port over loopback and accept
  the connection;
- do the same in a child `python3 -I -c` interpreter, which prints one JSON
  line with its step results and the port it bound.

Every socket is closed as soon as its probe ends. Only `127.0.0.1` port `0` is
bound, and only `127.0.0.1` is connected to. No public address is opened and
no network call is made. `integration_gate` is never imported or started. The
child is bounded by a 10 s timeout and sockets by a 5 s timeout, with no retry
and no polling. Step exceptions, including child `OSError`, timeout and
malformed output, are recorded in the report and never raised.

Output is one JSON object (`schema_version` 1) with these top-level fields:

- `tool`, `mode` (`host` or `self-test`);
- `interpreter` (version, implementation, executable) and `platform`;
- `bind_host`, `bind_port_requested`;
- `in_process` and `child`, each with `ok`, `port` and per-step
  `create`/`bind`/`listen`/`connect` results. A step after a failure is
  recorded as `skipped: <step> failed`. `child` also records `command`,
  `returncode`, `stderr` and `error`;
- `all_ok`, `require_exit`;
- fixed flags `evidence_prep: true`, `gate_suite_run: false`,
  `host_selected: false`, `permission_granted: false`.

Plain mode always exits 0. `--require` exits 1 when any probe failed.
`--self-test` exits 0 on pass and 1 on failure. Any other argument exits 2.

`--self-test` replaces the real `socket.socket`, `subprocess.run` and
`subprocess.Popen` with tripwires for its whole run, then drives the report
logic through injected fake socket and subprocess factories:

- success;
- `PermissionError(1, 'Operation not permitted')` at create;
- `OSError` at bind;
- child failure: exit 1 with `REFUSING_BIND`-style stderr;
- child output that is not JSON;
- a child that reports `ok` with port 0.

Each case checks:

- the JSON round-trip and every named field;
- `all_ok`, plain exit 0, and `--require` exit 0 or 1 as expected;
- the failed step is recorded, earlier steps are ok and later steps are
  skipped;
- every fake socket is closed;
- every bind is to `('127.0.0.1', 0)` and every connect to `127.0.0.1`. These
  are literal values, so editing the module constants is caught;
- the child argv is `[executable, '-I', '-c', CHILD_PROGRAM]`, with the
  timeout set and no shell.

The self-test also compiles `CHILD_PROGRAM`, checks that it binds
`('127.0.0.1', 0)`, checks the usage exit 2, and fails if any tripwire fired.

Two lines in the existing `Stdlib offline document checks` step of
`.github/workflows/protocol.yml` wire the script plain and with
`--self-test`, after `check_ci_test_discovery.py --self-test`. A two-line
comment in that step says the plain run describes only the runner's loopback
context and is not a host selection. No other workflow line changes.
`check_ci_checker_wiring.py`, including its `SELF_TEST_ONLY` allowlist, is
unchanged.

## Changed paths

| Path | Change |
|---|---|
| `scripts/check_loopback_host.py` | New loopback host preflight with a fake-only self-test. |
| `.github/workflows/protocol.yml` | Two added commands and two comment lines in the existing stdlib step. |
| `docs/README.md` | One validation index bullet and a separating blank line. |
| `docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md` | One pointer-only bullet in the `plan-plan-gate-fsm-seeded-journey-differentia` entry, before `Disposition`; all other lines unchanged. |
| `validation/2026-10-27-plan-loopback-host-preflight/README.md` | This execution record. |

## Existing coverage mapping

| Requirement | Coverage before this node | Evidence / addressed gap |
|---|---|---|
| Know whether a host permits loopback sockets before running the gate suite | Partially covered | `integration_gate/test_http_gate.py::start_process` and the `REFUSING_BIND` report in `integration_gate/server.py` show a loopback failure only by running the gate. |
| Analogous host preflight | Not applicable | `scripts/check_stage5_host.py` preflights a different prerequisite set (the stage-5 PostgreSQL host). |
| Standalone, read-only loopback capability report (in-process and child) | Not covered | The new script fills this gap. Its self-test covers the four required injected cases, two extra child-output cases and `--require` exit 1. |
| New checker wired plain and `--self-test` | Sufficiently covered | Existing `check_ci_checker_wiring.py`, which now counts 33 scripts. |
| Validation record indexed | Sufficiently covered | Existing `check_docs_index.py` plain and self-test. |

## Commands and results

Commands were run from the repository root with Python 3.13.5
(`/usr/bin/python3`) and `PYTHONDONTWRITEBYTECODE=1`, unless noted.

### Builder-host plain-mode result

`python3 scripts/check_loopback_host.py` exited 0. Both probes passed on this
builder host. The full JSON:

```json
{
  "all_ok": true,
  "bind_host": "127.0.0.1",
  "bind_port_requested": 0,
  "child": {
    "command": [
      "/usr/bin/python3",
      "-I",
      "-c",
      "<CHILD_PROGRAM>"
    ],
    "error": null,
    "ok": true,
    "port": 40903,
    "returncode": 0,
    "stderr": "",
    "steps": {
      "bind": {
        "error": null,
        "ok": true
      },
      "connect": {
        "error": null,
        "ok": true
      },
      "create": {
        "error": null,
        "ok": true
      },
      "listen": {
        "error": null,
        "ok": true
      }
    }
  },
  "evidence_prep": true,
  "gate_suite_run": false,
  "host_selected": false,
  "in_process": {
    "ok": true,
    "port": 49137,
    "steps": {
      "bind": {
        "error": null,
        "ok": true
      },
      "connect": {
        "error": null,
        "ok": true
      },
      "create": {
        "error": null,
        "ok": true
      },
      "listen": {
        "error": null,
        "ok": true
      }
    }
  },
  "interpreter": {
    "executable": "/usr/bin/python3",
    "implementation": "CPython",
    "version": "3.13.5"
  },
  "mode": "host",
  "permission_granted": false,
  "platform": {
    "machine": "x86_64",
    "platform": "Linux-6.12.94+-x86_64-with-glibc2.41",
    "release": "6.12.94+",
    "system": "Linux"
  },
  "require_exit": 0,
  "schema_version": 1,
  "tool": "check_loopback_host"
}
```

The ephemeral ports differ between runs. This builder host is not the host
whose denial the gate seeded-journey stop records. The result says nothing
about that host, and it does not select or authorize this one.

### Script commands

| Command | Result |
|---|---|
| `python3 -m py_compile scripts/check_loopback_host.py` | Exit 0. The generated `scripts/__pycache__` was removed afterwards (it is git-ignored). |
| `python3 scripts/check_loopback_host.py` | Exit 0. JSON above, `all_ok: true` |
| `python3 -I -c "import json; d=json.load(open('/tmp/lb.json')); print(sorted(d))"` on the saved plain output | Exit 0. All 15 top-level fields are present |
| `python3 scripts/check_loopback_host.py --require` | Exit 0 (`all_ok` true on this host) |
| `python3 scripts/check_loopback_host.py --self-test` | Exit 0. Six `self-test: caught …` lines, then `self-test: pass` |
| `python3 scripts/check_loopback_host.py --bogus` | Exit 2. `usage: check_loopback_host.py [--require \| --self-test]` |
| `cd /tmp && python3 <worktree>/scripts/check_loopback_host.py` | Exit 0. Does not depend on the working directory |
| `python3.12 scripts/check_loopback_host.py` / `--require` / `--self-test` (Python 3.12.15) | Exit 0 / 0 / 0. Plain shows `all_ok` true and version 3.12.15 |
| In-process real-host child failure: `sys.executable='/nonexistent/python3'`, then `main([])` and `main(['--require'])` | Plain 0, require 1. `child.error` is `FileNotFoundError: [Errno 2] No such file or directory: '/nonexistent/python3'`, and `in_process.ok` is true |
| In-memory mutation probe (`/tmp/lb_mut.py`, which loads the script and patches one function or constant per run; the file on disk is not modified) | Every mutation makes `self_test()` return 1. A no-op `FakeSocket.close`: 5 cases fail. `BIND_HOST='0.0.0.0'`: 6 fail. `exit_code` always 0: 5 fail. A fake factory that calls the real `socket.socket`: the tripwire fires. `_valid_port` always true: 1 fails |
| In-memory wiring negative: `check_ci_checker_wiring.check()` on workflow text with one loopback line removed | Without the plain line: `self-test-only (unlisted): check_loopback_host.py`. Without the `--self-test` line: `plain-only: check_loopback_host.py` |

`strace` is not installed on this host. The claim that the self-test opens no
real socket therefore rests on the tripwires and on the mutation probe above,
where the tripwire fired.

### Full `Stdlib offline document checks` step

All 59 `python3 scripts/…` commands of the step, including the two new lines,
were run one subprocess per workflow line, in workflow order. All exited 0.
Last output line of each:

| Command | Result |
|---|---|
| `check_status_register.py` / `--self-test` | 0 `capability register ok: paths=452 ev_ids=15 original32=32` / 0 `self-test: pass` |
| `check_rs_profile_traceability.py` / `--self-test` | 0 `blueprint=47 profile=47 expected=47` / 0 pass |
| `check_read_model_source_map.py` / `--self-test` | 0 `queries=13 anchors=128 catalogues=2 citations=145` / 0 pass |
| `check_docs_index.py` / `--self-test` | 0 `docs index ok: scanned=291 indexed=256 allowlisted=35` / 0 pass |
| `check_i12_proof_ids.py` / `--self-test` | 0 / 0 |
| `check_delegation_layer_matrix.py` / `--self-test` | 0 `rows=36 expected=36` / 0 |
| `check_rs_predicate_evidence_map.py` / `--self-test` | 0 `rows=23` / 0 |
| `check_rs_im_evidence_map.py` / `--self-test` | 0 `rows=30` / 0 |
| `check_tl_predicate_evidence_map.py` / `--self-test` | 0 `rows=49` / 0 |
| `check_contract_error_codes.py` / `--self-test` | 0 `rows=199 … CLASS_C=0` / 0 |
| `check_adapter_identity_map.py` / `--self-test` | 0 `rows=17` / 0 |
| `check_v5_transition_evidence_map.py` / `--self-test` | 0 `rows=10` / 0 |
| `check_readiness_evidence_map.py` / `--self-test` | 0 `rows=36` / 0 |
| `check_settlement_evidence_map.py` / `--self-test` | 0 `rows=27` / 0 `(33 negative controls)` |
| `check_bra_evidence_map.py` / `--self-test` | 0 `rows=39` / 0 `(50 negative controls)` |
| `check_credit_evidence_map.py` / `--self-test` | 0 `rows=22` / 0 `(55 negative controls)` |
| `check_primary_price_fee_evidence_map.py` / `--self-test` | 0 `rows=14` / 0 `(76 negative controls)` |
| `check_ai_delegation_evidence_map.py` / `--self-test` | 0 `rows=11` / 0 `(86 negative controls)` |
| `check_lifecycle_adr_evidence_map.py` / `--self-test` | 0 `27 rows … OK` / 0 |
| `check_contract_invariants_evidence_map.py` / `--self-test` | 0 `27 rows … OK` / 0 |
| `check_toss_card_profile_evidence_map.py` / `--self-test` | 0 `41 rows … OK` / 0 |
| `check_bcs1_evidence_map.py` / `--self-test` | 0 `rows=39` / 0 |
| `check_performance_measurement_evidence_map.py` / `--self-test` | 0 `rows=42` / 0 |
| `check_feature_semantics_evidence_map.py` / `--self-test` | 0 `rows=41` / 0 |
| `check_integration_gate_contract_evidence_map.py` / `--self-test` | 0 `rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1` / 0 `(85 negative controls; …)` |
| `check_evidence_map_rollup.py` / `--self-test` | 0 `evidence map roll-up ok: contracts=25; textual index only` / 0 `(16 negative controls)` |
| `check_ci_checker_wiring.py` / `--self-test` | 0 `ci checker wiring ok: scripts=33 plain=32 self_test=33 self_test_only=1 docs=22 citations=99` / 0 `(13 negative controls)` |
| `check_ci_test_discovery.py` / `--self-test` | 0 `reference_suites=6 node_tests=8 modules=4 excluded=3` / 0 `(18 negative controls)` |
| `check_loopback_host.py` / `--self-test` | 0 (JSON report) / 0 `self-test: pass` |
| `check_stage5_host.py --self-test` | 0 `self-test: pass` |

The integration-gate map counts (`COVERED=37 PARTIAL=16 NOT_COVERED=1`) and the
rollup are unchanged by this node; no map row was edited.

### Other verification

| Command | Result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. `OK` |
| `git diff --stat origin/main -- integration_gate runtime reference docs/contracts .aiops docs/tasks scripts/check_ci_checker_wiring.py docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md` | Empty |
| `git status --porcelain` | Only the five paths in the changed-path table |
| Cargo / `ktx-kernel.yml` jobs | NOT_RUN: no Rust or runtime path is touched |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | NOT_RUN on purpose: running the gate suite is out of this node's scope |

## CI classification note

In CI, the plain run reports only the GitHub runner that executes it. It
always exits 0, so it cannot fail the step on its own; the `--self-test` line
can. Its output is not the authorized host for the gate stop and not
exact-head evidence for any other head. Making CI depend on `--require` would
be a policy choice for the owner and is not made here.

## Contract findings

No class A or class C contract violation is found. The script observes
operating-system capability, not protocol behavior, and touches no contract.
Class B characterization: on this builder host, at this time, both loopback
probes succeeded.

## Non-claims, residuals and deviations

- This record supplies host-context evidence for
  `plan-plan-gate-fsm-seeded-journey-differentia`
  ([addendum entry](../../docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia))
  and for the `CHK-HTTP-SUITE` row of
  [the integration gate evidence map](../../docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md).
  It does not choose a host, grant permission, run `test_http_gate`, or change
  any map status or owner. `CHK-HTTP-SUITE` stays `PARTIAL` with its existing
  owner, and the stop's disposition stays open.
- A passing preflight does not prove that `test_http_gate` passes. It shows
  only that the probed socket and child-process calls succeeded at that time.
- Behavior on non-Linux platforms has not been tested.
- No change to `integration_gate/**`, the gate tests,
  `check_ci_checker_wiring.py`, any evidence-map row, `runtime/`, `reference/`,
  `docs/contracts/`, `docs/tasks/` or `.aiops/`.
- Deviations from the design plan:
  - The self-test adds two child cases (malformed stdout and `ok` without a
    valid port) and a usage-exit check.
  - The plain report is printed with `indent=2` for readability. It is still
    a single JSON document.
  - The design plan treated a socket-denying builder host as likely. This
    host allowed loopback, so `--require` exited 0 here. The `--require`
    exit 1 path is shown by the self-test and by the real-host child-failure
    run.
- Follow-up candidate, not in scope: a `CURRENT_CAPABILITY_REGISTER.md`
  checker-list pointer to the new script in a later register-sync node.
