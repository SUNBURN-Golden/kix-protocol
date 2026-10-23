#[test_only]
/// RS-C15 and the creation staging of profile section 7.
module kix_rights_scale::creation_tests;
use kix_rights_scale::rights_scale::{Self as rs, ShowControl, InventoryPage, PaymentRefShard, IssuerCap};
use kix_rights_scale::support as s;
use sui::test_scenario as ts;

#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun consumption_before_seal_is_rejected() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 8, 0, 4, 2);
    s::stage(&mut sc, show);
    s::issue(&mut sc, show, 0, 0, s::b());
    sc.end();
}

#[test]
fun staged_show_opens_only_at_seal_and_matches_the_range_table() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 16, 0, 4, 2);
    s::stage(&mut sc, show);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    assert!(!rs::control_open(&c) && !rs::control_sealed(&c));
    assert!(rs::control_claimed_pages(&c) == 4 && rs::control_page_count(&c) == 4);
    assert!(rs::control_claimed_shards(&c) == 2 && rs::control_shard_count(&c) == 2);
    assert!(rs::control_claim_sequence(&c) == 6);
    ts::return_shared(c);
    s::seal(&mut sc, show);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    assert!(rs::control_open(&c) && rs::control_sealed(&c) && rs::control_cancel_generation(&c) == 0);
    ts::return_shared(c);
    sc.end();
}

#[test]
fun staging_over_several_transactions_still_yields_one_page_per_index() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 16, 4, 4, 3);
    // 4 seated pages + 1 GA page, 3 shards: claimed in uneven batches, out of order.
    let mut k = 0u64;
    while (k < 3) {
        sc.next_tx(s::a());
        let mut c = sc.take_shared_by_id<ShowControl>(show);
        let cap = sc.take_from_sender<IssuerCap>();
        if (k == 0) { rs::claim_pages(&mut c, &cap, 3, 2, sc.ctx()); }
        else if (k == 1) { rs::claim_pages(&mut c, &cap, 0, 3, sc.ctx()); }
        else { rs::claim_shards(&mut c, &cap, 0, 3, sc.ctx()); };
        ts::return_shared(c);
        sc.return_to_sender(cap);
        k = k + 1;
    };
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    assert!(rs::control_claimed_pages(&c) == 5 && rs::control_page_count(&c) == 5);
    assert!(rs::control_claimed_shards(&c) == 3 && rs::control_claim_sequence(&c) == 8);
    ts::return_shared(c);
    s::seal(&mut sc, show);
    sc.end();
}

#[test, expected_failure(abort_code = sui::derived_object::EObjectAlreadyExists)]
fun second_claim_of_the_same_page_aborts() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 8, 0, 4, 1);
    s::stage(&mut sc, show);
    sc.next_tx(s::a());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    // A retry after a lost response, with new transaction bytes.
    rs::claim_pages(&mut c, &cap, 1, 1, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
    sc.end();
}

#[test, expected_failure(abort_code = sui::derived_object::EObjectAlreadyExists)]
fun overlapping_page_claim_range_aborts() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 12, 0, 4, 1);
    sc.next_tx(s::a());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::claim_pages(&mut c, &cap, 0, 2, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
    sc.next_tx(s::a());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::claim_pages(&mut c, &cap, 1, 2, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
    sc.end();
}

#[test, expected_failure(abort_code = sui::derived_object::EObjectAlreadyExists)]
fun second_claim_of_the_same_shard_aborts() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 8, 0, 4, 2);
    s::stage(&mut sc, show);
    sc.next_tx(s::a());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::claim_shards(&mut c, &cap, 0, 1, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
    sc.end();
}

#[test]
fun page_and_shard_keys_do_not_share_an_address_space() {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 8, 0, 4, 2);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut i = 0;
    while (i < 2) {
        assert!(rs::page_address(&c, i) != rs::shard_address(&c, i));
        i = i + 1;
    };
    // Both kinds of object exist at their derived addresses, claimed through the same UID.
    let p = sc.take_shared_by_id<InventoryPage>(s::page_id(&c, 1));
    let sh = sc.take_shared_by_id<PaymentRefShard>(s::shard_id(&c, 1));
    assert!(rs::page_start(&p) == 4 && rs::shard_size(&sh) == 0);
    ts::return_shared(sh); ts::return_shared(p); ts::return_shared(c);
    sc.end();
}

#[test, expected_failure(abort_code = 14, location = kix_rights_scale::rights_scale)]
fun seal_without_every_page_is_rejected() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 12, 0, 4, 1);
    sc.next_tx(s::a());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::claim_pages(&mut c, &cap, 0, 2, sc.ctx());
    rs::claim_shards(&mut c, &cap, 0, 1, sc.ctx());
    rs::seal(&mut c, &cap, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
    sc.end();
}

#[test, expected_failure(abort_code = 14, location = kix_rights_scale::rights_scale)]
fun seal_without_every_shard_is_rejected() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 8, 0, 4, 2);
    sc.next_tx(s::a());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::claim_pages(&mut c, &cap, 0, 2, sc.ctx());
    rs::claim_shards(&mut c, &cap, 0, 1, sc.ctx());
    rs::seal(&mut c, &cap, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
    sc.end();
}

