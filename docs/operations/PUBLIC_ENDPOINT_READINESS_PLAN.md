# Public endpoint unlock readiness plan

Status: document-only planning; the public endpoint lock remains closed.
Node: `public-endpoint-readiness-plan` (canonical dependencies: `[]`).
Source: [`.aiops/program.json`](../../.aiops/program.json), pinned at
`4052dccfcbeaa95c1f21c2973ef530e5d5905759`; this is the original node,
not a new execution plan or completion claim for any other node.

## Authority and current boundary

[PROGRAM_DECISIONS_20260928 §5](../decisions/PROGRAM_DECISIONS_20260928.md)
requires authentication, TLS, an operations owner, an incident response plan,
and explicit User approval before opening a public operational endpoint.
[PROGRAM_ROADMAP_20260930 §5](../decisions/PROGRAM_ROADMAP_20260930.md)
keeps the gate at `127.0.0.1`. The current [development plan](../DEVELOPMENT_PLAN.md),
[Task 005](../tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md),
[Model 1](../decisions/AUTHORITY_MODEL_1.md), and [AGENTS.md](../../AGENTS.md)
continue to apply. Candidate scope and pending external prerequisites are not
execution approval.

The [OpenAPI boundary](../contracts/openapi/README.md) is unchanged:
`actor` is a fixture string, not authentication; the catalogue has no `servers`
or security scheme. The gate has no TLS or public deployment. `/health` means
liveness; `/ready` means local reference readiness, not production readiness.
Local replay and a successful receipt do not prove external delivery, chain
finality, bank exactly-once or production durability. The readiness journal
remains optional, local, single-process and single-writer under D-3; all
production/truth/conformance/readiness flags remain false.

This change adds only this plan. It authorizes no listener, tunnel, proxy,
public DNS, certificate issuance, deployment, provider call, spending, secret
or repository setting change. The kernel blobs and `reference/v0.3-rc1/**`
remain unchanged. All other §5 locks remain: real funds/PG/bank/KYC, regulated
credit, testnet/mainnet, R2/custom replication/consensus/storage, PR #11
integration, coin/TIX and stable SDK/public publishing. The separately gated
TL-2 localnet exception does not apply here.

## Required evidence before a future unlock decision

The following are preparation requirements for a separately authorized task,
not selected product policies or changes to current contracts.

| Area | Evidence the future decision packet must contain | Responsible role and unresolved decision |
|---|---|---|
| Authentication and authorization | Threat model identifying clients, operators and machine identities; proposed trust boundary; verified identity-to-actor binding; action/resource/scope authorization; credential issuance, rotation, revocation and compromise procedures; negative tests for missing, expired, revoked, forged and cross-scope credentials. Caller-supplied actor and trace headers cannot establish authority. | User appoints security/identity owner; appointment UNDETERMINED. Scheme, session lifetime, administrative privileges and delegation policy: DECISION_REQUIRED · Astra, with User approval where required. |
| TLS and network boundary | Proposed ingress-to-executor diagram; certificate/domain custody and renewal owner; trust validation and expiry/rotation failure tests; proof of which hop terminates TLS and protection of every subsequent hop; prevention of direct unauthenticated backend access and spoofed proxy identity. No public address or service is created by this plan. | User appoints operations/security owner; appointment UNDETERMINED. TLS termination topology and accepted security profile require separate review/approval; provider-specific constraints remain UNDETERMINED with provider technical owner. |
| Operations ownership | Named accountable owner and backup accepting responsibility; access matrix; inventory of service, data and credential custody; change/rollback authority; monitoring and alert routing; capacity/failure assumptions; recovery rehearsal and evidence access. | User names the operations owner and backup: UNDETERMINED. I11's named lifecycle approvers are not automatically public-service operators. Availability, response times, capacity, RTO/RPO and support coverage: DECISION_REQUIRED · Astra; no SLO is invented. |
| Incident response | Approved runbook covering authentication compromise, certificate expiry, overload, state divergence, suspected data disclosure and UNKNOWN outcomes; named incident commander/backup; containment, evidence preservation, reconciliation, recovery and reopening criteria; isolated rehearsal records. | Operations/security owner appointed by User: UNDETERMINED. Severity thresholds and escalation times: DECISION_REQUIRED · Astra. Notification duties and retention/deletion values: UNDETERMINED, User supplies jurisdiction/parties and legal/privacy counsel answers. |
| Explicit release authority | Evidence references pinned to exact source/configuration, independent review and required audits, actual exact-head KTX and KIX results, operations acceptance, unresolved-item register, and a User decision identifying the precise endpoint/environment/scope permitted. | User alone approves unlock; publication, audit PASS or CI success does not grant activation. Separate source/architecture gates remain required. |

