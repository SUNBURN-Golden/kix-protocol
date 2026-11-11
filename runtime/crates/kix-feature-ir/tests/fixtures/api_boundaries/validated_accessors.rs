mod support;

use kix_feature_ir::{ColumnSchema, DatasetSchema, FeaturePlanV1, ValidatedFeaturePlan};

fn main() {
    let (candidate, schemas) = support::validated_inputs();
    let checked: ValidatedFeaturePlan<'_> = candidate.validate_with_schemas(&schemas).unwrap();
    let _: &FeaturePlanV1 = checked.plan();
    let _: &[DatasetSchema] = checked.catalog();
    let _: &[ColumnSchema] = checked.output_schema();
}
