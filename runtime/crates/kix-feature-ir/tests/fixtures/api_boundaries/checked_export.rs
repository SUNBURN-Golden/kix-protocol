mod support;

use kix_feature_ir::{Fast64MoneyProfile, FeatureIrError};
use kix_types::AssetAmount;

fn main() {
    let profile =
        Fast64MoneyProfile::checked(support::key(), support::registry_hash(), 100).unwrap();
    let amount: AssetAmount = support::amount();
    let _: Result<i64, FeatureIrError> = profile.export_amount(amount);
    let _ = profile.key();
    let _ = profile.registry_hash();
    let _: i64 = profile.execution_max_atoms();
}
