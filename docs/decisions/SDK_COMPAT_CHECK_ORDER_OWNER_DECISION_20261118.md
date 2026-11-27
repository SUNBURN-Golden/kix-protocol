# SDK manifest verifier §4 check order — owner decision location record (2026-11-18)

Node `plan-plan-sdk-compat-manifest-clause-evidence`, branch
`agent/kix-plan-plan-sdk-compat-manifest-clause-evidence`; issue: none. Document
date: 2026-11-18. Written in the node's fix round 1 as the remedy named by the
round-1 independent review.

Status: location record. This document creates no new decision, does not mark
anything as reviewed, and changes no contract, grade, ledger row or node state.
The recorder is the builder, not the decision-maker and not a non-author
reviewer. It records, under [AGENTS.md](../../AGENTS.md) §5, a human
authorization that was granted outside this repository and delivered to the
build session by the supervisor, so that the authorization is verifiable
in-repo instead of resting on builder-authored artifacts alone.

## 1. The decision and its provenance

Decision-maker: JunTae (owner), delegated through the KIX supervisor on
2026-11-18, delegation batch tag `[pt224u]`. The decision answers this node's
class C stop (`DECISION_REQUIRED.md` at the worktree root during the stopped
build, since removed as the decision itself instructs).

Delivery channel: the supervisor-generated builder prompt for this node's
build session, section `=== Owner decision (answers the earlier
DECISION_REQUIRED; authoritative for this node) ===`. The prompt file is
supervisor-owned and lives outside the repository, at
`/workspace/kix-run/logs/plan-plan-sdk-compat-manifest-clause-evidence_build_a0_codex0.prompt.md`
(lines 260–262 at the time this record was written). The same text is preserved
in the supervisor's node state files
`/workspace/kix-run/state/plan-plan-sdk-compat-manifest-clause-evidence.decision.md`
(the stop) and
`/workspace/kix-run/state/plan-plan-sdk-compat-manifest-clause-evidence.decision_answer.md`
(the answer). Builder sessions edit the worktree only and cannot write those
channels.

Verbatim decision text (prompt lines 261–262, line wrapping as delivered):

> Owner decision (KIX supervisor, delegated by JunTae 2026-11-18 [pt224u]; authoritative for this node).
> Option 1 approved and authorized in this node (integration step 1, producer qualification; the contract stays unchanged): in sdk/compat/verify_compat.mjs move the profile byte-hash check ahead of the OpenAPI, generator/toolchain and SDK output checks so the order matches COMPATIBILITY_MANIFEST_V1 §4 exactly; add a regression (the C4 repro must now fail at the profile hash first); reclassify C4-CHECK-ORDER in the map and replace the checker's live class-C anchor guard accordingly. Do not change SDK output bytes, OpenAPI files, the manifest format or any vector; if the producer qualification tuple pins verify_compat.mjs bytes, update that pin in the same PR and say so in the validation record. Remove DECISION_REQUIRED.md and finish with STATUS: READY.

Corroboration, not independent verification: the same 2026-11-18 `[pt224u]`
delegation tag appears on 24 lines of the supervisor's loop ledger
(`/workspace/kix-run/AUTOLOOP_RESULT.md`, also outside the repository) for that
day's batch of node dispositions (drops, CI re-runs, fix rounds), including this
node's FIX row. The builder cannot cryptographically verify the owner's
delegation; this record preserves the supervisor-delivered text as received and
names its channel. If the owner or supervisor disputes the text, this record
and the change it authorizes must be revisited by them, not by a builder.

Why this record exists: the round-1 independent review (supervisor-commissioned,
read-only) accepted the verifier fix as technically sound — "a pure relocation
of the profile read+hash block (no logic change)" fixing "a real class C
discrepancy rather than weakening anything" — but blocked because the
authorization was unrecorded in-repo, and named the remedy: "add the pt224u
decision record in-tree (a follow-up docs commit referencing the exact
authorized change), or revert to the diagnostic-only delivery". The decision's
genuineness was checked against the supervisor-owned prompt, state files and
ledger above before writing this record. The sibling node
`plan-plan-aid-contract-map-partial-closure` received the same delegation tag
for its own §7 check-order stop and recorded it in the same genre
(`docs/decisions/AI_DELEGATION_CHECK_ORDER_OWNER_DECISION_20261118.md`, present
on cached `origin/main` `b2357bc4d3f6de2e7dd0a09f53596f24d0a944f7` but not at
this branch's base `22d05a0c82693ad4575a72c2d342b4e47114447f`, so it is named
here as a source pointer, not a branch Markdown link). The in-repo genre
precedents at this base are
[OPENAPI_CATALOGUE_PROMOTION_OWNER_DECISION_20261009.md](OPENAPI_CATALOGUE_PROMOTION_OWNER_DECISION_20261009.md)
and [POLICY_DEEPENING_OWNER_DECISION_20261009.md](POLICY_DEEPENING_OWNER_DECISION_20261009.md).

