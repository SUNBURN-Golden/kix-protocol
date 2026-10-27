#![allow(dead_code)]

use kix_feature_ir::{Fast64MoneyProfile, MoneyProfileKey};
use kix_types::{AssetAmount, AssetId, Hash32, RegistryVersion};

pub fn key() -> MoneyProfileKey {
    MoneyProfileKey {
        asset_id: AssetId::from_bytes([1; 32]),
        registry_version: RegistryVersion::new(2).unwrap(),
    }
}

pub fn registry_hash() -> Hash32 {
    Hash32::from_bytes([3; 32])
}

pub fn profile() -> Fast64MoneyProfile {
    Fast64MoneyProfile::checked(key(), registry_hash(), 100).unwrap()
}

pub fn amount() -> AssetAmount {
    let key = key();
    AssetAmount::checked(
        key.asset_id,
        100,
        100,
        key.registry_version,
        registry_hash(),
    )
    .unwrap()
}
