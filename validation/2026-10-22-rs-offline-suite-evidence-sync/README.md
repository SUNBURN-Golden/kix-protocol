# RS offline Node suites cited in the predicate and impact-table maps

Builder reading, not an Astra review and not an acceptance.

## Identity and scope

Node: `plan-plan-rs-offline-suite-evidence-sync` (loop-proposed, not in `.aiops/program.json`).
No issue and no task document under `docs/tasks/` exists for it. This is not ASTRA
program mode: no signer, no delivery marker. Depends on `plan-rs-verifier-binding-offline-tests`
and `plan-rs-model-gap-closure`.
Branch: `agent/kix-plan-plan-rs-offline-suite-evidence-sync`.
Starting HEAD and cached `origin/main`: `f1734e00e5a167dc18bfff1a873994bee124a3f7` (both
refs were equal). Remote freshness is unverified: the supervisor prohibits network
actions, which supersedes the session-start fetch. No commit, push or PR was made by the builder.

Scope: both evidence-map checkers (`.test.mjs` citations resolved by node:test name),
the RR-4 cells of `docs/status/RS_PREDICATE_EVIDENCE_MAP.md`, the IM-14/15/16/17/19/27
cells of `docs/status/RS_IM_EVIDENCE_MAP.md` (with the wording that became false), one
index hook and one index bullet in `docs/README.md`, and this record. No `*.mjs`, Move,
circuit, workflow, contract, `.aiops/`, `docs/tasks/`, `reference/v0.3-rc1/**` or locked
kernel file changed. The 2026-10-21 records are not edited (historical evidence).

## Existing coverage mapping (before the change)

| Item | Classification | Evidence |
|---|---|---|
| `protocol.yml` runs the eight suites in the `rights-scale` job | Covered | `.github/workflows/protocol.yml` steps `Offline manifest validation regressions` … `Offline verifier binding regressions` (lines 43–60 at this base). |
| RR-4 and IM-19 cite `witness-reconstruction.test.mjs` structurally | Not covered | The two maps linked it through ordinary Markdown only; the checker allowlist excluded `.test.mjs`. |
| IM-14/15/16/17/27 cite the other seven suites | Not covered | The cells cited records and `profile-constants.mjs`, not the test names. |
| Stale "not invoked by either workflow" wording | Present | RR-4 missing cell and §3 note, IM-19 missing cell and §3 note, `docs/README.md` line 233. |
| Checker positive control for a new symbol kind | Partially covered | Move and Python probes existed; none for node:test names. |

## Checker extension

Both `scripts/check_rs_predicate_evidence_map.py` and `scripts/check_rs_im_evidence_map.py`:

- the local-column path pattern is `reference/rights_scale/client/[a-z0-9-]+(?:\.test)?\.mjs`;
- `suffix_of(path)` returns `.test.mjs` for such a path, and `symbol_defined` resolves its symbol with
  `test_named`: the file must contain `test('<name>'` or `test("<name>"`. The semantics are the same
  existence-only semantics as `.py`/`.rs`/`.move`: nothing is executed and a passing name does not show
  that the test asserts the predicate;
- the match is a substring of the call text, so a nested `t.test('…'` or `await test('…'` also resolves,
  while a template-literal name such as ``test(`gamma_${x}`…)`` is not citable (the cited names below are
  all literal; names containing `:`, `/` or spaces are fine, none contains `|`, a backtick or `::`);
- self-test additions: a positive control (`alpha_probe` and nested `beta_probe` resolve; `alpha_prob`,
  a comment-only `delta_probe` and a template-literal prefix `gamma_` do not), and a negative case
  `misspelled node:test name` that appends
  `` `reference/rights_scale/client/witness-reconstruction.test.mjs::populated_tre` `` to the RR-4 local cell
  (predicate checker) or the IM-19 local cell (impact-table checker). `populated_tre` is a substring of the
  real name `populated_tree` and of the file, so the case shows that the rule is the stricter `test('name'`
  and not text presence; it must fail with `is not defined in the file`.

