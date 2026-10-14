#[test_only]
/// Root rules RR-1 and RR-2 as pure arithmetic. Every constant below was produced by
/// `client/gen-move-vectors.mjs` with circomlibjs, the Poseidon the circuits use, so these
/// tests tie the on-chain `poseidon_bn254` tree math to the circuit-side hash.
/// `node gen-move-vectors.mjs --check` fails when this file and circomlibjs disagree.
module kix_rights_scale::root_math_tests;
use kix_rights_scale::rights_scale as rs;
use sui::test_scenario as ts;

const ZERO_1: u256 = 14744269619966411208579211824598458697587494354926760081771325075741142829156;
const ZERO_2: u256 = 7423237065226347324353380772367382631490014989348495481811164164159255474657;
const ZERO_9: u256 = 6573136701248752079028194407151022595060682063033565181951145966236778420039;
const EMPTY_ROOT_10: u256 = 12413880268183407374852357075976609371175688755676981206018884971008854919922;
const ROOT_3_AFTER_1: u256 = 13137366353036525042469986902114481547911233226484758790130549040613696276199;
const ROOT_3_AFTER_2: u256 = 13641718821863571325143210987927009226667968557371544972936660053391389596688;
const ROOT_3_AFTER_3: u256 = 17622378152528767967472835082403003709637669084976904759047010984916171017561;
const ROOT_10_AFTER_1: u256 = 13435157595452499831328342371188872370195603936081551072324668619215518361592;
const ROOT_10_AFTER_2: u256 = 11894166152725933167799962082781238356992134909095608370740726318210113531042;
const ROOT_10_AFTER_3: u256 = 15198915676663620714989452771055542096236157964614070370198930474590801349403;
const ROOT_10_AFTER_4: u256 = 12497660747801460804045916613486574742363061972261539687119204602169762583870;
const ROOT_10_AFTER_5: u256 = 17162178407478046736786119174946953698818562625526652776447028614558469203139;
const REV_ROOT_SLOT5_GEN3: u256 = 13244524416568403798025217453455705458746775544182100578009770988457660307114;
const REV_ROOT_SLOT5_GEN3_SLOT700_GEN9: u256 = 3152138033071002246062408124070017822973530135719734160069333386947667197940;
const REV_ROOT_SLOT5_GEN1: u256 = 13404783072601146301905239779586182435169773207776100075563879709185402771500;
const REV_ROOT_SLOT5_GEN1_SLOT6_GEN1: u256 = 13157866518049886677357396406645732991983157383651785516205048597975895031116;
const DOMAIN_SHOW_0xA_V1: u256 = 20892688189080764756269199611444112928396341353986819302201583306982655383071;
const DOMAIN_SHOW_0xA_V2: u256 = 11718660909891685775628008701364306495861560468444079594113895687833836583839;
const DOMAIN_SHOW_0xB_V1: u256 = 17059319430238837083318205685265764523248661663047995316412832935460085432932;
const DOMAIN_SHOW_0xA_V1_OTHER_HASH: u256 = 14960427691455505564621039134455698780441211410527555132588378543747957249916;

// ---------------------------------------------------------------- empty trees

#[test]
fun empty_tree_zero_hashes_match_circomlibjs() {
    let mut sc = ts::begin(@0xA);
    let tree = rs::new_tree_for_testing(object::id_from_address(@0xA), 10, 4, sc.ctx());
    assert!(rs::tree_zero(&tree, 0) == 0);
    assert!(rs::tree_zero(&tree, 1) == ZERO_1);
    assert!(rs::tree_zero(&tree, 2) == ZERO_2);
    assert!(rs::tree_zero(&tree, 9) == ZERO_9);
    assert!(rs::tree_zero(&tree, 10) == EMPTY_ROOT_10);
    assert!(rs::tree_root(&tree) == EMPTY_ROOT_10 && rs::tree_leaf_count(&tree) == 0);
    // The ring starts with the empty root only.
    assert!(rs::tree_roots(&tree) == vector[EMPTY_ROOT_10]);
    rs::destroy_tree_for_testing(tree);
    sc.end();
}

