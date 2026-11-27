# audit8-rs-map-rs-c01-issuercap-open-cell

Node: `audit8-rs-map-rs-c01-issuercap-open-cell`. Source: KIX audit #8.
Wording in one cell of the map; no test, option choice, profile/register/checker change, no grade change.
Issue: none. Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not a program-mode session.

This session did not commit, push, open a pull request, create or close an issue, or comment.
There is no implementation commit SHA and no final task head SHA. Local results below are not
exact-head CI. Exact-head CI for the final head is not recorded in the commit (AGENTS §11); it
belongs in the PR closure report.

Observed `origin/main` and branch HEAD at session start: `4da9f7762beddf1a93d95cf26e55d7bf64316711`
(merge of PR #207). `git fetch origin main` ran and left it unchanged (no delta).

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` =
`69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
`b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `reference/v0.3-rc1/**` is untouched.

## What changed

`docs/status/RS_PREDICATE_EVIDENCE_MAP.md`, RS-C01 row, cell 8 ("Missing or open") only.

- Before: `none`
- After: `The required `attest_issuance` path (no owned input) is covered by the cells to the left; the cap-split configuration test stays closed until the `IssuerCap` option is chosen (Astra's choice: `docs/contracts/RIGHTS_SCALE_PROFILE.md` section 13, `IssuerCap` paragraph; `validation/2026-10-14-rs-1-issuercap-probe/README.md`), and this map claims no cap-split test.`

Status stays `COVERED_LOCALNET`: the checker requires missing-text only for PARTIAL, NOT_COVERED and
MEASUREMENT_ONLY rows. The counts line, owner cell (`RS-1`) and citations are unchanged. The
2026-10-16 record's RS-C01 "none" is left as history; this record supersedes it for that cell only.

## Changed paths

- `docs/status/RS_PREDICATE_EVIDENCE_MAP.md`
- `docs/README.md`
- `validation/2026-10-18-audit8-rs-map-rs-c01-issuercap-open-cell/README.md` (this file)

## Existing coverage mapping (AGENTS §7)

| Requirement | Coverage | Evidence |
|---|---|---|
| Required `attest_issuance` path | sufficiently covered | `predicate_tests.move::c01_a_second_attestation_for_a_reserved_slot_aborts`; `test_model.py::test_c01_one_winner_per_slot_and_independent_authorities_at_a_boundary`; `localnet.mjs::duplicateSlotRace` |
| Cap-split configuration test | not covered, deferred by the contract (profile §13) | nothing added |
| Wording of cell 8 | not checked by a checker beyond non-empty | read against profile RS-C01 row and §13 `IssuerCap` paragraph, and the probe README |

No test or script was added or renamed.

## Contract findings (AGENTS §8)

- A: the required path matches the contract.
- B: the cap-split test is deferred by the contract itself; the option is OPEN with Astra.
- C: none.

## Not run

- `cargo`, clippy, fmt, Move, ZK, localnet, Node and SDK suites: NOT_RUN, docs-only change.
- Exact-head CI: not available before commit. Every changed path is `docs/*` or `validation/*`, so hosted runs classify as docs-only and skip the heavy steps; that green result is not full verification.

## Non-claims

- No `IssuerCap` option was chosen or ranked.
- No test was added or renamed; no grade changed; the operational count stays 0.
- The probe fact is one-validator localnet only.
- A status is a builder reading; Astra may reclassify.
