# AI 위임 §7 검사 순서 — 소유자 결정 위치 기록 (2026-11-18)

Node `plan-plan-aid-contract-map-partial-closure`, branch
`agent/kix-plan-plan-aid-contract-map-partial-closure`; issue: none. Document
date: 2026-11-18. Written in the node's fix round 1 as the remedy named by the
round-1 independent review.

상태: 위치 기록 (location record). This document creates no new decision, does
not mark anything as reviewed, and changes no contract, grade, ledger row or
node state. The recorder is the builder, not the decision-maker and not a
non-author reviewer. It records, under [AGENTS.md](../../AGENTS.md) §5, a human
authorization that was granted outside this repository and delivered to the
build session by the supervisor, so that the authorization is verifiable
in-repo instead of resting on builder-authored artifacts alone.

## 1. The decision and its provenance

Decision-maker: JunTae (owner), delegated through the KIX supervisor on
2026-11-18, delegation batch tag `[pt224u]`. The decision answers this node's
class C stop (`DECISION_REQUIRED.md` at the worktree root, since removed as the
decision itself instructs).

Delivery channel: the supervisor-generated builder prompt for this node's
build session, section `=== Owner decision (answers the earlier
DECISION_REQUIRED; authoritative for this node) ===`. The prompt file is
supervisor-owned and lives outside the repository, at
`/workspace/kix-run/logs/plan-plan-aid-contract-map-partial-closure_build_a0_codex0.prompt.md`
(lines 182–186 at the time this record was written). Builder sessions edit the
worktree only and cannot write that channel.

Verbatim decision text (prompt lines 183–184, line wrapping as delivered):

> Owner decision (KIX supervisor, delegated by JunTae 2026-11-18 [pt224u]; authoritative for this node).
> Option 1 approved and authorized in this node (the contract stays authoritative, unchanged): fix reference/ai_delegation/ai_delegation_mock.py call_tool so that, after actor registration and identifier well-formedness, a grant bound to another agent returns UNKNOWN_ACTOR before deny/allow tool-list rejection (contract §7 item 1 before item 2). Keep all other check order and existing-grant behavior. Replace the class-C characterization test with a conformance regression (agent-2 on g-1 -> UNKNOWN_ACTOR, state unchanged; also with no_such_tool), and update the evidence map rows from PARTIAL/class C accordingly. Remove DECISION_REQUIRED.md and finish with STATUS: READY.

Corroboration, not independent verification: the same 2026-11-18 `[pt224u]`
delegation tag appears throughout the supervisor's loop ledger
(`/workspace/kix-run/AUTOLOOP_RESULT.md`, also outside the repository) for that
day's batch of node dispositions (drops, CI re-runs, fix rounds). The builder
cannot cryptographically verify the owner's delegation; this record preserves
the supervisor-delivered text as received and names its channel. If the owner
or supervisor disputes the text, this record and the change it authorizes must
be revisited by them, not by a builder.

Why this record exists: the round-1 independent review (supervisor-commissioned,
read-only) accepted the fix as "correct, minimal, and contract-conformant" but
blocked because the authorization was unrecorded in-repo, and named the remedy:
"Remedy if the decision is genuine: record it under `docs/decisions/` (or have
the owner confirm it in-repo)". The decision's genuineness was checked against
the supervisor-owned prompt and ledger above before writing this record.

## 2. The stop it answers

The stopped build reported a class C discrepancy under AGENTS.md §8: in
`AiDelegationMock.call_tool`, a registered agent targeting another agent's
grant received `TRANSFER_FORBIDDEN` (tool `transfer`) or `TOOL_NOT_ALLOWED`
(tool `no_such_tool`) where [AI_DELEGATION_AUTHORITY.md](../contracts/AI_DELEGATION_AUTHORITY.md)
§7 item 1 requires `UNKNOWN_ACTOR` before the item-2 tool lists.

The stop is recorded on cached `origin/main` as item A5 of
`docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md` (node
`plan-plan-open-decisions-addendum-20261026-ai`, merged as `be97eaa`; cached
`origin/main` `9f118dc3584edd61ca1076f5f0c2123c1c9428fe`). That file does not
exist at this branch's base `a38e1679449e74186c5a4e3d19b6cb79f6b791d5`, so this
is a source pointer, not a branch Markdown link. The addendum names the source
stop's SHA-256
`24338c0753381529f3a9c00936dd8792130d8021cdef4ce0b60b9e8c6dae8e12`, its two
options (1: fix the mock in a separately authorized node; 2: amend the
contract), the source recommendation (option 1), and the decision owner
verbatim:

> Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge.

The recorded owner answer selects option 1. Option 1 changes no contract text:
`AI_DELEGATION_AUTHORITY.md` stays authoritative and byte-identical, so no
contract amendment requiring Astra design authority occurred. This record
claims no Astra audit or architecture signature for the fix; Astra's authority
and required audits under User decision M5 are unchanged. The addendum is a
merged historical record and is not edited here; whether ledger item A5 is
closed in the open-decisions ledger is the ledger owner's disposition, not this
record's. The addendum's "missing-grant binding remains UNDETERMINED" note is
untouched: the fix keeps the original `UNKNOWN_GRANT` behavior for missing
grants, and the node's class B characterization of that case stands.

## 3. Scope of the authorization

For this node only, the decision supersedes the node specification's
"Test-only: no mock, contract or flag change" acceptance item and the class C
"record a minimal reproduction and stop (no fix)" instruction, and authorizes
exactly:

1. The `call_tool` precedence fix: after actor registration and identifier
   well-formedness, an existing grant bound to another agent returns
   `UNKNOWN_ACTOR` before deny/allow tool-list rejection. All other check order
   and existing-grant behavior is kept; missing grants still reach
   `UNKNOWN_GRANT` after the tool lists.
2. Replacing the class C characterization pin with a conformance regression
   (`agent-2` on `g-1` → `UNKNOWN_ACTOR`, state unchanged; also with
   `no_such_tool`).
3. Updating the evidence map rows accordingly (the checker's status rules still
   hold §0 and §7 at PARTIAL for the remaining gaps).
4. Removing `DECISION_REQUIRED.md` and finishing with `STATUS: READY`.

Necessary harness consequence, recorded as a deviation in the validation
record: the seeded differential oracle
`reference/ai_delegation/ai_delegation_property_support.py::Model.predict_call_tool`
and one exact-code expectation in
`reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_deny_and_unknown_tools`
required the same precedence alignment to keep the differential suite green.
The addendum's option-1 inventory (I-S1) lists `Model.predict_call_tool` among
option 1's primary sites. No other oracle behavior changed.

Everything else stays locked: the contract text, `runtime/ARCHITECTURE.toml`,
`delegated_execution_enabled = false` and all eleven always-false flags, the
two locked kernel blobs, `reference/v0.3-rc1/**`, and every lock in
[PROGRAM_DECISIONS_20260928.md](PROGRAM_DECISIONS_20260928.md) §5. No policy
value, new protocol command, enablement, funds, provider call or production
behavior is authorized or introduced. This record does not authorize a merge;
merge authorization remains with the User.

## 4. Where the decision is cited and implemented

- [Partial-closure validation record](../../validation/2026-10-26-plan-aid-contract-map-partial-closure/README.md)
  — opening basis, changed files, deviations, and the fix-round-1 section.
- [AI delegation contract evidence map](../status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md)
  — §0 Basis update note for 2026-11-18.
- [Docs index](../README.md) — the AI delegation contract entry links this
  record.
- Implementation: `reference/ai_delegation/ai_delegation_mock.py::AiDelegationMock.call_tool`;
  regression `reference/ai_delegation/test_check_order_precedence.py::CheckOrderPrecedenceTests.test_actor_binding_precedes_tool_lists`
  and the pair-matrix cells for check 1 versus check 2.

## 5. Non-claims

1. This record adds no decision and selects no option beyond the verbatim text
   it preserves.
2. The recorder is the builder. This is not a non-author exact-HEAD review, an
   Astra audit, or an acceptance.
3. The owner's delegation is preserved as delivered by the supervisor; no
   independent cryptographic or out-of-band confirmation is claimed.
4. At the time of writing, no exact-head CI exists for the commit that will
   carry this record. CI evidence is recorded in the PR closure, not by a
   further commit (AGENTS.md §11).
5. No §5 lock is opened, no ledger row is closed, no grade is promoted, and no
   production readiness, durability, distributed fencing, bank exactly-once,
   chain finality or legal compliance claim is made.