// ---------------------------------------------------------------- RR-1 incremental tree

#[test]
fun depth_three_incremental_roots_match_circomlibjs() {
    let mut sc = ts::begin(@0xA);
    let mut tree = rs::new_tree_for_testing(object::id_from_address(@0xA), 3, 8, sc.ctx());
    rs::tree_insert_for_testing(&mut tree, 11);
    assert!(rs::tree_root(&tree) == ROOT_3_AFTER_1);
    rs::tree_insert_for_testing(&mut tree, 22);
    assert!(rs::tree_root(&tree) == ROOT_3_AFTER_2);
    rs::tree_insert_for_testing(&mut tree, 33);
    assert!(rs::tree_root(&tree) == ROOT_3_AFTER_3 && rs::tree_leaf_count(&tree) == 3);
    // Index 2 is a left child, so the level-0 frontier holds the newest leaf.
    assert!(rs::tree_frontier(&tree, 0) == 33);
    rs::destroy_tree_for_testing(tree);
    sc.end();
}

#[test]
fun depth_ten_incremental_roots_match_circomlibjs() {
    let mut sc = ts::begin(@0xA);
    let mut tree = rs::new_tree_for_testing(object::id_from_address(@0xA), 10, 8, sc.ctx());
    let expected = vector[ROOT_10_AFTER_1, ROOT_10_AFTER_2, ROOT_10_AFTER_3, ROOT_10_AFTER_4, ROOT_10_AFTER_5];
    let mut i = 0;
    while (i < expected.length()) {
        rs::tree_insert_for_testing(&mut tree, (101 + i) as u256);
        assert!(rs::tree_root(&tree) == expected[i]);
        i = i + 1;
    };
    assert!(rs::tree_leaf_count(&tree) == 5);
    rs::destroy_tree_for_testing(tree);
    sc.end();
}

#[test]
fun history_keeps_exactly_the_last_k_roots() {
    let mut sc = ts::begin(@0xA);
    let mut tree = rs::new_tree_for_testing(object::id_from_address(@0xA), 10, 3, sc.ctx());
    let mut roots = vector[rs::tree_root(&tree)];
    let mut i = 0;
    while (i < 7) {
        rs::tree_insert_for_testing(&mut tree, (500 + i) as u256);
        roots.push_back(rs::tree_root(&tree));
        // Age 0 is the current root; ages 0..K-1 are accepted and age K is not.
        let mut age = 0;
        while (age < roots.length()) {
            let root = roots[roots.length() - 1 - age];
            assert!(rs::root_in_history(&tree, root) == (age < 3));
            age = age + 1;
        };
        assert!(rs::tree_roots(&tree).length() == if (roots.length() < 3) roots.length() else 3);
        i = i + 1;
    };
    rs::destroy_tree_for_testing(tree);
    sc.end();
}

#[test]
fun a_history_of_one_accepts_only_the_current_root() {
    let mut sc = ts::begin(@0xA);
    let mut tree = rs::new_tree_for_testing(object::id_from_address(@0xA), 4, 1, sc.ctx());
    let before = rs::tree_root(&tree);
    rs::tree_insert_for_testing(&mut tree, 1);
    assert!(!rs::root_in_history(&tree, before) && rs::root_in_history(&tree, rs::tree_root(&tree)));
    rs::destroy_tree_for_testing(tree);
    sc.end();
}

#[test]
fun an_unknown_root_is_never_in_the_history() {
    let mut sc = ts::begin(@0xA);
    let mut tree = rs::new_tree_for_testing(object::id_from_address(@0xA), 4, 4, sc.ctx());
    rs::tree_insert_for_testing(&mut tree, 1);
    assert!(!rs::root_in_history(&tree, 0) && !rs::root_in_history(&tree, 12345));
    rs::destroy_tree_for_testing(tree);
    sc.end();
}

