# Perf-probe pin addendum validation — 2026-10-27

Builder evidence for `plan-plan-open-decisions-addendum-perf-probe-`.
Task input: supervisor-supplied node specification/read-only design plan; issue
and node-specific `docs/tasks/` document: none. Not ASTRA program mode; audit
floor A2, no architecture gate. Supplied planner run `1793083431` was not run.

Observed cached `origin/main`, base and starting/current committed HEAD:
`8e4813e868961adbabb7d1ee450a346f8fb6add1` (#321).
Branch: `agent/kix-plan-plan-open-decisions-addendum-perf-probe-`.
No local base delta. `git fetch origin main`: NOT_RUN because the supervisor
explicitly prohibits all network actions; remote freshness remains unverified.
Implementation/final delivery head: unassigned, uncommitted worktree patch over
that SHA; the supervisor performs publication. KTX exact-head CI run ID/status/
conclusion: unavailable / NOT_RUN / not queried. KIX protocol exact-head CI:
unavailable / NOT_RUN / not queried. Merge SHA, final-merge blob checks and
post-merge main CI: not applicable. Local READY means builder handoff only.

## Changed paths and scope

- `docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md`
- `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md`
- `docs/README.md` (one index bullet linking both documents)

No pin, example, test, checker, map status, contract, CI, program or task input
was changed. No commit, push, reset, PR, issue, comment, GitHub/network action,
branch/tag change or background job was performed. Temporary scripts/logs were
kept under `/tmp`. No Cargo or release-example command was executed.
The external stop's command is quoted as historical input, not a command run here.

## Existing coverage mapped before edits

| Requirement | Existing coverage | Evidence / gap addressed |
|---|---|---|
| Stop owner, options and recommendation | Sufficiently covered | Original external DECISION_REQUIRED.md, numbered text/digest below; copied verbatim, not redefined. |
| Seven prior stops | Sufficiently covered at #313 | October 27 closure and holding records; this addendum checks forward through #321. |
| Dated perf stop, complete pin occurrence inventory and eight merge facts | Not covered | New addendum plus Git object/source/first-parent outputs below. |
| Source drift semantics | Partially covered | CONTRACT_INVARIANTS §2 and map S2-ANCHORS/F-B1 already preserve historical drift. The performance map characterizes four example pins; no current edge equality test is present. |
| Binding serialization | Sufficiently covered for synthetic fields | performance_harness.rs::evidence_binding_records_budgets_toolchain_and_non_claims; strings are fixture data, not current-file comparisons. Not rerun for this documentation change. |
| Index, register, roll-up, checker wiring and suite discovery | Sufficiently covered for structural assertions | Existing five checkers, plain/self-test, unchanged. Their semantics do not validate every claim or owner quotation. |
| Exact quotations, owners, pin occurrences, links/fragments and merge identities | Partially covered | Temporary consistency script below fills this document-specific gap; no permanent helper/test added. |
| Preservation / three-file boundary | Sufficiently covered by direct Git checks | Before/after object and working-file hashes; protected-path comparison; untracked-aware boundary and temporary-index diff. |

## Verification scope

The ten narrow requested runs passed first (five plain plus five self-test).
The full **Stdlib offline document checks** run block in protocol.yml is the
closest local equivalent for these documentation-only paths. Its 57 commands
are extracted unchanged and run in order, in the foreground; only --self-test
is run for the stage-5 host checker, as CI specifies. Final results are recorded
below. The KTX/protocol docs-only path classifiers were inspected: these three
paths qualify; Cargo/Clippy/formatting and heavy protocol jobs are skipped for
this change class. No full workflow or hosted CI execution is claimed.

Both AGENTS §4 locks match before and after, using `git rev-parse HEAD:<path>`
and working-file `git hash-object -- <path>`:

| Target | Required/observed Git blob | Result |
|---|---|---|
| runtime/crates/kix-kernel/src/lib.rs | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | MATCH |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | `b607996c83a119c349f1cc90469ac1ba82764e20` | MATCH |

The before manifest covers every tracked file under `reference/v0.3-rc1/` and
`.aiops/`; committed and working bytes agree. The after check compares those
same files and paths with that manifest and the base. In particular,
`.aiops/program.json` is unchanged. Protected-path diffs are empty.
`git diff --check` is clean, with new-file whitespace checked too.
The actual index is left untouched. Because normal `git diff` omits untracked
files, a temporary alternate index/object directory initialized from HEAD uses intent-to-add for
the two new files, then runs the exact `git diff --name-only origin/main` and
`git diff --check` commands. The output lists exactly the three deliverables;
normal status independently records the same set. No staging in the real index
or commit is performed.

## Findings, deviations and limitations

- Fetch omitted under the supervisor's no-network rule. Local HEAD equals the
  cached main ref; live-main freshness is unknown. No rebase/base change.
- The source stop's `7ba8003` and `41abd14` are implementation heads. First-parent
  merges are #317 `d016caee4ae40f28f531809359ee77ac22db0073` and #318
  `70b976c0b8db686b1d21ff0831c275abf77a3d0a`. Both identities are preserved;
  the addendum corrects the design's shorthand instead of calling heads merges.
- The stop attributes the pin to `9e8f489`; that commit introduces the edge source
  blob. `git log -S LOCKED_EDGE` identifies the example constant's introduction
  as `28c9c130e9ab9be017a8302dc1e4a4cbd3cbfffa`. Documentary correction only.
- Inventory expands the explicitly named constants to all executable Python
  locks and SDK SOURCE_BLOB, synthetic Rust bindings, normative Markdown locks,
  their repeated evidence copies and the required historical A/L/R anchors.
  Recorded current IDs are freshly computed, not copied from old reports.
- Initial temporary preservation collector exited 1 because `git ls-files`
  quoted a Korean filename. It stopped on a read-only rev-parse error (128),
  before edits; using NUL-delimited paths fixed the collector and the rerun
  passed. The failed command/output is preserved below. No protected-byte
  discrepancy occurred. The first temporary-index intent-to-add also failed
  read-only (128) when Git tried to create the empty blob in the real object
  store; a temporary object directory with a read-only alternate fixed that.
  The first transcript render retained trailing spaces/tabs from numbered
  blank source lines and diff context; acceptance exited 1 and the temporary
  index whitespace check exited 2. Rendering trailing line whitespace without
  those spaces fixed the documentation, without changing source bytes.
  A temporary renderer edit had a quoting SyntaxError (exit 1); it was corrected
  before writing its output. None of these were checker/test failures.
  An exploratory `cat` used the wrong prior-validation
  directory (exit 1); the existing `...closure-20261027/README.md` was then read.
  An exploratory `rg` used `reference/ai_delegation/mock.py` (exit 2); the actual
  `ai_delegation_mock.py` was then located and read. Neither changes evidence.
- Required checks demand no out-of-scope change. No new class C violation was
  found or reproduced. Existing A5/SD1 class C reports remain attributed to their
  holding records. The example refusal is an observed frozen-input mismatch;
  historical A/L/R differences are the existing class B F-B1 characterization.
- Every stop remains STILL OPEN. Recommendation A belongs to the source stop;
  it is not endorsed. Preserving NOT_RUN does not select D. The User owns the
  new decision. No policy value, option, node state, owner or grade is changed.
- Product TPS/p99/failure-rate targets stay UNDETERMINED (User); other existing
  uncertainties retain their recorded owners. No timing/performance value,
  host provisioning, listener, provider/bank/chain execution, real funds,
  storage/replication/consensus implementation, production runtime, durability,
  legal compliance, independent review, A2/Astra audit or merge readiness is
  established. Final-head CI and owner dispositions remain supervisor follow-up.

## Git candidate classification

The recorded basis scan has 2,105 matching lines and 434 unique exact-width
40-hex tokens: 294 local commit objects, 13 tree objects, 3 tag objects, 69 blob
objects and 55 unavailable objects. The regex excludes longer digests rather
than taking their first 40 characters. Selected raw scan output and complete batch type output
are below. Repeated tokens on one line are classified together; every matching
line was classified from the complete scan; its full text is reproducible from
the recorded HEAD. New documents are absent from the recorded HEAD
scan, preventing a self-reference inventory loop.

The eight inventoried values are P1–P5 and A/L/R. Remaining local blobs identify
historical source/output versions, imported text, validation snapshots or
reported current blobs, not required equality values in executable/normative
locks. They are excluded from the pin inventory for that reason, not silently
assumed to match today. External blob citations and unmerged submission blobs
without local objects are documentary provenance, not an executable local pin;
no network lookup is made and no MATCH/DIFFERS is invented for them. Missing
objects are not classified as local blobs solely from their length.

Each unique candidate below has its observed object type and disposition. The
selected raw scan supplies principal pin file:line/context; the addendum
appendix supplies all repeated pin-value occurrences. All Rust/Python candidates outside the eight values are verified
commit/tree IDs by the temporary acceptance script.

| Value | Observed type | Disposition |
|---|---|---|
| `0000000000000000000000000000000000000000` | unavailable | Synthetic zero sentinel, not an object pin |
| `01a86f66f1a2a0de98ae00f89e49d45ec07ec8da` | commit | commit identity; not a blob pin |
| `01f6c04c71dac27fab5d17017f4e837c076218c6` | commit | commit identity; not a blob pin |
| `0262dd972aa07ca36fb4394311d910b55f80738f` | commit | commit identity; not a blob pin |
| `02b1bf202b926c3b99cb39b360a50b2a75d3f744` | commit | commit identity; not a blob pin |
| `035d5705c93b318a49941ce5f7410f843360c427` | commit | commit identity; not a blob pin |
| `0394a36a655b86bacb568b055d377d4c4fd91185` | commit | commit identity; not a blob pin |
| `047d08e34659a5c392a0a0b08883846253c2aef8` | commit | commit identity; not a blob pin |
| `050a0e1e50f56622d8137e6516b01c6a0c8538cf` | commit | commit identity; not a blob pin |
| `054bc714b3c475fb8536df8d2d788b42e8c74b6c` | blob | Source/output snapshot or reported current value; no current equality gate |
| `059410cd85bf944142175fbd70364f7cc54ea196` | commit | commit identity; not a blob pin |
| `05d133c9dc4ef8e979391ced4099d2c9415e0124` | tag | tag identity; not a blob pin |
| `063e37c7d23bae6deeb51b3ff142fccfabf74d42` | blob | Source/output snapshot or reported current value; no current equality gate |
| `0672452e35a8582ee824dd29fd0dddd94320b453` | commit | commit identity; not a blob pin |
| `06b9ec68f9dc9dd4af4d70c236360be964a84ae1` | blob | Source/output snapshot or reported current value; no current equality gate |
| `07c36869e7b68fff10b02e6c59d7119df56d0785` | blob | Inventory A; all occurrences listed in addendum |
| `08119a41b7c8088a0e9d40bd35228af33d795643` | commit | commit identity; not a blob pin |
| `0846e4ddf1d55cc4ac619e2c350c4e3574547bda` | commit | commit identity; not a blob pin |
| `08b317e5096893432116e41c8312697793500cfe` | commit | commit identity; not a blob pin |
| `08ced25441171b2423e6399f04dae14ca0a0a3f8` | commit | commit identity; not a blob pin |
| `09470db220965390edeecdb75f56f8c827dd15b6` | commit | commit identity; not a blob pin |
| `09e161caa652d75e9617caf632b3b9899be35740` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `0b8b6b484c1b5d49b7cb285e780481061c2b16c7` | commit | commit identity; not a blob pin |
| `0bbc9b9cd421b386a542a8ed4351fb6aaeff907a` | commit | commit identity; not a blob pin |
| `0cb65749492bf78e6cea00d3c9c7eee4f891827d` | commit | commit identity; not a blob pin |
| `0db660a1085ca179c341c89129eeda763977b1fb` | commit | commit identity; not a blob pin |
| `0dee7319c2598083d9e6c02e917940f8648b1a40` | commit | commit identity; not a blob pin |
| `10e44d40abd878736b900d768f925725c95a8cd0` | commit | commit identity; not a blob pin |
| `118fc28862a6828b80166433bac6f5476037629d` | commit | commit identity; not a blob pin |
| `11d6bc63c732204b78531cc7959afefa69a77703` | blob | Source/output snapshot or reported current value; no current equality gate |
| `1311668253bbbbffdc90f1a9f446c42d43e5fa1f` | tag | tag identity; not a blob pin |
| `13134e49704815457fef444ce61d781b5a424713` | commit | commit identity; not a blob pin |
| `13c565560c758c2007c482376e68ada45b922c2e` | commit | commit identity; not a blob pin |
| `154e9aae3da1bf0044dad606fcfd7e2fb6b3f8df` | commit | commit identity; not a blob pin |
| `1578bc39bd256d4e894ce341a108be1647b9e14d` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `15f7fe67726c04efd5a6d289ef985041f40c511a` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `16a6aa05d7d9f693bd4dbbad85008243fa8fd95d` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `16aa6d528c2b2a519d99e724b986717fc090b1e3` | commit | commit identity; not a blob pin |
| `17c8a7dc66e49b090067b94ff7bc68cb6d79c5ee` | commit | commit identity; not a blob pin |
| `18aefc8f7c0dd13b7249e0d80304f3b97459fa3a` | commit | commit identity; not a blob pin |
| `18b80a79614b3a5866f61728b0935294360cfa85` | commit | commit identity; not a blob pin |
| `19a58ab1e232c54eb39b717a94c637322c493a4d` | blob | Source/output snapshot or reported current value; no current equality gate |
| `1a529d036d2d7f33eb17f4c143b16a3213f26973` | blob | Source/output snapshot or reported current value; no current equality gate |
| `1a69364eca0e2a219854c443f8183a9b0e733a2d` | commit | commit identity; not a blob pin |
| `1bb000bd125a1e8ecdd033cea01733d58588199e` | commit | commit identity; not a blob pin |
| `1c129f1a5fd73636c30c90a33ecfb9e4adf21217` | commit | commit identity; not a blob pin |
| `1c9488499bbd954f1c14e5f571f24f3f1d976338` | commit | commit identity; not a blob pin |
| `1cb2d26c4b6d8cc7aa2d362bf017e4d30f5a2080` | commit | commit identity; not a blob pin |
| `1d8d228e6fa5cabacf341dd6add0890e8fe95421` | commit | commit identity; not a blob pin |
| `1eb7d7d2978950073973a43e495ec5e31c5f543e` | commit | commit identity; not a blob pin |
| `1f01a9321c641c7a7fafa2a33e4350a2fa711730` | commit | commit identity; not a blob pin |
| `1f9cceb99404cd673205d5fa1f46db8900e74da4` | blob | Source/output snapshot or reported current value; no current equality gate |
| `1fa6676860710e6bad6d882a57a91972407e2e41` | blob | Source/output snapshot or reported current value; no current equality gate |
| `1fb0c8b50ac4de5693996412337d36cd6683bdf2` | commit | commit identity; not a blob pin |
| `1fc02920d93fe0fb1f272fa917f6e20ba26cc987` | commit | commit identity; not a blob pin |
| `20b692b0e7de91f70693d15b14ff5c5c52fc21cb` | commit | commit identity; not a blob pin |
| `20b9538f9d48ad513c2f2ea28c478d01c758b01d` | tree | tree identity; not a blob pin |
| `22d05a0c82693ad4575a72c2d342b4e47114447f` | commit | commit identity; not a blob pin |
| `22df2e96d1a7de4d0de371a1f64776e80af9d999` | commit | commit identity; not a blob pin |
| `22f9fc9781732d651e18384c9a8eb1dabddf73a6` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `23391ab50e0467bc7b234c55e98614713d531f58` | commit | commit identity; not a blob pin |
| `2393988eeca984f12f0819ac56b6870be1a5832f` | commit | commit identity; not a blob pin |
| `244595db1524cbb1a01148baa07d6d28cd1b8dc6` | commit | commit identity; not a blob pin |
| `2497471dfab21ffd68d600e6ce508e5d6d65bae5` | commit | commit identity; not a blob pin |
| `24b925955ae17942ab25b68b1e5a9111d6983501` | tree | tree identity; not a blob pin |
| `2554173ebdda0922aaf7a0bc7ea773075187a3d9` | commit | commit identity; not a blob pin |
| `2658a43aefa792ff783457188814f8598a62f5b0` | commit | commit identity; not a blob pin |
| `2676b5bff0f8d696f18139aebb7e862a965139e3` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `26be51051939cfe88f7ff542f355f10ff7a3fcd7` | blob | Source/output snapshot or reported current value; no current equality gate |
| `26f1b9535db24a6b2e9c28753f561d4d6a271815` | commit | commit identity; not a blob pin |
| `2798352822e7ee657ae789ec370d0390a31febdc` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `28539987d1e676f0724081c41b22db51e731a967` | commit | commit identity; not a blob pin |
| `2862f34b588e70841a57762d8ce756fd240f5e95` | commit | commit identity; not a blob pin |
| `28f263b5839921b729c2729c8ff5041f57d306ec` | commit | commit identity; not a blob pin |
| `293cc81198d45faf8111637af6fe4d28fa3470cb` | commit | commit identity; not a blob pin |
| `2ae8f1d0774befb0d71eb07f2e3d7454d3fcdc64` | commit | commit identity; not a blob pin |
| `2b358c225256e8c13c517167c8b1c30156a4383d` | blob | Source/output snapshot or reported current value; no current equality gate |
| `2b91c41288b048a233f95b2d4e285b9c262d2333` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `2c7bc7dd7d4831b0ab3c0ce5e394999a7f72de12` | commit | commit identity; not a blob pin |
| `2d2e93eb14fe41bafaf2dbaa91f02d861c8be8b5` | commit | commit identity; not a blob pin |
| `2d86e35be414181184c16a6de1649aaff95bad64` | commit | commit identity; not a blob pin |
| `2e43b285e2a07b4af6377ae7f776a550dd884e95` | commit | commit identity; not a blob pin |
| `2ead88aec7f5fc36ed802c32c98f3053367c7ede` | commit | commit identity; not a blob pin |
| `2f527f4fa6d0a1c6185deca7dc29eef49de01005` | blob | Source/output snapshot or reported current value; no current equality gate |
| `301de8c7da8859164ee708b2560bfc30d13531a4` | blob | Source/output snapshot or reported current value; no current equality gate |
| `306dfa1261eb02881d1914b34d6510fc698a9979` | commit | commit identity; not a blob pin |
| `3181adca80c2979145ccf54e0abe8330c162f738` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `31e60b2269e90cba6da9a1a41dacf039f5662c30` | commit | commit identity; not a blob pin |
| `31eac0637a324244aeca00e849fdb0f7c685232e` | commit | commit identity; not a blob pin |
| `34584c427260826cde67d726e18c92e01839817f` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `34a722d26fa894366c26bac9de4187c598fbf3eb` | commit | commit identity; not a blob pin |
| `34e114876b0b11c390a56381ad16ebd13914f8d5` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `37504dd43411d331d6e0d9351c86ae0e10ae33f0` | commit | commit identity; not a blob pin |
| `3771a8739b906a478b54c597df37e27d1afc5f21` | blob | Source/output snapshot or reported current value; no current equality gate |
| `378f1e817f22401c65007e7de3313901ca0ea724` | commit | commit identity; not a blob pin |
| `38096dc849dc338f12aa69bce2200cda971a6d3c` | tree | tree identity; not a blob pin |
| `384c935010a33c160ccdb26b568ebc7454777f09` | blob | Source/output snapshot or reported current value; no current equality gate |
| `38901ede6a20dc67025014116ea92c0ea35f8bf5` | tree | tree identity; not a blob pin |
| `39146a44187af4b43ac57148661bc3af2fb3104f` | commit | commit identity; not a blob pin |
| `394084b15e01bbe4a5612aeb3431f3278c43dd85` | tree | tree identity; not a blob pin |
| `3995d878823727669023fa395819c79a8c227850` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af` | commit | commit identity; not a blob pin |
| `3b6bdd26f61bb828af3781946b63a3a3fa03187b` | commit | commit identity; not a blob pin |
| `3b8067d48cbda967cbf531258215c5243b96fbcd` | commit | commit identity; not a blob pin |
| `3cbb8df3a466fe171d7261f9090c324a458af3f6` | commit | commit identity; not a blob pin |
| `3ce6e4975b7f439d67482451bb47a22c940add26` | commit | commit identity; not a blob pin |
| `3e7c64a515e908b312604e82405b963d100caa07` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `3ea44ce1d9003ad095e408039e1f755c319c4dfb` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `3f1e78d94bb06488a9375a718fae22d6d76375be` | blob | Source/output snapshot or reported current value; no current equality gate |
| `403d3e29413b1e78c5da945cd33389b50d4514a4` | commit | commit identity; not a blob pin |
| `4052dccfcbeaa95c1f21c2973ef530e5d5905759` | commit | commit identity; not a blob pin |
| `40d904318b58d1ccfd2e86e77e6b290856ec95a7` | blob | Source/output snapshot or reported current value; no current equality gate |
| `411e7a592fa4219ed606ec770ab903c6a6fd36c7` | blob | Source/output snapshot or reported current value; no current equality gate |
| `412e1ed7bc740599227567f60bf315bb7ecab818` | commit | commit identity; not a blob pin |
| `41a799987fe3a6a207abcce75045265c5796e1e4` | commit | commit identity; not a blob pin |
| `4338fc72698f2f15c3723f3d13e677d3e1aff29d` | blob | Source/output snapshot or reported current value; no current equality gate |
| `4428d2bbd00a1e43bf0b61dd402c6ad0fc67bb39` | blob | Source/output snapshot or reported current value; no current equality gate |
| `44659fa4d3553dec46d709450249d2764fba8d8d` | commit | commit identity; not a blob pin |
| `4480c9db7be539abd5a99e640b5a25c7eef8cafe` | commit | commit identity; not a blob pin |
| `4584c9ad2a8c886acc3cd0b1e021a5802e6424f3` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `45c08d519daa70adaf89ba5e8d2e89175422dc17` | commit | commit identity; not a blob pin |
| `45ec626e2ffcd1cd47aa982622877873b5297139` | commit | commit identity; not a blob pin |
| `46d01d149d96c7776283ccdface2e0c6244caae2` | blob | Source/output snapshot or reported current value; no current equality gate |
| `46e3b38a8dbde60f5a1cd197577a2dc73214ff2e` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `471728e6488719be471eebb3ca8c30ab2948c444` | commit | commit identity; not a blob pin |
| `47eed4b01b93dc4b00e102729bad1c74abdbae95` | commit | commit identity; not a blob pin |
| `4813388b5bcde72c298c7392ff5230316da44470` | commit | commit identity; not a blob pin |
| `492a85d36fc79aa31d3938bd44024b73dd70dfad` | commit | commit identity; not a blob pin |
| `492ae8c9d7a3171890cbea2ecdb913519b83c158` | blob | Source/output snapshot or reported current value; no current equality gate |
| `492e3aacf4fc5260240df10c3c55a39a54fcb466` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `49933ea5288caeca8642d1e84afbd3f7d6820020` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `4a73103904a8b8428cc1424a6e9f52b13ef3ed09` | blob | Source/output snapshot or reported current value; no current equality gate |
| `4da9f7762beddf1a93d95cf26e55d7bf64316711` | commit | commit identity; not a blob pin |
| `4e2122a3f61a0feea2c43035c1ae834e7097e429` | commit | commit identity; not a blob pin |
| `4e3ce63eaca8ab766c9c88adc712554fb0027d36` | commit | commit identity; not a blob pin |
| `4e5c30cc6779ea8b7d26fa40fdde6c84adfd44b7` | commit | commit identity; not a blob pin |
| `4ec0f93255b9be1715784f1d2a5edde411cc96c6` | commit | commit identity; not a blob pin |
| `50af6096a84f72c8c1249f23279dab0b279e4c82` | commit | commit identity; not a blob pin |
| `5155ed307c71917ba3442fc5e1fc4cb950efefdc` | commit | commit identity; not a blob pin |
| `51d83808478e56c81c6f43e2a13450d435e922e6` | commit | commit identity; not a blob pin |
| `521f06f7d9194ffc4eae21bfb13f7e82b6ef9241` | commit | commit identity; not a blob pin |
| `52bd45eff0d77280406a819e62e33212ca50370f` | commit | commit identity; not a blob pin |
| `53c16b226346f2df824f93a5756a080acd489ec1` | commit | commit identity; not a blob pin |
| `543c1438ce044479fd9646bc5e1cde933a153a4c` | commit | commit identity; not a blob pin |
| `5440de0cf721932398af87344fe59d48b9858ad3` | blob | Source/output snapshot or reported current value; no current equality gate |
| `547d9fd5cd0e2d54e4fd61050d6f4fff530f3750` | commit | commit identity; not a blob pin |
| `54a785b864d629d623afc36ed807d9daebaf9285` | commit | commit identity; not a blob pin |
| `554b78e80f505a008dcbfb4e1c9f271d902a4039` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `5561fc965803935be1894457ebc762a3d36489f5` | commit | commit identity; not a blob pin |
| `5587afb34cdf9df51b981bcea4a9507250e70528` | commit | commit identity; not a blob pin |
| `55a3df4968f5684bb4cb9e3c9781ab5f00165235` | commit | commit identity; not a blob pin |
| `55b018503df24cfbe36cbf17bbf48a8c0778757f` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `55e253944f1cf66faa27652680ca7b2a3783b1c3` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `56b17aea66a4c006a1c6b2d0de77d76b10feb062` | blob | Source/output snapshot or reported current value; no current equality gate |
| `56d4a3d193cfe5575285f4b59a8e1faa7ce9a079` | blob | Source/output snapshot or reported current value; no current equality gate |
| `56d5f59468969825e0e2cd22f6803ebb5e6fb662` | commit | commit identity; not a blob pin |
| `5714603158ddac1a5dcbe2e645c902e26f2b20a9` | commit | commit identity; not a blob pin |
| `57a3e3049c84a2ac0112371594e9bb4b85a8296f` | commit | commit identity; not a blob pin |
| `57adb8d579986a945b716f0f181c0be938ceb389` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `58386edc269ef88ff0f40ab0a9d50e87cba80ca8` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `58dd527ff53097f5231e89f25ebdf3e94586ee65` | commit | commit identity; not a blob pin |
| `590e544b3d097ba3de2fc573deae43b15bc39773` | commit | commit identity; not a blob pin |
| `59746105a8e1b82b0109bb958e6f9104abb70f39` | tree | tree identity; not a blob pin |
| `5a09a325e2f6415b7fe638d0dbcd826b4d45fb86` | commit | commit identity; not a blob pin |
| `5c11893edb186c739140330626d5caf74fa668b6` | commit | commit identity; not a blob pin |
| `5c59d95ec52379e010f8e9c660da11cfa6498def` | commit | commit identity; not a blob pin |
| `5e20a467160148ad5c2debfe357dfb8da084a30a` | commit | commit identity; not a blob pin |
| `5e43f6f21b9f3c8be3af1d371b9c5d955de34cb8` | blob | Source/output snapshot or reported current value; no current equality gate |
| `5e8ee3f1882d97f1c442fe485407e51822ec22ce` | commit | commit identity; not a blob pin |
| `5eb95eabcac8b71e0c6c92b4fb322a0e4fe5bb45` | commit | commit identity; not a blob pin |
| `5f55793de15792686bfa7a5be0da24fa4acb41fa` | blob | Source/output snapshot or reported current value; no current equality gate |
| `5fffc196be37425366b2a6ec7faeec1db9bbca46` | commit | commit identity; not a blob pin |
| `60e7683ad28d5264f398d7965c06bfd840aa7338` | commit | commit identity; not a blob pin |
| `619ae21c82ca3df5661bd3831613f15fa65225ff` | blob | Inventory P5; all occurrences listed in addendum |
| `624b28d024279bd077e1247f37566333457750bd` | commit | commit identity; not a blob pin |
| `62bb47f63408264b2d4dda50da94bb4d77c015c9` | commit | commit identity; not a blob pin |
| `62fd4302af952a66c1a6e3fb3b3ea5a1eeebee64` | blob | Source/output snapshot or reported current value; no current equality gate |
| `6332bca0f54cc2114d986b24ab218ace33a5df12` | commit | commit identity; not a blob pin |
| `64916cdf387d43c3db4ec9d487a246d3347b8d62` | blob | Source/output snapshot or reported current value; no current equality gate |
| `67088f944155224b2b16fdb8b51ac781d930382c` | blob | Source/output snapshot or reported current value; no current equality gate |
| `68a65db0208cf57e35750b226dfac49f555ae850` | commit | commit identity; not a blob pin |
| `69564b166f0c27f9af5d8422f0a466b18d74c20f` | blob | Inventory P1; all occurrences listed in addendum |
| `696420af819ebc004067fd52971d016e51e6cdcb` | blob | Source/output snapshot or reported current value; no current equality gate |
| `6b6d7675eecba9f599a8760698fd2c469359aef9` | commit | commit identity; not a blob pin |
| `6bdd571fcb88496c98e25b32213c60017e209198` | commit | commit identity; not a blob pin |
| `6cdff624203a9610ed9b84fafec8dad07995c414` | commit | commit identity; not a blob pin |
| `6dbf8dfed6ee790e2ee56b49a75b727edd9db977` | commit | commit identity; not a blob pin |
| `6e54e723d582e88ae89df309eb144d4664c7e1f5` | commit | commit identity; not a blob pin |
| `6edba1a60c14d5b43bf05336294e678b46794fee` | tree | tree identity; not a blob pin |
| `6ee81c86a6f587b6b1bf549ce0043a5e43555d43` | blob | Source/output snapshot or reported current value; no current equality gate |
| `6efea0adcc2b1c7f4bd62c43673cc54830a8fc37` | blob | Source/output snapshot or reported current value; no current equality gate |
| `6f7559470bf2d555bbd80d0ae5d5f8a008e798f7` | commit | commit identity; not a blob pin |
| `70000ed8a189b8b3b92a4a858d7cce1ed43e5d7b` | commit | commit identity; not a blob pin |
| `70b976c0b8db686b1d21ff0831c275abf77a3d0a` | commit | commit identity; not a blob pin |
| `729a106add049ad1a75b90f99c00b6e0ccb8a67d` | commit | commit identity; not a blob pin |
| `7327a00a68ef6efa81a795173af5e4572ccd90ef` | commit | commit identity; not a blob pin |
| `73f324a00f345e120014718b67a7c03ecbf1198a` | commit | commit identity; not a blob pin |
| `7481b0e16ce9b903abbffa62249bb91cd9e63cfe` | commit | commit identity; not a blob pin |
| `751c51bdff661673eb2edb9de0dea8f6cbdac2e0` | commit | commit identity; not a blob pin |
| `756c2f78c9b6058b6acf1573aba052118669a2f5` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `757131963bf63296cee3395158864d43d6ede2f3` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `75e3b9965ec4441b242907269a2f5e397f8c8914` | blob | Source/output snapshot or reported current value; no current equality gate |
| `76b5e342c298ebaac42d6ebc7d5ecd6bd27811e6` | commit | commit identity; not a blob pin |
| `771545ae4b64f069396667f399b5200c44fd9af0` | commit | commit identity; not a blob pin |
| `77517f0c74cd892ca299cacf987cbab64a03337d` | commit | commit identity; not a blob pin |
| `77da4bcc37e227c549929740a30e4ac544efe4db` | commit | commit identity; not a blob pin |
| `788896ed3e00bae3d06d26b7e2ce999a00ff1029` | blob | Source/output snapshot or reported current value; no current equality gate |
| `78b78b1b4a4ffe92de461edd351235ce858b335a` | commit | commit identity; not a blob pin |
| `78ed34d37568d9084f75a546bbb6377d16397521` | blob | Source/output snapshot or reported current value; no current equality gate |
| `78f7f80e22f35b8a8cfae56cbded38f3caf22331` | commit | commit identity; not a blob pin |
| `7949fe3e7ac4a370c0b4cbb05ac39a3779e8c466` | commit | commit identity; not a blob pin |
| `7ae4535c472cbe5416cf68a298fd4cd1dcf2a38a` | blob | Source/output snapshot or reported current value; no current equality gate |
| `7b6a293e903845ff9c06a19f9a02c075d1790089` | commit | commit identity; not a blob pin |
| `7bdc99933c804b417b94d9dba40f13d370861cab` | commit | commit identity; not a blob pin |
| `7be6b7507201674599f5d35aaa329cdbeb75ab38` | commit | commit identity; not a blob pin |
| `7e580b26c04edb226a729c79a2ec6731c1f858b2` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `7e6d215031d7ff454b132b8c1ca657455cbc2734` | tag | tag identity; not a blob pin |
| `7f480fa4e3f18db83605a59cab4ae9b2e405478f` | commit | commit identity; not a blob pin |
| `7f59ed18129960724696400f7f4c9fca3d465fd9` | commit | commit identity; not a blob pin |
| `7f99812f4558e4802a51d5468da35754db693c43` | commit | commit identity; not a blob pin |
| `808640d9b49aecf29d8e6f46033c15eca236efa7` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `82f0a5d2ecb6797a15087d13a1b7d67482de3b09` | commit | commit identity; not a blob pin |
| `8340a418523e92fb938d9a82b23f81c1ce0e6156` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `83f1f17bbfea81a8371e4c598d41f2915102a6e8` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `841408e77065c841ea73e2cf04fe8c03fbd35f5d` | commit | commit identity; not a blob pin |
| `8495c7651e456cead3a8812b9e6fb183f818acd2` | tree | tree identity; not a blob pin |
| `84cc3ea7763ed6d5e08021e1a9930edd7ff5721d` | commit | commit identity; not a blob pin |
| `85145eb33799a7c712890ff81708def8a7d61ee5` | commit | commit identity; not a blob pin |
| `85acc3399a23e87ee4092693840c4e0a620867a0` | commit | commit identity; not a blob pin |
| `8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d` | blob | Source/output snapshot or reported current value; no current equality gate |
| `876f41067bc7eb70bcd6ebd9c744c11b46f046b6` | commit | commit identity; not a blob pin |
| `8785416213151b7cdfefae2bccbac00ef168e3da` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `87bcdfaa528eb4f99f0ac6ed643f840d738994b7` | blob | Source/output snapshot or reported current value; no current equality gate |
| `8931820e77860f575faee636cacca2c45e4f2c98` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `8b88ba7176a98faf64565434d05e44d97dc3cf8f` | blob | Source/output snapshot or reported current value; no current equality gate |
| `8b92eb42353d5ca1058227671b3abda3142643c3` | commit | commit identity; not a blob pin |
| `8d310e76e6a0e8999be427e95599b62f1f8b13a5` | commit | commit identity; not a blob pin |
| `8e69bd7f64e019dc3e1256a94ccf283d13dffc73` | commit | commit identity; not a blob pin |
| `8e85ef4e14c2615a94b8efca6acd60ea4fe52fb0` | commit | commit identity; not a blob pin |
| `8fff6c191c690e803a1bb901a0cf7b5765167985` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `900866ee99a71254fb7da1ad2aa4640477ac550c` | blob | Inventory R; all occurrences listed in addendum |
| `90c6e7a6bfa305764a9b66df3cafdae038b5139f` | commit | commit identity; not a blob pin |
| `90d320325a601e1f604cd901703fd2a5094ca527` | commit | commit identity; not a blob pin |
| `91d2e507362a79834c09790d9f379ee15f2a1453` | commit | commit identity; not a blob pin |
| `92d08e755dfe362ed224112c8dada6c5fcea17d4` | commit | commit identity; not a blob pin |
| `93cec6aaf12f22bf8aefc0453fe545b6bd38b819` | commit | commit identity; not a blob pin |
| `9411d3c008d58d50e6a26bc07f1e46a8e8e4fa84` | blob | Source/output snapshot or reported current value; no current equality gate |
| `94376835ea4fc818619fc79e2be4df7d4947496a` | commit | commit identity; not a blob pin |
| `944cb16f3ade5a395c0febe84fd47d5c16dc0fa3` | commit | commit identity; not a blob pin |
| `94a768e19df12703ea0b9a49e49972feb2f6ef4f` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `954e6e3a2b6abbe40af3a13d04e4263fa7fbe547` | commit | commit identity; not a blob pin |
| `957f75d75ea4854eba117d66d07663133f0b7b2c` | commit | commit identity; not a blob pin |
| `96d0daad5b96af501c19284f149cb288b17e5d05` | commit | commit identity; not a blob pin |
| `974d8e4875c5128266aaefa830bdfcd33cf89534` | commit | commit identity; not a blob pin |
| `9805d74a1ef794f14a6eca9894cfe1a2034e2e91` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `98d5f6372b68f875bcb2b670c5998697ecfb76c1` | commit | commit identity; not a blob pin |
| `99c2655d38c283497b92dc24ba84a2ae6a5461fb` | commit | commit identity; not a blob pin |
| `99f30c2d641646d653b62383b213452fd0a0498b` | commit | commit identity; not a blob pin |
| `9a8da873074aa96ceda07a772629098762238773` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `9aa464b6b9d89cdf1da65f828b55e6e97bf7bef0` | commit | commit identity; not a blob pin |
| `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1` | commit | commit identity; not a blob pin |
| `9b462fd2cd6890cd0d8fbc2930f2cc54255e2915` | commit | commit identity; not a blob pin |
| `9c4da8d53947a8ca049b6284fa5ca915fb5947ec` | commit | commit identity; not a blob pin |
| `9c59e0a81f1675fa919ba9327642269bef9e70af` | blob | Source/output snapshot or reported current value; no current equality gate |
| `9d0860c870e4a06f6b8e876cbee6446f50b22b15` | commit | commit identity; not a blob pin |
| `9d1ff76377fd7c65911c1fb7cb7b515a55489e2d` | commit | commit identity; not a blob pin |
| `9d50fb660248b66a5959f48f7dc96e68c9d5530b` | commit | commit identity; not a blob pin |
| `9d5ce5228045673eb362c5f20cc019a6cd8a5ad1` | blob | Source/output snapshot or reported current value; no current equality gate |
| `9dd1413f060a420b3a97896b9451c82574f56d08` | blob | Source/output snapshot or reported current value; no current equality gate |
| `9e2dad654d7c6e46efade803018ef3e2cfea5e0a` | commit | commit identity; not a blob pin |
| `9e5d96e995fe2cff29b2b52863f6d6dc5c4d9289` | blob | Source/output snapshot or reported current value; no current equality gate |
| `9e8f4898cb429e1146ea924d6c254b7fd490a3b2` | commit | commit identity; not a blob pin |
| `9eb6b5f932cae5f4f1b431ef79c9f15874db1c36` | commit | commit identity; not a blob pin |
| `9eb6b9ff24c6ca5825a3d999c81932a38ae79f02` | commit | commit identity; not a blob pin |
| `9ed15a7adc93359e99bb5c3512a3ca20c77cb264` | commit | commit identity; not a blob pin |
| `9f0177ab45cf3ca704ecf5a152b3c1785c8f22a7` | commit | commit identity; not a blob pin |
| `9fd4d4836ab4d7eb666ebd4ff2ac0708870d7a58` | commit | commit identity; not a blob pin |
| `a013cb0c471be0422a4a70d6b98e86c03f7131fa` | commit | commit identity; not a blob pin |
| `a059bd69eae321ccfeb5940f3d675b962103d361` | commit | commit identity; not a blob pin |
| `a0db1e226e27b1c5f60ee938fb528ff795907056` | commit | commit identity; not a blob pin |
| `a0e16328c1b4939458b2abe5b4b5167b79a15c26` | commit | commit identity; not a blob pin |
| `a114b5bd67164dd1264bc4ad838566809b5bc0b4` | commit | commit identity; not a blob pin |
| `a13244fe6dc07d72b314752f056612899dc544cb` | commit | commit identity; not a blob pin |
| `a176c1f22c0af21500cb52a777bc889b808e561c` | commit | commit identity; not a blob pin |
| `a1a8af283a7a22036485c3b7cb097db9855ad91f` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `a26af69be951a213d495a4c3e4e4022e16d87065` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `a2814923bc671889da49984a2c95964340a1506d` | commit | commit identity; not a blob pin |
| `a2a2e29ceefd50952454c6b378363b31be84c3b4` | commit | commit identity; not a blob pin |
| `a329ec07ac52ec15bff6c48079115d81ace5ab67` | commit | commit identity; not a blob pin |
| `a34a38b73f096c9f6597b38a111d95ca12ecd159` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `a38e1679449e74186c5a4e3d19b6cb79f6b791d5` | commit | commit identity; not a blob pin |
| `a3f0fea3160fdea2f59fa8658573be173e242074` | commit | commit identity; not a blob pin |
| `a4158b3fb495aa12507ceb44bf128bfbe7dba2ac` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `a45b246082453cb739e51bb0577bed646e4d1935` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `a47828dd4517c5a7397e09eb6b563a64e4265c82` | commit | commit identity; not a blob pin |
| `a483ab1777ad0c3e15ff71798822cbf6b3666f83` | commit | commit identity; not a blob pin |
| `a4ab8d0119daba974dd59a20d3da05d82bd61118` | commit | commit identity; not a blob pin |
| `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` | tree | tree identity; not a blob pin |
| `a744b0a036d7e1edb48416871af20cd182f23df4` | commit | commit identity; not a blob pin |
| `a74e7c459d3be6754ac3cf24503e43c7bc312358` | commit | commit identity; not a blob pin |
| `a7c9d4467a9170ba4a062554562a4610c0b27573` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `a7e6febded343fe0fd43df2059874525194efecf` | commit | commit identity; not a blob pin |
| `a83d09cd99017875f583383e6ebbabc46a6a63eb` | commit | commit identity; not a blob pin |
| `a8b7355712c58de8d27c85a535fb241a09a4037c` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `a8bc9e853f3b0d82c5c4ee2d0bb4620ac36662e4` | commit | commit identity; not a blob pin |
| `a9be88d3da4d735aabc5168c68007c062956b412` | commit | commit identity; not a blob pin |
| `aaa7ebee8c436f1a01cf813d497b018185eecec8` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `aac2e72d8d5df86032ec2154172f724d07ebbcf1` | commit | commit identity; not a blob pin |
| `ab3902f66c9abd3875f36126a021710c887d015f` | blob | Source/output snapshot or reported current value; no current equality gate |
| `ab42cfef43a40c6b86fd3f22b69f00e134cc472e` | commit | commit identity; not a blob pin |
| `ab611650286f9b5db82b491d398dc47e27a93864` | commit | commit identity; not a blob pin |
| `aba875635f682bb9914e0dee016ced58e130cc04` | commit | commit identity; not a blob pin |
| `aca49f6e5498291c1f221185df1ee5cdbf333342` | commit | commit identity; not a blob pin |
| `ad3cee9e6aa68aa14c3b35901f66b6cab40cf75a` | commit | commit identity; not a blob pin |
| `adcddc510a66ff70725084c0846830c29ef9ebbe` | commit | commit identity; not a blob pin |
| `ae5fd6aee210007b2f1ca7f96809c76348aadae4` | blob | Source/output snapshot or reported current value; no current equality gate |
| `ae6b905104d0cb2022001fb32ad98b1a6b3046ec` | commit | commit identity; not a blob pin |
| `ae869f38438d8174103171ec741a41376aee60df` | commit | commit identity; not a blob pin |
| `afe7ded7abc1b6e6cc65c8b179c2d6dac009c891` | commit | commit identity; not a blob pin |
| `b1fe707bfcc99ac43edcbd2622caad1a25e1ce22` | commit | commit identity; not a blob pin |
| `b3f1c6c1f943dc5faccaa9451aee55fa7305dc4c` | commit | commit identity; not a blob pin |
| `b57d49d068c14d1a012e73cbc8c10c8f6ee5d631` | commit | commit identity; not a blob pin |
| `b607996c83a119c349f1cc90469ac1ba82764e20` | blob | Inventory P2; all occurrences listed in addendum |
| `b61e48d965e7ed3f1c5f4fcd5ad863b961ce4e28` | commit | commit identity; not a blob pin |
| `b6373c2448ac947d245851abf7c4d9a00e70f5c9` | commit | commit identity; not a blob pin |
| `b665f9a0ad41a46e2169cb142b91d598665aa7ab` | commit | commit identity; not a blob pin |
| `b6cc9978c64b1ff54f822ea930424b5d78dfca2a` | commit | commit identity; not a blob pin |
| `b761bd60f45f224b4c5db5e3af6963eb6e7dc4d5` | commit | commit identity; not a blob pin |
| `b8b7455cf346d98689238d3eeaf07fc139fa6a7d` | commit | commit identity; not a blob pin |
| `b8c8d1057e8124fef09dc2301fdc841015f22b4a` | commit | commit identity; not a blob pin |
| `b9184e48f0df3f26a5214ec00eea20b0629b447f` | commit | commit identity; not a blob pin |
| `ba352dfe9789af89983e9c1b1a303461ea240016` | commit | commit identity; not a blob pin |
| `ba5bd063daf87a365d4bf6f795c8940ee7fcfb17` | commit | commit identity; not a blob pin |
| `bad6927e6bdfbb1681c1e51b40b73089ea557e1d` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `bb193efb5d238581096372c8a20bee1271dfe4df` | commit | commit identity; not a blob pin |
| `bb24207cb648acfe3083c4a2e7720251b06ad639` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `bd367efcc9127663b902b973850ffafc179469df` | commit | commit identity; not a blob pin |
| `bdc663b47663b885dce36e7138a407b7b0658089` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `bf460b1f7724c5ad7d561b19a64959383fcec6a8` | commit | commit identity; not a blob pin |
| `bf6c2be37e8c55778f4fe378634f7895fd69a327` | commit | commit identity; not a blob pin |
| `c0fc5b4aed4da32284d9879ad21ef6b584db01d2` | commit | commit identity; not a blob pin |
| `c2cde86e21a6e5ba6f24a56548636db6d0a34c6f` | commit | commit identity; not a blob pin |
| `c3a2b304641dcd2373e0267030dc69ea48d55f5e` | commit | commit identity; not a blob pin |
| `c3b02085650ad394283f3325cf5dd87664c66ddb` | tree | tree identity; not a blob pin |
| `c4287ed94a0bd0295f0452fc4374a45dd661159d` | commit | commit identity; not a blob pin |
| `c4cfe54d4ef18ae8e99599ad4e9038ccf5d18a4c` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `c51142ae5090fb00d68fa4f2d8722c6a1d526345` | commit | commit identity; not a blob pin |
| `c5121714b58c3e5250740c924733e1964445d102` | commit | commit identity; not a blob pin |
| `c5d2792170e8e476370a064b8a7de626a5213412` | commit | commit identity; not a blob pin |
| `c690c9fa6e1b3bc058fd35be507c1c1d94e2419c` | commit | commit identity; not a blob pin |
| `c7762c2724d5d28fd2e5e4f00cc5aae4f1f7908f` | commit | commit identity; not a blob pin |
| `c7b470fc39ad6f6aa6ad59c18b5595cde41a7200` | commit | commit identity; not a blob pin |
| `c8267d1c2bdbcd732aa46401fe059b92d8ae72a6` | commit | commit identity; not a blob pin |
| `c8b806ebd0f959814acfd184edadf244bf18d1b4` | commit | commit identity; not a blob pin |
| `caec5434c12f1238d7b3c014b404f4f8bddadd78` | commit | commit identity; not a blob pin |
| `cb59612b847fc2e6ef71810202be5e2ca5f76724` | commit | commit identity; not a blob pin |
| `ced0e2f42c0491753db91acf87bd61574eb37ce4` | commit | commit identity; not a blob pin |
| `cfeb0d69561103302b6fdc3d10842768c3420151` | commit | commit identity; not a blob pin |
| `d016caee4ae40f28f531809359ee77ac22db0073` | commit | commit identity; not a blob pin |
| `d1cc57a7d6c640b5df3eacd65a1d8593f0beb346` | commit | commit identity; not a blob pin |
| `d236cfc69e21b88a74caef8879e7ea08008628aa` | commit | commit identity; not a blob pin |
| `d2b748aef0c7b4af5bef23c771c6bce22b52905f` | commit | commit identity; not a blob pin |
| `d37ea7df55423c83bedee16bf12bdc8dd61f7cae` | blob | Inventory P3; all occurrences listed in addendum |
| `d554ffc40d93b85fdd01057f48fdccfa0d991d94` | commit | commit identity; not a blob pin |
| `d5b9f2d67b5532fa35464c8557e88f70be300888` | commit | commit identity; not a blob pin |
| `d63768ddf276c60173aa2c933f4feef3449a9452` | commit | commit identity; not a blob pin |
| `d6a6a10f3f5fbaf31f54ad676a9b5e36c0e3d313` | commit | commit identity; not a blob pin |
| `d71b4117741f596e2b618ed1c32a42597bc0980b` | commit | commit identity; not a blob pin |
| `d7549d1473258dda617e241fff22bcbd697fbb17` | commit | commit identity; not a blob pin |
| `d82c37964d8f87c43d110b19899ee4d6622e87b4` | blob | Source/output snapshot or reported current value; no current equality gate |
| `d84cc50f78a37420ca9d12752ac23f9f9b51c5fc` | commit | commit identity; not a blob pin |
| `dafe686bfb708a309fcb36482f60fb1aaeb947b2` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `db02ae11bf4a1d7705f31b328c627714f91e1c78` | commit | commit identity; not a blob pin |
| `db9152ab1c5ef113b8727749d4309ec70505480f` | commit | commit identity; not a blob pin |
| `dbc152cd601a1dfbff2c8cb9a447b2010b16ccc4` | tree | tree identity; not a blob pin |
| `dd0a501248e092c2a4475088d94d7449b7bd98b5` | commit | commit identity; not a blob pin |
| `dd92e1146ec8eb7024da6c0f62aa721bdc1be780` | commit | commit identity; not a blob pin |
| `dedfdf11878696bea956df61ad53498c247cd8da` | blob | Source/output snapshot or reported current value; no current equality gate |
| `df7b026590677448438be62d2249f13f2da1cbaf` | commit | commit identity; not a blob pin |
| `df8bf63daf52d35f49e109fa10d14a59ee494ee7` | blob | Source/output snapshot or reported current value; no current equality gate |
| `e00e68e680d586346abada94500955abfe938ca3` | commit | commit identity; not a blob pin |
| `e1fd5d1b24cdc5e08a29f1e8216a1c6b62c3f44d` | blob | Source/output snapshot or reported current value; no current equality gate |
| `e2313ab473ea1b5a7b5b9246a564749188c1c2c8` | commit | commit identity; not a blob pin |
| `e26f1bac5f5170fbfd8b51aad71ba49d0665e609` | commit | commit identity; not a blob pin |
| `e291a88211c45ee7285fd8abebcc6ef92bc39f23` | commit | commit identity; not a blob pin |
| `e2a029d8ac3af7575888dac22fc4bf173ebec232` | commit | commit identity; not a blob pin |
| `e34868c6a12e5488224095b3248e59c8be9128f1` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `e7259a5d17f0d73a993858c5f17e678700a74498` | commit | commit identity; not a blob pin |
| `e80c5d53989af35987aa0b8371b4220acd4e3808` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `e864de49dcfbb053232ba42b24dbdeab04b43373` | tree | tree identity; not a blob pin |
| `e953c4870aaeee24b13c75a8647c50609720ae01` | blob | Inventory L; all occurrences listed in addendum |
| `e9caa181278048cdd0c403929d00a03d5ecd3ab4` | commit | commit identity; not a blob pin |
| `e9f6fc0d880b9f74213791b36df65f63ad88c1c5` | commit | commit identity; not a blob pin |
| `ea165f8d65b6e75b540449e92b4886f43607fa02` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `ea867668696d6b1114a443d0fe4e840d96b948f6` | commit | commit identity; not a blob pin |
| `ea8b19ea533ebb9622900b0ca3bffe3f6405ac4b` | commit | commit identity; not a blob pin |
| `eb0a53cd70cd22ad4301cd0be9d368db8caa355c` | blob | Source/output snapshot or reported current value; no current equality gate |
| `eb14da2a6c5b5366cd4aed855bd453dcb4d79a42` | commit | commit identity; not a blob pin |
| `eb1caf8285c174697d78834246a304ffe9006427` | commit | commit identity; not a blob pin |
| `ecb78a446e988fb40615f3e62da08714ef5786f5` | commit | commit identity; not a blob pin |
| `ed1d48d52d943f000511573b78ebcfbf3cf5c114` | commit | commit identity; not a blob pin |
| `ee35e81f13558c1482947498570a2ebd8e4dfc4c` | blob | Source/output snapshot or reported current value; no current equality gate |
| `ee64ca29d99c5b955fb96d29a0ccfaa8cdae52b6` | blob | Source/output snapshot or reported current value; no current equality gate |
| `eee77d135f03471b78ce673223dafc7e0b0fb36b` | commit | commit identity; not a blob pin |
| `eef11daa33332c2ddfd75ab3045a8caa3b84513f` | commit | commit identity; not a blob pin |
| `ef942b7713c7468e8851c6b372b64d42b5333ad8` | commit | commit identity; not a blob pin |
| `eff0f44f28d0232c6177c40b2f2feb2aa951ae09` | commit | commit identity; not a blob pin |
| `f020860b86933bf7511befccdb833b0c532b3629` | blob | Inventory P4; all occurrences listed in addendum |
| `f021965129e767234225364e229fb4be99395e6a` | blob | Source/output snapshot or reported current value; no current equality gate |
| `f1734e00e5a167dc18bfff1a873994bee124a3f7` | commit | commit identity; not a blob pin |
| `f1cc5b565a6dfb239795f586ae5e6454f377830b` | blob | Source/output snapshot or reported current value; no current equality gate |
| `f1ff0705f3e847573646824c284001ccd00ffd01` | blob | Source/output snapshot or reported current value; no current equality gate |
| `f2a370dd55c29d7b3403e3872489bd965e38411e` | commit | commit identity; not a blob pin |
| `f4df0d8ce0253e7b9755f7eb77e857b2d49057e0` | commit | commit identity; not a blob pin |
| `f50047a902f9e4f2e6a25e904f6f89ad758eb8c0` | commit | commit identity; not a blob pin |
| `f6558996c611f74b88c60928f5b285c553303c14` | commit | commit identity; not a blob pin |
| `f8a63bc83d2bc00f8e128d10d2b7bd83db84e510` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `f8df15beef280a8aa02929f92974f09fcc58e7a8` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `f931cfc87bdeaa1ed2495df0ce659ee832ac1c33` | commit | commit identity; not a blob pin |
| `faf41fca3ac0a4ed838ae269816dbc53510cbbd9` | blob | Source/output snapshot or reported current value; no current equality gate |
| `fb8b67b6d9f1fcddea68153a9f4b9e9310cee776` | tree | tree identity; not a blob pin |
| `fc11cdf0150e54ed38bb363f2ded7238c48c6e53` | commit | commit identity; not a blob pin |
| `fc28ad4eda7e49f34324d46253dfd950533740db` | commit | commit identity; not a blob pin |
| `fc3ed1b33bf294cb48f3fbcb9cce5df058e51733` | blob | Source/output snapshot or reported current value; no current equality gate |
| `fe08e4134b2f2e58f48b636bdae7440d8cdb70dc` | commit | commit identity; not a blob pin |
| `fe1f8666c4e50f7740bfe48641d3015fb66ef7fc` | commit | commit identity; not a blob pin |
| `fe865e6b94b5724e60f2d16371eb0a3b76f66fed` | unavailable | External/unmerged provenance identity; unavailable locally; not a local executable lock |
| `fe8f12832e01828a1cba80aec908d6c9971cffcf` | commit | commit identity; not a blob pin |
| `fec140112e11fe7403fa4fbda57d629e52a99f72` | blob | Source/output snapshot or reported current value; no current equality gate |
| `fecb5e993c986080c63b4de41be5c5f476592610` | commit | commit identity; not a blob pin |
| `ff0f39a8129ca8b8d30818cce35c3d4e588872fc` | blob | Source/output snapshot or reported current value; no current equality gate |
| `ff1a955815a054f2345a2e06939f2c84bfc29be6` | commit | commit identity; not a blob pin |
| `ff88c441f36cde5b581ba29ce4c46ac47f22b218` | commit | commit identity; not a blob pin |
| `fff19605f0ccff71b6f24e61f1f8114b5c0ddd57` | commit | commit identity; not a blob pin |

## Command evidence

Commands below actually ran. Read-only source/merge-content reads are summarized
by output length in the table; the exact basis/command identifies their bytes.
Raw outputs (with the scan selection explicitly labeled) are retained for pin
values, type classification, first-parent
identities/transitions, stop attribution, preservation and checker results.
No source commands quoted by those outputs were executed as a result of reading.

| No. | Command | Result |
|---|---|---|
| 1 | `git rev-parse origin/main HEAD` | exit 0 |
| 2 | `git status --short --untracked-files=all` | exit 0 |
| 3 | `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 4 | `git hash-object -- runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 5 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 6 | `git hash-object -- runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 7 | `git ls-files reference/v0.3-rc1/ .aiops/` | exit 0 |
| 8 | `git rev-parse HEAD:.aiops/program.json` | exit 0 |
| 9 | `git hash-object -- .aiops/program.json` | exit 0 |
| 10 | `git rev-parse HEAD:reference/v0.3-rc1/DESIGN_SUI_ZK.md` | exit 0 |
| 11 | `git hash-object -- reference/v0.3-rc1/DESIGN_SUI_ZK.md` | exit 0 |
| 12 | `git rev-parse 'HEAD:"reference/v0.3-rc1/KIX_v0.3_rc1_\352\265\254\355\230\204\352\262\260\352\263\274\354\231\200_\354\213\244\355\226\211\354\241\260\352\261\264.md"'` | exit 128 |
| 13 | `git rev-parse origin/main HEAD` | exit 0 |
| 14 | `git status --short --untracked-files=all` | exit 0 |
| 15 | `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 16 | `git hash-object -- runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 17 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 18 | `git hash-object -- runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 19 | `git ls-files -z reference/v0.3-rc1/ .aiops/` | exit 0 |
| 20 | `git rev-parse HEAD:.aiops/program.json` | exit 0 |
| 21 | `git hash-object -- .aiops/program.json` | exit 0 |
| 22 | `git rev-parse HEAD:reference/v0.3-rc1/DESIGN_SUI_ZK.md` | exit 0 |
| 23 | `git hash-object -- reference/v0.3-rc1/DESIGN_SUI_ZK.md` | exit 0 |
| 24 | `git rev-parse 'HEAD:reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md'` | exit 0 |
| 25 | `git hash-object -- 'reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md'` | exit 0 |
| 26 | `git rev-parse HEAD:reference/v0.3-rc1/README.md` | exit 0 |
| 27 | `git hash-object -- reference/v0.3-rc1/README.md` | exit 0 |
| 28 | `git rev-parse HEAD:reference/v0.3-rc1/adapters.py` | exit 0 |
| 29 | `git hash-object -- reference/v0.3-rc1/adapters.py` | exit 0 |
| 30 | `git rev-parse HEAD:reference/v0.3-rc1/archive_driver.py` | exit 0 |
| 31 | `git hash-object -- reference/v0.3-rc1/archive_driver.py` | exit 0 |
| 32 | `git rev-parse HEAD:reference/v0.3-rc1/assets.py` | exit 0 |
| 33 | `git hash-object -- reference/v0.3-rc1/assets.py` | exit 0 |
| 34 | `git rev-parse HEAD:reference/v0.3-rc1/canonical_encoding.py` | exit 0 |
| 35 | `git hash-object -- reference/v0.3-rc1/canonical_encoding.py` | exit 0 |
| 36 | `git rev-parse HEAD:reference/v0.3-rc1/changes_from_v02.diff` | exit 0 |
| 37 | `git hash-object -- reference/v0.3-rc1/changes_from_v02.diff` | exit 0 |
| 38 | `git rev-parse HEAD:reference/v0.3-rc1/check_reproducibility.py` | exit 0 |
| 39 | `git hash-object -- reference/v0.3-rc1/check_reproducibility.py` | exit 0 |
| 40 | `git rev-parse HEAD:reference/v0.3-rc1/client/archive-fixture.mjs` | exit 0 |
| 41 | `git hash-object -- reference/v0.3-rc1/client/archive-fixture.mjs` | exit 0 |
| 42 | `git rev-parse HEAD:reference/v0.3-rc1/client/backup.mjs` | exit 0 |
| 43 | `git hash-object -- reference/v0.3-rc1/client/backup.mjs` | exit 0 |
| 44 | `git rev-parse HEAD:reference/v0.3-rc1/client/canonical_encoding.ts` | exit 0 |
| 45 | `git hash-object -- reference/v0.3-rc1/client/canonical_encoding.ts` | exit 0 |
| 46 | `git rev-parse HEAD:reference/v0.3-rc1/client/commerce_v2.ts` | exit 0 |
| 47 | `git hash-object -- reference/v0.3-rc1/client/commerce_v2.ts` | exit 0 |
| 48 | `git rev-parse HEAD:reference/v0.3-rc1/client/compile-circuits.mjs` | exit 0 |
| 49 | `git hash-object -- reference/v0.3-rc1/client/compile-circuits.mjs` | exit 0 |
| 50 | `git rev-parse HEAD:reference/v0.3-rc1/client/encoding.mjs` | exit 0 |
| 51 | `git hash-object -- reference/v0.3-rc1/client/encoding.mjs` | exit 0 |
| 52 | `git rev-parse HEAD:reference/v0.3-rc1/client/independent.mjs` | exit 0 |
| 53 | `git hash-object -- reference/v0.3-rc1/client/independent.mjs` | exit 0 |
| 54 | `git rev-parse HEAD:reference/v0.3-rc1/client/localnet-boundaries.mjs` | exit 0 |
| 55 | `git hash-object -- reference/v0.3-rc1/client/localnet-boundaries.mjs` | exit 0 |
| 56 | `git rev-parse HEAD:reference/v0.3-rc1/client/localnet-paid.mjs` | exit 0 |
| 57 | `git hash-object -- reference/v0.3-rc1/client/localnet-paid.mjs` | exit 0 |
| 58 | `git rev-parse HEAD:reference/v0.3-rc1/client/localnet.mjs` | exit 0 |
| 59 | `git hash-object -- reference/v0.3-rc1/client/localnet.mjs` | exit 0 |
| 60 | `git rev-parse HEAD:reference/v0.3-rc1/client/offline.test.mjs` | exit 0 |
| 61 | `git hash-object -- reference/v0.3-rc1/client/offline.test.mjs` | exit 0 |
| 62 | `git rev-parse HEAD:reference/v0.3-rc1/client/package-lock.json` | exit 0 |
| 63 | `git hash-object -- reference/v0.3-rc1/client/package-lock.json` | exit 0 |
| 64 | `git rev-parse HEAD:reference/v0.3-rc1/client/package.json` | exit 0 |
| 65 | `git hash-object -- reference/v0.3-rc1/client/package.json` | exit 0 |
| 66 | `git rev-parse HEAD:reference/v0.3-rc1/client/paid-chain.mjs` | exit 0 |
| 67 | `git hash-object -- reference/v0.3-rc1/client/paid-chain.mjs` | exit 0 |
| 68 | `git rev-parse HEAD:reference/v0.3-rc1/client/private.mjs` | exit 0 |
| 69 | `git hash-object -- reference/v0.3-rc1/client/private.mjs` | exit 0 |
| 70 | `git rev-parse HEAD:reference/v0.3-rc1/client/setup-zk.mjs` | exit 0 |
| 71 | `git hash-object -- reference/v0.3-rc1/client/setup-zk.mjs` | exit 0 |
| 72 | `git rev-parse HEAD:reference/v0.3-rc1/client/types.mjs` | exit 0 |
| 73 | `git hash-object -- reference/v0.3-rc1/client/types.mjs` | exit 0 |
| 74 | `git rev-parse HEAD:reference/v0.3-rc1/client/verify_canonical.ts` | exit 0 |
| 75 | `git hash-object -- reference/v0.3-rc1/client/verify_canonical.ts` | exit 0 |
| 76 | `git rev-parse HEAD:reference/v0.3-rc1/client/zk-policy.mjs` | exit 0 |
| 77 | `git hash-object -- reference/v0.3-rc1/client/zk-policy.mjs` | exit 0 |
| 78 | `git rev-parse HEAD:reference/v0.3-rc1/client/zk-regression.mjs` | exit 0 |
| 79 | `git hash-object -- reference/v0.3-rc1/client/zk-regression.mjs` | exit 0 |
| 80 | `git rev-parse HEAD:reference/v0.3-rc1/client/zk-test-utils.mjs` | exit 0 |
| 81 | `git hash-object -- reference/v0.3-rc1/client/zk-test-utils.mjs` | exit 0 |
| 82 | `git rev-parse HEAD:reference/v0.3-rc1/commerce.py` | exit 0 |
| 83 | `git hash-object -- reference/v0.3-rc1/commerce.py` | exit 0 |
| 84 | `git rev-parse HEAD:reference/v0.3-rc1/commerce_driver.py` | exit 0 |
| 85 | `git hash-object -- reference/v0.3-rc1/commerce_driver.py` | exit 0 |
| 86 | `git rev-parse HEAD:reference/v0.3-rc1/common.py` | exit 0 |
| 87 | `git hash-object -- reference/v0.3-rc1/common.py` | exit 0 |
| 88 | `git rev-parse HEAD:reference/v0.3-rc1/contracts.py` | exit 0 |
| 89 | `git hash-object -- reference/v0.3-rc1/contracts.py` | exit 0 |
| 90 | `git rev-parse HEAD:reference/v0.3-rc1/core.py` | exit 0 |
| 91 | `git hash-object -- reference/v0.3-rc1/core.py` | exit 0 |
| 92 | `git rev-parse HEAD:reference/v0.3-rc1/dispatch.py` | exit 0 |
| 93 | `git hash-object -- reference/v0.3-rc1/dispatch.py` | exit 0 |
| 94 | `git rev-parse HEAD:reference/v0.3-rc1/execution_contracts.py` | exit 0 |
| 95 | `git hash-object -- reference/v0.3-rc1/execution_contracts.py` | exit 0 |
| 96 | `git rev-parse HEAD:reference/v0.3-rc1/finance.py` | exit 0 |
| 97 | `git hash-object -- reference/v0.3-rc1/finance.py` | exit 0 |
| 98 | `git rev-parse HEAD:reference/v0.3-rc1/fixtures/canonical_encoding_v1.json` | exit 0 |
| 99 | `git hash-object -- reference/v0.3-rc1/fixtures/canonical_encoding_v1.json` | exit 0 |
| 100 | `git rev-parse HEAD:reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json` | exit 0 |
| 101 | `git hash-object -- reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json` | exit 0 |
| 102 | `git rev-parse HEAD:reference/v0.3-rc1/lifecycle.py` | exit 0 |
| 103 | `git hash-object -- reference/v0.3-rc1/lifecycle.py` | exit 0 |
| 104 | `git rev-parse HEAD:reference/v0.3-rc1/mock_provider.py` | exit 0 |
| 105 | `git hash-object -- reference/v0.3-rc1/mock_provider.py` | exit 0 |
| 106 | `git rev-parse HEAD:reference/v0.3-rc1/mutation_check.py` | exit 0 |
| 107 | `git hash-object -- reference/v0.3-rc1/mutation_check.py` | exit 0 |
| 108 | `git rev-parse HEAD:reference/v0.3-rc1/observations.py` | exit 0 |
| 109 | `git hash-object -- reference/v0.3-rc1/observations.py` | exit 0 |
| 110 | `git rev-parse HEAD:reference/v0.3-rc1/paid_archive.py` | exit 0 |
| 111 | `git hash-object -- reference/v0.3-rc1/paid_archive.py` | exit 0 |
| 112 | `git rev-parse HEAD:reference/v0.3-rc1/paid_driver.py` | exit 0 |
| 113 | `git hash-object -- reference/v0.3-rc1/paid_driver.py` | exit 0 |
| 114 | `git rev-parse HEAD:reference/v0.3-rc1/paid_integration.py` | exit 0 |
| 115 | `git hash-object -- reference/v0.3-rc1/paid_integration.py` | exit 0 |
| 116 | `git rev-parse HEAD:reference/v0.3-rc1/paid_recovery.py` | exit 0 |
| 117 | `git hash-object -- reference/v0.3-rc1/paid_recovery.py` | exit 0 |
| 118 | `git rev-parse HEAD:reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 119 | `git hash-object -- reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 120 | `git rev-parse HEAD:reference/v0.3-rc1/requirements.txt` | exit 0 |
| 121 | `git hash-object -- reference/v0.3-rc1/requirements.txt` | exit 0 |
| 122 | `git rev-parse HEAD:reference/v0.3-rc1/results/acceptance_trace.json` | exit 0 |
| 123 | `git hash-object -- reference/v0.3-rc1/results/acceptance_trace.json` | exit 0 |
| 124 | `git rev-parse HEAD:reference/v0.3-rc1/results/client_offline_tests.txt` | exit 0 |
| 125 | `git hash-object -- reference/v0.3-rc1/results/client_offline_tests.txt` | exit 0 |
| 126 | `git rev-parse HEAD:reference/v0.3-rc1/results/client_syntax.json` | exit 0 |
| 127 | `git hash-object -- reference/v0.3-rc1/results/client_syntax.json` | exit 0 |
| 128 | `git rev-parse HEAD:reference/v0.3-rc1/results/manifest.sha256.json` | exit 0 |
| 129 | `git hash-object -- reference/v0.3-rc1/results/manifest.sha256.json` | exit 0 |
| 130 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M01.txt` | exit 0 |
| 131 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M01.txt` | exit 0 |
| 132 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M02.txt` | exit 0 |
| 133 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M02.txt` | exit 0 |
| 134 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M03.txt` | exit 0 |
| 135 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M03.txt` | exit 0 |
| 136 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M04.txt` | exit 0 |
| 137 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M04.txt` | exit 0 |
| 138 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M05.txt` | exit 0 |
| 139 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M05.txt` | exit 0 |
| 140 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M06.txt` | exit 0 |
| 141 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M06.txt` | exit 0 |
| 142 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M07.txt` | exit 0 |
| 143 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M07.txt` | exit 0 |
| 144 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M08.txt` | exit 0 |
| 145 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M08.txt` | exit 0 |
| 146 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M09.txt` | exit 0 |
| 147 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M09.txt` | exit 0 |
| 148 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M10.txt` | exit 0 |
| 149 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M10.txt` | exit 0 |
| 150 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M11.txt` | exit 0 |
| 151 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M11.txt` | exit 0 |
| 152 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M12.txt` | exit 0 |
| 153 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M12.txt` | exit 0 |
| 154 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M13.txt` | exit 0 |
| 155 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M13.txt` | exit 0 |
| 156 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M14.txt` | exit 0 |
| 157 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M14.txt` | exit 0 |
| 158 | `git rev-parse HEAD:reference/v0.3-rc1/results/mutation_results.json` | exit 0 |
| 159 | `git hash-object -- reference/v0.3-rc1/results/mutation_results.json` | exit 0 |
| 160 | `git rev-parse HEAD:reference/v0.3-rc1/results/preflight.json` | exit 0 |
| 161 | `git hash-object -- reference/v0.3-rc1/results/preflight.json` | exit 0 |
| 162 | `git rev-parse HEAD:reference/v0.3-rc1/results/reproducibility.json` | exit 0 |
| 163 | `git hash-object -- reference/v0.3-rc1/results/reproducibility.json` | exit 0 |
| 164 | `git rev-parse HEAD:reference/v0.3-rc1/results/review_trace_v03.json` | exit 0 |
| 165 | `git hash-object -- reference/v0.3-rc1/results/review_trace_v03.json` | exit 0 |
| 166 | `git rev-parse HEAD:reference/v0.3-rc1/results/tests.txt` | exit 0 |
| 167 | `git hash-object -- reference/v0.3-rc1/results/tests.txt` | exit 0 |
| 168 | `git rev-parse HEAD:reference/v0.3-rc1/results/v02_unchanged.json` | exit 0 |
| 169 | `git hash-object -- reference/v0.3-rc1/results/v02_unchanged.json` | exit 0 |
| 170 | `git rev-parse HEAD:reference/v0.3-rc1/results/verification.json` | exit 0 |
| 171 | `git hash-object -- reference/v0.3-rc1/results/verification.json` | exit 0 |
| 172 | `git rev-parse HEAD:reference/v0.3-rc1/review_provenance/baseline_integrity.json` | exit 0 |
| 173 | `git hash-object -- reference/v0.3-rc1/review_provenance/baseline_integrity.json` | exit 0 |
| 174 | `git rev-parse HEAD:reference/v0.3-rc1/review_provenance/baseline_reproduced.json` | exit 0 |
| 175 | `git hash-object -- reference/v0.3-rc1/review_provenance/baseline_reproduced.json` | exit 0 |
| 176 | `git rev-parse HEAD:reference/v0.3-rc1/review_provenance/review_v02_probe.py` | exit 0 |
| 177 | `git hash-object -- reference/v0.3-rc1/review_provenance/review_v02_probe.py` | exit 0 |
| 178 | `git rev-parse HEAD:reference/v0.3-rc1/review_provenance/review_verification.json` | exit 0 |
| 179 | `git hash-object -- reference/v0.3-rc1/review_provenance/review_verification.json` | exit 0 |
| 180 | `git rev-parse HEAD:reference/v0.3-rc1/review_trace_v03.py` | exit 0 |
| 181 | `git hash-object -- reference/v0.3-rc1/review_trace_v03.py` | exit 0 |
| 182 | `git rev-parse HEAD:reference/v0.3-rc1/scripts/preflight.py` | exit 0 |
| 183 | `git hash-object -- reference/v0.3-rc1/scripts/preflight.py` | exit 0 |
| 184 | `git rev-parse HEAD:reference/v0.3-rc1/scripts/verify_package.py` | exit 0 |
| 185 | `git hash-object -- reference/v0.3-rc1/scripts/verify_package.py` | exit 0 |
| 186 | `git rev-parse HEAD:reference/v0.3-rc1/source_inventory.json` | exit 0 |
| 187 | `git hash-object -- reference/v0.3-rc1/source_inventory.json` | exit 0 |
| 188 | `git rev-parse HEAD:reference/v0.3-rc1/storage_receipt.py` | exit 0 |
| 189 | `git hash-object -- reference/v0.3-rc1/storage_receipt.py` | exit 0 |
| 190 | `git rev-parse HEAD:reference/v0.3-rc1/sui/Move.lock` | exit 0 |
| 191 | `git hash-object -- reference/v0.3-rc1/sui/Move.lock` | exit 0 |
| 192 | `git rev-parse HEAD:reference/v0.3-rc1/sui/Move.toml` | exit 0 |
| 193 | `git hash-object -- reference/v0.3-rc1/sui/Move.toml` | exit 0 |
| 194 | `git rev-parse HEAD:reference/v0.3-rc1/sui/sources/rights.move` | exit 0 |
| 195 | `git hash-object -- reference/v0.3-rc1/sui/sources/rights.move` | exit 0 |
| 196 | `git rev-parse HEAD:reference/v0.3-rc1/sui/sources/zk_gate.move` | exit 0 |
| 197 | `git hash-object -- reference/v0.3-rc1/sui/sources/zk_gate.move` | exit 0 |
| 198 | `git rev-parse HEAD:reference/v0.3-rc1/sui/tests/rights_tests.move` | exit 0 |
| 199 | `git hash-object -- reference/v0.3-rc1/sui/tests/rights_tests.move` | exit 0 |
| 200 | `git rev-parse HEAD:reference/v0.3-rc1/test_assets.py` | exit 0 |
| 201 | `git hash-object -- reference/v0.3-rc1/test_assets.py` | exit 0 |
| 202 | `git rev-parse HEAD:reference/v0.3-rc1/test_canonical_encoding.py` | exit 0 |
| 203 | `git hash-object -- reference/v0.3-rc1/test_canonical_encoding.py` | exit 0 |
| 204 | `git rev-parse HEAD:reference/v0.3-rc1/test_commerce.py` | exit 0 |
| 205 | `git hash-object -- reference/v0.3-rc1/test_commerce.py` | exit 0 |
| 206 | `git rev-parse HEAD:reference/v0.3-rc1/test_commerce_driver.py` | exit 0 |
| 207 | `git hash-object -- reference/v0.3-rc1/test_commerce_driver.py` | exit 0 |
| 208 | `git rev-parse HEAD:reference/v0.3-rc1/test_core.py` | exit 0 |
| 209 | `git hash-object -- reference/v0.3-rc1/test_core.py` | exit 0 |
| 210 | `git rev-parse HEAD:reference/v0.3-rc1/test_execution_contracts.py` | exit 0 |
| 211 | `git hash-object -- reference/v0.3-rc1/test_execution_contracts.py` | exit 0 |
| 212 | `git rev-parse HEAD:reference/v0.3-rc1/test_paid_archive.py` | exit 0 |
| 213 | `git hash-object -- reference/v0.3-rc1/test_paid_archive.py` | exit 0 |
| 214 | `git rev-parse HEAD:reference/v0.3-rc1/test_paid_integration.py` | exit 0 |
| 215 | `git hash-object -- reference/v0.3-rc1/test_paid_integration.py` | exit 0 |
| 216 | `git rev-parse HEAD:reference/v0.3-rc1/test_paid_recovery.py` | exit 0 |
| 217 | `git hash-object -- reference/v0.3-rc1/test_paid_recovery.py` | exit 0 |
| 218 | `git rev-parse HEAD:reference/v0.3-rc1/test_storage_receipt.py` | exit 0 |
| 219 | `git hash-object -- reference/v0.3-rc1/test_storage_receipt.py` | exit 0 |
| 220 | `git rev-parse HEAD:reference/v0.3-rc1/test_v02.py` | exit 0 |
| 221 | `git hash-object -- reference/v0.3-rc1/test_v02.py` | exit 0 |
| 222 | `git rev-parse HEAD:reference/v0.3-rc1/test_v03.py` | exit 0 |
| 223 | `git hash-object -- reference/v0.3-rc1/test_v03.py` | exit 0 |
| 224 | `git rev-parse HEAD:reference/v0.3-rc1/vendor/rights_model.py` | exit 0 |
| 225 | `git hash-object -- reference/v0.3-rc1/vendor/rights_model.py` | exit 0 |
| 226 | `git rev-parse HEAD:reference/v0.3-rc1/vendor/tix_reconcile.py` | exit 0 |
| 227 | `git hash-object -- reference/v0.3-rc1/vendor/tix_reconcile.py` | exit 0 |
| 228 | `git rev-parse HEAD:reference/v0.3-rc1/verify.py` | exit 0 |
| 229 | `git hash-object -- reference/v0.3-rc1/verify.py` | exit 0 |
| 230 | `git rev-parse HEAD:reference/v0.3-rc1/zk/artifacts/README.md` | exit 0 |
| 231 | `git hash-object -- reference/v0.3-rc1/zk/artifacts/README.md` | exit 0 |
| 232 | `git rev-parse HEAD:reference/v0.3-rc1/zk/circuits/common.circom` | exit 0 |
| 233 | `git hash-object -- reference/v0.3-rc1/zk/circuits/common.circom` | exit 0 |
| 234 | `git rev-parse HEAD:reference/v0.3-rc1/zk/circuits/mint.circom` | exit 0 |
| 235 | `git hash-object -- reference/v0.3-rc1/zk/circuits/mint.circom` | exit 0 |
| 236 | `git rev-parse HEAD:reference/v0.3-rc1/zk/circuits/spend.circom` | exit 0 |
| 237 | `git hash-object -- reference/v0.3-rc1/zk/circuits/spend.circom` | exit 0 |
| 238 | `git grep -n -E '(^&#124;[^0-9a-f])[0-9a-f]{40}([^0-9a-f]&#124;$)' HEAD -- '*.rs' '*.py' '*.md'` | exit 0 |
| 239 | `sha256sum /workspace/kix-run/wt/plan-perf-probe-fail-closed-and-release-repro/DECISION_REQUIRED.md` | exit 0 |
| 240 | `nl -ba /workspace/kix-run/wt/plan-perf-probe-fail-closed-and-release-repro/DECISION_REQUIRED.md` | exit 0 |
| 241 | `git log --first-parent --merges '--format=%H %s' origin/main` | exit 0 |
| 242 | `git show -s --format=%H%n%P%n%s 035d5705c93b318a49941ce5f7410f843360c427` | exit 0 |
| 243 | `git diff '035d5705c93b318a49941ce5f7410f843360c427^1' 035d5705c93b318a49941ce5f7410f843360c427 --name-status` | exit 0 |
| 244 | `git diff '035d5705c93b318a49941ce5f7410f843360c427^1' 035d5705c93b318a49941ce5f7410f843360c427 -- docs/ validation/ .github/workflows/ scripts/` | exit 0; read 3597 output lines |
| 245 | `git show -s --format=%H%n%P%n%s eb1caf8285c174697d78834246a304ffe9006427` | exit 0 |
| 246 | `git diff 'eb1caf8285c174697d78834246a304ffe9006427^1' eb1caf8285c174697d78834246a304ffe9006427 --name-status` | exit 0 |
| 247 | `git diff 'eb1caf8285c174697d78834246a304ffe9006427^1' eb1caf8285c174697d78834246a304ffe9006427 -- docs/ validation/ .github/workflows/ scripts/` | exit 0; read 313 output lines |
| 248 | `git show -s --format=%H%n%P%n%s 876f41067bc7eb70bcd6ebd9c744c11b46f046b6` | exit 0 |
| 249 | `git diff '876f41067bc7eb70bcd6ebd9c744c11b46f046b6^1' 876f41067bc7eb70bcd6ebd9c744c11b46f046b6 --name-status` | exit 0 |
| 250 | `git diff '876f41067bc7eb70bcd6ebd9c744c11b46f046b6^1' 876f41067bc7eb70bcd6ebd9c744c11b46f046b6 -- docs/ validation/ .github/workflows/ scripts/` | exit 0; read 211 output lines |
| 251 | `git show -s --format=%H%n%P%n%s d016caee4ae40f28f531809359ee77ac22db0073` | exit 0 |
| 252 | `git diff 'd016caee4ae40f28f531809359ee77ac22db0073^1' d016caee4ae40f28f531809359ee77ac22db0073 --name-status` | exit 0 |
| 253 | `git diff 'd016caee4ae40f28f531809359ee77ac22db0073^1' d016caee4ae40f28f531809359ee77ac22db0073 -- docs/ validation/ .github/workflows/ scripts/` | exit 0; read 223 output lines |
| 254 | `git show -s --format=%H%n%P%n%s 70b976c0b8db686b1d21ff0831c275abf77a3d0a` | exit 0 |
| 255 | `git diff '70b976c0b8db686b1d21ff0831c275abf77a3d0a^1' 70b976c0b8db686b1d21ff0831c275abf77a3d0a --name-status` | exit 0 |
| 256 | `git diff '70b976c0b8db686b1d21ff0831c275abf77a3d0a^1' 70b976c0b8db686b1d21ff0831c275abf77a3d0a -- docs/ validation/ .github/workflows/ scripts/` | exit 0; read 345 output lines |
| 257 | `git show -s --format=%H%n%P%n%s 9d50fb660248b66a5959f48f7dc96e68c9d5530b` | exit 0 |
| 258 | `git diff '9d50fb660248b66a5959f48f7dc96e68c9d5530b^1' 9d50fb660248b66a5959f48f7dc96e68c9d5530b --name-status` | exit 0 |
| 259 | `git diff '9d50fb660248b66a5959f48f7dc96e68c9d5530b^1' 9d50fb660248b66a5959f48f7dc96e68c9d5530b -- docs/ validation/ .github/workflows/ scripts/` | exit 0; read 194 output lines |
| 260 | `git show -s --format=%H%n%P%n%s 9ed15a7adc93359e99bb5c3512a3ca20c77cb264` | exit 0 |
| 261 | `git diff '9ed15a7adc93359e99bb5c3512a3ca20c77cb264^1' 9ed15a7adc93359e99bb5c3512a3ca20c77cb264 --name-status` | exit 0 |
| 262 | `git diff '9ed15a7adc93359e99bb5c3512a3ca20c77cb264^1' 9ed15a7adc93359e99bb5c3512a3ca20c77cb264 -- docs/ validation/ .github/workflows/ scripts/` | exit 0; read 318 output lines |
| 263 | `git show -s --format=%H%n%P%n%s 8e4813e868961adbabb7d1ee450a346f8fb6add1` | exit 0 |
| 264 | `git diff '8e4813e868961adbabb7d1ee450a346f8fb6add1^1' 8e4813e868961adbabb7d1ee450a346f8fb6add1 --name-status` | exit 0 |
| 265 | `git diff '8e4813e868961adbabb7d1ee450a346f8fb6add1^1' 8e4813e868961adbabb7d1ee450a346f8fb6add1 -- docs/ validation/ .github/workflows/ scripts/` | exit 0; read 1035 output lines |
| 266 | `git log --first-parent --merges --full-history '--format=%H %s' origin/main -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 267 | `git log --follow '--format=%H %s' -- runtime/crates/kix-kernel/examples/r1_perf_probe.rs` | exit 0 |
| 268 | `git show -s --format=%H%n%P%n%s 9e8f489` | exit 0 |
| 269 | `git show -s --format=%H%n%P%n%s 7ba8003` | exit 0 |
| 270 | `git show -s --format=%H%n%P%n%s 41abd14` | exit 0 |
| 271 | `git diff 'd016caee4ae40f28f531809359ee77ac22db0073^1' d016caee4ae40f28f531809359ee77ac22db0073 -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 272 | `git rev-parse 'd016caee4ae40f28f531809359ee77ac22db0073^1:runtime/crates/kix-kernel/tests/contract_edge_cases.rs' d016caee4ae40f28f531809359ee77ac22db0073:runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 273 | `git diff '70b976c0b8db686b1d21ff0831c275abf77a3d0a^1' 70b976c0b8db686b1d21ff0831c275abf77a3d0a -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 274 | `git rev-parse '70b976c0b8db686b1d21ff0831c275abf77a3d0a^1:runtime/crates/kix-kernel/tests/contract_edge_cases.rs' 70b976c0b8db686b1d21ff0831c275abf77a3d0a:runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 275 | `git show HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs` | exit 0; read 241 output lines |
| 276 | `git show HEAD:runtime/crates/kix-kernel/tests/contract_invariants.rs` | exit 0; read 1116 output lines |
| 277 | `git show HEAD:runtime/crates/kix-kernel/tests/e4_state_model.rs` | exit 0; read 2202 output lines |
| 278 | `git show HEAD:runtime/crates/kix-kernel/tests/performance_harness.rs` | exit 0; read 776 output lines |
| 279 | `git show HEAD:docs/contracts/CONTRACT_INVARIANTS.md` | exit 0; read 91 output lines |
| 280 | `git show HEAD:docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md` | exit 0; read 95 output lines |
| 281 | `git show HEAD:docs/contracts/PERFORMANCE_MEASUREMENT.md` | exit 0; read 123 output lines |
| 282 | `git show HEAD:docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md` | exit 0; read 112 output lines |
| 283 | `git show HEAD:docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md` | exit 0; read 229 output lines |
| 284 | `git show HEAD:.github/workflows/ktx-kernel.yml` | exit 0; read 124 output lines |
| 285 | `git show HEAD:.github/workflows/protocol.yml` | exit 0; read 412 output lines |
| 286 | `git show HEAD:exploration/stage4/budget.py` | exit 0; read 42 output lines |
| 287 | `git show HEAD:scripts/check_adapter_identity_map.py` | exit 0; read 535 output lines |
| 288 | `git show HEAD:scripts/check_bcs1_evidence_map.py` | exit 0; read 430 output lines |
| 289 | `git show HEAD:scripts/check_contract_invariants_evidence_map.py` | exit 0; read 542 output lines |
| 290 | `git show HEAD:scripts/check_feature_semantics_evidence_map.py` | exit 0; read 403 output lines |
| 291 | `git show HEAD:scripts/check_integration_gate_contract_evidence_map.py` | exit 0; read 510 output lines |
| 292 | `git show HEAD:scripts/check_lifecycle_adr_evidence_map.py` | exit 0; read 376 output lines |
| 293 | `git show HEAD:scripts/check_performance_measurement_evidence_map.py` | exit 0; read 411 output lines |
| 294 | `git show HEAD:scripts/check_readiness_evidence_map.py` | exit 0; read 666 output lines |
| 295 | `git show HEAD:scripts/check_sdk_client.py` | exit 0; read 193 output lines |
| 296 | `git show HEAD:scripts/check_toss_card_profile_evidence_map.py` | exit 0; read 455 output lines |
| 297 | `git show HEAD:scripts/check_v5_transition_evidence_map.py` | exit 0; read 644 output lines |
| 298 | `git grep -n -E 'r1_perf_probe&#124;cargo run&#124;--examples&#124;--all-targets' HEAD -- .github/ scripts/ runtime/` | exit 0 |
| 299 | `git cat-file -t 69564b166f0c27f9af5d8422f0a466b18d74c20f` | exit 0 |
| 300 | `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 301 | `git hash-object -- runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 302 | `git cat-file -t b607996c83a119c349f1cc90469ac1ba82764e20` | exit 0 |
| 303 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 304 | `git hash-object -- runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 305 | `git cat-file -t d37ea7df55423c83bedee16bf12bdc8dd61f7cae` | exit 0 |
| 306 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 307 | `git hash-object -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 308 | `git cat-file -t f020860b86933bf7511befccdb833b0c532b3629` | exit 0 |
| 309 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/support/model_v4.rs` | exit 0 |
| 310 | `git hash-object -- runtime/crates/kix-kernel/tests/support/model_v4.rs` | exit 0 |
| 311 | `git cat-file -t 619ae21c82ca3df5661bd3831613f15fa65225ff` | exit 0 |
| 312 | `git rev-parse HEAD:reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 313 | `git hash-object -- reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 314 | `git cat-file -t 07c36869e7b68fff10b02e6c59d7119df56d0785` | exit 0 |
| 315 | `git rev-parse HEAD:docs/adr/0001-ktx-authority-commit-recovery.md` | exit 0 |
| 316 | `git hash-object -- docs/adr/0001-ktx-authority-commit-recovery.md` | exit 0 |
| 317 | `git rev-parse 0394a36a655b86bacb568b055d377d4c4fd91185:docs/adr/0001-ktx-authority-commit-recovery.md` | exit 0 |
| 318 | `git cat-file -t e953c4870aaeee24b13c75a8647c50609720ae01` | exit 0 |
| 319 | `git rev-parse HEAD:docs/contracts/STATE_LIFECYCLE.md` | exit 0 |
| 320 | `git hash-object -- docs/contracts/STATE_LIFECYCLE.md` | exit 0 |
| 321 | `git rev-parse 0394a36a655b86bacb568b055d377d4c4fd91185:docs/contracts/STATE_LIFECYCLE.md` | exit 0 |
| 322 | `git cat-file -t 900866ee99a71254fb7da1ad2aa4640477ac550c` | exit 0 |
| 323 | `git rev-parse HEAD:runtime/crates/kix-kernel/README.md` | exit 0 |
| 324 | `git hash-object -- runtime/crates/kix-kernel/README.md` | exit 0 |
| 325 | `git rev-parse 0394a36a655b86bacb568b055d377d4c4fd91185:runtime/crates/kix-kernel/README.md` | exit 0 |
| 326 | `git cat-file --batch-check='%(objectname) %(objecttype)' (stdin: all 434 unique scan candidates, sorted)` | exit 0 |
| 327 | `git log '--format=%H %s' -S LOCKED_EDGE -- runtime/crates/kix-kernel/examples/r1_perf_probe.rs` | exit 0 |
| 328 | `git rev-parse 9e8f489:runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 329 | `git show HEAD:docs/status/OPEN_USER_DECISIONS_20261022.md` | exit 0; read 99 output lines |
| 330 | `git show HEAD:docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md` | exit 0; read 262 output lines |
| 331 | `git show HEAD:docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md` | exit 0; read 215 output lines |
| 332 | `git show HEAD:docs/status/OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md` | exit 0; read 403 output lines |
| 333 | `git show HEAD:docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md` | exit 0; read 186 output lines |
| 334 | `git show HEAD:docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md` | exit 0; read 102 output lines |
| 335 | `git show HEAD:reference/ai_delegation/ai_delegation_mock.py` | exit 0; read 621 output lines |
| 336 | `git show HEAD:sdk/compat/verify_compat.mjs` | exit 0; read 381 output lines |
| 337 | `git show HEAD:docs/decisions/PROGRAM_DECISIONS_20260928.md` | exit 0; read 140 output lines |
| 338 | `python3 scripts/check_docs_index.py` | exit 0 |
| 339 | `python3 scripts/check_docs_index.py --self-test` | exit 0 |
| 340 | `python3 scripts/check_status_register.py` | exit 0 |
| 341 | `python3 scripts/check_status_register.py --self-test` | exit 0 |
| 342 | `python3 scripts/check_evidence_map_rollup.py` | exit 0 |
| 343 | `python3 scripts/check_evidence_map_rollup.py --self-test` | exit 0 |
| 344 | `python3 scripts/check_ci_checker_wiring.py` | exit 0 |
| 345 | `python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0 |
| 346 | `python3 scripts/check_ci_test_discovery.py` | exit 0 |
| 347 | `python3 scripts/check_ci_test_discovery.py --self-test` | exit 0 |
| 348 | `git grep -n -E '(^&#124;[^0-9a-f])[0-9a-f]{40}([^0-9a-f]&#124;$)' HEAD -- '*.rs' '*.py' '*.md'` | exit 0 |
| 349 | `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 350 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 351 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 352 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/support/model_v4.rs` | exit 0 |
| 353 | `git rev-parse HEAD:reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 354 | `git rev-parse HEAD:docs/adr/0001-ktx-authority-commit-recovery.md` | exit 0 |
| 355 | `git rev-parse HEAD:docs/contracts/STATE_LIFECYCLE.md` | exit 0 |
| 356 | `git rev-parse HEAD:runtime/crates/kix-kernel/README.md` | exit 0 |
| 357 | `git show -s --format=%P 035d5705c93b318a49941ce5f7410f843360c427` | exit 0 |
| 358 | `git show -s --format=%P eb1caf8285c174697d78834246a304ffe9006427` | exit 0 |
| 359 | `git show -s --format=%P 876f41067bc7eb70bcd6ebd9c744c11b46f046b6` | exit 0 |
| 360 | `git show -s --format=%P d016caee4ae40f28f531809359ee77ac22db0073` | exit 0 |
| 361 | `git show -s --format=%P 70b976c0b8db686b1d21ff0831c275abf77a3d0a` | exit 0 |
| 362 | `git show -s --format=%P 9d50fb660248b66a5959f48f7dc96e68c9d5530b` | exit 0 |
| 363 | `git show -s --format=%P 9ed15a7adc93359e99bb5c3512a3ca20c77cb264` | exit 0 |
| 364 | `git show -s --format=%P 8e4813e868961adbabb7d1ee450a346f8fb6add1` | exit 0 |
| 365 | `git diff --name-only origin/main` | exit 0 |
| 366 | `git ls-files --others --exclude-standard` | exit 0 |
| 367 | `git grep -n r1_perf_probe HEAD -- '*.rs' '*.py' '*.yml' '*.yaml'` | exit 0 |
| 368 | `git show HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs (numbered output lines 8–11)` | exit 0 |
| 369 | `git show HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs (numbered output lines 39–99)` | exit 0 |
| 370 | `git show HEAD:docs/contracts/CONTRACT_INVARIANTS.md (numbered output lines 25–35)` | exit 0 |
| 371 | `git show HEAD:docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md (numbered output lines 80–88)` | exit 0 |
| 372 | `git show HEAD:reference/ai_delegation/ai_delegation_mock.py (numbered output lines 276–295)` | exit 0 |
| 373 | `git show HEAD:sdk/compat/verify_compat.mjs (numbered output lines 160–238)` | exit 0 |
| 374 | `python3 scripts/check_status_register.py` | exit 0 |
| 375 | `python3 scripts/check_status_register.py --self-test` | exit 0 |
| 376 | `python3 scripts/check_rs_profile_traceability.py` | exit 0 |
| 377 | `python3 scripts/check_rs_profile_traceability.py --self-test` | exit 0 |
| 378 | `python3 scripts/check_read_model_source_map.py` | exit 0 |
| 379 | `python3 scripts/check_read_model_source_map.py --self-test` | exit 0 |
| 380 | `python3 scripts/check_docs_index.py` | exit 0 |
| 381 | `python3 scripts/check_docs_index.py --self-test` | exit 0 |
| 382 | `python3 scripts/check_i12_proof_ids.py` | exit 0 |
| 383 | `python3 scripts/check_i12_proof_ids.py --self-test` | exit 0 |
| 384 | `python3 scripts/check_delegation_layer_matrix.py` | exit 0 |
| 385 | `python3 scripts/check_delegation_layer_matrix.py --self-test` | exit 0 |
| 386 | `python3 scripts/check_rs_predicate_evidence_map.py` | exit 0 |
| 387 | `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0 |
| 388 | `python3 scripts/check_rs_im_evidence_map.py` | exit 0 |
| 389 | `python3 scripts/check_rs_im_evidence_map.py --self-test` | exit 0 |
| 390 | `python3 scripts/check_tl_predicate_evidence_map.py` | exit 0 |
| 391 | `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0 |
| 392 | `python3 scripts/check_contract_error_codes.py` | exit 0 |
| 393 | `python3 scripts/check_contract_error_codes.py --self-test` | exit 0 |
| 394 | `python3 scripts/check_adapter_identity_map.py` | exit 0 |
| 395 | `python3 scripts/check_adapter_identity_map.py --self-test` | exit 0 |
| 396 | `python3 scripts/check_v5_transition_evidence_map.py` | exit 0 |
| 397 | `python3 scripts/check_v5_transition_evidence_map.py --self-test` | exit 0 |
| 398 | `python3 scripts/check_readiness_evidence_map.py` | exit 0 |
| 399 | `python3 scripts/check_readiness_evidence_map.py --self-test` | exit 0 |
| 400 | `python3 scripts/check_settlement_evidence_map.py` | exit 0 |
| 401 | `python3 scripts/check_settlement_evidence_map.py --self-test` | exit 0 |
| 402 | `python3 scripts/check_bra_evidence_map.py` | exit 0 |
| 403 | `python3 scripts/check_bra_evidence_map.py --self-test` | exit 0 |
| 404 | `python3 scripts/check_credit_evidence_map.py` | exit 0 |
| 405 | `python3 scripts/check_credit_evidence_map.py --self-test` | exit 0 |
| 406 | `python3 scripts/check_primary_price_fee_evidence_map.py` | exit 0 |
| 407 | `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | exit 0 |
| 408 | `python3 scripts/check_ai_delegation_evidence_map.py` | exit 0 |
| 409 | `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | exit 0 |
| 410 | `python3 scripts/check_lifecycle_adr_evidence_map.py` | exit 0 |
| 411 | `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | exit 0 |
| 412 | `python3 scripts/check_contract_invariants_evidence_map.py` | exit 0 |
| 413 | `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | exit 0 |
| 414 | `python3 scripts/check_toss_card_profile_evidence_map.py` | exit 0 |
| 415 | `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | exit 0 |
| 416 | `python3 scripts/check_bcs1_evidence_map.py` | exit 0 |
| 417 | `python3 scripts/check_bcs1_evidence_map.py --self-test` | exit 0 |
| 418 | `python3 scripts/check_performance_measurement_evidence_map.py` | exit 0 |
| 419 | `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | exit 0 |
| 420 | `python3 scripts/check_feature_semantics_evidence_map.py` | exit 0 |
| 421 | `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | exit 0 |
| 422 | `python3 scripts/check_integration_gate_contract_evidence_map.py` | exit 0 |
| 423 | `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | exit 0 |
| 424 | `python3 scripts/check_evidence_map_rollup.py` | exit 0 |
| 425 | `python3 scripts/check_evidence_map_rollup.py --self-test` | exit 0 |
| 426 | `python3 scripts/check_ci_checker_wiring.py` | exit 0 |
| 427 | `python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0 |
| 428 | `python3 scripts/check_ci_test_discovery.py` | exit 0 |
| 429 | `python3 scripts/check_ci_test_discovery.py --self-test` | exit 0 |
| 430 | `python3 scripts/check_stage5_host.py --self-test` | exit 0 |
| 431 | `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 432 | `git hash-object -- runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 433 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 434 | `git hash-object -- runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 435 | `git ls-files -z reference/v0.3-rc1/ .aiops/` | exit 0 |
| 436 | `git rev-parse origin/main:.aiops/program.json` | exit 0 |
| 437 | `git hash-object -- .aiops/program.json` | exit 0 |
| 438 | `git rev-parse origin/main:reference/v0.3-rc1/DESIGN_SUI_ZK.md` | exit 0 |
| 439 | `git hash-object -- reference/v0.3-rc1/DESIGN_SUI_ZK.md` | exit 0 |
| 440 | `git rev-parse 'origin/main:reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md'` | exit 0 |
| 441 | `git hash-object -- 'reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md'` | exit 0 |
| 442 | `git rev-parse origin/main:reference/v0.3-rc1/README.md` | exit 0 |
| 443 | `git hash-object -- reference/v0.3-rc1/README.md` | exit 0 |
| 444 | `git rev-parse origin/main:reference/v0.3-rc1/adapters.py` | exit 0 |
| 445 | `git hash-object -- reference/v0.3-rc1/adapters.py` | exit 0 |
| 446 | `git rev-parse origin/main:reference/v0.3-rc1/archive_driver.py` | exit 0 |
| 447 | `git hash-object -- reference/v0.3-rc1/archive_driver.py` | exit 0 |
| 448 | `git rev-parse origin/main:reference/v0.3-rc1/assets.py` | exit 0 |
| 449 | `git hash-object -- reference/v0.3-rc1/assets.py` | exit 0 |
| 450 | `git rev-parse origin/main:reference/v0.3-rc1/canonical_encoding.py` | exit 0 |
| 451 | `git hash-object -- reference/v0.3-rc1/canonical_encoding.py` | exit 0 |
| 452 | `git rev-parse origin/main:reference/v0.3-rc1/changes_from_v02.diff` | exit 0 |
| 453 | `git hash-object -- reference/v0.3-rc1/changes_from_v02.diff` | exit 0 |
| 454 | `git rev-parse origin/main:reference/v0.3-rc1/check_reproducibility.py` | exit 0 |
| 455 | `git hash-object -- reference/v0.3-rc1/check_reproducibility.py` | exit 0 |
| 456 | `git rev-parse origin/main:reference/v0.3-rc1/client/archive-fixture.mjs` | exit 0 |
| 457 | `git hash-object -- reference/v0.3-rc1/client/archive-fixture.mjs` | exit 0 |
| 458 | `git rev-parse origin/main:reference/v0.3-rc1/client/backup.mjs` | exit 0 |
| 459 | `git hash-object -- reference/v0.3-rc1/client/backup.mjs` | exit 0 |
| 460 | `git rev-parse origin/main:reference/v0.3-rc1/client/canonical_encoding.ts` | exit 0 |
| 461 | `git hash-object -- reference/v0.3-rc1/client/canonical_encoding.ts` | exit 0 |
| 462 | `git rev-parse origin/main:reference/v0.3-rc1/client/commerce_v2.ts` | exit 0 |
| 463 | `git hash-object -- reference/v0.3-rc1/client/commerce_v2.ts` | exit 0 |
| 464 | `git rev-parse origin/main:reference/v0.3-rc1/client/compile-circuits.mjs` | exit 0 |
| 465 | `git hash-object -- reference/v0.3-rc1/client/compile-circuits.mjs` | exit 0 |
| 466 | `git rev-parse origin/main:reference/v0.3-rc1/client/encoding.mjs` | exit 0 |
| 467 | `git hash-object -- reference/v0.3-rc1/client/encoding.mjs` | exit 0 |
| 468 | `git rev-parse origin/main:reference/v0.3-rc1/client/independent.mjs` | exit 0 |
| 469 | `git hash-object -- reference/v0.3-rc1/client/independent.mjs` | exit 0 |
| 470 | `git rev-parse origin/main:reference/v0.3-rc1/client/localnet-boundaries.mjs` | exit 0 |
| 471 | `git hash-object -- reference/v0.3-rc1/client/localnet-boundaries.mjs` | exit 0 |
| 472 | `git rev-parse origin/main:reference/v0.3-rc1/client/localnet-paid.mjs` | exit 0 |
| 473 | `git hash-object -- reference/v0.3-rc1/client/localnet-paid.mjs` | exit 0 |
| 474 | `git rev-parse origin/main:reference/v0.3-rc1/client/localnet.mjs` | exit 0 |
| 475 | `git hash-object -- reference/v0.3-rc1/client/localnet.mjs` | exit 0 |
| 476 | `git rev-parse origin/main:reference/v0.3-rc1/client/offline.test.mjs` | exit 0 |
| 477 | `git hash-object -- reference/v0.3-rc1/client/offline.test.mjs` | exit 0 |
| 478 | `git rev-parse origin/main:reference/v0.3-rc1/client/package-lock.json` | exit 0 |
| 479 | `git hash-object -- reference/v0.3-rc1/client/package-lock.json` | exit 0 |
| 480 | `git rev-parse origin/main:reference/v0.3-rc1/client/package.json` | exit 0 |
| 481 | `git hash-object -- reference/v0.3-rc1/client/package.json` | exit 0 |
| 482 | `git rev-parse origin/main:reference/v0.3-rc1/client/paid-chain.mjs` | exit 0 |
| 483 | `git hash-object -- reference/v0.3-rc1/client/paid-chain.mjs` | exit 0 |
| 484 | `git rev-parse origin/main:reference/v0.3-rc1/client/private.mjs` | exit 0 |
| 485 | `git hash-object -- reference/v0.3-rc1/client/private.mjs` | exit 0 |
| 486 | `git rev-parse origin/main:reference/v0.3-rc1/client/setup-zk.mjs` | exit 0 |
| 487 | `git hash-object -- reference/v0.3-rc1/client/setup-zk.mjs` | exit 0 |
| 488 | `git rev-parse origin/main:reference/v0.3-rc1/client/types.mjs` | exit 0 |
| 489 | `git hash-object -- reference/v0.3-rc1/client/types.mjs` | exit 0 |
| 490 | `git rev-parse origin/main:reference/v0.3-rc1/client/verify_canonical.ts` | exit 0 |
| 491 | `git hash-object -- reference/v0.3-rc1/client/verify_canonical.ts` | exit 0 |
| 492 | `git rev-parse origin/main:reference/v0.3-rc1/client/zk-policy.mjs` | exit 0 |
| 493 | `git hash-object -- reference/v0.3-rc1/client/zk-policy.mjs` | exit 0 |
| 494 | `git rev-parse origin/main:reference/v0.3-rc1/client/zk-regression.mjs` | exit 0 |
| 495 | `git hash-object -- reference/v0.3-rc1/client/zk-regression.mjs` | exit 0 |
| 496 | `git rev-parse origin/main:reference/v0.3-rc1/client/zk-test-utils.mjs` | exit 0 |
| 497 | `git hash-object -- reference/v0.3-rc1/client/zk-test-utils.mjs` | exit 0 |
| 498 | `git rev-parse origin/main:reference/v0.3-rc1/commerce.py` | exit 0 |
| 499 | `git hash-object -- reference/v0.3-rc1/commerce.py` | exit 0 |
| 500 | `git rev-parse origin/main:reference/v0.3-rc1/commerce_driver.py` | exit 0 |
| 501 | `git hash-object -- reference/v0.3-rc1/commerce_driver.py` | exit 0 |
| 502 | `git rev-parse origin/main:reference/v0.3-rc1/common.py` | exit 0 |
| 503 | `git hash-object -- reference/v0.3-rc1/common.py` | exit 0 |
| 504 | `git rev-parse origin/main:reference/v0.3-rc1/contracts.py` | exit 0 |
| 505 | `git hash-object -- reference/v0.3-rc1/contracts.py` | exit 0 |
| 506 | `git rev-parse origin/main:reference/v0.3-rc1/core.py` | exit 0 |
| 507 | `git hash-object -- reference/v0.3-rc1/core.py` | exit 0 |
| 508 | `git rev-parse origin/main:reference/v0.3-rc1/dispatch.py` | exit 0 |
| 509 | `git hash-object -- reference/v0.3-rc1/dispatch.py` | exit 0 |
| 510 | `git rev-parse origin/main:reference/v0.3-rc1/execution_contracts.py` | exit 0 |
| 511 | `git hash-object -- reference/v0.3-rc1/execution_contracts.py` | exit 0 |
| 512 | `git rev-parse origin/main:reference/v0.3-rc1/finance.py` | exit 0 |
| 513 | `git hash-object -- reference/v0.3-rc1/finance.py` | exit 0 |
| 514 | `git rev-parse origin/main:reference/v0.3-rc1/fixtures/canonical_encoding_v1.json` | exit 0 |
| 515 | `git hash-object -- reference/v0.3-rc1/fixtures/canonical_encoding_v1.json` | exit 0 |
| 516 | `git rev-parse origin/main:reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json` | exit 0 |
| 517 | `git hash-object -- reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json` | exit 0 |
| 518 | `git rev-parse origin/main:reference/v0.3-rc1/lifecycle.py` | exit 0 |
| 519 | `git hash-object -- reference/v0.3-rc1/lifecycle.py` | exit 0 |
| 520 | `git rev-parse origin/main:reference/v0.3-rc1/mock_provider.py` | exit 0 |
| 521 | `git hash-object -- reference/v0.3-rc1/mock_provider.py` | exit 0 |
| 522 | `git rev-parse origin/main:reference/v0.3-rc1/mutation_check.py` | exit 0 |
| 523 | `git hash-object -- reference/v0.3-rc1/mutation_check.py` | exit 0 |
| 524 | `git rev-parse origin/main:reference/v0.3-rc1/observations.py` | exit 0 |
| 525 | `git hash-object -- reference/v0.3-rc1/observations.py` | exit 0 |
| 526 | `git rev-parse origin/main:reference/v0.3-rc1/paid_archive.py` | exit 0 |
| 527 | `git hash-object -- reference/v0.3-rc1/paid_archive.py` | exit 0 |
| 528 | `git rev-parse origin/main:reference/v0.3-rc1/paid_driver.py` | exit 0 |
| 529 | `git hash-object -- reference/v0.3-rc1/paid_driver.py` | exit 0 |
| 530 | `git rev-parse origin/main:reference/v0.3-rc1/paid_integration.py` | exit 0 |
| 531 | `git hash-object -- reference/v0.3-rc1/paid_integration.py` | exit 0 |
| 532 | `git rev-parse origin/main:reference/v0.3-rc1/paid_recovery.py` | exit 0 |
| 533 | `git hash-object -- reference/v0.3-rc1/paid_recovery.py` | exit 0 |
| 534 | `git rev-parse origin/main:reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 535 | `git hash-object -- reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 536 | `git rev-parse origin/main:reference/v0.3-rc1/requirements.txt` | exit 0 |
| 537 | `git hash-object -- reference/v0.3-rc1/requirements.txt` | exit 0 |
| 538 | `git rev-parse origin/main:reference/v0.3-rc1/results/acceptance_trace.json` | exit 0 |
| 539 | `git hash-object -- reference/v0.3-rc1/results/acceptance_trace.json` | exit 0 |
| 540 | `git rev-parse origin/main:reference/v0.3-rc1/results/client_offline_tests.txt` | exit 0 |
| 541 | `git hash-object -- reference/v0.3-rc1/results/client_offline_tests.txt` | exit 0 |
| 542 | `git rev-parse origin/main:reference/v0.3-rc1/results/client_syntax.json` | exit 0 |
| 543 | `git hash-object -- reference/v0.3-rc1/results/client_syntax.json` | exit 0 |
| 544 | `git rev-parse origin/main:reference/v0.3-rc1/results/manifest.sha256.json` | exit 0 |
| 545 | `git hash-object -- reference/v0.3-rc1/results/manifest.sha256.json` | exit 0 |
| 546 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M01.txt` | exit 0 |
| 547 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M01.txt` | exit 0 |
| 548 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M02.txt` | exit 0 |
| 549 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M02.txt` | exit 0 |
| 550 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M03.txt` | exit 0 |
| 551 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M03.txt` | exit 0 |
| 552 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M04.txt` | exit 0 |
| 553 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M04.txt` | exit 0 |
| 554 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M05.txt` | exit 0 |
| 555 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M05.txt` | exit 0 |
| 556 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M06.txt` | exit 0 |
| 557 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M06.txt` | exit 0 |
| 558 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M07.txt` | exit 0 |
| 559 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M07.txt` | exit 0 |
| 560 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M08.txt` | exit 0 |
| 561 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M08.txt` | exit 0 |
| 562 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M09.txt` | exit 0 |
| 563 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M09.txt` | exit 0 |
| 564 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M10.txt` | exit 0 |
| 565 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M10.txt` | exit 0 |
| 566 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M11.txt` | exit 0 |
| 567 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M11.txt` | exit 0 |
| 568 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M12.txt` | exit 0 |
| 569 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M12.txt` | exit 0 |
| 570 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M13.txt` | exit 0 |
| 571 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M13.txt` | exit 0 |
| 572 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M14.txt` | exit 0 |
| 573 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M14.txt` | exit 0 |
| 574 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_results.json` | exit 0 |
| 575 | `git hash-object -- reference/v0.3-rc1/results/mutation_results.json` | exit 0 |
| 576 | `git rev-parse origin/main:reference/v0.3-rc1/results/preflight.json` | exit 0 |
| 577 | `git hash-object -- reference/v0.3-rc1/results/preflight.json` | exit 0 |
| 578 | `git rev-parse origin/main:reference/v0.3-rc1/results/reproducibility.json` | exit 0 |
| 579 | `git hash-object -- reference/v0.3-rc1/results/reproducibility.json` | exit 0 |
| 580 | `git rev-parse origin/main:reference/v0.3-rc1/results/review_trace_v03.json` | exit 0 |
| 581 | `git hash-object -- reference/v0.3-rc1/results/review_trace_v03.json` | exit 0 |
| 582 | `git rev-parse origin/main:reference/v0.3-rc1/results/tests.txt` | exit 0 |
| 583 | `git hash-object -- reference/v0.3-rc1/results/tests.txt` | exit 0 |
| 584 | `git rev-parse origin/main:reference/v0.3-rc1/results/v02_unchanged.json` | exit 0 |
| 585 | `git hash-object -- reference/v0.3-rc1/results/v02_unchanged.json` | exit 0 |
| 586 | `git rev-parse origin/main:reference/v0.3-rc1/results/verification.json` | exit 0 |
| 587 | `git hash-object -- reference/v0.3-rc1/results/verification.json` | exit 0 |
| 588 | `git rev-parse origin/main:reference/v0.3-rc1/review_provenance/baseline_integrity.json` | exit 0 |
| 589 | `git hash-object -- reference/v0.3-rc1/review_provenance/baseline_integrity.json` | exit 0 |
| 590 | `git rev-parse origin/main:reference/v0.3-rc1/review_provenance/baseline_reproduced.json` | exit 0 |
| 591 | `git hash-object -- reference/v0.3-rc1/review_provenance/baseline_reproduced.json` | exit 0 |
| 592 | `git rev-parse origin/main:reference/v0.3-rc1/review_provenance/review_v02_probe.py` | exit 0 |
| 593 | `git hash-object -- reference/v0.3-rc1/review_provenance/review_v02_probe.py` | exit 0 |
| 594 | `git rev-parse origin/main:reference/v0.3-rc1/review_provenance/review_verification.json` | exit 0 |
| 595 | `git hash-object -- reference/v0.3-rc1/review_provenance/review_verification.json` | exit 0 |
| 596 | `git rev-parse origin/main:reference/v0.3-rc1/review_trace_v03.py` | exit 0 |
| 597 | `git hash-object -- reference/v0.3-rc1/review_trace_v03.py` | exit 0 |
| 598 | `git rev-parse origin/main:reference/v0.3-rc1/scripts/preflight.py` | exit 0 |
| 599 | `git hash-object -- reference/v0.3-rc1/scripts/preflight.py` | exit 0 |
| 600 | `git rev-parse origin/main:reference/v0.3-rc1/scripts/verify_package.py` | exit 0 |
| 601 | `git hash-object -- reference/v0.3-rc1/scripts/verify_package.py` | exit 0 |
| 602 | `git rev-parse origin/main:reference/v0.3-rc1/source_inventory.json` | exit 0 |
| 603 | `git hash-object -- reference/v0.3-rc1/source_inventory.json` | exit 0 |
| 604 | `git rev-parse origin/main:reference/v0.3-rc1/storage_receipt.py` | exit 0 |
| 605 | `git hash-object -- reference/v0.3-rc1/storage_receipt.py` | exit 0 |
| 606 | `git rev-parse origin/main:reference/v0.3-rc1/sui/Move.lock` | exit 0 |
| 607 | `git hash-object -- reference/v0.3-rc1/sui/Move.lock` | exit 0 |
| 608 | `git rev-parse origin/main:reference/v0.3-rc1/sui/Move.toml` | exit 0 |
| 609 | `git hash-object -- reference/v0.3-rc1/sui/Move.toml` | exit 0 |
| 610 | `git rev-parse origin/main:reference/v0.3-rc1/sui/sources/rights.move` | exit 0 |
| 611 | `git hash-object -- reference/v0.3-rc1/sui/sources/rights.move` | exit 0 |
| 612 | `git rev-parse origin/main:reference/v0.3-rc1/sui/sources/zk_gate.move` | exit 0 |
| 613 | `git hash-object -- reference/v0.3-rc1/sui/sources/zk_gate.move` | exit 0 |
| 614 | `git rev-parse origin/main:reference/v0.3-rc1/sui/tests/rights_tests.move` | exit 0 |
| 615 | `git hash-object -- reference/v0.3-rc1/sui/tests/rights_tests.move` | exit 0 |
| 616 | `git rev-parse origin/main:reference/v0.3-rc1/test_assets.py` | exit 0 |
| 617 | `git hash-object -- reference/v0.3-rc1/test_assets.py` | exit 0 |
| 618 | `git rev-parse origin/main:reference/v0.3-rc1/test_canonical_encoding.py` | exit 0 |
| 619 | `git hash-object -- reference/v0.3-rc1/test_canonical_encoding.py` | exit 0 |
| 620 | `git rev-parse origin/main:reference/v0.3-rc1/test_commerce.py` | exit 0 |
| 621 | `git hash-object -- reference/v0.3-rc1/test_commerce.py` | exit 0 |
| 622 | `git rev-parse origin/main:reference/v0.3-rc1/test_commerce_driver.py` | exit 0 |
| 623 | `git hash-object -- reference/v0.3-rc1/test_commerce_driver.py` | exit 0 |
| 624 | `git rev-parse origin/main:reference/v0.3-rc1/test_core.py` | exit 0 |
| 625 | `git hash-object -- reference/v0.3-rc1/test_core.py` | exit 0 |
| 626 | `git rev-parse origin/main:reference/v0.3-rc1/test_execution_contracts.py` | exit 0 |
| 627 | `git hash-object -- reference/v0.3-rc1/test_execution_contracts.py` | exit 0 |
| 628 | `git rev-parse origin/main:reference/v0.3-rc1/test_paid_archive.py` | exit 0 |
| 629 | `git hash-object -- reference/v0.3-rc1/test_paid_archive.py` | exit 0 |
| 630 | `git rev-parse origin/main:reference/v0.3-rc1/test_paid_integration.py` | exit 0 |
| 631 | `git hash-object -- reference/v0.3-rc1/test_paid_integration.py` | exit 0 |
| 632 | `git rev-parse origin/main:reference/v0.3-rc1/test_paid_recovery.py` | exit 0 |
| 633 | `git hash-object -- reference/v0.3-rc1/test_paid_recovery.py` | exit 0 |
| 634 | `git rev-parse origin/main:reference/v0.3-rc1/test_storage_receipt.py` | exit 0 |
| 635 | `git hash-object -- reference/v0.3-rc1/test_storage_receipt.py` | exit 0 |
| 636 | `git rev-parse origin/main:reference/v0.3-rc1/test_v02.py` | exit 0 |
| 637 | `git hash-object -- reference/v0.3-rc1/test_v02.py` | exit 0 |
| 638 | `git rev-parse origin/main:reference/v0.3-rc1/test_v03.py` | exit 0 |
| 639 | `git hash-object -- reference/v0.3-rc1/test_v03.py` | exit 0 |
| 640 | `git rev-parse origin/main:reference/v0.3-rc1/vendor/rights_model.py` | exit 0 |
| 641 | `git hash-object -- reference/v0.3-rc1/vendor/rights_model.py` | exit 0 |
| 642 | `git rev-parse origin/main:reference/v0.3-rc1/vendor/tix_reconcile.py` | exit 0 |
| 643 | `git hash-object -- reference/v0.3-rc1/vendor/tix_reconcile.py` | exit 0 |
| 644 | `git rev-parse origin/main:reference/v0.3-rc1/verify.py` | exit 0 |
| 645 | `git hash-object -- reference/v0.3-rc1/verify.py` | exit 0 |
| 646 | `git rev-parse origin/main:reference/v0.3-rc1/zk/artifacts/README.md` | exit 0 |
| 647 | `git hash-object -- reference/v0.3-rc1/zk/artifacts/README.md` | exit 0 |
| 648 | `git rev-parse origin/main:reference/v0.3-rc1/zk/circuits/common.circom` | exit 0 |
| 649 | `git hash-object -- reference/v0.3-rc1/zk/circuits/common.circom` | exit 0 |
| 650 | `git rev-parse origin/main:reference/v0.3-rc1/zk/circuits/mint.circom` | exit 0 |
| 651 | `git hash-object -- reference/v0.3-rc1/zk/circuits/mint.circom` | exit 0 |
| 652 | `git rev-parse origin/main:reference/v0.3-rc1/zk/circuits/spend.circom` | exit 0 |
| 653 | `git hash-object -- reference/v0.3-rc1/zk/circuits/spend.circom` | exit 0 |
| 654 | `git ls-files --others --exclude-standard reference/v0.3-rc1/ .aiops/` | exit 0 |
| 655 | `git diff --name-only origin/main -- runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs reference/v0.3-rc1/ .aiops/ docs/tasks/` | exit 0 |
| 656 | `env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-mn4p61ce/index git read-tree HEAD` | exit 0 |
| 657 | `env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-mn4p61ce/index git add --intent-to-add -- docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md` | exit 128 |
| 658 | `git grep -n -E '(^&#124;[^0-9a-f])[0-9a-f]{40}([^0-9a-f]&#124;$)' HEAD -- '*.rs' '*.py' '*.md'` | exit 0 |
| 659 | `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 660 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 661 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 662 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/support/model_v4.rs` | exit 0 |
| 663 | `git rev-parse HEAD:reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 664 | `git rev-parse HEAD:docs/adr/0001-ktx-authority-commit-recovery.md` | exit 0 |
| 665 | `git rev-parse HEAD:docs/contracts/STATE_LIFECYCLE.md` | exit 0 |
| 666 | `git rev-parse HEAD:runtime/crates/kix-kernel/README.md` | exit 0 |
| 667 | `git show -s --format=%P 035d5705c93b318a49941ce5f7410f843360c427` | exit 0 |
| 668 | `git show -s --format=%P eb1caf8285c174697d78834246a304ffe9006427` | exit 0 |
| 669 | `git show -s --format=%P 876f41067bc7eb70bcd6ebd9c744c11b46f046b6` | exit 0 |
| 670 | `git show -s --format=%P d016caee4ae40f28f531809359ee77ac22db0073` | exit 0 |
| 671 | `git show -s --format=%P 70b976c0b8db686b1d21ff0831c275abf77a3d0a` | exit 0 |
| 672 | `git show -s --format=%P 9d50fb660248b66a5959f48f7dc96e68c9d5530b` | exit 0 |
| 673 | `git show -s --format=%P 9ed15a7adc93359e99bb5c3512a3ca20c77cb264` | exit 0 |
| 674 | `git show -s --format=%P 8e4813e868961adbabb7d1ee450a346f8fb6add1` | exit 0 |
| 675 | `git diff --name-only origin/main` | exit 0 |
| 676 | `git ls-files --others --exclude-standard` | exit 0 |
| 677 | `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 678 | `git hash-object -- runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 679 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 680 | `git hash-object -- runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 681 | `git ls-files -z reference/v0.3-rc1/ .aiops/` | exit 0 |
| 682 | `git rev-parse origin/main:.aiops/program.json` | exit 0 |
| 683 | `git hash-object -- .aiops/program.json` | exit 0 |
| 684 | `git rev-parse origin/main:reference/v0.3-rc1/DESIGN_SUI_ZK.md` | exit 0 |
| 685 | `git hash-object -- reference/v0.3-rc1/DESIGN_SUI_ZK.md` | exit 0 |
| 686 | `git rev-parse 'origin/main:reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md'` | exit 0 |
| 687 | `git hash-object -- 'reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md'` | exit 0 |
| 688 | `git rev-parse origin/main:reference/v0.3-rc1/README.md` | exit 0 |
| 689 | `git hash-object -- reference/v0.3-rc1/README.md` | exit 0 |
| 690 | `git rev-parse origin/main:reference/v0.3-rc1/adapters.py` | exit 0 |
| 691 | `git hash-object -- reference/v0.3-rc1/adapters.py` | exit 0 |
| 692 | `git rev-parse origin/main:reference/v0.3-rc1/archive_driver.py` | exit 0 |
| 693 | `git hash-object -- reference/v0.3-rc1/archive_driver.py` | exit 0 |
| 694 | `git rev-parse origin/main:reference/v0.3-rc1/assets.py` | exit 0 |
| 695 | `git hash-object -- reference/v0.3-rc1/assets.py` | exit 0 |
| 696 | `git rev-parse origin/main:reference/v0.3-rc1/canonical_encoding.py` | exit 0 |
| 697 | `git hash-object -- reference/v0.3-rc1/canonical_encoding.py` | exit 0 |
| 698 | `git rev-parse origin/main:reference/v0.3-rc1/changes_from_v02.diff` | exit 0 |
| 699 | `git hash-object -- reference/v0.3-rc1/changes_from_v02.diff` | exit 0 |
| 700 | `git rev-parse origin/main:reference/v0.3-rc1/check_reproducibility.py` | exit 0 |
| 701 | `git hash-object -- reference/v0.3-rc1/check_reproducibility.py` | exit 0 |
| 702 | `git rev-parse origin/main:reference/v0.3-rc1/client/archive-fixture.mjs` | exit 0 |
| 703 | `git hash-object -- reference/v0.3-rc1/client/archive-fixture.mjs` | exit 0 |
| 704 | `git rev-parse origin/main:reference/v0.3-rc1/client/backup.mjs` | exit 0 |
| 705 | `git hash-object -- reference/v0.3-rc1/client/backup.mjs` | exit 0 |
| 706 | `git rev-parse origin/main:reference/v0.3-rc1/client/canonical_encoding.ts` | exit 0 |
| 707 | `git hash-object -- reference/v0.3-rc1/client/canonical_encoding.ts` | exit 0 |
| 708 | `git rev-parse origin/main:reference/v0.3-rc1/client/commerce_v2.ts` | exit 0 |
| 709 | `git hash-object -- reference/v0.3-rc1/client/commerce_v2.ts` | exit 0 |
| 710 | `git rev-parse origin/main:reference/v0.3-rc1/client/compile-circuits.mjs` | exit 0 |
| 711 | `git hash-object -- reference/v0.3-rc1/client/compile-circuits.mjs` | exit 0 |
| 712 | `git rev-parse origin/main:reference/v0.3-rc1/client/encoding.mjs` | exit 0 |
| 713 | `git hash-object -- reference/v0.3-rc1/client/encoding.mjs` | exit 0 |
| 714 | `git rev-parse origin/main:reference/v0.3-rc1/client/independent.mjs` | exit 0 |
| 715 | `git hash-object -- reference/v0.3-rc1/client/independent.mjs` | exit 0 |
| 716 | `git rev-parse origin/main:reference/v0.3-rc1/client/localnet-boundaries.mjs` | exit 0 |
| 717 | `git hash-object -- reference/v0.3-rc1/client/localnet-boundaries.mjs` | exit 0 |
| 718 | `git rev-parse origin/main:reference/v0.3-rc1/client/localnet-paid.mjs` | exit 0 |
| 719 | `git hash-object -- reference/v0.3-rc1/client/localnet-paid.mjs` | exit 0 |
| 720 | `git rev-parse origin/main:reference/v0.3-rc1/client/localnet.mjs` | exit 0 |
| 721 | `git hash-object -- reference/v0.3-rc1/client/localnet.mjs` | exit 0 |
| 722 | `git rev-parse origin/main:reference/v0.3-rc1/client/offline.test.mjs` | exit 0 |
| 723 | `git hash-object -- reference/v0.3-rc1/client/offline.test.mjs` | exit 0 |
| 724 | `git rev-parse origin/main:reference/v0.3-rc1/client/package-lock.json` | exit 0 |
| 725 | `git hash-object -- reference/v0.3-rc1/client/package-lock.json` | exit 0 |
| 726 | `git rev-parse origin/main:reference/v0.3-rc1/client/package.json` | exit 0 |
| 727 | `git hash-object -- reference/v0.3-rc1/client/package.json` | exit 0 |
| 728 | `git rev-parse origin/main:reference/v0.3-rc1/client/paid-chain.mjs` | exit 0 |
| 729 | `git hash-object -- reference/v0.3-rc1/client/paid-chain.mjs` | exit 0 |
| 730 | `git rev-parse origin/main:reference/v0.3-rc1/client/private.mjs` | exit 0 |
| 731 | `git hash-object -- reference/v0.3-rc1/client/private.mjs` | exit 0 |
| 732 | `git rev-parse origin/main:reference/v0.3-rc1/client/setup-zk.mjs` | exit 0 |
| 733 | `git hash-object -- reference/v0.3-rc1/client/setup-zk.mjs` | exit 0 |
| 734 | `git rev-parse origin/main:reference/v0.3-rc1/client/types.mjs` | exit 0 |
| 735 | `git hash-object -- reference/v0.3-rc1/client/types.mjs` | exit 0 |
| 736 | `git rev-parse origin/main:reference/v0.3-rc1/client/verify_canonical.ts` | exit 0 |
| 737 | `git hash-object -- reference/v0.3-rc1/client/verify_canonical.ts` | exit 0 |
| 738 | `git rev-parse origin/main:reference/v0.3-rc1/client/zk-policy.mjs` | exit 0 |
| 739 | `git hash-object -- reference/v0.3-rc1/client/zk-policy.mjs` | exit 0 |
| 740 | `git rev-parse origin/main:reference/v0.3-rc1/client/zk-regression.mjs` | exit 0 |
| 741 | `git hash-object -- reference/v0.3-rc1/client/zk-regression.mjs` | exit 0 |
| 742 | `git rev-parse origin/main:reference/v0.3-rc1/client/zk-test-utils.mjs` | exit 0 |
| 743 | `git hash-object -- reference/v0.3-rc1/client/zk-test-utils.mjs` | exit 0 |
| 744 | `git rev-parse origin/main:reference/v0.3-rc1/commerce.py` | exit 0 |
| 745 | `git hash-object -- reference/v0.3-rc1/commerce.py` | exit 0 |
| 746 | `git rev-parse origin/main:reference/v0.3-rc1/commerce_driver.py` | exit 0 |
| 747 | `git hash-object -- reference/v0.3-rc1/commerce_driver.py` | exit 0 |
| 748 | `git rev-parse origin/main:reference/v0.3-rc1/common.py` | exit 0 |
| 749 | `git hash-object -- reference/v0.3-rc1/common.py` | exit 0 |
| 750 | `git rev-parse origin/main:reference/v0.3-rc1/contracts.py` | exit 0 |
| 751 | `git hash-object -- reference/v0.3-rc1/contracts.py` | exit 0 |
| 752 | `git rev-parse origin/main:reference/v0.3-rc1/core.py` | exit 0 |
| 753 | `git hash-object -- reference/v0.3-rc1/core.py` | exit 0 |
| 754 | `git rev-parse origin/main:reference/v0.3-rc1/dispatch.py` | exit 0 |
| 755 | `git hash-object -- reference/v0.3-rc1/dispatch.py` | exit 0 |
| 756 | `git rev-parse origin/main:reference/v0.3-rc1/execution_contracts.py` | exit 0 |
| 757 | `git hash-object -- reference/v0.3-rc1/execution_contracts.py` | exit 0 |
| 758 | `git rev-parse origin/main:reference/v0.3-rc1/finance.py` | exit 0 |
| 759 | `git hash-object -- reference/v0.3-rc1/finance.py` | exit 0 |
| 760 | `git rev-parse origin/main:reference/v0.3-rc1/fixtures/canonical_encoding_v1.json` | exit 0 |
| 761 | `git hash-object -- reference/v0.3-rc1/fixtures/canonical_encoding_v1.json` | exit 0 |
| 762 | `git rev-parse origin/main:reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json` | exit 0 |
| 763 | `git hash-object -- reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json` | exit 0 |
| 764 | `git rev-parse origin/main:reference/v0.3-rc1/lifecycle.py` | exit 0 |
| 765 | `git hash-object -- reference/v0.3-rc1/lifecycle.py` | exit 0 |
| 766 | `git rev-parse origin/main:reference/v0.3-rc1/mock_provider.py` | exit 0 |
| 767 | `git hash-object -- reference/v0.3-rc1/mock_provider.py` | exit 0 |
| 768 | `git rev-parse origin/main:reference/v0.3-rc1/mutation_check.py` | exit 0 |
| 769 | `git hash-object -- reference/v0.3-rc1/mutation_check.py` | exit 0 |
| 770 | `git rev-parse origin/main:reference/v0.3-rc1/observations.py` | exit 0 |
| 771 | `git hash-object -- reference/v0.3-rc1/observations.py` | exit 0 |
| 772 | `git rev-parse origin/main:reference/v0.3-rc1/paid_archive.py` | exit 0 |
| 773 | `git hash-object -- reference/v0.3-rc1/paid_archive.py` | exit 0 |
| 774 | `git rev-parse origin/main:reference/v0.3-rc1/paid_driver.py` | exit 0 |
| 775 | `git hash-object -- reference/v0.3-rc1/paid_driver.py` | exit 0 |
| 776 | `git rev-parse origin/main:reference/v0.3-rc1/paid_integration.py` | exit 0 |
| 777 | `git hash-object -- reference/v0.3-rc1/paid_integration.py` | exit 0 |
| 778 | `git rev-parse origin/main:reference/v0.3-rc1/paid_recovery.py` | exit 0 |
| 779 | `git hash-object -- reference/v0.3-rc1/paid_recovery.py` | exit 0 |
| 780 | `git rev-parse origin/main:reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 781 | `git hash-object -- reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 782 | `git rev-parse origin/main:reference/v0.3-rc1/requirements.txt` | exit 0 |
| 783 | `git hash-object -- reference/v0.3-rc1/requirements.txt` | exit 0 |
| 784 | `git rev-parse origin/main:reference/v0.3-rc1/results/acceptance_trace.json` | exit 0 |
| 785 | `git hash-object -- reference/v0.3-rc1/results/acceptance_trace.json` | exit 0 |
| 786 | `git rev-parse origin/main:reference/v0.3-rc1/results/client_offline_tests.txt` | exit 0 |
| 787 | `git hash-object -- reference/v0.3-rc1/results/client_offline_tests.txt` | exit 0 |
| 788 | `git rev-parse origin/main:reference/v0.3-rc1/results/client_syntax.json` | exit 0 |
| 789 | `git hash-object -- reference/v0.3-rc1/results/client_syntax.json` | exit 0 |
| 790 | `git rev-parse origin/main:reference/v0.3-rc1/results/manifest.sha256.json` | exit 0 |
| 791 | `git hash-object -- reference/v0.3-rc1/results/manifest.sha256.json` | exit 0 |
| 792 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M01.txt` | exit 0 |
| 793 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M01.txt` | exit 0 |
| 794 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M02.txt` | exit 0 |
| 795 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M02.txt` | exit 0 |
| 796 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M03.txt` | exit 0 |
| 797 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M03.txt` | exit 0 |
| 798 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M04.txt` | exit 0 |
| 799 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M04.txt` | exit 0 |
| 800 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M05.txt` | exit 0 |
| 801 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M05.txt` | exit 0 |
| 802 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M06.txt` | exit 0 |
| 803 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M06.txt` | exit 0 |
| 804 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M07.txt` | exit 0 |
| 805 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M07.txt` | exit 0 |
| 806 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M08.txt` | exit 0 |
| 807 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M08.txt` | exit 0 |
| 808 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M09.txt` | exit 0 |
| 809 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M09.txt` | exit 0 |
| 810 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M10.txt` | exit 0 |
| 811 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M10.txt` | exit 0 |
| 812 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M11.txt` | exit 0 |
| 813 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M11.txt` | exit 0 |
| 814 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M12.txt` | exit 0 |
| 815 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M12.txt` | exit 0 |
| 816 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M13.txt` | exit 0 |
| 817 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M13.txt` | exit 0 |
| 818 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M14.txt` | exit 0 |
| 819 | `git hash-object -- reference/v0.3-rc1/results/mutation_logs/M14.txt` | exit 0 |
| 820 | `git rev-parse origin/main:reference/v0.3-rc1/results/mutation_results.json` | exit 0 |
| 821 | `git hash-object -- reference/v0.3-rc1/results/mutation_results.json` | exit 0 |
| 822 | `git rev-parse origin/main:reference/v0.3-rc1/results/preflight.json` | exit 0 |
| 823 | `git hash-object -- reference/v0.3-rc1/results/preflight.json` | exit 0 |
| 824 | `git rev-parse origin/main:reference/v0.3-rc1/results/reproducibility.json` | exit 0 |
| 825 | `git hash-object -- reference/v0.3-rc1/results/reproducibility.json` | exit 0 |
| 826 | `git rev-parse origin/main:reference/v0.3-rc1/results/review_trace_v03.json` | exit 0 |
| 827 | `git hash-object -- reference/v0.3-rc1/results/review_trace_v03.json` | exit 0 |
| 828 | `git rev-parse origin/main:reference/v0.3-rc1/results/tests.txt` | exit 0 |
| 829 | `git hash-object -- reference/v0.3-rc1/results/tests.txt` | exit 0 |
| 830 | `git rev-parse origin/main:reference/v0.3-rc1/results/v02_unchanged.json` | exit 0 |
| 831 | `git hash-object -- reference/v0.3-rc1/results/v02_unchanged.json` | exit 0 |
| 832 | `git rev-parse origin/main:reference/v0.3-rc1/results/verification.json` | exit 0 |
| 833 | `git hash-object -- reference/v0.3-rc1/results/verification.json` | exit 0 |
| 834 | `git rev-parse origin/main:reference/v0.3-rc1/review_provenance/baseline_integrity.json` | exit 0 |
| 835 | `git hash-object -- reference/v0.3-rc1/review_provenance/baseline_integrity.json` | exit 0 |
| 836 | `git rev-parse origin/main:reference/v0.3-rc1/review_provenance/baseline_reproduced.json` | exit 0 |
| 837 | `git hash-object -- reference/v0.3-rc1/review_provenance/baseline_reproduced.json` | exit 0 |
| 838 | `git rev-parse origin/main:reference/v0.3-rc1/review_provenance/review_v02_probe.py` | exit 0 |
| 839 | `git hash-object -- reference/v0.3-rc1/review_provenance/review_v02_probe.py` | exit 0 |
| 840 | `git rev-parse origin/main:reference/v0.3-rc1/review_provenance/review_verification.json` | exit 0 |
| 841 | `git hash-object -- reference/v0.3-rc1/review_provenance/review_verification.json` | exit 0 |
| 842 | `git rev-parse origin/main:reference/v0.3-rc1/review_trace_v03.py` | exit 0 |
| 843 | `git hash-object -- reference/v0.3-rc1/review_trace_v03.py` | exit 0 |
| 844 | `git rev-parse origin/main:reference/v0.3-rc1/scripts/preflight.py` | exit 0 |
| 845 | `git hash-object -- reference/v0.3-rc1/scripts/preflight.py` | exit 0 |
| 846 | `git rev-parse origin/main:reference/v0.3-rc1/scripts/verify_package.py` | exit 0 |
| 847 | `git hash-object -- reference/v0.3-rc1/scripts/verify_package.py` | exit 0 |
| 848 | `git rev-parse origin/main:reference/v0.3-rc1/source_inventory.json` | exit 0 |
| 849 | `git hash-object -- reference/v0.3-rc1/source_inventory.json` | exit 0 |
| 850 | `git rev-parse origin/main:reference/v0.3-rc1/storage_receipt.py` | exit 0 |
| 851 | `git hash-object -- reference/v0.3-rc1/storage_receipt.py` | exit 0 |
| 852 | `git rev-parse origin/main:reference/v0.3-rc1/sui/Move.lock` | exit 0 |
| 853 | `git hash-object -- reference/v0.3-rc1/sui/Move.lock` | exit 0 |
| 854 | `git rev-parse origin/main:reference/v0.3-rc1/sui/Move.toml` | exit 0 |
| 855 | `git hash-object -- reference/v0.3-rc1/sui/Move.toml` | exit 0 |
| 856 | `git rev-parse origin/main:reference/v0.3-rc1/sui/sources/rights.move` | exit 0 |
| 857 | `git hash-object -- reference/v0.3-rc1/sui/sources/rights.move` | exit 0 |
| 858 | `git rev-parse origin/main:reference/v0.3-rc1/sui/sources/zk_gate.move` | exit 0 |
| 859 | `git hash-object -- reference/v0.3-rc1/sui/sources/zk_gate.move` | exit 0 |
| 860 | `git rev-parse origin/main:reference/v0.3-rc1/sui/tests/rights_tests.move` | exit 0 |
| 861 | `git hash-object -- reference/v0.3-rc1/sui/tests/rights_tests.move` | exit 0 |
| 862 | `git rev-parse origin/main:reference/v0.3-rc1/test_assets.py` | exit 0 |
| 863 | `git hash-object -- reference/v0.3-rc1/test_assets.py` | exit 0 |
| 864 | `git rev-parse origin/main:reference/v0.3-rc1/test_canonical_encoding.py` | exit 0 |
| 865 | `git hash-object -- reference/v0.3-rc1/test_canonical_encoding.py` | exit 0 |
| 866 | `git rev-parse origin/main:reference/v0.3-rc1/test_commerce.py` | exit 0 |
| 867 | `git hash-object -- reference/v0.3-rc1/test_commerce.py` | exit 0 |
| 868 | `git rev-parse origin/main:reference/v0.3-rc1/test_commerce_driver.py` | exit 0 |
| 869 | `git hash-object -- reference/v0.3-rc1/test_commerce_driver.py` | exit 0 |
| 870 | `git rev-parse origin/main:reference/v0.3-rc1/test_core.py` | exit 0 |
| 871 | `git hash-object -- reference/v0.3-rc1/test_core.py` | exit 0 |
| 872 | `git rev-parse origin/main:reference/v0.3-rc1/test_execution_contracts.py` | exit 0 |
| 873 | `git hash-object -- reference/v0.3-rc1/test_execution_contracts.py` | exit 0 |
| 874 | `git rev-parse origin/main:reference/v0.3-rc1/test_paid_archive.py` | exit 0 |
| 875 | `git hash-object -- reference/v0.3-rc1/test_paid_archive.py` | exit 0 |
| 876 | `git rev-parse origin/main:reference/v0.3-rc1/test_paid_integration.py` | exit 0 |
| 877 | `git hash-object -- reference/v0.3-rc1/test_paid_integration.py` | exit 0 |
| 878 | `git rev-parse origin/main:reference/v0.3-rc1/test_paid_recovery.py` | exit 0 |
| 879 | `git hash-object -- reference/v0.3-rc1/test_paid_recovery.py` | exit 0 |
| 880 | `git rev-parse origin/main:reference/v0.3-rc1/test_storage_receipt.py` | exit 0 |
| 881 | `git hash-object -- reference/v0.3-rc1/test_storage_receipt.py` | exit 0 |
| 882 | `git rev-parse origin/main:reference/v0.3-rc1/test_v02.py` | exit 0 |
| 883 | `git hash-object -- reference/v0.3-rc1/test_v02.py` | exit 0 |
| 884 | `git rev-parse origin/main:reference/v0.3-rc1/test_v03.py` | exit 0 |
| 885 | `git hash-object -- reference/v0.3-rc1/test_v03.py` | exit 0 |
| 886 | `git rev-parse origin/main:reference/v0.3-rc1/vendor/rights_model.py` | exit 0 |
| 887 | `git hash-object -- reference/v0.3-rc1/vendor/rights_model.py` | exit 0 |
| 888 | `git rev-parse origin/main:reference/v0.3-rc1/vendor/tix_reconcile.py` | exit 0 |
| 889 | `git hash-object -- reference/v0.3-rc1/vendor/tix_reconcile.py` | exit 0 |
| 890 | `git rev-parse origin/main:reference/v0.3-rc1/verify.py` | exit 0 |
| 891 | `git hash-object -- reference/v0.3-rc1/verify.py` | exit 0 |
| 892 | `git rev-parse origin/main:reference/v0.3-rc1/zk/artifacts/README.md` | exit 0 |
| 893 | `git hash-object -- reference/v0.3-rc1/zk/artifacts/README.md` | exit 0 |
| 894 | `git rev-parse origin/main:reference/v0.3-rc1/zk/circuits/common.circom` | exit 0 |
| 895 | `git hash-object -- reference/v0.3-rc1/zk/circuits/common.circom` | exit 0 |
| 896 | `git rev-parse origin/main:reference/v0.3-rc1/zk/circuits/mint.circom` | exit 0 |
| 897 | `git hash-object -- reference/v0.3-rc1/zk/circuits/mint.circom` | exit 0 |
| 898 | `git rev-parse origin/main:reference/v0.3-rc1/zk/circuits/spend.circom` | exit 0 |
| 899 | `git hash-object -- reference/v0.3-rc1/zk/circuits/spend.circom` | exit 0 |
| 900 | `git ls-files --others --exclude-standard reference/v0.3-rc1/ .aiops/` | exit 0 |
| 901 | `git diff --name-only origin/main -- runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs reference/v0.3-rc1/ .aiops/ docs/tasks/` | exit 0 |
| 902 | `git rev-parse --path-format=absolute --git-path objects` | exit 0 |
| 903 | `env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-e0705idp/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-index-e0705idp/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git read-tree HEAD` | exit 0 |
| 904 | `env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-e0705idp/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-index-e0705idp/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git add --intent-to-add -- docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md` | exit 0 |
| 905 | `env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-e0705idp/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-index-e0705idp/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git diff --name-only origin/main` | exit 0 |
| 906 | `env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-e0705idp/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-index-e0705idp/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git diff --check` | exit 2 |
| 907 | `git grep -n -E '(^&#124;[^0-9a-f])[0-9a-f]{40}([^0-9a-f]&#124;$)' HEAD -- '*.rs' '*.py' '*.md'` | exit 0 |
| 908 | `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | exit 0 |
| 909 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 910 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | exit 0 |
| 911 | `git rev-parse HEAD:runtime/crates/kix-kernel/tests/support/model_v4.rs` | exit 0 |
| 912 | `git rev-parse HEAD:reference/v0.3-rc1/protocol_contract.json` | exit 0 |
| 913 | `git rev-parse HEAD:docs/adr/0001-ktx-authority-commit-recovery.md` | exit 0 |
| 914 | `git rev-parse HEAD:docs/contracts/STATE_LIFECYCLE.md` | exit 0 |
| 915 | `git rev-parse HEAD:runtime/crates/kix-kernel/README.md` | exit 0 |
| 916 | `git show -s --format=%P 035d5705c93b318a49941ce5f7410f843360c427` | exit 0 |
| 917 | `git show -s --format=%P eb1caf8285c174697d78834246a304ffe9006427` | exit 0 |
| 918 | `git show -s --format=%P 876f41067bc7eb70bcd6ebd9c744c11b46f046b6` | exit 0 |
| 919 | `git show -s --format=%P d016caee4ae40f28f531809359ee77ac22db0073` | exit 0 |
| 920 | `git show -s --format=%P 70b976c0b8db686b1d21ff0831c275abf77a3d0a` | exit 0 |
| 921 | `git show -s --format=%P 9d50fb660248b66a5959f48f7dc96e68c9d5530b` | exit 0 |
| 922 | `git show -s --format=%P 9ed15a7adc93359e99bb5c3512a3ca20c77cb264` | exit 0 |
| 923 | `git show -s --format=%P 8e4813e868961adbabb7d1ee450a346f8fb6add1` | exit 0 |
| 924 | `git diff --name-only origin/main` | exit 0 |
| 925 | `git ls-files --others --exclude-standard` | exit 0 |
| 926 | `git rev-parse --path-format=absolute --git-path objects` | exit 0 |
| 927 | `env GIT_INDEX_FILE=/tmp/kix-perf-pin-final-ocpikj0d/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-final-ocpikj0d/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git read-tree HEAD` | exit 0 |
| 928 | `env GIT_INDEX_FILE=/tmp/kix-perf-pin-final-ocpikj0d/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-final-ocpikj0d/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git add --intent-to-add -- docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md` | exit 0 |
| 929 | `env GIT_INDEX_FILE=/tmp/kix-perf-pin-final-ocpikj0d/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-final-ocpikj0d/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git diff --name-only origin/main` | exit 0 |
| 930 | `env GIT_INDEX_FILE=/tmp/kix-perf-pin-final-ocpikj0d/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-final-ocpikj0d/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git diff --check` | exit 0 |
| 931 | `git diff --check` | exit 0 |
| 932 | `git diff --cached --name-only` | exit 0 |

## Raw outputs

Trailing line whitespace is stripped for Markdown, and NUL path separators
are rendered as newlines. Identical repeated command/output pairs are shown
once; all executions/exits remain in the command table. Source digests and
Git object IDs are unaffected.

### Command 1 — basis

```text
$ git rev-parse origin/main HEAD
8e4813e868961adbabb7d1ee450a346f8fb6add1
8e4813e868961adbabb7d1ee450a346f8fb6add1
exit: 0
```

### Command 2 — start status

```text
$ git status --short --untracked-files=all
exit: 0
```

### Command 3 — before locks

```text
$ git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs
69564b166f0c27f9af5d8422f0a466b18d74c20f
exit: 0
```

### Command 4 — before locks

```text
$ git hash-object -- runtime/crates/kix-kernel/src/lib.rs
69564b166f0c27f9af5d8422f0a466b18d74c20f
exit: 0
```

### Command 5 — before locks

```text
$ git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs
b607996c83a119c349f1cc90469ac1ba82764e20
exit: 0
```

### Command 6 — before locks

```text
$ git hash-object -- runtime/crates/kix-kernel/tests/quarantine_capacity.rs
b607996c83a119c349f1cc90469ac1ba82764e20
exit: 0
```

### Command 7 — before protected manifest

```text
$ git ls-files reference/v0.3-rc1/ .aiops/
.aiops/program.json
reference/v0.3-rc1/DESIGN_SUI_ZK.md
"reference/v0.3-rc1/KIX_v0.3_rc1_\352\265\254\355\230\204\352\262\260\352\263\274\354\231\200_\354\213\244\355\226\211\354\241\260\352\261\264.md"
reference/v0.3-rc1/README.md
reference/v0.3-rc1/adapters.py
reference/v0.3-rc1/archive_driver.py
reference/v0.3-rc1/assets.py
reference/v0.3-rc1/canonical_encoding.py
reference/v0.3-rc1/changes_from_v02.diff
reference/v0.3-rc1/check_reproducibility.py
reference/v0.3-rc1/client/archive-fixture.mjs
reference/v0.3-rc1/client/backup.mjs
reference/v0.3-rc1/client/canonical_encoding.ts
reference/v0.3-rc1/client/commerce_v2.ts
reference/v0.3-rc1/client/compile-circuits.mjs
reference/v0.3-rc1/client/encoding.mjs
reference/v0.3-rc1/client/independent.mjs
reference/v0.3-rc1/client/localnet-boundaries.mjs
reference/v0.3-rc1/client/localnet-paid.mjs
reference/v0.3-rc1/client/localnet.mjs
reference/v0.3-rc1/client/offline.test.mjs
reference/v0.3-rc1/client/package-lock.json
reference/v0.3-rc1/client/package.json
reference/v0.3-rc1/client/paid-chain.mjs
reference/v0.3-rc1/client/private.mjs
reference/v0.3-rc1/client/setup-zk.mjs
reference/v0.3-rc1/client/types.mjs
reference/v0.3-rc1/client/verify_canonical.ts
reference/v0.3-rc1/client/zk-policy.mjs
reference/v0.3-rc1/client/zk-regression.mjs
reference/v0.3-rc1/client/zk-test-utils.mjs
reference/v0.3-rc1/commerce.py
reference/v0.3-rc1/commerce_driver.py
reference/v0.3-rc1/common.py
reference/v0.3-rc1/contracts.py
reference/v0.3-rc1/core.py
reference/v0.3-rc1/dispatch.py
reference/v0.3-rc1/execution_contracts.py
reference/v0.3-rc1/finance.py
reference/v0.3-rc1/fixtures/canonical_encoding_v1.json
reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json
reference/v0.3-rc1/lifecycle.py
reference/v0.3-rc1/mock_provider.py
reference/v0.3-rc1/mutation_check.py
reference/v0.3-rc1/observations.py
reference/v0.3-rc1/paid_archive.py
reference/v0.3-rc1/paid_driver.py
reference/v0.3-rc1/paid_integration.py
reference/v0.3-rc1/paid_recovery.py
reference/v0.3-rc1/protocol_contract.json
reference/v0.3-rc1/requirements.txt
reference/v0.3-rc1/results/acceptance_trace.json
reference/v0.3-rc1/results/client_offline_tests.txt
reference/v0.3-rc1/results/client_syntax.json
reference/v0.3-rc1/results/manifest.sha256.json
reference/v0.3-rc1/results/mutation_logs/M01.txt
reference/v0.3-rc1/results/mutation_logs/M02.txt
reference/v0.3-rc1/results/mutation_logs/M03.txt
reference/v0.3-rc1/results/mutation_logs/M04.txt
reference/v0.3-rc1/results/mutation_logs/M05.txt
reference/v0.3-rc1/results/mutation_logs/M06.txt
reference/v0.3-rc1/results/mutation_logs/M07.txt
reference/v0.3-rc1/results/mutation_logs/M08.txt
reference/v0.3-rc1/results/mutation_logs/M09.txt
reference/v0.3-rc1/results/mutation_logs/M10.txt
reference/v0.3-rc1/results/mutation_logs/M11.txt
reference/v0.3-rc1/results/mutation_logs/M12.txt
reference/v0.3-rc1/results/mutation_logs/M13.txt
reference/v0.3-rc1/results/mutation_logs/M14.txt
reference/v0.3-rc1/results/mutation_results.json
reference/v0.3-rc1/results/preflight.json
reference/v0.3-rc1/results/reproducibility.json
reference/v0.3-rc1/results/review_trace_v03.json
reference/v0.3-rc1/results/tests.txt
reference/v0.3-rc1/results/v02_unchanged.json
reference/v0.3-rc1/results/verification.json
reference/v0.3-rc1/review_provenance/baseline_integrity.json
reference/v0.3-rc1/review_provenance/baseline_reproduced.json
reference/v0.3-rc1/review_provenance/review_v02_probe.py
reference/v0.3-rc1/review_provenance/review_verification.json
reference/v0.3-rc1/review_trace_v03.py
reference/v0.3-rc1/scripts/preflight.py
reference/v0.3-rc1/scripts/verify_package.py
reference/v0.3-rc1/source_inventory.json
reference/v0.3-rc1/storage_receipt.py
reference/v0.3-rc1/sui/Move.lock
reference/v0.3-rc1/sui/Move.toml
reference/v0.3-rc1/sui/sources/rights.move
reference/v0.3-rc1/sui/sources/zk_gate.move
reference/v0.3-rc1/sui/tests/rights_tests.move
reference/v0.3-rc1/test_assets.py
reference/v0.3-rc1/test_canonical_encoding.py
reference/v0.3-rc1/test_commerce.py
reference/v0.3-rc1/test_commerce_driver.py
reference/v0.3-rc1/test_core.py
reference/v0.3-rc1/test_execution_contracts.py
reference/v0.3-rc1/test_paid_archive.py
reference/v0.3-rc1/test_paid_integration.py
reference/v0.3-rc1/test_paid_recovery.py
reference/v0.3-rc1/test_storage_receipt.py
reference/v0.3-rc1/test_v02.py
reference/v0.3-rc1/test_v03.py
reference/v0.3-rc1/vendor/rights_model.py
reference/v0.3-rc1/vendor/tix_reconcile.py
reference/v0.3-rc1/verify.py
reference/v0.3-rc1/zk/artifacts/README.md
reference/v0.3-rc1/zk/circuits/common.circom
reference/v0.3-rc1/zk/circuits/mint.circom
reference/v0.3-rc1/zk/circuits/spend.circom
exit: 0
```

### Command 8 — before protected

```text
$ git rev-parse HEAD:.aiops/program.json
ff0f39a8129ca8b8d30818cce35c3d4e588872fc
exit: 0
```

### Command 9 — before protected

```text
$ git hash-object -- .aiops/program.json
ff0f39a8129ca8b8d30818cce35c3d4e588872fc
exit: 0
```

### Command 10 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/DESIGN_SUI_ZK.md
b71ad6d1b3b000c8ead472d3aed27963bd00b8ca
exit: 0
```

### Command 11 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/DESIGN_SUI_ZK.md
b71ad6d1b3b000c8ead472d3aed27963bd00b8ca
exit: 0
```

### Command 12 — before protected

```text
$ git rev-parse 'HEAD:"reference/v0.3-rc1/KIX_v0.3_rc1_\352\265\254\355\230\204\352\262\260\352\263\274\354\231\200_\354\213\244\355\226\211\354\241\260\352\261\264.md"'
fatal: path '"reference/v0.3-rc1/KIX_v0.3_rc1_\352\265\254\355\230\204\352\262\260\352\263\274\354\231\200_\354\213\244\355\226\211\354\241\260\352\261\264.md"' does not exist in 'HEAD'
HEAD:"reference/v0.3-rc1/KIX_v0.3_rc1_\352\265\254\355\230\204\352\262\260\352\263\274\354\231\200_\354\213\244\355\226\211\354\241\260\352\261\264.md"
exit: 128
```

### Command 19 — before protected manifest

```text
$ git ls-files -z reference/v0.3-rc1/ .aiops/
.aiops/program.json
reference/v0.3-rc1/DESIGN_SUI_ZK.md
reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md
reference/v0.3-rc1/README.md
reference/v0.3-rc1/adapters.py
reference/v0.3-rc1/archive_driver.py
reference/v0.3-rc1/assets.py
reference/v0.3-rc1/canonical_encoding.py
reference/v0.3-rc1/changes_from_v02.diff
reference/v0.3-rc1/check_reproducibility.py
reference/v0.3-rc1/client/archive-fixture.mjs
reference/v0.3-rc1/client/backup.mjs
reference/v0.3-rc1/client/canonical_encoding.ts
reference/v0.3-rc1/client/commerce_v2.ts
reference/v0.3-rc1/client/compile-circuits.mjs
reference/v0.3-rc1/client/encoding.mjs
reference/v0.3-rc1/client/independent.mjs
reference/v0.3-rc1/client/localnet-boundaries.mjs
reference/v0.3-rc1/client/localnet-paid.mjs
reference/v0.3-rc1/client/localnet.mjs
reference/v0.3-rc1/client/offline.test.mjs
reference/v0.3-rc1/client/package-lock.json
reference/v0.3-rc1/client/package.json
reference/v0.3-rc1/client/paid-chain.mjs
reference/v0.3-rc1/client/private.mjs
reference/v0.3-rc1/client/setup-zk.mjs
reference/v0.3-rc1/client/types.mjs
reference/v0.3-rc1/client/verify_canonical.ts
reference/v0.3-rc1/client/zk-policy.mjs
reference/v0.3-rc1/client/zk-regression.mjs
reference/v0.3-rc1/client/zk-test-utils.mjs
reference/v0.3-rc1/commerce.py
reference/v0.3-rc1/commerce_driver.py
reference/v0.3-rc1/common.py
reference/v0.3-rc1/contracts.py
reference/v0.3-rc1/core.py
reference/v0.3-rc1/dispatch.py
reference/v0.3-rc1/execution_contracts.py
reference/v0.3-rc1/finance.py
reference/v0.3-rc1/fixtures/canonical_encoding_v1.json
reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json
reference/v0.3-rc1/lifecycle.py
reference/v0.3-rc1/mock_provider.py
reference/v0.3-rc1/mutation_check.py
reference/v0.3-rc1/observations.py
reference/v0.3-rc1/paid_archive.py
reference/v0.3-rc1/paid_driver.py
reference/v0.3-rc1/paid_integration.py
reference/v0.3-rc1/paid_recovery.py
reference/v0.3-rc1/protocol_contract.json
reference/v0.3-rc1/requirements.txt
reference/v0.3-rc1/results/acceptance_trace.json
reference/v0.3-rc1/results/client_offline_tests.txt
reference/v0.3-rc1/results/client_syntax.json
reference/v0.3-rc1/results/manifest.sha256.json
reference/v0.3-rc1/results/mutation_logs/M01.txt
reference/v0.3-rc1/results/mutation_logs/M02.txt
reference/v0.3-rc1/results/mutation_logs/M03.txt
reference/v0.3-rc1/results/mutation_logs/M04.txt
reference/v0.3-rc1/results/mutation_logs/M05.txt
reference/v0.3-rc1/results/mutation_logs/M06.txt
reference/v0.3-rc1/results/mutation_logs/M07.txt
reference/v0.3-rc1/results/mutation_logs/M08.txt
reference/v0.3-rc1/results/mutation_logs/M09.txt
reference/v0.3-rc1/results/mutation_logs/M10.txt
reference/v0.3-rc1/results/mutation_logs/M11.txt
reference/v0.3-rc1/results/mutation_logs/M12.txt
reference/v0.3-rc1/results/mutation_logs/M13.txt
reference/v0.3-rc1/results/mutation_logs/M14.txt
reference/v0.3-rc1/results/mutation_results.json
reference/v0.3-rc1/results/preflight.json
reference/v0.3-rc1/results/reproducibility.json
reference/v0.3-rc1/results/review_trace_v03.json
reference/v0.3-rc1/results/tests.txt
reference/v0.3-rc1/results/v02_unchanged.json
reference/v0.3-rc1/results/verification.json
reference/v0.3-rc1/review_provenance/baseline_integrity.json
reference/v0.3-rc1/review_provenance/baseline_reproduced.json
reference/v0.3-rc1/review_provenance/review_v02_probe.py
reference/v0.3-rc1/review_provenance/review_verification.json
reference/v0.3-rc1/review_trace_v03.py
reference/v0.3-rc1/scripts/preflight.py
reference/v0.3-rc1/scripts/verify_package.py
reference/v0.3-rc1/source_inventory.json
reference/v0.3-rc1/storage_receipt.py
reference/v0.3-rc1/sui/Move.lock
reference/v0.3-rc1/sui/Move.toml
reference/v0.3-rc1/sui/sources/rights.move
reference/v0.3-rc1/sui/sources/zk_gate.move
reference/v0.3-rc1/sui/tests/rights_tests.move
reference/v0.3-rc1/test_assets.py
reference/v0.3-rc1/test_canonical_encoding.py
reference/v0.3-rc1/test_commerce.py
reference/v0.3-rc1/test_commerce_driver.py
reference/v0.3-rc1/test_core.py
reference/v0.3-rc1/test_execution_contracts.py
reference/v0.3-rc1/test_paid_archive.py
reference/v0.3-rc1/test_paid_integration.py
reference/v0.3-rc1/test_paid_recovery.py
reference/v0.3-rc1/test_storage_receipt.py
reference/v0.3-rc1/test_v02.py
reference/v0.3-rc1/test_v03.py
reference/v0.3-rc1/vendor/rights_model.py
reference/v0.3-rc1/vendor/tix_reconcile.py
reference/v0.3-rc1/verify.py
reference/v0.3-rc1/zk/artifacts/README.md
reference/v0.3-rc1/zk/circuits/common.circom
reference/v0.3-rc1/zk/circuits/mint.circom
reference/v0.3-rc1/zk/circuits/spend.circom
exit: 0
```

### Command 24 — before protected

```text
$ git rev-parse 'HEAD:reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md'
301fe796c16ee9a44e9f69d62f7015775c4a69e3
exit: 0
```

### Command 25 — before protected

```text
$ git hash-object -- 'reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md'
301fe796c16ee9a44e9f69d62f7015775c4a69e3
exit: 0
```

### Command 26 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/README.md
ae08e234389f4616de123ff848186a145f476806
exit: 0
```

### Command 27 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/README.md
ae08e234389f4616de123ff848186a145f476806
exit: 0
```

### Command 28 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/adapters.py
f0097af0fefdff1d92eb0640a4c45692f68d7db6
exit: 0
```

### Command 29 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/adapters.py
f0097af0fefdff1d92eb0640a4c45692f68d7db6
exit: 0
```

### Command 30 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/archive_driver.py
e773292fccfbfa7265d2a28d5f241f806f9494d7
exit: 0
```

### Command 31 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/archive_driver.py
e773292fccfbfa7265d2a28d5f241f806f9494d7
exit: 0
```

### Command 32 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/assets.py
6383cd608f203e237d7879efe59b4297bb09fe05
exit: 0
```

### Command 33 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/assets.py
6383cd608f203e237d7879efe59b4297bb09fe05
exit: 0
```

### Command 34 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/canonical_encoding.py
30d646818c94c20e6a93d6b463598b6254e053df
exit: 0
```

### Command 35 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/canonical_encoding.py
30d646818c94c20e6a93d6b463598b6254e053df
exit: 0
```

### Command 36 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/changes_from_v02.diff
aa8d41d12ed2d2775a200ea0261dc5d89a565992
exit: 0
```

### Command 37 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/changes_from_v02.diff
aa8d41d12ed2d2775a200ea0261dc5d89a565992
exit: 0
```

### Command 38 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/check_reproducibility.py
b5eef81a2e96b0cab1b7746f0248c249f4fa382c
exit: 0
```

### Command 39 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/check_reproducibility.py
b5eef81a2e96b0cab1b7746f0248c249f4fa382c
exit: 0
```

### Command 40 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/archive-fixture.mjs
99c842d1fc9580bdb87a79b5ecdcfb811c79aa58
exit: 0
```

### Command 41 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/archive-fixture.mjs
99c842d1fc9580bdb87a79b5ecdcfb811c79aa58
exit: 0
```

### Command 42 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/backup.mjs
6d185685210be88b86c0157df9b9799dffc210fe
exit: 0
```

### Command 43 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/backup.mjs
6d185685210be88b86c0157df9b9799dffc210fe
exit: 0
```

### Command 44 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/canonical_encoding.ts
60974034546e85ffbdacce3f581adda59d8237f2
exit: 0
```

### Command 45 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/canonical_encoding.ts
60974034546e85ffbdacce3f581adda59d8237f2
exit: 0
```

### Command 46 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/commerce_v2.ts
44703752f50473ed5b2992a73f88e4ed70341c2c
exit: 0
```

### Command 47 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/commerce_v2.ts
44703752f50473ed5b2992a73f88e4ed70341c2c
exit: 0
```

### Command 48 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/compile-circuits.mjs
061c6a9cbce05e204b3ee243c1ea4dfc5c7e8207
exit: 0
```

### Command 49 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/compile-circuits.mjs
061c6a9cbce05e204b3ee243c1ea4dfc5c7e8207
exit: 0
```

### Command 50 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/encoding.mjs
34f8e570bd449275d3111518ea882d1a5fe005bd
exit: 0
```

### Command 51 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/encoding.mjs
34f8e570bd449275d3111518ea882d1a5fe005bd
exit: 0
```

### Command 52 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/independent.mjs
331b617ac2b010a28ad34e4e7db269dc3b5fcde4
exit: 0
```

### Command 53 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/independent.mjs
331b617ac2b010a28ad34e4e7db269dc3b5fcde4
exit: 0
```

### Command 54 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/localnet-boundaries.mjs
d65b7593695c29100f5af18cd9d8cba5dbcee35e
exit: 0
```

### Command 55 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/localnet-boundaries.mjs
d65b7593695c29100f5af18cd9d8cba5dbcee35e
exit: 0
```

### Command 56 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/localnet-paid.mjs
4ab7c7bb4fbcb3e6322dcdda99f82f1767163216
exit: 0
```

### Command 57 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/localnet-paid.mjs
4ab7c7bb4fbcb3e6322dcdda99f82f1767163216
exit: 0
```

### Command 58 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/localnet.mjs
f3a676e73de5bf5434ce2db80ec9abbbeb210259
exit: 0
```

### Command 59 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/localnet.mjs
f3a676e73de5bf5434ce2db80ec9abbbeb210259
exit: 0
```

### Command 60 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/offline.test.mjs
dd1d46e273d3e3e8e5a6744aebcf400a3142855f
exit: 0
```

### Command 61 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/offline.test.mjs
dd1d46e273d3e3e8e5a6744aebcf400a3142855f
exit: 0
```

### Command 62 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/package-lock.json
4a6431cd2e93c8a53cabfbe35e5cd5de2583c181
exit: 0
```

### Command 63 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/package-lock.json
4a6431cd2e93c8a53cabfbe35e5cd5de2583c181
exit: 0
```

### Command 64 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/package.json
085af5ae575ca60bebdfd2acefdf7eae11ebdfb6
exit: 0
```

### Command 65 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/package.json
085af5ae575ca60bebdfd2acefdf7eae11ebdfb6
exit: 0
```

### Command 66 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/paid-chain.mjs
d23782e52a517a81026f6c4d172e5ac0b1580942
exit: 0
```

### Command 67 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/paid-chain.mjs
d23782e52a517a81026f6c4d172e5ac0b1580942
exit: 0
```

### Command 68 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/private.mjs
e9cc6bdb3cfa9d5f5d5979517146ea469ebb865e
exit: 0
```

### Command 69 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/private.mjs
e9cc6bdb3cfa9d5f5d5979517146ea469ebb865e
exit: 0
```

### Command 70 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/setup-zk.mjs
b27b581ec22f76f2631af54484fd582f914a82f0
exit: 0
```

### Command 71 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/setup-zk.mjs
b27b581ec22f76f2631af54484fd582f914a82f0
exit: 0
```

### Command 72 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/types.mjs
7fcad757367415f87098dd25c89620c1529cb933
exit: 0
```

### Command 73 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/types.mjs
7fcad757367415f87098dd25c89620c1529cb933
exit: 0
```

### Command 74 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/verify_canonical.ts
0e2894956970d4d898ea57cf2a9abadab81ec2c8
exit: 0
```

### Command 75 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/verify_canonical.ts
0e2894956970d4d898ea57cf2a9abadab81ec2c8
exit: 0
```

### Command 76 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/zk-policy.mjs
8bd3f600dee47331bda24e0deb2993e591627558
exit: 0
```

### Command 77 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/zk-policy.mjs
8bd3f600dee47331bda24e0deb2993e591627558
exit: 0
```

### Command 78 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/zk-regression.mjs
4372288383c7c158d0c8beeb569954ae70cdda07
exit: 0
```

### Command 79 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/zk-regression.mjs
4372288383c7c158d0c8beeb569954ae70cdda07
exit: 0
```

### Command 80 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/client/zk-test-utils.mjs
15c0a397ee5dceb1ace0548e0e87c0ceee526532
exit: 0
```

### Command 81 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/client/zk-test-utils.mjs
15c0a397ee5dceb1ace0548e0e87c0ceee526532
exit: 0
```

### Command 82 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/commerce.py
eb0a53cd70cd22ad4301cd0be9d368db8caa355c
exit: 0
```

### Command 83 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/commerce.py
eb0a53cd70cd22ad4301cd0be9d368db8caa355c
exit: 0
```

### Command 84 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/commerce_driver.py
09c643f8a33daf119b5c9d5902fb9eadbd876ad4
exit: 0
```

### Command 85 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/commerce_driver.py
09c643f8a33daf119b5c9d5902fb9eadbd876ad4
exit: 0
```

### Command 86 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/common.py
f23d267405611c6cf2cbbcb952929dbedd21616d
exit: 0
```

### Command 87 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/common.py
f23d267405611c6cf2cbbcb952929dbedd21616d
exit: 0
```

### Command 88 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/contracts.py
53a72e0e2e962a1759456739f8eb81d72e001284
exit: 0
```

### Command 89 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/contracts.py
53a72e0e2e962a1759456739f8eb81d72e001284
exit: 0
```

### Command 90 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/core.py
fd02b70c58a35ec5d7f3dda36c62856d2155251f
exit: 0
```

### Command 91 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/core.py
fd02b70c58a35ec5d7f3dda36c62856d2155251f
exit: 0
```

### Command 92 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/dispatch.py
1ad053df55ede1364cfb1671bf0d43fdd2e500a2
exit: 0
```

### Command 93 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/dispatch.py
1ad053df55ede1364cfb1671bf0d43fdd2e500a2
exit: 0
```

### Command 94 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/execution_contracts.py
6b14a5db16cdba5a3c1013fe1623106df7b2f4cd
exit: 0
```

### Command 95 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/execution_contracts.py
6b14a5db16cdba5a3c1013fe1623106df7b2f4cd
exit: 0
```

### Command 96 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/finance.py
05393f495fcc3512bb17505c8202396d1865ec41
exit: 0
```

### Command 97 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/finance.py
05393f495fcc3512bb17505c8202396d1865ec41
exit: 0
```

### Command 98 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/fixtures/canonical_encoding_v1.json
90c74af5e5464d990afb8096d3e315d629743361
exit: 0
```

### Command 99 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/fixtures/canonical_encoding_v1.json
90c74af5e5464d990afb8096d3e315d629743361
exit: 0
```

### Command 100 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json
40cb76cb8af8cbf617a18b8a92990e3aac7e999a
exit: 0
```

### Command 101 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json
40cb76cb8af8cbf617a18b8a92990e3aac7e999a
exit: 0
```

### Command 102 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/lifecycle.py
4770ee2ce63e784d696e06f34797137805b2b6b9
exit: 0
```

### Command 103 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/lifecycle.py
4770ee2ce63e784d696e06f34797137805b2b6b9
exit: 0
```

### Command 104 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/mock_provider.py
a0a07b39c4642bc81d951dbeeefeaf62a790d6fd
exit: 0
```

### Command 105 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/mock_provider.py
a0a07b39c4642bc81d951dbeeefeaf62a790d6fd
exit: 0
```

### Command 106 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/mutation_check.py
45e7e06e6770ce21ed07d78eb7c4f3aa025d5de0
exit: 0
```

### Command 107 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/mutation_check.py
45e7e06e6770ce21ed07d78eb7c4f3aa025d5de0
exit: 0
```

### Command 108 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/observations.py
4551be53386557e3dc71d295646eaf5ab8318a42
exit: 0
```

### Command 109 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/observations.py
4551be53386557e3dc71d295646eaf5ab8318a42
exit: 0
```

### Command 110 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/paid_archive.py
cc035517114c8810736d5e480fe14e17f4b6b0d7
exit: 0
```

### Command 111 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/paid_archive.py
cc035517114c8810736d5e480fe14e17f4b6b0d7
exit: 0
```

### Command 112 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/paid_driver.py
3412c363e8688555b1ab9b2f8586110b27df7008
exit: 0
```

### Command 113 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/paid_driver.py
3412c363e8688555b1ab9b2f8586110b27df7008
exit: 0
```

### Command 114 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/paid_integration.py
a8306ab079391702bd17540e131c8117c763629b
exit: 0
```

### Command 115 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/paid_integration.py
a8306ab079391702bd17540e131c8117c763629b
exit: 0
```

### Command 116 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/paid_recovery.py
16191b15c7a5157526aa01e49e04a229b5be05ec
exit: 0
```

### Command 117 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/paid_recovery.py
16191b15c7a5157526aa01e49e04a229b5be05ec
exit: 0
```

### Command 118 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/protocol_contract.json
619ae21c82ca3df5661bd3831613f15fa65225ff
exit: 0
```

### Command 119 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/protocol_contract.json
619ae21c82ca3df5661bd3831613f15fa65225ff
exit: 0
```

### Command 120 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/requirements.txt
666c60dfa2fd8cacb8a8945f805fda6db39f9299
exit: 0
```

### Command 121 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/requirements.txt
666c60dfa2fd8cacb8a8945f805fda6db39f9299
exit: 0
```

### Command 122 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/acceptance_trace.json
3fda1262ffa630b010eb629b0e30ce2e8ae5f50e
exit: 0
```

### Command 123 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/acceptance_trace.json
3fda1262ffa630b010eb629b0e30ce2e8ae5f50e
exit: 0
```

### Command 124 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/client_offline_tests.txt
d351ed1b80f031461b2a57cb9a577347427bb643
exit: 0
```

### Command 125 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/client_offline_tests.txt
d351ed1b80f031461b2a57cb9a577347427bb643
exit: 0
```

### Command 126 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/client_syntax.json
3ca4eed2507f2134234bad86df4d8b69817d4de7
exit: 0
```

### Command 127 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/client_syntax.json
3ca4eed2507f2134234bad86df4d8b69817d4de7
exit: 0
```

### Command 128 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/manifest.sha256.json
6b779387247920bffffeff5cfacd6bfc11f84127
exit: 0
```

### Command 129 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/manifest.sha256.json
6b779387247920bffffeff5cfacd6bfc11f84127
exit: 0
```

### Command 130 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M01.txt
477b00cc36e446fb308c817b7f4f50a9cc4a7014
exit: 0
```

### Command 131 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M01.txt
477b00cc36e446fb308c817b7f4f50a9cc4a7014
exit: 0
```

### Command 132 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M02.txt
e656a9c1243f96f96196a5bd57e7b8a52b275776
exit: 0
```

### Command 133 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M02.txt
e656a9c1243f96f96196a5bd57e7b8a52b275776
exit: 0
```

### Command 134 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M03.txt
df142f75c3acb4b940b2cce06400c9820357630c
exit: 0
```

### Command 135 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M03.txt
df142f75c3acb4b940b2cce06400c9820357630c
exit: 0
```

### Command 136 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M04.txt
404ca2c7f76de172a6dff1a15ef0311f849d8dc9
exit: 0
```

### Command 137 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M04.txt
404ca2c7f76de172a6dff1a15ef0311f849d8dc9
exit: 0
```

### Command 138 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M05.txt
b44e803bcb986dcdc82c2dbdfd931d786d8440a6
exit: 0
```

### Command 139 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M05.txt
b44e803bcb986dcdc82c2dbdfd931d786d8440a6
exit: 0
```

### Command 140 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M06.txt
0df5fe9d80d914cbc6e95cf5f594ee0e7180a5f8
exit: 0
```

### Command 141 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M06.txt
0df5fe9d80d914cbc6e95cf5f594ee0e7180a5f8
exit: 0
```

### Command 142 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M07.txt
348a7d05fa787ce139bd2c402c9042529cf4e487
exit: 0
```

### Command 143 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M07.txt
348a7d05fa787ce139bd2c402c9042529cf4e487
exit: 0
```

### Command 144 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M08.txt
c3ba396ab5b39fafa07df167af57e555ad8368dd
exit: 0
```

### Command 145 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M08.txt
c3ba396ab5b39fafa07df167af57e555ad8368dd
exit: 0
```

### Command 146 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M09.txt
d32c7d16ca5eb4775d3353a3cf1db6c45cee3efd
exit: 0
```

### Command 147 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M09.txt
d32c7d16ca5eb4775d3353a3cf1db6c45cee3efd
exit: 0
```

### Command 148 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M10.txt
0f0fb480a7c042bdaa4b34f9099ce4c93c4b3c51
exit: 0
```

### Command 149 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M10.txt
0f0fb480a7c042bdaa4b34f9099ce4c93c4b3c51
exit: 0
```

### Command 150 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M11.txt
0941b10178f614159f248fc57dc0c7b8d2d5a91f
exit: 0
```

### Command 151 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M11.txt
0941b10178f614159f248fc57dc0c7b8d2d5a91f
exit: 0
```

### Command 152 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M12.txt
c9ce89485b474bfc5ad468cb50a4254b95f7a8e4
exit: 0
```

### Command 153 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M12.txt
c9ce89485b474bfc5ad468cb50a4254b95f7a8e4
exit: 0
```

### Command 154 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M13.txt
9a6929779d9c3f52ce95479bc8cf089d0aa50089
exit: 0
```

### Command 155 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M13.txt
9a6929779d9c3f52ce95479bc8cf089d0aa50089
exit: 0
```

### Command 156 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_logs/M14.txt
e3829e77c0f389fc31f180701a888273e8f134d9
exit: 0
```

### Command 157 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_logs/M14.txt
e3829e77c0f389fc31f180701a888273e8f134d9
exit: 0
```

### Command 158 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/mutation_results.json
83301937ef2443dfd4e44b0464ee09cc7d1fdc7f
exit: 0
```

### Command 159 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/mutation_results.json
83301937ef2443dfd4e44b0464ee09cc7d1fdc7f
exit: 0
```

### Command 160 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/preflight.json
558a1e59d2a921932b7bde570e6597dfaf2e925e
exit: 0
```

### Command 161 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/preflight.json
558a1e59d2a921932b7bde570e6597dfaf2e925e
exit: 0
```

### Command 162 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/reproducibility.json
3a3faba979742d1fc5be6627a2d9716fb91a33b8
exit: 0
```

### Command 163 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/reproducibility.json
3a3faba979742d1fc5be6627a2d9716fb91a33b8
exit: 0
```

### Command 164 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/review_trace_v03.json
75147c8f0d4192fa2c9269950867824116ef6bdf
exit: 0
```

### Command 165 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/review_trace_v03.json
75147c8f0d4192fa2c9269950867824116ef6bdf
exit: 0
```

### Command 166 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/tests.txt
eca04766e566c4eedc3253fabfccb25422a06cd4
exit: 0
```

### Command 167 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/tests.txt
eca04766e566c4eedc3253fabfccb25422a06cd4
exit: 0
```

### Command 168 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/v02_unchanged.json
c8639c8980ea44864a0bee16241b6830fb1dc7c2
exit: 0
```

### Command 169 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/v02_unchanged.json
c8639c8980ea44864a0bee16241b6830fb1dc7c2
exit: 0
```

### Command 170 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/results/verification.json
cee2e47a294d33599c6b89bba3a60d082d246961
exit: 0
```

### Command 171 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/results/verification.json
cee2e47a294d33599c6b89bba3a60d082d246961
exit: 0
```

### Command 172 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/review_provenance/baseline_integrity.json
11d6afbd6ca7e89bad7047efabb52edb736b3ea9
exit: 0
```

### Command 173 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/review_provenance/baseline_integrity.json
11d6afbd6ca7e89bad7047efabb52edb736b3ea9
exit: 0
```

### Command 174 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/review_provenance/baseline_reproduced.json
dd89cea025800a6cf1a8cde6ffdea30f0d5ef769
exit: 0
```

### Command 175 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/review_provenance/baseline_reproduced.json
dd89cea025800a6cf1a8cde6ffdea30f0d5ef769
exit: 0
```

### Command 176 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/review_provenance/review_v02_probe.py
5ecf0d82ce3f46cec9c75ffa69600c76f31c9c2c
exit: 0
```

### Command 177 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/review_provenance/review_v02_probe.py
5ecf0d82ce3f46cec9c75ffa69600c76f31c9c2c
exit: 0
```

### Command 178 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/review_provenance/review_verification.json
b5950eb99a82ae73de0b552a2b4eee1823ddab62
exit: 0
```

### Command 179 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/review_provenance/review_verification.json
b5950eb99a82ae73de0b552a2b4eee1823ddab62
exit: 0
```

### Command 180 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/review_trace_v03.py
5e631f7aa92a23a96275f47553da3ecd9de97678
exit: 0
```

### Command 181 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/review_trace_v03.py
5e631f7aa92a23a96275f47553da3ecd9de97678
exit: 0
```

### Command 182 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/scripts/preflight.py
b6d87981b94c947e5b538b8e328b111bf1913612
exit: 0
```

### Command 183 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/scripts/preflight.py
b6d87981b94c947e5b538b8e328b111bf1913612
exit: 0
```

### Command 184 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/scripts/verify_package.py
9198166197c7b76d24fed3d1256a00a336c4bb05
exit: 0
```

### Command 185 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/scripts/verify_package.py
9198166197c7b76d24fed3d1256a00a336c4bb05
exit: 0
```

### Command 186 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/source_inventory.json
d59196e1dc97b5ec8c73738e78b452e9c72624fc
exit: 0
```

### Command 187 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/source_inventory.json
d59196e1dc97b5ec8c73738e78b452e9c72624fc
exit: 0
```

### Command 188 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/storage_receipt.py
eecce5d698d3103b15a9834b558aee619fb2fb8b
exit: 0
```

### Command 189 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/storage_receipt.py
eecce5d698d3103b15a9834b558aee619fb2fb8b
exit: 0
```

### Command 190 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/sui/Move.lock
76f76e701cb9b394ae520bfbf0c162e1101dc4cd
exit: 0
```

### Command 191 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/sui/Move.lock
76f76e701cb9b394ae520bfbf0c162e1101dc4cd
exit: 0
```

### Command 192 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/sui/Move.toml
e7f4a535cd23e7ceba4f78c34151b473db737867
exit: 0
```

### Command 193 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/sui/Move.toml
e7f4a535cd23e7ceba4f78c34151b473db737867
exit: 0
```

### Command 194 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/sui/sources/rights.move
ea7905038bcbd51c7ea126ff6b12d560f6227dd5
exit: 0
```

### Command 195 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/sui/sources/rights.move
ea7905038bcbd51c7ea126ff6b12d560f6227dd5
exit: 0
```

### Command 196 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/sui/sources/zk_gate.move
333e0cfd7911e97f10354507eef5d327a446061e
exit: 0
```

### Command 197 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/sui/sources/zk_gate.move
333e0cfd7911e97f10354507eef5d327a446061e
exit: 0
```

### Command 198 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/sui/tests/rights_tests.move
8717d1f86228cc502a1948e58e8618bbd7d994d0
exit: 0
```

### Command 199 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/sui/tests/rights_tests.move
8717d1f86228cc502a1948e58e8618bbd7d994d0
exit: 0
```

### Command 200 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_assets.py
fac5e15e06fe0a90259e9fd6079abe5c4ba4c5e0
exit: 0
```

### Command 201 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_assets.py
fac5e15e06fe0a90259e9fd6079abe5c4ba4c5e0
exit: 0
```

### Command 202 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_canonical_encoding.py
335f5d576c96beeb241d295ea6dfc33b46bbdbc8
exit: 0
```

### Command 203 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_canonical_encoding.py
335f5d576c96beeb241d295ea6dfc33b46bbdbc8
exit: 0
```

### Command 204 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_commerce.py
be9659197294415038f24144b61a499fafb2e4e1
exit: 0
```

### Command 205 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_commerce.py
be9659197294415038f24144b61a499fafb2e4e1
exit: 0
```

### Command 206 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_commerce_driver.py
9f0466ab923cfddbac03e4ac6dc07373d302b41f
exit: 0
```

### Command 207 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_commerce_driver.py
9f0466ab923cfddbac03e4ac6dc07373d302b41f
exit: 0
```

### Command 208 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_core.py
dcf29bb14d134cae0d25d51bc076d6cf0e69b0c4
exit: 0
```

### Command 209 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_core.py
dcf29bb14d134cae0d25d51bc076d6cf0e69b0c4
exit: 0
```

### Command 210 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_execution_contracts.py
8965fcf65e0ed569313160f71a17736757a50b60
exit: 0
```

### Command 211 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_execution_contracts.py
8965fcf65e0ed569313160f71a17736757a50b60
exit: 0
```

### Command 212 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_paid_archive.py
ac9cf5ed9367eadbd5917c1e27fb80fa860223f0
exit: 0
```

### Command 213 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_paid_archive.py
ac9cf5ed9367eadbd5917c1e27fb80fa860223f0
exit: 0
```

### Command 214 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_paid_integration.py
f451fd57215e67f9ac6a118fd0c61fc37d9ea0b5
exit: 0
```

### Command 215 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_paid_integration.py
f451fd57215e67f9ac6a118fd0c61fc37d9ea0b5
exit: 0
```

### Command 216 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_paid_recovery.py
6e86d418d67b2e18275390adde0820db0d87bdcc
exit: 0
```

### Command 217 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_paid_recovery.py
6e86d418d67b2e18275390adde0820db0d87bdcc
exit: 0
```

### Command 218 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_storage_receipt.py
09c523702ad28395cef39249aa8c26fd8888e9b0
exit: 0
```

### Command 219 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_storage_receipt.py
09c523702ad28395cef39249aa8c26fd8888e9b0
exit: 0
```

### Command 220 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_v02.py
a389aa7eb7f7d4305a52d29595ec688d69d87a7a
exit: 0
```

### Command 221 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_v02.py
a389aa7eb7f7d4305a52d29595ec688d69d87a7a
exit: 0
```

### Command 222 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/test_v03.py
9e739ac657974fa3700c92abeb272071dd7ea9b3
exit: 0
```

### Command 223 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/test_v03.py
9e739ac657974fa3700c92abeb272071dd7ea9b3
exit: 0
```

### Command 224 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/vendor/rights_model.py
03b095d806fd2f0e85323d69739906b50b227466
exit: 0
```

### Command 225 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/vendor/rights_model.py
03b095d806fd2f0e85323d69739906b50b227466
exit: 0
```

### Command 226 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/vendor/tix_reconcile.py
8bc8847f164118d8205e209386aa542d1e7f8a2e
exit: 0
```

### Command 227 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/vendor/tix_reconcile.py
8bc8847f164118d8205e209386aa542d1e7f8a2e
exit: 0
```

### Command 228 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/verify.py
a209e7e5b3dd1167f125a06addf364745b709267
exit: 0
```

### Command 229 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/verify.py
a209e7e5b3dd1167f125a06addf364745b709267
exit: 0
```

### Command 230 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/zk/artifacts/README.md
6861ccc1d7ef6caac6e1e37043f47ce907b2eeb4
exit: 0
```

### Command 231 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/zk/artifacts/README.md
6861ccc1d7ef6caac6e1e37043f47ce907b2eeb4
exit: 0
```

### Command 232 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/zk/circuits/common.circom
5a4cc324e5694bb78db2b9448642eaeacd769413
exit: 0
```

### Command 233 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/zk/circuits/common.circom
5a4cc324e5694bb78db2b9448642eaeacd769413
exit: 0
```

### Command 234 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/zk/circuits/mint.circom
de6b2e918be4e61bb5debdee351cf39eddd3383d
exit: 0
```

### Command 235 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/zk/circuits/mint.circom
de6b2e918be4e61bb5debdee351cf39eddd3383d
exit: 0
```

### Command 236 — before protected

```text
$ git rev-parse HEAD:reference/v0.3-rc1/zk/circuits/spend.circom
1cdabb7000e639789f6d2ecd074824fca04206e9
exit: 0
```

### Command 237 — before protected

```text
$ git hash-object -- reference/v0.3-rc1/zk/circuits/spend.circom
1cdabb7000e639789f6d2ecd074824fca04206e9
exit: 0
```

### Command 238 — complete source scan

```text
$ git grep -n -E '(^|[^0-9a-f])[0-9a-f]{40}([^0-9a-f]|$)' HEAD -- '*.rs' '*.py' '*.md'
[Selected principal pin-value lines from 2,105 output lines; complete candidate types/classifications above, repeated occurrences in the addendum.]
HEAD:.github/PULL_REQUEST_TEMPLATE/devin_pr_template.md:19:- [ ] `runtime/crates/kix-kernel/src/lib.rs` matches blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
HEAD:.github/PULL_REQUEST_TEMPLATE/devin_pr_template.md:20:- [ ] `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` matches blob `b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:AGENTS.md:92:  - required Git blob: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
HEAD:AGENTS.md:94:  - required Git blob: `b607996c83a119c349f1cc90469ac1ba82764e20`
HEAD:README.md:20:| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | 검토한 R1 v4 동작을 고정해 모델·불변식·측정 결과의 기준이 움직이지 않게 함 |
HEAD:README.md:21:| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | 만석에서도 bound 격리를 보존하는 검토 회귀를 고정 |
HEAD:docs/CODE_HYGIENE_BACKLOG.md:28:- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
HEAD:docs/CODE_HYGIENE_BACKLOG.md:29:- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`
HEAD:docs/DEVELOPMENT_PLAN.md:57:- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
HEAD:docs/DEVELOPMENT_PLAN.md:58:- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`
HEAD:docs/adr/0001-ktx-authority-commit-recovery.md:70:The R1 A revision was published at `b57d49d068c14d1a012e73cbc8c10c8f6ee5d631` and is included in main `94376835ea4fc818619fc79e2be4df7d4947496a`; locked kernel blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`. It accepts semantics version 4 and rejects other versions: bound-operation quarantine applies before conflict capacity checks, while unbound quarantine requires retained evidence; see the review addendum below. Its replay test reconstructs in-memory state from the same ordered inputs. This is NOT disk, upgrade, cluster-replay or leader-crash verification.
HEAD:docs/adr/0003-coin-tix-lock-localnet-re-ruling-request.md:27:| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
HEAD:docs/adr/0003-coin-tix-lock-localnet-re-ruling-request.md:28:| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |
HEAD:docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md:28:읽은 tree의 잠금 blob은 `runtime/crates/kix-kernel/src/lib.rs = 69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs = b607996c83a119c349f1cc90469ac1ba82764e20`다. 이번 작성 경로는 문서 두 개뿐이며 잠금·참조 구현을 수정하지 않는다.
HEAD:docs/contracts/ADAPTER_EVENT_IDENTITY.md:45:`runtime/crates/kix-kernel/src/lib.rs` blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`의
HEAD:docs/contracts/CONTRACT_INVARIANTS.md:5:Kernel blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` and locked quarantine
HEAD:docs/contracts/CONTRACT_INVARIANTS.md:6:regression `b607996c83a119c349f1cc90469ac1ba82764e20` remain unchanged.
HEAD:docs/contracts/CONTRACT_INVARIANTS.md:32:| A | docs/adr/0001-ktx-authority-commit-recovery.md | 07c36869e7b68fff10b02e6c59d7119df56d0785 | §3 stable identity/original result; §4 atomic reservation; §5 read-only replay; §6 event vs economic dedupe; §8 inventory and bounds |
HEAD:docs/contracts/CONTRACT_INVARIANTS.md:33:| L | docs/contracts/STATE_LIFECYCLE.md | e953c4870aaeee24b13c75a8647c50609720ae01 | §2 command/observation lifetimes; §3 LC-FACT; §5 LC-TERM captured facts are not erased; §6 no invented GC |
HEAD:docs/contracts/CONTRACT_INVARIANTS.md:34:| R | runtime/crates/kix-kernel/README.md | 900866ee99a71254fb7da1ad2aa4640477ac550c | Implemented meaning; Observation reservation and remaining gaps; bounded sum and first-capture contract |
HEAD:docs/contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md:6:잠금 blob 둘은 그대로다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:docs/contracts/PERFORMANCE_BASELINE_V4.md:26:| kernel | semantics=4; blob 69564b166f0c27f9af5d8422f0a466b18d74c20f |
HEAD:docs/contracts/PG_TOSS_CARD_PROFILE.md:61:`69564b166f0c27f9af5d8422f0a466b18d74c20f`의 context/mark_payment_unknown/expire/observe_capture.
HEAD:docs/contracts/RIGHTS_SCALE_PROFILE.md:24:- 잠금 blob은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`. `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`. 이 노드는 두 파일을 수정하지 않는다.
HEAD:docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:81:| 그 blob | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
HEAD:docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:82:| 잠금만 확인, 본문은 스캔하지 않음 | `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20` |
HEAD:docs/contracts/STATE_LIFECYCLE.md:12:`69564b166f0c27f9af5d8422f0a466b18d74c20f`.
HEAD:docs/contracts/STATE_LIFECYCLE.md:34:`07c36869e7b68fff10b02e6c59d7119df56d0785`다.
HEAD:docs/contracts/STATE_LIFECYCLE.md:488:`69564b166f0c27f9af5d8422f0a466b18d74c20f`에서 `observe_capture`는 첫 capture를
HEAD:docs/contracts/STATE_LIFECYCLE.md:595:| 0.1 — 첫 묶음 최초 수명 계약 (`0394a36a655b86bacb568b055d377d4c4fd91185`) | `e953c4870aaeee24b13c75a8647c50609720ae01` | LC-FACT/LC-CUT/LC-TERM과 제공자 종결 보증을 전제한 초기 초안 |
HEAD:docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md:7:잠금 blob 둘은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`. 문서 추가 뒤에 다시 계산한다. 두 파일은 수정하지 않는다.
HEAD:docs/contracts/TOKEN_ROLE_AND_SUPPLY.md:7:잠금 blob 둘은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`. 문서 추가 뒤에 다시 계산한다. 두 파일은 수정하지 않는다.
HEAD:docs/contracts/openapi/README.md:30:| git blob | `619ae21c82ca3df5661bd3831613f15fa65225ff` |
HEAD:docs/decisions/AI_DELEGATION_EXECUTION_DECISION_PROPOSAL_20261016.md:32:| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
HEAD:docs/decisions/AI_DELEGATION_EXECUTION_DECISION_PROPOSAL_20261016.md:33:| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |
HEAD:docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md:20:- 잠금 blob은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. 문서 추가 뒤에 다시 계산한다. 두 파일은 수정하지 않는다.
HEAD:docs/decisions/CUT_PROOF_I12_20261008.md:12:- 잠금 blob은 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. 이 노드는 두 파일을 수정하지 않는다.
HEAD:docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md:28:| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
HEAD:docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md:29:| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |
HEAD:docs/decisions/GATE_BROWSER_ACCESS_DECISION_20261008.md:10:- 잠금 blob은 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:docs/decisions/INTEGRATION_A_DECISION_PROPOSAL_20261009.md:20:- 잠금 blob은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. 문서 추가 뒤에 다시 계산한다. 두 파일은 수정하지 않는다.
HEAD:docs/decisions/INTEGRATION_A_REESTIMATE_20261009.md:18:- 잠금 blob은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. 두 파일은 수정하지 않는다. 문서 추가 뒤에 다시 계산한다.
HEAD:docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md:18:- 잠금 blob은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. 문서 추가 뒤에 다시 계산한다. 두 파일은 수정하지 않는다.
HEAD:docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md:10:- 잠금 blob은 요구값과 일치했다. `lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md:16:- 잠금 blob은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. 문서 추가 뒤에 다시 계산한다. 두 파일은 수정하지 않는다.
HEAD:docs/decisions/TESTNET_KEY_MANAGEMENT_DECISION_PROPOSAL_20261016.md:32:| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
HEAD:docs/decisions/TESTNET_KEY_MANAGEMENT_DECISION_PROPOSAL_20261016.md:33:| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |
HEAD:docs/decisions/TL2_DOES_NOT_OPEN_20261009.md:9:잠금 blob 둘은 작업 전 요구값과 일치했다. 이 기록만 더한 뒤에도 같다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`. 두 파일은 수정하지 않는다. `reference/v0.3-rc1/**`도 수정하지 않는다. Sui 프레임워크 rev는 `reference/v0.3-rc1/sui/Move.toml`의 `808640d9b49aecf29d8e6f46033c15eca236efa7` 그대로다.
HEAD:docs/decisions/TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md:9:잠금 blob 둘은 작업 전 요구값과 일치했다. 이 기록만 더한 뒤에도 같다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`. 두 파일은 수정하지 않는다. `reference/v0.3-rc1/**`도 수정하지 않는다. 저장소의 Move 매니페스트는 `reference/v0.3-rc1/sui/Move.toml` 하나다. Sui 프레임워크 rev는 `808640d9b49aecf29d8e6f46033c15eca236efa7` 그대로다.
HEAD:docs/decisions/TL4_THREAT_MODEL_20261009.md:9:잠금 blob 둘은 작업 전 요구값과 일치했다. 이 기록과 하네스를 더한 뒤에도 같아야 한다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`. 두 파일은 수정하지 않는다. `reference/v0.3-rc1/**`도 수정하지 않는다.
HEAD:docs/decisions/TL5_ACTIVATION_DECISION_PROPOSAL_20261009.md:32:| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
HEAD:docs/decisions/TL5_ACTIVATION_DECISION_PROPOSAL_20261009.md:33:| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |
HEAD:docs/decisions/TL_PRICE_SOURCE_NOT_NEEDED_20261009.md:7:잠금 blob 둘은 작업 전 요구값과 일치했다. 이 기록만 더한 뒤에도 같다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`. 두 파일은 수정하지 않는다. `reference/v0.3-rc1/**`도 수정하지 않는다.
HEAD:docs/decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md:31:- 잠금 blob은 작업 전 요구값과 일치했다: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:docs/decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md:207:# 69564b166f0c27f9af5d8422f0a466b18d74c20f, b607996c83a119c349f1cc90469ac1ba82764e20
HEAD:docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md:8:- Locked blobs verified before and after the work (`git hash-object`): `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`. The checker recomputes both on every run.
HEAD:docs/status/AI_DELEGATION_LAYER_MATRIX.md:10:- Locked blobs verified at that base: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. This node does not touch them.
HEAD:docs/status/ASTRA_DECISION_SHEETS_KO.md:22:  `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
HEAD:docs/status/ASTRA_DECISION_SHEETS_KO.md:24:  `b607996c83a119c349f1cc90469ac1ba82764e20`. 이 노드는 두 파일을 수정하지 않는다.
HEAD:docs/status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md:29:  `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
HEAD:docs/status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md:31:  `b607996c83a119c349f1cc90469ac1ba82764e20`. 이 노드는 두 파일을 수정하지 않는다.
HEAD:docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md:10:Locked blobs before work: kernel lib `69564b166f0c27f9af5d8422f0a466b18d74c20f`; quarantine test `b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:10:- Locked blobs: `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`. Checked before work; the checker rehashes raw bytes read-only. The [validation record](../../validation/2026-10-26-plan-contract-invariants-evidence-map/README.md) records commands and after checks.
HEAD:docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:84:- **F-B1 — class B, historical anchor drift.** Contract §2 explicitly pins commit 0394a36a655b86bacb568b055d377d4c4fd91185. Its STATE_LIFECYCLE blob e953c4870aaeee24b13c75a8647c50609720ae01, ADR blob 07c36869e7b68fff10b02e6c59d7119df56d0785 and kernel README blob 900866ee99a71254fb7da1ad2aa4640477ac550c differ from current 8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d, 054bc714b3c475fb8536df8d2d788b42e8c74b6c and 788896ed3e00bae3d06d26b7e2ce999a00ff1029 respectively. Historical pins are preserved; no old CI transfers to these current sources. Owner: contract owner.
HEAD:docs/status/CURRENT_CAPABILITY_REGISTER.md:257:`runtime/crates/kix-kernel/src/lib.rs = 69564b166f0c27f9af5d8422f0a466b18d74c20f`;
HEAD:docs/status/CURRENT_CAPABILITY_REGISTER.md:258:`runtime/crates/kix-kernel/tests/quarantine_capacity.rs = b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:11:Locked blobs before work: `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`. Both must remain byte-identical.
HEAD:docs/status/I12_REVIEW_PACK.md:20:  `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
HEAD:docs/status/I12_REVIEW_PACK.md:22:  `b607996c83a119c349f1cc90469ac1ba82764e20`. This node does not touch them.
HEAD:docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md:10:- Locked blobs before work: `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`. Checker recomputes both.
HEAD:docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md:9:- Current source Git blobs: STATE_LIFECYCLE = `8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d`; ADR-0001 = `054bc714b3c475fb8536df8d2d788b42e8c74b6c`. [CONTRACT_INVARIANTS §2](../contracts/CONTRACT_INVARIANTS.md#2-exact-existing-contract-anchors) pins historical lifecycle `e953c4870aaeee24b13c75a8647c50609720ae01` and ADR `07c36869e7b68fff10b02e6c59d7119df56d0785`. This is source-version drift, recorded as a characterization; historical pins are preserved. This map reads the current clauses, without transferring old CI evidence.
HEAD:docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md:10:- Locked blobs before work: `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`. The checker rehashes raw bytes read-only. The [validation record](../../validation/2026-10-26-plan-lifecycle-adr-clause-evidence-map/README.md) records the after check.
HEAD:docs/status/LOCK_ENFORCEMENT.md:17:- `src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
HEAD:docs/status/LOCK_ENFORCEMENT.md:18:- `tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`
HEAD:docs/status/LOCK_ENFORCEMENT.md:62:잠금 소스의 blob은 그대로입니다. `lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
HEAD:docs/status/LOCK_ENFORCEMENT.md:63:`quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`입니다.
HEAD:docs/status/OPEN_USER_DECISIONS_20261022.md:46:  `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
HEAD:docs/status/OPEN_USER_DECISIONS_20261022.md:48:  `b607996c83a119c349f1cc90469ac1ba82764e20`. 이 노드는 두 파일을 수정하지 않는다.
HEAD:docs/status/ORIGINAL_32_STATUS.md:70:| K | c8267d1c2bdbcd732aa46401fe059b92d8ae72a6 | runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f | 35047176862, 35047176861 |
HEAD:docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:11:Locked blobs before work: kernel lib `69564b166f0c27f9af5d8422f0a466b18d74c20f`; quarantine test `b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md:10:- Locked v4 lib.rs blob: `69564b166f0c27f9af5d8422f0a466b18d74c20f`; quarantine_capacity.rs blob: `b607996c83a119c349f1cc90469ac1ba82764e20`. Checker recomputes these bytes on each run.
HEAD:docs/status/PR11_PRESERVATION.md:57:- overlay에 사용한 기존 커널 blob: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
HEAD:docs/status/PR11_PRESERVATION.md:81:- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
HEAD:docs/status/PR11_PRESERVATION.md:82:- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:8:- Locked blobs verified before and after the work (`git hash-object`): `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`. The checker recomputes both on every run.
HEAD:docs/status/RS0_REVIEW_PACK.md:19:  `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
HEAD:docs/status/RS0_REVIEW_PACK.md:21:  `b607996c83a119c349f1cc90469ac1ba82764e20`. This node does not touch them.
HEAD:docs/status/TOKEN_LEGAL_REVIEW_BRIEF_KO.md:7:잠금 blob은 [AGENTS.md](../../AGENTS.md) §4의 요구값과 같다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`. 두 파일과 `reference/v0.3-rc1/**`는 수정하지 않는다.
HEAD:docs/status/V5_TRANSITION_EVIDENCE_MAP.md:8:- Locked blobs verified before and after the work (`git hash-object`): `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`. The checker recomputes both on every run.
HEAD:docs/tasks/DEVIN_FIRST_BATCH_E4_AUDIT.md:26:  - blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`
HEAD:docs/tasks/DEVIN_FIRST_BATCH_E4_AUDIT.md:28:  - blob `b607996c83a119c349f1cc90469ac1ba82764e20`
HEAD:docs/tasks/TASK_003C1_EVIDENCE_GATES.md:20:- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
HEAD:docs/tasks/TASK_003C1_EVIDENCE_GATES.md:21:- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:docs/tasks/TASK_003C1_EVIDENCE_GATES.md:22:- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`: `d37ea7df55423c83bedee16bf12bdc8dd61f7cae`.
HEAD:docs/tasks/TASK_003C1_EVIDENCE_GATES.md:23:- `runtime/crates/kix-kernel/tests/support/model_v4.rs`: `f020860b86933bf7511befccdb833b0c532b3629`.
HEAD:docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md:64:- `runtime/crates/kix-kernel/src/lib.rs` → `69564b166f0c27f9af5d8422f0a466b18d74c20f`
HEAD:docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md:65:- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` → `b607996c83a119c349f1cc90469ac1ba82764e20`
HEAD:docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md:66:- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs` → `d37ea7df55423c83bedee16bf12bdc8dd61f7cae`
HEAD:docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md:67:- `runtime/crates/kix-kernel/tests/support/model_v4.rs` → `f020860b86933bf7511befccdb833b0c532b3629`
HEAD:exploration/stage4/budget.py:40:    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:exploration/stage4/budget.py:41:    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
HEAD:runtime/crates/kix-kernel/README.md:8:Locked kernel Git blob: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
HEAD:runtime/crates/kix-kernel/README.md:9:Locked quarantine-test Git blob: `b607996c83a119c349f1cc90469ac1ba82764e20`.
HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs:8:const LOCKED_KERNEL: &str = "69564b166f0c27f9af5d8422f0a466b18d74c20f";
HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs:9:const LOCKED_QUARANTINE: &str = "b607996c83a119c349f1cc90469ac1ba82764e20";
HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs:10:const LOCKED_EDGE: &str = "d37ea7df55423c83bedee16bf12bdc8dd61f7cae";
HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs:11:const LOCKED_MODEL: &str = "f020860b86933bf7511befccdb833b0c532b3629";
HEAD:runtime/crates/kix-kernel/tests/contract_invariants.rs:17:const LOCKED: &str = "69564b166f0c27f9af5d8422f0a466b18d74c20f";
HEAD:runtime/crates/kix-kernel/tests/e4_state_model.rs:30:const LOCKED_KERNEL: &str = "69564b166f0c27f9af5d8422f0a466b18d74c20f";
HEAD:runtime/crates/kix-kernel/tests/e4_state_model.rs:31:const LOCKED_TEST: &str = "b607996c83a119c349f1cc90469ac1ba82764e20";
HEAD:runtime/crates/kix-kernel/tests/performance_harness.rs:192:        kernel_blob: "69564b166f0c27f9af5d8422f0a466b18d74c20f",
HEAD:runtime/crates/kix-kernel/tests/performance_harness.rs:193:        quarantine_blob: "b607996c83a119c349f1cc90469ac1ba82764e20",
HEAD:runtime/crates/kix-kernel/tests/performance_harness.rs:194:        contract_edge_blob: "d37ea7df55423c83bedee16bf12bdc8dd61f7cae",
HEAD:runtime/crates/kix-kernel/tests/performance_harness.rs:195:        model_v4_blob: "f020860b86933bf7511befccdb833b0c532b3629",
HEAD:runtime/crates/kix-kernel/tests/performance_harness.rs:211:    assert!(json.contains("69564b166f0c27f9af5d8422f0a466b18d74c20f"));
HEAD:runtime/crates/kix-kernel/tests/performance_harness.rs:212:    assert!(json.contains("b607996c83a119c349f1cc90469ac1ba82764e20"));
HEAD:runtime/crates/kix-kernel/tests/performance_harness.rs:213:    assert!(json.contains("d37ea7df55423c83bedee16bf12bdc8dd61f7cae"));
HEAD:runtime/crates/kix-kernel/tests/performance_harness.rs:214:    assert!(json.contains("f020860b86933bf7511befccdb833b0c532b3629"));
HEAD:scripts/check_adapter_identity_map.py:63:    KERNEL_LIB: '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:scripts/check_adapter_identity_map.py:64:    KERNEL_QC: 'b607996c83a119c349f1cc90469ac1ba82764e20',
HEAD:scripts/check_bcs1_evidence_map.py:17:        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:scripts/check_bcs1_evidence_map.py:19:        'b607996c83a119c349f1cc90469ac1ba82764e20',
HEAD:scripts/check_contract_invariants_evidence_map.py:18:        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:scripts/check_contract_invariants_evidence_map.py:20:        'b607996c83a119c349f1cc90469ac1ba82764e20',
HEAD:scripts/check_feature_semantics_evidence_map.py:70:        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:scripts/check_feature_semantics_evidence_map.py:72:        'b607996c83a119c349f1cc90469ac1ba82764e20',
HEAD:scripts/check_integration_gate_contract_evidence_map.py:88:        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:scripts/check_integration_gate_contract_evidence_map.py:90:        'b607996c83a119c349f1cc90469ac1ba82764e20',
HEAD:scripts/check_lifecycle_adr_evidence_map.py:23:        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:scripts/check_lifecycle_adr_evidence_map.py:25:        'b607996c83a119c349f1cc90469ac1ba82764e20',
HEAD:scripts/check_performance_measurement_evidence_map.py:22:        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:scripts/check_performance_measurement_evidence_map.py:24:        'b607996c83a119c349f1cc90469ac1ba82764e20',
HEAD:scripts/check_readiness_evidence_map.py:71:    KERNEL_LIB: '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:scripts/check_readiness_evidence_map.py:72:    KERNEL_QC: 'b607996c83a119c349f1cc90469ac1ba82764e20',
HEAD:scripts/check_sdk_client.py:31:SOURCE_BLOB = '619ae21c82ca3df5661bd3831613f15fa65225ff'
HEAD:scripts/check_toss_card_profile_evidence_map.py:22:        '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:scripts/check_toss_card_profile_evidence_map.py:24:        'b607996c83a119c349f1cc90469ac1ba82764e20',
HEAD:scripts/check_v5_transition_evidence_map.py:69:    KERNEL_LIB: '69564b166f0c27f9af5d8422f0a466b18d74c20f',
HEAD:scripts/check_v5_transition_evidence_map.py:70:    KERNEL_QC: 'b607996c83a119c349f1cc90469ac1ba82764e20',
exit: 0
```

### Command 239 — stop attribution

```text
$ sha256sum /workspace/kix-run/wt/plan-perf-probe-fail-closed-and-release-repro/DECISION_REQUIRED.md
e3e2c6143c019b9b0ca704a4be6e4e6e26910fcb4acd568acd745975a80d272b  /workspace/kix-run/wt/plan-perf-probe-fail-closed-and-release-repro/DECISION_REQUIRED.md
exit: 0
```

### Command 240 — stop source lines

````text
$ nl -ba /workspace/kix-run/wt/plan-perf-probe-fail-closed-and-release-repro/DECISION_REQUIRED.md
     1	# DECISION_REQUIRED — perf probe contract-edge frozen pin drift
     2
     3	Node: `plan-perf-probe-fail-closed-and-release-repro` (planner run `1793078707`, not program mode). Observed `origin/main` and HEAD: `9ed15a7adc93359e99bb5c3512a3ca20c77cb264`. Evidence: [validation record](validation/2026-10-27-plan-perf-probe-fail-closed-and-release-repro/README.md).
     4
     5	## What happened
     6
     7	The node ran the release example once, as its contract procedure describes:
     8
     9	```
    10	cargo run --manifest-path runtime/Cargo.toml -p kix-kernel --example r1_perf_probe --release --locked -- .local/perf/plan-perf-probe-fail-closed-and-release-repro 8192 4096 1000
    11	```
    12
    13	It exited with status 1: `Error: "frozen blob mismatch; refusing to write unbound performance evidence"`. It wrote no output directory and no measurements.
    14
    15	The cause is the example-specific pin `LOCKED_EDGE` in `runtime/crates/kix-kernel/examples/r1_perf_probe.rs`:
    16
    17	| File | Pinned | Current |
    18	|---|---|---|
    19	| `runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | `d37ea7df55423c83bedee16bf12bdc8dd61f7cae` (set at `9e8f489`, 2026-09-18, historical Task 004) | `8533d6419077d6a073d16ca2fce3a7d461a4de5b` |
    20
    21	The merged nodes `plan-plan-contract-invariants-s5-availability` (`7ba8003`) and `plan-plan-contract-invariants-s5-precedence-m` (`41abd14`) appended tests to that file on 2026-10-27 and did not update the pin. No test or CI runs the release example, so nothing reported the drift. The other three pins, including the two AGENTS §4 locks and `LOCKED_MODEL`, still match.
    22
    23	The node's STOP rule says: if the edge or model pin no longer matches, record the refusal as a finding and stop with DECISION_REQUIRED rather than re-pinning. The pin was not changed.
    24
    25	## What is needed
    26
    27	The required value of `LOCKED_EDGE`, or a change to which blobs the release example must gate on. Until then, X-RELEASE-REPRO, X-OUTPUT-FILES and BD-RUN-VALUES cannot leave NOT_RUN on current `main`.
    28
    29	## Options
    30
    31	- **A. Re-pin in a separate task.** A new task, branch, session and PR updates `LOCKED_EDGE` to the current blob, with owner authorization, then runs the release example once and records the eleven files and `binding.json`. The two AGENTS §4 locks stay unchanged. Cost: the pin goes stale again whenever `contract_edge_cases.rs` changes, unless a check is added.
    32	- **B. Bind but do not gate on the example-specific blobs.** Record the edge and model blobs in `binding.json` but refuse only on the two AGENTS §4 locks. This changes the contract clause `잠금 blob이 필요한 값과 다르면 예시는 증거 파일을 쓰지 않고 실패한다` as it applies to four blobs, so it needs a contract decision.
    33	- **C. Run against a historical tree** where all four pins match (before `7ba8003`). That measures old test sources, so it is not current evidence.
    34	- **D. Leave the three release rows NOT_RUN** and take no action.
    35
    36	## Recommendation
    37
    38	**A**, as a separate task. Optionally that task, or another one, adds a cheap test or checker rule that compares `LOCKED_EDGE` and `LOCKED_MODEL` with the current blobs, so future drift fails CI instead of failing silently at release time. Any such checker or CI change needs its own scope.
    39
    40	## Who decides
    41
    42	The User (repository owner). This node's builder does not re-pin, does not change the contract, and does not report merge-ready for the release part. The BD-FAIL-CLOSED part (pure gate plus synthetic-hash refusal tests) is complete and does not depend on this decision.
exit: 0
````

### Command 241 — first-parent log

```text
$ git log --first-parent --merges '--format=%H %s' origin/main
8e4813e868961adbabb7d1ee450a346f8fb6add1 Merge pull request #321 from SUNBURN-Golden/agent/kix-plan-ci-test-suite-discovery-guard
9ed15a7adc93359e99bb5c3512a3ca20c77cb264 Merge pull request #320 from SUNBURN-Golden/agent/kix-plan-v5-kernel-only-contract-invariant-histor
9d50fb660248b66a5959f48f7dc96e68c9d5530b Merge pull request #319 from SUNBURN-Golden/agent/kix-plan-plan-perf-harness-kernel-construction-co
70b976c0b8db686b1d21ff0831c275abf77a3d0a Merge pull request #318 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-s5-precedence-m
d016caee4ae40f28f531809359ee77ac22db0073 Merge pull request #317 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-s5-availability
876f41067bc7eb70bcd6ebd9c744c11b46f046b6 Merge pull request #316 from SUNBURN-Golden/agent/kix-plan-plan-perf-harness-map-json-csv-closure-2
eb1caf8285c174697d78834246a304ffe9006427 Merge pull request #315 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-f-b3-reply-asse
035d5705c93b318a49941ce5f7410f843360c427 Merge pull request #314 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-closure-20261027
09470db220965390edeecdb75f56f8c827dd15b6 Merge pull request #313 from SUNBURN-Golden/agent/kix-plan-plan-evidence-map-rollup-check
d2b748aef0c7b4af5bef23c771c6bce22b52905f Merge pull request #312 from SUNBURN-Golden/agent/kix-plan-plan-integration-gate-map-offline-closur
e00e68e680d586346abada94500955abfe938ca3 Merge pull request #311 from SUNBURN-Golden/agent/kix-plan-plan-feature-ir-validator-matrix-closure
58dd527ff53097f5231e89f25ebdf3e94586ee65 Merge pull request #310 from SUNBURN-Golden/agent/kix-plan-plan-feature-ir-money-profile-precedence
118fc28862a6828b80166433bac6f5476037629d Merge pull request #309 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-inv3-sensitivit
ae6b905104d0cb2022001fb32ad98b1a6b3046ec Merge pull request #308 from SUNBURN-Golden/agent/kix-plan-plan-perf-harness-map-partial-closure
a8bc9e853f3b0d82c5c4ee2d0bb4620ac36662e4 Merge pull request #307 from SUNBURN-Golden/agent/kix-plan-plan-integration-gate-map-offline-checke
a176c1f22c0af21500cb52a777bc889b808e561c Merge pull request #306 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-addendum-20261026-sd
23391ab50e0467bc7b234c55e98614713d531f58 Merge pull request #305 from SUNBURN-Golden/agent/kix-plan-plan-integration-gate-contract-clause-ev
22d05a0c82693ad4575a72c2d342b4e47114447f Merge pull request #304 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-addendum-bcs1-checke
9fd4d4836ab4d7eb666ebd4ff2ac0708870d7a58 Merge pull request #303 from SUNBURN-Golden/agent/kix-plan-plan-feature-semantics-v1-evidence-map
412e1ed7bc740599227567f60bf315bb7ecab818 Merge pull request #302 from SUNBURN-Golden/agent/kix-plan-plan-rs4-l2-option-impact-inventory
fc11cdf0150e54ed38bb363f2ded7238c48c6e53 Merge pull request #301 from SUNBURN-Golden/agent/kix-plan-plan-ci-checker-wiring-guard
ff1a955815a054f2345a2e06939f2c84bfc29be6 Merge pull request #300 from SUNBURN-Golden/agent/kix-plan-plan-performance-measurement-clause-evid
1f01a9321c641c7a7fafa2a33e4350a2fa711730 Merge pull request #299 from SUNBURN-Golden/agent/kix-plan-plan-bcs1-contract-clause-evidence-map
18aefc8f7c0dd13b7249e0d80304f3b97459fa3a Merge pull request #298 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-addendum-20261026-ai
957f75d75ea4854eba117d66d07663133f0b7b2c Merge pull request #297 from SUNBURN-Golden/agent/kix-plan-plan-toss-card-profile-evidence-map
1bb000bd125a1e8ecdd033cea01733d58588199e Merge pull request #296 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-evidence-map
54a785b864d629d623afc36ed807d9daebaf9285 Merge pull request #295 from SUNBURN-Golden/agent/kix-plan-plan-lifecycle-adr-clause-evidence-map
944cb16f3ade5a395c0febe84fd47d5c16dc0fa3 Merge pull request #294 from SUNBURN-Golden/agent/kix-plan-plan-primary-fee-pf-c05-isolation-tests
a38e1679449e74186c5a4e3d19b6cb79f6b791d5 Merge pull request #293 from SUNBURN-Golden/agent/kix-plan-ai-delegation-contract-clause-evidence-m
a0db1e226e27b1c5f60ee938fb528ff795907056 Merge pull request #292 from SUNBURN-Golden/agent/kix-plan-product-contract-map-partial-closure
01f6c04c71dac27fab5d17017f4e837c076218c6 Merge pull request #291 from SUNBURN-Golden/agent/kix-plan-primary-price-fee-contract-clause-eviden
92d08e755dfe362ed224112c8dada6c5fcea17d4 Merge pull request #290 from SUNBURN-Golden/agent/kix-plan-plan-register-index-crosswalk-sync-20261
22df2e96d1a7de4d0de371a1f64776e80af9d999 Merge pull request #289 from SUNBURN-Golden/agent/kix-plan-ci-wire-product-contract-evidence-checke
c7762c2724d5d28fd2e5e4f00cc5aae4f1f7908f Merge pull request #288 from SUNBURN-Golden/agent/kix-plan-primary-fee-split-offline-differential
53c16b226346f2df824f93a5756a080acd489ec1 Merge pull request #287 from SUNBURN-Golden/agent/kix-plan-credit-f04-contract-clause-evidence-map
a329ec07ac52ec15bff6c48079115d81ace5ab67 Merge pull request #286 from SUNBURN-Golden/agent/kix-plan-bra-contract-clause-evidence-map
c0fc5b4aed4da32284d9879ad21ef6b584db01d2 Merge pull request #285 from SUNBURN-Golden/agent/kix-plan-settlement-contract-clause-evidence-map
590e544b3d097ba3de2fc573deae43b15bc39773 Merge pull request #284 from SUNBURN-Golden/agent/kix-audit15-reference-test-sibling-path-guard
fe08e4134b2f2e58f48b636bdae7440d8cdb70dc Merge pull request #283 from SUNBURN-Golden/agent/kix-audit15-open-decisions-closure-20261025
ff88c441f36cde5b581ba29ce4c46ac47f22b218 Merge pull request #282 from SUNBURN-Golden/agent/kix-audit15-plan-section5-quote-completeness
0db660a1085ca179c341c89129eeda763977b1fb Merge pull request #281 from SUNBURN-Golden/agent/kix-audit15-plan-register-index-crosswalk-sync-20261
d6a6a10f3f5fbaf31f54ad676a9b5e36c0e3d313 Merge pull request #280 from SUNBURN-Golden/agent/kix-plan-plan-restore-fingerprint-equivalence
4480c9db7be539abd5a99e640b5a25c7eef8cafe Merge pull request #279 from SUNBURN-Golden/agent/kix-plan-plan-aid-rejection-atomicity
41a799987fe3a6a207abcce75045265c5796e1e4 Merge pull request #278 from SUNBURN-Golden/agent/kix-plan-plan-resale-admission-rejection-atomicit
99f30c2d641646d653b62383b213452fd0a0498b Merge pull request #277 from SUNBURN-Golden/agent/kix-plan-plan-bra-aid-returned-data-isolation
5a09a325e2f6415b7fe638d0dbcd826b4d45fb86 Merge pull request #276 from SUNBURN-Golden/agent/kix-plan-plan-register-index-sync-20261024
7327a00a68ef6efa81a795173af5e4572ccd90ef Merge pull request #275 from SUNBURN-Golden/agent/kix-plan-plan-reward-snapshot-isolation
a7e6febded343fe0fd43df2059874525194efecf Merge pull request #274 from SUNBURN-Golden/agent/kix-plan-plan-rs-map-gap-closure-batch-2
f50047a902f9e4f2e6a25e904f6f89ad758eb8c0 Merge pull request #272 from SUNBURN-Golden/agent/kix-audit14-audit14-loop-node-crosswalk-refresh
08ced25441171b2423e6399f04dae14ca0a0a3f8 Merge pull request #271 from SUNBURN-Golden/agent/kix-audit14-audit14-open-decisions-closure-addendum
2d2e93eb14fe41bafaf2dbaa91f02d861c8be8b5 Merge pull request #270 from SUNBURN-Golden/agent/kix-audit14-audit14-plan-register-index-sync-2026102
c7b470fc39ad6f6aa6ad59c18b5595cde41a7200 Merge pull request #269 from SUNBURN-Golden/agent/kix-plan-plan-bra-section9-inline-error-code-cove
a3f0fea3160fdea2f59fa8658573be173e242074 Merge pull request #268 from SUNBURN-Golden/agent/kix-plan-readiness-receipt-audit-tests
f4df0d8ce0253e7b9755f7eb77e857b2d49057e0 Merge pull request #267 from SUNBURN-Golden/agent/kix-plan-booking-resale-admission-seeded-property
fc28ad4eda7e49f34324d46253dfd950533740db Merge pull request #266 from SUNBURN-Golden/agent/kix-plan-readiness-conformance-negative-controls
afe7ded7abc1b6e6cc65c8b179c2d6dac009c891 Merge pull request #265 from SUNBURN-Golden/agent/kix-plan-fsm-returned-data-isolation
fecb5e993c986080c63b4de41be5c5f476592610 Merge pull request #264 from SUNBURN-Golden/agent/kix-plan-owner-stop-handoff-addendum
1d8d228e6fa5cabacf341dd6add0890e8fe95421 Merge pull request #263 from SUNBURN-Golden/agent/kix-plan-readiness-migration-edge-tests
471728e6488719be471eebb3ca8c30ab2948c444 Merge pull request #262 from SUNBURN-Golden/agent/kix-plan-rs-summary-arithmetic-tests
3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af Merge pull request #261 from SUNBURN-Golden/agent/kix-audit13-plan-register-sync-20261023
2393988eeca984f12f0819ac56b6870be1a5832f Merge pull request #260 from SUNBURN-Golden/agent/kix-audit13-ledger-index-count-fix
16aa6d528c2b2a519d99e724b986717fc090b1e3 Merge pull request #259 from SUNBURN-Golden/agent/kix-plan-plan-settlement-credit-rejection-atomici
d84cc50f78a37420ca9d12752ac23f9f9b51c5fc Merge pull request #258 from SUNBURN-Golden/agent/kix-plan-plan-open-user-decisions-ledger-20261022
56d5f59468969825e0e2cd22f6803ebb5e6fb662 Merge pull request #257 from SUNBURN-Golden/agent/kix-plan-plan-rs-offline-suite-evidence-sync
f1734e00e5a167dc18bfff1a873994bee124a3f7 Merge pull request #256 from SUNBURN-Golden/agent/kix-plan-plan-rs4-load-host-conditions-recorder
1a69364eca0e2a219854c443f8183a9b0e733a2d Merge pull request #255 from SUNBURN-Golden/agent/kix-plan-plan-ci-wire-stage5-host-preflight-selft
8e85ef4e14c2615a94b8efca6acd60ea4fe52fb0 Merge pull request #254 from SUNBURN-Golden/agent/kix-plan-plan-register-index-sync-20261022
f6558996c611f74b88c60928f5b285c553303c14 Merge pull request #253 from SUNBURN-Golden/agent/kix-plan-rs-verifier-binding-offline-tests
1c129f1a5fd73636c30c90a33ecfb9e4adf21217 Merge pull request #252 from SUNBURN-Golden/agent/kix-plan-rs-mint-wrapper-offline-tests
9eb6b5f932cae5f4f1b431ef79c9f15874db1c36 Merge pull request #251 from SUNBURN-Golden/agent/kix-plan-rs-admission-packet-offline-tests
93cec6aaf12f22bf8aefc0453fe545b6bd38b819 Merge pull request #248 from SUNBURN-Golden/agent/kix-plan-rs-offline-test-entrypoint
a2a2e29ceefd50952454c6b378363b31be84c3b4 Merge pull request #247 from SUNBURN-Golden/agent/kix-plan-v5-evidence-citation-guard
e9caa181278048cdd0c403929d00a03d5ecd3ab4 Merge pull request #246 from SUNBURN-Golden/agent/kix-plan-rs-ptau-header-tests
20b692b0e7de91f70693d15b14ff5c5c52fc21cb Merge pull request #245 from SUNBURN-Golden/agent/kix-plan-rs-spend-witness-offline-tests
4e5c30cc6779ea8b7d26fa40fdde6c84adfd44b7 Merge pull request #243 from SUNBURN-Golden/agent/kix-plan-rs-zk-encoding-regressions
b761bd60f45f224b4c5db5e3af6963eb6e7dc4d5 Merge pull request #242 from SUNBURN-Golden/agent/kix-plan-rs-manifest-offline-regressions
8b92eb42353d5ca1058227671b3abda3142643c3 Merge pull request #241 from SUNBURN-Golden/agent/kix-plan-rs-witness-ci-wiring
45ec626e2ffcd1cd47aa982622877873b5297139 Merge pull request #240 from SUNBURN-Golden/agent/kix-plan-rs-witness-offline-regressions
9b462fd2cd6890cd0d8fbc2930f2cc54255e2915 Merge pull request #239 from SUNBURN-Golden/agent/kix-plan-readiness-checker-partial-fixture
26f1b9535db24a6b2e9c28753f561d4d6a271815 Merge pull request #236 from SUNBURN-Golden/agent/kix-plan-plan-astra-decision-sheets-rs-stage5
e9f6fc0d880b9f74213791b36df65f63ad88c1c5 Merge pull request #238 from SUNBURN-Golden/agent/kix-audit9-stdlib-step-comment-accuracy
eef11daa33332c2ddfd75ab3045a8caa3b84513f Merge pull request #237 from SUNBURN-Golden/agent/kix-audit9-delegated-exec-ga-late-capture-mirror
e2313ab473ea1b5a7b5b9246a564749188c1c2c8 Merge pull request #235 from SUNBURN-Golden/agent/kix-plan-plan-kix-types-boundary-fixtures
059410cd85bf944142175fbd70364f7cc54ea196 Merge pull request #234 from SUNBURN-Golden/agent/kix-plan-plan-readiness-contract-evidence-map
91d2e507362a79834c09790d9f379ee15f2a1453 Merge pull request #233 from SUNBURN-Golden/agent/kix-plan-plan-reward-wrap-conformance
4e3ce63eaca8ab766c9c88adc712554fb0027d36 Merge pull request #232 from SUNBURN-Golden/agent/kix-plan-plan-register-index-sync-20261021
a114b5bd67164dd1264bc4ad838566809b5bc0b4 Merge pull request #231 from SUNBURN-Golden/agent/kix-plan-settlement-multi-payee-refund-corpus
6f7559470bf2d555bbd80d0ae5d5f8a008e798f7 Merge pull request #230 from SUNBURN-Golden/agent/kix-plan-rs4-load-measurement-gap-report
aac2e72d8d5df86032ec2154172f724d07ebbcf1 Merge pull request #229 from SUNBURN-Golden/agent/kix-plan-read-model-contract-fixture-prep
70000ed8a189b8b3b92a4a858d7cce1ed43e5d7b Merge pull request #228 from SUNBURN-Golden/agent/kix-plan-token-reward-rejection-atomicity
154e9aae3da1bf0044dad606fcfd7e2fb6b3f8df Merge pull request #227 from SUNBURN-Golden/agent/kix-plan-stage5-host-preflight-checker
2c7bc7dd7d4831b0ab3c0ce5e394999a7f72de12 Merge pull request #226 from SUNBURN-Golden/agent/kix-plan-plan-ai-delegation-wrap-conformance
99c2655d38c283497b92dc24ba84a2ae6a5461fb Merge pull request #225 from SUNBURN-Golden/agent/kix-plan-plan-v5-transition-evidence-map
b8c8d1057e8124fef09dc2301fdc841015f22b4a Merge pull request #224 from SUNBURN-Golden/agent/kix-plan-plan-token-reward-readiness-wrap
6cdff624203a9610ed9b84fafec8dad07995c414 Merge pull request #223 from SUNBURN-Golden/agent/kix-plan-plan-adapter-identity-evidence-map
b3f1c6c1f943dc5faccaa9451aee55fa7305dc4c Merge pull request #222 from SUNBURN-Golden/agent/kix-plan-plan-register-index-sync-20261020
01a86f66f1a2a0de98ae00f89e49d45ec07ec8da Merge pull request #221 from SUNBURN-Golden/agent/kix-plan-rs-grant-cut-order-tests
08119a41b7c8088a0e9d40bd35228af33d795643 Merge pull request #220 from SUNBURN-Golden/agent/kix-plan-bra-fsm-error-code-coverage
77da4bcc37e227c549929740a30e4ac544efe4db Merge pull request #219 from SUNBURN-Golden/agent/kix-plan-bra-reservation-rejection-atomicity
fe8f12832e01828a1cba80aec908d6c9971cffcf Merge pull request #218 from SUNBURN-Golden/agent/kix-plan-tl-predicate-evidence-map
fe1f8666c4e50f7740bfe48641d3015fb66ef7fc Merge pull request #217 from SUNBURN-Golden/agent/kix-plan-rs-model-gap-closure
39146a44187af4b43ac57148661bc3af2fb3104f Merge pull request #216 from SUNBURN-Golden/agent/kix-plan-v5-lifecycle-seeded-model-test
90d320325a601e1f604cd901703fd2a5094ca527 Merge pull request #215 from SUNBURN-Golden/agent/kix-plan-readiness-crash-point-sweep
306dfa1261eb02881d1914b34d6510fc698a9979 Merge pull request #214 from SUNBURN-Golden/agent/kix-plan-contract-error-code-coverage
5587afb34cdf9df51b981bcea4a9507250e70528 Merge pull request #213 from SUNBURN-Golden/agent/kix-plan-plan-rs-im-evidence-map
9eb6b9ff24c6ca5825a3d999c81932a38ae79f02 Merge pull request #212 from SUNBURN-Golden/agent/kix-plan-plan-delegated-exec-seeded-differential
ed1d48d52d943f000511573b78ebcfbf3cf5c114 Merge pull request #211 from SUNBURN-Golden/agent/kix-plan-plan-ai-delegation-seeded-property-suite
e291a88211c45ee7285fd8abebcc6ef92bc39f23 Merge pull request #210 from SUNBURN-Golden/agent/kix-audit8-loop-node-canonical-crosswalk
85acc3399a23e87ee4092693840c4e0a620867a0 Merge pull request #209 from SUNBURN-Golden/agent/kix-audit8-readiness-conformance-sweep-limit-note
08b317e5096893432116e41c8312697793500cfe Merge pull request #208 from SUNBURN-Golden/agent/kix-audit8-rs-map-rs-c01-issuercap-open-cell
4da9f7762beddf1a93d95cf26e55d7bf64316711 Merge pull request #207 from SUNBURN-Golden/agent/kix-audit8-plan-register-index-sync-20261017
244595db1524cbb1a01148baa07d6d28cd1b8dc6 Merge pull request #206 from SUNBURN-Golden/agent/kix-plan-plan-booking-resale-adopt-issued-atomici
7bdc99933c804b417b94d9dba40f13d370861cab Merge pull request #205 from SUNBURN-Golden/agent/kix-plan-plan-readiness-journal-byte-sweep
492a85d36fc79aa31d3938bd44024b73dd70dfad Merge pull request #204 from SUNBURN-Golden/agent/kix-plan-feature-semantics-v1-edge-fixtures
5eb95eabcac8b71e0c6c92b4fb322a0e4fe5bb45 Merge pull request #203 from SUNBURN-Golden/agent/kix-plan-credit-f04-seeded-property-suite
9d0860c870e4a06f6b8e876cbee6446f50b22b15 Merge pull request #202 from SUNBURN-Golden/agent/kix-plan-settlement-seeded-property-suite
9f0177ab45cf3ca704ecf5a152b3c1785c8f22a7 Merge pull request #201 from SUNBURN-Golden/agent/kix-plan-rs-predicate-evidence-map
543c1438ce044479fd9646bc5e1cde933a153a4c Merge pull request #200 from SUNBURN-Golden/agent/kix-plan-delegation-layer-gap-matrix
624b28d024279bd077e1247f37566333457750bd Merge pull request #199 from SUNBURN-Golden/agent/kix-plan-ci-wire-i12-proof-ids-check
9d1ff76377fd7c65911c1fb7cb7b515a55489e2d Merge pull request #198 from SUNBURN-Golden/agent/kix-audit7-docs-index-allowlist-prune
2497471dfab21ffd68d600e6ce508e5d6d65bae5 Merge pull request #197 from SUNBURN-Golden/agent/kix-audit7-plan-register-index-sync-20261016b
aca49f6e5498291c1f221185df1ee5cdbf333342 Merge pull request #196 from SUNBURN-Golden/agent/kix-plan-feature-ir-plan-limit-edge-tests
a013cb0c471be0422a4a70d6b98e86c03f7131fa Merge pull request #194 from SUNBURN-Golden/agent/kix-plan-plan-register-index-sync-20261016
ea867668696d6b1114a443d0fe4e840d96b948f6 Merge pull request #193 from SUNBURN-Golden/agent/kix-ai-delegation-execution-decision
47eed4b01b93dc4b00e102729bad1c74abdbae95 Merge pull request #192 from SUNBURN-Golden/agent/kix-testnet-key-management-decision
751c51bdff661673eb2edb9de0dea8f6cbdac2e0 Merge pull request #190 from SUNBURN-Golden/agent/kix-rs-4-l1
10e44d40abd878736b900d768f925725c95a8cd0 Merge pull request #189 from SUNBURN-Golden/agent/kix-audit6-docs-index-check-validation-records
2ae8f1d0774befb0d71eb07f2e3d7454d3fcdc64 Merge pull request #188 from SUNBURN-Golden/agent/kix-audit6-rs1-state-answer-archive
52bd45eff0d77280406a819e62e33212ca50370f Merge pull request #187 from SUNBURN-Golden/agent/kix-audit6-rs-profile-revision-log-0-2
50af6096a84f72c8c1249f23279dab0b279e4c82 Merge pull request #186 from SUNBURN-Golden/agent/kix-audit6-plan-index-sync-20261014
9c4da8d53947a8ca049b6284fa5ca915fb5947ec Merge pull request #185 from SUNBURN-Golden/agent/kix-audit6-register-sync-v5-rs-20261014
ced0e2f42c0491753db91acf87bd61574eb37ce4 Merge pull request #184 from SUNBURN-Golden/agent/kix-rs-3b
adcddc510a66ff70725084c0846830c29ef9ebbe Merge pull request #183 from SUNBURN-Golden/agent/kix-rs-3a
bd367efcc9127663b902b973850ffafc179469df Merge pull request #182 from SUNBURN-Golden/agent/kix-rs-2
dd92e1146ec8eb7024da6c0f62aa721bdc1be780 Merge pull request #181 from SUNBURN-Golden/agent/kix-rs-1-issuercap-probe
7b6a293e903845ff9c06a19f9a02c075d1790089 Merge pull request #180 from SUNBURN-Golden/agent/kix-rs-1
4813388b5bcde72c298c7392ff5230316da44470 Merge pull request #179 from SUNBURN-Golden/agent/kix-k-stage2-v5-impl
ab42cfef43a40c6b86fd3f22b69f00e134cc472e Merge pull request #176 from SUNBURN-Golden/agent/kix-audit5-docs-index-check-ci-wire
2862f34b588e70841a57762d8ce756fd240f5e95 Merge pull request #175 from SUNBURN-Golden/agent/kix-audit5-plan-index-sync-20261013-b
aba875635f682bb9914e0dee016ced58e130cc04 Merge pull request #174 from SUNBURN-Golden/agent/kix-audit5-read-model-source-map-checker-decouple
db9152ab1c5ef113b8727749d4309ec70505480f Merge pull request #173 from SUNBURN-Golden/agent/kix-plan-docs-index-coverage-check
3b8067d48cbda967cbf531258215c5243b96fbcd Merge pull request #172 from SUNBURN-Golden/agent/kix-plan-read-model-source-map
cb59612b847fc2e6ef71810202be5e2ca5f76724 Merge pull request #171 from SUNBURN-Golden/agent/kix-plan-i12-review-pack
5e8ee3f1882d97f1c442fe485407e51822ec22ce Merge pull request #170 from SUNBURN-Golden/agent/kix-plan-offline-doc-checks-ci
1eb7d7d2978950073973a43e495ec5e31c5f543e Merge pull request #169 from SUNBURN-Golden/agent/kix-plan-astra-decision-sheets-listvalues-v5-rs0
77517f0c74cd892ca299cacf987cbab64a03337d Merge pull request #168 from SUNBURN-Golden/agent/kix-plan-rs0-review-pack
ba352dfe9789af89983e9c1b1a303461ea240016 Merge pull request #167 from SUNBURN-Golden/agent/kix-plan-register-nontl-rows-sync
3ce6e4975b7f439d67482451bb47a22c940add26 Merge pull request #166 from SUNBURN-Golden/agent/kix-tl-5-decision
18b80a79614b3a5866f61728b0935294360cfa85 Merge pull request #165 from SUNBURN-Golden/agent/kix-audit4-audit4-plan-s5-index-f04-criteria-toss-p
a0e16328c1b4939458b2abe5b4b5167b79a15c26 Merge pull request #164 from SUNBURN-Golden/agent/kix-audit4-audit4-tl-plan-index-register-sync
5e20a467160148ad5c2debfe357dfb8da084a30a Merge pull request #163 from SUNBURN-Golden/agent/kix-audit4-audit4-policy-deepening-owner-decision-r
4e2122a3f61a0feea2c43035c1ae834e7097e429 Merge pull request #162 from SUNBURN-Golden/agent/kix-tl-4
6bdd571fcb88496c98e25b32213c60017e209198 Merge pull request #159 from SUNBURN-Golden/agent/kix-tl-3-onchain
02b1bf202b926c3b99cb39b360a50b2a75d3f744 Merge pull request #156 from SUNBURN-Golden/agent/kix-settlement-policy-deepening
31eac0637a324244aeca00e849fdb0f7c685232e Merge pull request #161 from SUNBURN-Golden/agent/kix-toss-sandbox-conformance-plan
d7549d1473258dda617e241fff22bcbd697fbb17 Merge pull request #160 from SUNBURN-Golden/agent/kix-f04-real-funds-lift-criteria
9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1 Merge pull request #158 from SUNBURN-Golden/agent/kix-f04-mock-deepening
28f263b5839921b729c2729c8ff5041f57d306ec Merge pull request #157 from SUNBURN-Golden/agent/kix-booking-resale-admission-deepening
17c8a7dc66e49b090067b94ff7bc68cb6d79c5ee Merge pull request #155 from SUNBURN-Golden/agent/kix-audit3-openapi-promotion-owner-decision-record
1c9488499bbd954f1c14e5f571f24f3f1d976338 Merge pull request #154 from SUNBURN-Golden/agent/kix-audit3-tl-docs-plan-index-sync
eb14da2a6c5b5366cd4aed855bd453dcb4d79a42 Merge pull request #153 from SUNBURN-Golden/agent/kix-audit3-ci-wire-token-reward-suite
d63768ddf276c60173aa2c933f4feef3449a9452 Merge pull request #152 from SUNBURN-Golden/agent/kix-openapi-catalogue-promotion
c2cde86e21a6e5ba6f24a56548636db6d0a34c6f Merge pull request #151 from SUNBURN-Golden/agent/kix-tl-legal-brief
fff19605f0ccff71b6f24e61f1f8114b5c0ddd57 Merge pull request #150 from SUNBURN-Golden/agent/kix-tl-3-offchain
1cb2d26c4b6d8cc7aa2d362bf017e4d30f5a2080 Merge pull request #149 from SUNBURN-Golden/agent/kix-tl-2
ad3cee9e6aa68aa14c3b35901f66b6cab40cf75a Merge pull request #148 from SUNBURN-Golden/agent/kix-tl-coin-lock-adr
841408e77065c841ea73e2cf04fe8c03fbd35f5d Merge pull request #147 from SUNBURN-Golden/agent/kix-tl-1
28539987d1e676f0724081c41b22db51e731a967 Merge pull request #146 from SUNBURN-Golden/agent/kix-tl-price-source-contract
5714603158ddac1a5dcbe2e645c902e26f2b20a9 Merge pull request #145 from SUNBURN-Golden/agent/kix-tl-0
51d83808478e56c81c6f43e2a13450d435e922e6 Merge pull request #144 from SUNBURN-Golden/agent/kix-audit2-gate-browser-access-test-determinism
e2a029d8ac3af7575888dac22fc4bf173ebec232 Merge pull request #143 from SUNBURN-Golden/agent/kix-audit2-k-decisions-plan-sync-20261009
b6cc9978c64b1ff54f822ea930424b5d78dfca2a Merge pull request #142 from SUNBURN-Golden/agent/kix-k-a-integration-decision
57a3e3049c84a2ac0112371594e9bb4b85a8296f Merge pull request #141 from SUNBURN-Golden/agent/kix-k-a-reestimate
bb193efb5d238581096372c8a20bee1271dfe4df Merge pull request #140 from SUNBURN-Golden/agent/kix-k-stage4-adoption-decision
6e54e723d582e88ae89df309eb144d4664c7e1f5 Merge pull request #139 from SUNBURN-Golden/agent/kix-k2-retention-proposal
a483ab1777ad0c3e15ff71798822cbf6b3666f83 Merge pull request #138 from SUNBURN-Golden/agent/kix-k-stage2-v5-design-decision
a059bd69eae321ccfeb5940f3d675b962103d361 Merge pull request #137 from SUNBURN-Golden/agent/kix-k1-evidence-close
ae869f38438d8174103171ec741a41376aee60df Merge pull request #136 from SUNBURN-Golden/agent/kix-k1-cut-proof
7be6b7507201674599f5d35aaa329cdbeb75ab38 Merge pull request #135 from SUNBURN-Golden/agent/kix-gate-browser-access
eb1f63022482fd9b7c35d1a58924ee51625f56b7 Merge pull request #134 from SUNBURN-Golden/agent/kix-audit1-ci-discover-ai-delegation-tests
861bff26279a4ef257648c7e25c11bc20712037a Merge pull request #133 from SUNBURN-Golden/agent/kix-audit1-docs-index-sync-20261008
5363a49edb0e8d5c75d24df6176e0c0a8e09842c Merge pull request #132 from SUNBURN-Golden/agent/kix-gate-browser-access-decision
771545ae4b64f069396667f399b5200c44fd9af0 Merge pull request #131 from SUNBURN-Golden/agent/kix-readiness-extensions
90c6e7a6bfa305764a9b66df3cafdae038b5139f Merge pull request #130 from SUNBURN-Golden/agent/kix-ai-delegation-contract-mock
d71b4117741f596e2b618ed1c32a42597bc0980b Merge pull request #129 from SUNBURN-Golden/agent/kix-move-primary-price-fee
2ead88aec7f5fc36ed802c32c98f3053367c7ede Merge pull request #127 from SUNBURN-Golden/agent/kix-read-model-contract
547d9fd5cd0e2d54e4fd61050d6f4fff530f3750 Merge pull request #126 from SUNBURN-Golden/agent/kix-tl-a
68a58aedb358ff2506001f6c46cd618706c023af Merge pull request #125 from SUNBURN-Golden/agent/kix-rs-0
5561fc965803935be1894457ebc762a3d36489f5 Merge pull request #124 from SUNBURN-Golden/agent/kix-k1-adapter-event-identity
a74e7c459d3be6754ac3cf24503e43c7bc312358 Merge pull request #123 from SUNBURN-Golden/agent/kix-p-sdk-0
8dc60dfee3816864f4f45394ff31bb8070e76274 Merge pull request #122 from SUNBURN-Golden/agent/kix-k-stage4-local-exploration
7481b0e16ce9b903abbffa62249bb91cd9e63cfe Merge pull request #120 from BeautifulMind-JT/aiops/native-c103391b9cbd4fc5
2554173ebdda0922aaf7a0bc7ea773075187a3d9 Merge pull request #119 from BeautifulMind-JT/aiops/native-c90c4b5d293b4944
4052dccfcbeaa95c1f21c2973ef530e5d5905759 Merge pull request #118 from BeautifulMind-JT/aiops/native-1d03058d26ee4ee0
403d3e29413b1e78c5da945cd33389b50d4514a4 Merge pull request #117 from BeautifulMind-JT/aiops/native-b35b31e9104c48e0
ecb78a446e988fb40615f3e62da08714ef5786f5 Merge pull request #116 from BeautifulMind-JT/aiops/native-4a3e8bab0579456d
0b8b6b484c1b5d49b7cb285e780481061c2b16c7 Merge pull request #115 from BeautifulMind-JT/aiops/native-c2a8b366c436443d
5155ed307c71917ba3442fc5e1fc4cb950efefdc Merge pull request #114 from BeautifulMind-JT/aiops/native-1c37130ab62a476b
9aa464b6b9d89cdf1da65f828b55e6e97bf7bef0 Merge pull request #113 from BeautifulMind-JT/aiops/native-a144f560a0a44ba7
c8b806ebd0f959814acfd184edadf244bf18d1b4 Merge pull request #112 from BeautifulMind-JT/aiops/native-f3441d8b23f143b7
b6373c2448ac947d245851abf7c4d9a00e70f5c9 Merge pull request #89 from BeautifulMind-JT/codex/expanded-program-start-20261002
6427b3b86ebf7140ba9b9bd4bbd6532ecd9662e3 Merge pull request #88 from BeautifulMind-JT/codex/program-expansion-detailed-20261002
dd0a501248e092c2a4475088d94d7449b7bd98b5 Merge pull request #81: roadmap R-1 and KIX program registration draft (Astra Fable PASS_WITH_NOTES at 2e9c7b5)
78b78b1b4a4ffe92de461edd351235ce858b335a Merge pull request #80 from BeautifulMind-JT/claude/kix-protocol-commerce-aiops-review-ydlupm
5cf416832fe8660c74c9ef7cc30f576875a94e78 Merge pull request #79 from BeautifulMind-JT/claude/focused-lovelace-vx68yk
13134e49704815457fef444ce61d781b5a424713 Merge pull request #78 from BeautifulMind-JT/claude/awesome-lovelace-bf9ual
ba5bd063daf87a365d4bf6f795c8940ee7fcfb17 Merge pull request #77 from BeautifulMind-JT/claude/awesome-lovelace-bf9ual
4e313363fd725c8f8b9664cdd1ae4e5f9cff3528 Merge pull request #76 from BeautifulMind-JT/claude/awesome-lovelace-bf9ual
b8b7455cf346d98689238d3eeaf07fc139fa6a7d Merge pull request #75 from BeautifulMind-JT/claude/awesome-lovelace-bf9ual
60e7683ad28d5264f398d7965c06bfd840aa7338 Merge pull request #74 from BeautifulMind-JT/claude/awesome-lovelace-bf9ual
cfeb0d69561103302b6fdc3d10842768c3420151 Merge pull request #73 from BeautifulMind-JT/claude/awesome-lovelace-bf9ual
34a722d26fa894366c26bac9de4187c598fbf3eb Merge pull request #72 from BeautifulMind-JT/ops/cp-opt-002-policy
fac35fff3a17cbbddd0abb7371e4952045884986 Merge pull request #57 from BeautifulMind-JT/docs/task-005-mega-commerce-program-20260925
ccd8e43b57a0f840d863786b317eaccdf76c4c6f Merge pull request #54 from BeautifulMind-JT/docs/task-004-perf-measurement-20260925
52a9b5cbf7777df55d2d2062cb8d99d862b423bb Merge pull request #71 from BeautifulMind-JT/agent/prod-readiness-20260926
3b6bdd26f61bb828af3781946b63a3a3fa03187b Merge pull request #70 from BeautifulMind-JT/agent/admission-harden-20260926
5c59d95ec52379e010f8e9c660da11cfa6498def Merge pull request #69 from BeautifulMind-JT/agent/http-integration-gate-20260926
8c1a4db7cfe70b0e772a2ef0f24492967c84f7f1 Merge pull request #68 from BeautifulMind-JT/agent/credit-depth-20260926
ef942b7713c7468e8851c6b372b64d42b5333ad8 Merge pull request #67 from BeautifulMind-JT/agent/resale-depth-20260926
a47828dd4517c5a7397e09eb6b563a64e4265c82 Merge pull request #66 from BeautifulMind-JT/agent/reservation-ticketing-depth-20260926
85145eb33799a7c712890ff81708def8a7d61ee5 Merge pull request #64 from BeautifulMind-JT/agent/settlement-depth-fsm-20260926
a744b0a036d7e1edb48416871af20cd182f23df4 Merge pull request #63 from BeautifulMind-JT/agent/openapi-contract-only-20260926
b61e48d965e7ed3f1c5f4fcd5ad863b961ce4e28 Merge pull request #62 from BeautifulMind-JT/agent/wave5-credit-f04-mock-20260926
4ec0f93255b9be1715784f1d2a5edde411cc96c6 Merge pull request #61 from BeautifulMind-JT/agent/wave4-booking-resale-admission-20260926
9e2dad654d7c6e46efade803018ef3e2cfea5e0a Merge pull request #60 from BeautifulMind-JT/agent/wave3-settlement-f01-f03-20260926
a2814923bc671889da49984a2c95964340a1506d Merge pull request #59 from BeautifulMind-JT/agent/wave2-rights-zk-gate-20260926
19bad99eee02214ffa053cace64dc7877e02d204 Merge pull request #58 from BeautifulMind-JT/agent/task-004-perf-measurement-20260925
729a106add049ad1a75b90f99c00b6e0ccb8a67d Merge pull request #52 from BeautifulMind-JT/ops/cp-extract-001
ec3f6db0d613385bfdf2392a4295f0099be1eec6 Merge pull request #48 from BeautifulMind-JT/ops/enable-grok-build-canary
a99045baece02d603f9badf38fbe6ae5d8dbedbe control-plane: enable runtime (Astra C2a) with RUNTIME_PATHS-aligned SHA (#47)
ce3284fa6a5b1c426a0a89c545e818fd74e1984b control-plane: set activated_runtime_sha to attested 6d543a7 (runtime still off) (#46)
6d543a7c4540f42d099294d9da0679a9548b1817 Merge pull request #45 from BeautifulMind-JT/test/cp-e1-fault-injection-103003c
103003c77cbf07b991e0905ce730b0604c15a0c0 Merge pull request #44 from BeautifulMind-JT/fix/cp-slack-fixture-36
db7dcd69ac98e9171c37f1f213267849c4cd86b6 Merge pull request #43 from BeautifulMind-JT/ops/activation-control-ba366de-preflight
a7b086e88e570c8321e1c87ada1986a253ea8755 Merge pull request #42 from BeautifulMind-JT/fix/cp-boundary-003-residual-ba366de
ba366def267df55fab09a3c630830c32e3758941 Merge pull request #41 from BeautifulMind-JT/fix/cp-rollout-004-kix-upstream-findings
4b8ba575c65be183adb71f012310885d8fe70980 Merge pull request #39 from BeautifulMind-JT/devin/cp-boundary-003
6dbf8dfed6ee790e2ee56b49a75b727edd9db977 Merge pull request #29 from BeautifulMind-JT/ops/agent-control-plane-20260921
5cc58d296d428e5d21f8f467b25f12b78dc44789 Merge pull request #30 from BeautifulMind-JT/agent/task-003c1-evidence-gates-20260921
6332bca0f54cc2114d986b24ab218ace33a5df12 Merge PR #24: Task 003-B E-4 property expansion
c3a2b304641dcd2373e0267030dc69ea48d55f5e Merge PR #23: Task 003-A E-4 model schema
db02ae11bf4a1d7705f31b328c627714f91e1c78 Merge PR #22: STATE_LIFECYCLE 0.6 precedence
a83d09cd99017875f583383e6ebbabc46a6a63eb Merge PR #21: formalize KIX agent governance
a4ad7343f30e5f81eede30fa200f129b8c946981 Merge PR #20: Devin Task 001 E-4 contract edge-case audit
5fffc196be37425366b2a6ec7faeec1db9bbca46 Merge PR #19: preserve release body and record preservation provenance
1fb0c8b50ac4de5693996412337d36cd6683bdf2 Merge PR #18: preserved Sui research and R2 handoff requirements
46b4a5e06bce4ce1c97e66d8839fa6f92d35e530 Merge PR #17: lifecycle 0.5 and alternate authority scope
3cbb8df3a466fe171d7261f9090c324a458af3f6 Merge PR #16: LC-TERM conditions and approval, contract version 0.3
73f324a00f345e120014718b67a7c03ecbf1198a Merge PR #15: provisional Toss card scope and document consistency
94376835ea4fc818619fc79e2be4df7d4947496a Merge PR #14: align documentation entrypoints with current approvals
bf6c2be37e8c55778f4fe378634f7895fd69a327 Merge PR #13: R1 v4 verification baseline, contracts and measurement apparatus
31e60b2269e90cba6da9a1a41dacf039f5662c30 Merge PR #12: preserve locked R1 v4 baseline and audit lineage
eff0f44f28d0232c6177c40b2f2feb2aa951ae09 Merge PR #1: fix Groth16 fixture setup and reject stale rights
exit: 0
```

### Command 242 — merge 314

```text
$ git show -s --format=%H%n%P%n%s 035d5705c93b318a49941ce5f7410f843360c427
035d5705c93b318a49941ce5f7410f843360c427
09470db220965390edeecdb75f56f8c827dd15b6 bce1c9e870f90fd180e0780fdb38acd50f8a5c24
Merge pull request #314 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-closure-20261027
exit: 0
```

### Command 243 — merge paths 314

```text
$ git diff '035d5705c93b318a49941ce5f7410f843360c427^1' 035d5705c93b318a49941ce5f7410f843360c427 --name-status
M	docs/README.md
A	docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md
A	validation/2026-10-27-plan-open-decisions-closure-20261027/README.md
exit: 0
```

### Command 245 — merge 315

```text
$ git show -s --format=%H%n%P%n%s eb1caf8285c174697d78834246a304ffe9006427
eb1caf8285c174697d78834246a304ffe9006427
035d5705c93b318a49941ce5f7410f843360c427 90d827dc09132d9ceb4b7e721c1f5617b9e47fc8
Merge pull request #315 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-f-b3-reply-asse
exit: 0
```

### Command 246 — merge paths 315

```text
$ git diff 'eb1caf8285c174697d78834246a304ffe9006427^1' eb1caf8285c174697d78834246a304ffe9006427 --name-status
M	docs/README.md
M	docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md
M	runtime/crates/kix-kernel/tests/contract_invariants.rs
A	validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md
exit: 0
```

### Command 248 — merge 316

```text
$ git show -s --format=%H%n%P%n%s 876f41067bc7eb70bcd6ebd9c744c11b46f046b6
876f41067bc7eb70bcd6ebd9c744c11b46f046b6
eb1caf8285c174697d78834246a304ffe9006427 87f40aa89d77f924481ff1dd6cc828d81a7b8b46
Merge pull request #316 from SUNBURN-Golden/agent/kix-plan-plan-perf-harness-map-json-csv-closure-2
exit: 0
```

### Command 249 — merge paths 316

```text
$ git diff '876f41067bc7eb70bcd6ebd9c744c11b46f046b6^1' 876f41067bc7eb70bcd6ebd9c744c11b46f046b6 --name-status
M	docs/README.md
M	docs/status/EVIDENCE_MAP_ROLLUP.md
M	docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md
M	runtime/crates/kix-kernel/tests/performance_harness.rs
A	validation/2026-10-27-plan-perf-harness-map-json-csv-closure-2/README.md
exit: 0
```

### Command 251 — merge 317

```text
$ git show -s --format=%H%n%P%n%s d016caee4ae40f28f531809359ee77ac22db0073
d016caee4ae40f28f531809359ee77ac22db0073
876f41067bc7eb70bcd6ebd9c744c11b46f046b6 7ba8003f4a18bbd622ce87b1cfb0fa856e4a4178
Merge pull request #317 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-s5-availability
exit: 0
```

### Command 252 — merge paths 317

```text
$ git diff 'd016caee4ae40f28f531809359ee77ac22db0073^1' d016caee4ae40f28f531809359ee77ac22db0073 --name-status
M	docs/README.md
M	docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md
M	runtime/crates/kix-kernel/tests/contract_edge_cases.rs
A	validation/2026-10-27-plan-contract-invariants-s5-availability/README.md
exit: 0
```

### Command 254 — merge 318

```text
$ git show -s --format=%H%n%P%n%s 70b976c0b8db686b1d21ff0831c275abf77a3d0a
70b976c0b8db686b1d21ff0831c275abf77a3d0a
d016caee4ae40f28f531809359ee77ac22db0073 41abd142e7b16a6ab1370cf001b3fccb4b720900
Merge pull request #318 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-s5-precedence-m
exit: 0
```

### Command 255 — merge paths 318

```text
$ git diff '70b976c0b8db686b1d21ff0831c275abf77a3d0a^1' 70b976c0b8db686b1d21ff0831c275abf77a3d0a --name-status
M	docs/README.md
M	docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md
M	runtime/crates/kix-kernel/tests/contract_edge_cases.rs
A	validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md
exit: 0
```

### Command 257 — merge 319

```text
$ git show -s --format=%H%n%P%n%s 9d50fb660248b66a5959f48f7dc96e68c9d5530b
9d50fb660248b66a5959f48f7dc96e68c9d5530b
70b976c0b8db686b1d21ff0831c275abf77a3d0a c677f09bea37bb1fe00a768b9ef369dfa5dc6d41
Merge pull request #319 from SUNBURN-Golden/agent/kix-plan-plan-perf-harness-kernel-construction-co
exit: 0
```

### Command 258 — merge paths 319

```text
$ git diff '9d50fb660248b66a5959f48f7dc96e68c9d5530b^1' 9d50fb660248b66a5959f48f7dc96e68c9d5530b --name-status
M	docs/README.md
M	docs/status/EVIDENCE_MAP_ROLLUP.md
M	docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md
M	runtime/crates/kix-kernel/tests/performance_harness.rs
M	runtime/crates/kix-kernel/tests/support/perf_probe.rs
A	validation/2026-10-27-plan-perf-harness-kernel-construction-co/README.md
exit: 0
```

### Command 260 — merge 320

```text
$ git show -s --format=%H%n%P%n%s 9ed15a7adc93359e99bb5c3512a3ca20c77cb264
9ed15a7adc93359e99bb5c3512a3ca20c77cb264
9d50fb660248b66a5959f48f7dc96e68c9d5530b 150180214612b7b6f55bb4f6c49834bd9f5cec88
Merge pull request #320 from SUNBURN-Golden/agent/kix-plan-v5-kernel-only-contract-invariant-histor
exit: 0
```

### Command 261 — merge paths 320

```text
$ git diff '9ed15a7adc93359e99bb5c3512a3ca20c77cb264^1' 9ed15a7adc93359e99bb5c3512a3ca20c77cb264 --name-status
M	docs/README.md
A	runtime/crates/kix-kernel-v5/tests/contract_invariants_v5.rs
A	validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md
exit: 0
```

### Command 263 — merge 321

```text
$ git show -s --format=%H%n%P%n%s 8e4813e868961adbabb7d1ee450a346f8fb6add1
8e4813e868961adbabb7d1ee450a346f8fb6add1
9ed15a7adc93359e99bb5c3512a3ca20c77cb264 e265d30d10e9f18feb7c9fb968e09a5c6260e9ad
Merge pull request #321 from SUNBURN-Golden/agent/kix-plan-ci-test-suite-discovery-guard
exit: 0
```

### Command 264 — merge paths 321

```text
$ git diff '8e4813e868961adbabb7d1ee450a346f8fb6add1^1' 8e4813e868961adbabb7d1ee450a346f8fb6add1 --name-status
M	.github/workflows/protocol.yml
M	docs/README.md
A	scripts/check_ci_test_discovery.py
A	validation/2026-10-27-plan-ci-test-suite-discovery-guard/README.md
exit: 0
```

### Command 266 — edge merge history

```text
$ git log --first-parent --merges --full-history '--format=%H %s' origin/main -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs
70b976c0b8db686b1d21ff0831c275abf77a3d0a Merge pull request #318 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-s5-precedence-m
d016caee4ae40f28f531809359ee77ac22db0073 Merge pull request #317 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-s5-availability
a4ad7343f30e5f81eede30fa200f129b8c946981 Merge PR #20: Devin Task 001 E-4 contract edge-case audit
exit: 0
```

### Command 267 — pin provenance

```text
$ git log --follow '--format=%H %s' -- runtime/crates/kix-kernel/examples/r1_perf_probe.rs
28c9c130e9ab9be017a8302dc1e4a4cbd3cbfffa test: separate v4 perf summaries by outcome and load regime
a4ba244f4170d2823e8f4ca196f0655a077c0e82 test: format only newly introduced first-batch harness sources
7f480fa4e3f18db83605a59cab4ae9b2e405478f test: start approved R1 v4 first batch with independent model and measurement harness
exit: 0
```

### Command 268 — stop named commit

```text
$ git show -s --format=%H%n%P%n%s 9e8f489
9e8f4898cb429e1146ea924d6c254b7fd490a3b2
a4ab8d0119daba974dd59a20d3da05d82bd61118
test(kernel): add contract edge-case audit and evidence note
exit: 0
```

### Command 269 — stop named commit

```text
$ git show -s --format=%H%n%P%n%s 7ba8003
7ba8003f4a18bbd622ce87b1cfb0fa856e4a4178
876f41067bc7eb70bcd6ebd9c744c11b46f046b6
plan-plan-contract-invariants-s5-availability: Contract-based availability examples for CONTRACT_INVARIANTS §5 safe-but
exit: 0
```

### Command 270 — stop named commit

```text
$ git show -s --format=%H%n%P%n%s 41abd14
41abd142e7b16a6ab1370cf001b3fccb4b720900
d016caee4ae40f28f531809359ee77ac22db0073
plan-plan-contract-invariants-s5-precedence-m: Guard-pair error-precedence matrix for CONTRACT_INVARIANTS §5 (S5-PRECED
exit: 0
```

### Command 271 — edge merge diff 317

```text
$ git diff 'd016caee4ae40f28f531809359ee77ac22db0073^1' d016caee4ae40f28f531809359ee77ac22db0073 -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs
diff --git a/runtime/crates/kix-kernel/tests/contract_edge_cases.rs b/runtime/crates/kix-kernel/tests/contract_edge_cases.rs
index d37ea7d..dab3300 100644
--- a/runtime/crates/kix-kernel/tests/contract_edge_cases.rs
+++ b/runtime/crates/kix-kernel/tests/contract_edge_cases.rs
@@ -9,11 +9,20 @@
 //! `docs/contracts/STATE_LIFECYCLE.md` §2/§3/§5,
 //! `runtime/crates/kix-kernel/README.md` "Implemented meaning" and
 //! "Observation reservation and remaining gaps".
+//!
+//! The availability examples at the end answer `docs/contracts/CONTRACT_INVARIANTS.md`
+//! §5 ("incorrect but safe rejections"; "No finite test proves all inputs"). Each
+//! builds a state in which ADR §3/§4/§6/§8, STATE_LIFECYCLE §2/§5.7 and the README
+//! require a reservation to be held, and asserts that it is. They are finite,
+//! source-informed examples (the author knew the locked kernel source), not an
+//! availability proof. Values the contracts leave open (the bundle maximum,
+//! inclusive record limits, exact rejection/error variants, cross-kind
+//! selections) are labelled AGENTS §8 class B characterizations.

 use kix_kernel::{
     CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel, KernelError, Limits,
-    ObservationOutcome, OrderState, ProviderOperation, Rejection, Reserve, ReserveOutcome,
-    SEMANTICS_VERSION, Selection,
+    MAX_BUNDLE, ObservationOutcome, OrderState, ProviderOperation, Rejection, Reserve,
+    ReserveOutcome, SEMANTICS_VERSION, Selection,
 };
 use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

@@ -438,3 +447,416 @@ fn retained_unbound_conflict_bans_the_identity_for_any_future_order() {
         ReserveOutcome::Held(id(6))
     );
 }
+
+// ---------------------------------------------------------------------------
+// CONTRACT_INVARIANTS §5 availability examples (S5-SAFE-REJECT / S5-FINITE).
+// ---------------------------------------------------------------------------
+
+/// Mirrors the CONTRACT_INVARIANTS §4 seat fixture: actual segments [65, 5].
+const SEGMENTS: [u16; 2] = [65, 5];
+/// Mirrors the CONTRACT_INVARIANTS §4 GA fixture capacity.
+const GA_CAPACITY: u32 = 6;
+const ROOMY: Limits = Limits {
+    commands: 32,
+    orders: 32,
+    observations: 32,
+};
+
+fn kernel_with(inventory: Inventory, limits: Limits) -> Kernel {
+    Kernel::new(id(9), fence(), 1, inventory, limits).unwrap()
+}
+
+fn seat_kernel() -> Kernel {
+    kernel_with(Inventory::seats(&SEGMENTS).unwrap(), ROOMY)
+}
+
+fn ga_kernel() -> Kernel {
+    kernel_with(Inventory::general_admission(GA_CAPACITY).unwrap(), ROOMY)
+}
+
+fn seats(n: u8, first: u16, count: u16) -> Reserve {
+    Reserve {
+        selection: Selection::Seats { first, count },
+        ..request(n, first)
+    }
+}
+
+fn ga(n: u8, count: u32) -> Reserve {
+    Reserve {
+        selection: Selection::GeneralAdmission { count },
+        ..request(n, 0)
+    }
+}
+
+fn units(selection: Selection) -> u32 {
+    match selection {
+        Selection::Seats { count, .. } => u32::from(count),
+        Selection::GeneralAdmission { count } => count,
+    }
+}
+
+/// A new command is held: original result, new order in Held owning its
+/// inventory with the exact request, and remaining reduced by exactly its units.
+fn assert_held(k: &mut Kernel, now_ms: u64, r: &Reserve) {
+    let remaining = k.remaining();
+    let reply = k.reserve(ctx(now_ms), r.clone()).unwrap();
+    assert_eq!(reply.original, ReserveOutcome::Held(r.order_id), "{r:?}");
+    assert!(!reply.replayed);
+    let order = k.order(r.order_id).expect("held order is recorded");
+    assert_eq!(order.request, *r);
+    assert_eq!(order.state, OrderState::Held);
+    assert!(order.inventory_owned);
+    assert_eq!(k.remaining(), remaining - units(r.selection));
+}
+
+/// A new command is recorded as a business rejection without creating an
+/// order or allocating any inventory (STATE_LIFECYCLE §2; ADR §4).
+fn assert_rejected(k: &mut Kernel, now_ms: u64, r: &Reserve, reason: Rejection) {
+    let (remaining, orders) = (k.remaining(), k.order_count());
+    let reply = k.reserve(ctx(now_ms), r.clone()).unwrap();
+    assert_eq!(reply.original, ReserveOutcome::Rejected(reason), "{r:?}");
+    assert!(!reply.replayed);
+    assert_eq!((k.remaining(), k.order_count()), (remaining, orders));
+}
+
+fn assert_error_leaves_state(k: &mut Kernel, context: Context, r: Reserve, want: KernelError) {
+    let before = k.clone();
+    assert_eq!(k.reserve(context, r), Err(want));
+    assert_eq!(*k, before);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT. ADR §8 "All-or-none selection must
+/// handle real aisles ... R1 covers contiguous segment selection" and README
+/// "Implemented meaning": "All-or-none contiguous selection inside real
+/// segments". A free range inside one actual segment must be held, including
+/// one ending exactly at the aisle and the whole second segment. The two
+/// MAX_BUNDLE cases are class B characterizations: the README names a maximum
+/// bundle length but no value; the second also crosses the 64-bit word.
+#[test]
+fn free_contiguous_range_inside_one_actual_segment_is_held() {
+    for (first, count) in [(0, 1), (20, 5), (60, 5), (64, 1), (65, 5), (69, 1)] {
+        let mut k = seat_kernel();
+        assert_held(&mut k, 1, &seats(30, first, count));
+        assert_eq!(k.remaining(), 70 - u32::from(count));
+    }
+    // Class B characterization: the public MAX_BUNDLE is the observed maximum.
+    for first in [0, 1] {
+        let mut k = seat_kernel();
+        assert_held(&mut k, 1, &seats(31, first, MAX_BUNDLE));
+        assert_eq!(k.remaining(), 70 - u32::from(MAX_BUNDLE));
+    }
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT. README "Implemented meaning":
+/// "crossing a 64-bit word when appropriate but never crossing an aisle"; ADR
+/// §8 "machine-word boundaries". A free range across seats 63/64 or 127/128
+/// inside one segment is held, including one that fits exactly between two
+/// existing holds and one that ends exactly at the aisle.
+#[test]
+fn word_crossing_range_inside_one_segment_is_held_between_neighbours() {
+    let mut k = seat_kernel();
+    assert_held(&mut k, 1, &seats(30, 63, 2));
+    assert_eq!(k.remaining(), 68);
+
+    let mut k = kernel_with(Inventory::seats(&[200]).unwrap(), ROOMY);
+    assert_held(&mut k, 1, &seats(31, 60, 3));
+    assert_held(&mut k, 2, &seats(32, 66, 2));
+    // Seats 63..66 are exactly the free gap and cross the word at 64.
+    assert_held(&mut k, 3, &seats(33, 63, 3));
+    assert_held(&mut k, 4, &seats(34, 127, 2));
+    assert_eq!(k.remaining(), 200 - 10);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT. README "Implemented meaning": "GA
+/// capacity cannot overdraw"; ADR §8 "R1 covers ... GA capacity". Capacity is
+/// the limit, so a request for exactly the remaining units is held, in one
+/// request or after earlier holds. The seat analogue takes every seat of two
+/// actual segments with bundles inside each segment.
+#[test]
+fn seats_and_general_admission_are_held_up_to_exact_remaining_capacity() {
+    let mut k = ga_kernel();
+    assert_held(&mut k, 1, &ga(30, GA_CAPACITY));
+    assert_eq!(k.remaining(), 0);
+
+    let mut k = ga_kernel();
+    assert_held(&mut k, 1, &ga(31, 1));
+    assert_held(&mut k, 2, &ga(32, 2));
+    assert_eq!(k.remaining(), 3);
+    assert_held(&mut k, 3, &ga(33, 3));
+    assert_eq!(k.remaining(), 0);
+
+    let mut k = kernel_with(Inventory::seats(&[5, 5]).unwrap(), ROOMY);
+    assert_held(&mut k, 1, &seats(34, 0, 5));
+    assert_held(&mut k, 2, &seats(35, 5, 5));
+    assert_eq!(k.remaining(), 0);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT. STATE_LIFECYCLE §5.7 "expire releases
+/// only Held"; ADR §6 a late capture never resurrects an expired order "or
+/// releas[es] inventory now owned by another order", so released inventory
+/// can be owned by another order; README "Implemented meaning". After expiry
+/// releases a hold, a new command, order and operation can take those units,
+/// including a superset of released and never-held seats, while the expired
+/// order stays Expired without inventory. Reuse after cancel_scope is class B:
+/// ADR §7 cancellation is a sticky local fence, and no contract defines reopening.
+#[test]
+fn inventory_released_by_expiry_is_reusable_by_a_new_command() {
+    let mut k = seat_kernel();
+    let old = seats(30, 2, 4);
+    assert_held(&mut k, 1, &old);
+    assert!(k.expire(ctx(EXPIRY), old.order_id).unwrap());
+    assert_eq!(k.remaining(), 70);
+    let new = Reserve {
+        expires_at_ms: 500,
+        ..seats(31, 0, 8)
+    };
+    assert_held(&mut k, EXPIRY + 1, &new);
+    let expired = k.order(old.order_id).unwrap();
+    assert_eq!(expired.state, OrderState::Expired);
+    assert!(!expired.inventory_owned);
+    assert_eq!(k.remaining(), 62);
+
+    let mut k = ga_kernel();
+    let old = ga(32, GA_CAPACITY);
+    assert_held(&mut k, 1, &old);
+    assert!(k.expire(ctx(EXPIRY), old.order_id).unwrap());
+    assert_eq!(k.remaining(), GA_CAPACITY);
+    let new = Reserve {
+        expires_at_ms: 500,
+        ..ga(33, GA_CAPACITY)
+    };
+    assert_held(&mut k, EXPIRY + 1, &new);
+    let expired = k.order(old.order_id).unwrap();
+    assert_eq!(expired.state, OrderState::Expired);
+    assert!(!expired.inventory_owned);
+    assert_eq!(k.remaining(), 0);
+}
+
+/// Unrelated rejections, errors and replays, then the final success. Every
+/// rejected request asks for the target selection, so any partial allocation
+/// would make the final reservation fail.
+fn success_after_noise(
+    mut k: Kernel,
+    holder: Reserve,
+    blocked: Reserve,
+    target: Selection,
+    invalid: [Selection; 2],
+) -> Kernel {
+    let at = |n: u8| Reserve {
+        selection: target,
+        ..request(n, 0)
+    };
+    assert_held(&mut k, 1, &holder);
+    assert_rejected(&mut k, 2, &blocked, Rejection::Unavailable);
+
+    // ADR §3/§5: replay returns the original result and is read-only.
+    let before = k.clone();
+    for (r, original) in [
+        (&holder, ReserveOutcome::Held(holder.order_id)),
+        (&blocked, ReserveOutcome::Rejected(Rejection::Unavailable)),
+    ] {
+        let replay = k.reserve(ctx(3), r.clone()).unwrap();
+        assert!(replay.replayed);
+        assert_eq!(replay.original, original);
+    }
+    assert_eq!(k, before);
+
+    // Recorded business rejections (STATE_LIFECYCLE §2). The exact variants are
+    // class B characterizations; that nothing is allocated is ADR §4.
+    let reused_order = Reserve {
+        order_id: holder.order_id,
+        ..at(40)
+    };
+    assert_rejected(&mut k, 4, &reused_order, Rejection::OrderExists);
+    let reused_payment = Reserve {
+        payment: holder.payment,
+        ..at(41)
+    };
+    assert_rejected(&mut k, 5, &reused_payment, Rejection::OperationAlreadyBound);
+    for (n, selection) in [(42, invalid[0]), (43, invalid[1])] {
+        let r = Reserve {
+            selection,
+            ..request(n, 0)
+        };
+        assert_rejected(&mut k, 6, &r, Rejection::InvalidRequest);
+    }
+    let already_expired = Reserve {
+        expires_at_ms: 7,
+        ..at(44)
+    };
+    assert_rejected(&mut k, 7, &already_expired, Rejection::InvalidRequest);
+
+    // Errors change no state (whole-kernel Eq); variants are class B.
+    let target_request = at(45);
+    let altered = Reserve {
+        expires_at_ms: EXPIRY + 1,
+        ..holder.clone()
+    };
+    assert_error_leaves_state(&mut k, ctx(8), altered, KernelError::CommandConflict);
+    assert_error_leaves_state(
+        &mut k,
+        ctx(0),
+        target_request.clone(),
+        KernelError::ClockRegression,
+    );
+    let stale = Context {
+        fence: ExecutionFence {
+            owner: id(8),
+            generation: 2,
+        },
+        ..ctx(8)
+    };
+    assert_error_leaves_state(
+        &mut k,
+        stale,
+        target_request.clone(),
+        KernelError::ExecutionFenced,
+    );
+    let old_semantics = Context {
+        semantics_version: SEMANTICS_VERSION - 1,
+        ..ctx(8)
+    };
+    assert_error_leaves_state(
+        &mut k,
+        old_semantics,
+        target_request.clone(),
+        KernelError::UnsupportedSemantics,
+    );
+    let foreign = Reserve {
+        id: CommandId {
+            scope: id(77),
+            ..target_request.id
+        },
+        ..target_request.clone()
+    };
+    assert_error_leaves_state(&mut k, ctx(8), foreign, KernelError::WrongScope);
+
+    // The same command identity that only met errors is still a new command.
+    assert_held(&mut k, 9, &target_request);
+    assert_eq!(k.order(blocked.order_id), None);
+    k
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT and S5-FINITE. ADR §3/§5: replay
+/// returns the original result and is read-only; ADR §4 "Every fallible
+/// validation precedes all mutation" (no partial allocation); STATE_LIFECYCLE
+/// §2: business rejections are recorded command results. After a blocked
+/// overlap, replays, order/operation reuse, invalid and expired requests and
+/// guard errors, the still-free target selection must be held, on a seat and
+/// a GA fixture. Cross-kind selections are class B characterizations.
+#[test]
+fn success_follows_unrelated_rejections_errors_and_replays() {
+    let k = success_after_noise(
+        seat_kernel(),
+        seats(30, 10, 3),
+        seats(31, 12, 4),
+        Selection::Seats {
+            first: 13,
+            count: 3,
+        },
+        [
+            Selection::Seats {
+                first: 63,
+                count: 4,
+            },
+            Selection::GeneralAdmission { count: 1 },
+        ],
+    );
+    assert_eq!(k.remaining(), 70 - 6);
+
+    let k = success_after_noise(
+        ga_kernel(),
+        ga(30, 4),
+        ga(31, 3),
+        Selection::GeneralAdmission { count: 2 },
+        [
+            Selection::GeneralAdmission { count: 0 },
+            Selection::Seats { first: 0, count: 1 },
+        ],
+    );
+    assert_eq!(k.remaining(), 0);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT and S5-FINITE. README "Implemented
+/// meaning": bounded commands/orders/observations with no dedupe eviction; ADR
+/// §3 "capacity exhaustion backpressures instead of forgetting"; STATE_LIFECYCLE
+/// §2 rejections are recorded. With the smallest legal limits a reservation is
+/// held, and with three command and two order slots the last of each still
+/// admits a reservation after a recorded rejection. Old results still replay;
+/// only the next new command backpressures. Inclusive limits and the exact
+/// Capacity variant are class B characterizations.
+#[test]
+fn last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection() {
+    let minimal = Limits {
+        commands: 1,
+        orders: 1,
+        observations: 1,
+    };
+    let tight = Limits {
+        commands: 3,
+        orders: 2,
+        observations: 1,
+    };
+    let fixtures = [
+        (
+            Inventory::seats(&SEGMENTS).unwrap(),
+            [seats(30, 0, 2), seats(31, 1, 2), seats(32, 2, 3)],
+            seats(33, 10, 1),
+        ),
+        (
+            Inventory::general_admission(GA_CAPACITY).unwrap(),
+            [ga(30, 3), ga(31, 4), ga(32, 3)],
+            ga(33, 1),
+        ),
+    ];
+    for (inventory, [first, blocked, last], next) in fixtures {
+        let mut k = kernel_with(inventory.clone(), minimal);
+        assert_held(&mut k, 1, &first);
+
+        let mut k = kernel_with(inventory, tight);
+        assert_held(&mut k, 1, &first);
+        assert_rejected(&mut k, 2, &blocked, Rejection::Unavailable);
+        assert_eq!(k.order_count(), 1);
+        assert_held(&mut k, 3, &last);
+        assert_eq!(k.order_count(), 2);
+
+        let before = k.clone();
+        assert!(k.reserve(ctx(4), first.clone()).unwrap().replayed);
+        assert!(k.reserve(ctx(4), blocked.clone()).unwrap().replayed);
+        assert_eq!(k, before);
+        assert_error_leaves_state(&mut k, ctx(4), next, KernelError::Capacity);
+    }
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT. README "Hard boundaries": "The
+/// initial fixture accepts positive-price orders"; STATE_LIFECYCLE §5.7 and §2
+/// (as asserted by expiry_instant_is_treated_consistently_by_every_entry_point):
+/// now_ms >= expires_at_ms is expired, so expires_at_ms = now_ms + 1 is live.
+/// The smallest positive price with a 1 ms TTL is held on both fixtures and is
+/// released exactly at its expiry instant.
+#[test]
+fn smallest_positive_price_and_one_millisecond_ttl_are_held() {
+    let now = 40;
+    for (mut k, selection) in [
+        (
+            seat_kernel(),
+            Selection::Seats {
+                first: 69,
+                count: 1,
+            },
+        ),
+        (ga_kernel(), Selection::GeneralAdmission { count: 1 }),
+    ] {
+        let total = k.remaining();
+        let r = Reserve {
+            selection,
+            amount: amount(1),
+            expires_at_ms: now + 1,
+            ..request(30, 0)
+        };
+        assert_held(&mut k, now, &r);
+        assert!(k.expire(ctx(now + 1), r.order_id).unwrap());
+        assert_eq!(k.order(r.order_id).unwrap().state, OrderState::Expired);
+        assert_eq!(k.remaining(), total);
+    }
+}
exit: 0
```

### Command 272 — edge merge blob transition 317

```text
$ git rev-parse 'd016caee4ae40f28f531809359ee77ac22db0073^1:runtime/crates/kix-kernel/tests/contract_edge_cases.rs' d016caee4ae40f28f531809359ee77ac22db0073:runtime/crates/kix-kernel/tests/contract_edge_cases.rs
d37ea7df55423c83bedee16bf12bdc8dd61f7cae
dab33001dee34f7e773645b3ff17119cfb56a614
exit: 0
```

### Command 273 — edge merge diff 318

```text
$ git diff '70b976c0b8db686b1d21ff0831c275abf77a3d0a^1' 70b976c0b8db686b1d21ff0831c275abf77a3d0a -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs
diff --git a/runtime/crates/kix-kernel/tests/contract_edge_cases.rs b/runtime/crates/kix-kernel/tests/contract_edge_cases.rs
index dab3300..8533d64 100644
--- a/runtime/crates/kix-kernel/tests/contract_edge_cases.rs
+++ b/runtime/crates/kix-kernel/tests/contract_edge_cases.rs
@@ -18,6 +18,14 @@
 //! availability proof. Values the contracts leave open (the bundle maximum,
 //! inclusive record limits, exact rejection/error variants, cross-kind
 //! selections) are labelled AGENTS §8 class B characterizations.
+//!
+//! The error-precedence pairs after them answer the §5 "wrong error precedence"
+//! question (S5-PRECEDENCE). Each arms two public rejection guards on one call,
+//! but only where ADR §3/§5/§6 or STATE_LIFECYCLE §2–§4 decide which one wins,
+//! asserts that outcome with a whole-kernel `Eq` check and shows the losing
+//! guard is live on a clone, a twin or a later valid call. Pairs no contract
+//! orders are class B characterizations in the S5-PRECEDENCE validation
+//! record and are deliberately not asserted here.

 use kix_kernel::{
     CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel, KernelError, Limits,
@@ -860,3 +868,578 @@ fn smallest_positive_price_and_one_millisecond_ttl_are_held() {
         assert_eq!(k.remaining(), total);
     }
 }
+
+// ---------------------------------------------------------------------------
+// CONTRACT_INVARIANTS §5 error-precedence pairs (S5-PRECEDENCE).
+// ---------------------------------------------------------------------------
+
+/// A context under a semantics version other than v4.
+fn old_semantics(now_ms: u64) -> Context {
+    Context {
+        semantics_version: SEMANTICS_VERSION - 1,
+        ..ctx(now_ms)
+    }
+}
+
+/// The owner installed by `replace_owner` in these examples.
+fn next_fence() -> ExecutionFence {
+    ExecutionFence {
+        owner: id(8),
+        generation: 2,
+    }
+}
+
+fn ctx_under(fence: ExecutionFence, now_ms: u64) -> Context {
+    Context {
+        fence,
+        ..ctx(now_ms)
+    }
+}
+
+fn seat_limits(limits: Limits) -> Kernel {
+    kernel_with(Inventory::seats(&[10]).unwrap(), limits)
+}
+
+/// The call fails with `want` and leaves the whole kernel unchanged.
+fn refused<T: PartialEq + std::fmt::Debug>(
+    k: &mut Kernel,
+    want: KernelError,
+    call: impl FnOnce(&mut Kernel) -> Result<T, KernelError>,
+) {
+    let before = k.clone();
+    assert_eq!(call(&mut *k), Err(want));
+    assert_eq!(*k, before);
+}
+
+/// A new command is recorded with `want` as its first result.
+fn recorded(k: &mut Kernel, context: Context, r: Reserve, want: ReserveOutcome) {
+    let reply = k.reserve(context, r).unwrap();
+    assert_eq!(reply.original, want);
+    assert!(!reply.replayed);
+}
+
+/// ADR §6 / addendum A: event 1 first names `a`, then `b`, quarantining both.
+fn quarantine_pair(k: &mut Kernel, a: &Reserve, b: &Reserve, now_ms: u64) {
+    k.observe_capture(ctx(now_ms), capture(a, 1)).unwrap();
+    assert_eq!(
+        k.observe_capture(ctx(now_ms + 1), capture(b, 1)).unwrap(),
+        ObservationOutcome::Conflict
+    );
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, payload conflict × local cancellation.
+/// ADR §3: the same identity with a different payload is a conflict, not a new
+/// command, so ADR §7's fence on new work does not record a BusinessFenced
+/// result for it. A fresh identity is fenced; the original still replays.
+#[test]
+fn altered_payload_conflicts_after_local_cancellation() {
+    let mut k = kernel();
+    let original = request(3, 0);
+    k.reserve(ctx(1), original.clone()).unwrap();
+    k.cancel_scope(ctx(2), 2).unwrap();
+    let altered = Reserve {
+        expected_business_epoch: 2,
+        ..original.clone()
+    };
+    refused(&mut k, KernelError::CommandConflict, |k| {
+        k.reserve(ctx(3), altered)
+    });
+
+    let fenced = ReserveOutcome::Rejected(Rejection::BusinessFenced);
+    recorded(&mut k.clone(), ctx(3), request(4, 1), fenced);
+    let before = k.clone();
+    let replay = k.reserve(ctx(3), original).unwrap();
+    assert!(replay.replayed);
+    assert_eq!(replay.original, ReserveOutcome::Held(id(3)));
+    assert_eq!(k, before);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, payload conflict × full command
+/// records. ADR §3: an altered payload is a conflict on an existing identity,
+/// which needs no new record; capacity backpressure applies to new commands.
+#[test]
+fn altered_payload_conflicts_at_full_command_capacity() {
+    let mut k = seat_limits(Limits {
+        commands: 1,
+        ..ROOMY
+    });
+    let original = request(3, 0);
+    k.reserve(ctx(1), original.clone()).unwrap();
+    let altered = Reserve {
+        selection: Selection::Seats { first: 1, count: 1 },
+        ..original.clone()
+    };
+    refused(&mut k, KernelError::CommandConflict, |k| {
+        k.reserve(ctx(2), altered)
+    });
+
+    refused(&mut k.clone(), KernelError::Capacity, |k| {
+        k.reserve(ctx(2), request(4, 1))
+    });
+    assert!(k.reserve(ctx(2), original).unwrap().replayed);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, payload conflict × unavailable
+/// inventory. ADR §3 conflict, and README "Immutable original outcome replay
+/// before new-attempt availability checks": moving a held command onto taken
+/// seats is a conflict, not a recorded Unavailable result.
+#[test]
+fn altered_payload_conflicts_when_its_selection_is_unavailable() {
+    let mut k = kernel();
+    let holder = request(3, 0);
+    let mover = request(4, 1);
+    k.reserve(ctx(1), holder).unwrap();
+    k.reserve(ctx(2), mover.clone()).unwrap();
+    let onto_holder = Reserve {
+        selection: Selection::Seats { first: 0, count: 1 },
+        ..mover.clone()
+    };
+    refused(&mut k, KernelError::CommandConflict, |k| {
+        k.reserve(ctx(3), onto_holder)
+    });
+
+    let unavailable = ReserveOutcome::Rejected(Rejection::Unavailable);
+    recorded(&mut k.clone(), ctx(3), request(5, 0), unavailable);
+    assert!(k.reserve(ctx(3), mover).unwrap().replayed);
+    assert!(k.order(id(4)).unwrap().inventory_owned);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, payload conflict × quarantine. ADR §3
+/// conflict; ADR §6 a quarantined operation "cannot later gain a fresh
+/// reservation binding". Re-pointing an existing command at a quarantined
+/// operation is a conflict, records no OperationQuarantined result and leaves
+/// the existing order unreviewed.
+#[test]
+fn altered_payload_conflicts_when_its_operation_is_quarantined() {
+    let mut k = kernel();
+    let (a, b, x) = (request(3, 0), request(4, 1), request(5, 2));
+    for (t, r) in [(1, &a), (2, &b), (3, &x)] {
+        k.reserve(ctx(t), r.clone()).unwrap();
+    }
+    quarantine_pair(&mut k, &a, &b, 4);
+    let onto_quarantined = Reserve {
+        payment: b.payment,
+        ..x.clone()
+    };
+    refused(&mut k, KernelError::CommandConflict, |k| {
+        k.reserve(ctx(6), onto_quarantined)
+    });
+
+    let fresh = Reserve {
+        payment: b.payment,
+        ..request(6, 3)
+    };
+    let quarantined = ReserveOutcome::Rejected(Rejection::OperationQuarantined);
+    recorded(&mut k.clone(), ctx(6), fresh, quarantined);
+    assert!(k.reserve(ctx(6), x.clone()).unwrap().replayed);
+    assert!(!k.order(x.order_id).unwrap().review_required);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, payload conflict × UNKNOWN. ADR §3
+/// conflict; ADR §6 and STATE_LIFECYCLE §2 an UNKNOWN operation and its slot
+/// survive the TTL. An altered retry after the deadline is a conflict and does
+/// not record an OperationAlreadyBound result or touch the UNKNOWN order.
+#[test]
+fn altered_payload_conflicts_without_touching_an_unknown_payment() {
+    let mut k = kernel();
+    let unknown = request(3, 0);
+    k.reserve(ctx(1), unknown.clone()).unwrap();
+    k.mark_payment_unknown(ctx(2), unknown.order_id).unwrap();
+    let altered = Reserve {
+        order_id: id(4),
+        selection: Selection::Seats { first: 1, count: 1 },
+        expires_at_ms: 500,
+        ..unknown.clone()
+    };
+    refused(&mut k, KernelError::CommandConflict, |k| {
+        k.reserve(ctx(EXPIRY + 1), altered.clone())
+    });
+    let order = k.order(unknown.order_id).unwrap();
+    assert_eq!(order.state, OrderState::PaymentUnknown);
+    assert!(order.inventory_owned);
+    assert_eq!(k.reserved_observation_count(), 1);
+
+    let fresh = Reserve {
+        id: request(5, 1).id,
+        ..altered
+    };
+    let bound = ReserveOutcome::Rejected(Rejection::OperationAlreadyBound);
+    recorded(&mut k.clone(), ctx(EXPIRY + 1), fresh, bound);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, semantics version × local
+/// cancellation. ADR §5: v4 "rejects other versions", so neither a
+/// BusinessFenced command result nor a ReturnRequired capture is applied under
+/// another version. The same inputs under v4 then meet the cancellation.
+#[test]
+fn unsupported_semantics_records_nothing_after_local_cancellation() {
+    let mut k = kernel();
+    let unknown = request(3, 0);
+    k.reserve(ctx(1), unknown.clone()).unwrap();
+    k.mark_payment_unknown(ctx(2), unknown.order_id).unwrap();
+    k.cancel_scope(ctx(3), 2).unwrap();
+    let fresh = request(4, 1);
+    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
+        k.reserve(old_semantics(4), fresh.clone())
+    });
+    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
+        k.observe_capture(old_semantics(4), capture(&unknown, 1))
+    });
+
+    let fenced = ReserveOutcome::Rejected(Rejection::BusinessFenced);
+    recorded(&mut k, ctx(4), fresh, fenced);
+    assert_eq!(
+        k.observe_capture(ctx(5), capture(&unknown, 1)).unwrap(),
+        ObservationOutcome::ReturnRequired
+    );
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, semantics version × unavailable
+/// inventory. ADR §5: another version is rejected, so no Unavailable result is
+/// recorded; the same identity under v4 is still a new command.
+#[test]
+fn unsupported_semantics_records_no_unavailable_rejection() {
+    let mut k = kernel();
+    k.reserve(ctx(1), request(3, 0)).unwrap();
+    let blocked = request(4, 0);
+    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
+        k.reserve(old_semantics(2), blocked.clone())
+    });
+
+    let unavailable = ReserveOutcome::Rejected(Rejection::Unavailable);
+    recorded(&mut k, ctx(2), blocked, unavailable);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, semantics version × quarantine.
+/// ADR §5 rejects other versions; ADR §6 and addendum A define the v4
+/// quarantine. A conflicting event under another version quarantines nothing,
+/// and a reservation naming a quarantined operation records nothing.
+#[test]
+fn unsupported_semantics_applies_no_quarantine() {
+    let mut k = kernel();
+    let (a, b) = (request(3, 0), request(4, 1));
+    k.reserve(ctx(1), a.clone()).unwrap();
+    k.reserve(ctx(2), b.clone()).unwrap();
+    k.observe_capture(ctx(3), capture(&a, 1)).unwrap();
+    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
+        k.observe_capture(old_semantics(4), capture(&b, 1))
+    });
+    assert_eq!(k.quarantined_operation_count(), 0);
+
+    assert_eq!(
+        k.observe_capture(ctx(4), capture(&b, 1)).unwrap(),
+        ObservationOutcome::Conflict
+    );
+    assert_eq!(k.quarantined_operation_count(), 2);
+    let reused = Reserve {
+        payment: b.payment,
+        ..request(5, 2)
+    };
+    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
+        k.reserve(old_semantics(5), reused.clone())
+    });
+    let quarantined = ReserveOutcome::Rejected(Rejection::OperationQuarantined);
+    recorded(&mut k, ctx(5), reused, quarantined);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, semantics version × UNKNOWN. ADR §5
+/// rejects other versions, so another version neither commits the UNKNOWN
+/// send transition and its slot nor applies the first capture that would
+/// spend that slot.
+#[test]
+fn unsupported_semantics_neither_sends_nor_captures_an_unknown_payment() {
+    let mut k = kernel();
+    let order = request(3, 0);
+    k.reserve(ctx(1), order.clone()).unwrap();
+    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
+        k.mark_payment_unknown(old_semantics(2), order.order_id)
+    });
+    assert_eq!(k.order(order.order_id).unwrap().state, OrderState::Held);
+    assert_eq!(k.reserved_observation_count(), 0);
+
+    k.mark_payment_unknown(ctx(2), order.order_id).unwrap();
+    assert_eq!(k.reserved_observation_count(), 1);
+    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
+        k.observe_capture(old_semantics(3), capture(&order, 1))
+    });
+    assert_eq!(k.order(order.order_id).unwrap().captured, None);
+
+    assert_eq!(
+        k.observe_capture(ctx(3), capture(&order, 1)).unwrap(),
+        ObservationOutcome::PaymentConfirmed
+    );
+    assert_eq!(k.reserved_observation_count(), 0);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, regressed time × local cancellation.
+/// ADR §5: supplied time and monotonicity are validated at the ordered
+/// boundary, so a regressed input is not admitted: no BusinessFenced result is
+/// recorded and no ReturnRequired capture is applied. Valid times then meet the
+/// cancellation.
+#[test]
+fn regressed_time_records_nothing_after_local_cancellation() {
+    let mut k = kernel();
+    let unknown = request(3, 0);
+    k.reserve(ctx(1), unknown.clone()).unwrap();
+    k.mark_payment_unknown(ctx(2), unknown.order_id).unwrap();
+    k.cancel_scope(ctx(10), 2).unwrap();
+    let fresh = request(4, 1);
+    refused(&mut k, KernelError::ClockRegression, |k| {
+        k.reserve(ctx(5), fresh.clone())
+    });
+    refused(&mut k, KernelError::ClockRegression, |k| {
+        k.observe_capture(ctx(5), capture(&unknown, 1))
+    });
+
+    let fenced = ReserveOutcome::Rejected(Rejection::BusinessFenced);
+    recorded(&mut k, ctx(11), fresh, fenced);
+    assert_eq!(
+        k.observe_capture(ctx(12), capture(&unknown, 1)).unwrap(),
+        ObservationOutcome::ReturnRequired
+    );
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, full command records × local
+/// cancellation. STATE_LIFECYCLE §2: business rejections are recorded first
+/// results; ADR §3: bounded records backpressure instead of forgetting. With no
+/// command slot, no BusinessFenced result can be recorded, so the call is
+/// refused unchanged; a twin with free slots records BusinessFenced.
+#[test]
+fn full_command_capacity_backpressures_after_local_cancellation() {
+    let history = |limits| {
+        let mut k = seat_limits(limits);
+        k.reserve(ctx(1), request(3, 0)).unwrap();
+        k.cancel_scope(ctx(2), 2).unwrap();
+        k
+    };
+    let mut full = history(Limits {
+        commands: 1,
+        ..ROOMY
+    });
+    refused(&mut full, KernelError::Capacity, |k| {
+        k.reserve(ctx(3), request(4, 1))
+    });
+
+    let fenced = ReserveOutcome::Rejected(Rejection::BusinessFenced);
+    recorded(&mut history(ROOMY), ctx(3), request(4, 1), fenced);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, stale execution fence × unavailable
+/// inventory. ADR §3/§6: internal fencing stops new internal writes by an old
+/// owner, so the old owner records no Unavailable result; the current owner
+/// does.
+#[test]
+fn stale_execution_fence_records_no_unavailable_rejection() {
+    let mut k = kernel();
+    k.reserve(ctx(1), request(3, 0)).unwrap();
+    k.replace_owner(ctx(2), next_fence()).unwrap();
+    let blocked = request(4, 0);
+    refused(&mut k, KernelError::ExecutionFenced, |k| {
+        k.reserve(ctx(3), blocked.clone())
+    });
+
+    let unavailable = ReserveOutcome::Rejected(Rejection::Unavailable);
+    recorded(&mut k, ctx_under(next_fence(), 3), blocked, unavailable);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, stale execution fence × quarantine.
+/// ADR §3/§6: the old owner's writes are stopped and "the current owner applies
+/// those facts under its current execution fence". An old-fence conflicting
+/// event quarantines nothing, and an old-fence reservation naming the
+/// quarantined operation records nothing; the current owner applies both.
+#[test]
+fn stale_execution_fence_applies_no_quarantine() {
+    let mut k = kernel();
+    let (a, b) = (request(3, 0), request(4, 1));
+    k.reserve(ctx(1), a.clone()).unwrap();
+    k.reserve(ctx(2), b.clone()).unwrap();
+    k.observe_capture(ctx(3), capture(&a, 1)).unwrap();
+    k.replace_owner(ctx(4), next_fence()).unwrap();
+    refused(&mut k, KernelError::ExecutionFenced, |k| {
+        k.observe_capture(ctx(5), capture(&b, 1))
+    });
+    assert_eq!(k.quarantined_operation_count(), 0);
+
+    assert_eq!(
+        k.observe_capture(ctx_under(next_fence(), 5), capture(&b, 1))
+            .unwrap(),
+        ObservationOutcome::Conflict
+    );
+    assert_eq!(k.quarantined_operation_count(), 2);
+    let reused = Reserve {
+        payment: b.payment,
+        ..request(5, 2)
+    };
+    refused(&mut k, KernelError::ExecutionFenced, |k| {
+        k.reserve(ctx(6), reused.clone())
+    });
+    let quarantined = ReserveOutcome::Rejected(Rejection::OperationQuarantined);
+    recorded(&mut k, ctx_under(next_fence(), 6), reused, quarantined);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, stale execution fence × UNKNOWN.
+/// ADR §3/§6: the old owner can neither authorize a send retry nor apply the
+/// late fact; STATE_LIFECYCLE §2: owner change never releases the UNKNOWN
+/// operation or its slot. The current owner may retry and applies the capture.
+#[test]
+fn stale_execution_fence_neither_sends_nor_captures_an_unknown_payment() {
+    let mut k = kernel();
+    let order = request(3, 0);
+    k.reserve(ctx(1), order.clone()).unwrap();
+    k.mark_payment_unknown(ctx(2), order.order_id).unwrap();
+    k.replace_owner(ctx(3), next_fence()).unwrap();
+    refused(&mut k, KernelError::ExecutionFenced, |k| {
+        k.mark_payment_unknown(ctx(4), order.order_id)
+    });
+    refused(&mut k, KernelError::ExecutionFenced, |k| {
+        k.observe_capture(ctx(4), capture(&order, 1))
+    });
+    assert_eq!(k.reserved_observation_count(), 1);
+    assert_eq!(
+        k.order(order.order_id).unwrap().state,
+        OrderState::PaymentUnknown
+    );
+
+    k.mark_payment_unknown(ctx_under(next_fence(), 4), order.order_id)
+        .unwrap();
+    assert_eq!(k.reserved_observation_count(), 1);
+    assert_eq!(
+        k.observe_capture(ctx_under(next_fence(), 5), capture(&order, 1))
+            .unwrap(),
+        ObservationOutcome::PaymentConfirmed
+    );
+    assert_eq!(k.reserved_observation_count(), 0);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, regressed time × unavailable
+/// inventory. ADR §5: a regressed input is not admitted, so no Unavailable
+/// result is recorded; the same identity at a valid time is a new command.
+#[test]
+fn regressed_time_records_no_unavailable_rejection() {
+    let mut k = kernel();
+    k.reserve(ctx(10), request(3, 0)).unwrap();
+    let blocked = request(4, 0);
+    refused(&mut k, KernelError::ClockRegression, |k| {
+        k.reserve(ctx(5), blocked.clone())
+    });
+
+    let unavailable = ReserveOutcome::Rejected(Rejection::Unavailable);
+    recorded(&mut k, ctx(11), blocked, unavailable);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, regressed time × quarantine. ADR §5:
+/// a regressed input is not admitted; ADR addendum A: an admitted conflict
+/// quarantines bound operations even when it returns Capacity. A regressed
+/// conflicting event therefore quarantines nothing, with or without evidence
+/// budget, and a regressed reservation naming the quarantined operation
+/// records nothing.
+#[test]
+fn regressed_time_applies_no_quarantine() {
+    for observations in [ROOMY.observations, 1] {
+        let mut k = seat_limits(Limits {
+            observations,
+            ..ROOMY
+        });
+        let (a, b) = (request(3, 0), request(4, 1));
+        k.reserve(ctx(1), a.clone()).unwrap();
+        k.reserve(ctx(2), b.clone()).unwrap();
+        k.observe_capture(ctx(10), capture(&a, 1)).unwrap();
+        refused(&mut k, KernelError::ClockRegression, |k| {
+            k.observe_capture(ctx(5), capture(&b, 1))
+        });
+        assert_eq!(k.quarantined_operation_count(), 0);
+
+        let admitted = k.observe_capture(ctx(11), capture(&b, 1));
+        if observations == 1 {
+            assert_eq!(admitted, Err(KernelError::Capacity));
+        } else {
+            assert_eq!(admitted, Ok(ObservationOutcome::Conflict));
+        }
+        assert_eq!(k.quarantined_operation_count(), 2);
+        let reused = Reserve {
+            payment: b.payment,
+            ..request(5, 2)
+        };
+        refused(&mut k, KernelError::ClockRegression, |k| {
+            k.reserve(ctx(5), reused.clone())
+        });
+        let quarantined = ReserveOutcome::Rejected(Rejection::OperationQuarantined);
+        recorded(&mut k, ctx(12), reused, quarantined);
+    }
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, regressed time × UNKNOWN. ADR §5: a
+/// regressed capture is not admitted, so it neither records the capture nor
+/// spends the reserved slot; STATE_LIFECYCLE §2 keeps the slot for the later
+/// valid capture.
+#[test]
+fn regressed_time_applies_no_capture_to_an_unknown_payment() {
+    let mut k = kernel();
+    let order = request(3, 0);
+    k.reserve(ctx(1), order.clone()).unwrap();
+    k.mark_payment_unknown(ctx(10), order.order_id).unwrap();
+    refused(&mut k, KernelError::ClockRegression, |k| {
+        k.observe_capture(ctx(5), capture(&order, 1))
+    });
+    assert_eq!(k.reserved_observation_count(), 1);
+    assert_eq!(k.order(order.order_id).unwrap().captured, None);
+
+    assert_eq!(
+        k.observe_capture(ctx(11), capture(&order, 1)).unwrap(),
+        ObservationOutcome::PaymentConfirmed
+    );
+    assert_eq!(k.reserved_observation_count(), 0);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, full command records × unavailable
+/// inventory. STATE_LIFECYCLE §2 records business rejections; ADR §3 bounded
+/// records backpressure instead of forgetting. With no command slot, no
+/// Unavailable result is recorded; a twin with free slots records it.
+#[test]
+fn full_command_capacity_backpressures_before_an_unavailable_rejection() {
+    let history = |limits| {
+        let mut k = seat_limits(limits);
+        k.reserve(ctx(1), request(3, 0)).unwrap();
+        k
+    };
+    let mut full = history(Limits {
+        commands: 1,
+        ..ROOMY
+    });
+    refused(&mut full, KernelError::Capacity, |k| {
+        k.reserve(ctx(2), request(4, 0))
+    });
+
+    let unavailable = ReserveOutcome::Rejected(Rejection::Unavailable);
+    recorded(&mut history(ROOMY), ctx(2), request(4, 0), unavailable);
+}
+
+/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, full command records × quarantine on
+/// reserve. STATE_LIFECYCLE §2 and ADR §3 as above; ADR §6 bars the quarantined
+/// operation from a fresh binding. With no command slot, no
+/// OperationQuarantined result is recorded; a twin with free slots records it.
+#[test]
+fn full_command_capacity_backpressures_before_a_quarantine_rejection() {
+    let (a, b) = (request(3, 0), request(4, 1));
+    let history = |limits| {
+        let mut k = seat_limits(limits);
+        k.reserve(ctx(1), a.clone()).unwrap();
+        k.reserve(ctx(2), b.clone()).unwrap();
+        quarantine_pair(&mut k, &a, &b, 3);
+        k
+    };
+    let reused = Reserve {
+        payment: b.payment,
+        ..request(5, 2)
+    };
+    let mut full = history(Limits {
+        commands: 2,
+        ..ROOMY
+    });
+    refused(&mut full, KernelError::Capacity, |k| {
+        k.reserve(ctx(5), reused.clone())
+    });
+
+    let quarantined = ReserveOutcome::Rejected(Rejection::OperationQuarantined);
+    recorded(&mut history(ROOMY), ctx(5), reused, quarantined);
+}
exit: 0
```

### Command 274 — edge merge blob transition 318

```text
$ git rev-parse '70b976c0b8db686b1d21ff0831c275abf77a3d0a^1:runtime/crates/kix-kernel/tests/contract_edge_cases.rs' 70b976c0b8db686b1d21ff0831c275abf77a3d0a:runtime/crates/kix-kernel/tests/contract_edge_cases.rs
dab33001dee34f7e773645b3ff17119cfb56a614
8533d6419077d6a073d16ca2fce3a7d461a4de5b
exit: 0
```

### Command 298 — invocation scan

```text
$ git grep -n -E 'r1_perf_probe|cargo run|--examples|--all-targets' HEAD -- .github/ scripts/ runtime/
HEAD:.github/workflows/ktx-kernel.yml:106:        run: cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings
HEAD:.github/workflows/protocol.yml:324:          cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings
HEAD:runtime/PERFORMANCE_PROFILE.md:4:No production or durable KTX throughput/floor is claimed. R1 is a pure single-shard transition kernel. A **memory-only measurement apparatus exists** at `runtime/crates/kix-kernel/examples/r1_perf_probe.rs`, with `tests/performance_harness.rs` and `tests/support/perf_probe.rs`. It has no production, durable-storage or distributed-fault performance harness, deployed cells or durable ACK.
HEAD:runtime/README.md:30:cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings
HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs:31:            "usage: r1_perf_probe <output-dir> <samples:1..100000> <command-limit> <rate:0=service-only>"
HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs:165:            "runtime/crates/kix-kernel/examples/r1_perf_probe.rs",
HEAD:runtime/crates/kix-kernel/tests/e4_state_model.rs:1914:        "examples/r1_perf_probe.rs",
HEAD:scripts/check_performance_measurement_evidence_map.py:18:                'runtime/crates/kix-kernel/examples/r1_perf_probe.rs')
exit: 0
```

### Command 299 — pin P1

```text
$ git cat-file -t 69564b166f0c27f9af5d8422f0a466b18d74c20f
blob
exit: 0
```

### Command 302 — pin P2

```text
$ git cat-file -t b607996c83a119c349f1cc90469ac1ba82764e20
blob
exit: 0
```

### Command 305 — pin P3

```text
$ git cat-file -t d37ea7df55423c83bedee16bf12bdc8dd61f7cae
blob
exit: 0
```

### Command 306 — pin P3

```text
$ git rev-parse HEAD:runtime/crates/kix-kernel/tests/contract_edge_cases.rs
8533d6419077d6a073d16ca2fce3a7d461a4de5b
exit: 0
```

### Command 307 — pin P3

```text
$ git hash-object -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs
8533d6419077d6a073d16ca2fce3a7d461a4de5b
exit: 0
```

### Command 308 — pin P4

```text
$ git cat-file -t f020860b86933bf7511befccdb833b0c532b3629
blob
exit: 0
```

### Command 309 — pin P4

```text
$ git rev-parse HEAD:runtime/crates/kix-kernel/tests/support/model_v4.rs
f020860b86933bf7511befccdb833b0c532b3629
exit: 0
```

### Command 310 — pin P4

```text
$ git hash-object -- runtime/crates/kix-kernel/tests/support/model_v4.rs
f020860b86933bf7511befccdb833b0c532b3629
exit: 0
```

### Command 311 — pin P5

```text
$ git cat-file -t 619ae21c82ca3df5661bd3831613f15fa65225ff
blob
exit: 0
```

### Command 314 — pin A

```text
$ git cat-file -t 07c36869e7b68fff10b02e6c59d7119df56d0785
blob
exit: 0
```

### Command 315 — pin A

```text
$ git rev-parse HEAD:docs/adr/0001-ktx-authority-commit-recovery.md
054bc714b3c475fb8536df8d2d788b42e8c74b6c
exit: 0
```

### Command 316 — pin A

```text
$ git hash-object -- docs/adr/0001-ktx-authority-commit-recovery.md
054bc714b3c475fb8536df8d2d788b42e8c74b6c
exit: 0
```

### Command 317 — historical anchor A

```text
$ git rev-parse 0394a36a655b86bacb568b055d377d4c4fd91185:docs/adr/0001-ktx-authority-commit-recovery.md
07c36869e7b68fff10b02e6c59d7119df56d0785
exit: 0
```

### Command 318 — pin L

```text
$ git cat-file -t e953c4870aaeee24b13c75a8647c50609720ae01
blob
exit: 0
```

### Command 319 — pin L

```text
$ git rev-parse HEAD:docs/contracts/STATE_LIFECYCLE.md
8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d
exit: 0
```

### Command 320 — pin L

```text
$ git hash-object -- docs/contracts/STATE_LIFECYCLE.md
8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d
exit: 0
```

### Command 321 — historical anchor L

```text
$ git rev-parse 0394a36a655b86bacb568b055d377d4c4fd91185:docs/contracts/STATE_LIFECYCLE.md
e953c4870aaeee24b13c75a8647c50609720ae01
exit: 0
```

### Command 322 — pin R

```text
$ git cat-file -t 900866ee99a71254fb7da1ad2aa4640477ac550c
blob
exit: 0
```

### Command 323 — pin R

```text
$ git rev-parse HEAD:runtime/crates/kix-kernel/README.md
788896ed3e00bae3d06d26b7e2ce999a00ff1029
exit: 0
```

### Command 324 — pin R

```text
$ git hash-object -- runtime/crates/kix-kernel/README.md
788896ed3e00bae3d06d26b7e2ce999a00ff1029
exit: 0
```

### Command 325 — historical anchor R

```text
$ git rev-parse 0394a36a655b86bacb568b055d377d4c4fd91185:runtime/crates/kix-kernel/README.md
900866ee99a71254fb7da1ad2aa4640477ac550c
exit: 0
```

### Command 326 — all candidate types

```text
$ git cat-file --batch-check='%(objectname) %(objecttype)' (stdin: all 434 unique scan candidates, sorted)
0000000000000000000000000000000000000000 missing
01a86f66f1a2a0de98ae00f89e49d45ec07ec8da commit
01f6c04c71dac27fab5d17017f4e837c076218c6 commit
0262dd972aa07ca36fb4394311d910b55f80738f commit
02b1bf202b926c3b99cb39b360a50b2a75d3f744 commit
035d5705c93b318a49941ce5f7410f843360c427 commit
0394a36a655b86bacb568b055d377d4c4fd91185 commit
047d08e34659a5c392a0a0b08883846253c2aef8 commit
050a0e1e50f56622d8137e6516b01c6a0c8538cf commit
054bc714b3c475fb8536df8d2d788b42e8c74b6c blob
059410cd85bf944142175fbd70364f7cc54ea196 commit
05d133c9dc4ef8e979391ced4099d2c9415e0124 tag
063e37c7d23bae6deeb51b3ff142fccfabf74d42 blob
0672452e35a8582ee824dd29fd0dddd94320b453 commit
06b9ec68f9dc9dd4af4d70c236360be964a84ae1 blob
07c36869e7b68fff10b02e6c59d7119df56d0785 blob
08119a41b7c8088a0e9d40bd35228af33d795643 commit
0846e4ddf1d55cc4ac619e2c350c4e3574547bda commit
08b317e5096893432116e41c8312697793500cfe commit
08ced25441171b2423e6399f04dae14ca0a0a3f8 commit
09470db220965390edeecdb75f56f8c827dd15b6 commit
09e161caa652d75e9617caf632b3b9899be35740 missing
0b8b6b484c1b5d49b7cb285e780481061c2b16c7 commit
0bbc9b9cd421b386a542a8ed4351fb6aaeff907a commit
0cb65749492bf78e6cea00d3c9c7eee4f891827d commit
0db660a1085ca179c341c89129eeda763977b1fb commit
0dee7319c2598083d9e6c02e917940f8648b1a40 commit
10e44d40abd878736b900d768f925725c95a8cd0 commit
118fc28862a6828b80166433bac6f5476037629d commit
11d6bc63c732204b78531cc7959afefa69a77703 blob
1311668253bbbbffdc90f1a9f446c42d43e5fa1f tag
13134e49704815457fef444ce61d781b5a424713 commit
13c565560c758c2007c482376e68ada45b922c2e commit
154e9aae3da1bf0044dad606fcfd7e2fb6b3f8df commit
1578bc39bd256d4e894ce341a108be1647b9e14d missing
15f7fe67726c04efd5a6d289ef985041f40c511a missing
16a6aa05d7d9f693bd4dbbad85008243fa8fd95d missing
16aa6d528c2b2a519d99e724b986717fc090b1e3 commit
17c8a7dc66e49b090067b94ff7bc68cb6d79c5ee commit
18aefc8f7c0dd13b7249e0d80304f3b97459fa3a commit
18b80a79614b3a5866f61728b0935294360cfa85 commit
19a58ab1e232c54eb39b717a94c637322c493a4d blob
1a529d036d2d7f33eb17f4c143b16a3213f26973 blob
1a69364eca0e2a219854c443f8183a9b0e733a2d commit
1bb000bd125a1e8ecdd033cea01733d58588199e commit
1c129f1a5fd73636c30c90a33ecfb9e4adf21217 commit
1c9488499bbd954f1c14e5f571f24f3f1d976338 commit
1cb2d26c4b6d8cc7aa2d362bf017e4d30f5a2080 commit
1d8d228e6fa5cabacf341dd6add0890e8fe95421 commit
1eb7d7d2978950073973a43e495ec5e31c5f543e commit
1f01a9321c641c7a7fafa2a33e4350a2fa711730 commit
1f9cceb99404cd673205d5fa1f46db8900e74da4 blob
1fa6676860710e6bad6d882a57a91972407e2e41 blob
1fb0c8b50ac4de5693996412337d36cd6683bdf2 commit
1fc02920d93fe0fb1f272fa917f6e20ba26cc987 commit
20b692b0e7de91f70693d15b14ff5c5c52fc21cb commit
20b9538f9d48ad513c2f2ea28c478d01c758b01d tree
22d05a0c82693ad4575a72c2d342b4e47114447f commit
22df2e96d1a7de4d0de371a1f64776e80af9d999 commit
22f9fc9781732d651e18384c9a8eb1dabddf73a6 missing
23391ab50e0467bc7b234c55e98614713d531f58 commit
2393988eeca984f12f0819ac56b6870be1a5832f commit
244595db1524cbb1a01148baa07d6d28cd1b8dc6 commit
2497471dfab21ffd68d600e6ce508e5d6d65bae5 commit
24b925955ae17942ab25b68b1e5a9111d6983501 tree
2554173ebdda0922aaf7a0bc7ea773075187a3d9 commit
2658a43aefa792ff783457188814f8598a62f5b0 commit
2676b5bff0f8d696f18139aebb7e862a965139e3 missing
26be51051939cfe88f7ff542f355f10ff7a3fcd7 blob
26f1b9535db24a6b2e9c28753f561d4d6a271815 commit
2798352822e7ee657ae789ec370d0390a31febdc missing
28539987d1e676f0724081c41b22db51e731a967 commit
2862f34b588e70841a57762d8ce756fd240f5e95 commit
28f263b5839921b729c2729c8ff5041f57d306ec commit
293cc81198d45faf8111637af6fe4d28fa3470cb commit
2ae8f1d0774befb0d71eb07f2e3d7454d3fcdc64 commit
2b358c225256e8c13c517167c8b1c30156a4383d blob
2b91c41288b048a233f95b2d4e285b9c262d2333 missing
2c7bc7dd7d4831b0ab3c0ce5e394999a7f72de12 commit
2d2e93eb14fe41bafaf2dbaa91f02d861c8be8b5 commit
2d86e35be414181184c16a6de1649aaff95bad64 commit
2e43b285e2a07b4af6377ae7f776a550dd884e95 commit
2ead88aec7f5fc36ed802c32c98f3053367c7ede commit
2f527f4fa6d0a1c6185deca7dc29eef49de01005 blob
301de8c7da8859164ee708b2560bfc30d13531a4 blob
306dfa1261eb02881d1914b34d6510fc698a9979 commit
3181adca80c2979145ccf54e0abe8330c162f738 missing
31e60b2269e90cba6da9a1a41dacf039f5662c30 commit
31eac0637a324244aeca00e849fdb0f7c685232e commit
34584c427260826cde67d726e18c92e01839817f missing
34a722d26fa894366c26bac9de4187c598fbf3eb commit
34e114876b0b11c390a56381ad16ebd13914f8d5 missing
37504dd43411d331d6e0d9351c86ae0e10ae33f0 commit
3771a8739b906a478b54c597df37e27d1afc5f21 blob
378f1e817f22401c65007e7de3313901ca0ea724 commit
38096dc849dc338f12aa69bce2200cda971a6d3c tree
384c935010a33c160ccdb26b568ebc7454777f09 blob
38901ede6a20dc67025014116ea92c0ea35f8bf5 tree
39146a44187af4b43ac57148661bc3af2fb3104f commit
394084b15e01bbe4a5612aeb3431f3278c43dd85 tree
3995d878823727669023fa395819c79a8c227850 missing
3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af commit
3b6bdd26f61bb828af3781946b63a3a3fa03187b commit
3b8067d48cbda967cbf531258215c5243b96fbcd commit
3cbb8df3a466fe171d7261f9090c324a458af3f6 commit
3ce6e4975b7f439d67482451bb47a22c940add26 commit
3e7c64a515e908b312604e82405b963d100caa07 missing
3ea44ce1d9003ad095e408039e1f755c319c4dfb missing
3f1e78d94bb06488a9375a718fae22d6d76375be blob
403d3e29413b1e78c5da945cd33389b50d4514a4 commit
4052dccfcbeaa95c1f21c2973ef530e5d5905759 commit
40d904318b58d1ccfd2e86e77e6b290856ec95a7 blob
411e7a592fa4219ed606ec770ab903c6a6fd36c7 blob
412e1ed7bc740599227567f60bf315bb7ecab818 commit
41a799987fe3a6a207abcce75045265c5796e1e4 commit
4338fc72698f2f15c3723f3d13e677d3e1aff29d blob
4428d2bbd00a1e43bf0b61dd402c6ad0fc67bb39 blob
44659fa4d3553dec46d709450249d2764fba8d8d commit
4480c9db7be539abd5a99e640b5a25c7eef8cafe commit
4584c9ad2a8c886acc3cd0b1e021a5802e6424f3 missing
45c08d519daa70adaf89ba5e8d2e89175422dc17 commit
45ec626e2ffcd1cd47aa982622877873b5297139 commit
46d01d149d96c7776283ccdface2e0c6244caae2 blob
46e3b38a8dbde60f5a1cd197577a2dc73214ff2e missing
471728e6488719be471eebb3ca8c30ab2948c444 commit
47eed4b01b93dc4b00e102729bad1c74abdbae95 commit
4813388b5bcde72c298c7392ff5230316da44470 commit
492a85d36fc79aa31d3938bd44024b73dd70dfad commit
492ae8c9d7a3171890cbea2ecdb913519b83c158 blob
492e3aacf4fc5260240df10c3c55a39a54fcb466 missing
49933ea5288caeca8642d1e84afbd3f7d6820020 missing
4a73103904a8b8428cc1424a6e9f52b13ef3ed09 blob
4da9f7762beddf1a93d95cf26e55d7bf64316711 commit
4e2122a3f61a0feea2c43035c1ae834e7097e429 commit
4e3ce63eaca8ab766c9c88adc712554fb0027d36 commit
4e5c30cc6779ea8b7d26fa40fdde6c84adfd44b7 commit
4ec0f93255b9be1715784f1d2a5edde411cc96c6 commit
50af6096a84f72c8c1249f23279dab0b279e4c82 commit
5155ed307c71917ba3442fc5e1fc4cb950efefdc commit
51d83808478e56c81c6f43e2a13450d435e922e6 commit
521f06f7d9194ffc4eae21bfb13f7e82b6ef9241 commit
52bd45eff0d77280406a819e62e33212ca50370f commit
53c16b226346f2df824f93a5756a080acd489ec1 commit
543c1438ce044479fd9646bc5e1cde933a153a4c commit
5440de0cf721932398af87344fe59d48b9858ad3 blob
547d9fd5cd0e2d54e4fd61050d6f4fff530f3750 commit
54a785b864d629d623afc36ed807d9daebaf9285 commit
554b78e80f505a008dcbfb4e1c9f271d902a4039 missing
5561fc965803935be1894457ebc762a3d36489f5 commit
5587afb34cdf9df51b981bcea4a9507250e70528 commit
55a3df4968f5684bb4cb9e3c9781ab5f00165235 commit
55b018503df24cfbe36cbf17bbf48a8c0778757f missing
55e253944f1cf66faa27652680ca7b2a3783b1c3 missing
56b17aea66a4c006a1c6b2d0de77d76b10feb062 blob
56d4a3d193cfe5575285f4b59a8e1faa7ce9a079 blob
56d5f59468969825e0e2cd22f6803ebb5e6fb662 commit
5714603158ddac1a5dcbe2e645c902e26f2b20a9 commit
57a3e3049c84a2ac0112371594e9bb4b85a8296f commit
57adb8d579986a945b716f0f181c0be938ceb389 missing
58386edc269ef88ff0f40ab0a9d50e87cba80ca8 missing
58dd527ff53097f5231e89f25ebdf3e94586ee65 commit
590e544b3d097ba3de2fc573deae43b15bc39773 commit
59746105a8e1b82b0109bb958e6f9104abb70f39 tree
5a09a325e2f6415b7fe638d0dbcd826b4d45fb86 commit
5c11893edb186c739140330626d5caf74fa668b6 commit
5c59d95ec52379e010f8e9c660da11cfa6498def commit
5e20a467160148ad5c2debfe357dfb8da084a30a commit
5e43f6f21b9f3c8be3af1d371b9c5d955de34cb8 blob
5e8ee3f1882d97f1c442fe485407e51822ec22ce commit
5eb95eabcac8b71e0c6c92b4fb322a0e4fe5bb45 commit
5f55793de15792686bfa7a5be0da24fa4acb41fa blob
5fffc196be37425366b2a6ec7faeec1db9bbca46 commit
60e7683ad28d5264f398d7965c06bfd840aa7338 commit
619ae21c82ca3df5661bd3831613f15fa65225ff blob
624b28d024279bd077e1247f37566333457750bd commit
62bb47f63408264b2d4dda50da94bb4d77c015c9 commit
62fd4302af952a66c1a6e3fb3b3ea5a1eeebee64 blob
6332bca0f54cc2114d986b24ab218ace33a5df12 commit
64916cdf387d43c3db4ec9d487a246d3347b8d62 blob
67088f944155224b2b16fdb8b51ac781d930382c blob
68a65db0208cf57e35750b226dfac49f555ae850 commit
69564b166f0c27f9af5d8422f0a466b18d74c20f blob
696420af819ebc004067fd52971d016e51e6cdcb blob
6b6d7675eecba9f599a8760698fd2c469359aef9 commit
6bdd571fcb88496c98e25b32213c60017e209198 commit
6cdff624203a9610ed9b84fafec8dad07995c414 commit
6dbf8dfed6ee790e2ee56b49a75b727edd9db977 commit
6e54e723d582e88ae89df309eb144d4664c7e1f5 commit
6edba1a60c14d5b43bf05336294e678b46794fee tree
6ee81c86a6f587b6b1bf549ce0043a5e43555d43 blob
6efea0adcc2b1c7f4bd62c43673cc54830a8fc37 blob
6f7559470bf2d555bbd80d0ae5d5f8a008e798f7 commit
70000ed8a189b8b3b92a4a858d7cce1ed43e5d7b commit
70b976c0b8db686b1d21ff0831c275abf77a3d0a commit
729a106add049ad1a75b90f99c00b6e0ccb8a67d commit
7327a00a68ef6efa81a795173af5e4572ccd90ef commit
73f324a00f345e120014718b67a7c03ecbf1198a commit
7481b0e16ce9b903abbffa62249bb91cd9e63cfe commit
751c51bdff661673eb2edb9de0dea8f6cbdac2e0 commit
756c2f78c9b6058b6acf1573aba052118669a2f5 missing
757131963bf63296cee3395158864d43d6ede2f3 missing
75e3b9965ec4441b242907269a2f5e397f8c8914 blob
76b5e342c298ebaac42d6ebc7d5ecd6bd27811e6 commit
771545ae4b64f069396667f399b5200c44fd9af0 commit
77517f0c74cd892ca299cacf987cbab64a03337d commit
77da4bcc37e227c549929740a30e4ac544efe4db commit
788896ed3e00bae3d06d26b7e2ce999a00ff1029 blob
78b78b1b4a4ffe92de461edd351235ce858b335a commit
78ed34d37568d9084f75a546bbb6377d16397521 blob
78f7f80e22f35b8a8cfae56cbded38f3caf22331 commit
7949fe3e7ac4a370c0b4cbb05ac39a3779e8c466 commit
7ae4535c472cbe5416cf68a298fd4cd1dcf2a38a blob
7b6a293e903845ff9c06a19f9a02c075d1790089 commit
7bdc99933c804b417b94d9dba40f13d370861cab commit
7be6b7507201674599f5d35aaa329cdbeb75ab38 commit
7e580b26c04edb226a729c79a2ec6731c1f858b2 missing
7e6d215031d7ff454b132b8c1ca657455cbc2734 tag
7f480fa4e3f18db83605a59cab4ae9b2e405478f commit
7f59ed18129960724696400f7f4c9fca3d465fd9 commit
7f99812f4558e4802a51d5468da35754db693c43 commit
808640d9b49aecf29d8e6f46033c15eca236efa7 missing
82f0a5d2ecb6797a15087d13a1b7d67482de3b09 commit
8340a418523e92fb938d9a82b23f81c1ce0e6156 missing
83f1f17bbfea81a8371e4c598d41f2915102a6e8 missing
841408e77065c841ea73e2cf04fe8c03fbd35f5d commit
8495c7651e456cead3a8812b9e6fb183f818acd2 tree
84cc3ea7763ed6d5e08021e1a9930edd7ff5721d commit
85145eb33799a7c712890ff81708def8a7d61ee5 commit
85acc3399a23e87ee4092693840c4e0a620867a0 commit
8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d blob
876f41067bc7eb70bcd6ebd9c744c11b46f046b6 commit
8785416213151b7cdfefae2bccbac00ef168e3da missing
87bcdfaa528eb4f99f0ac6ed643f840d738994b7 blob
8931820e77860f575faee636cacca2c45e4f2c98 missing
8b88ba7176a98faf64565434d05e44d97dc3cf8f blob
8b92eb42353d5ca1058227671b3abda3142643c3 commit
8d310e76e6a0e8999be427e95599b62f1f8b13a5 commit
8e69bd7f64e019dc3e1256a94ccf283d13dffc73 commit
8e85ef4e14c2615a94b8efca6acd60ea4fe52fb0 commit
8fff6c191c690e803a1bb901a0cf7b5765167985 missing
900866ee99a71254fb7da1ad2aa4640477ac550c blob
90c6e7a6bfa305764a9b66df3cafdae038b5139f commit
90d320325a601e1f604cd901703fd2a5094ca527 commit
91d2e507362a79834c09790d9f379ee15f2a1453 commit
92d08e755dfe362ed224112c8dada6c5fcea17d4 commit
93cec6aaf12f22bf8aefc0453fe545b6bd38b819 commit
9411d3c008d58d50e6a26bc07f1e46a8e8e4fa84 blob
94376835ea4fc818619fc79e2be4df7d4947496a commit
944cb16f3ade5a395c0febe84fd47d5c16dc0fa3 commit
94a768e19df12703ea0b9a49e49972feb2f6ef4f missing
954e6e3a2b6abbe40af3a13d04e4263fa7fbe547 commit
957f75d75ea4854eba117d66d07663133f0b7b2c commit
96d0daad5b96af501c19284f149cb288b17e5d05 commit
974d8e4875c5128266aaefa830bdfcd33cf89534 commit
9805d74a1ef794f14a6eca9894cfe1a2034e2e91 missing
98d5f6372b68f875bcb2b670c5998697ecfb76c1 commit
99c2655d38c283497b92dc24ba84a2ae6a5461fb commit
99f30c2d641646d653b62383b213452fd0a0498b commit
9a8da873074aa96ceda07a772629098762238773 missing
9aa464b6b9d89cdf1da65f828b55e6e97bf7bef0 commit
9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1 commit
9b462fd2cd6890cd0d8fbc2930f2cc54255e2915 commit
9c4da8d53947a8ca049b6284fa5ca915fb5947ec commit
9c59e0a81f1675fa919ba9327642269bef9e70af blob
9d0860c870e4a06f6b8e876cbee6446f50b22b15 commit
9d1ff76377fd7c65911c1fb7cb7b515a55489e2d commit
9d50fb660248b66a5959f48f7dc96e68c9d5530b commit
9d5ce5228045673eb362c5f20cc019a6cd8a5ad1 blob
9dd1413f060a420b3a97896b9451c82574f56d08 blob
9e2dad654d7c6e46efade803018ef3e2cfea5e0a commit
9e5d96e995fe2cff29b2b52863f6d6dc5c4d9289 blob
9e8f4898cb429e1146ea924d6c254b7fd490a3b2 commit
9eb6b5f932cae5f4f1b431ef79c9f15874db1c36 commit
9eb6b9ff24c6ca5825a3d999c81932a38ae79f02 commit
9ed15a7adc93359e99bb5c3512a3ca20c77cb264 commit
9f0177ab45cf3ca704ecf5a152b3c1785c8f22a7 commit
9fd4d4836ab4d7eb666ebd4ff2ac0708870d7a58 commit
a013cb0c471be0422a4a70d6b98e86c03f7131fa commit
a059bd69eae321ccfeb5940f3d675b962103d361 commit
a0db1e226e27b1c5f60ee938fb528ff795907056 commit
a0e16328c1b4939458b2abe5b4b5167b79a15c26 commit
a114b5bd67164dd1264bc4ad838566809b5bc0b4 commit
a13244fe6dc07d72b314752f056612899dc544cb commit
a176c1f22c0af21500cb52a777bc889b808e561c commit
a1a8af283a7a22036485c3b7cb097db9855ad91f missing
a26af69be951a213d495a4c3e4e4022e16d87065 missing
a2814923bc671889da49984a2c95964340a1506d commit
a2a2e29ceefd50952454c6b378363b31be84c3b4 commit
a329ec07ac52ec15bff6c48079115d81ace5ab67 commit
a34a38b73f096c9f6597b38a111d95ca12ecd159 missing
a38e1679449e74186c5a4e3d19b6cb79f6b791d5 commit
a3f0fea3160fdea2f59fa8658573be173e242074 commit
a4158b3fb495aa12507ceb44bf128bfbe7dba2ac missing
a45b246082453cb739e51bb0577bed646e4d1935 missing
a47828dd4517c5a7397e09eb6b563a64e4265c82 commit
a483ab1777ad0c3e15ff71798822cbf6b3666f83 commit
a4ab8d0119daba974dd59a20d3da05d82bd61118 commit
a6ecb124dc2b2267ca6be19e39fbe2aef143074b tree
a744b0a036d7e1edb48416871af20cd182f23df4 commit
a74e7c459d3be6754ac3cf24503e43c7bc312358 commit
a7c9d4467a9170ba4a062554562a4610c0b27573 missing
a7e6febded343fe0fd43df2059874525194efecf commit
a83d09cd99017875f583383e6ebbabc46a6a63eb commit
a8b7355712c58de8d27c85a535fb241a09a4037c missing
a8bc9e853f3b0d82c5c4ee2d0bb4620ac36662e4 commit
a9be88d3da4d735aabc5168c68007c062956b412 commit
aaa7ebee8c436f1a01cf813d497b018185eecec8 missing
aac2e72d8d5df86032ec2154172f724d07ebbcf1 commit
ab3902f66c9abd3875f36126a021710c887d015f blob
ab42cfef43a40c6b86fd3f22b69f00e134cc472e commit
ab611650286f9b5db82b491d398dc47e27a93864 commit
aba875635f682bb9914e0dee016ced58e130cc04 commit
aca49f6e5498291c1f221185df1ee5cdbf333342 commit
ad3cee9e6aa68aa14c3b35901f66b6cab40cf75a commit
adcddc510a66ff70725084c0846830c29ef9ebbe commit
ae5fd6aee210007b2f1ca7f96809c76348aadae4 blob
ae6b905104d0cb2022001fb32ad98b1a6b3046ec commit
ae869f38438d8174103171ec741a41376aee60df commit
afe7ded7abc1b6e6cc65c8b179c2d6dac009c891 commit
b1fe707bfcc99ac43edcbd2622caad1a25e1ce22 commit
b3f1c6c1f943dc5faccaa9451aee55fa7305dc4c commit
b57d49d068c14d1a012e73cbc8c10c8f6ee5d631 commit
b607996c83a119c349f1cc90469ac1ba82764e20 blob
b61e48d965e7ed3f1c5f4fcd5ad863b961ce4e28 commit
b6373c2448ac947d245851abf7c4d9a00e70f5c9 commit
b665f9a0ad41a46e2169cb142b91d598665aa7ab commit
b6cc9978c64b1ff54f822ea930424b5d78dfca2a commit
b761bd60f45f224b4c5db5e3af6963eb6e7dc4d5 commit
b8b7455cf346d98689238d3eeaf07fc139fa6a7d commit
b8c8d1057e8124fef09dc2301fdc841015f22b4a commit
b9184e48f0df3f26a5214ec00eea20b0629b447f commit
ba352dfe9789af89983e9c1b1a303461ea240016 commit
ba5bd063daf87a365d4bf6f795c8940ee7fcfb17 commit
bad6927e6bdfbb1681c1e51b40b73089ea557e1d missing
bb193efb5d238581096372c8a20bee1271dfe4df commit
bb24207cb648acfe3083c4a2e7720251b06ad639 missing
bd367efcc9127663b902b973850ffafc179469df commit
bdc663b47663b885dce36e7138a407b7b0658089 missing
bf460b1f7724c5ad7d561b19a64959383fcec6a8 commit
bf6c2be37e8c55778f4fe378634f7895fd69a327 commit
c0fc5b4aed4da32284d9879ad21ef6b584db01d2 commit
c2cde86e21a6e5ba6f24a56548636db6d0a34c6f commit
c3a2b304641dcd2373e0267030dc69ea48d55f5e commit
c3b02085650ad394283f3325cf5dd87664c66ddb tree
c4287ed94a0bd0295f0452fc4374a45dd661159d commit
c4cfe54d4ef18ae8e99599ad4e9038ccf5d18a4c missing
c51142ae5090fb00d68fa4f2d8722c6a1d526345 commit
c5121714b58c3e5250740c924733e1964445d102 commit
c5d2792170e8e476370a064b8a7de626a5213412 commit
c690c9fa6e1b3bc058fd35be507c1c1d94e2419c commit
c7762c2724d5d28fd2e5e4f00cc5aae4f1f7908f commit
c7b470fc39ad6f6aa6ad59c18b5595cde41a7200 commit
c8267d1c2bdbcd732aa46401fe059b92d8ae72a6 commit
c8b806ebd0f959814acfd184edadf244bf18d1b4 commit
caec5434c12f1238d7b3c014b404f4f8bddadd78 commit
cb59612b847fc2e6ef71810202be5e2ca5f76724 commit
ced0e2f42c0491753db91acf87bd61574eb37ce4 commit
cfeb0d69561103302b6fdc3d10842768c3420151 commit
d016caee4ae40f28f531809359ee77ac22db0073 commit
d1cc57a7d6c640b5df3eacd65a1d8593f0beb346 commit
d236cfc69e21b88a74caef8879e7ea08008628aa commit
d2b748aef0c7b4af5bef23c771c6bce22b52905f commit
d37ea7df55423c83bedee16bf12bdc8dd61f7cae blob
d554ffc40d93b85fdd01057f48fdccfa0d991d94 commit
d5b9f2d67b5532fa35464c8557e88f70be300888 commit
d63768ddf276c60173aa2c933f4feef3449a9452 commit
d6a6a10f3f5fbaf31f54ad676a9b5e36c0e3d313 commit
d71b4117741f596e2b618ed1c32a42597bc0980b commit
d7549d1473258dda617e241fff22bcbd697fbb17 commit
d82c37964d8f87c43d110b19899ee4d6622e87b4 blob
d84cc50f78a37420ca9d12752ac23f9f9b51c5fc commit
dafe686bfb708a309fcb36482f60fb1aaeb947b2 missing
db02ae11bf4a1d7705f31b328c627714f91e1c78 commit
db9152ab1c5ef113b8727749d4309ec70505480f commit
dbc152cd601a1dfbff2c8cb9a447b2010b16ccc4 tree
dd0a501248e092c2a4475088d94d7449b7bd98b5 commit
dd92e1146ec8eb7024da6c0f62aa721bdc1be780 commit
dedfdf11878696bea956df61ad53498c247cd8da blob
df7b026590677448438be62d2249f13f2da1cbaf commit
df8bf63daf52d35f49e109fa10d14a59ee494ee7 blob
e00e68e680d586346abada94500955abfe938ca3 commit
e1fd5d1b24cdc5e08a29f1e8216a1c6b62c3f44d blob
e2313ab473ea1b5a7b5b9246a564749188c1c2c8 commit
e26f1bac5f5170fbfd8b51aad71ba49d0665e609 commit
e291a88211c45ee7285fd8abebcc6ef92bc39f23 commit
e2a029d8ac3af7575888dac22fc4bf173ebec232 commit
e34868c6a12e5488224095b3248e59c8be9128f1 missing
e7259a5d17f0d73a993858c5f17e678700a74498 commit
e80c5d53989af35987aa0b8371b4220acd4e3808 missing
e864de49dcfbb053232ba42b24dbdeab04b43373 tree
e953c4870aaeee24b13c75a8647c50609720ae01 blob
e9caa181278048cdd0c403929d00a03d5ecd3ab4 commit
e9f6fc0d880b9f74213791b36df65f63ad88c1c5 commit
ea165f8d65b6e75b540449e92b4886f43607fa02 missing
ea867668696d6b1114a443d0fe4e840d96b948f6 commit
ea8b19ea533ebb9622900b0ca3bffe3f6405ac4b commit
eb0a53cd70cd22ad4301cd0be9d368db8caa355c blob
eb14da2a6c5b5366cd4aed855bd453dcb4d79a42 commit
eb1caf8285c174697d78834246a304ffe9006427 commit
ecb78a446e988fb40615f3e62da08714ef5786f5 commit
ed1d48d52d943f000511573b78ebcfbf3cf5c114 commit
ee35e81f13558c1482947498570a2ebd8e4dfc4c blob
ee64ca29d99c5b955fb96d29a0ccfaa8cdae52b6 blob
eee77d135f03471b78ce673223dafc7e0b0fb36b commit
eef11daa33332c2ddfd75ab3045a8caa3b84513f commit
ef942b7713c7468e8851c6b372b64d42b5333ad8 commit
eff0f44f28d0232c6177c40b2f2feb2aa951ae09 commit
f020860b86933bf7511befccdb833b0c532b3629 blob
f021965129e767234225364e229fb4be99395e6a blob
f1734e00e5a167dc18bfff1a873994bee124a3f7 commit
f1cc5b565a6dfb239795f586ae5e6454f377830b blob
f1ff0705f3e847573646824c284001ccd00ffd01 blob
f2a370dd55c29d7b3403e3872489bd965e38411e commit
f4df0d8ce0253e7b9755f7eb77e857b2d49057e0 commit
f50047a902f9e4f2e6a25e904f6f89ad758eb8c0 commit
f6558996c611f74b88c60928f5b285c553303c14 commit
f8a63bc83d2bc00f8e128d10d2b7bd83db84e510 missing
f8df15beef280a8aa02929f92974f09fcc58e7a8 missing
f931cfc87bdeaa1ed2495df0ce659ee832ac1c33 commit
faf41fca3ac0a4ed838ae269816dbc53510cbbd9 blob
fb8b67b6d9f1fcddea68153a9f4b9e9310cee776 tree
fc11cdf0150e54ed38bb363f2ded7238c48c6e53 commit
fc28ad4eda7e49f34324d46253dfd950533740db commit
fc3ed1b33bf294cb48f3fbcb9cce5df058e51733 blob
fe08e4134b2f2e58f48b636bdae7440d8cdb70dc commit
fe1f8666c4e50f7740bfe48641d3015fb66ef7fc commit
fe865e6b94b5724e60f2d16371eb0a3b76f66fed missing
fe8f12832e01828a1cba80aec908d6c9971cffcf commit
fec140112e11fe7403fa4fbda57d629e52a99f72 blob
fecb5e993c986080c63b4de41be5c5f476592610 commit
ff0f39a8129ca8b8d30818cce35c3d4e588872fc blob
ff1a955815a054f2345a2e06939f2c84bfc29be6 commit
ff88c441f36cde5b581ba29ce4c46ac47f22b218 commit
fff19605f0ccff71b6f24e61f1f8114b5c0ddd57 commit
exit: 0
```

### Command 327 — pin introduction

```text
$ git log '--format=%H %s' -S LOCKED_EDGE -- runtime/crates/kix-kernel/examples/r1_perf_probe.rs
28c9c130e9ab9be017a8302dc1e4a4cbd3cbfffa test: separate v4 perf summaries by outcome and load regime
exit: 0
```

### Command 328 — edge source introduction

```text
$ git rev-parse 9e8f489:runtime/crates/kix-kernel/tests/contract_edge_cases.rs
d37ea7df55423c83bedee16bf12bdc8dd61f7cae
exit: 0
```

### Command 338 — narrow checker

```text
$ python3 scripts/check_docs_index.py
docs index ok: scanned=288 indexed=253 allowlisted=35
exit: 0
```

### Command 339 — narrow checker

```text
$ python3 scripts/check_docs_index.py --self-test
self-test: detected removed index link to docs/adr/0001-ktx-authority-commit-recovery.md (not indexed: docs/adr/0001-ktx-authority-commit-recovery.md)
self-test: detected unindexed scanned file docs/status/SELFTEST_UNINDEXED.md (not indexed: docs/status/SELFTEST_UNINDEXED.md)
self-test: detected unindexed validation record validation/SELFTEST_UNINDEXED/README.md (not indexed: validation/SELFTEST_UNINDEXED/README.md)
self-test: detected dropped allowlist entry docs/contracts/openapi/fsm-command-contract.json (not indexed: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected removed scanned file docs/contracts/openapi/fsm-command-contract.json (allowlist names a file outside the scanned set: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected allowlisted entry also index-linked docs/contracts/openapi/fsm-command-contract.json (allowlisted but indexed: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected broken index link docs/status/SELFTEST_MISSING_TARGET.md (broken index link: docs/status/SELFTEST_MISSING_TARGET.md)
self-test: pass
exit: 0
```

### Command 340 — narrow checker

```text
$ python3 scripts/check_status_register.py
capability register ok: paths=385 ev_ids=15 original32=32
exit: 0
```

### Command 341 — narrow checker

```text
$ python3 scripts/check_status_register.py --self-test
self-test: detected missing path (path not found: docs/status/NO_SUCH_FILE_9f3a.md)
self-test: detected undefined EV id (undefined evidence id referenced: EV-XXX)
self-test: detected dropped original id (original id E01 appears 0 times as a row key (want 1))
self-test: detected duplicated original id (original id E01 appears 2 times as a row key (want 1))
self-test: pass
exit: 0
```

### Command 342 — narrow checker

```text
$ python3 scripts/check_evidence_map_rollup.py
evidence map roll-up ok: contracts=25; textual index only
exit: 0
```

### Command 343 — narrow checker

```text
$ python3 scripts/check_evidence_map_rollup.py --self-test
self-test: detected missing contract
self-test: detected stale copied Counts line
self-test: detected Counts disagree with table
self-test: detected missing map path
self-test: detected duplicate contract
self-test: detected non-contract row
self-test: detected missing checker
self-test: detected unlisted status
self-test: detected nonzero unexplained token
self-test: detected duplicate Counts line
self-test: detected owners mismatch
self-test: detected arity mismatch
self-test: detected no-map row without reason
self-test: detected source owner has break
self-test: detected Counts trailing whitespace
self-test: detected missing Status table
self-test: pass (16 negative controls)
exit: 0
```

### Command 344 — narrow checker

```text
$ python3 scripts/check_ci_checker_wiring.py
ci checker wiring ok: scripts=32 plain=31 self_test=32 self_test_only=1 docs=22 citations=99
exit: 0
```

### Command 345 — narrow checker

```text
$ python3 scripts/check_ci_checker_wiring.py --self-test
self-test: detected unwired checker
self-test: detected plain-only wiring
self-test: detected unlisted self-test-only checker
self-test: detected missing cited checker
self-test: detected document cites unrun checker
self-test: detected allowlisted script wired plain
self-test: detected allowlisted script missing self-test
self-test: detected missing allowlisted script
self-test: detected workflow invokes missing file
self-test: detected commented-out invocation
self-test: detected no scripts
self-test: detected no invocations
self-test: detected no documents
self-test: pass (13 negative controls)
exit: 0
```

### Command 346 — narrow checker

```text
$ python3 scripts/check_ci_test_discovery.py
reached: reference/ai_delegation files=6 <- protocol/Offline reference state machines and OpenAPI pins
reached: reference/booking_resale_admission files=17 <- protocol/Offline reference state machines and OpenAPI pins
reached: reference/credit_advance_f04 files=8 <- protocol/Offline reference state machines and OpenAPI pins
reached: reference/rights_scale files=6 <- rights-scale/Rights-scale Move and model tests
reached: reference/settlement_f01_f03 files=11 <- protocol/Offline reference state machines and OpenAPI pins
reached: reference/token_reward files=8 <- protocol/Offline reference state machines and OpenAPI pins
reached: reference/rights_scale/client/admission-packet.test.mjs <- rights-scale/Offline admission packet regressions
reached: reference/rights_scale/client/mint-note.test.mjs <- rights-scale/Offline mint note regressions
reached: reference/rights_scale/client/ptau-header.test.mjs <- rights-scale/Offline PTAU header parsing regressions
reached: reference/rights_scale/client/spend-witness.test.mjs <- rights-scale/Offline spend witness regressions
reached: reference/rights_scale/client/verifier-binding.test.mjs <- rights-scale/Offline verifier binding regressions
reached: reference/rights_scale/client/witness-reconstruction.test.mjs <- rights-scale/Offline witness reconstruction regressions
reached: reference/rights_scale/client/zk-helpers.test.mjs <- rights-scale/Offline public-byte encoding regressions
reached: reference/rights_scale/client/zk-policy-v2.test.mjs <- rights-scale/Offline manifest validation regressions
reached: integration_gate.test_http_gate <- protocol/Non-production HTTP integration gate
reached: integration_gate.test_offline_limits <- protocol/Offline reference state machines and OpenAPI pins
reached: readiness.test_conformance_sensitivity <- protocol/Non-production HTTP integration gate via readiness.test_faults
reached: readiness.test_faults <- protocol/Non-production HTTP integration gate
excluded: reference/v0.1: historical v0.1 reference tree; no protocol.yml step runs its tests and this guard does not claim they run
excluded: reference/v0.2: historical v0.2 reference tree; no protocol.yml step runs its tests and this guard does not claim they run
excluded: reference/v0.3-rc1: historical v0.3-rc1 tree; its Python tests are invoked inside scripts/verify_runtime.py, which this guard does not parse, so no run is claimed here
ci test discovery ok: reference_suites=6 node_tests=8 modules=4 excluded=3
exit: 0
```

### Command 347 — narrow checker

```text
$ python3 scripts/check_ci_test_discovery.py --self-test
self-test: detected unwired suite directory
self-test: detected unwired node test
self-test: detected unreached top-level module
self-test: detected unreached nested module
self-test: detected unreached module outside a package
self-test: detected exclusion without reason
self-test: detected module reached only by import statement
self-test: detected module reached only as a package attribute
self-test: detected partial from-import
self-test: detected reference test in a non-package subdirectory
self-test: detected commented-out wiring line
self-test: detected unexpanded loop variable
self-test: detected unsupported discover option
self-test: detected workflow names missing module
self-test: detected workflow names missing node test
self-test: detected exclusion of an absent tree
self-test: detected excluded tree wired by discover
self-test: detected empty workflow
self-test: pass (18 negative controls)
exit: 0
```

### Command 357 — acceptance merge 314

```text
$ git show -s --format=%P 035d5705c93b318a49941ce5f7410f843360c427
09470db220965390edeecdb75f56f8c827dd15b6 bce1c9e870f90fd180e0780fdb38acd50f8a5c24
exit: 0
```

### Command 358 — acceptance merge 315

```text
$ git show -s --format=%P eb1caf8285c174697d78834246a304ffe9006427
035d5705c93b318a49941ce5f7410f843360c427 90d827dc09132d9ceb4b7e721c1f5617b9e47fc8
exit: 0
```

### Command 359 — acceptance merge 316

```text
$ git show -s --format=%P 876f41067bc7eb70bcd6ebd9c744c11b46f046b6
eb1caf8285c174697d78834246a304ffe9006427 87f40aa89d77f924481ff1dd6cc828d81a7b8b46
exit: 0
```

### Command 360 — acceptance merge 317

```text
$ git show -s --format=%P d016caee4ae40f28f531809359ee77ac22db0073
876f41067bc7eb70bcd6ebd9c744c11b46f046b6 7ba8003f4a18bbd622ce87b1cfb0fa856e4a4178
exit: 0
```

### Command 361 — acceptance merge 318

```text
$ git show -s --format=%P 70b976c0b8db686b1d21ff0831c275abf77a3d0a
d016caee4ae40f28f531809359ee77ac22db0073 41abd142e7b16a6ab1370cf001b3fccb4b720900
exit: 0
```

### Command 362 — acceptance merge 319

```text
$ git show -s --format=%P 9d50fb660248b66a5959f48f7dc96e68c9d5530b
70b976c0b8db686b1d21ff0831c275abf77a3d0a c677f09bea37bb1fe00a768b9ef369dfa5dc6d41
exit: 0
```

### Command 363 — acceptance merge 320

```text
$ git show -s --format=%P 9ed15a7adc93359e99bb5c3512a3ca20c77cb264
9d50fb660248b66a5959f48f7dc96e68c9d5530b 150180214612b7b6f55bb4f6c49834bd9f5cec88
exit: 0
```

### Command 364 — acceptance merge 321

```text
$ git show -s --format=%P 8e4813e868961adbabb7d1ee450a346f8fb6add1
9ed15a7adc93359e99bb5c3512a3ca20c77cb264 e265d30d10e9f18feb7c9fb968e09a5c6260e9ad
exit: 0
```

### Command 365 — actual index diff

```text
$ git diff --name-only origin/main
docs/README.md
exit: 0
```

### Command 366 — actual untracked

```text
$ git ls-files --others --exclude-standard
docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md
exit: 0
```

### Command 367 — all source invocation references

```text
$ git grep -n r1_perf_probe HEAD -- '*.rs' '*.py' '*.yml' '*.yaml'
HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs:31:            "usage: r1_perf_probe <output-dir> <samples:1..100000> <command-limit> <rate:0=service-only>"
HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs:165:            "runtime/crates/kix-kernel/examples/r1_perf_probe.rs",
HEAD:runtime/crates/kix-kernel/tests/e4_state_model.rs:1914:        "examples/r1_perf_probe.rs",
HEAD:scripts/check_performance_measurement_evidence_map.py:18:                'runtime/crates/kix-kernel/examples/r1_perf_probe.rs')
exit: 0
```

### Command 368 — numbered source excerpt

```text
$ git show HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs (numbered output lines 8–11)
8: const LOCKED_KERNEL: &str = "69564b166f0c27f9af5d8422f0a466b18d74c20f";
9: const LOCKED_QUARANTINE: &str = "b607996c83a119c349f1cc90469ac1ba82764e20";
10: const LOCKED_EDGE: &str = "d37ea7df55423c83bedee16bf12bdc8dd61f7cae";
11: const LOCKED_MODEL: &str = "f020860b86933bf7511befccdb833b0c532b3629";
exit: 0
```

### Command 369 — numbered source excerpt

```text
$ git show HEAD:runtime/crates/kix-kernel/examples/r1_perf_probe.rs (numbered output lines 39–99)
39:     if count == 0 || count > 100_000 || limit < 2 {
40:         return Err("invalid sample count or command limit".into());
41:     }
42:     let repo = repo_root()?;
43:     let kernel_blob = git_line(
44:         &repo,
45:         &["hash-object", "--", "runtime/crates/kix-kernel/src/lib.rs"],
46:     )?;
47:     let quarantine_blob = git_line(
48:         &repo,
49:         &[
50:             "hash-object",
51:             "--",
52:             "runtime/crates/kix-kernel/tests/quarantine_capacity.rs",
53:         ],
54:     )?;
55:     let edge_blob = git_line(
56:         &repo,
57:         &[
58:             "hash-object",
59:             "--",
60:             "runtime/crates/kix-kernel/tests/contract_edge_cases.rs",
61:         ],
62:     )?;
63:     let model_blob = git_line(
64:         &repo,
65:         &[
66:             "hash-object",
67:             "--",
68:             "runtime/crates/kix-kernel/tests/support/model_v4.rs",
69:         ],
70:     )?;
71:     if kernel_blob != LOCKED_KERNEL
72:         || quarantine_blob != LOCKED_QUARANTINE
73:         || edge_blob != LOCKED_EDGE
74:         || model_blob != LOCKED_MODEL
75:     {
76:         return Err("frozen blob mismatch; refusing to write unbound performance evidence".into());
77:     }
78:     let mut reports = Vec::with_capacity(4);
79:     for workload in [
80:         probe::Workload::Uniform,
81:         probe::Workload::HotSeat,
82:         probe::Workload::Retry,
83:         probe::Workload::Conflict,
84:     ] {
85:         reports.push(probe::run(workload, count, limit, rate));
86:     }
87:     let low_count = probe::low_load_sample_count(limit);
88:     let low = probe::run(probe::Workload::Uniform, low_count, limit, rate);
89:     if !low.low_load() {
90:         return Err(
91:             "low-load uniform control saturated or rejected; no evidence directory was written"
92:                 .into(),
93:         );
94:     }
95:     std::fs::create_dir_all(&directory)?;
96:     for report in reports {
97:         write_workload(&directory, report, rate, limit)?;
98:     }
99:     std::fs::write(directory.join("low-load-uniform.csv"), &low.raw_csv)?;
exit: 0
```

### Command 370 — numbered source excerpt

```text
$ git show HEAD:docs/contracts/CONTRACT_INVARIANTS.md (numbered output lines 25–35)
25: ## 2. Exact existing contract anchors
26:
27: All paths below refer to commit
28: `0394a36a655b86bacb568b055d377d4c4fd91185` (unless expressly stated otherwise).
29:
30: | ID | Path | Full Git blob | Clauses used |
31: |---|---|---|---|
32: | A | docs/adr/0001-ktx-authority-commit-recovery.md | 07c36869e7b68fff10b02e6c59d7119df56d0785 | §3 stable identity/original result; §4 atomic reservation; §5 read-only replay; §6 event vs economic dedupe; §8 inventory and bounds |
33: | L | docs/contracts/STATE_LIFECYCLE.md | e953c4870aaeee24b13c75a8647c50609720ae01 | §2 command/observation lifetimes; §3 LC-FACT; §5 LC-TERM captured facts are not erased; §6 no invented GC |
34: | R | runtime/crates/kix-kernel/README.md | 900866ee99a71254fb7da1ad2aa4640477ac550c | Implemented meaning; Observation reservation and remaining gaps; bounded sum and first-capture contract |
35:
exit: 0
```

### Command 371 — numbered source excerpt

```text
$ git show HEAD:docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md (numbered output lines 80–88)
80: | P-E4-COMPARISONS | 131072 comparisons | 4 * 256 * 128 = 131072 comparisons | MATCH |
81:
82: ## 4. Findings
83:
84: - **F-B1 — class B, historical anchor drift.** Contract §2 explicitly pins commit 0394a36a655b86bacb568b055d377d4c4fd91185. Its STATE_LIFECYCLE blob e953c4870aaeee24b13c75a8647c50609720ae01, ADR blob 07c36869e7b68fff10b02e6c59d7119df56d0785 and kernel README blob 900866ee99a71254fb7da1ad2aa4640477ac550c differ from current 8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d, 054bc714b3c475fb8536df8d2d788b42e8c74b6c and 788896ed3e00bae3d06d26b7e2ce999a00ff1029 respectively. Historical pins are preserved; no old CI transfers to these current sources. Owner: contract owner.
85: - **F-B2 — class B, INV-3 sensitivity boundary (narrowed).** The new inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations test rejects observer copies with (a) altered replay replies, (b) changed public state or a false Eq sentinel, and (c) rewritten first results after later state changes, for both Held and Rejected first results. Unmodified observations pass. The generated corpus uses the same check_replay predicate. Remaining boundaries: admitted time has no public accessor and is witnessed only through whole-kernel Eq, and the fixture author knew the kernel source. Contract §4 still names four corruptions; this extra sensitivity dimension is not a contract violation. Owner: kernel contract owner/non-author A2 reviewer.
86: - **F-B3 — class B, reply observation boundary.** “Every reply” in §4 means public post-state predicates run after every reply. Non-reserve reply values are only read via is_ok(); expected business replies are not predicted. Reserve replay has stronger typed-result assertions. Owner: kernel contract owner/non-author A2 reviewer.
87: - **F-B4 — class B, historical model naming.** The e4 module description and locked_v4_matches_independent_state_model identifier use independent language, while contract §1 corrects the provenance. E4 is source-informed in this map. Representation separation and finite agreement do not establish specification independence. Owner: contract owner/non-author A2 reviewer.
88: - **F-B5 — class B, availability example boundary.** The seven S5 success examples assert Held only where ADR §§3/4/6/8, STATE_LIFECYCLE §2/§5.7 or the kernel README require a reservation to succeed. Left undefined and therefore not asserted as required: (a) reuse after cancel_scope, because ADR §7 makes cancellation a sticky local business fence and no contract defines reopening; (b) reuse of inventory released when a late capture produces ReturnRequired; (c) the bundle maximum value and whether record-count limits are inclusive, since the README names maximum bundle lengths and configured record counts without values, so the MAX_BUNDLE and last-slot cases are labelled characterizations; (d) the exact Rejection and KernelError variants and cross-kind selection handling on the unrelated-rejection steps. The author knew the locked kernel source when choosing boundaries. Owner: kernel contract owner/non-author A2 reviewer.
exit: 0
```

### Command 372 — numbered source excerpt

```text
$ git show HEAD:reference/ai_delegation/ai_delegation_mock.py (numbered output lines 276–295)
276:         proposal["effects_executed"] = False
277:         self._invariant()
278:         return {"duplicate": False, "proposal": self._view_proposal(proposal)}
279:
280:     def call_tool(self, actor: object, grant_id: object, tool: object, args: object, now: object) -> dict:
281:         _require(type(actor) is str and actor in self._agents, "UNKNOWN_ACTOR")
282:         grant_id = _ident(grant_id)
283:         _require(type(tool) is str, "INVALID_ID")
284:         if tool in DENYLIST:
285:             raise AiDelegationError(DENYLIST[tool])
286:         _require(tool in ALLOWLIST, "TOOL_NOT_ALLOWED")
287:         now = _logical(now)
288:         _require(type(args) is dict, "INVALID_ID")
289:         grant = self._grants.get(grant_id)
290:         _require(grant is not None, "UNKNOWN_GRANT")
291:         _require(grant["agent_id"] == actor, "UNKNOWN_ACTOR")
292:         if tool == "withdraw_proposal":
293:             return self._withdraw(grant, args)
294:         if tool == "propose_action":
295:             return self._propose_action(grant, args, now)
exit: 0
```

### Command 373 — numbered source excerpt

```text
$ git show HEAD:sdk/compat/verify_compat.mjs (numbered output lines 160–238)
160:     if (typeof ref.path !== "string" || ref.path.includes("..") || ref.path.startsWith("/")) {
161:       errors.push(`${label} path drift`);
162:       continue;
163:     }
164:     const bytes = readExact(resolve(ROOT, ref.path), errors, label);
165:     if (!bytes) {
166:       continue;
167:     }
168:     if (sha256Hex(bytes) !== ref.sha256 || gitBlobId(bytes) !== ref.gitBlob) {
169:       errors.push(`${label} bytes drift`);
170:     }
171:     loaded[label] = bytes;
172:   }
173:
174:   if (!sameKeys(keysOf(manifest.generator), ["path", "sha256", "toolchain"])) {
175:     errors.push("generator field set drift");
176:   } else {
177:     const toolchains = JSON.parse(readFileSync(resolve(ROOT, "toolchains.json"), "utf8"));
178:     const expectedToolchain = `node-${toolchains.nodeMajor}`;
179:     if (manifest.generator.toolchain !== expectedToolchain) {
180:       errors.push("toolchain drift");
181:     }
182:     const running = process.versions.node.split(".")[0];
183:     if (running !== String(toolchains.nodeMajor)) {
184:       errors.push("running node does not match toolchains.json");
185:     }
186:     if (manifest.generator.path !== "sdk/generate/generate_client.mjs") {
187:       errors.push("generator path drift");
188:     }
189:     const generatorBytes = readExact(resolve(ROOT, manifest.generator.path), errors, "generator");
190:     if (generatorBytes && sha256Hex(generatorBytes) !== manifest.generator.sha256) {
191:       errors.push("generator bytes drift");
192:     }
193:   }
194:
195:   if (!sameKeys(keysOf(manifest.sdk_output), ["path", "sha256"])) {
196:     errors.push("sdk_output field set drift");
197:   } else if (manifest.sdk_output.path !== "sdk/generated/catalogue.ts") {
198:     errors.push("sdk_output path drift");
199:   } else {
200:     const outputBytes = readExact(resolve(ROOT, manifest.sdk_output.path), errors, "sdk_output");
201:     if (outputBytes && sha256Hex(outputBytes) !== manifest.sdk_output.sha256) {
202:       errors.push("sdk_output bytes drift");
203:     }
204:   }
205:
206:   if (!sameKeys(keysOf(manifest.source_references), ["extension_profile", "fixture_profile"])) {
207:     errors.push("source_references field set drift");
208:   } else if (manifest.source_references.fixture_profile !== "reference/v0.3-rc1/protocol_contract.json") {
209:     errors.push("source_references drift");
210:   } else {
211:     const extension = manifest.source_references.extension_profile;
212:     if (extension !== false) {
213:       if (!sameKeys(keysOf(extension), ["gitBlob", "path", "sha256"])) {
214:         errors.push("extension_profile field set drift");
215:       } else if (extension.path !== "docs/contracts/openapi/fsm-command-contract.json") {
216:         errors.push("extension_profile path drift");
217:       } else {
218:         const extensionBytes = readExact(resolve(ROOT, extension.path), errors, "extension_profile");
219:         if (
220:           extensionBytes &&
221:           (sha256Hex(extensionBytes) !== extension.sha256 || gitBlobId(extensionBytes) !== extension.gitBlob)
222:         ) {
223:           errors.push("extension_profile bytes drift");
224:         }
225:       }
226:     }
227:   }
228:
229:   if (!Array.isArray(manifest.vectors)) {
230:     errors.push("vectors drift");
231:   }
232:
233:   const profilePath = resolve(ROOT, "sdk/compat/profiles", `${manifest.profile_revision}.profile.json`);
234:   const profileBytes = readExact(profilePath, errors, "profile");
235:   if (profileBytes && sha256Hex(profileBytes) !== manifest.profile_sha256) {
236:     errors.push("profile bytes drift");
237:   }
238:   let profile;
exit: 0
```

### Command 376 — CI offline block

```text
$ python3 scripts/check_rs_profile_traceability.py
rs profile traceability ok: blueprint=47 profile=47 expected=47
exit: 0
```

### Command 377 — CI offline block

```text
$ python3 scripts/check_rs_profile_traceability.py --self-test
self-test: detected removed RS-C01 from profile (missing in profile: RS-C01)
self-test: detected duplicated RS-C01 in profile (duplicated in profile: RS-C01 (2))
self-test: detected removed IM-01 from profile (missing in profile: IM-01)
self-test: detected duplicated IM-01 in profile (duplicated in profile: IM-01 (2))
self-test: detected removed RS-C03 from blueprint (missing in blueprint: RS-C03)
self-test: detected duplicated RS-C03 in blueprint (duplicated in blueprint: RS-C03 (2))
self-test: detected extra ids in profile (extra in profile: RS-C99 (1))
self-test: pass
exit: 0
```

### Command 378 — CI offline block

```text
$ python3 scripts/check_read_model_source_map.py
read model source map ok: queries=13 anchors=128 catalogues=2 citations=145
exit: 0
```

### Command 379 — CI offline block

```text
$ python3 scripts/check_read_model_source_map.py --self-test
self-test: detected anchor line moved (A01: reference/booking_resale_admission/mock_gates.py:96 lacks self._shows (token at lines 97,148,170,657,905))
self-test: detected anchor line out of range (A01: reference/booking_resale_admission/mock_gates.py has 936 lines, cited 99999)
self-test: detected anchor token changed (A01: reference/booking_resale_admission/mock_gates.py:97 lacks self._nope)
self-test: detected query row dropped (missing query row: get_show)
self-test: detected query row duplicated (duplicated query row: get_show (2))
self-test: detected unknown query row (unknown query row: get_zilch)
self-test: detected status flipped (status drift for list_shows: declared SOURCE_FOUND but absence anchors remain: A04,A05)
self-test: detected source label on missing query (status drift for list_shows: declared SOURCE_MISSING but `list_shows 원천` anchors exist: A03)
self-test: detected absence anchors dropped (status drift for list_shows: declared SOURCE_MISSING but no def list_shows( absence anchor)
self-test: detected catalogue expectation flipped (catalogue C02: query name get_show must be in docs/contracts/openapi/fsm-command-contract.json commands)
self-test: detected catalogue row dropped (missing catalogue expectation for reference/v0.3-rc1/protocol_contract.json)
self-test: detected rmq cite out of range (citation out of range: docs/contracts/READ_MODEL_QUERIES.md:99999 (405 lines))
self-test: detected blob id mismatch (READ_MODEL_QUERIES.md blob drift: doc cites 0000000000000000000000000000000000000000, actual 06b9ec68f9dc9dd4af4d70c236360be964a84ae1)
self-test: detected cited surface renamed (A06: reference/booking_resale_admission/reservation_fsm.py:705 lacks def view_show()
self-test: detected absent surface added (A04: def list_shows( must not appear in reference/booking_resale_admission/mock_gates.py)
self-test: detected query in core catalogue (catalogue C01: query name now in reference/v0.3-rc1/protocol_contract.json commands: get_show)
self-test: pass
exit: 0
```

### Command 382 — CI offline block

```text
$ python3 scripts/check_i12_proof_ids.py
i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14
exit: 0
```

### Command 383 — CI offline block

```text
$ python3 scripts/check_i12_proof_ids.py --self-test
self-test: detected removed P1 heading from proof (missing in proof: P1)
self-test: detected removed A5 row from proof (missing in proof: A5)
self-test: detected removed A9 row from pack (missing in pack: A9)
self-test: detected extra A11 row in pack (extra in pack: A11 (1))
self-test: detected extra P9 heading in proof (extra in proof: P9 (1))
self-test: detected unresolved proof §9 citation in pack (unresolved section reference in pack line 220: proof §9)
self-test: pass
exit: 0
```

### Command 384 — CI offline block

```text
$ python3 scripts/check_delegation_layer_matrix.py
delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6
exit: 0
```

### Command 385 — CI offline block

```text
$ python3 scripts/check_delegation_layer_matrix.py --self-test
self-test: detected removed DLG-17 row (missing in matrix: DLG-17)
self-test: detected dangling path (DLG-06: chain citation reference/rights_scale/sui/sources/NO_SUCH_FILE.move does not exist)
self-test: detected dangling symbol (DLG-06: chain citation reference/rights_scale/sui/sources/rights_scale.move::no_such_fn_9f3a is not defined in the file)
self-test: detected duplicated DLG-17 row (duplicated in matrix: DLG-17 (2))
self-test: detected unknown status (DLG-01: unknown status 'SUFFICIENT')
self-test: detected mock test that does not cite the id (DLG-01: mock tests ['test_period_boundaries'] differ from docstring citations ['test_query_does_not_change_state_and_propose_is_a_memo'])
self-test: detected MOCK_ONLY row with a chain citation (DLG-01: MOCK_ONLY needs none in chain and executor cells)
self-test: detected id dropped from the Neither line (gap summary '- Neither:' lists ['DLG-02', 'DLG-03', 'DLG-04', 'DLG-05', 'DLG-07', 'DLG-08', 'DLG-09', 'DLG-10', 'DLG-11', 'DLG-12', 'DLG-14', 'DLG-15', 'DLG-16', 'DLG-17', 'DLG-18', 'DLG-19', 'DLG-21', 'DLG-24', 'DLG-25', 'DLG-27', 'DLG-28', 'DLG-29', 'DLG-30', 'DLG-31', 'DLG-33', 'DLG-34', 'DLG-35', 'DLG-36'] but the table gives ['DLG-01', 'DLG-02', 'DLG-03', 'DLG-04', 'DLG-05', 'DLG-07', 'DLG-08', 'DLG-09', 'DLG-10', 'DLG-11', 'DLG-12', 'DLG-14', 'DLG-15', 'DLG-16', 'DLG-17', 'DLG-18', 'DLG-19', 'DLG-21', 'DLG-24', 'DLG-25', 'DLG-27', 'DLG-28', 'DLG-29', 'DLG-30', 'DLG-31', 'DLG-33', 'DLG-34', 'DLG-35', 'DLG-36'])
self-test: pass
exit: 0
```

### Command 386 — CI offline block

```text
$ python3 scripts/check_rs_predicate_evidence_map.py
rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2
exit: 0
```

### Command 387 — CI offline block

```text
$ python3 scripts/check_rs_predicate_evidence_map.py --self-test
self-test: detected removed RS-C01 row (missing in map: RS-C01)
self-test: detected duplicated RS-C01 row (duplicated in map: RS-C01 (2))
self-test: detected dangling path (RS-C01: move citation reference/rights_scale/sui/tests/no_such_file.move does not exist)
self-test: detected dangling symbol (RS-C01: move citation reference/rights_scale/sui/tests/predicate_tests.move::no_such_fn_9f3a is not defined in the file)
self-test: detected unknown status (RS-C01: unknown status 'SUFFICIENT')
self-test: detected NOT_COVERED row that carries a citation (RS-C01: NOT_COVERED row carries a citation)
self-test: detected uncited row that is not NOT_COVERED (RS-C13: COVERED_MODEL_OR_MEMORY row has no citation, so it must be NOT_COVERED)
self-test: detected altered test id (RS-C01: test id 'RS-C01-T9' differs from the profile 'RS-C01-T1')
self-test: detected owner not written in the profile (RS-C02: owner part 'Nobody Else' is not written in the profile)
self-test: detected empty missing cell on a PARTIAL row (RS-C07: PARTIAL row must say what is missing)
self-test: detected citation under reference/v0.3-rc1 (RS-C07: python citation reference/v0.3-rc1/x.py is under reference/v0.3-rc1)
self-test: detected split label dropped (RS-C07: split label '(a)' is missing)
self-test: detected misspelled node:test name (RR-4: local citation reference/rights_scale/client/witness-reconstruction.test.mjs::populated_tre is not defined in the file)
self-test: detected wrong counts line (counts line 'Counts: COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=96 NOT_COVERED=0 MEASUREMENT_ONLY=2' differs from the table 'Counts: COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2')
self-test: pass
exit: 0
```

### Command 388 — CI offline block

```text
$ python3 scripts/check_rs_im_evidence_map.py
rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2
exit: 0
```

### Command 389 — CI offline block

```text
$ python3 scripts/check_rs_im_evidence_map.py --self-test
self-test: detected removed IM-01 row (missing in map: IM-01)
self-test: detected duplicated IM-01 row (duplicated in map: IM-01 (2))
self-test: detected dangling path (IM-01: move citation reference/rights_scale/sui/tests/no_such_file.move does not exist)
self-test: detected dangling symbol (IM-01: move citation reference/rights_scale/sui/tests/predicate_tests.move::no_such_fn_9f3a is not defined in the file)
self-test: detected unknown status (IM-01: unknown status 'SUFFICIENT')
self-test: detected altered treatment word (IM-01: treatment '유지' differs from the profile '변경')
self-test: detected treatment word that is not a profile word (IM-01: treatment 'keep' is not one of the profile words)
self-test: detected NOT_COVERED row that carries a citation (IM-01: NOT_COVERED row carries a citation)
self-test: detected PARTIAL row with an empty missing cell (IM-03: PARTIAL row must say what is missing)
self-test: detected PARTIAL row with an owner the profile does not write (IM-03: owner part 'Nobody Else' is not written in the profile)
self-test: detected citation under reference/v0.3-rc1 (IM-01: python citation reference/v0.3-rc1/x.py is under reference/v0.3-rc1)
self-test: detected UNCHANGED_BY_DESIGN on a changed row (IM-01: UNCHANGED_BY_DESIGN is only for 손대지 않음 rows)
self-test: detected COVERED status on an untouched row (IM-25: a 손대지 않음 row is never COVERED_MODEL_OR_MEMORY)
self-test: detected misspelled node:test name (IM-19: local citation reference/rights_scale/client/witness-reconstruction.test.mjs::populated_tre is not defined in the file)
self-test: detected wrong cell count (IM-01: expected 11 cells, found 12)
self-test: detected wrong counts line (counts line 'Counts: COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=912 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2' differs from the table 'Counts: COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2')
self-test: pass
exit: 0
```

### Command 390 — CI offline block

```text
$ python3 scripts/check_tl_predicate_evidence_map.py
tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7
exit: 0
```

### Command 391 — CI offline block

```text
$ python3 scripts/check_tl_predicate_evidence_map.py --self-test
self-test: detected removed TK-4 row (missing in map: TK-4)
self-test: detected duplicated TK-4 row (duplicated in map: TK-4 (2))
self-test: detected invented id (invented id: TK-99)
self-test: detected dangling path (TK-4: citation reference/token_reward/no_such_file.py is not an allowed evidence path)
self-test: detected dangling symbol (TK-4: citation reference/token_reward/test_reward_model.py::no_such_fn_9f3a is not defined in the file)
self-test: detected unknown status (TK-4: unknown status 'SUFFICIENT')
self-test: detected uncited row that is not NOT_VERIFIABLE_NO_PACKAGE (V1: HARNESS_AUTHOR_SIDE row has no citation)
self-test: detected empty missing cell (V1: empty missing-or-open cell)
self-test: detected owner not in source (V1: owner 'Nobody Else' not found in docs/blueprints/optional-native-token-v1/README.md)
self-test: detected stale counts line (counts line 'Counts: HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=9924 PARTIAL=7' differs from 'Counts: HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7')
self-test: pass
exit: 0
```

### Command 392 — CI offline block

```text
$ python3 scripts/check_contract_error_codes.py
contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0
exit: 0
```

### Command 393 — CI offline block

```text
$ python3 scripts/check_contract_error_codes.py --self-test
self-test: detected removed doc row (SET: INVALID_ID missing in doc)
self-test: detected duplicated doc row (SET: INVALID_ID duplicated in doc (2))
self-test: detected misspelled code (missing side) (SET: INVALID_ID missing in doc)
self-test: detected misspelled code (extra side) (SET: INVALID_IDX is not in the contract table)
self-test: detected stale counts line (counts line 'Counts: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=9199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0' differs from the table 'Counts: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0')
self-test: detected wrong cell count (SET: expected 6 cells, found 7)
self-test: detected unknown status (SET INVALID_ID: unknown status 'SUFFICIENT')
self-test: detected MOCK_INVARIANT row (SET: MOCK_INVARIANT is excluded and must not have a row)
self-test: detected removed raise site (SET INVALID_ID: Raised cites a site but none is derived)
self-test: detected removed asserting test (SET INVALID_ID: Asserted cites a site but none is derived)
self-test: detected Raised cell set to no (SET INVALID_ID: Raised is no but the sources have 2 site(s))
self-test: detected dangling path (SET INVALID_ID: Raised citation reference/settlement_f01_f03/no_such.py::x: file does not exist)
self-test: detected dangling symbol (SET INVALID_ID: Raised citation reference/settlement_f01_f03/mock_settlement.py::no_such_fn_9f3a: symbol is not defined in the file)
self-test: detected citation outside the suite directory (SET INVALID_ID: Raised citation reference/ai_delegation/ai_delegation_mock.py::x is outside the suite directory reference/settlement_f01_f03)
self-test: detected citation under reference/v0.3-rc1 (SET INVALID_ID: Raised citation reference/v0.3-rc1/x.py::y is under reference/v0.3-rc1)
self-test: detected citation that is not a derived site (SET INVALID_ID: Raised citation reference/settlement_f01_f03/mock_settlement.py::MockSettlement.__init__ is not a derived site)
self-test: detected contract table with an added code (SET: ADDED_PROBE_CODE missing in doc)
self-test: detected contract table with a removed heading (SET: heading '## 6. 오류 코드' not found)
self-test: detected COVERED row without an asserting test (SET INVALID_ID: COVERED needs both a raise site and an asserting test)
self-test: detected added code in the BRA-RES contract table (BRA-RES: ADDED_PROBE_CODE missing in doc)
self-test: detected removed raise site on a BRA-RES row (BRA-RES TICKET_NOT_ISSUED: Raised cites a site but none is derived)
self-test: detected citation that is not a derived site on a BRA-RES row (BRA-RES TICKET_NOT_ISSUED: Raised citation reference/booking_resale_admission/resale_fsm.py::ResaleMachine._listing is not a derived site)
self-test: detected missing section 9 raise citation (BRA-RES9 ALREADY_CONSUMED: Raised is no but the sources have 1 site(s))
self-test: detected missing section 9 assertion citation (BRA-RES9 ALREADY_CONSUMED: Asserted is no but the sources have 11 site(s))
self-test: detected added code in the section 9.2 effect column (BRA-RES9: ADDED_PROBE_CODE missing in doc)
self-test: detected added code in the section 9.5 code column (BRA-RES9: ADDED_PROBE_CODE missing in doc)
self-test: detected removed section 9.5 heading (BRA-RES9: heading '### 9.5 정산 게이트' not found)
self-test: detected malformed section 9.5 row (BRA-RES9: heading '### 9.5 정산 게이트': expected 2 cells, found 3)
self-test: detected CLASS_B status on an asserted code with a none note (SET INVALID_ID: CLASS_B row needs a reasoned note)
self-test: detected CLASS_C status on an asserted code (SET INVALID_ID: CLASS_C row is asserted by a test, so it is COVERED)
self-test: pass
exit: 0
```

### Command 394 — CI offline block

```text
$ python3 scripts/check_adapter_identity_map.py
adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8
exit: 0
```

### Command 395 — CI offline block

```text
$ python3 scripts/check_adapter_identity_map.py --self-test
self-test: detected removed TransmissionId row (missing in map: TransmissionId)
self-test: detected duplicated TransmissionId row (duplicated in map: TransmissionId (2))
self-test: detected invented id (invented id in map section: FAKE-ID-9f3a)
self-test: detected dangling path (TransmissionId: kernel citation runtime/crates/kix-kernel/tests/no_such.rs does not exist)
self-test: detected dangling symbol (TransmissionId: kernel citation runtime/crates/kix-kernel/src/lib.rs::no_such_fn_9f3a is not defined in the file)
self-test: detected citation in the wrong column (TransmissionId: mock citation runtime/crates/kix-kernel/src/lib.rs is outside the mock column paths)
self-test: detected citation under reference/v0.3-rc1 (TransmissionId: mock citation reference/v0.3-rc1/core.py is under reference/v0.3-rc1)
self-test: detected unknown status (TransmissionId: unknown status 'SUFFICIENT')
self-test: detected status that does not match the cells (RULE-OBSERVE-KEY: status PARTIAL should be CARRIED for these cells)
self-test: detected UNDETERMINED cell with no owner (TransmissionId: profile cell has UNDETERMINED with no owner)
self-test: detected UNDETERMINED owner not in the contract (TransmissionId: owner 'Nobody Else' is not written in the contract)
self-test: detected non-CARRIED row with no owner (TransmissionId: UNDETERMINED row must have an owner)
self-test: detected owner not in the contract (TransmissionId: owner 'Nobody Else' is not written in the contract)
self-test: detected NO_SURFACE row that carries a citation (S4-SOURCE: status NO_SURFACE should be UNDETERMINED for these cells)
self-test: detected missing citation under wrong prefix is not the only bug; free-text-only surface cell (TransmissionId: mock cell is neither none, a citation, nor an owned UNDETERMINED)
self-test: detected wrong counts line (counts line 'Counts: CARRIED=2 PARTIAL=997 NO_SURFACE=0 UNDETERMINED=8' differs from the table 'Counts: CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8')
self-test: detected map cell that cites the missing cell (TransmissionId: ? citation runtime/crates/kix-kernel/src/lib.rs is inside the missing cell)
self-test: detected mutated locked blob (locked blob mismatch: runtime/crates/kix-kernel/src/lib.rs (have 2b91c41288b048a233f95b2d4e285b9c262d2333, want 69564b166f0c27f9af5d8422f0a466b18d74c20f))
self-test: detected removed contract anchor (RULE-OBSERVE-KEY: contract anchor 'observe_capture`의 중복 키는 `(provider, account, event_id)`다' is gone)
self-test: pass
exit: 0
```

### Command 396 — CI offline block

```text
$ python3 scripts/check_v5_transition_evidence_map.py
v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0
exit: 0
```

### Command 397 — CI offline block

```text
$ python3 scripts/check_v5_transition_evidence_map.py --self-test
self-test: exercised v5 tests bare existing path (alone and mixed lists)
self-test: exercised v5 tests bare missing path (alone and mixed lists)
self-test: exercised v5 tests bare injected path (alone and mixed lists)
self-test: exercised v5 tests empty symbol (alone and mixed lists)
self-test: exercised v5 tests spaces-only symbol (alone and mixed lists)
self-test: exercised v5 tests tabs-only symbol (alone and mixed lists)
self-test: exercised v5 tests missing file (alone and mixed lists)
self-test: exercised v5 tests missing function (alone and mixed lists)
self-test: exercised v5 tests helper function (alone and mixed lists)
self-test: exercised v5 tests invalid test path (alone and mixed lists)
self-test: exercised stop guard bare existing path (alone and mixed lists)
self-test: exercised stop guard bare missing path (alone and mixed lists)
self-test: exercised stop guard bare injected path (alone and mixed lists)
self-test: exercised stop guard empty symbol (alone and mixed lists)
self-test: exercised stop guard spaces-only symbol (alone and mixed lists)
self-test: exercised stop guard tabs-only symbol (alone and mixed lists)
self-test: exercised stop guard missing file (alone and mixed lists)
self-test: exercised stop guard missing function (alone and mixed lists)
self-test: exercised stop guard helper function (alone and mixed lists)
self-test: exercised stop guard invalid test path (alone and mixed lists)
self-test: detected removed TERM row (missing in map: TERM)
self-test: detected duplicated TERM row (duplicated in map: TERM (2))
self-test: detected invented id (invented id in map section: FAKE-ID-9f3a)
self-test: detected dangling path (citation runtime/crates/kix-kernel-v5/tests/no_such.rs::x does not exist)
self-test: detected helper fn cited as a test (citation runtime/crates/kix-kernel-v5/tests/termination.rs::unchanged is not defined in the file)
self-test: detected dangling test symbol (citation runtime/crates/kix-kernel-v5/tests/termination.rs::no_such_test_9f3a is not defined in the file)
self-test: detected test citation in the surface column (TERM: v5 surface citation runtime/crates/kix-kernel-v5/tests/termination.rs is not the v5 lib.rs)
self-test: detected citation under reference/v0.3-rc1 (citation reference/v0.3-rc1/core.py::execute is under reference/v0.3-rc1)
self-test: detected STOPPED row carrying a test (SLOT-RELEASE: status STOPPED should be TESTED for these cells)
self-test: detected TESTED row with none tests (TERM: status TESTED should be OPEN for these cells)
self-test: detected STOPPED without a decision citation (SLOT-RELEASE: STOPPED row must cite the design decision or the implementation record)
self-test: detected STOPPED with a none missing cell (SLOT-RELEASE: STOPPED row must say what is missing or open)
self-test: detected unknown status (TERM: unknown status 'SUFFICIENT')
self-test: detected citation inside the missing cell (TERM: citation docs/contracts/STATE_LIFECYCLE.md::LC-TERM is inside the missing cell)
self-test: detected decision citation to a non-decision file (TERM: decision citation runtime/crates/kix-kernel-v5/src/lib.rs is not a decision document)
self-test: detected open input not in the open-inputs file (open input I99 is not a row of docs/contracts/FIRST_BATCH_OPEN_INPUTS.md)
self-test: detected free-text-only surface cell (TERM: v5 surface is neither no entry point nor a lib.rs citation)
self-test: detected wrong counts line (counts line 'Counts: rows=10 TESTED=99 STOPPED=4 OPEN=0' differs from the table 'Counts: rows=10 TESTED=6 STOPPED=4 OPEN=0')
self-test: detected mutated locked blob (locked blob mismatch: runtime/crates/kix-kernel/src/lib.rs (have 2b91c41288b048a233f95b2d4e285b9c262d2333, want 69564b166f0c27f9af5d8422f0a466b18d74c20f))
self-test: detected removed anchor (TERM: contract anchor 'LC-TERM' is gone)
self-test: pass
exit: 0
```

### Command 398 — CI offline block

```text
$ python3 scripts/check_readiness_evidence_map.py
readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9
exit: 0
```

### Command 399 — CI offline block

```text
$ python3 scripts/check_readiness_evidence_map.py --self-test
self-test: baseline supplied map
self-test: synthetic PARTIAL positive control passed
self-test: detected PARTIAL row without an owner (REC-CORE-COMMIT: PARTIAL row must have an owner)
self-test: detected removed RCV-TORN-TAIL row (missing in map: RCV-TORN-TAIL)
self-test: detected duplicated RCV-TORN-TAIL row (duplicated in map: RCV-TORN-TAIL (2))
self-test: detected invented id (invented id in map section: FAKE-ID-9f3a)
self-test: detected dangling path (RCV-TORN-TAIL: readiness.test_conformance_sensitivity citation readiness/test_conformance_sensitivity.py does not exist)
self-test: detected dangling symbol (RCV-TORN-TAIL: readiness.test_faults citation readiness/test_faults.py::no_such_test_9f3a is not defined in the file)
self-test: detected citation in the wrong column (RCV-TORN-TAIL: readiness.test_faults citation readiness/conformance.py is outside the readiness.test_faults column paths)
self-test: detected citation under reference/v0.3-rc1 (RCV-TORN-TAIL: readiness.test_faults citation reference/v0.3-rc1/core.py is under reference/v0.3-rc1)
self-test: detected free-text-only fixture cell (RCV-TORN-TAIL: readiness.conformance cell is neither none nor a citation)
self-test: detected citation inside the missing cell (RCV-TORN-TAIL: ? citation readiness/store.py is inside the missing cell)
self-test: detected unknown status (RCV-TORN-TAIL: unknown status 'SUFFICIENT')
self-test: detected status that does not match the cells (JRN-SINGLE-WRITER: status PARTIAL should be EXERCISED for these cells)
self-test: detected EXERCISED row with no fixture citation (JRN-SINGLE-WRITER: status EXERCISED should be NOT_EXERCISED for these cells)
self-test: detected NOT_EXERCISED row carrying a citation (RCV-TORN-TAIL: status NOT_EXERCISED should be EXERCISED for these cells)
self-test: detected OPEN on a non-designated row (JRN-SINGLE-WRITER: OPEN is reserved for the designated open or held rows)
self-test: detected designated open row reclassified (HOLD-NEW-COMMANDS: EXERCISED row is a designated open row and must carry OPEN)
self-test: detected OPEN row with no owner (OPEN-LENPREFIX-MIDFRAME: OPEN row must have an owner)
self-test: detected owner not written in the owner sources (JRN-SINGLE-WRITER: owner 'Nobody Else' is not written in the owner sources)
self-test: detected EXERCISED row naming a gap (JRN-SINGLE-WRITER: status EXERCISED should be PARTIAL for these cells)
self-test: detected wrong counts line (counts line 'Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=999' differs from the table 'Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9')
self-test: detected dropped banner phrase (banner phrase 'operational count stays 0' is gone)
self-test: detected mutated locked blob (locked blob mismatch: runtime/crates/kix-kernel/src/lib.rs (have 2b91c41288b048a233f95b2d4e285b9c262d2333, want 69564b166f0c27f9af5d8422f0a466b18d74c20f))
self-test: detected removed contract anchor (FLAG-PROTOCOL-TRUTH: contract anchor '`protocolTruth` | `false` | 저널 레코드는 프로토콜 명령이나 권위 있는 상태가 아니다' is gone)
self-test: pass
self-test: baseline zero-PARTIAL map
self-test: synthetic PARTIAL positive control passed
self-test: detected PARTIAL row without an owner (REC-CORE-COMMIT: PARTIAL row must have an owner)
self-test: detected removed RCV-TORN-TAIL row (missing in map: RCV-TORN-TAIL)
self-test: detected duplicated RCV-TORN-TAIL row (duplicated in map: RCV-TORN-TAIL (2))
self-test: detected invented id (invented id in map section: FAKE-ID-9f3a)
self-test: detected dangling path (RCV-TORN-TAIL: readiness.test_conformance_sensitivity citation readiness/test_conformance_sensitivity.py does not exist)
self-test: detected dangling symbol (RCV-TORN-TAIL: readiness.test_faults citation readiness/test_faults.py::no_such_test_9f3a is not defined in the file)
self-test: detected citation in the wrong column (RCV-TORN-TAIL: readiness.test_faults citation readiness/conformance.py is outside the readiness.test_faults column paths)
self-test: detected citation under reference/v0.3-rc1 (RCV-TORN-TAIL: readiness.test_faults citation reference/v0.3-rc1/core.py is under reference/v0.3-rc1)
self-test: detected free-text-only fixture cell (RCV-TORN-TAIL: readiness.conformance cell is neither none nor a citation)
self-test: detected citation inside the missing cell (RCV-TORN-TAIL: ? citation readiness/store.py is inside the missing cell)
self-test: detected unknown status (RCV-TORN-TAIL: unknown status 'SUFFICIENT')
self-test: detected status that does not match the cells (JRN-SINGLE-WRITER: status PARTIAL should be EXERCISED for these cells)
self-test: detected EXERCISED row with no fixture citation (JRN-SINGLE-WRITER: status EXERCISED should be NOT_EXERCISED for these cells)
self-test: detected NOT_EXERCISED row carrying a citation (RCV-TORN-TAIL: status NOT_EXERCISED should be EXERCISED for these cells)
self-test: detected OPEN on a non-designated row (JRN-SINGLE-WRITER: OPEN is reserved for the designated open or held rows)
self-test: detected designated open row reclassified (HOLD-NEW-COMMANDS: EXERCISED row is a designated open row and must carry OPEN)
self-test: detected OPEN row with no owner (OPEN-LENPREFIX-MIDFRAME: OPEN row must have an owner)
self-test: detected owner not written in the owner sources (JRN-SINGLE-WRITER: owner 'Nobody Else' is not written in the owner sources)
self-test: detected EXERCISED row naming a gap (JRN-SINGLE-WRITER: status EXERCISED should be PARTIAL for these cells)
self-test: detected wrong counts line (counts line 'Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=999' differs from the table 'Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9')
self-test: detected dropped banner phrase (banner phrase 'operational count stays 0' is gone)
self-test: detected mutated locked blob (locked blob mismatch: runtime/crates/kix-kernel/src/lib.rs (have 2b91c41288b048a233f95b2d4e285b9c262d2333, want 69564b166f0c27f9af5d8422f0a466b18d74c20f))
self-test: detected removed contract anchor (FLAG-PROTOCOL-TRUTH: contract anchor '`protocolTruth` | `false` | 저널 레코드는 프로토콜 명령이나 권위 있는 상태가 아니다' is gone)
self-test: pass
exit: 0
```

### Command 400 — CI offline block

```text
$ python3 scripts/check_settlement_evidence_map.py
settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8
exit: 0
```

### Command 401 — CI offline block

```text
$ python3 scripts/check_settlement_evidence_map.py --self-test
self-test: detected missing clause
self-test: detected new contract heading
self-test: detected removed required heading
self-test: detected duplicate contract heading
self-test: detected duplicate row
self-test: detected invented row
self-test: detected dangling path
self-test: detected dangling symbol
self-test: detected helper symbol
self-test: detected protected reference path
self-test: detected cross-suite on other row
self-test: detected unlisted credit file
self-test: detected absolute path
self-test: detected parent path
self-test: detected closed policy
self-test: detected unknown owner
self-test: detected missing owner
self-test: detected missing UNDETERMINED
self-test: detected heading drift
self-test: detected row width
self-test: detected unknown status
self-test: detected uncited COVERED
self-test: detected uncited PARTIAL
self-test: detected COVERED gap
self-test: detected PARTIAL missing gap
self-test: detected NOT_COVERED citation
self-test: detected bare citation
self-test: detected stale counts
self-test: detected duplicate counts
self-test: detected missing banner
self-test: detected missing grade banner
self-test: detected ordinary class
self-test: detected invalid Python
self-test: pass (33 negative controls)
exit: 0
```

### Command 402 — CI offline block

```text
$ python3 scripts/check_bra_evidence_map.py
bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2
exit: 0
```

### Command 403 — CI offline block

```text
$ python3 scripts/check_bra_evidence_map.py --self-test
self-test: detected missing clause
self-test: detected new contract heading
self-test: detected removed required heading
self-test: detected duplicate heading
self-test: detected duplicate row
self-test: detected invented row
self-test: detected dangling path
self-test: detected dangling symbol
self-test: detected helper symbol
self-test: detected dynamic setattr row
self-test: detected protected path
self-test: detected absolute path
self-test: detected parent path
self-test: detected backslash path
self-test: detected closed open clause
self-test: detected closed options
self-test: detected promoted real gaps
self-test: detected unknown owner
self-test: detected missing owner
self-test: detected empty owner
self-test: detected missing UNDETERMINED
self-test: detected open item missing
self-test: detected open item invented
self-test: detected open item duplicate
self-test: detected open item adopted
self-test: detected open item status
self-test: detected open item owner drift
self-test: detected open item missing owner
self-test: detected open item missing UNDETERMINED
self-test: detected open item row width
self-test: detected open item dangling citation
self-test: detected title drift
self-test: detected row width
self-test: detected unknown status
self-test: detected missing paraphrase
self-test: detected uncited COVERED
self-test: detected uncited PARTIAL
self-test: detected COVERED gap
self-test: detected PARTIAL missing gap
self-test: detected NOT_COVERED missing gap
self-test: detected NOT_COVERED citation
self-test: detected bare citation
self-test: detected stale counts
self-test: detected duplicate counts
self-test: detected stale open-items count
self-test: detected duplicate open-items count
self-test: detected missing banner
self-test: detected missing grade banner
self-test: detected ordinary class
self-test: detected invalid Python
self-test: same-module transitive inheritance pass
self-test: pass (50 negative controls)
exit: 0
```

### Command 404 — CI offline block

```text
$ python3 scripts/check_credit_evidence_map.py
credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3
exit: 0
```

### Command 405 — CI offline block

```text
$ python3 scripts/check_credit_evidence_map.py --self-test
self-test: detected missing clause
self-test: detected new contract heading
self-test: detected removed required heading
self-test: detected duplicate heading
self-test: detected duplicate row
self-test: detected invented row
self-test: detected dangling path
self-test: detected dangling symbol
self-test: detected helper symbol
self-test: detected non-test method
self-test: detected protected path
self-test: detected absolute path
self-test: detected parent path
self-test: detected backslash path
self-test: detected closed open clause
self-test: detected closed options
self-test: detected closed policy clause
self-test: detected promoted real gaps
self-test: detected unknown owner
self-test: detected incomplete owners
self-test: detected missing owner
self-test: detected empty owner
self-test: detected missing UNDETERMINED
self-test: detected open item missing
self-test: detected open item invented
self-test: detected open item duplicate
self-test: detected open item adopted
self-test: detected open item status
self-test: detected open item owner drift
self-test: detected open item shortened owner
self-test: detected open item missing owner
self-test: detected open item missing UNDETERMINED
self-test: detected open item row width
self-test: detected open item dangling citation
self-test: detected title drift
self-test: detected row width
self-test: detected unknown status
self-test: detected missing paraphrase
self-test: detected uncited COVERED
self-test: detected uncited PARTIAL
self-test: detected COVERED gap
self-test: detected PARTIAL missing gap
self-test: detected NOT_COVERED missing gap
self-test: detected NOT_COVERED citation
self-test: detected bare citation
self-test: detected stale counts
self-test: detected duplicate counts
self-test: detected stale open-items count
self-test: detected duplicate open-items count
self-test: detected missing banner
self-test: detected missing grade banner
self-test: detected both banners missing
self-test: detected contract policy drift
self-test: detected ordinary class
self-test: detected invalid Python
self-test: direct TestCase selection pass
self-test: pass (55 negative controls)
exit: 0
```

### Command 406 — CI offline block

```text
$ python3 scripts/check_primary_price_fee_evidence_map.py
primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5
exit: 0
```

### Command 407 — CI offline block

```text
$ python3 scripts/check_primary_price_fee_evidence_map.py --self-test
self-test: detected missing clause
self-test: detected duplicate clause
self-test: detected invented clause
self-test: detected new contract heading
self-test: detected removed PF-C heading
self-test: detected removed numbered heading
self-test: detected duplicate contract heading
self-test: detected title drift
self-test: detected dangling path
self-test: detected dangling symbol
self-test: detected helper symbol
self-test: detected non-test method
self-test: detected protected path
self-test: detected absolute path
self-test: detected parent path
self-test: detected backslash path
self-test: detected noncanonical path
self-test: detected nested path
self-test: detected non-test file
self-test: detected bare citation
self-test: detected stale counts
self-test: detected duplicate counts
self-test: detected closed PF-C03
self-test: detected closed §4
self-test: detected closed §6
self-test: detected promoted PF-C04
self-test: detected promoted PF-C05
self-test: detected PF-C05 opened
self-test: detected PF-C05 owner drift
self-test: detected PF-C05 missing marker
self-test: detected PF-C owner drift
self-test: detected unknown owner
self-test: detected clause owner drift
self-test: detected missing owner
self-test: detected empty owner
self-test: detected missing open marker
self-test: detected closed chain row
self-test: detected cited chain row
self-test: detected missing chain row
self-test: detected missing chain PF-C05
self-test: detected duplicate chain row
self-test: detected invented chain row
self-test: detected chain owner drift
self-test: detected chain missing marker
self-test: detected chain row width
self-test: detected stale chain count
self-test: detected duplicate chain count
self-test: detected open item owner drift
self-test: detected open item shortened owner
self-test: detected open item status drift
self-test: detected contract status drift
self-test: detected open item title drift
self-test: detected missing open item
self-test: detected duplicate open item
self-test: detected invented open item
self-test: detected O-label order drift
self-test: detected open item missing marker
self-test: detected open item missing owner
self-test: detected cited open item
self-test: detected open item row width
self-test: detected stale open count
self-test: detected duplicate open count
self-test: detected missing contract open item
self-test: detected row width
self-test: detected unknown status
self-test: detected missing paraphrase
self-test: detected uncited COVERED
self-test: detected uncited PARTIAL
self-test: detected COVERED gap
self-test: detected PARTIAL missing gap
self-test: detected NOT_COVERED missing gap
self-test: detected NOT_COVERED citation
self-test: detected missing banner
self-test: detected missing grade banner
self-test: detected ordinary class
self-test: detected invalid Python
self-test: direct TestCase selection pass
self-test: pass (76 negative controls)
exit: 0
```

### Command 408 — CI offline block

```text
$ python3 scripts/check_ai_delegation_evidence_map.py
ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1
exit: 0
```

### Command 409 — CI offline block

```text
$ python3 scripts/check_ai_delegation_evidence_map.py --self-test
self-test: detected missing clause
self-test: detected duplicate clause
self-test: detected invented clause
self-test: detected clause row width
self-test: detected missing code
self-test: detected duplicate code
self-test: detected invented code
self-test: detected code row width
self-test: detected code order
self-test: detected missing flag
self-test: detected duplicate flag
self-test: detected invented flag
self-test: detected flag row width
self-test: detected flag order
self-test: detected missing item
self-test: detected duplicate item
self-test: detected invented item
self-test: detected item row width
self-test: detected item order
self-test: detected new contract heading
self-test: detected removed heading
self-test: detected duplicate contract heading
self-test: detected title drift
self-test: detected missing paraphrase
self-test: detected dangling path
self-test: detected protected path
self-test: detected absolute path
self-test: detected parent path
self-test: detected backslash path
self-test: detected noncanonical path
self-test: detected nested path
self-test: detected non-test file
self-test: detected unapproved readiness file
self-test: detected dangling symbol
self-test: detected helper symbol
self-test: detected non-test method
self-test: detected bare citation
self-test: detected ordinary class
self-test: detected invalid Python
self-test: detected orphan readiness mixin
self-test: detected stale Counts:
self-test: detected duplicate Counts:
self-test: detected stale Codes:
self-test: detected duplicate Codes:
self-test: detected stale Flags:
self-test: detected duplicate Flags:
self-test: detected stale Open items:
self-test: detected duplicate Open items:
self-test: detected closed §9
self-test: detected promoted §10
self-test: detected clause owner drift
self-test: detected unknown owner
self-test: detected empty owner
self-test: detected missing owner
self-test: detected missing open marker
self-test: detected §3 unknown status
self-test: detected §1 COVERED needs a citation
self-test: detected §3 PARTIAL needs a citation
self-test: detected §1 COVERED gap must be none
self-test: detected §3 PARTIAL needs a named gap
self-test: detected §10 NOT_COVERED needs a named gap
self-test: detected §10 NOT_COVERED evidence must be none
self-test: detected §3 unknown DLG id
self-test: detected §6 must point to all DLG
self-test: detected §3 DLG pointer format
self-test: detected §3 DLG pointer range
self-test: detected §3 DLG pointer duplicate
self-test: detected copied DLG row
self-test: detected missing matrix id
self-test: detected code absent from ECC
self-test: detected constructor exclusion
self-test: detected AID pointer drift
self-test: detected contract flag drift
self-test: detected mock flag drift
self-test: detected execution enabled
self-test: detected open item item title drift
self-test: detected open item item status drift
self-test: detected open item open-item evidence must be none
self-test: detected open item item must remain OPEN
self-test: detected open item OPEN needs an open marker
self-test: detected open item OPEN needs an owner
self-test: detected O8 owner drift
self-test: detected O8 execution posture
self-test: detected missing banner Builder-authored map, not a review or an acceptance
self-test: detected missing banner no grade change
self-test: detected missing banner `delegated_execution_enabled` stays `false`
self-test: transitive TestCase selection and symlink fencing pass
self-test: pass (86 negative controls)
exit: 0
```

### Command 410 — CI offline block

```text
$ python3 scripts/check_lifecycle_adr_evidence_map.py
lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK
exit: 0
```

### Command 411 — CI offline block

```text
$ python3 scripts/check_lifecycle_adr_evidence_map.py --self-test
self-test: positive injected citation and 49 negative fixtures passed (memory only)
exit: 0
```

### Command 412 — CI offline block

```text
$ python3 scripts/check_contract_invariants_evidence_map.py
contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK
exit: 0
```

### Command 413 — CI offline block

```text
$ python3 scripts/check_contract_invariants_evidence_map.py --self-test
contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only)
exit: 0
```

### Command 414 — CI offline block

```text
$ python3 scripts/check_toss_card_profile_evidence_map.py
Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK
exit: 0
```

### Command 415 — CI offline block

```text
$ python3 scripts/check_toss_card_profile_evidence_map.py --self-test
Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only)
exit: 0
```

### Command 416 — CI offline block

```text
$ python3 scripts/check_bcs1_evidence_map.py
BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17
exit: 0
```

### Command 417 — CI offline block

```text
$ python3 scripts/check_bcs1_evidence_map.py --self-test
self-test: detected missing test citation alone (is not a test function)
self-test: detected missing test citation mixed (is not a test function)
self-test: detected non-test helper alone (is not a test function)
self-test: detected non-test helper mixed (is not a test function)
self-test: detected bare path alone (needs a nonempty test symbol)
self-test: detected bare path mixed (needs a nonempty test symbol)
self-test: detected empty symbol alone (needs a nonempty test symbol)
self-test: detected empty symbol mixed (needs a nonempty test symbol)
self-test: detected blank symbol alone (needs a nonempty test symbol)
self-test: detected blank symbol mixed (needs a nonempty test symbol)
self-test: detected prose after citation alone (bad test-cell grammar)
self-test: detected prose after citation mixed (bad test-cell grammar)
self-test: detected kernel path (outside test paths)
self-test: detected absolute path (not repo-relative)
self-test: detected traversal (not repo-relative)
self-test: detected reference path (forbidden reference)
self-test: detected missing file (file missing)
self-test: detected non-UTF8 file (not UTF-8)
self-test: detected before module (not in mod tests)
self-test: detected after module (not in mod tests)
self-test: detected removed row (missing row)
self-test: detected duplicate row (duplicated row)
self-test: detected invented row (invented row)
self-test: detected row width (expected seven cells)
self-test: detected header (bad table header)
self-test: detected counts (counts mismatch)
self-test: detected duplicate section (expected one section)
self-test: detected FU row removed (follow-up table mismatch)
self-test: detected non-claim removed (missing non-claim)
self-test: detected section field (section/clause mismatch)
self-test: detected OPEN status (bad status)
self-test: detected SUFFICIENT status (bad status)
self-test: detected covered gap (COVERED needs)
self-test: detected covered without tests (COVERED needs)
self-test: detected partial without tests (PARTIAL needs)
self-test: detected partial without gap (PARTIAL needs)
self-test: detected partial without owner (PARTIAL needs)
self-test: detected not covered with tests (NOT_COVERED needs)
self-test: detected FU flipped (must stay NOT_COVERED)
self-test: detected FU tag dropped (missing follow-up tag)
self-test: detected preserved partial citation lost (must stay PARTIAL)
self-test: detected preserved partial promoted (must stay PARTIAL)
self-test: detected bad owner (unknown owner)
self-test: detected empty gap (Gap/Owner must be nonempty)
self-test: detected anchor removed (contract anchor is gone)
self-test: detected new numbered section (unmapped contract section)
self-test: detected contract hex drift (golden constant mismatch)
self-test: detected golden byte drift (golden constant mismatch)
self-test: detected locked-blob drift (locked blob mismatch)
self-test: detected locked-blob drift (locked blob mismatch)
self-test: pass (2 positive controls, 50 negative fixtures)
exit: 0
```

### Command 418 — CI offline block

```text
$ python3 scripts/check_performance_measurement_evidence_map.py
performance evidence map ok: Counts: rows=42 COVERED=29 PARTIAL=9 NOT_COVERED=1 NOT_RUN=3
exit: 0
```

### Command 419 — CI offline block

```text
$ python3 scripts/check_performance_measurement_evidence_map.py --self-test
self-test: detected fabricated test citation alone (is not a test function)
self-test: detected fabricated test citation mixed (is not a test function)
self-test: detected non-test helper alone (is not a test function)
self-test: detected non-test helper mixed (is not a test function)
self-test: detected bare test path alone (needs a nonempty test symbol)
self-test: detected bare test path mixed (needs a nonempty test symbol)
self-test: detected empty test symbol alone (needs a nonempty test symbol)
self-test: detected empty test symbol mixed (needs a nonempty test symbol)
self-test: detected blank test symbol alone (needs a nonempty test symbol)
self-test: detected blank test symbol mixed (needs a nonempty test symbol)
self-test: detected prose after citation alone (bad test-cell grammar)
self-test: detected prose after citation mixed (bad test-cell grammar)
self-test: detected outside allowed files (outside)
self-test: detected absolute path (not repo-relative)
self-test: detected traversal (not repo-relative)
self-test: detected reference path (forbidden reference)
self-test: detected missing file (file missing)
self-test: detected non-UTF8 file (not UTF-8)
self-test: detected outside allowed files (outside)
self-test: detected absolute path (not repo-relative)
self-test: detected traversal (not repo-relative)
self-test: detected reference path (forbidden reference)
self-test: detected missing file (file missing)
self-test: detected non-UTF8 file (not UTF-8)
self-test: detected source citation (is not a source symbol)
self-test: detected source citation (needs a nonempty source symbol)
self-test: detected source citation (bad source-cell grammar)
self-test: detected source citation (historical file only allowed)
self-test: detected removed row (missing row)
self-test: detected duplicate row (duplicated row)
self-test: detected invented row (invented row)
self-test: detected row width (expected eight cells)
self-test: detected header (bad table header)
self-test: detected counts (counts mismatch)
self-test: detected duplicate map heading (expected one section)
self-test: detected historical phrase (historical reference phrase missing)
self-test: detected historical attribution (historical attribution missing)
self-test: detected non-claim removed (missing non-claim: no product TPS, p99 or failure-rate value)
self-test: detected non-claim removed (missing non-claim: UNDETERMINED (owner: User))
self-test: detected non-claim removed (missing non-claim: no benchmark claim)
self-test: detected non-claim removed (missing non-claim: release probe NOT_RUN)
self-test: detected section field (section/clause mismatch)
self-test: detected empty clause (section/clause mismatch)
self-test: detected OPEN status (bad status)
self-test: detected covered gap (COVERED needs)
self-test: detected covered without tests (COVERED needs)
self-test: detected partial without tests (PARTIAL needs)
self-test: detected partial without gap (PARTIAL needs)
self-test: detected partial without owner (PARTIAL needs)
self-test: detected unknown owner (unknown owner)
self-test: detected empty gap (Gap must be nonempty)
self-test: detected not run with tests (NOT_RUN needs)
self-test: detected not covered with tests (NOT_COVERED needs)
self-test: detected historical row source (historical citation/phrase missing)
self-test: detected pinned status flipped (must stay NOT_RUN)
self-test: detected pinned status flipped (must stay NOT_RUN)
self-test: detected pinned status flipped (must stay NOT_RUN)
self-test: detected pinned status flipped (must stay NOT_COVERED)
self-test: detected anchor removed (contract anchor is gone)
self-test: detected new heading (unmapped contract section)
self-test: detected duplicate heading (duplicated contract section)
self-test: detected missing heading (missing contract section)
self-test: detected locked-blob drift (locked blob mismatch: runtime/crates/kix-kernel/src/lib.rs)
self-test: detected locked-blob drift (locked blob mismatch: runtime/crates/kix-kernel/tests/quarantine_capacity.rs)
self-test: detected example constant drift (example constant mismatch: LOCKED_KERNEL)
self-test: detected example constant drift (example constant mismatch: LOCKED_QUARANTINE)
self-test: pass (2 positive controls, 66 negative fixtures; memory only)
exit: 0
```

### Command 420 — CI offline block

```text
$ python3 scripts/check_feature_semantics_evidence_map.py
feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17
exit: 0
```

### Command 421 — CI offline block

```text
$ python3 scripts/check_feature_semantics_evidence_map.py --self-test
self-test: detected missing row
self-test: detected duplicate row
self-test: detected invented row
self-test: detected row width
self-test: detected table header
self-test: detected counts
self-test: detected duplicate map heading
self-test: detected section coverage
self-test: detected gate row
self-test: detected fabricated symbol alone
self-test: detected fabricated symbol mixed
self-test: detected non-test helper alone
self-test: detected non-test helper mixed
self-test: detected nested non-test helper alone
self-test: detected nested non-test helper mixed
self-test: detected bare path alone
self-test: detected bare path mixed
self-test: detected empty symbol alone
self-test: detected empty symbol mixed
self-test: detected blank symbol alone
self-test: detected blank symbol mixed
self-test: detected prose alone
self-test: detected prose mixed
self-test: detected absolute path alone
self-test: detected absolute path mixed
self-test: detected traversal alone
self-test: detected traversal mixed
self-test: detected reference path alone
self-test: detected reference path mixed
self-test: detected outside path alone
self-test: detected outside path mixed
self-test: detected missing file
self-test: detected non-UTF8 file
self-test: detected section cell
self-test: detected empty clause
self-test: detected bad status
self-test: detected covered gap
self-test: detected covered owner
self-test: detected covered no tests
self-test: detected partial no tests
self-test: detected partial no gap
self-test: detected partial no owner
self-test: detected uncovered has tests
self-test: detected uncovered no gap
self-test: detected uncovered no owner
self-test: detected unknown owner
self-test: detected empty gap
self-test: detected pinned status X-JOIN-EXEC
self-test: detected pinned owner X-JOIN-EXEC
self-test: detected pinned status X-GROUP-EXEC
self-test: detected pinned owner X-GROUP-EXEC
self-test: detected pinned status X-SORT-EXEC
self-test: detected pinned owner X-SORT-EXEC
self-test: detected pinned status X-AGG-EXEC
self-test: detected pinned owner X-AGG-EXEC
self-test: detected pinned status X-BACKEND-CONFORMANCE
self-test: detected pinned owner X-BACKEND-CONFORMANCE
self-test: detected characterization status S10-LIMITS
self-test: detected characterization owner S10-LIMITS
self-test: detected characterization status S8-F64-TOLERANCE
self-test: detected characterization owner S8-F64-TOLERANCE
self-test: detected class-B citation
self-test: detected class-B citation
self-test: detected non-claim
self-test: detected non-claim
self-test: detected non-claim
self-test: detected non-claim
self-test: detected new heading
self-test: detected duplicate heading
self-test: detected missing heading
self-test: detected unnumbered heading
self-test: detected gate removed
self-test: detected gate reordered
self-test: detected gate anchor drift
self-test: detected anchor drift
self-test: detected locked blob drift
self-test: detected locked blob drift
self-test: pass (77 negative controls, injected positive control)
exit: 0
```

### Command 422 — CI offline block

```text
$ python3 scripts/check_integration_gate_contract_evidence_map.py
integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1
exit: 0
```

### Command 423 — CI offline block

```text
$ python3 scripts/check_integration_gate_contract_evidence_map.py --self-test
self-test: detected missing row
self-test: detected duplicate row
self-test: detected invented row
self-test: detected row width
self-test: detected table header
self-test: detected counts
self-test: detected duplicate map heading
self-test: detected section coverage
self-test: detected fabricated method alone
self-test: detected fabricated method mixed
self-test: detected fabricated offline method alone
self-test: detected fabricated offline method mixed
self-test: detected module helper alone
self-test: detected module helper mixed
self-test: detected wrong class alone
self-test: detected wrong class mixed
self-test: detected bare path alone
self-test: detected bare path mixed
self-test: detected empty symbol alone
self-test: detected empty symbol mixed
self-test: detected absolute path alone
self-test: detected absolute path mixed
self-test: detected traversal alone
self-test: detected traversal mixed
self-test: detected backslash path alone
self-test: detected backslash path mixed
self-test: detected reference path alone
self-test: detected reference path mixed
self-test: detected outside path alone
self-test: detected outside path mixed
self-test: detected wrong column alone
self-test: detected wrong column mixed
self-test: detected prose alone
self-test: detected prose mixed
self-test: detected missing file
self-test: detected non-UTF8 file
self-test: detected syntax error
self-test: detected fabricated checker
self-test: detected nested checker
self-test: detected bare checker
self-test: detected checker wrong column
self-test: detected wrapper import removed
self-test: detected section cell
self-test: detected empty clause
self-test: detected bad status
self-test: detected covered gap
self-test: detected covered owner
self-test: detected partial no gap
self-test: detected partial no owner
self-test: detected uncovered has tests
self-test: detected uncovered has checkers
self-test: detected uncovered no gap
self-test: detected uncovered no owner
self-test: detected unknown owner
self-test: detected empty gap
self-test: detected backticks gap
self-test: detected covered no citations
self-test: detected partial no citations
self-test: detected pinned status I-GATE-ROUTING
self-test: detected pinned owner I-GATE-ROUTING
self-test: detected pinned status CHK-HTTP-SUITE
self-test: detected pinned owner CHK-HTTP-SUITE
self-test: detected required citation K-READINESS-FSM-REFUSED
self-test: detected required citation R-7
self-test: detected required citation G-LOOPBACK-BIND
self-test: detected required citation G-NO-PUBLIC
self-test: detected anchor drift
self-test: detected added heading
self-test: detected duplicate heading
self-test: detected read item 7 removed
self-test: detected workflow command missing
self-test: detected open gap not implemented in this node
self-test: detected open gap OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia
self-test: detected open gap owner
self-test: detected non-claim runs only where loopback is permitted
self-test: detected non-claim no production endpoint
self-test: detected non-claim no gate behavior change
self-test: detected non-claim no grade change
self-test: detected locked blob runtime/crates/kix-kernel/src/lib.rs
self-test: detected locked blob runtime/crates/kix-kernel/tests/quarantine_capacity.rs
self-test: detected forbidden import socket
self-test: detected forbidden import subprocess
self-test: detected forbidden import http
self-test: detected forbidden import integration_gate
self-test: detected forbidden from import
self-test: pass (85 negative controls; injected positive and valid status controls)
exit: 0
```

### Command 430 — CI offline block

```text
$ python3 scripts/check_stage5_host.py --self-test
self-test: caught all prerequisites pass
self-test: caught postgres binary missing
self-test: caught postgres binary not executable
self-test: caught postgres --version exits non-zero
self-test: caught postgres --version times out
self-test: caught wrong upstream version 17.10
self-test: caught wrong version 17.110 (no substring match)
self-test: caught wrong debian revision deb13u2
self-test: caught missing debian revision
self-test: caught trailing suffix on banner
self-test: caught initdb banner mismatches independently
self-test: caught psycopg import fails
self-test: caught psycopg probe times out (error-key dict)
self-test: caught psycopg major version 2
self-test: caught psycopg major version 4
self-test: caught psycopg version unparseable
self-test: caught taskset missing from PATH
self-test: caught ss missing from PATH
self-test: caught core 1 outside affinity mask
self-test: caught affinity API unavailable
self-test: pass
exit: 0
```

### Command 436 — after protected

```text
$ git rev-parse origin/main:.aiops/program.json
ff0f39a8129ca8b8d30818cce35c3d4e588872fc
exit: 0
```

### Command 438 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/DESIGN_SUI_ZK.md
b71ad6d1b3b000c8ead472d3aed27963bd00b8ca
exit: 0
```

### Command 440 — after protected

```text
$ git rev-parse 'origin/main:reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md'
301fe796c16ee9a44e9f69d62f7015775c4a69e3
exit: 0
```

### Command 442 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/README.md
ae08e234389f4616de123ff848186a145f476806
exit: 0
```

### Command 444 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/adapters.py
f0097af0fefdff1d92eb0640a4c45692f68d7db6
exit: 0
```

### Command 446 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/archive_driver.py
e773292fccfbfa7265d2a28d5f241f806f9494d7
exit: 0
```

### Command 448 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/assets.py
6383cd608f203e237d7879efe59b4297bb09fe05
exit: 0
```

### Command 450 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/canonical_encoding.py
30d646818c94c20e6a93d6b463598b6254e053df
exit: 0
```

### Command 452 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/changes_from_v02.diff
aa8d41d12ed2d2775a200ea0261dc5d89a565992
exit: 0
```

### Command 454 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/check_reproducibility.py
b5eef81a2e96b0cab1b7746f0248c249f4fa382c
exit: 0
```

### Command 456 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/archive-fixture.mjs
99c842d1fc9580bdb87a79b5ecdcfb811c79aa58
exit: 0
```

### Command 458 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/backup.mjs
6d185685210be88b86c0157df9b9799dffc210fe
exit: 0
```

### Command 460 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/canonical_encoding.ts
60974034546e85ffbdacce3f581adda59d8237f2
exit: 0
```

### Command 462 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/commerce_v2.ts
44703752f50473ed5b2992a73f88e4ed70341c2c
exit: 0
```

### Command 464 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/compile-circuits.mjs
061c6a9cbce05e204b3ee243c1ea4dfc5c7e8207
exit: 0
```

### Command 466 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/encoding.mjs
34f8e570bd449275d3111518ea882d1a5fe005bd
exit: 0
```

### Command 468 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/independent.mjs
331b617ac2b010a28ad34e4e7db269dc3b5fcde4
exit: 0
```

### Command 470 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/localnet-boundaries.mjs
d65b7593695c29100f5af18cd9d8cba5dbcee35e
exit: 0
```

### Command 472 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/localnet-paid.mjs
4ab7c7bb4fbcb3e6322dcdda99f82f1767163216
exit: 0
```

### Command 474 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/localnet.mjs
f3a676e73de5bf5434ce2db80ec9abbbeb210259
exit: 0
```

### Command 476 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/offline.test.mjs
dd1d46e273d3e3e8e5a6744aebcf400a3142855f
exit: 0
```

### Command 478 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/package-lock.json
4a6431cd2e93c8a53cabfbe35e5cd5de2583c181
exit: 0
```

### Command 480 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/package.json
085af5ae575ca60bebdfd2acefdf7eae11ebdfb6
exit: 0
```

### Command 482 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/paid-chain.mjs
d23782e52a517a81026f6c4d172e5ac0b1580942
exit: 0
```

### Command 484 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/private.mjs
e9cc6bdb3cfa9d5f5d5979517146ea469ebb865e
exit: 0
```

### Command 486 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/setup-zk.mjs
b27b581ec22f76f2631af54484fd582f914a82f0
exit: 0
```

### Command 488 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/types.mjs
7fcad757367415f87098dd25c89620c1529cb933
exit: 0
```

### Command 490 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/verify_canonical.ts
0e2894956970d4d898ea57cf2a9abadab81ec2c8
exit: 0
```

### Command 492 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/zk-policy.mjs
8bd3f600dee47331bda24e0deb2993e591627558
exit: 0
```

### Command 494 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/zk-regression.mjs
4372288383c7c158d0c8beeb569954ae70cdda07
exit: 0
```

### Command 496 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/client/zk-test-utils.mjs
15c0a397ee5dceb1ace0548e0e87c0ceee526532
exit: 0
```

### Command 498 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/commerce.py
eb0a53cd70cd22ad4301cd0be9d368db8caa355c
exit: 0
```

### Command 500 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/commerce_driver.py
09c643f8a33daf119b5c9d5902fb9eadbd876ad4
exit: 0
```

### Command 502 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/common.py
f23d267405611c6cf2cbbcb952929dbedd21616d
exit: 0
```

### Command 504 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/contracts.py
53a72e0e2e962a1759456739f8eb81d72e001284
exit: 0
```

### Command 506 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/core.py
fd02b70c58a35ec5d7f3dda36c62856d2155251f
exit: 0
```

### Command 508 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/dispatch.py
1ad053df55ede1364cfb1671bf0d43fdd2e500a2
exit: 0
```

### Command 510 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/execution_contracts.py
6b14a5db16cdba5a3c1013fe1623106df7b2f4cd
exit: 0
```

### Command 512 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/finance.py
05393f495fcc3512bb17505c8202396d1865ec41
exit: 0
```

### Command 514 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/fixtures/canonical_encoding_v1.json
90c74af5e5464d990afb8096d3e315d629743361
exit: 0
```

### Command 516 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/fixtures/unicode15_assigned_ranges.json
40cb76cb8af8cbf617a18b8a92990e3aac7e999a
exit: 0
```

### Command 518 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/lifecycle.py
4770ee2ce63e784d696e06f34797137805b2b6b9
exit: 0
```

### Command 520 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/mock_provider.py
a0a07b39c4642bc81d951dbeeefeaf62a790d6fd
exit: 0
```

### Command 522 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/mutation_check.py
45e7e06e6770ce21ed07d78eb7c4f3aa025d5de0
exit: 0
```

### Command 524 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/observations.py
4551be53386557e3dc71d295646eaf5ab8318a42
exit: 0
```

### Command 526 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/paid_archive.py
cc035517114c8810736d5e480fe14e17f4b6b0d7
exit: 0
```

### Command 528 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/paid_driver.py
3412c363e8688555b1ab9b2f8586110b27df7008
exit: 0
```

### Command 530 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/paid_integration.py
a8306ab079391702bd17540e131c8117c763629b
exit: 0
```

### Command 532 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/paid_recovery.py
16191b15c7a5157526aa01e49e04a229b5be05ec
exit: 0
```

### Command 534 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/protocol_contract.json
619ae21c82ca3df5661bd3831613f15fa65225ff
exit: 0
```

### Command 536 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/requirements.txt
666c60dfa2fd8cacb8a8945f805fda6db39f9299
exit: 0
```

### Command 538 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/acceptance_trace.json
3fda1262ffa630b010eb629b0e30ce2e8ae5f50e
exit: 0
```

### Command 540 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/client_offline_tests.txt
d351ed1b80f031461b2a57cb9a577347427bb643
exit: 0
```

### Command 542 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/client_syntax.json
3ca4eed2507f2134234bad86df4d8b69817d4de7
exit: 0
```

### Command 544 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/manifest.sha256.json
6b779387247920bffffeff5cfacd6bfc11f84127
exit: 0
```

### Command 546 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M01.txt
477b00cc36e446fb308c817b7f4f50a9cc4a7014
exit: 0
```

### Command 548 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M02.txt
e656a9c1243f96f96196a5bd57e7b8a52b275776
exit: 0
```

### Command 550 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M03.txt
df142f75c3acb4b940b2cce06400c9820357630c
exit: 0
```

### Command 552 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M04.txt
404ca2c7f76de172a6dff1a15ef0311f849d8dc9
exit: 0
```

### Command 554 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M05.txt
b44e803bcb986dcdc82c2dbdfd931d786d8440a6
exit: 0
```

### Command 556 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M06.txt
0df5fe9d80d914cbc6e95cf5f594ee0e7180a5f8
exit: 0
```

### Command 558 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M07.txt
348a7d05fa787ce139bd2c402c9042529cf4e487
exit: 0
```

### Command 560 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M08.txt
c3ba396ab5b39fafa07df167af57e555ad8368dd
exit: 0
```

### Command 562 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M09.txt
d32c7d16ca5eb4775d3353a3cf1db6c45cee3efd
exit: 0
```

### Command 564 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M10.txt
0f0fb480a7c042bdaa4b34f9099ce4c93c4b3c51
exit: 0
```

### Command 566 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M11.txt
0941b10178f614159f248fc57dc0c7b8d2d5a91f
exit: 0
```

### Command 568 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M12.txt
c9ce89485b474bfc5ad468cb50a4254b95f7a8e4
exit: 0
```

### Command 570 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M13.txt
9a6929779d9c3f52ce95479bc8cf089d0aa50089
exit: 0
```

### Command 572 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_logs/M14.txt
e3829e77c0f389fc31f180701a888273e8f134d9
exit: 0
```

### Command 574 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/mutation_results.json
83301937ef2443dfd4e44b0464ee09cc7d1fdc7f
exit: 0
```

### Command 576 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/preflight.json
558a1e59d2a921932b7bde570e6597dfaf2e925e
exit: 0
```

### Command 578 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/reproducibility.json
3a3faba979742d1fc5be6627a2d9716fb91a33b8
exit: 0
```

### Command 580 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/review_trace_v03.json
75147c8f0d4192fa2c9269950867824116ef6bdf
exit: 0
```

### Command 582 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/tests.txt
eca04766e566c4eedc3253fabfccb25422a06cd4
exit: 0
```

### Command 584 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/v02_unchanged.json
c8639c8980ea44864a0bee16241b6830fb1dc7c2
exit: 0
```

### Command 586 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/results/verification.json
cee2e47a294d33599c6b89bba3a60d082d246961
exit: 0
```

### Command 588 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/review_provenance/baseline_integrity.json
11d6afbd6ca7e89bad7047efabb52edb736b3ea9
exit: 0
```

### Command 590 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/review_provenance/baseline_reproduced.json
dd89cea025800a6cf1a8cde6ffdea30f0d5ef769
exit: 0
```

### Command 592 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/review_provenance/review_v02_probe.py
5ecf0d82ce3f46cec9c75ffa69600c76f31c9c2c
exit: 0
```

### Command 594 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/review_provenance/review_verification.json
b5950eb99a82ae73de0b552a2b4eee1823ddab62
exit: 0
```

### Command 596 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/review_trace_v03.py
5e631f7aa92a23a96275f47553da3ecd9de97678
exit: 0
```

### Command 598 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/scripts/preflight.py
b6d87981b94c947e5b538b8e328b111bf1913612
exit: 0
```

### Command 600 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/scripts/verify_package.py
9198166197c7b76d24fed3d1256a00a336c4bb05
exit: 0
```

### Command 602 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/source_inventory.json
d59196e1dc97b5ec8c73738e78b452e9c72624fc
exit: 0
```

### Command 604 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/storage_receipt.py
eecce5d698d3103b15a9834b558aee619fb2fb8b
exit: 0
```

### Command 606 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/sui/Move.lock
76f76e701cb9b394ae520bfbf0c162e1101dc4cd
exit: 0
```

### Command 608 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/sui/Move.toml
e7f4a535cd23e7ceba4f78c34151b473db737867
exit: 0
```

### Command 610 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/sui/sources/rights.move
ea7905038bcbd51c7ea126ff6b12d560f6227dd5
exit: 0
```

### Command 612 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/sui/sources/zk_gate.move
333e0cfd7911e97f10354507eef5d327a446061e
exit: 0
```

### Command 614 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/sui/tests/rights_tests.move
8717d1f86228cc502a1948e58e8618bbd7d994d0
exit: 0
```

### Command 616 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_assets.py
fac5e15e06fe0a90259e9fd6079abe5c4ba4c5e0
exit: 0
```

### Command 618 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_canonical_encoding.py
335f5d576c96beeb241d295ea6dfc33b46bbdbc8
exit: 0
```

### Command 620 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_commerce.py
be9659197294415038f24144b61a499fafb2e4e1
exit: 0
```

### Command 622 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_commerce_driver.py
9f0466ab923cfddbac03e4ac6dc07373d302b41f
exit: 0
```

### Command 624 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_core.py
dcf29bb14d134cae0d25d51bc076d6cf0e69b0c4
exit: 0
```

### Command 626 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_execution_contracts.py
8965fcf65e0ed569313160f71a17736757a50b60
exit: 0
```

### Command 628 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_paid_archive.py
ac9cf5ed9367eadbd5917c1e27fb80fa860223f0
exit: 0
```

### Command 630 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_paid_integration.py
f451fd57215e67f9ac6a118fd0c61fc37d9ea0b5
exit: 0
```

### Command 632 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_paid_recovery.py
6e86d418d67b2e18275390adde0820db0d87bdcc
exit: 0
```

### Command 634 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_storage_receipt.py
09c523702ad28395cef39249aa8c26fd8888e9b0
exit: 0
```

### Command 636 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_v02.py
a389aa7eb7f7d4305a52d29595ec688d69d87a7a
exit: 0
```

### Command 638 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/test_v03.py
9e739ac657974fa3700c92abeb272071dd7ea9b3
exit: 0
```

### Command 640 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/vendor/rights_model.py
03b095d806fd2f0e85323d69739906b50b227466
exit: 0
```

### Command 642 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/vendor/tix_reconcile.py
8bc8847f164118d8205e209386aa542d1e7f8a2e
exit: 0
```

### Command 644 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/verify.py
a209e7e5b3dd1167f125a06addf364745b709267
exit: 0
```

### Command 646 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/zk/artifacts/README.md
6861ccc1d7ef6caac6e1e37043f47ce907b2eeb4
exit: 0
```

### Command 648 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/zk/circuits/common.circom
5a4cc324e5694bb78db2b9448642eaeacd769413
exit: 0
```

### Command 650 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/zk/circuits/mint.circom
de6b2e918be4e61bb5debdee351cf39eddd3383d
exit: 0
```

### Command 652 — after protected

```text
$ git rev-parse origin/main:reference/v0.3-rc1/zk/circuits/spend.circom
1cdabb7000e639789f6d2ecd074824fca04206e9
exit: 0
```

### Command 654 — protected untracked

```text
$ git ls-files --others --exclude-standard reference/v0.3-rc1/ .aiops/
exit: 0
```

### Command 655 — protected diff

```text
$ git diff --name-only origin/main -- runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs reference/v0.3-rc1/ .aiops/ docs/tasks/
exit: 0
```

### Command 656 — temporary index

```text
$ env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-mn4p61ce/index git read-tree HEAD
exit: 0
```

### Command 657 — temporary index

```text
$ env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-mn4p61ce/index git add --intent-to-add -- docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md
error: unable to create temporary file: Read-only file system
fatal: cannot create an empty blob in the object database
exit: 128
```

### Command 902 — original object store

```text
$ git rev-parse --path-format=absolute --git-path objects
/workspace/kix-run/repo/.git/objects
exit: 0
```

### Command 903 — temporary index

```text
$ env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-e0705idp/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-index-e0705idp/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git read-tree HEAD
exit: 0
```

### Command 904 — temporary index

```text
$ env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-e0705idp/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-index-e0705idp/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git add --intent-to-add -- docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md
exit: 0
```

### Command 905 — three-file diff with temporary index

```text
$ env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-e0705idp/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-index-e0705idp/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git diff --name-only origin/main
docs/README.md
docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md
exit: 0
```

### Command 906 — whitespace with temporary index

```text
$ env GIT_INDEX_FILE=/tmp/kix-perf-pin-index-e0705idp/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-index-e0705idp/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git diff --check
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3269: trailing whitespace.
+     2
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3271: trailing whitespace.
+     4
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3273: trailing whitespace.
+     6
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3275: trailing whitespace.
+     8
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3279: trailing whitespace.
+    12
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3281: trailing whitespace.
+    14
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3283: trailing whitespace.
+    16
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3287: trailing whitespace.
+    20
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3289: trailing whitespace.
+    22
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3291: trailing whitespace.
+    24
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3293: trailing whitespace.
+    26
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3295: trailing whitespace.
+    28
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3297: trailing whitespace.
+    30
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3302: trailing whitespace.
+    35
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3304: trailing whitespace.
+    37
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3306: trailing whitespace.
+    39
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3308: trailing whitespace.
+    41
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3813: trailing whitespace.
+
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3822: trailing whitespace.
+
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4272: trailing whitespace.
+
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:5953: trailing whitespace.
+26:
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:5956: trailing whitespace.
+29:
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:5962: trailing whitespace.
+35:
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:5971: trailing whitespace.
+81:
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:5973: trailing whitespace.
+83:
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:5989: trailing whitespace.
+279:
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6026: trailing whitespace.
+173:
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6047: trailing whitespace.
+194:
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6058: trailing whitespace.
+205:
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6081: trailing whitespace.
+228:
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6085: trailing whitespace.
+232:
exit: 2
```

### Command 927 — final temporary index

```text
$ env GIT_INDEX_FILE=/tmp/kix-perf-pin-final-ocpikj0d/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-final-ocpikj0d/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git read-tree HEAD
exit: 0
```

### Command 928 — final temporary index

```text
$ env GIT_INDEX_FILE=/tmp/kix-perf-pin-final-ocpikj0d/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-final-ocpikj0d/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git add --intent-to-add -- docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md
exit: 0
```

### Command 929 — final three-file diff

```text
$ env GIT_INDEX_FILE=/tmp/kix-perf-pin-final-ocpikj0d/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-final-ocpikj0d/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git diff --name-only origin/main
docs/README.md
docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md
validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md
exit: 0
```

### Command 930 — final whitespace including new files

```text
$ env GIT_INDEX_FILE=/tmp/kix-perf-pin-final-ocpikj0d/index GIT_OBJECT_DIRECTORY=/tmp/kix-perf-pin-final-ocpikj0d/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/workspace/kix-run/repo/.git/objects git diff --check
exit: 0
```

### Command 931 — final normal whitespace

```text
$ git diff --check
exit: 0
```

### Command 932 — real index unchanged

```text
$ git diff --cached --name-only
exit: 0
```

## Temporary consistency script

This script ran from /tmp, is documentary evidence only, and is not installed
as a repository checker. Its helper only captures subprocess outputs/exits.

```python
from pathlib import Path
import subprocess,json,re,sys,hashlib,collections,unicodedata
sys.path.insert(0,'/tmp');from kix_evidence import run
add=Path('docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md').read_text()
stop_path=Path('/workspace/kix-run/wt/plan-perf-probe-fail-closed-and-release-repro/DECISION_REQUIRED.md')
stop=stop_path.read_text()
assert hashlib.sha256(stop_path.read_bytes()).hexdigest() in add
for heading,nextheading in [('Options','Recommendation'),('Recommendation','Who decides')]:
 text=stop.split('## '+heading+'\n\n')[1].split('\n## '+nextheading)[0].strip()
 assert '\n'.join('> '+line if line else '>' for line in text.splitlines()) in add, heading
assert 'This document selects no option and changes no node state.' in add
assert 'Decision owner for PERF-PROBE: **the User (repository owner)**' in add
closure=Path('docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md').read_text()
ids=['L1','L2','A2','A4','A5','BCS1','SD1','PERF-PROBE']
for key in ids:
 rows=[l for l in add.splitlines() if l.startswith('| '+key+' |')];assert len(rows)==1
 cells=[c.strip() for c in rows[0].strip('|').split('|')];assert cells[4:6]==['STILL OPEN','none']
 if key!='PERF-PROBE':
  old=next(l for l in closure.splitlines() if l.startswith('| '+key+' |'))
  assert cells[3]==[c.strip() for c in old.strip('|').split('|')][3]
print('PASS: exact source options/recommendation, digest, non-selection, eight stops, seven verbatim owners')
pins=json.loads(Path('/tmp/kix-pins.json').read_text())
scan=run(['git','grep','-n','-E','(^|[^0-9a-f])[0-9a-f]{40}([^0-9a-f]|$)','HEAD','--','*.rs','*.py','*.md'],'acceptance basis scan')
for key,p in pins.items():
 assert p['pin'] in add and p['current'] in add
 assert run(['git','rev-parse','HEAD:'+p['target']],'acceptance pin '+key).strip()==p['current']
 grouped=collections.defaultdict(list)
 for file,line,source in p['occurrences']:
  original=subprocess.check_output(['git','show','HEAD:'+file],text=True).splitlines()[line-1]
  assert p['pin'] in original
  grouped[file].append(str(line))
 for file,lines in grouped.items():assert f"| {key} | `{file}:{','.join(lines)}` |" in add,(key,file)
assert pins['P1']['status']==pins['P2']['status']=='MATCH'
assert pins['P3']['status']=='DIFFERS'
# Every 40-hex token in Rust/Python is accounted for: eight known pin values,
# commit IDs in audit prose/fixtures, and one tree ID in the checker.
known={p['pin'] for p in pins.values()}
for l in scan.splitlines():
 file=l.split(':')[1]
 if not file.endswith(('.rs','.py')):continue
 for h in re.findall(r'(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])',l):
  if h not in known:assert subprocess.check_output(['git','cat-file','-t',h],text=True).strip() in ['commit','tree'],l
print('PASS: all executable/fixture candidates and every pin-value file:line occurrence accounted for; P1/P2 MATCH, P3 DIFFERS')
merges=json.loads(Path('/tmp/kix-merges.json').read_text())
for pr,sha in merges:
 assert f'| #{pr} | `{sha}` |' in add
 parents=run(['git','show','-s','--format=%P',sha],'acceptance merge '+pr).split()
 assert len(parents)==2
 if pr=='317':assert parents[1]=='7ba8003f4a18bbd622ce87b1cfb0fa856e4a4178'
 if pr=='318':assert parents[1]=='41abd142e7b16a6ab1370cf001b3fccb4b720900'
print('PASS: eight first-parent PR/merge identities and stop implementation heads')
maptext=Path('docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md').read_text()
for key in ['X-RELEASE-REPRO','X-OUTPUT-FILES','BD-RUN-VALUES']:
 line=next(l for l in maptext.splitlines() if l.startswith('| '+key+' |'))
 assert [c.strip() for c in line.strip('|').split('|')][5]=='NOT_RUN',line
print('PASS: three release rows remain NOT_RUN')
# Local Markdown destinations plus GitHub-style heading fragments.
for dest in re.findall(r'\]\(([^)]+)\)',add):
 file,_,anchor=dest.partition('#')
 target=(Path('docs/status')/file).resolve() if file else Path('docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md').resolve()
 assert target.is_file(),dest
 if anchor:
  heads=[]
  for l in target.read_text().splitlines():
   if l.startswith('#'):
    h=re.sub(r'[^\w\- ]','',l.lstrip('#').strip().lower()).replace(' ','-')
    heads.append(h)
  assert anchor in heads,(dest,heads)
print('PASS: all addendum Markdown links and fragments resolve')
missing=['durable/','scripts/stage5_local_check.py','validation/2026-10-13-k-stage5-durable-tx/','validation/2026-10-15-rs-4-l2-load/','docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md','scripts/check_sdk_compat_manifest_evidence_map.py']
for path in missing:assert not Path(path).exists(),path
print('PASS: six named L1/L2/SD1 missing artifacts remain absent')
expected={'docs/README.md','docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md','validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md'}
tracked=set(run(['git','diff','--name-only','origin/main'],'actual index diff').splitlines())
untracked=set(run(['git','ls-files','--others','--exclude-standard'],'actual untracked').splitlines())
assert tracked|untracked==expected,(tracked,untracked)
for path in expected:
 assert all(l==l.rstrip() for l in Path(path).read_text().splitlines()),path
print('PASS: exactly three deliverable paths including untracked files; new-file whitespace clean')
```

Actual acceptance output (exit 0):

```text
PASS: exact source options/recommendation, digest, non-selection, eight stops, seven verbatim owners
PASS: all executable/fixture candidates and every pin-value file:line occurrence accounted for; P1/P2 MATCH, P3 DIFFERS
PASS: eight first-parent PR/merge identities and stop implementation heads
PASS: three release rows remain NOT_RUN
PASS: all addendum Markdown links and fragments resolve
PASS: six named L1/L2/SD1 missing artifacts remain absent
PASS: exactly three deliverable paths including untracked files; new-file whitespace clean
```

## Temporary capture and offline-check procedures

```python
import subprocess, json, shlex
from pathlib import Path
LOG=Path('/tmp/kix-evidence.jsonl')
def run(args, label='', expected=0):
    p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    row={'label':label,'command':shlex.join(args),'exit':p.returncode,'output':p.stdout}
    with LOG.open('a') as f: f.write(json.dumps(row)+'\n')
    if p.returncode != expected: raise RuntimeError(row)
    return p.stdout
if __name__=='__main__':
    run(['git','rev-parse','origin/main','HEAD'],'basis')
    run(['git','status','--short','--untracked-files=all'],'start status')
    for path in ['runtime/crates/kix-kernel/src/lib.rs','runtime/crates/kix-kernel/tests/quarantine_capacity.rs']:
        run(['git','rev-parse','HEAD:'+path],'before locks')
        run(['git','hash-object','--',path],'before locks')
    paths=run(['git','ls-files','-z','reference/v0.3-rc1/','.aiops/'],'before protected manifest').rstrip('\0').split('\0')
    manifest={}
    for path in paths:
        head=run(['git','rev-parse','HEAD:'+path],'before protected').strip()
        actual=run(['git','hash-object','--',path],'before protected').strip()
        assert head==actual, path
        manifest[path]=head
    Path('/tmp/kix-protected.json').write_text(json.dumps(manifest))
    scan=run(['git','grep','-n','-E','(^|[^0-9a-f])[0-9a-f]{40}([^0-9a-f]|$)','HEAD','--','*.rs','*.py','*.md'],'complete source scan')
    import re, collections
    values=collections.Counter(re.findall(r'(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])',scan))
    classified={}
    for value in sorted(values):
        p=subprocess.run(['git','cat-file','-t',value],text=True,capture_output=True)
        classified[value]={'kind':p.stdout.strip() if p.returncode==0 else 'unavailable','count':values[value]}
    Path('/tmp/kix-values.json').write_text(json.dumps(classified))
    print('candidate lines',len(scan.splitlines()),'unique values',len(values))
    print(collections.Counter(v['kind'] for v in classified.values()))
    for v,meta in classified.items():
        if meta['kind'] not in ['commit','tree','tag']: print(v,meta)
```

```python
from pathlib import Path
import re,sys,shlex
sys.path.insert(0,'/tmp');from kix_evidence import run
workflow=Path('.github/workflows/protocol.yml').read_text()
block=workflow.split('      - name: Stdlib offline document checks\n',1)[1].split('      - uses:',1)[0]
commands=[line.strip() for line in block.splitlines() if re.fullmatch(r'\s*python3 scripts/check_\w+\.py(?: --self-test)?',line)]
assert len(commands)==57,len(commands)
assert 'python3 scripts/check_stage5_host.py --self-test' in commands
assert 'python3 scripts/check_stage5_host.py' not in commands
for cmd in commands:
 result=run(shlex.split(cmd),'CI offline block')
 print(cmd,'-> exit 0; '+result.strip().splitlines()[-1])
print('PASS: all 57 workflow offline-document commands exited 0')
```

```python
from pathlib import Path
import json,sys,os,tempfile,subprocess
sys.path.insert(0,'/tmp');from kix_evidence import run
pins=json.loads(Path('/tmp/kix-pins.json').read_text())
for key in ['P1','P2']:
 p=pins[key];assert run(['git','rev-parse','HEAD:'+p['target']],'after locks').strip()==p['pin']
 assert run(['git','hash-object','--',p['target']],'after locks').strip()==p['pin']
manifest=json.loads(Path('/tmp/kix-protected.json').read_text())
paths=run(['git','ls-files','-z','reference/v0.3-rc1/','.aiops/'],'after protected manifest').rstrip('\0').split('\0')
assert set(paths)==set(manifest)
for path,before in manifest.items():
 assert run(['git','rev-parse','origin/main:'+path],'after protected').strip()==before
 assert run(['git','hash-object','--',path],'after protected').strip()==before
assert not run(['git','ls-files','--others','--exclude-standard','reference/v0.3-rc1/','.aiops/'],'protected untracked').strip()
assert not run(['git','diff','--name-only','origin/main','--','runtime/crates/kix-kernel/src/lib.rs','runtime/crates/kix-kernel/tests/quarantine_capacity.rs','reference/v0.3-rc1/','.aiops/','docs/tasks/'],'protected diff').strip()
print(f'PASS: two locks and all {len(manifest)} tracked reference/.aiops files byte-identical to base and before manifest')
new=['docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md','validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md']
with tempfile.TemporaryDirectory(prefix='kix-perf-pin-index-') as temp:
 index=str(Path(temp)/'index')
 objects=Path(temp)/'objects'
 objects.mkdir()
 original_objects=run(['git','rev-parse','--path-format=absolute','--git-path','objects'],'original object store').strip()
 prefix=['env','GIT_INDEX_FILE='+index,'GIT_OBJECT_DIRECTORY='+str(objects),'GIT_ALTERNATE_OBJECT_DIRECTORIES='+original_objects]
 run(prefix+['git','read-tree','HEAD'],'temporary index')
 run(prefix+['git','add','--intent-to-add','--']+new,'temporary index')
 names=run(prefix+['git','diff','--name-only','origin/main'],'three-file diff with temporary index')
 assert set(names.splitlines())==set(new+['docs/README.md'])
 run(prefix+['git','diff','--check'],'whitespace with temporary index')
 print('PASS: git diff --name-only origin/main (temporary index) lists exactly:\n'+names,end='')
run(['git','diff','--check'],'normal index whitespace')
run(['git','status','--short','--untracked-files=all'],'final status')
print('PASS: real index untouched; normal git diff --check exit 0')
```
