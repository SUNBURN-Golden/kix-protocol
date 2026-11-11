mod support;

fn main() {
    let profile = support::profile();
    let _ = profile.registry_hash;
}
