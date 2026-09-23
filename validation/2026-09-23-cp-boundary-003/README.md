# CP-BOUNDARY-003 — trusted workflow boundary evidence

Author-side evidence for the pre-job authorization boundary evaluated by an
isolated, credential-free probe GitHub Actions runner. This record documents
probe coverage only. It does not claim production coverage, does not authorize
merge, and does not activate anything.

- Task: `CP-BOUNDARY-003` rev 1 — https://github.com/BeautifulMind-JT/kix-protocol/issues/37
- Immutable spec: `docs/tasks/CP-BOUNDARY-003.md` @ `b9184e48f0df3f26a5214ec00eea20b0629b447f`
- Branch: `devin/cp-boundary-003` (implementation), `probe/cp-boundary-003` (probe fixtures)
- Host: `grok-bot-vm-364569106`, session `b003-devin-202609231723`

## SOURCE_BASE / HEAD

- Base (pinned task commit): `b9184e48f0df3f26a5214ec00eea20b0629b447f`
- Implementation HEAD: see PR #39 head (exact SHA recorded in the PR body at push time)
- Locked blobs verified unchanged at HEAD:
  - `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`
  - `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`

## TRUSTED_BOUNDARY_IMPLEMENTATION

Runner source inspection (actions/runner v2.337.0) established that
`ACTIONS_RUNNER_HOOK_JOB_STARTED` is injected as the first `preJobSteps` entry
with `condition: always()` (`JobExtension.cs`), ahead of container setup and
job steps — but a non-zero hook exit does NOT stop subsequent `always()`
steps (`StepsRunner.cs`). The boundary therefore has two enforcement parts:

1. `scripts/control_plane_boundary.py` — policy evaluator. Compares observed
   claims (env `GITHUB_*` + `GITHUB_EVENT_PATH` webhook payload fields) against
   an allow-list policy; fail-closed on missing/unreadable/digest-mismatched
   policy, missing required claims, or no matching rule. Emits an immutable
   decision record per job. `verify-install`/`check-env` subcommands validate
   installed digests, file modes, ownership, env wiring, `.env` boundary keys.
2. `scripts/control_plane_boundary_hook.sh` — pre-job hook. On DENY it flushes
   the decision record and SIGKILLs the `Runner.Worker` ancestor, so no job
   step, pre-action, or `always()` step can execute. `ASTRA_BOUNDARY_KILL=0`
   exists only to demonstrate the report-only bypass.
3. `scripts/control_plane_boundary_probe.sh` — probe launcher. Runs the runner
   inside `unshare -rm` + chroot: job code sees only runner dir (rw), boundary
   dir (ro), evidence dir (rw), read-only `/usr`+minimal `/etc`, empty `/tmp`
   `/home`. Builder credentials and `/etc/astra` are never mounted. Refuses to
   launch if `verify-install` fails or the job-writable `runner/.env` carries
   boundary keys (hook override / env tampering).
4. `RUNBOOKS/BOUNDARY.md` — versioned install/rollback for the real host.
5. `.github/control-plane/boundary-policy.example.json` — policy template;
   probe policy is separate and never grants production scope.

## PROBE_RUNNER_VERSION

- actions/runner `v2.337.0`, linux-x64, archive sha256
  `70920811a4f8ad4328818682bca5c6469c1c942fab52448868071d0063816613`
- Probe runner name `astra-boundary-probe-01`, label `astra-boundary-probe`,
  registration id 21 (removed after the probe).
- Installed boundary digests (`boundary-digests.txt`):
  - hook sha256 `a208b7d89ae8986588267bab033ad04b5449f8b2b659672299a386e57c4437bd`
  - evaluator sha256 `ed919cb4ed6796bd498ecf65c7e907c4716bdda5e39fecc11338491303fd2eb2`
  - probe policy sha256 `143769c3f402b18aba7f2be29f4c33b1dc87e29629c0b9c77bf341fa5b9b525c`
    (original; pinned approved source `a60d820…`) and
    `5697610bfaf21b9bf8fe277c801a3e73b0c52eaa98c9df12c0c83b18b46c8748`
    (final; pinned approved source `511ddab…`)

## ALLOWED_PROBE

Approved job = `sentinel` of `probe-boundary.yml`, `push` event on
`refs/heads/probe/cp-boundary-003`, repo id 1365416872, actor/owner id
263336091, exact workflow source sha.

- Run `35839662606` attempt 4 (sha `a60d820…`): **ALLOW**, job succeeded,
  `sentinels/sentinel-35839662606-4.json` written by the job. Isolation
  verified inside the job: `/boundary` read-only, builder credentials and
  host control config not present in the job filesystem.
- Run `35842262601` attempt 2 (sha `511ddab…`): **ALLOW** after policy re-pin,
  `sentinels/sentinel-35842262601-2.json`.

## REJECTED_PROBES

All decision records are in `decisions/`. A DENY kills the worker inside the
hook, before any job step; no hostile sentinel exists for any denied run.
Representative records:

