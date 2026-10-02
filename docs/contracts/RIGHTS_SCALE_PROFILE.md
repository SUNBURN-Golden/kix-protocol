# Rights Scale public profile — RS-PUBLIC-1

2026-10-02 implementation proposal, localnet only. Direct user request: “실제 Move 구현은 아직 16슬롯 제한도 풀어서 우리의 원대한 계획에 맞는 원대한 슬롯으로 구성해줘”. This authorizes implementation work, not AIOPS activation, deployment, merge or production qualification. Independent architecture review and exact-head CI remain required. The [blueprint](../blueprints/rights-scale-v1/README.md) remains historical design evidence.

## Object and authority contract

New package: `reference/rights-scale-v1/sui`, module `kix_scale::rights`. Existing `reference/v0.3-rc1` Move/circuits/decoders and kernel locks are unchanged. Package-separated types cannot be mixed. No coin, actual funds or external payment calls.

- Immutable capacity 1..65,536 per show; a bounded implementation profile, not a measured service capacity or permanent protocol ceiling.
- Independent shared `InventoryPage` objects contain at most 256 slots. Slot n maps to page n/256 and offset n%256. The final page is truncated; ranges never overlap. 65,536 slots require 256 pages.
- ShowControl contains no page-ID vector or mutable issuance counter. Typed PageKey/ShardKey derive independent IDs from its UID. Claim is unique. Construction proceeds in bounded transactions. Seal requires every page and all 16 payment-reference shards. Issuance is blocked before seal; additions/resealing are blocked afterward.
- Hot-path issuer calls authenticate the transaction sender against the immutable issuer address, choosing the blueprint's sender-authenticated alternative to one owned IssuerCap. IssuerCap remains non-transferable construction/cancellation authority. Removing it from issuance does not prove scheduling throughput; gas-object contention still exists.
- All consuming ticket operations require the exact ShowControl and page, checking show ID, derived page ID, slot range, generation and version. Global cancellation writes ShowControl once; subsequent consuming operations reject its closed state.
- Direct issue and primary attestation require expected_generation. Issuance increments it. Refund frees inventory without resetting it. Cancellation of an unminted reservation increments it too. A stale request after refund/cancellation cannot issue a new right. This is stale-intent fencing, not off-chain first-result replay or retry permission after UNKNOWN.
- Payment references are 32 bytes; route is the first Blake2b256 byte modulo 16. Check the shard's show/index/derived ID. Table-backed references preserve primary/resale uniqueness across pages. Used/refunded references remain. Reservation cancellation removes its unused reference, while consuming the reservation generation.
- Direct issue, paid issue, gift/resale, admission, refund-duty events, revoke and cancellation retain legacy public semantics except the explicit profile changes above. Attester claims are not bank facts. Refund events do not move cash. Revocation does not reopen inventory. Refund after show cancellation remains rejected, matching the legacy characterization rather than inventing settlement policy.
- Page size 256 and shard count 16 are candidate engineering bounds, not measured optima. Changes require a reviewed profile revision.

## Deferred paths

Private proofs/RR-2/revocation trees, nullifier/challenge shards, verifier/manifest, GA allocation, delegated grants, Rust v5, generated SDK and Commerce binding remain pending. This package has no shield/private-consume function and cannot silently reuse a legacy proof. Public scale does not qualify private or delegated scale. Existing shows are not migrated.

Multiple issue calls in one valid PTB rely on Sui's transaction rollback. No split-transaction atomicity or dedicated bundle helper/bound is claimed. The localnet driver tests one failed cross-page PTB with unchanged first-page inventory. Concurrent overlapping bundles and a dedicated RS-C05 application bound remain pending.

## Evidence boundaries

Move scenario tests cover 15/16/17, 255/256/257, 1,024/16,384/65,536 construction and last-slot issue; incomplete seal, duplicate page/issue, wrong page/shard, cross-page payment-reference reuse, paid refund/reissue, stale issue after refund, cleanup after cancellation, gifts/resale/admission and duplicate admission. Legacy tests are run separately.

Large capacity is not the same as filling every slot or concurrent ticket sales. Functional tests do not establish gas limits, TPS/p99, production recovery, privacy or independent audit. Sequential public portions of RS-C01/03/06/07/08/15/16 are covered; concurrency and all deferred paths remain unqualified. Do not mark RS-0/RS-1/RS-4 or AIOPS nodes DONE from source existence. Reconcile this direct-user implementation evidence in a separately reviewed plan revision.

The disposable localnet driver additionally executes the public path on an actual one-validator chain at 1,024/16,384/65,536 capacities. It builds all ranges, issues the last slot, verifies rollback of a cross-page failed PTB, rejects stale issuance after refund, accepts the new generation and rejects issuance after cancellation. This still does not fill every slot, measure throughput or qualify fault tolerance.
