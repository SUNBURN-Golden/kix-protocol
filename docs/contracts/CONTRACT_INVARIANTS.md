# Contract-derived checks over the locked v4 kernel

2026-09-16. Review supplement to approved first-batch commit
`0394a36a655b86bacb568b055d377d4c4fd91185`.
Kernel blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` and locked quarantine
regression `b607996c83a119c349f1cc90469ac1ba82764e20` remain unchanged.
No R2, integration (a), lifecycle-release implementation, index or hygiene work.

## 1. Provenance correction — not a clean-room reference

The author read the kernel source while writing `tests/support/model_v4.rs`.
Its reserve guard order, including original-result lookup before execution/time
checks, follows that implementation. Data representation is separate (owner array
and Vec rather than the kernel bitmap/maps), and it does not call Kernel for an
expected result, but this is NOT independently derived specification provenance.
The 131,072 prior comparisons establish finite-trace agreement, not which side
is correct. A shared misunderstanding can survive both. The old source and raw
results are preserved rather than rewritten to appear independent.

The new `tests/contract_invariants.rs` imports neither model_v4 nor its generator,
replies or guard-order logic. It feeds one kernel, observes its public history and
checks contract predicates. Its author still knows the kernel source; this is an
independent oracle PATH, not a claim of clean-room authorship or formal proof.

## 2. Exact existing contract anchors

All paths below refer to commit
`0394a36a655b86bacb568b055d377d4c4fd91185` (unless expressly stated otherwise).

| ID | Path | Full Git blob | Clauses used |
|---|---|---|---|
| A | docs/adr/0001-ktx-authority-commit-recovery.md | 07c36869e7b68fff10b02e6c59d7119df56d0785 | §3 stable identity/original result; §4 atomic reservation; §5 read-only replay; §6 event vs economic dedupe; §8 inventory and bounds |
| L | docs/contracts/STATE_LIFECYCLE.md | e953c4870aaeee24b13c75a8647c50609720ae01 | §2 command/observation lifetimes; §3 LC-FACT; §5 LC-TERM captured facts are not erased; §6 no invented GC |
| R | runtime/crates/kix-kernel/README.md | 900866ee99a71254fb7da1ad2aa4640477ac550c | Implemented meaning; Observation reservation and remaining gaps; bounded sum and first-capture contract |

These are existing contractual statements, not claims that all future LC-TERM
or chain grant procedures are implemented. Tests cover only current v4 operations.

## 3. Five predicates and their observation boundary

| ID | Contract-derived requirement | Kernel-only check | Source |
|---|---|---|---|
| INV-1 | A seat has no two active owners; reservation conserves inventory | Read all attempted order IDs from the SUT; count must equal order_count. Reconstruct occupied ranges from actual inventory_owned orders and reject overlap/aisle crossing; occupied + remaining = fixture total. GA uses u64 sums. | A §4/§8; R Implemented meaning |
| INV-2 | Observation budget includes stored events + conflicts + reserved slots and stays bounded | Checked sum of three public counters <= configured bound. order_count and quarantine count checked; observed distinct completed commands <= command cap. | A §8; L §2; R Observation reservation |
| INV-3 | A completed command's first result cannot change | Save the first observed typed payload/result, then re-request it after every main step with its original context; require replayed=true and same original. An Eq clone only detects mutation by the read-only probe, not recovery. | A §3/§5; L §2 command row |
| INV-4 | One full provider/account/operation has only one economic capture effect | Check unique operation-to-order binding and count None→Some captured transitions <=1. Repeated capture must not change inventory ownership again. | A §6; L §3 |
| INV-5 | An already retained capture cannot vanish or change through any tested transition | Keep first observed captured AssetAmount including asset/version/hash; after every action and error require same order/binding/amount still present. | L §3 LC-FACT and §5 LC-TERM; A §6 |

All attempted order IDs are recorded, including rejected ones, and their observed
order count must agree with the kernel's public count. This prevents silently
ignoring a known created order. Private maps/bitmap are not exposed or changed;
physical command-map allocation beyond the public boundary is not measured.
The observed-command limit is not a claim to inspect the private commands map.

'Capture' here means the kernel's retained fact under trusted-input assumptions.
It is NOT independently verified bank settlement. There is no external ledger in
v4, so INV-4 does not prove bank exactly-once or an unimplemented balance ledger.
A repeated PaymentConfirmed reply for the same event is not itself double payment;
state changes and binding are checked instead of counting that response string.

## 4. Corpus and sensitivity

The new test builds 4 fixture configurations × 64 seeds × 96 main calls = 24,576
main calls. Two seat fixtures use actual segments [65,5]; two GA fixtures use
capacity 6. Small budgets exercise saturation. Six known input actions initialize
each trace with a captured fact to avoid vacuous capture-preservation checks;
90 seeded stimuli follow. No next expected business reply is predicted by a model.
Read-only replay probes are reported separately and are not counted as new
commands or successful purchases. Every reply, including Err(Capacity), is checked.

Separate predicate sensitivity feeds deliberately corrupted COPIES OF OBSERVED
VIEWS (overlap, exceeded budget, missing capture, double transition count) to the
checker. Neither the locked kernel nor model_v4 is mutated. These are checker
sensitivity tests, not production fault injection or proof of complete detection.
Execution results are attached to their exact later CI head, not implied here.

## 5. Which defects each oracle can detect

These five predicates detect visible overlap/accounting breaks, over-budget state,
changed first outcomes, duplicate operation capture and capture loss without a
reference state machine. They can still miss incorrect but safe rejections, wrong
error precedence, an unnecessarily sticky hold, and exact phase/review semantics
not expressed by a predicate. A full transition oracle or explicit contract-based
example is needed for those questions. The current source-informed model can
expose DIFFERENCES on them; it cannot resolve shared errors by itself.

No finite test proves all inputs. A kernel that incorrectly rejects many valid
inputs may satisfy safety properties; the seeded initialization guards only some
trivial vacuity, not general availability. Single-process tests do not establish
persistence, independent fencing or chain authority. The original E-4 differential
suite is retained as a complementary regression asset, not relabelled as proof.
