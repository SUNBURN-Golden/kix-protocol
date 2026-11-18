"""Source-informed, offline transport evidence for F04 §§7.11–7.12 refusals.

Literal inputs and expected errors transcribe the two pinned contract suites.
Replay calls the unchanged observers; helpers here are test-only, not a service
or a protocol interface. No error precedence or product policy is established.
"""
from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from credit_fixture import FixtureError, decode_json, exact_fields  # noqa: E402
from settlement_credit_boundary_vectors import canonical  # noqa: E402
import settlement_variance as variance  # noqa: E402
import shared_exposure as exposure  # noqa: E402

FIXTURE = HERE / 'fixtures/capital_refusal_vectors_v1.json'
FIXTURE_SHA256 = '1b0b82f2fba57a1fafe911a5416faa71131a1e871ac1eb0ca97391d37b9f3331'
SOURCE_PATHS = (
    'docs/contracts/CREDIT_ADVANCE_F04.md',
    'docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md',
    'reference/credit_advance_f04/credit_fixture.py',
    'reference/credit_advance_f04/fixtures/settlement_variance_v1.json',
    'reference/credit_advance_f04/fixtures/shared_exposure_v1.json',
    'reference/credit_advance_f04/settlement_credit_boundary_vectors.py',
    'reference/credit_advance_f04/settlement_variance.py',
    'reference/credit_advance_f04/shared_exposure.py',
    'reference/credit_advance_f04/test_settlement_variance_contract.py',
    'reference/credit_advance_f04/test_shared_exposure_contract.py',
)
# Explicit 18 + 33 source cases, independent of the artifact and observer output.
# Columns: case_id, source method, source parameter/mutation, predicate, error code.
INVENTORY = (
    ('V01_tolerance_omitted', 'test_tolerance_is_required_with_no_default', 'tolerance omitted', 'tolerance is a required keyword with no default', 'TOLERANCE_REQUIRED'),
    ('V02_tolerance_true', 'test_tolerance_rejects_bool_negative_float_string_and_none', 'tolerance=true', 'tolerance must be a non-bool int >= 0', 'TOLERANCE_INVALID'),
    ('V03_tolerance_false', 'test_tolerance_rejects_bool_negative_float_string_and_none', 'tolerance=false', 'tolerance must be a non-bool int >= 0', 'TOLERANCE_INVALID'),
    ('V04_tolerance_negative', 'test_tolerance_rejects_bool_negative_float_string_and_none', 'tolerance=-1', 'tolerance must be a non-bool int >= 0', 'TOLERANCE_INVALID'),
    ('V05_tolerance_integer_float', 'test_tolerance_rejects_bool_negative_float_string_and_none', 'tolerance=1.0', 'tolerance must be a non-bool int >= 0', 'TOLERANCE_INVALID'),
    ('V06_tolerance_fraction', 'test_tolerance_rejects_bool_negative_float_string_and_none', 'tolerance=0.5', 'tolerance must be a non-bool int >= 0', 'TOLERANCE_INVALID'),
    ('V07_tolerance_string', 'test_tolerance_rejects_bool_negative_float_string_and_none', 'tolerance="10"', 'tolerance must be a non-bool int >= 0', 'TOLERANCE_INVALID'),
    ('V08_tolerance_null', 'test_tolerance_rejects_bool_negative_float_string_and_none', 'tolerance=null', 'tolerance must be a non-bool int >= 0', 'TOLERANCE_INVALID'),
    ('V09_claim_mismatch', 'test_view_binding_conflict_is_rejected', 'credit_view.claim_id="claim-other"', 'views must share claim_id and trade_id; currency must be KRW', 'VIEW_BINDING_CONFLICT'),
    ('V10_trade_mismatch', 'test_view_binding_conflict_is_rejected', 'credit_view.trade_id="trade-other"', 'views must share claim_id and trade_id; currency must be KRW', 'VIEW_BINDING_CONFLICT'),
    ('V11_currency_mismatch', 'test_view_binding_conflict_is_rejected', 'settlement_view.currency="USD"', 'views must share claim_id and trade_id; currency must be KRW', 'VIEW_BINDING_CONFLICT'),
    ('V12_unfrozen', 'test_view_must_be_frozen', 'credit_view.snapshot_frozen=false', 'credit view must have snapshot_frozen=true', 'VIEW_NOT_FROZEN'),
    ('V13_missing_obligations', 'test_malformed_and_non_mock_views_are_rejected', 'settlement_view.obligations omitted', 'source-informed characterization: required mock view fields and bounded non-bool integer amounts', 'VIEW_INVALID'),
    ('V14_settlement_provenance', 'test_malformed_and_non_mock_views_are_rejected', 'settlement_view.provenance="SOME_OTHER_PROVENANCE"', 'source-informed characterization: required mock view fields and bounded non-bool integer amounts', 'VIEW_INVALID'),
    ('V15_cash_float', 'test_malformed_and_non_mock_views_are_rejected', 'settlement_view.confirmed_cash=0.0', 'source-informed characterization: required mock view fields and bounded non-bool integer amounts', 'VIEW_INVALID'),
    ('V16_outstanding_bool', 'test_malformed_and_non_mock_views_are_rejected', 'settlement_view.obligations[0].outstanding=true', 'source-informed characterization: required mock view fields and bounded non-bool integer amounts', 'VIEW_INVALID'),
    ('V17_credit_provenance', 'test_malformed_and_non_mock_views_are_rejected', 'credit_view.provenance="SOME_OTHER_PROVENANCE"', 'source-informed characterization: required mock view fields and bounded non-bool integer amounts', 'VIEW_INVALID'),
    ('V18_negative_face', 'test_malformed_and_non_mock_views_are_rejected', 'credit_view.open_face=-1', 'source-informed characterization: required mock view fields and bounded non-bool integer amounts', 'VIEW_INVALID'),
    ('E01_limit_omitted', 'test_limit_is_required_with_no_default', 'limit omitted', 'limit is a required keyword with no default', 'LIMIT_REQUIRED'),
    ('E02_limit_true', 'test_limit_rejects_bool_negative_float_string_and_none', 'limit=true', 'limit must be a non-bool int >= 0', 'LIMIT_INVALID'),
    ('E03_limit_false', 'test_limit_rejects_bool_negative_float_string_and_none', 'limit=false', 'limit must be a non-bool int >= 0', 'LIMIT_INVALID'),
    ('E04_limit_negative', 'test_limit_rejects_bool_negative_float_string_and_none', 'limit=-1', 'limit must be a non-bool int >= 0', 'LIMIT_INVALID'),
    ('E05_limit_integer_float', 'test_limit_rejects_bool_negative_float_string_and_none', 'limit=1.0', 'limit must be a non-bool int >= 0', 'LIMIT_INVALID'),
    ('E06_limit_fraction', 'test_limit_rejects_bool_negative_float_string_and_none', 'limit=0.5', 'limit must be a non-bool int >= 0', 'LIMIT_INVALID'),
    ('E07_limit_string', 'test_limit_rejects_bool_negative_float_string_and_none', 'limit="10"', 'limit must be a non-bool int >= 0', 'LIMIT_INVALID'),
    ('E08_limit_null', 'test_limit_rejects_bool_negative_float_string_and_none', 'limit=null', 'limit must be a non-bool int >= 0', 'LIMIT_INVALID'),
    ('E09_reserved_conflict', 'test_view_binding_conflict_is_rejected', 'views[1].reserved_open+=1; residual_unreserved-=1', 'same-claim trade_id and capacity snapshots must agree; currency must be KRW', 'VIEW_BINDING_CONFLICT'),
    ('E10_trade_conflict', 'test_view_binding_conflict_is_rejected', 'views[1].trade_id="trade-other"', 'same-claim trade_id and capacity snapshots must agree; currency must be KRW', 'VIEW_BINDING_CONFLICT'),
    ('E11_face_conflict', 'test_view_binding_conflict_is_rejected', 'views[1].open_face+=1; residual_unreserved+=1', 'same-claim trade_id and capacity snapshots must agree; currency must be KRW', 'VIEW_BINDING_CONFLICT'),
    ('E12_currency_conflict', 'test_view_binding_conflict_is_rejected', 'views[0].currency="USD"', 'same-claim trade_id and capacity snapshots must agree; currency must be KRW', 'VIEW_BINDING_CONFLICT'),
    ('E13_unfrozen', 'test_view_must_be_frozen', 'views[0].snapshot_frozen=false', 'views must be frozen; pre-draw grouping is undefined', 'VIEW_NOT_FROZEN'),
    ('E14_pre_draw', 'test_view_must_be_frozen', 'approved adv-pre actual CreditMachine.view before draw', 'views must be frozen; pre-draw grouping is undefined', 'VIEW_NOT_FROZEN'),
    ('E15_missing_outstanding', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].outstanding_exposure omitted', 'required view fields', 'VIEW_INVALID'),
    ('E16_provenance', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].provenance="SOME_OTHER_PROVENANCE"', 'mock provenance', 'VIEW_INVALID'),
    ('E17_ledger', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].exposure_ledger="SOME_OTHER_LEDGER"', 'mock exposure ledger', 'VIEW_INVALID'),
    ('E18_outstanding_bool', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].outstanding_exposure=true', 'non-bool integer amounts', 'VIEW_INVALID'),
    ('E19_negative_drawn', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].drawn_exposure=-1', 'amounts >= 0', 'VIEW_INVALID'),
    ('E20_repaid_float', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].repaid_exposure=1.0', 'integer amounts', 'VIEW_INVALID'),
    ('E21_face_overflow', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].open_face=1000000000001', 'amounts <= 10**12', 'VIEW_INVALID'),
    ('E22_exposure_arithmetic', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].outstanding_exposure+=1', 'outstanding_exposure = drawn_exposure - repaid_exposure', 'VIEW_INVALID'),
    ('E23_capacity_arithmetic', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].residual_unreserved+=1', 'residual_unreserved = open_face - reserved_open', 'VIEW_INVALID'),
    ('E24_phase', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].phase="OFFERED" (other fields unchanged)', 'phase must be DRAWN, CLOSED or DEFAULTED', 'VIEW_INVALID'),
    ('E25_advance_label', 'test_malformed_and_non_mock_views_are_rejected', 'views[0].advance_id=" x"', 'source-informed characterization: advance_id must be a nonempty trimmed string', 'VIEW_INVALID'),
    ('E26_duplicate_advance', 'test_malformed_and_non_mock_views_are_rejected', '[copy(base[0]), copy(base[0])]', 'duplicate advance_id is invalid', 'VIEW_INVALID'),
    ('E27_empty_views', 'test_malformed_and_non_mock_views_are_rejected', 'credit_views=[]', 'nonempty list of credit views', 'VIEW_INVALID'),
    ('E28_group_empty', 'test_malformed_and_non_mock_views_are_rejected', 'group_id=""', 'source-informed characterization: group_id must be a nonempty trimmed string caller label', 'VIEW_INVALID'),
    ('E29_group_space', 'test_malformed_and_non_mock_views_are_rejected', 'group_id=" x"', 'source-informed characterization: group_id must be a nonempty trimmed string caller label', 'VIEW_INVALID'),
    ('E30_group_integer', 'test_malformed_and_non_mock_views_are_rejected', 'group_id=123', 'source-informed characterization: group_id must be a nonempty trimmed string caller label', 'VIEW_INVALID'),
    ('E31_group_bool', 'test_malformed_and_non_mock_views_are_rejected', 'group_id=true', 'source-informed characterization: group_id must be a nonempty trimmed string caller label', 'VIEW_INVALID'),
    ('E32_group_null', 'test_malformed_and_non_mock_views_are_rejected', 'group_id=null', 'source-informed characterization: group_id must be a nonempty trimmed string caller label', 'VIEW_INVALID'),
    ('E33_non_list', 'test_malformed_and_non_mock_views_are_rejected', 'credit_views={"not":"a list"}', 'nonempty list of credit views', 'VIEW_INVALID'),
)
DISPATCH = {
    'observe_settlement_variance': (
        variance.observe_settlement_variance, variance.VarianceObservationError,
        'tolerance', 'settlement_variance', 'SettlementVarianceContractTests', '7.11'),
    'observe_shared_exposure': (
        exposure.observe_shared_exposure, exposure.SharedExposureError,
        'limit', 'shared_exposure', 'SharedExposureContractTests', '7.12'),
}


