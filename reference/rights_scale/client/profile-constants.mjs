// Localnet fixture values of the extended rights profile, mirrored from
// sui/sources/rights_scale.move. Astra-owned; none is a protocol value and none is an
// operational default (docs/contracts/RIGHTS_SCALE_PROFILE.md sections 4 and 13).
// The private journey reads the same numbers back from the published package through
// view calls and refuses to run when they differ, so this file cannot drift silently.
export const PROFILE_VERSION=1;
export const DEPTH=10;            // note tree depth, revocation tree depth, slot range-check bits
export const SLOT_BITS=10;
export const ROOT_HISTORY_K=4;    // test-only fixture; the operational K is UNDETERMINED (DECISION_REQUIRED, Astra)
export const NULLIFIER_SHARDS=4;
export const CHALLENGE_SHARDS=4;
export const SHIELDED=3;
export const MINT='mint_scale';
export const SPEND='spend_scale';
export const MINT_PUBLIC=['commitment','slot','generation','domain'];
export const SPEND_PUBLIC=['noteRoot','revocationRoot','nullifier','context','domain','action'];
