# 2026-09-15 audit remediation

Baseline: `0bbc9b9cd421b386a542a8ed4351fb6aaeff907a` (PR #8).
Toolchain: Rust 1.98.1. This work changes the existing S06.2 branch; it does not create a second production runtime or mark S07 complete.

## Executed evidence

The auditor's eight proposed tests were actually compiled and run. The baseline workspace's eight Rust source/manifest/toolchain blobs were checked against the GitHub blob IDs before execution. The auditor's test was added unchanged to the baseline snapshot.

- `before.log`: baseline **3 passed, 5 failed**, exit 101. These are the five expected assertion failures, not compiler errors.
- `after.log`: remediated workspace **43 passed, 0 failed**: 17 existing tests, 8 audit cases, 18 additional tests. Several additional tests exercise multiple adversarial inputs.
- `checks.json`: exact validation commands and exit statuses, including fmt, clippy with warnings denied, and the architecture declaration check.
- `manifest.json`: audited baseline and hashes of the tested Rust sources and integration tests.

The remediated audit test preserves its assertions; its comments and formatting now record execution instead of calling it an unexecuted proposal.

To reproduce the baseline in a full repository checkout:

```bash
git worktree add --detach ../kix-audit-baseline 0bbc9b9cd421b386a542a8ed4351fb6aaeff907a
mkdir -p ../kix-audit-baseline/runtime/crates/kix-feature-ir/tests
cp runtime/crates/kix-feature-ir/tests/audit_regressions.rs ../kix-audit-baseline/runtime/crates/kix-feature-ir/tests/
cd ../kix-audit-baseline
cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --test audit_regressions
```

Expected baseline: exactly the five negative cases fail and the three positive controls pass. On the remediated branch, run the commands in `checks.json`; all must pass.

## Resolution by finding

| Finding | Implemented result | Remaining boundary |
| --- | --- | --- |
| A01, security outside main | PR #1 merged alone, with expected-head guard, into main `eff0f44f28d0232c6177c40b2f2feb2aa951ae09`; its prior head CI was successful | New main CI is a separate result; production ceremony and migration remain incomplete |
| A02, Filter F64 | Every predicate subtree uses the recursive type/F64 validator | Backend must consume schema-validated plan |
| A03, nested terminal divide | Both operands are recursively validated as same-type integers; nested F64 rejected | Parser allocation limits and backend conformance remain future work |
| A04, type gaps | Boolean predicates, operator/output types, aggregate input requirements, column existence, duplicate outputs/keys, dataset versions, join/group/sort keys checked | `validate()` remains preflight; execution requires `validate_with_schemas` and a trusted catalog supplied separately from the plan |
| A05, Fast64 binding | Private profile identity; `export_amount(AssetAmount)` checks asset/version/hash and range; raw scalar export API removed | `checked` does not authenticate registry claims. Authenticated snapshot-only construction remains an S07-D gate |
| Topology ambiguity | Reserved seats require individual cells; authoritative current control object specified; stale epoch, overlapping seats and dual GA token consumption added to gates | No new Move implementation or throughput proof |
| clippy installed but unused | CI now runs workspace/all-target clippy with `-D warnings` | Does not replace protocol tests |

## Main integration and branch protection

Security head `a13244fe6dc07d72b314752f056612899dc544cb` had successful workflow [34791063708](https://github.com/BeautifulMind-JT/kix-protocol/actions/runs/34791063708). The unchanged main base was checked before merging only PR #1. The new main runs [34923732279](https://github.com/BeautifulMind-JT/kix-protocol/actions/runs/34923732279). Read that run's live conclusion; this document does not turn a pending run into success.

The rulesets endpoint returned HTTP 403 with: `Upgrade to GitHub Pro or make this repository public to enable this feature.` Main was observed as `protected: false`. This work did not change repository visibility, billing, branch protection, or required-review settings. These controls are not complete. Account-level eligibility and administration access must be resolved before the requested rules can be enabled.

PR #2–#8 are not bulk merged. Preserve their dependency bases and integrate separately with CI at each resulting main SHA. The FeatureIR fixes are retained on PR #8's branch, while main receives the isolated security fix.

## Completion limits

No production PostgreSQL, PG/bank credentials, BCS codec, Polars compiler, authenticated export, new Move topology or GPU execution has been delivered here. No application deployment or database migration was performed. Historical storage-loss root cause, remote durability and restored-writer authority remain open; S05's read-only restoration claims are unchanged.

Next: S07-A actual encode/decode/hash and cross-language golden vectors with malformed-wire rejection; then S07-B/C persistent orders, observations, obligations, refund reservations and outbox with concurrency/unknown-outcome/crash tests. Real-money operation remains blocked.
