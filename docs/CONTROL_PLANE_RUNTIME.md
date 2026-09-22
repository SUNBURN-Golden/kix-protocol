# Control Plane Runtime v1

This runtime implements the mechanical subset of the repository's V2 AI engineering control-plane contract.

## Boundary

GitHub is the durable control surface. GitHub Actions concurrency serializes one canonical task issue at a time. `scripts/control_plane.py` validates the task envelope, writes one canonical machine-owned control-record comment, fences duplicate launches, and records `SUBMITTING`, `CONFIRMED`, `FAILED_PRESTART`, or `UNKNOWN`.

It does **not** make architecture, builder-routing, reviewer, merge, or product decisions.

## Build host

Register the persistent builder machine as a GitHub Actions self-hosted runner with both labels:

- `self-hosted`
- `astra-control-plane`

Separate worktrees/processes on this host are not a security boundary.

## Provider wrappers

Provider-specific CLI syntax is isolated behind host-local executables:

- `/opt/astra/bin/astra-builder-devin`
- `/opt/astra/bin/astra-builder-grok-build`
- `/opt/astra/bin/astra-builder-glm`

Each wrapper receives exactly one argument: the path to a JSON launch packet.

A wrapper that proves an external session started writes one JSON object to stdout and exits 0:

```json
{"outcome":"CONFIRMED","session_id":"provider-session-id"}
```

A wrapper that proves no external session/process started may write:

```json
{"outcome":"FAILED_PRESTART","reason":"explanation"}
```

Any non-zero wrapper exit is treated as `UNKNOWN`, because the control plane cannot prove whether an external launch occurred.

Wrappers must pass the packet's `launch_request_id` through as the provider idempotency key whenever the provider supports one. They must not merge, alter task semantics, choose another builder, or silently retry an ambiguous launch.

## Canonical task requirements

Runtime v1 accepts `BUILDER_STANDARD` tasks only. The canonical task issue must contain the V4 envelope fields, including `BUILDER_ID`. `CANONICAL_TASK_POINTER` and `CONTROL_RECORD_POINTER` both point to that canonical issue URL.

The machine-owned control record is the single `github-actions[bot]` issue comment containing `<!-- ASTRA_CONTROL_RECORD_V1 -->`.

## Activation

The runtime is fail-closed. `.github/control-plane/activation.json` must satisfy all of the following before `runtime_enabled` may become `true`:

1. User activation approval is durably recorded.
2. The exact runtime implementation SHA receives the required independent audit PASS.
3. The self-hosted build host passes wrapper preflight.
4. The activation record points to the exact audited runtime SHA and evidence pointers.

A documentation PASS does not satisfy the runtime implementation audit.

## CI

`control-plane-ci.yml` uses Python's standard library only. It compiles and self-tests the runtime and verifies the V2 governance markers and activation invariants.

`control-plane-runtime.yml` is intentionally fail-closed for dispatch until activation is complete.
