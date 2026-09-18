# Devin Task 001 — First-batch E-4 contract edge-case audit

## Objective

Advance the currently approved first batch by closing part of the remaining **model/check review and scope-hardening** work around the locked v4 kernel.

This is a test-and-evidence task. It is **not** authorization to change kernel semantics, implement R2, integrate PR #11, add storage, add lifecycle release/GC, or perform live PG/Sui work.

Bootstrap base for this task: `5fffc196be37425366b2a6ec7faeec1db9bbca46`.
At session start, re-fetch `origin/main`; if main has moved, report the delta before rebasing or changing the task base.

## Mandatory reading

Follow root `AGENTS.md`, then read:

- `docs/contracts/CONTRACT_INVARIANTS.md`, especially §5.
- `runtime/crates/kix-kernel/README.md`.
- Existing kernel tests under `runtime/crates/kix-kernel/tests/`.
- The first-batch evidence under `validation/` that those documents reference.

## Locked files

These must remain byte-identical:

- `runtime/crates/kix-kernel/src/lib.rs`
  - blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
  - blob `b607996c83a119c349f1cc90469ac1ba82764e20`

Do not edit them even to fix formatting.

## Work plan

### A. Coverage inventory first

Before writing tests, map existing tests to the gaps explicitly acknowledged in `CONTRACT_INVARIANTS.md` and the kernel README.

At minimum assess:

1. immutable original-result replay versus current-state queries;
2. same command identity with altered request payload;
3. error/guard precedence that is contract-significant rather than merely implementation detail;
4. PaymentUnknown retention across TTL;
5. late capture after expiry/cancellation and ReturnRequired behavior;
6. bound review/quarantine behavior after matching or conflicting evidence;
7. retained versus unretained unbound conflict identity;
8. observation-slot/capacity behavior around the first bound capture.

If a behavior already has adequate deterministic regression coverage, record the exact test/path rather than duplicating it.

### B. Add only missing, contract-driven coverage

Add the smallest set of new tests/support code needed for material gaps.

Preferred properties of new tests:

- use the public `kix-kernel` API and observable state;
- do not import the source-informed `model_v4` oracle unless the test is explicitly differential;
- encode a documented contract predicate or a clearly identified characterization;
- verify non-mutation where rejection/replay is supposed to be read-only;
- avoid asserting undocumented private-map layout or implementation trivia.

A new file such as `runtime/crates/kix-kernel/tests/contract_edge_cases.rs` is acceptable if that is the cleanest organization, but choose structure based on the existing suite.

### C. Locked-kernel defect rule

If the audit finds behavior that contradicts the current contract and fixing it would require a locked-file change:

- do not modify the locked file;
- produce a minimal reproducible case;
- keep committed CI passing;
- document the conflict and the exact proposed follow-up instead of silently redefining the contract.

### D. Evidence

Update or add a narrowly scoped review/validation note that records:

- exact base/head;
- coverage mapping: existing versus newly added;
- exact commands run and results;
- locked blob verification;
- limitations of the new tests;
- any discovered contract/implementation conflict.

Do not alter historical evidence files merely to make the new run look like an old baseline.

## Acceptance criteria

The task is complete only when all are true:

- both locked blobs are unchanged;
- no production kernel/source semantics are changed;
- no R2, integration (a), storage, lifecycle-release/index, live PG or live-chain implementation is introduced;
- existing relevant tests still pass;
- new tests, if any, pass and correspond to a documented gap;
- coverage inventory clearly shows which acknowledged edge cases are already covered and which received new coverage;
- the PR reports exact verification evidence and explicit non-claims;
- the PR remains draft for human review.

Do not merge the PR.