def _require(condition, message):
    if not condition:
        raise AssertionError(message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _verify_structure(pack):
    """Validate transport/citations only; malformed observer values pass through."""
    exact_fields(pack, {'fixture_version', 'fixture_kind', 'synthetic_only',
                        'provenance', 'source_pins', 'cases'}, 'refusal pack')
    _require(pack['fixture_version'] == 'capital-refusal/1', 'fixture version')
    _require(pack['fixture_kind'] == 'SYNTHETIC_OBSERVER_REJECTION_VECTORS', 'fixture kind')
    _require(pack['synthetic_only'] is True, 'synthetic only')
    _require(pack['provenance'] == {'settlement': 'MOCK_SETTLEMENT_ONLY',
                                  'credit': 'MOCK_CREDIT_F04_ONLY'}, 'provenance')
    _require(type(pack['cases']) is list, 'cases must be a list')
    ids = []
    for case in pack['cases']:
        exact_fields(case, {'case_id', 'observer', 'source_test', 'source_case',
                            'contract', 'predicate', 'arguments', 'keywords',
                            'expected_error'}, 'case')
        for field in ('case_id', 'observer', 'source_test', 'source_case', 'contract', 'predicate'):
            _require(type(case[field]) is str and bool(case[field]), field)
        _require(case['observer'] in DISPATCH, 'observer selector')
        keyword = DISPATCH[case['observer']][2]
        _require(type(case['arguments']) is list and len(case['arguments']) == 2,
                 'two positional arguments required')
        exact_fields(case['keywords'], set(), 'keywords', {keyword})
        exact_fields(case['expected_error'], {'type', 'code'}, 'expected error')
        ids.append(case['case_id'])
    expected_ids = [row[0] for row in INVENTORY]
    _require(len(ids) == len(set(ids)), 'duplicate case ID')
    _require(ids == expected_ids, 'missing, extra or reordered source cases')
    for case, (case_id, method, source_case, predicate, code) in zip(pack['cases'], INVENTORY):
        observer = ('observe_settlement_variance' if case_id.startswith('V')
                    else 'observe_shared_exposure')
        _, error_class, _, module, source_class, section = DISPATCH[observer]
        source_test = (f'reference/credit_advance_f04/test_{module}_contract.py::'
                       f'{source_class}.{method}')
        _require(case['observer'] == observer, f'{case_id}: observer')
        _require(case['source_test'] == source_test, f'{case_id}: source test')
        _require(case['source_case'] == source_case, f'{case_id}: source case')
        _require(case['predicate'] == predicate, f'{case_id}: predicate')
        _require(case['contract'] == f'docs/contracts/CREDIT_ADVANCE_F04.md#{section}',
                 f'{case_id}: contract')
        _require(case['expected_error'] == {'type': error_class.__name__, 'code': code},
                 f'{case_id}: expected error')


def _verify_sources(pack, read_source=None):
    if read_source is None:
        read_source = lambda path: (ROOT / path).read_bytes()
    pins = pack['source_pins']
    _require(type(pins) is list, 'source pins must be a list')
    for pin in pins:
        exact_fields(pin, {'path', 'sha256'}, 'source pin')
    _require([pin['path'] for pin in pins] == list(SOURCE_PATHS), 'source path inventory')
    for pin in pins:
        _require(pin['sha256'] == _sha(read_source(pin['path'])),
                 f'source hash: {pin["path"]}')


def _load(raw):
    pack = decode_json(raw.decode('utf-8'))
    _require(canonical(pack) == raw, 'noncanonical artifact')
    _require(_sha(raw) == FIXTURE_SHA256, 'artifact hash')
    _verify_structure(pack)
    _verify_sources(pack)
    return pack


def _replay(case):
    observer, error_class, *_ = DISPATCH[case['observer']]
    arguments, keywords = copy.deepcopy((case['arguments'], case['keywords']))
    before = canonical([arguments, keywords])
    try:
        try:
            observer(*arguments, **keywords)
        except Exception as error:
            _require(type(error) is error_class, f'{case["case_id"]}: exception class {type(error)}')
            _require(type(error).__name__ == case['expected_error']['type'], 'expected exception type')
            _require(error.code == case['expected_error']['code'], f'{case["case_id"]}: code {error.code}')
        else:
            raise AssertionError(f'{case["case_id"]}: observer unexpectedly succeeded')
    finally:
        # Canonical bytes distinguish True/1/1.0, unlike Python container equality.
        _require(canonical([arguments, keywords]) == before, f'{case["case_id"]}: input mutation')


class CapitalRefusalVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = FIXTURE.read_bytes()
        cls.pack = _load(cls.raw)
        cls.by_id = {case['case_id']: case for case in cls.pack['cases']}

    def test_artifact_and_source_pins(self):
        self.assertEqual(_sha(self.raw), FIXTURE_SHA256)
        self.assertEqual(self.raw, canonical(self.pack))
        _verify_sources(self.pack)

    def test_case_inventory_and_citations(self):
        _verify_structure(self.pack)
        self.assertEqual(sum(key.startswith('V') for key in self.by_id), 18)
        self.assertEqual(sum(key.startswith('E') for key in self.by_id), 33)
        for case in self.pack['cases']:
            with self.subTest(case=case['case_id']):
                path, qualified = case['source_test'].split('::')
                class_name, method_name = qualified.split('.')
                tree = ast.parse((ROOT / path).read_text(encoding='utf-8'))
                source_class = next(node for node in tree.body
                                    if isinstance(node, ast.ClassDef) and node.name == class_name)
                self.assertIn(method_name, [node.name for node in source_class.body
                                           if isinstance(node, ast.FunctionDef)])
                contract, section = case['contract'].split('#')
                self.assertIn(f'### {section} ', (ROOT / contract).read_text(encoding='utf-8'))

    def test_input_types_and_keyword_presence(self):
        for prefix, keyword in (('V', 'tolerance'), ('E', 'limit')):
            self.assertEqual(self.by_id[f'{prefix}01_{keyword}_omitted']['keywords'], {})
            values = (('true', True), ('false', False), ('negative', -1),
                      ('integer_float', 1.0), ('fraction', 0.5), ('string', '10'), ('null', None))
            for number, (label, value) in enumerate(values, 2):
                keywords = self.by_id[f'{prefix}{number:02}_{keyword}_{label}']['keywords']
                self.assertEqual(set(keywords), {keyword})
                self.assertIs(type(keywords[keyword]), type(value))
                self.assertEqual(canonical(keywords[keyword]), canonical(value))
        self.assertNotIn('obligations', self.by_id['V13_missing_obligations']['arguments'][0])
        self.assertIs(type(self.by_id['V15_cash_float']['arguments'][0]['confirmed_cash']), float)
        self.assertIs(self.by_id['V16_outstanding_bool']['arguments'][0]['obligations'][0]['outstanding'], True)
        self.assertNotIn('outstanding_exposure', self.by_id['E15_missing_outstanding']['arguments'][1][0])
        self.assertIs(type(self.by_id['E20_repaid_float']['arguments'][1][0]['repaid_exposure']), float)
        pre = self.by_id['E14_pre_draw']['arguments'][1][0]
        self.assertEqual(pre['phase'], 'APPROVED')
        self.assertIs(pre['snapshot_frozen'], False)
        self.assertEqual(self.by_id['E26_duplicate_advance']['arguments'][1][0],
                         self.by_id['E26_duplicate_advance']['arguments'][1][1])
        for case_id, expected_type in [('E28_group_empty', str), ('E29_group_space', str),
                                      ('E30_group_integer', int), ('E31_group_bool', bool),
                                      ('E32_group_null', type(None))]:
            self.assertIs(type(self.by_id[case_id]['arguments'][0]), expected_type)
        self.assertEqual(self.by_id['E27_empty_views']['arguments'][1], [])
        self.assertEqual(self.by_id['E33_non_list']['arguments'][1], {'not': 'a list'})

    def test_rejections_match_and_preserve_inputs(self):
        before = canonical(self.pack)
        for case in self.pack['cases']:
            with self.subTest(case=case['case_id']):
                _replay(case)
        self.assertEqual(canonical(self.pack), before)

    def test_positive_controls(self):
        for module in (variance, exposure):
            fixture = module.load_fixture(module.FIXTURE)
            before = canonical(fixture)
            results = module.run_scenarios(fixture)
            self.assertEqual(len(results), 6)
            self.assertEqual(canonical(fixture), before)
            for result in results:
                with self.subTest(control=result['id']):
                    self.assertIs(result['match'], True)
                    record = result['record']
                    self.assertEqual(record['mapping'], module.MAPPING)
                    self.assertEqual(record['mapping']['contract_status'], 'NOT_BOUND')
                    self.assertEqual(record['mapping']['repair'], 'NONE')
                    self.assertEqual(record['refund_component'], 'NOT_BOUND')
                    self.assertIs(record['authorizes_exposure'], False)
                    self.assertIs(record['mutates_state'], False)
                    self.assertIs(record['fail_closed'], True)
                    if module is exposure:
                        self.assertIs(record['legal_debtor_bound'], False)

    def test_verifier_sensitivity(self):
        # Semantic checks run directly, bypassing the artifact hash so it cannot
        # conceal an ineffective inventory, replay or source verifier.
        for mutation in ('missing', 'duplicate', 'code', 'type', 'citation', 'predicate'):
            pack = copy.deepcopy(self.pack)
            if mutation == 'missing': pack['cases'].pop()
            elif mutation == 'duplicate': pack['cases'][-1] = copy.deepcopy(pack['cases'][0])
            elif mutation == 'code': pack['cases'][0]['expected_error']['code'] = 'TOLERANCE_INVALID'
            elif mutation == 'type': pack['cases'][0]['expected_error']['type'] = 'SharedExposureError'
            elif mutation == 'citation': pack['cases'][0]['source_test'] += '_missing'
            else: pack['cases'][0]['predicate'] = 'changed predicate'
            with self.subTest(structure=mutation), self.assertRaises(AssertionError):
                _verify_structure(pack)
        for field, value in (('code', 'TOLERANCE_INVALID'), ('type', 'SharedExposureError')):
            case = copy.deepcopy(self.pack['cases'][0])
            case['expected_error'][field] = value
            with self.subTest(replay=field), self.assertRaises(AssertionError):
                _replay(case)
        success = copy.deepcopy(self.by_id['V08_tolerance_null'])
        success['keywords'] = {'tolerance': 0}
        with self.assertRaisesRegex(AssertionError, 'unexpectedly succeeded'):
            _replay(success)
        for mutation in ('missing', 'duplicate', 'digest', 'path'):
            pack = copy.deepcopy(self.pack)
            if mutation == 'missing': pack['source_pins'].pop()
            elif mutation == 'duplicate': pack['source_pins'].append(pack['source_pins'][0])
            elif mutation == 'digest': pack['source_pins'][0]['sha256'] = '0' * 64
            else: pack['source_pins'][0]['path'] = '../outside'
            with self.subTest(pins=mutation), self.assertRaises(AssertionError):
                _verify_sources(pack)
        changed_path = SOURCE_PATHS[0]
        with self.assertRaisesRegex(AssertionError, 'source hash'):
            _verify_sources(self.pack, lambda path: (ROOT / path).read_bytes()
                            + (b'changed' if path == changed_path else b''))
        changed = copy.deepcopy(self.pack)
        changed['cases'][0]['keywords'] = {'tolerance': None}
        with self.assertRaisesRegex(AssertionError, 'artifact hash'):
            _load(canonical(changed))
        with self.assertRaisesRegex(AssertionError, 'noncanonical'):
            _load(self.raw + b'\n')
        for malformed in ('{"duplicate":1,"duplicate":2}', 'NaN', '1e999'):
            with self.subTest(json=malformed), self.assertRaises(FixtureError):
                _load(malformed.encode('utf-8'))
        for mutation in ('keyword', 'arity', 'extra_field'):
            pack = copy.deepcopy(self.pack)
            case = pack['cases'][0]
            if mutation == 'keyword': case['keywords'] = {'limit': 0}
            elif mutation == 'arity': case['arguments'].pop()
            else: case['extra'] = True
            with self.subTest(wrapper=mutation), self.assertRaises((AssertionError, FixtureError)):
                _verify_structure(pack)


if __name__ == '__main__':
    unittest.main()