| Case | Run / job | Evidence |
| --- | --- | --- |
| Wrong workflow | `35840620471` `attack3` (probe-evil3.yml) | decision `…473427`; DENY on `GITHUB_WORKFLOW_REF`; `always()`/override steps show no conclusion |
| Wrong ref | `35841012764`/`35841012920` (`refs/heads/probe/evil-ref`) | DENY on `GITHUB_REF` |
| Wrong event | `35841079651`, `35841182785`, `35841654177`, `35842265934`a2 (`pull_request`, `refs/pull/38/merge`) | DENY on `GITHUB_REF`+`GITHUB_EVENT_NAME`+workflow ref |
| Wrong actor | `35841179113` sentinel | DENY with sole reason `GITHUB_ACTOR_ID: '263336091' not in ['999999999']` (bogus-actor policy variant `650c66b…`) |
| Wrong source/commit | `35841648841` sentinel | DENY with sole reason `GITHUB_WORKFLOW_SHA … not in ['0000…']` (bogus-sha variant `f052500…`); also run `35839662606` attempts 1–3 |
| Policy digest mismatch | `35839662606` attempts 2–3 | DENY `policy sha256 mismatch: 143769c3… != d213bdef…` — policy edited between launch pin and job start |
| Missing policy | `35841855483`, `35841849179`, `35841849166`, `35841838742`, `35841844914` | DENY `policy unreadable: /boundary/missing.json` |
| Modified hook / modified policy (install-time) | `verify-install` rc=2 | `FAIL: hook sha256 mismatch` / `FAIL: policy sha256 mismatch` against trusted pinned digests |
| `.env` tamper / hook override | launch refusal | after a job wrote `ACTIONS_RUNNER_HOOK_JOB_STARTED=/tmp/evil.sh` into `runner/.env`, launcher refused restart: `runner .env carries boundary configuration; refusing launch` (observed twice) |
| Job with action pre-steps (`actions/checkout`) | `35841376330`, `35841648912` `attack4` | DENY inside hook before checkout's pre-step; no `evil4-*` sentinel exists for denied runs |
| `if: always()` after rejection | `35840620471` `attack3` | steps `always-sentinel`, `override-attempt` have `conclusion: null`; `evil3-35840733240-*.txt` absent |
| Wrong repository | not live-testable | probe runner is registered to this repository only; cross-repo claims covered by unit tests |

## BYPASS_FINDINGS

- A pre-job hook that only exits nonzero is NOT a boundary: with
  `ASTRA_BOUNDARY_KILL=0` (report-only) the hook still wrote DENY records, but
  run `35840733254` `attack3` executed `always-sentinel` and `override-attempt`
  anyway (`sentinels/evil3-35840733254-1.txt`, `.env` override written). Worker
  termination on deny is required; the enforce path does that.
- Missing-hook baseline (`PROBE_NO_HOOK=1`): runs `35842262598`/`35842262617`
  and sentinel runs `35842262601`a1/`35842265934`a1 executed freely
  (`evil3-35842262617-1.txt`, `evil4-35842262598-1.txt`, `evil4-always-…`),
  confirming the hook is the enforcement point and that hook absence in
  production must be treated as launch-refusing misconfiguration.
- Job containers / service containers: **NOT TESTED — docker absent on this
  host** (`docker: command not found` at job setup; runs failed in setup, not
  at the boundary). The hook runs before container setup in `preJobSteps`
  ordering, but no probe claim is made for containerized jobs.
- Environment/default-shell injection: the hook is invoked by the runner with
  worker env, not job `env:`/`defaults:`; job-side env cannot alter hook
  arguments. Runner-side env injection via job-writable `.env` is refused by
  the launcher (above).

## LOCAL_REGRESSION

```
python3 -I -m py_compile scripts/control_plane_boundary.py scripts/control_plane.py   -> OK
python3 -I scripts/control_plane.py self-test                                        -> PASS
python3 -m unittest discover -s scripts -p 'test_control_plane*.py' -v               -> 94 tests, OK
python3 -I scripts/control_plane.py validate-repo                                    -> PASS
```

## REMOTE_CI

Exact-head CI for the implementation HEAD is recorded in PR #39 checks; do not
attribute earlier-SHA results to later SHAs.

## HOST_INSTALL_READY

No. Probe coverage only; host install is a separate gated step documented in
`RUNBOOKS/BOUNDARY.md`. Not claimed.

## INDEPENDENT_REVIEW

Pending — designated lane `GROK_BUILD`, audit floor A3. This file is author
evidence only.

## PRODUCTION_RUNNER: NOT_CONNECTED

No privileged/production runner was registered or activated. The probe runner
(registration id 21) was removed after the probe.

## RUNTIME_ENABLED: false

Unchanged.

## EVIDENCE_POINTER

This directory (`validation/2026-09-23-cp-boundary-003/` on branch
`devin/cp-boundary-003`, PR #39) contains the decision records, sentinel
outputs, digests, and runner log. Probe fixtures live on branch
`probe/cp-boundary-003` and are intentionally not in the PR.
