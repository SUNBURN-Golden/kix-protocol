mod support;

use kix_feature_ir::OutputKind;

fn main() {
    let (candidate, schemas) = support::validated_inputs();
    let checked = candidate.validate_with_schemas(&schemas).unwrap();
    checked.output_schema()[0].kind = OutputKind::U64;
}
