# rs-1 decision answer — owner delegate (2026-10-13)

Appended verbatim from the task input. Author: owner delegate.

**Selected: Option 2.** RS-1 implements the public path against the merged draft as it sits on commit `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1`. Astra architecture review of `docs/contracts/RIGHTS_SCALE_PROFILE.md` 0.1 and `docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md` happens at the RS-1 ARCHITECTURE gate, not as a predecessor. This sentence is the explicit User authorization option 2 asked for.

**Records to make (builder, this or next RS-1 session):**
- Add `docs/decisions/RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md` stating the above, naming the commit, and naming the owner delegate as author. Do not edit the status line of profile 0.1; it stays "초안" until Astra signs at the gate.
- Update `docs/status/CURRENT_CAPABILITY_REGISTER.md` RS-1 row to "in progress; authorized against draft 0.1 @ 9b12626b". RS-0 row stays SOURCE_ONLY.
- `state/rs-1.decision_answer.md` gets this answer appended.

**Scope of RS-1 implementation:** `issue`, `seal`, page claim, bundle, `revoke`, `cancel_show` exactly as the §3 table reads. Localnet only. Reference model and tests included.

**Open items, resolved for RS-1:**
- **GA redistribution (RS-C02 sentence 2):** not implemented. No new §3 operation. Stays `DECISION_REQUIRED · Astra`. Add a test asserting no redistribution entry exists in the package.
- **CI wiring:** yes. Builder adds a `rights-scale` job to `.github/workflows` that runs the new Move tests and localnet driver on pull requests to `main`. Required check, not optional.
- **Localnet constants (not protocol values; mainnet values stay `UNDETERMINED · Astra`):** `profile_version = 1`; `MAX_BUNDLE_CHAIN = 8`; `P = 1024` slots per show; `S = 64` slots per page; routing hash = `blake2b256(show_id || page_index || profile_version)`. Declared as named constants in one module with a comment "localnet default; Astra-owned".
- **IssuerCap:** one owned object minted to the publisher at package publish. `issue` takes `&IssuerCap`. No transfer or burn function in RS-1. `rs-1-issuercap-probe` runs first in the RS-1 session; if it contradicts this, the probe result wins and is recorded.
- **Sort key for page claim ordering:** `(page_index asc, claim_sequence asc)`.
- **Visibility:** all state and decision files committed to `agent/kix-rs-1`, visible in repo. No private channel.
- **Retention:** decision records in `docs/decisions` are permanent. `state/*.decision*.md` kept until the RS-1 gate closes, then archived under `docs/decisions/archive/`.
- **Legal hold:** none.

**Excluded, unchanged:** anything needing money, hardware, Sui mainnet or any production deployment, real secrets, or production runtime. Marked deferred, owner Astra/User.

An earlier draft from the stopped build may already be in the worktree; continue from it.
