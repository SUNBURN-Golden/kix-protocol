mod support;

use kix_feature_ir::Stage;

fn main() {
    let (mut candidate, schemas) = support::validated_inputs();
    let checked = candidate.validate_with_schemas(&schemas).unwrap();
    candidate.stages.push(Stage::Limit(2));
    let _ = checked.plan();
}