## Citations added, with the asserting body

Paths are relative to `reference/rights_scale/client/`; line numbers are those of the file at this base.
"Asserts" is a builder reading of the quoted body; every suite shares the client Poseidon where it hashes,
so none is an independent cryptographic check.

### RR-4 (predicate map, column 6) — status unchanged `COVERED_LOCALNET`

- `witness-reconstruction.test.mjs::dense_fixture_matches_existing_move_known_answers` (line 110):
  `assert.equal(emptyRoot, 1241388…919922n); assert.deepEqual(noteRoots, [1343515…, …]); assert.equal(revocationRoots[1], …); assert.equal(revocationRoots[2], …);`
  with the comment "Copied from sui/tests/root_math_tests.move; originally generated with the SAME circomlibjs
  primitive. No Move execution is claimed by this check." Asserts the dense oracle equals the Move known answers.
- `::populated_tree` (line 126): `test('populated_tree', () => accepts(makeFixture()));` — asserts the full reconstruction
  from synthetic events is accepted against the injected NoteTree/RevocationState projections.
- `::reordered_notes` (line 127): splices `[4, 1, 3, 0, 2]` into the note events and `await accepts(fixture)` — asserts the
  event list is re-ordered by index before rebuilding.
- `::note_root_mismatch` (line 154): `rejectsChange(f => { f.tree.root = String(BigInt(f.tree.root) + 1n); }, 'REBUILT_NOTE_ROOT_MISMATCH:' + sourceName)`
  — asserts an altered object root is rejected with that diagnostic after exactly the allowed reads.
- `::omitted_nonmaximal_revocation` (line 169): `f.revocations.splice(0, 1); // same final root, fewer events: the count must catch it`
  rejected with `REBUILT_REVOCATION_ROOT_MISMATCH:…` — asserts the revocation count guard.

### IM-14 (impact map, column 7) — status unchanged `PARTIAL`

- `spend-witness.test.mjs::commitment_binding: isolated secret, slot, generation, commitment and coherent domain changes` (line 104):
  `for (const [field, value] of [['secret','18'],['slot','701'],['generation','5'],['commitment','1']]) … f.note[field] = value; await assert.rejects(() => invoke(f), {message: 'NOTE_COMMITMENT_MISMATCH'});`
  and a case where `f.tree.domain = 78n; f.note.domain = '78'` ("Both domains agree, but commitment still binds domain 77")
  also rejects. The fixture commitment is `H([17n, 700n, 4n, domain, 1n])` (line 16), i.e. the five-input layout.
- `mint-note.test.mjs::mint_witness_binding` (line 168): `assert.deepEqual(state.input, expectedInput)` where the expected
  commitment is `p([17n, 700n, 4n, 77n, 1n])` (line 15) and the input keys are exactly
  `commitment, slot, generation, domain, secret, inverse`; `(17n * inverse) % FR === 1n`.
- Effect: the sentence "no test pins the commitment layout" in the missing cell is replaced by a statement that the client-side
  offline tests do, with a shared Poseidon, while no Move or circuit test does. The row stays `PARTIAL`.

### IM-15 — status unchanged `COVERED_LOCALNET`

- `spend-witness.test.mjs::distinct_indices: note insertion 2 and revocation slot 700 use different paths and leaves` (line 149):
  `assert.deepEqual(w.input.noteBits, …Math.floor(2 / 2 ** i) % 2…); assert.notDeepEqual(w.input.noteBits, slotBits.map(String));`
  with `foldPath(f.note.commitment, noteSiblings, noteBits) === noteRoot` and `foldPath(3n, revocationSiblings, slotBits) === revocationRoot`
  — asserts the note tree is indexed by insertion index and the revocation tree by slot.
- `::context_binding: each gate limb, challenge and expiry changes context alone` (line 182): for `low`, `high`, `challenge`, `expires`
  `assert.notEqual(changed.input.context, base.input.context)` while `publicSignals[0,1,2,4,5]` stay equal — asserts the context binding.