/// RR-1: leaves are append-only, so the leaf capacity is the number of successful inserts.
#[test, expected_failure(abort_code = 20, location = kix_rights_scale::rights_scale)]
fun the_leaf_after_capacity_aborts() {
    let mut sc = ts::begin(@0xA);
    let mut tree = rs::new_tree_for_testing(object::id_from_address(@0xA), 2, 4, sc.ctx());
    let mut i = 0;
    while (i < 5) { rs::tree_insert_for_testing(&mut tree, (i + 1) as u256); i = i + 1; };
    rs::destroy_tree_for_testing(tree);
    sc.end();
}

#[test]
fun the_last_leaf_up_to_capacity_is_accepted() {
    let mut sc = ts::begin(@0xA);
    let mut tree = rs::new_tree_for_testing(object::id_from_address(@0xA), 2, 4, sc.ctx());
    let mut i = 0;
    while (i < 4) { rs::tree_insert_for_testing(&mut tree, (i + 1) as u256); i = i + 1; };
    assert!(rs::tree_leaf_count(&tree) == 4);
    rs::destroy_tree_for_testing(tree);
    sc.end();
}

// ---------------------------------------------------------------- RR-2 sparse revocation tree

public fun rev_root_slot5_gen1(): u256 { REV_ROOT_SLOT5_GEN1 }
public fun rev_root_slot5_gen1_slot6_gen1(): u256 { REV_ROOT_SLOT5_GEN1_SLOT6_GEN1 }
public fun empty_root(): u256 { EMPTY_ROOT_10 }

public fun rev_siblings_5(): vector<u256> {
    vector[
        0,
        14744269619966411208579211824598458697587494354926760081771325075741142829156,
        7423237065226347324353380772367382631490014989348495481811164164159255474657,
        11286972368698509976183087595462810875513684078608517520839298933882497716792,
        3607627140608796879659380071776844901612302623152076817094415224584923813162,
        19712377064642672829441595136074946683621277828620209496774504837737984048981,
        20775607673010627194014556968476266066927294572720319469184847051418138353016,
        3396914609616007258851405644437304192397291162432396347162513310381425243293,
        21551820661461729022865262380882070649935529853313286572328683688269863701601,
        6573136701248752079028194407151022595060682063033565181951145966236778420039,
    ]
}

public fun rev_siblings_700(): vector<u256> {
    vector[
        0,
        14744269619966411208579211824598458697587494354926760081771325075741142829156,
        7423237065226347324353380772367382631490014989348495481811164164159255474657,
        11286972368698509976183087595462810875513684078608517520839298933882497716792,
        3607627140608796879659380071776844901612302623152076817094415224584923813162,
        19712377064642672829441595136074946683621277828620209496774504837737984048981,
        20775607673010627194014556968476266066927294572720319469184847051418138353016,
        3396914609616007258851405644437304192397291162432396347162513310381425243293,
        21551820661461729022865262380882070649935529853313286572328683688269863701601,
        21514904242129687568952375775041687404767496121443096417241720531776930620941,
    ]
}

public fun rev_siblings_6_after_5(): vector<u256> {
    vector[
        0,
        12583541437132735734108669866114103169564651237895298778035846191048104863326,
        7423237065226347324353380772367382631490014989348495481811164164159255474657,
        11286972368698509976183087595462810875513684078608517520839298933882497716792,
        3607627140608796879659380071776844901612302623152076817094415224584923813162,
        19712377064642672829441595136074946683621277828620209496774504837737984048981,
        20775607673010627194014556968476266066927294572720319469184847051418138353016,
        3396914609616007258851405644437304192397291162432396347162513310381425243293,
        21551820661461729022865262380882070649935529853313286572328683688269863701601,
        6573136701248752079028194407151022595060682063033565181951145966236778420039,
    ]
}

