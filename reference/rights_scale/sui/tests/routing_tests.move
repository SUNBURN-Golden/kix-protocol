#[test_only]
/// Known answers computed independently in Python (blake2b-256 over show id || reference ||
/// profile_version as little-endian u64, first 8 bytes little-endian, modulo shard count).
module kix_rights_scale::routing_tests;
use kix_rights_scale::rights_scale as rs;
use kix_rights_scale::support as s;

fun route(tag: u8, version: u64, shards: u64): u64 {
    rs::route_index(object::id_from_address(@0xab), s::ref_bytes(tag), version, shards)
}

#[test]
fun routing_matches_the_python_reference() {
    let four = vector[2u64, 0, 3, 0, 1, 2, 3, 0];
    let eight = vector[2u64, 4, 7, 4, 5, 2, 7, 4];
    let two = vector[0u64, 0, 1, 0, 1, 0, 1, 0];
    let sixty_four = vector[18u64, 20, 31, 44, 37, 50, 39, 44];
    let mut i = 0;
    while (i < 8) {
        let tag = ((i + 1) as u8);
        assert!(route(tag, 1, 1) == 0);
        assert!(route(tag, 1, 2) == two[i]);
        assert!(route(tag, 1, 4) == four[i]);
        assert!(route(tag, 1, 8) == eight[i]);
        assert!(route(tag, 1, 64) == sixty_four[i]);
        i = i + 1;
    };
    // profile_version is part of the hash input.
    assert!(route(1, 2, 4) == 0 && route(1, 1, 4) == 2);
}

#[test]
fun the_same_bytes_always_reach_the_same_shard() {
    let mut shards = 1;
    while (shards <= 8) {
        let mut tag = 1u8;
        while (tag <= 20) {
            assert!(route(tag, 1, shards) == route(tag, 1, shards) && route(tag, 1, shards) < shards);
            tag = tag + 1;
        };
        shards = shards * 2;
    };
}

/// A reference reserved through its routed shard is found show-wide: reuse is rejected
/// whatever the shard count.
fun reuse(shards: u64) {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 8, 0, 4, shards);
    s::reserve(&mut sc, show, 0, 0, s::b(), 50000, s::ref_bytes(3));
    s::reserve(&mut sc, show, 1, 0, s::c(), 50000, s::ref_bytes(3));
    sc.end();
}
#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun reuse_is_rejected_with_1_shard() { reuse(1); }
#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun reuse_is_rejected_with_2_shards() { reuse(2); }
#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun reuse_is_rejected_with_4_shards() { reuse(4); }
#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun reuse_is_rejected_with_8_shards() { reuse(8); }

/// A shard that is not the routed one cannot hold the reference.
#[test, expected_failure(abort_code = 16, location = kix_rights_scale::rights_scale)]
fun a_reference_cannot_be_recorded_in_the_wrong_shard() {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 8, 0, 4, 2);
    let routed = route_for_show(&mut sc, show, 3);
    s::reserve_in_shard(&mut sc, show, 0, s::b(), s::ref_bytes(3), 1 - routed);
    sc.end();
}
fun route_for_show(sc: &mut sui::test_scenario::Scenario, show: ID, tag: u8): u64 {
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<rs::ShowControl>(show);
    let r = rs::shard_index_for_ref(&c, s::ref_bytes(tag));
    sui::test_scenario::return_shared(c);
    r
}
