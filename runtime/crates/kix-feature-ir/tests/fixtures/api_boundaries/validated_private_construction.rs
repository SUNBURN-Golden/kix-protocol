mod support;

use kix_feature_ir::ValidatedFeaturePlan;

fn main() {
    let (candidate, schemas) = support::validated_inputs();
    let _ = ValidatedFeaturePlan {
        plan: &candidate,
        catalog: &schemas,
        output: Vec::new(),
    };
}
