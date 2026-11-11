# rs-3a — on-chain delegation primitives: page-level grant, GrantControl, revocation cut (localnet)

Evidence for KIX program node `rs-3a`: the on-chain delegation primitives of the extended
rights-scale profile (`docs/blueprints/rights-scale-v1/README.md` §6 rules 3–4, §8 row RS-3a;
`docs/contracts/RIGHTS_SCALE_PROFILE.md` §10). A page is the minimum delegation unit; grant
currentness lives in one shared `GrantControl` per grant; revocation is one write on the grant
that blocks new delegated consumption while obligations created before the cut are preserved.

**Everything here is a localnet fixture.** No delegated execution, no kernel lease/fencing/GC,
no Track K lifecycle, no RS-3b page↔kernel mapping, no grant expiry/TTL or allowed-operations
set, no GA redistribution, no coin/TIX module. Nothing below is a performance, durability or
production claim. The 16-slot reference profile (`reference/v0.3-rc1/**`, its 19 Move tests and
its ZK regression) is byte-identical and passes. The two locked kernel blobs are unchanged.
This session did not commit, push, open a pull request, or edit `.aiops/`, `docs/tasks/` or CI.
The supervisor owns git.

## Identity

| Item | Value |
|---|---|
| Task | `rs-3a` — RS-3a: on-chain delegation primitives. No task issue; no `docs/tasks/` file for this node |
| Observed `origin/main` | `bd367ef` (local `origin/main` ref; the supervisor rule for this session forbids network actions, so `git fetch origin main` was not run) |
| Branch / task base | `agent/kix-rs-3a` at `bd367ef` (equal to the observed main; no delta to report) |
| Implementation commit | none. The worktree is dirty on the task base |
| Depends on | `rs-1` (and the merged rs-2 private path at `c6ca519`) |
| Authorization | node definition; `docs/contracts/RIGHTS_SCALE_PROFILE.md` §10 updated to the implemented semantics (contract_change=YES per the node; the profile stays draft until Astra's ARCHITECTURE gate) |

## What landed

- **`GrantControl`** (`reference/rights_scale/sui/sources/rights_scale.move`): one shared object
  per grant — `show`, `issuer`, `delegate`, `generation` (1 at creation, +1 at the cut), `open`.
  Created by `create_grant` with `object::new` (grants are dynamic, not a derived key space);
  `delegate != 0x0` and an open show are required.
- **Page-level grant assignment**: `delegate_page` (issuer-signed; requires an open grant of
  the same show, an undelegated page with `reserved == 0` — an unresolved reservation would be
  stranded, RS-C07b) and `undelegate_page` (issuer-signed; requires the grant closed and
  `reserved == 0`; a page holding a stranded pre-cut reservation is not "validated unused" and
  cannot be reclaimed).
- **The revocation cut**: `revoke_grant` — one write on the grant (`open = false`,
  `generation += 1`), signed by `g.issuer`. `GrantRevoked` is the durable record. Pre-cut
  obligations (live tickets, refund duties) are untouched; every delegated path aborts with
  `EGrantClosed` from that write on.
- **Delegated paths**: `issue_delegated`, `bundle_issue_delegated`,
  `attest_issuance_delegated`, `issue_paid_delegated`, `cancel_issuance_delegated`,
  `refund_delegated`. Each passes a `GrantControl` through `check_grant`
  (`g.show == id(c) && g.open && p.delegated_to == id(g)`). The issuer/attester-side paths are
  signed by `g.delegate` (`EAuthority` otherwise); `refund_delegated` stays holder-signed — the
  grant check replaces only the delegation gate. A delegated `attest_issuance` mints the
  `IssuancePayment` to the delegate.
- **Direct-path guards**: `issue`, `attest_issuance`, `issue_paid`, `cancel_issuance`,
  `refund` (and bundles through `issue`) abort `EDelegated` on a delegated page. `revoke`,
  holder ops and the private path are unchanged — they are not in the contract's five-path list.
- **New error codes**: `EDelegated = 23`, `EGrantClosed = 24`. New events: `GrantCreated`,
  `PageDelegated`, `GrantRevoked`, `PageUndelegated`. Views: `page_delegated`, `page_grant`,
  `grant_show`, `grant_issuer`, `grant_delegate`, `grant_generation`, `grant_open`,
  `payment_slot`, `payment_ref`, `payment_expected_generation`.
- **Shared bodies**: the five inventory operations were refactored so the direct and delegated
  variants run the same state logic after their distinct gates (`issue_body`,
  `attest_issuance_body`, `cancel_issuance_body`, `issue_paid_body`, `refund_apply`).
- **Model/vectors/driver**: `model.py` mirrors every new operation, ordering and abort code;
  `vectors/public_path.json` gained scenario `rs3a_delegation_cut` (grant → reserved-page
  refusal → delegate → direct-path refusals → delegated issue/attest/pay/refund/bundle → the
  cut → every delegated path `EGrantClosed` → stranded-reservation reclaim refusal → a second
  grant unaffected by the first's cut → `undelegate_page` → the direct path resumes);
  `client/types.mjs` + `client/localnet.mjs` drive the new operations and snapshot
  `delegated_to` and the grant objects; `compare_localnet.py` compares them.

## Changed paths (complete)

Modified: `reference/rights_scale/sui/sources/rights_scale.move`,
`reference/rights_scale/sui/tests/support.move`,
`reference/rights_scale/model.py`, `reference/rights_scale/replay.py`,
`reference/rights_scale/test_model.py`,
`reference/rights_scale/vectors/public_path.json`,
`reference/rights_scale/client/types.mjs`,
`reference/rights_scale/client/localnet.mjs`,
`reference/rights_scale/client/private-localnet.mjs` (page snapshot gained `delegated_to`, matching the model),
`reference/rights_scale/compare_localnet.py`,
`docs/contracts/RIGHTS_SCALE_PROFILE.md` (§3 object/operation tables, §10),
`docs/status/CURRENT_CAPABILITY_REGISTER.md` (RS-3a row only).

Added: `reference/rights_scale/sui/tests/delegation_tests.move`, this directory.

Not touched: `reference/v0.3-rc1/**`, `runtime/**`, `.aiops/`, `docs/tasks/`, all CI workflow
files, zk circuits and committed artifacts, `docs/decisions/`, `docs/blueprints/`.

## Locked blobs

| File | Required blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

## Existing coverage first (AGENTS.md §7)

| Requirement | Existing coverage | Class |
|---|---|---|
| Page-level grant / GrantControl currentness | none — `delegated_to` existed on `InventoryPage` but was always `none` | not covered |
| Direct calls rejected on a delegated page | none | not covered |
| Revocation cut blocks old-grant consumption, preserves pre-cut obligations | none (the A-4/LC-CUT draft had no implementation) | not covered |
| Bundle across the delegation boundary is atomic | partially: `bundle_tests` cover page boundaries; the delegation boundary needed its own case | partially covered |
| `reserved > 0` precondition on delegation and on post-cut reclaim | none | not covered |
| RS-C16 control coherence for grants | partially: wrong-show/wrong-page control checks exist for the direct path | partially covered |

The 16-slot suite stays as the reference-profile regression and is **not** counted as evidence
for any row above.

## New tests and evidence, and the gap each addresses

| Artifact | Count | Gap addressed |
|---|---|---|
| `sui/tests/delegation_tests.move` | 33 tests | grant lifecycle (create/delegate/revoke/undelegate), all five direct paths refused on a delegated page (`EDelegated`), delegate-binding (`EAuthority`), wrong-grant/wrong-page/wrong-show rejections, the cut (`EGrantClosed` on every delegated path), stranded-reservation reclaim refusal, bundle-boundary atomicity, holder-signed `refund_delegated`, `cancel_show`/`revoke` characterizations |
| `test_model.py` `Delegation` class | 10 tests | the same predicates on the Python reference model, plus grant-independent operation after another grant's cut |
| `vectors/public_path.json` `rs3a_delegation_cut` | 39 steps | end-to-end scripted delegation scenario replayed by both the model and the chain driver |
| `localnet.mjs` + `compare_localnet.py` | +1 scenario, snapshot fields `delegated_to`/`grants`/payment `holder` | chain-vs-model agreement on every new state field, per step and at the end |

Move totals: `kix_rights_scale` 252 tests (219 before this node + 33 new), reference `kix` 19.

## Commands actually run and results

| Command | Result |
|---|---|
| `.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui` | 252/252 pass |
| `.local/bin/sui move … test --path reference/v0.3-rc1/sui` | 19/19 pass — the 16-slot regression |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 90/90 pass (includes `test_private_model.py`) |
| `PATH=<node24>:$PATH .venv/bin/python scripts/run_localnet_rights_scale.py` | `PASSED_ACTUAL_LOCALNET`, 15 scenarios, failures `[]`, including `rs3a_delegation_cut` |
| `PATH=<node24>:$PATH .venv/bin/python scripts/run_localnet_rights_scale_private.py` | `PASSED_ACTUAL_LOCALNET`, 3 scenarios / 120 steps, failures `[]` — RS-2 regression unchanged |
| `npm --prefix reference/rights_scale/client run test:zk` | PASSED, 54 checks |
| `npm --prefix reference/v0.3-rc1/client run test:zk` | PASSED, `ARCHIVED_AND_FRESH_KEYS` |
| `.venv/bin/python scripts/run_localnet.py` (16-slot public, unchanged) | `PASSED_ACTUAL_LOCALNET` |
| `.venv/bin/python scripts/run_localnet.py --private` (16-slot private, unchanged) | `PASSED_ACTUAL_LOCALNET` |
| `python3 scripts/check_rs_profile_traceability.py`, `check_status_register.py`, `check_docs_index.py` (+ `--self-test`) | pass |
| `.venv/bin/python scripts/verify_runtime.py` | all 8 checks pass, incl. `circuit-build` and `rs2-circuit-build` |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 78/78 pass, unchanged code |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | clean |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |

Environment: `sui` 1.79.1-808640d9b49a (pinned rev `808640d9`, reused from a sibling worktree),
Node v24.19.0 (`/home/box/.local/opt/node-v24.19.0-linux-x64/bin` on `PATH`), Python 3.12.15
(`.venv`). Localnet only; every chain result above came from a disposable single-validator
localnet created and stopped by the runner scripts.

## Contract/implementation discrepancy classification (AGENTS.md §8)

**A. Contract-defined and matching:** page as the minimum delegation unit (§10.2); the five
grant-checked paths including `refund` and `cancel_issuance` (§10.3); currentness in one
`GrantControl`, the one-write cut, per-page `delegated_to` clearing after it (§10.4); pre-cut
obligation preservation and the "validated unused" reclaim condition (§10.5, A-4/LC-CUT);
`reserved > 0` blocks delegation (RS-C07b); cross-show/wrong-object rejection (RS-C16).

**B. Contract undefined — recorded as characterizations, none invented into a contract:**
1. Delegate-binding: the issuer/attester-side delegated paths require `ctx.sender() ==
   g.delegate`; `refund_delegated` stays holder-signed. Per the node's own name and A-4's
   delegate field; if that binding is judged a policy value it is a reviewer/Astra question.
2. `cancel_show` does not revoke grants — recorded; delegated paths still check `c.open`.
3. `revoke` works unchanged on delegated pages (not in the five-path list); a revoked slot
   stays retired either way.
4. `shield`/`consume_private` do not write `occupied` and take no delegation gate; whether the
   private path should also check grants is a gate question, not decided here.
5. Delegated paths take no `IssuerCap` — consistent with the issuer-cap probe's serialization
   finding; the §13 choice stays OPEN.
6. No grant expiry/TTL and no allowed-operations set on `GrantControl` — either would be a
   policy value (DECISION_REQUIRED territory) and is absent.
7. `bundle_issue_delegated` exists as the delegated counterpart of `bundle_issue`; `begin`/
   `finish_bundle` are grant-agnostic.

**C. Explicit contract violations:** none found.

## Explicit non-claims — what was not tested

- No testnet/mainnet, real funds, PG/bank/KYC, public endpoints, R2, replication/consensus/
  storage engine, coin/TIX module. Localnet only; RPC trusted.
- No delegated execution, executor handoff, kernel lease/fence/GC, Track K lifecycle, RS-3b
  page↔kernel mapping (each has its own node/track).
- No grant expiry, TTL, allowed-operations set, sub-page or GA-shard grants.
- No throughput, latency, gas-model or contention claims; the concurrency probes are the
  pre-existing RS-1 ones and are unchanged.
- Not run: `npm ci`, `bootstrap.sh`, any CI job (no network), mutation runs, a truly
  concurrent grant-revoke-vs-delegated-op race (sequential ordering on the chain is the
  semantics tested; the shared `GrantControl` write serializes them).
- No committed ZK material: the `zk/artifacts` fixture files were reused from a sibling
  worktree via symlinks under the gitignored directory; nothing proving-related was committed.

## Follow-up candidates

- `rs-3b`: executor mapping, kernel lease/fencing, page↔kernel-inventory correspondence.
- Track K v5: lifecycle termination, release, GC, index.
- RS-4: measurements (contention on a shared `GrantControl`, revoke-to-reflect latency).
- Astra (§13): whether `IssuerCap` splits per grant or is replaced for the delegated surface.
- Astra: whether `shield`/`consume_private` take a delegation gate.
