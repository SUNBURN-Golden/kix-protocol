mod support;

fn main() {
    let profile = support::profile();
    let _ = profile.export_amount(100_u128);
}
