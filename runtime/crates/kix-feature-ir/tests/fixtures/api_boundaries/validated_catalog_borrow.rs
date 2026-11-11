mod support;

fn main() {
    let (candidate, mut schemas) = support::validated_inputs();
    let checked = candidate.validate_with_schemas(&schemas).unwrap();
    schemas.clear();
    let _ = checked.catalog();
}