### IM-16 — status unchanged `PARTIAL`

- `ptau-header.test.mjs::source-informed: ptauPower reaches a later header past distinct and empty sections` (line 47):
  builds a four-section file and `assert.equal(ptauPower(bytes), 0x01020304)` — asserts only that the phase-1 power is read from a
  `.ptau` header. It does not assert the recount of constraints or the ceremony power chosen by RS-2, which is why the row stays `PARTIAL`
  with the same missing sentence. The citation is supplemental evidence for the phase-1 power read, not for the policy sentence.

### IM-17 — status unchanged `PARTIAL`

- `zk-policy-v2.test.mjs::source-informed: synthetic manifest control and matching explicit pins pass` (line 76):
  `assert.doesNotThrow(() => requirePhase2ManifestV2(validManifest(), {depth: DEPTH, slotBits: SLOT_BITS, profileVersion: PROFILE_VERSION, rootHistoryK: ROOT_HISTORY_K}))`
  and a manifest with `rootHistoryK = ROOT_HISTORY_K + 1` passes both without a pin and with a matching explicit `rootHistoryK` pin.
- `verifier-binding.test.mjs::artifacts_control` (line 170): the coherent synthetic manifest returns exactly `['manifest', 'hash', 'mintVK', 'spendVK']`
  with and without a pin, and the read trace equals `FULL_ARTIFACT_TRACE`.
- `::manifest_pin_mismatch` (line 183): a zero digest and a digest of other bytes each reject with `CIRCUIT_MANIFEST_PIN_MISMATCH` after only the manifest read.
- Effect: none on the missing cell. The `K` value stays UNDETERMINED and the "other keys" ambiguity is not decided; no Move, Python or Rust test reads a manifest, as the cell already says.

### IM-19 — status unchanged `PARTIAL`

- `witness-reconstruction.test.mjs::populated_tree`, `::unrelated_show_events` (line 133: a foreign-show note and revocation event are spliced in and
  `await accepts(fixture)`), `::revocation_count_mismatch` (line 163: `f.rev.revocations` + 1 rejected with `REBUILT_REVOCATION_ROOT_MISMATCH:…`)
  — assert that the witness inputs are rebuilt from public event data with only the named object reads
  (`rejectsChange` also asserts `spy.calls` equals `allowedReads`).
- `admission-packet.test.mjs::packet_contains_only_public_fields` (line 181): the packet keys are exactly
  `noteRoot, revocationRoot, nullifier, challenge, expiresMs, proof, publicSignals`, and `assertPublicStructure(packet)` rejects any nested key in
  `{note, secret, slot, generation, inverse, input, noteBits, noteSiblings, revocationSiblings}`.
  This concerns the client-built packet. It is not an assertion about the Move `consume_private` call, so the missing-cell sentence about the gate call stays,
  reworded: "no Move test asserts that the secret is absent from the gate call". The row stays `PARTIAL` as the reading note already said.

### IM-27 — status unchanged `COVERED_LOCALNET`

- `zk-helpers.test.mjs::source-informed: proof A / B.x0 / B.x1 / C order and widths` (line 79): `assert.equal(bytes.length, 128); assert.deepEqual(bytes, expectedProof());`
  with each 32-byte word at offsets 0, 32, 64, 96 compared to its literal word.
- `::source-informed: VK sign flags stay in their own compressed points` (line 134): `assert.deepEqual(vkBytes(key), expected)` with the sign flag `0x80` at offsets 31, 95, 159, 295 only.
- `admission-packet.test.mjs::public_signal_layout_rejections` (line 200) and `mint-note.test.mjs::mint_public_signal_layout_rejections` (line 205): wrong order,
  missing, extra and altered-at-each-position signals each `assert.rejects(invoke, {message: 'CIRCUIT_PUBLIC_INPUT_LAYOUT'})` with the verifier and encoder never reached.
