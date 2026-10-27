#![allow(dead_code)]

use kix_feature_ir::{
    ColumnId, ColumnSchema, DatasetRef, DatasetSchema, Fast64MoneyProfile, FeaturePlanV1,
    MoneyProfileKey, OutputKind, Stage,
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

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

// Synthetic schema claims only; validation does not authenticate their source.
pub fn validated_inputs() -> (FeaturePlanV1, Vec<DatasetSchema>) {
    let dataset = DatasetRef {
        dataset_id: KixId::from_bytes([2; 16]),
        schema_version: 1,
    };
    (
        FeaturePlanV1 {
            plan_id: KixId::from_bytes([1; 16]),
            source: dataset,
            stages: vec![Stage::Limit(1)],
        },
        vec![DatasetSchema {
            dataset,
            columns: vec![ColumnSchema {
                column: ColumnId(1),
                kind: OutputKind::I64,
            }],
        }],
    )
}
