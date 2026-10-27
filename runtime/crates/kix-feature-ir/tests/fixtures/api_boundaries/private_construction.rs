mod support;

use kix_feature_ir::Fast64MoneyProfile;

fn main() {
    let _ = Fast64MoneyProfile {
        key: support::key(),
        registry_hash: support::registry_hash(),
        execution_max_atoms: 100,
    };
}
