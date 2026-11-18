mod support;

fn main() {
    let mut profile = support::profile();
    profile.key = support::key();
}
