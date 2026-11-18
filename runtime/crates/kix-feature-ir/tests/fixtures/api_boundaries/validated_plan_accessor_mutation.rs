mod support;

fn main() {
    let (candidate, schemas) = support::validated_inputs();
    let checked = candidate.validate_with_schemas(&schemas).unwrap();
    checked.plan().stages.clear();
}
