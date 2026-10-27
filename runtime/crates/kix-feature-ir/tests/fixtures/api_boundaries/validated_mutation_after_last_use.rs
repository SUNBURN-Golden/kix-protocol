mod support;

use kix_feature_ir::Stage;

fn main() {
    let (mut candidate, mut schemas) = support::validated_inputs();
    let checked = candidate.validate_with_schemas(&schemas).unwrap();
    let _ = checked.plan();
    let _ = checked.catalog();
    let _ = checked.output_schema();
    // The wrapper binding remains in scope, but its last use precedes mutation.
    candidate.stages.push(Stage::Limit(2));
    schemas.clear();
}