- `verifier-binding.test.mjs::check_verifier_key_pin_rejections` (line 281): differing manifest hash, one mint byte, one spend byte, truncated, empty and swapped keys each
  `VERIFIER_KEY_PIN_MISMATCH` after the full artifact trace; `::check_verifier_object_pin_rejections` (line 253): other package, type name, module, and address-owned, shared and object-owned
  ownerships each `VERIFIER_OBJECT_PIN_MISMATCH` with trace exactly `['getObject']`.
- Effect: none on the missing cell (the manifest is a single-party local fixture and pins no operational Verifier ID). The caller-supplied-key half is shown by the Move and
  Python citations already present, and the Verifier decoding is a mock (`Verifier.parse` is a stub in `verifier-binding.test.mjs`).

All eight suites are now cited at least once: `zk-policy-v2` (IM-17), `zk-helpers` (IM-27), `ptau-header` (IM-16),
`witness-reconstruction` (RR-4, IM-19), `spend-witness` (IM-14, IM-15), `admission-packet` (IM-19, IM-27),
`mint-note` (IM-14, IM-27), `verifier-binding` (IM-17, IM-27). Citation totals: predicate map 168 → 173,
impact-table map 179 → 197.

## Status changes

**None.** No row changed status and no row was promoted `PARTIAL` → `COVERED_*`. Both `Counts:` lines are unchanged
(predicate: `COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2`;
impact table: `COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2`).
A candidate promotion (IM-14 on the client-side commitment tests; IM-19 on the packet test) was considered and not made: the quoted bodies assert client
construction with a shared Poseidon or a client packet, not the whole policy sentence, so that judgement is left to Astra.

## Wording changes (same status)

| Place | Change |
|---|---|
| Predicate map RR-4 missing cell | "see the supplemental offline RR-4 reading note below (local Node 24 pass; not invoked by either workflow)" replaced by the statement that the column-6 offline suite runs in the `rights-scale` job step `Offline witness reconstruction regressions`; retention stays UNDETERMINED. |
| Predicate map §3 RR-4 note | Rewritten: the names are structured citations, the workflow runs the suite, the 2026-10-21 execution record is superseded on that point, no exact-head CI claim, no independent cryptography, status unchanged. |
| Impact map IM-19 missing cell | "…but neither workflow invokes it. No test asserts that the secret is absent from the gate call" replaced by the workflow step name, the BCS/transport non-claim, the packet-test scope and the retained gate-call gap. |
| Impact map IM-14 missing cell | "no test pins the commitment layout" replaced by the client-side tests, the shared Poseidon and the absence of any Move or circuit test. |
| Impact map §3 IM-19 note | Replaced by a note covering all eight suites and the six rows; says no row changes status. |
| Both maps §0 and §1 | Node line mentions this update and the base; §1 states that a `.test.mjs` symbol is a node:test name located as `test('name'` / `test("name"`. |
| `docs/README.md` line 233 | Hook now says that at the 2026-10-21 record's head no workflow ran the suite (wired since, see the next entry). The record itself is unchanged. |
| `docs/README.md` | New bullet for this record in the 2026-10-22 section. |

`grep -rnE "not invoked by either workflow|neither workflow invokes|invoked by either" docs validation` returns no line after the change.

## Commands actually run and results

Run from the node worktree root; Python 3 standard library only.