#[test]
fun sparse_update_roots_match_circomlibjs() {
    // The empty tree and the leaf 0 give the empty root for any slot.
    assert!(rs::sparse_root_for_testing(10, 0, 5, rev_siblings_5()) == EMPTY_ROOT_10);
    // Slot 5 revoked at generation 3.
    assert!(rs::sparse_root_for_testing(10, 3, 5, rev_siblings_5()) == REV_ROOT_SLOT5_GEN3);
    // The issuer's next witness for slot 700 verifies against that root with leaf 0 ...
    assert!(rs::sparse_root_for_testing(10, 0, 700, rev_siblings_700()) == REV_ROOT_SLOT5_GEN3);
    // ... and produces the combined root with generation 9.
    assert!(rs::sparse_root_for_testing(10, 9, 700, rev_siblings_700()) == REV_ROOT_SLOT5_GEN3_SLOT700_GEN9);
}

#[test]
fun sparse_root_depends_on_the_leaf_value_and_the_slot() {
    let a = rs::sparse_root_for_testing(10, 1, 5, rev_siblings_5());
    assert!(a == REV_ROOT_SLOT5_GEN1);
    assert!(a != rs::sparse_root_for_testing(10, 2, 5, rev_siblings_5()));
    assert!(a != rs::sparse_root_for_testing(10, 1, 4, rev_siblings_5()));
    assert!(rs::sparse_root_for_testing(10, 1, 6, rev_siblings_6_after_5()) != a);
    assert!(rs::sparse_root_for_testing(10, 0, 6, rev_siblings_6_after_5()) == REV_ROOT_SLOT5_GEN1);
    assert!(rs::sparse_root_for_testing(10, 1, 6, rev_siblings_6_after_5()) == REV_ROOT_SLOT5_GEN1_SLOT6_GEN1);
}

#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun a_short_sibling_path_aborts() {
    let mut siblings = rev_siblings_5();
    siblings.pop_back();
    rs::sparse_root_for_testing(10, 1, 5, siblings);
}

#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun a_slot_outside_the_tree_aborts() {
    rs::sparse_root_for_testing(10, 1, 1024, rev_siblings_5());
}

#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun a_non_field_sibling_aborts() {
    let mut siblings = rev_siblings_5();
    siblings.pop_back();
    siblings.push_back(21888242871839275222246405745257275088548364400416034343698204186575808495617);
    rs::sparse_root_for_testing(10, 1, 5, siblings);
}

// ---------------------------------------------------------------- RS-C11 domain

#[test]
fun domain_matches_circomlibjs_and_binds_show_version_and_manifest() {
    let manifest = x"1111111111111111111111111111111111111111111111111111111111111111";
    let other = x"2222222222222222222222222222222222222222222222222222222222222222";
    let a = rs::domain_of(object::id_from_address(@0xA), 1, manifest);
    assert!(a == DOMAIN_SHOW_0xA_V1);
    assert!(rs::domain_of(object::id_from_address(@0xA), 2, manifest) == DOMAIN_SHOW_0xA_V2);
    assert!(rs::domain_of(object::id_from_address(@0xB), 1, manifest) == DOMAIN_SHOW_0xB_V1);
    assert!(rs::domain_of(object::id_from_address(@0xA), 1, other) == DOMAIN_SHOW_0xA_V1_OTHER_HASH);
    assert!(a != DOMAIN_SHOW_0xA_V2 && a != DOMAIN_SHOW_0xB_V1 && a != DOMAIN_SHOW_0xA_V1_OTHER_HASH);
}

#[test, expected_failure(abort_code = 18, location = kix_rights_scale::rights_scale)]
fun a_manifest_hash_that_is_not_32_bytes_aborts() {
    rs::domain_of(object::id_from_address(@0xA), 1, x"1111");
}
