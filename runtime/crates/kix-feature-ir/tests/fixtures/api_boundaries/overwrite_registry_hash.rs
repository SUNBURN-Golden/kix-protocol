mod support;

fn main() {
    let mut profile = support::profile();
    profile.registry_hash = support::registry_hash();
}