#[test, expected_failure(abort_code = 13, location = kix_rights_scale::rights_scale)]
fun seal_twice_is_rejected() {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 8, 0, 4, 1);
    s::seal(&mut sc, show);
    sc.end();
}

#[test, expected_failure(abort_code = 13, location = kix_rights_scale::rights_scale)]
fun no_page_can_be_added_after_seal() {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 8, 0, 4, 1);
    sc.next_tx(s::a());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::claim_pages(&mut c, &cap, 0, 1, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
    sc.end();
}

#[test, expected_failure(abort_code = 17, location = kix_rights_scale::rights_scale)]
fun claiming_past_the_range_table_is_rejected() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 8, 0, 4, 1);
    sc.next_tx(s::a());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::claim_pages(&mut c, &cap, 1, 2, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
    sc.end();
}

#[test, expected_failure(abort_code = 17, location = kix_rights_scale::rights_scale)]
fun claiming_zero_shards_is_rejected() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 8, 0, 4, 1);
    sc.next_tx(s::a());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::claim_shards(&mut c, &cap, 0, 0, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
    sc.end();
}

#[test, expected_failure(abort_code = 4, location = kix_rights_scale::rights_scale)]
fun another_publisher_cannot_claim_pages_of_this_show() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 8, 0, 4, 1);
    sc.next_tx(s::b());
    rs::init_for_testing(sc.ctx());
    sc.next_tx(s::b());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::claim_pages(&mut c, &cap, 0, 1, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
    sc.end();
}

fun create_with(seated: u64, ga: u64, page_size: u64, shards: u64, gates: vector<address>, org: u64, plat: u64) {
    let mut sc = s::begin();
    sc.next_tx(s::a());
    let cap = sc.take_from_sender<IssuerCap>();
    rs::create_show_control(&cap, seated, ga, page_size, shards, gates, vector[s::att()], 150000, org, plat,
        object::id_from_address(@0x0), sc.ctx());
    sc.return_to_sender(cap);
    sc.end();
}
#[test, expected_failure(abort_code = 6, location = kix_rights_scale::rights_scale)]
fun zero_page_size_is_rejected() { create_with(8, 0, 0, 1, vector[s::gate()], 200, 300); }
#[test, expected_failure(abort_code = 6, location = kix_rights_scale::rights_scale)]
fun zero_shards_are_rejected() { create_with(8, 0, 4, 0, vector[s::gate()], 200, 300); }
#[test, expected_failure(abort_code = 6, location = kix_rights_scale::rights_scale)]
fun zero_capacity_is_rejected() { create_with(0, 0, 4, 1, vector[s::gate()], 200, 300); }
#[test, expected_failure(abort_code = 6, location = kix_rights_scale::rights_scale)]
fun empty_gate_list_is_rejected() { create_with(8, 0, 4, 1, vector[], 200, 300); }
#[test, expected_failure(abort_code = 6, location = kix_rights_scale::rights_scale)]
fun bps_over_ten_thousand_is_rejected() { create_with(8, 0, 4, 1, vector[s::gate()], 9000, 1001); }

/// Seated pages first, then GA pages; ranges are contiguous, disjoint and cover [0, total).
fun table(seated: u64, ga: u64, page_size: u64) {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, seated, ga, page_size, 1);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let pages = s::take_pages(&sc, &c);
    let mut expected_start = 0;
    let mut i = 0;
    while (i < pages.length()) {
        let p = &pages[i];
        assert!(rs::page_start(p) == expected_start);
        assert!(rs::page_end(p) > rs::page_start(p) && rs::page_end(p) - rs::page_start(p) <= page_size);
        assert!(rs::page_free(p) == rs::page_end(p) - rs::page_start(p) && rs::page_conserved(p));
        let ga_page = rs::page_start(p) >= seated;
        assert!(rs::page_mode(p) == if (ga_page) 1 else 0);
        // A page never straddles the seated/GA boundary.
        assert!(rs::page_start(p) >= seated || rs::page_end(p) <= seated);
        assert!(rs::page_index_for_slot(&c, rs::page_start(p)) == i);
        assert!(rs::page_index_for_slot(&c, rs::page_end(p) - 1) == i);
        assert!(!rs::page_delegated(p));
        expected_start = rs::page_end(p);
        i = i + 1;
    };
    assert!(expected_start == seated + ga && rs::control_capacity(&c) == seated + ga);
    s::return_pages(pages);
    ts::return_shared(c);
    sc.end();
}
#[test] fun table_15_in_pages_of_4() { table(15, 0, 4); }
#[test] fun table_16_in_pages_of_4() { table(16, 0, 4); }
#[test] fun table_17_in_pages_of_4() { table(17, 0, 4); }
#[test] fun table_1023_in_pages_of_64() { table(1023, 0, 64); }
#[test] fun table_1024_in_pages_of_64() { table(1024, 0, 64); }
#[test] fun table_1025_in_pages_of_64() { table(1025, 0, 64); }
#[test] fun table_mixed_seated_and_ga() { table(10, 6, 4); }
#[test] fun table_all_ga() { table(0, 8, 4); }
#[test] fun table_one_slot_pages() { table(5, 0, 1); }
#[test] fun table_one_page_larger_than_the_show() { table(3, 0, 1024); }