Existing named owners in [FIRST_BATCH_OPEN_INPUTS](../contracts/FIRST_BATCH_OPEN_INPUTS.md)
are preserved: I09 is User policy selection plus developer measurement; I10
is User-supplied jurisdiction/parties plus legal/privacy review; I13 is
operations/security responsibility, budget and actual preservation/recovery
verification. I02/I03 remain User and Toss contract/sales/technical owners;
I04 remains Toss technical owner. Those inputs are not answered by public
TLS or authentication. No legal, tax, accounting or provider answer is inferred;
any such new answer remains UNDETERMINED with the relevant external owner.

## Incident procedure to prepare and rehearse

1. Detect and record the symptom, source/configuration identity, affected scope,
   operation identities, timestamps and observations. Keep secrets and personal
   payloads out of diagnostics; the approved retention/access policy is still
   required. Existing trace identifiers aid correlation, not proof of identity.
2. The appointed commander contains the affected ingress and stops new affected
   execution using approved controls. Preserve single-writer and UNKNOWN fencing;
   do not start a second writer or assume a failed transport means no effect.
   Credential/certificate rotation must follow the separately approved custody plan.
3. Preserve original inputs, first results, source positions, late observations
   and obligations. Do not delete evidence, force-release, automatically retry,
   poll or resend uncertain work. Reconcile UNKNOWN before authorizing any new
   external execution; historical replay is not fresh authority.
4. Diagnose and rehearse recovery against an approved backend and authority
   model. The optional local readiness journal is not an operational ledger,
   backup guarantee or audit evidence. Verify restored state, authorization and
   current source cuts without changing locked kernels or redefining contracts.
5. The appointed owner records recovery evidence and independent review.
   Reopening requires the applicable explicit release/unlock authorization;
   an incident workaround cannot lift another lock. Legal/privacy counsel
   determines notification duties, and authorized humans handle communications.
   No stakeholder messages are sent by this task.

## Evidence collection sequence and stop conditions

1. User appoints accountable operations/security owners and backups. Collect
   unresolved inputs without substituting agent defaults for policy values.
2. In separate authorized work, prepare authentication/TLS architecture and
   operations/incident proposals. Route product policy or new protocol commands
   to DECISION_REQUIRED · Astra; obtain any required architecture audit before
   dependent implementation. No canonical dependency is added to this node.
3. Once those designs and scope are approved, a separate implementation task
   may collect isolated non-production negative/security/recovery evidence.
   Browser CORS nodes, provider sandbox work, backend adoption and cross-repository
   integrations retain their own original dependencies and source gates. CORS
   permission is not authentication; sandbox evidence is not real-funds approval.
4. Assemble the exact-source decision packet described above. Missing owner,
   unresolved security/policy choice, missing external answer, failed test or
   absent required audit blocks public unlock. Keep UNDETERMINED/UNKNOWN visible.
5. Only a separate explicit User decision can open the public lock, and only
   within its stated scope. Implementation or release work is outside this node.

## Coverage mapping and acceptance

| Requirement | Existing coverage at the pin | Gap addressed by this document |
|---|---|---|
| Public lock and loopback gate | Sufficient for the current local boundary: decision §5, roadmap §5, `integration_gate/test_http_gate.py::test_refuses_non_loopback_bind` and `test_loopback_refusal_still_applies_with_a_readiness_directory` | No new bind behavior or duplicate regression test needed. |
| Authentication/TLS unlock preparation | Partial: OpenAPI README explicitly excludes authentication/TLS; catalogue pin check rejects invented public servers/security schemes | Required future evidence, responsible roles and unresolved decisions enumerated above. Public security remains unimplemented and unqualified. |
| Operations owner and incident preparation | Partial: FIRST_BATCH_OPEN_INPUTS I09/I10/I13 and D-3 state constraints; `test_health_is_not_readiness`, `test_drain_keeps_liveness_and_refuses_commands`, readiness fault suite | Owner appointment, incident scenarios, containment/evidence/recovery sequence and unlock stop conditions documented. No operational appointment or rehearsal claimed. |
| Plan document and unchanged contracts | Not previously covered by a dedicated endpoint readiness plan | This file provides the four-area plan, authority/evidence checklist and explicit non-deployment boundary. |

Acceptance for this implementation stage: this plan covers all four §5 areas
and User approval; policy/external uncertainties retain status and owner;
runtime, CI, immutable inputs and protected paths are unchanged; available
local document/contract checks are recorded in the handoff. No new executable
tests are needed for a document-only addition.

The Mac application must next obtain independent A2 review, publish its Draft
candidate, collect actual exact-head hosted KTX kernel verification and KIX
protocol verification and obtain separate final supervision. Draft workflows
can skip: absent/skipped CI is not full verification, and the application must
obtain actual required evidence without weakening CI. This implementation
checkpoint is not legacy DONE, checks-green acceptance, audit PASS, merge,
post-merge proof, release or program completion. Record final CI in the external
handoff rather than making a self-referential evidence commit.