## 2. The stop it answers

The stopped build reported a class C discrepancy under AGENTS.md §8:
[COMPATIBILITY_MANIFEST_V1](../contracts/sdk/COMPATIBILITY_MANIFEST_V1.md) §4
requires the verifier check order parse → manifest fields/kind → profile byte
hash → OpenAPI references → generator/toolchain → SDK output → vectors →
sidecar, but `sdk/compat/verify_compat.mjs` at the supplied base performed the
OpenAPI, generator/toolchain and SDK output checks before the profile byte
hash. Fail-closed error collection does not remove the ordering requirement.

The stop was recorded in the supervisor-owned state file named in §1 (not in
an in-tree ledger addendum): it offered option 1 (a separately authorized fix
node moving the profile-hash check and adding a regression), option 2 (an
explicitly authorized contract amendment making §4 order non-normative) and
option 3 (diagnostic-only delivery with the violation retained as a merge
blocker), recommended option 1, and named the User as decision-maker. The
minimal reproduction is
[repro_c4_check_order.py](../../validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py):
two corrupted digests in a temporary manifest with a valid sidecar; on the
original verifier the contract-only diagnostic preceded the profile diagnostic.

The recorded owner answer selects option 1 and authorizes it within this node
rather than a new one. Option 1 changes no contract text:
`COMPATIBILITY_MANIFEST_V1.md` stays authoritative and byte-identical, so no
contract amendment requiring Astra design authority occurred. This record
claims no Astra audit or architecture signature for the fix; Astra's authority
and required audits under User decision M5 are unchanged. Whether any
open-decisions ledger row for this stop is closed is the ledger owner's
disposition, not this record's.

## 3. Scope of the authorization

For this node only, the decision supersedes the node specification's
"SDK sources … byte-unchanged" acceptance item for exactly the two files it
names, and the class C "record a minimal reproduction and stop (no fix)"
instruction, and authorizes exactly:

1. The `sdk/compat/verify_compat.mjs` relocation: the profile read+hash block
   moves ahead of the OpenAPI, generator/toolchain and SDK output checks so
   the diagnostic order matches contract §4. No logic change; fail-closed
   behavior and the error set are otherwise unchanged.
2. A regression: the new
   `sdk/conformance/conformance.test.mjs::manifest verifier reports failures in contract order`
   test (canonical parse gates all later checks; the ten §4 stage diagnostics
   appear in contract order), and the two-fault repro updated so the profile
   hash drift is the first diagnostic and the verifier exits 1.
3. Reclassifying C4-CHECK-ORDER in the evidence map to COVERED and replacing
   the checker's live class-C anchor guard with the stage-order drift guard
   over the verifier source plus the required conformance-test citation.
4. Removing `DECISION_REQUIRED.md` and finishing with `STATUS: READY`.

The decision's conditional pin clause was checked: the producer qualification
tuple `docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json` on cached
`origin/main` lists 18 artifact entries and none pins `verify_compat.mjs`
bytes, so no tuple pin update was needed; the validation record says so.

Everything else stays locked: the contract text, SDK output bytes, OpenAPI
files, the manifest format, all manifests/profiles/sidecars/vectors, generated
SDK files, `reference/v0.3-rc1/**`, `.aiops/`, `docs/tasks/`, the two locked
kernel blobs, and every lock in
[PROGRAM_DECISIONS_20260928.md](PROGRAM_DECISIONS_20260928.md) §5. No policy
value, new protocol command, enablement, funds, provider call or production
behavior is authorized or introduced. This record does not authorize a merge;
merge authorization remains with the User.

## 4. Where the decision is cited and implemented

- [Validation record](../../validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/README.md)
  — opening basis, changed files, deviations, and the fix-round-1 section.
- [SDK compatibility manifest evidence map](../status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md)
  — §1 basis note and §3 class C section cite this record.
- [Docs index](../README.md) — this node's validation-index entry links this
  record.
- Implementation: `sdk/compat/verify_compat.mjs` (profile read+hash block);
  regression `sdk/conformance/conformance.test.mjs::manifest verifier reports failures in contract order`;
  guard `scripts/check_sdk_compat_manifest_evidence_map.py` (stage-order
  anchors and citation requirement); repro
  `validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py`.

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
   semantic-conformance, N/N−1, production-readiness, durability, distributed
   fencing, bank exactly-once, chain finality or legal compliance claim is
   made. The map's coverage remains bootstrap catalogue-schema-binding only.