| Command | Result |
|---|---|
| `git rev-parse HEAD origin/main` | both `f1734e00e5a167dc18bfff1a873994bee124a3f7` (no fetch: network prohibited) |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20`; unchanged |
| `python3 scripts/check_rs_predicate_evidence_map.py` | exit 0: `rows=23 expected=23 citations=173 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2` |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0: `detected misspelled node:test name (RR-4: local citation … witness-reconstruction.test.mjs::populated_tre is not defined in the file)`, `self-test: pass` |
| `python3 scripts/check_rs_im_evidence_map.py` | exit 0: `rows=30 expected=30 citations=197 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2` |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | exit 0: `detected misspelled node:test name (IM-19: … is not defined in the file)`, `self-test: pass` |
| The complete `Stdlib offline document checks` block of `.github/workflows/protocol.yml` (27 commands: status register, RS profile traceability, read-model source map, docs index, I12 proof ids, delegation layer matrix, both RS maps, TL predicate map, contract error codes, adapter identity map, v5 transition map, readiness map — each plain and `--self-test` — and `check_stage5_host.py --self-test`) | all 27 exit 0; the docs index reports `scanned=203 indexed=168 allowlisted=35` |
| `node --test reference/rights_scale/client/zk-policy-v2.test.mjs` (Node 24.19.0, toolchain copy) | `tests 267`, `pass 267`, `fail 0` |
| `node --test reference/rights_scale/client/zk-helpers.test.mjs` | `tests 166`, `pass 166`, `fail 0` |
| `node --test reference/rights_scale/client/ptau-header.test.mjs` | `tests 34`, `pass 34`, `fail 0` |
| `node --test` on `witness-reconstruction.test.mjs` and `spend-witness.test.mjs` | **Not run to completion.** `ERR_MODULE_NOT_FOUND` for `@mysten/sui` / `circomlibjs`: the worktree has no `node_modules`, none exists elsewhere on this host, and installing dependencies needs the network the supervisor forbids. `admission-packet`, `mint-note` and `verifier-binding` need the same packages and were not attempted. The cited names in those five suites are verified by the checker (name present) and by reading the bodies above, not by execution. |
| `grep -rnE "not invoked by either workflow\|neither workflow invokes\|invoked by either" docs validation` | no output |
| `git diff --check` | exit 0 |
| `git status --porcelain` | modified: the two checkers, the two maps, `docs/README.md`; new: this record |
| `git diff --stat HEAD -- reference .github docs/contracts .aiops docs/tasks runtime` | empty |

The Rust workspace tests were not run: the patch touches no `runtime/` file and `ktx-kernel.yml` classifies a docs/scripts-only change as skippable.

## Preservation

Locked blobs verified before and after (values above). `reference/v0.3-rc1/**`, `.aiops/`, `docs/tasks/`, `.github/`, `docs/contracts/`, every `*.mjs`, the Move sources and the circuits are unchanged (empty diff above).

## Changed paths

- `scripts/check_rs_predicate_evidence_map.py`
- `scripts/check_rs_im_evidence_map.py`
- `docs/status/RS_PREDICATE_EVIDENCE_MAP.md`
- `docs/status/RS_IM_EVIDENCE_MAP.md`
- `docs/README.md`
- `validation/2026-10-22-rs-offline-suite-evidence-sync/README.md`

## Non-claims

- The checkers prove that a cited node:test name exists in the file, not that the test passes, runs in CI or asserts the predicate.
- Five of the eight suites were not executed by this builder (dependencies unavailable offline); no exact-head CI result is claimed for any suite or for this node. Exact-head CI and the A2 review are delivery gates outside this record.
- No Sui, ZK, localnet or chain run; no real object BCS decoding, proof or key verification; shared Poseidon means no independent cryptographic proof.
- No status, grade, owner or operational value changed (K, depth, shard count, retention, Verifier ID pin, `MAX_BUNDLE_CHAIN`, `IssuerCap` stay UNDETERMINED with their owners); the operational count stays 0.
- No contract violation found; no contract-undefined characterization added beyond those the cited suites already label.

## Remaining uncertainty and follow-up candidates

- Whether IM-14 or IM-19 may be promoted on the quoted bodies is a question for Astra; the builder kept both `PARTIAL`.
- The `.test.mjs` match is a plain substring match: the text `test('name'` inside a comment or string would also resolve, and a template-literal test name cannot be cited.
- The `validation/2026-10-1[0-9]-…` path pattern is deliberately unchanged, so this record is linked by ordinary Markdown and not as a structured citation.
