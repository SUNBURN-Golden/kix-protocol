"""Offline companion navigation checks; existing suites own economic replay.

No fixture writes, subprocesses, consumer calls, or imported TestCase classes.
Detached byte readers exercise pin and association validation independently.
"""
from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path
import re
import unittest

from credit_fixture import decode_json, exact_fields, FixtureError
from settlement_credit_boundary_vectors import canonical

ROOT = Path(__file__).resolve().parents[2]
INDEX = 'docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json'
GUIDE = 'docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md'
CONTRACT = 'docs/contracts/CREDIT_ADVANCE_F04.md'
BASE = 'reference/credit_advance_f04/'
FIXTURES = BASE + 'fixtures/'
COMMERCE_RECEIPTS = 'reference/booking_resale_admission/fixtures/commerce_linked_refund_receipts_v1.json'
COMMERCE_RECEIPTS_SHA256 = '7181761ec5533cf1a9aab450f4a7f3d32ed6c467713c8d532ceff24a89908839'
RESALE_SDK_VECTORS = 'sdk/conformance/vectors/commerce-fixture-tuple.vectors.json'
RESALE_JOURNEY_RECEIPTS = 'reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json'
RESALE_JOURNEY_INPUT = 'reference/booking_resale_admission/fixtures/commerce_journey_conformance_v1.json'
RESALE_SOURCE_PINS = (
    (RESALE_SDK_VECTORS, 'c9fbeee6a04da371dd054a325c9435a401b9694a1619ac9939de38f257495e22'),
    (RESALE_JOURNEY_RECEIPTS, '6819d46a7b86e1a16bae83be90666560bb45aa66d3d6f0d5e050e03e7a952998'),
    (RESALE_JOURNEY_INPUT, 'f9555d84790b91eafe74c71453a2dbd301fae43566a5f0a3a47e19059151e9cc'),
)
SELF_CONTAINED_SHAPES = {'self_contained_refusals', 'self_contained_comparisons'}
# Independent fixed family/path, scenario/case identity and section-count inventory.
PACKS = (
    ('settlement_credit_boundary', 'ordered_steps', 'settlement_credit_boundary_v1.json', 'settlement_credit_boundary_vectors_v1.json',
     'test_settlement_credit_boundary.py', 'SettlementCreditBoundaryTests.test_vector_pack_replays_exactly',
     'Existing coverage mapped before adding tests (AGENTS.md §7)',
     ('S1_captured_face_no_derivation', 'S2_committed_face_no_derivation', 'S3_face_snapshot_frozen_and_stable_view_claim', 'S4_refund_obligation_partial_acceptance', 'S5_shared_exposure_two_advances', 'S6_reconciliation_gap_reported_no_repair'), ((0, 14), (0, 12), (0, 18), (0, 14), (0, 23), (0, 17))),
    ('economics_credit_consumer', 'scenario_inputs', 'economics_credit_consumer_v1.json', 'economics_credit_consumer_vectors_v1.json',
     'test_economics_credit_consumer_vectors.py', 'EconomicsCreditConsumerTests.test_public_snapshot_bytes_and_pins',
     'Histories and consumer example',
     ('P_partial_requester', 'F_full_before_distribution', 'FD_full_after_distribution'), ((0, 0), (0, 0), (0, 0))),
    ('capital_refusal', 'self_contained_refusals', 'capital_refusal_vectors_v1.json', 'capital_refusal_vectors_v1.json',
     'test_capital_refusal_vectors.py', 'CapitalRefusalVectorTests.test_rejections_match_and_preserve_inputs',
     'Capital companion rejection vectors',
     ('V01_tolerance_omitted', 'V02_tolerance_true', 'V03_tolerance_false', 'V04_tolerance_negative', 'V05_tolerance_integer_float', 'V06_tolerance_fraction', 'V07_tolerance_string', 'V08_tolerance_null', 'V09_claim_mismatch', 'V10_trade_mismatch', 'V11_currency_mismatch', 'V12_unfrozen', 'V13_missing_obligations', 'V14_settlement_provenance', 'V15_cash_float', 'V16_outstanding_bool', 'V17_credit_provenance', 'V18_negative_face', 'E01_limit_omitted', 'E02_limit_true', 'E03_limit_false', 'E04_limit_negative', 'E05_limit_integer_float', 'E06_limit_fraction', 'E07_limit_string', 'E08_limit_null', 'E09_reserved_conflict', 'E10_trade_conflict', 'E11_face_conflict', 'E12_currency_conflict', 'E13_unfrozen', 'E14_pre_draw', 'E15_missing_outstanding', 'E16_provenance', 'E17_ledger', 'E18_outstanding_bool', 'E19_negative_drawn', 'E20_repaid_float', 'E21_face_overflow', 'E22_exposure_arithmetic', 'E23_capacity_arithmetic', 'E24_phase', 'E25_advance_label', 'E26_duplicate_advance', 'E27_empty_views', 'E28_group_empty', 'E29_group_space', 'E30_group_integer', 'E31_group_bool', 'E32_group_null', 'E33_non_list'), ()),
    ('capital_operation_replay', 'setup_and_history', 'capital_operation_replay_v1.json', 'capital_operation_replay_vectors_v1.json',
     'test_capital_operation_replay_vectors.py', 'CapitalOperationReplayVectorTests.test_complete_history_vectors',
     'Capital operation replay vectors',
     ('R1_note_identity_and_historical_receipts', 'R2_repayment_sequence_refusals', 'R3_reconcile_restore_replay'), ((12, 13), (8, 9), (8, 3))),
    ('capital_terminal_capacity', 'setup_and_history', 'capital_terminal_capacity_v1.json', 'capital_terminal_capacity_vectors_v1.json',
     'test_capital_terminal_capacity_vectors.py', 'CapitalTerminalCapacityVectorTests.test_complete_history_vectors',
     'Companion terminal-capacity histories (plan-capital-terminal-capacity-vectors)',
     ('T1_repay_close_capacity_reuse', 'T2_default_retains_capacity'), ((15, 20), (15, 13))),
    ('capital_cross_claim_history', 'setup_and_history', 'capital_cross_claim_history_v1.json', 'capital_cross_claim_history_vectors_v1.json',
     'test_capital_cross_claim_history_vectors.py', 'CapitalCrossClaimHistoryVectorTests.test_complete_history_vectors',
     '2026-11-16 — ordered cross-claim Capital companion history',
     ('H1_two_claims_refund_default',), ((20, 7),)),
    ('capital_refund_composition', 'setup_and_history', 'capital_refund_composition_v1.json', 'capital_refund_composition_vectors_v1.json',
     'test_capital_refund_composition_vectors.py', 'CapitalRefundCompositionVectorTests.test_complete_history_vectors',
     'Refund composition companion (plan-capital-refund-composition-vectors)',
     ('R1_full_refund_after_partial_distribution', 'R2_partial_refunds_summing_to_gross'), ((12, 3), (12, 6))),
    ('capital_refund_identity', 'setup_and_history', 'capital_refund_identity_v1.json', 'capital_refund_identity_vectors_v1.json',
     'test_capital_refund_identity_vectors.py', 'CapitalRefundIdentityVectorTests.test_complete_history_vectors',
     'Capital refund and cancellation-acceptance identity histories',
     ('I1_refund_acceptance_identity',), ((12, 12),)),
    ('capital_reconcile_freshness', 'setup_and_history', 'capital_reconcile_freshness_v1.json', 'capital_reconcile_freshness_vectors_v1.json',
     'test_capital_reconcile_freshness_vectors.py', 'CapitalReconcileFreshnessVectorTests.test_complete_history_vectors',
     'Capital reconcile freshness vectors',
     ('F1_historical_reconcile_current_gap',), ((8, 7),)),
    ('capital_predraw_terminal', 'setup_and_history', 'capital_predraw_terminal_v1.json', 'capital_predraw_terminal_vectors_v1.json',
     'test_capital_predraw_terminal_vectors.py', 'CapitalPredrawTerminalVectorTests.test_complete_history_vectors',
     'Capital pre-draw rejection and cancellation companion (P1)',
     ('P1_reject_cancel_before_draw',), ((7, 13),)),
    ('capital_later_statement', 'setup_and_history', 'capital_later_statement_v1.json', 'capital_later_statement_vectors_v1.json',
     'test_capital_later_statement_vectors.py', 'CapitalLaterStatementVectorTests.test_complete_history_vectors',
     'Capital later settlement statement vectors',
     ('L1_later_statement_after_requester_refund',), ((8, 5),)),
    ('capital_mixed_checkpoint_views', 'self_contained_comparisons',
     'capital_mixed_checkpoint_views_vectors_v1.json', 'capital_mixed_checkpoint_views_vectors_v1.json',
     'test_capital_mixed_checkpoint_views.py', 'CapitalMixedCheckpointViewsTests.test_checkpoint_pairs',
     'Capital mixed-checkpoint views', ('repay_mixed', 'repay_same', 'close_mixed', 'close_same'), ()),
    ('capital_omitted_exposure_members', 'self_contained_comparisons',
     'capital_omitted_exposure_members_vectors_v1.json', 'capital_omitted_exposure_members_vectors_v1.json',
     'test_capital_omitted_exposure_members.py', 'CapitalOmittedExposureMembersTests.test_membership_pairs',
     'Capital omitted exposure members', ('e1_full', 'e1_omit_second', 'e2_full', 'e2_omit_second'), ()),
    ('capital_payee_order_recovery', 'self_contained_comparisons',
     'capital_payee_order_recovery_vectors_v1.json', 'capital_payee_order_recovery_vectors_v1.json',
     'test_capital_payee_order_recovery.py', 'CapitalPayeeOrderRecoveryTests.test_order_pair',
     'Capital payee order recovery', ('r1_fee_first', 'r1_residual_first'), ()),
    ('capital_offsetting_claim_gaps', 'self_contained_comparisons',
     'capital_offsetting_claim_gaps_vectors_v1.json', 'capital_offsetting_claim_gaps_vectors_v1.json',
     'test_capital_offsetting_claim_gaps.py', 'CapitalOffsettingClaimGapsTests.test_claim_pair',
     'Capital offsetting claim gaps', ('v4_claim_gap', 'v6_claim_gap'), ()),
    ('capital_commerce_refund_checkpoints', 'self_contained_comparisons',
     'capital_commerce_refund_checkpoints_vectors_v1.json', 'capital_commerce_refund_checkpoints_vectors_v1.json',
     'test_capital_commerce_refund_checkpoints.py', 'CapitalCommerceRefundCheckpointTests.test_checkpoint_replay',
     'Capital commerce refund checkpoints', ('commit', 'bind-refund', 'observe-mock-acceptance'), ()),
    ('capital_overlapping_exposure_groups', 'self_contained_comparisons',
     'capital_overlapping_exposure_groups_vectors_v1.json', 'capital_overlapping_exposure_groups_vectors_v1.json',
     'test_capital_overlapping_exposure_groups.py', 'CapitalOverlappingExposureGroupsTests.test_overlapping_groups',
     'Capital overlapping exposure groups', ('e3_ab', 'e3_bc', 'e3_abc', 'e3_duplicate_b'), ()),
    ('capital_resale_distribution_checkpoints', 'self_contained_comparisons',
     'capital_resale_distribution_checkpoints_vectors_v1.json', 'capital_resale_distribution_checkpoints_vectors_v1.json',
     'test_capital_resale_distribution_checkpoints.py', 'CapitalResaleDistributionCheckpointTests.test_checkpoint_replay',
     'Capital resale distribution checkpoints', ('settle-resale-commit', 'accept-A', 'distribute-resale'), ()),
    ('capital_group_sum_boundary', 'self_contained_comparisons',
     'capital_group_sum_boundary_vectors_v1.json', 'capital_group_sum_boundary_vectors_v1.json',
     'test_capital_group_sum_boundary.py', 'CapitalGroupSumBoundaryTests.test_group_sum_boundary',
     'Capital group sum boundary', ('at_total', 'one_below', 'single_view_overflow'), ()),
    ('capital_draw_refusal_after_restore', 'self_contained_comparisons',
     'capital_draw_refusal_after_restore_vectors_v1.json', 'capital_draw_refusal_after_restore_vectors_v1.json',
     'test_capital_draw_refusal_after_restore.py', 'CapitalDrawRefusalAfterRestoreTests.test_draw_refusal_pair',
     'Capital draw refusal after restore', ('original', 'restored'), ()),
    ('capital_equal_gross_claim_binding', 'self_contained_comparisons',
     'capital_equal_gross_claim_binding_vectors_v1.json', 'capital_equal_gross_claim_binding_vectors_v1.json',
     'test_capital_equal_gross_claim_binding.py', 'CapitalEqualGrossClaimBindingTests.test_equal_gross_claim_binding',
     'Capital equal-gross claim binding', ('matching', 'crossed'), ()),
)
QUALIFICATION = {
    'externalConsumerAcceptance': 'UNVERIFIED',
    'productLimits': {'status': 'UNDETERMINED', 'owner': 'Astra'},
    'legalResponsibility': {'status': 'UNDETERMINED', 'owner': 'User/legal'},
    'observationMapping': 'NOT_BOUND', 'refundComponent': 'NOT_BOUND',
    'repair': 'NONE', 'authorizesExposure': False, 'mutatesState': False,
    'failClosed': True, 'evidenceClass': 'B',
}
NON_CLAIMS = [
    'Non-normative discovery only; no protocol interface, client or execution authority.',
    'Source-informed Class B synthetic evidence is not clean-room verification or A2 non-author review.',
    'External kix-capital acceptance remains UNVERIFIED; no consumer was invoked.',
    'Product limits remain UNDETERMINED—Astra; legal responsibility UNDETERMINED—User/legal.',
    'Frozen faces are not revalued by later settlement refunds, distribution or acceptance.',
    'Refund obligations, recovery, PG adjustment and credit repayment remain separate; no netting is defined.',
    'Shared exposure counts capacity once per distinct claim, checks same-claim binding agreement and requires an explicit synthetic limit. Callers select the checkpoints.',
    'Within tolerance or limit is not acceptance, reconciliation completion or exposure authority.',
    'Observations and refund components remain NOT_BOUND; repair=NONE; all execution flags remain false.',
    'Snapshots and restore checks are supplemental observations, not published reads or new input commands.',
    'Hashes establish byte identity, not authenticity, durability, bank exactly-once, chain finality or legal compliance.',
    'No real funds, real PG/bank/KYC, public endpoints, Sui testnet/mainnet, secrets or production runtime.',
    'Local checks do not establish exact-head hosted KTX/KIX CI, independent review or production readiness.',
]
LIMITATIONS = {
    'settlement_credit_boundary': ['Literal settlement claim copied into F04; frozen face, separate refund obligation and reconciliation gap provide no repair or authority.'],
    'economics_credit_consumer': ['P, F and FD are distinct synthetic histories; economics distribution refusal and settlement phase are separate facts; acceptance does not repay credit.'],
    'capital_refusal': ['51 source-cited reference-only observer refusals; omitted keywords, nulls, booleans and floating numbers retain their original meanings; no new error precedence.'],
    'capital_operation_replay': ['Historical first receipts differ from current state; draw/repayment identity and restore are process-local evidence, not durable exactly-once execution.'],
    'capital_terminal_capacity': ['Repay preserves reservations; close at zero exposure releases capacity; default retains reservations and exposure. No new terminal or release behavior.'],
    'capital_cross_claim_history': ['Two distinct claims share a caller label, not a legal debtor; same-claim capacity is counted once and default exposure remains aggregated.'],
    'capital_refund_composition': ['One full-gross refund and successive partial refunds remain distinct; partial refunds summing to gross do not reclassify faces. Recovery, acceptance and credit obligations stay separate.'],
    'capital_refund_identity': ['Fresh command keys can journal an existing business binding once more. Original-key replay returns its historical receipt. Mock acceptance leaves confirmed cash, external return status and drawn credit unchanged.'],
    'capital_reconcile_freshness': ['Original keys replay their first reconcile receipts. Fresh local matches can coexist with a current variance outside the synthetic tolerance. The observation grants no exposure authority.'],
    'capital_predraw_terminal': [
        'In this synthetic, process-local history, rejection and cancellation precede the first credit note. '
        'Replays preserve historical outcomes. The separate full-capacity draw is mock evidence. '
        'Pre-draw shared-exposure grouping remains contract-undefined. A null shared_exposure records that the observer was skipped.',
    ],
    'capital_later_statement': [
        'The original statement key replays its first receipt without adding cash. '
        'The next distribution uses only new confirmed cash in the original fixture order. '
        'The requester refund and frozen credit remain separate. Cash delta is diagnostic and does not enter variance.',
    ],
    'capital_mixed_checkpoint_views': [
        'Mixing the initial and partial-repayment checkpoints can preserve same-claim binding agreement and report stale exposure. '
        'Mixing the initial and close checkpoints conflicts on reservation. Callers select the checkpoints.',
    ],
    'capital_omitted_exposure_members': [
        'Callers supply group membership. Complete means all views in the fixture scenario. '
        'The observer cannot certify real pool membership, and within_limit grants no exposure authority.',
    ],
    'capital_payee_order_recovery': [
        'The two R1 orders are caller-supplied synthetic inputs. Product waterfall priority remains '
        'UNDETERMINED with Astra. Recovery due records a fixture obligation. '
        'Collection and credit repayment are outside this comparison.',
    ],
    'capital_offsetting_claim_gaps': [
        'The zero sum is diagnostic arithmetic. Each claim remains outside its original synthetic '
        'tolerance with NOT_BOUND, repair=NONE and no exposure authority. '
        'Product thresholds remain UNDETERMINED with Astra.',
    ],
    'capital_commerce_refund_checkpoints': [
        'Three receipts for one purchase share the same frozen F04 face and zero variance. '
        'Requester refund outstanding and mock acceptance stay separate from F04 exposure and repayment. '
        'Receipt identity determines the checkpoint. The refund component remains NOT_BOUND.',
    ],
    'capital_overlapping_exposure_groups': [
        'Separate caller groups count the same defaulted advance. The distinct-member union counts '
        'it once, and a repeated advance within a single call returns VIEW_INVALID. '
        'The 90,000 KRW limit is fixture-only. Product limits remain UNDETERMINED with Astra.',
    ],
    'capital_resale_distribution_checkpoints': [
        'Commit and distribution supply settlement obligations for two observations of one frozen F04 face. '
        'The intervening resale receipt supplies mock ownership evidence only. '
        'The zero tolerance is fixture-only. Both observations retain NOT_BOUND and repair=NONE.',
    ],
    'capital_group_sum_boundary': [
        'The group sum can exceed the per-view ceiling. Both limits are synthetic caller inputs. '
        'Product limits remain UNDETERMINED with Astra. Within-limit status grants no exposure authority '
        'and the refund component remains NOT_BOUND.',
    ],
    'capital_draw_refusal_after_restore': [
        'Refused calls leave no accepted journal entry. Equal journals and state digests cannot establish '
        'whether the original received a refused call. The restored draw is an offline mock diagnostic only.',
    ],
    'capital_equal_gross_claim_binding': [
        'The F04 mock draw requires the committed settlement to match the offered claim identity '
        'even when currency and gross agree. Both settlement journals are preserved.',
    ],
}
SUPPORTING = (
    ('settlement_variance', 'SettlementVarianceContractTests', '7.11 정산 잔차(settlement variance)'),
    ('shared_exposure', 'SharedExposureContractTests', '7.12 공유 노출(shared exposure)'),
)


def _read(path):
    return (ROOT / path).read_bytes()


def _check(condition, message):
    if not condition:
        raise AssertionError(message)


def _same(left, right):
    # Canonical serialization preserves bool/int/float and omitted/null distinctions.
    return canonical(left) == canonical(right)


def _fields(value, fields, context):
    try:
        exact_fields(value, set(fields.split()), context)
    except FixtureError as error:
        raise AssertionError(str(error)) from error


def _pin(path, raw):
    return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest(),
            'gitBlob': hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()}


def _pin_check(pin, path, read):
    _fields(pin, 'path sha256 gitBlob', 'pin')
    _check(pin['path'] == path, 'pin path association')
    raw = read(path)
    _check(_same(pin, _pin(path, raw)), 'pin digest drift: ' + path)
    return decode_json(raw.decode('utf-8'))


def _resale_checkpoint_sources(pins, read):
    expected = [{'path': path, 'sha256': digest} for path, digest in RESALE_SOURCE_PINS]
    _check(_same(pins, expected), 'resale checkpoint source pins')
    raw_sources = {}
    for path, digest in RESALE_SOURCE_PINS:
        raw = read(path)
        _check(hashlib.sha256(raw).hexdigest() == digest, 'resale checkpoint source digest drift: ' + path)
        raw_sources[path] = raw
    return {path: decode_json(raw.decode('utf-8')) for path, raw in raw_sources.items()}


def _resolve(documents, ref):
    """Strict repository-file#JSON-pointer lookup, including RFC 6901 escapes."""
    _check(type(ref) is str and ref.count('#') == 1, 'reference syntax')
    path, pointer = ref.split('#')
    _check(path in documents and pointer.startswith('/'), 'reference document/pointer')
    node = documents[path]
    try:
        for token in pointer[1:].split('/'):
            _check(re.search(r'~(?![01])', token) is None, 'reference escape')
            token = token.replace('~1', '/').replace('~0', '~')
            if type(node) is list:
                _check(re.fullmatch(r'0|[1-9][0-9]*', token) is not None, 'reference array index')
                node = node[int(token)]
            else:
                _check(type(node) is dict, 'reference container')
                node = node[token]
        return node
    except (KeyError, IndexError, ValueError, TypeError) as error:
        raise AssertionError('unresolvable reference: ' + ref) from error


def _symbol_check(value, path, symbol, read):
    _check(_same(value, {'path': path, 'symbol': symbol}), 'replay location')
    class_name, method = symbol.split('.')
    tree = ast.parse(read(path), filename=path)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name]
    _check(len(classes) == 1 and sum(isinstance(n, ast.FunctionDef) and n.name == method
                                    for n in classes[0].body) == 1, 'replay symbol absent')


def _guide_check(refs, expected, read):
    _check(_same(refs, expected), 'guide association')
    for ref in refs:
        headings = [line.lstrip('#').strip() for line in read(ref['path']).decode('utf-8').splitlines()
                    if re.match(r'^#{1,6} ', line)]
        _check(ref['heading'] in headings, 'guide heading absent')


def _expected_associations(spec, source, output):
    """Derive navigation from original shapes, never from index-supplied references."""
    family, shape, input_name, output_name, *_rest, ids, counts = spec
    ipath, opath = FIXTURES + input_name, FIXTURES + output_name
    entries, observations = [], []
    if shape in SELF_CONTAINED_SHAPES:
        _check(tuple(c['case_id'] for c in source['cases']) == ids, 'case membership/order')
        for i, case in enumerate(source['cases']):
            prefix = ipath + '#/cases/' + str(i)
            entry = {'case_id': case['case_id'], 'input_ref': prefix}
            if shape == 'self_contained_refusals':
                entry.update(observer=case['observer'], arguments_ref=prefix + '/arguments',
                             keywords_ref=prefix + '/keywords', result_ref=prefix + '/expected_error')
            else:
                entry['result_ref'] = prefix + '/expected_result'
            if family == 'capital_commerce_refund_checkpoints':
                step = (9, 14, 15)[i]
                ref = f'{COMMERCE_RECEIPTS}#/cases/0/steps/{step}/receipt'
                _check(case['receipt_ref'] == ref, 'checkpoint receipt association: ' + case['case_id'])
                entry['receipt_ref'] = ref
            if family == 'capital_resale_distribution_checkpoints':
                step = (23, 24, 25)[i]
                ref = f'{RESALE_JOURNEY_RECEIPTS}#/steps/{step}/receipt'
                _check(case['receipt_ref'] == ref, 'checkpoint receipt association: ' + case['case_id'])
                entry['receipt_ref'] = ref
            entries.append(entry)
        if family == 'capital_group_sum_boundary':
            views = source['credit_views']
            _check(type(views) is list and len(views) == 2, 'source credit-view membership')
            refs = [f'{ipath}#/credit_views/{i}' for i in range(len(views))]
            for case, expected_refs in zip(source['cases'], (refs, refs, refs[:1]), strict=True):
                _check(_same(case['view_refs'], expected_refs), 'group sum case view association: ' + case['case_id'])
            observations = [{'kind': 'source_credit_view', 'ref': ref} for ref in refs]
        return entries, observations
    _check(tuple(s['scenario_id'] for s in source['scenarios']) == ids, 'scenario membership/order')
    _check(tuple(s['scenario_id'] for s in output['scenarios']) == ids, 'output scenario membership/order')
    for i, (scenario, result_scenario) in enumerate(zip(source['scenarios'], output['scenarios'])):
        prefix = '/scenarios/' + str(i)
        sid = scenario['scenario_id']
        if shape == 'scenario_inputs':
            inputs = scenario['inputs']
            # Mirror only the existing recipe's identities, never its economic calculations.
            step_ids = ['create', 'capture_confirm', 'settle']
            step_ids += [a['advance_id'] + ':' + op for a in inputs['advances']
                         for op in ('offer', 'approve', 'bind', 'draw')]
            step_ids += ['frozen']
            step_ids += [s for action in inputs['history'] for s in (action, 'after_' + action)]
            _check([s['step_id'] for s in result_scenario['steps']] == step_ids,
                   'economics recipe/order')
            for j, step_id in enumerate(step_ids):
                entries.append({'scenario_id': sid, 'section': 'steps', 'step_id': step_id,
                                'input_granularity': 'scenario', 'input_ref': ipath + '#' + prefix + '/inputs',
                                'result_ref': opath + '#' + prefix + '/steps/' + str(j) + '/result'})
            continue
        _check((len(scenario.get('setup_steps', [])), len(scenario['steps'])) == counts[i],
               'source section membership')
        sections = [('steps', 'steps')] if shape == 'ordered_steps' else [
            ('setup_steps', 'setup_results'), ('steps', 'history')]
        for section, result_section in sections:
            steps, results = scenario[section], result_scenario[result_section]
            step_ids = [s['step_id'] for s in steps]
            _check(len(step_ids) == len(set(step_ids)), 'duplicate source step')
            _check([s['step_id'] for s in results] == step_ids, 'output step identity/order')
            for j, (step, result) in enumerate(zip(steps, results)):
                entry = {'scenario_id': sid, 'section': section, 'step_id': step['step_id'],
                         'input_ref': ipath + '#' + prefix + '/' + section + '/' + str(j),
                         'result_ref': opath + '#' + prefix + '/' + result_section + '/' + str(j) + '/result'}
                for key in ('operation', 'target'):
                    if key in step:
                        entry[key] = step[key]
                    # Operation/target absent from some original history result shapes.
                    if key in result:
                        _check(result[key] == step.get(key), 'output ' + key + ' association')
                entries.append(entry)
                if 'snapshot' in result:
                    observations.append({'scenario_id': sid, 'kind': 'step_snapshot', 'step_id': step['step_id'],
                                         'ref': opath + '#' + prefix + '/' + result_section + '/' + str(j) + '/snapshot'})
        if shape == 'setup_and_history':
            observations.append({'scenario_id': sid, 'kind': 'initial_snapshot',
                                 'ref': opath + '#' + prefix + '/initial_snapshot'})
            if 'restore_checks' in result_scenario:
                observations.append({'scenario_id': sid, 'kind': 'restore_checks',
                                     'ref': opath + '#' + prefix + '/restore_checks'})
    return entries, observations


def validate_index(document, read=_read):
    """Validate associations without executing consumers or re-running economic models."""
    _fields(document, 'record_schema_version record_kind normative consumer qualification nonClaims packs supporting_evidence', 'record')
    _check(document['record_schema_version'] == 'kix-capital-companion-evidence-index/1', 'record version')
    _check(document['record_kind'] == 'NON_NORMATIVE_COMPANION_EVIDENCE_INDEX', 'record kind')
    _check(document['normative'] is False and document['consumer'] == 'kix-capital', 'normative/consumer claim')
    _check(_same(document['qualification'], QUALIFICATION), 'qualification claim/type')
    _check(_same(document['nonClaims'], NON_CLAIMS), 'nonClaims claim/type')
    packs = document['packs']
    _check(type(packs) is list and [p.get('id') for p in packs] == [s[0] for s in PACKS], 'pack membership/order')
    total = 0
    for pack, spec in zip(packs, PACKS):
        family, shape, input_name, output_name, test, symbol, heading, _ids, _counts = spec
        _fields(pack, 'id shape input output replay_test guide_refs limitations entries observations', 'pack')
        _check(pack['shape'] == shape, 'pack shape')
        _check(_same(pack['limitations'], LIMITATIONS[family]), 'pack limitations claim/type')
        source = _pin_check(pack['input'], FIXTURES + input_name, read)
        output = _pin_check(pack['output'], FIXTURES + output_name, read)
        if shape in SELF_CONTAINED_SHAPES:
            _check(_same(pack['input'], pack['output']), 'self-contained artifact association')
        else:
            _check(output['fixture_sha256'] == pack['input']['sha256'], 'output fixture association')
        _symbol_check(pack['replay_test'], BASE + test, symbol, read)
        _guide_check(pack['guide_refs'], [{'path': GUIDE, 'heading': heading}], read)
        expected, observations = _expected_associations(spec, source, output)
        _check(_same(pack['entries'], expected), 'entry membership/association/order/type: ' + family)
        _check(_same(pack['observations'], observations), 'supplemental observation association')
        documents = {pack['input']['path']: source, pack['output']['path']: output}
        if family == 'capital_commerce_refund_checkpoints':
            pin = {'path': COMMERCE_RECEIPTS, 'sha256': COMMERCE_RECEIPTS_SHA256}
            _check(_same(source['source_pins'], [pin]), 'Commerce receipt source pin')
            raw = read(COMMERCE_RECEIPTS)
            _check(hashlib.sha256(raw).hexdigest() == pin['sha256'], 'Commerce receipt digest drift')
            documents[COMMERCE_RECEIPTS] = decode_json(raw.decode('utf-8'))
        if family == 'capital_resale_distribution_checkpoints':
            documents.update(_resale_checkpoint_sources(source['source_pins'], read))
        for entry in pack['entries']:
            for key, ref in entry.items():
                if key.endswith('_ref'):
                    _resolve(documents, ref)
            if shape != 'self_contained_refusals':
                result = _resolve(documents, entry['result_ref'])
                _check(type(result) is dict and set(result) in ({'ok'}, {'error'}), 'complete result envelope')
        for observation in observations:
            _resolve(documents, observation['ref'])
        total += len(expected)
    supporting = document['supporting_evidence']
    _check(type(supporting) is list and [e.get('id') for e in supporting] == [s[0] for s in SUPPORTING],
           'supporting membership/order')
    for item, (family, cls, heading) in zip(supporting, SUPPORTING):
        _fields(item, 'id artifact replay_test contract_refs guide_refs entries', 'supporting')
        path = FIXTURES + family + '_v1.json'
        source = _pin_check(item['artifact'], path, read)
        _symbol_check(item['replay_test'], BASE + 'test_' + family + '_contract.py',
                      cls + '.test_all_scenarios_replay_to_expected', read)
        _guide_check(item['contract_refs'], [{'path': CONTRACT, 'heading': heading}], read)
        _guide_check(item['guide_refs'], [{'path': GUIDE, 'heading': 'Owners and limitations'}], read)
        ids = ('V1_face_snapshot_zero', 'V2_distribution_after_snapshot_negative', 'V3_refund_not_reflected_not_bound',
               'V4_positive_observation_sign', 'V5_exact_tolerance_boundary_within', 'V6_boundary_plus_one_out_of_tolerance') if family == 'settlement_variance' else (
                   'E1_two_advances_one_claim_exact_limit', 'E2_two_claims_one_debtor_label_over_limit',
                   'E3_pool_three_claims_default_still_aggregates', 'E4_refund_after_freeze_face_unchanged',
                   'E5_exact_limit_boundary_within', 'E6_repay_then_close_reservation_released')
        _check(tuple(s['id'] for s in source['scenarios']) == ids, 'supporting scenario membership/order')
        expected = [{'scenario_id': sid, 'input_ref': path + '#/scenarios/' + str(i),
                     'result_ref': path + '#/scenarios/' + str(i) + '/expected'} for i, sid in enumerate(ids)]
        _check(_same(item['entries'], expected), 'supporting entry association')
        for entry in expected:
            _resolve({path: source}, entry['input_ref'])
            _resolve({path: source}, entry['result_ref'])
    return total


class CapitalCompanionEvidenceIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = decode_json(_read(INDEX).decode('utf-8'))

    def _reject(self, mutate, diagnostic, read=_read):
        document = copy.deepcopy(self.document)
        mutate(document)
        with self.assertRaisesRegex(AssertionError, diagnostic):
            validate_index(document, read)

    def _detached(self, pack_index, side, mutate, diagnostic):
        """Rehash altered detached JSON so a digest failure cannot mask the association check."""
        document = copy.deepcopy(self.document)
        pack = document['packs'][pack_index]
        path = pack[side]['path']
        source = decode_json(_read(path).decode('utf-8'))
        mutate(source)
        raw = canonical(source)
        for pin_side in ('input', 'output'):
            if pack[pin_side]['path'] == path:
                pack[pin_side] = _pin(path, raw)
        with self.assertRaisesRegex(AssertionError, diagnostic):
            validate_index(document, lambda p: raw if p == path else _read(p))

    def test_complete_index(self):
        self.assertEqual(validate_index(self.document), 480)
        self.assertEqual(len(self.document['packs']), 21)
        self.assertEqual([len(p['entries']) for p in self.document['packs']],
                         [98, 54, 51, 53, 63, 27, 33, 24, 15, 20, 13, 4, 4, 2, 2, 3, 4, 3, 3, 2, 2])
        self.assertEqual(sum(len(p['observations']) for p in self.document['packs']), 130)
        self.assertEqual(sum(len(p['entries']) for p in self.document['supporting_evidence']), 12)

    def test_membership_controls(self):
        for mutate in (
            lambda d: d['packs'].pop(),
            lambda d: d['packs'].append(copy.deepcopy(d['packs'][0])),
            lambda d: d['packs'].reverse(),
            lambda d: d['packs'].__setitem__(1, copy.deepcopy(d['packs'][0])),
        ):
            self._reject(mutate, 'pack membership')
        # Every family: missing, duplicate and reordered entries. Later families
        # separately exercise setup and history; whole scenarios/cases are removed too.
        for i, original in enumerate(self.document['packs']):
            positions = [0]
            if original['shape'] == 'setup_and_history':
                positions.append(next(j for j, e in enumerate(original['entries']) if e['section'] == 'steps'))
            for position in positions:
                for action in ('remove', 'duplicate', 'reorder'):
                    with self.subTest(pack=original['id'], position=position, action=action):
                        def mutate(d):
                            entries = d['packs'][i]['entries']
                            if action == 'remove':
                                entries.pop(position)
                            elif action == 'duplicate':
                                entries.insert(position, copy.deepcopy(entries[position]))
                            else:
                                entries[position], entries[position + 1] = entries[position + 1], entries[position]
                        self._reject(mutate, 'entry membership')
            if original['shape'] not in SELF_CONTAINED_SHAPES:
                def remove_scenario(d):
                    entries = d['packs'][i]['entries']
                    sid = entries[0]['scenario_id']
                    d['packs'][i]['entries'] = [e for e in entries if e['scenario_id'] != sid]
                self._reject(remove_scenario, 'entry membership')
        for i in range(2):
            self._reject(lambda d: d['supporting_evidence'][i]['entries'].pop(), 'supporting entry')
        self._reject(lambda d: d['supporting_evidence'].pop(), 'supporting membership')
        self._reject(lambda d: d['supporting_evidence'].append(copy.deepcopy(d['supporting_evidence'][0])),
                     'supporting membership')

    def test_association_controls(self):
        # Two valid pointers, same operation, different scenarios: resolvability
        # and the operation name alone cannot establish the correct association.
        entries = self.document['packs'][0]['entries']
        first = entries[0]
        other = next(e for e in entries if e['scenario_id'] != first['scenario_id']
                     and e['operation'] == first['operation'])
        docs = {p['path']: decode_json(_read(p['path']).decode())
                for p in (self.document['packs'][0]['input'], self.document['packs'][0]['output'])}
        self.assertIsInstance(_resolve(docs, other['result_ref']), dict)
        self._reject(lambda d: d['packs'][0]['entries'][0].__setitem__('result_ref', other['result_ref']),
                     'entry membership/association')
        self._reject(lambda d: d['packs'][0]['entries'][0].__setitem__('input_ref', other['input_ref']),
                     'entry membership/association')
        self._reject(lambda d: d['packs'][0].__setitem__('output', copy.deepcopy(d['packs'][3]['output'])),
                     'pin path association')
        self._reject(lambda d: d['packs'][1]['entries'][0].__setitem__('input_granularity', 'step'),
                     'entry membership')
        self._reject(lambda d: d['packs'][2]['entries'][0].__setitem__(
            'arguments_ref', d['packs'][2]['entries'][1]['arguments_ref']), 'entry membership')
        histories = [i for i, spec in enumerate(PACKS) if spec[1] == 'setup_and_history']
        for i in histories:
            self._reject(lambda d: d['packs'][i]['observations'].pop(), 'supplemental observation')
            self._reject(lambda d: d['packs'][i]['entries'][0].__setitem__('section', 'steps'), 'entry membership')
        self._reject(lambda d: d['supporting_evidence'][0]['entries'][0].__setitem__(
            'result_ref', d['supporting_evidence'][0]['entries'][1]['result_ref']), 'supporting entry')
        # Detached output bytes have matching fresh SHA-256 and Git blob pins.
        # Identity/order must still fail independently of those hashes.
        self._detached(0, 'output', lambda d: d['scenarios'].reverse(), 'output scenario membership')
        self._detached(0, 'output', lambda d: d['scenarios'][0]['steps'].reverse(), 'output step identity')
        self._detached(0, 'output', lambda d: d['scenarios'][0]['steps'][0].__setitem__('operation', 'capture'),
                       'output operation association')
        self._detached(0, 'output', lambda d: d['scenarios'][0]['steps'][0].__setitem__('target', 'credit'),
                       'output target association')
        self._detached(0, 'output', lambda d: d['scenarios'][0]['steps'][0].__setitem__('result', {'ok': {}, 'error': {}}),
                       'complete result envelope')
        self._detached(1, 'output', lambda d: d['scenarios'][2]['steps'].reverse(), 'economics recipe/order')
        for i in histories:
            self._detached(i, 'output', lambda d: d['scenarios'][0]['setup_results'].pop(), 'output step identity')
            self._detached(i, 'output', lambda d: d['scenarios'][0]['history'].reverse(), 'output step identity')
        # Refusal file is genuinely self-contained: update both pins, then require
        # exact case identity, rather than accepting rehashed missing/duplicate cases.
        for change in ('remove', 'duplicate', 'reorder'):
            d = copy.deepcopy(self.document)
            path = d['packs'][2]['input']['path']
            source = decode_json(_read(path).decode())
            if change == 'remove':
                source['cases'].pop()
            elif change == 'duplicate':
                source['cases'].append(copy.deepcopy(source['cases'][0]))
            else:
                source['cases'].reverse()
            raw = canonical(source)
            d['packs'][2]['input'] = d['packs'][2]['output'] = _pin(path, raw)
            with self.assertRaisesRegex(AssertionError, 'case membership'):
                validate_index(d, lambda p: raw if p == path else _read(p))

    def test_refund_identity_crossed_references(self):
        # These acceptance rows share an operation, source, amount and settlement.
        # Swapping valid pointers must still break their command/receipt association.
        def swap(document, field):
            pack = next(p for p in document['packs'] if p['id'] == 'capital_refund_identity')
            rows = {entry['step_id']: entry for entry in pack['entries']}
            fresh, replay = rows['fresh-acceptance'], rows['replay-acceptance']
            fresh[field], replay[field] = replay[field], fresh[field]

        for field in ('input_ref', 'result_ref'):
            with self.subTest(field=field):
                self._reject(lambda d: swap(d, field), 'entry membership/association')

    def test_commerce_refund_checkpoints_crossed_references(self):
        index = next(i for i, pack in enumerate(self.document['packs'])
                     if pack['id'] == 'capital_commerce_refund_checkpoints')

        def swap(rows, field):
            bind, acceptance = rows[1:]
            bind[field], acceptance[field] = acceptance[field], bind[field]

        for field in ('input_ref', 'result_ref', 'receipt_ref'):
            with self.subTest(field=field):
                self._reject(lambda d: swap(d['packs'][index]['entries'], field),
                             'entry membership/association/order/type: capital_commerce_refund_checkpoints')
        self._detached(index, 'input', lambda d: swap(d['cases'], 'receipt_ref'),
                       'checkpoint receipt association: bind-refund')
        with self.assertRaisesRegex(AssertionError, 'Commerce receipt digest drift'):
            validate_index(self.document, lambda p: _read(p) + b'\n' if p == COMMERCE_RECEIPTS else _read(p))

    def test_resale_distribution_crossed_receipt_references(self):
        family = 'capital_resale_distribution_checkpoints'
        index = next(i for i, pack in enumerate(self.document['packs']) if pack['id'] == family)

        def swap(rows):
            commit, _, distribution = rows
            commit['receipt_ref'], distribution['receipt_ref'] = distribution['receipt_ref'], commit['receipt_ref']

        self._reject(lambda d: swap(d['packs'][index]['entries']),
                     'entry membership/association/order/type: ' + family)
        self._detached(index, 'input', lambda d: swap(d['cases']),
                       'checkpoint receipt association: settle-resale-commit')

    def test_mixed_checkpoint_crossed_references(self):
        index = next(i for i, pack in enumerate(self.document['packs'])
                     if pack['id'] == 'capital_mixed_checkpoint_views')

        def swap(document, case_id, field):
            entries = {entry['case_id']: entry for entry in document['packs'][index]['entries']}
            mixed, same = entries[case_id + '_mixed'], entries[case_id + '_same']
            mixed[field], same[field] = same[field], mixed[field]

        for case_id in ('repay', 'close'):
            for field in ('input_ref', 'result_ref'):
                with self.subTest(case=case_id, field=field):
                    self._reject(lambda d: swap(d, case_id, field), 'entry membership/association')
        self._detached(index, 'input', lambda d: d['cases'].reverse(), 'case membership/order')
        self._detached(index, 'input', lambda d: d['cases'][0].__setitem__('expected_result', {}),
                       'complete result envelope')

    def test_omitted_exposure_members_crossed_references(self):
        def swap(document, prefix, field):
            pack = next(p for p in document['packs'] if p['id'] == 'capital_omitted_exposure_members')
            entries = {entry['case_id']: entry for entry in pack['entries']}
            full, subset = entries[prefix + '_full'], entries[prefix + '_omit_second']
            full[field], subset[field] = subset[field], full[field]

        for prefix in ('e1', 'e2'):
            for field in ('input_ref', 'result_ref'):
                with self.subTest(pair=prefix, field=field):
                    self._reject(lambda d: swap(d, prefix, field),
                                 'entry membership/association/order/type: capital_omitted_exposure_members')

    def test_overlapping_exposure_groups_crossed_references(self):
        family = 'capital_overlapping_exposure_groups'

        def swap(document, field):
            pack = next(p for p in document['packs'] if p['id'] == family)
            ab, bc = pack['entries'][:2]
            ab[field], bc[field] = bc[field], ab[field]

        for field in ('input_ref', 'result_ref'):
            with self.subTest(field=field):
                self._reject(lambda d: swap(d, field), f'entry membership/association/order/type: {family}')

    def test_reconcile_freshness_crossed_references(self):
        def swap(document, target, collection, field):
            pack = next(p for p in document['packs'] if p['id'] == 'capital_reconcile_freshness')
            rows = {row.get('step_id'): row for row in pack[collection]}
            replayed, fresh = rows[target + '-replay'], rows[target + '-fresh']
            replayed[field], fresh[field] = fresh[field], replayed[field]

        for target in ('settlement', 'credit'):
            for collection, field, diagnostic in (
                ('entries', 'input_ref', 'entry membership/association'),
                ('entries', 'result_ref', 'entry membership/association'),
                ('observations', 'ref', 'supplemental observation association'),
            ):
                with self.subTest(target=target, field=field):
                    self._reject(lambda d: swap(d, target, collection, field), diagnostic)

    def test_predraw_terminal_crossed_references(self):
        def swap(document, step_id, collection, field):
            pack = next(p for p in document['packs'] if p['id'] == 'capital_predraw_terminal')
            rows = {row.get('step_id'): row for row in pack[collection]}
            original, replay = rows[step_id], rows['replay-' + step_id]
            original[field], replay[field] = replay[field], original[field]

        for step_id in ('reject-a', 'cancel-b'):
            for collection, field, diagnostic in (
                ('entries', 'input_ref', 'entry membership/association'),
                ('entries', 'result_ref', 'entry membership/association'),
                ('observations', 'ref', 'supplemental observation association'),
            ):
                with self.subTest(step_id=step_id, field=field):
                    self._reject(lambda d: swap(d, step_id, collection, field), diagnostic)

    def test_later_statement_crossed_references(self):
        # Both snapshots and both call argument sets are equal. Position still
        # distinguishes the first accepted observation from its replay.
        def swap(document, collection, field):
            pack = next(p for p in document['packs'] if p['id'] == 'capital_later_statement')
            rows = {row.get('step_id'): row for row in pack[collection]}
            first, replayed = rows['statement-later'], rows['statement-replay']
            first[field], replayed[field] = replayed[field], first[field]

        for collection, field, diagnostic in (
            ('entries', 'input_ref', 'entry membership/association'),
            ('entries', 'result_ref', 'entry membership/association'),
            ('observations', 'ref', 'supplemental observation association'),
        ):
            with self.subTest(field=field):
                self._reject(lambda d: swap(d, collection, field), diagnostic)

    def test_payee_order_crossed_result_references(self):
        def swap_results(document):
            pack = next(p for p in document['packs'] if p['id'] == 'capital_payee_order_recovery')
            fee_first, residual_first = pack['entries']
            fee_first['result_ref'], residual_first['result_ref'] = (
                residual_first['result_ref'], fee_first['result_ref'])

        self._reject(swap_results, 'entry membership/association/order/type: capital_payee_order_recovery')

    def test_offsetting_claim_gaps_crossed_result_references(self):
        family = 'capital_offsetting_claim_gaps'

        def swap_results(document):
            pack = next(p for p in document['packs'] if p['id'] == family)
            path = pack['output']['path']
            documents = {path: decode_json(_read(path).decode('utf-8'))}
            v4, v6 = pack['entries']
            v4['result_ref'], v6['result_ref'] = v6['result_ref'], v4['result_ref']
            self.assertEqual(_resolve(documents, v4['result_ref'])['ok']['claim_id'], 'claim-v2')
            self.assertEqual(_resolve(documents, v6['result_ref'])['ok']['claim_id'], 'claim-v4')

        self._reject(swap_results, 'entry membership/association/order/type: ' + family)

    def test_group_sum_boundary_crossed_references(self):
        family = 'capital_group_sum_boundary'
        i = next(i for i, pack in enumerate(self.document['packs']) if pack['id'] == family)
        path = self.document['packs'][i]['input']['path']
        documents = {path: decode_json(_read(path).decode('utf-8'))}

        def swap_refs(document, section, key):
            first, second = document['packs'][i][section][:2]
            first[key], second[key] = second[key], first[key]
            return _resolve(documents, first[key]), _resolve(documents, second[key])

        def swap_results(document):
            first, second = swap_refs(document, 'entries', 'result_ref')
            self.assertIs(first['ok']['within_limit'], False)
            self.assertIs(second['ok']['within_limit'], True)

        def swap_observations(document):
            first, second = swap_refs(document, 'observations', 'ref')
            self.assertEqual([first['amount'], second['amount']], [1, 1_000_000_000_000])

        self._reject(swap_results, 'entry membership/association/order/type: ' + family)
        self._reject(swap_observations, 'supplemental observation association')
        self._detached(i, 'input', lambda pack: pack['cases'][0]['view_refs'].reverse(),
                       'group sum case view association: at_total')

    def test_draw_refusal_after_restore_crossed_result_references(self):
        family = 'capital_draw_refusal_after_restore'

        def swap_results(document):
            pack = next(p for p in document['packs'] if p['id'] == family)
            path = pack['output']['path']
            documents = {path: decode_json(_read(path).decode('utf-8'))}
            original, restored = pack['entries']
            original['result_ref'], restored['result_ref'] = restored['result_ref'], original['result_ref']
            self.assertEqual(_resolve(documents, original['result_ref'])['ok']['applied'], 'draw')
            self.assertEqual(_resolve(documents, restored['result_ref'])['error']['code'],
                             'SETTLEMENT_NOT_COMMITTED')

        self._reject(swap_results, 'entry membership/association/order/type: ' + family)

    def test_equal_gross_claim_binding_crossed_result_references(self):
        family = 'capital_equal_gross_claim_binding'

        def swap_results(document):
            pack = next(p for p in document['packs'] if p['id'] == family)
            path = pack['output']['path']
            documents = {path: decode_json(_read(path).decode('utf-8'))}
            matching, crossed = pack['entries']
            matching['result_ref'], crossed['result_ref'] = crossed['result_ref'], matching['result_ref']
            self.assertEqual(_resolve(documents, matching['result_ref'])['error']['code'],
                             'SETTLEMENT_BINDING_CONFLICT')
            self.assertEqual(_resolve(documents, crossed['result_ref'])['ok']['applied'], 'draw')

        self._reject(swap_results, 'entry membership/association/order/type: ' + family)

    def test_pin_controls(self):
        for i in range(len(PACKS)):
            for side in ('input', 'output'):
                for field in ('sha256', 'gitBlob'):
                    with self.subTest(pack=i, side=side, field=field):
                        self._reject(lambda d: d['packs'][i][side].__setitem__(field, '0' * (64 if field == 'sha256' else 40)),
                                     'pin digest drift')
                path = self.document['packs'][i][side]['path']
                with self.assertRaisesRegex(AssertionError, 'pin digest drift'):
                    validate_index(self.document, lambda p: _read(p) + b' ' if p == path else _read(p))
        for i in range(2):
            self._reject(lambda d: d['supporting_evidence'][i]['artifact'].__setitem__('gitBlob', '0' * 40),
                         'pin digest drift')
        self._detached(0, 'output', lambda d: d.__setitem__('fixture_sha256', '0' * 64), 'output fixture association')
        self._reject(lambda d: d['packs'][0]['input'].__setitem__('extra', None), 'pin requires')

    def test_reference_controls(self):
        for pack in self.document['packs'] + self.document['supporting_evidence']:
            path, symbol = pack['replay_test']['path'], pack['replay_test']['symbol']
            for name in symbol.split('.'):
                raw = _read(path).replace(name.encode(), (name + '_removed').encode())
                with self.subTest(path=path, name=name):
                    with self.assertRaisesRegex(AssertionError, 'replay symbol absent'):
                        validate_index(self.document, lambda p: raw if p == path else _read(p))
        self._reject(lambda d: d['packs'][0]['replay_test'].__setitem__('symbol', 'Other.test_missing'), 'replay location')
        self._reject(lambda d: d['packs'][0]['guide_refs'][0].__setitem__('heading', 'invented'), 'guide association')
        for path in (GUIDE, CONTRACT):
            with self.assertRaisesRegex(AssertionError, 'guide heading absent'):
                validate_index(self.document, lambda p: b'# no cited headings\n' if p == path else _read(p))

    def test_qualification_controls(self):
        for key, value in (
            ('externalConsumerAcceptance', 'VERIFIED'), ('evidenceClass', 'A'),
            ('observationMapping', 'BOUND'), ('repair', 'AUTOMATIC'),
            ('refundComponent', 'BOUND'), ('authorizesExposure', True),
            ('authorizesExposure', 0), ('mutatesState', True), ('failClosed', 1),
            ('productLimits', {'status': 'DETERMINED', 'owner': 'Astra'}),
            ('legalResponsibility', {'status': 'UNDETERMINED', 'owner': 'Astra'}),
        ):
            with self.subTest(key=key, value=value):
                self._reject(lambda d: d['qualification'].__setitem__(key, value), 'qualification claim/type')
        for key in QUALIFICATION:
            self._reject(lambda d: d['qualification'].pop(key), 'qualification claim/type')
        for i in range(len(NON_CLAIMS)):
            self._reject(lambda d: d['nonClaims'].pop(i), 'nonClaims')
        for i in range(len(PACKS)):
            self._reject(lambda d: d['packs'][i]['limitations'].clear(), 'limitations')
        self._reject(lambda d: d.__setitem__('normative', 0), 'normative/consumer')
        self._reject(lambda d: d.__setitem__('extra', True), 'record requires')

    def test_json_and_pointer_controls(self):
        for raw in ('{"packs": [], "packs": []}', '{"x": NaN}', '{"x": Infinity}'):
            with self.assertRaises(FixtureError):
                decode_json(raw)
        docs = {'p.json': {'a/b': {'~name': [None, False, 1.0]}}}
        self.assertIsNone(_resolve(docs, 'p.json#/a~1b/~0name/0'))
        self.assertIs(_resolve(docs, 'p.json#/a~1b/~0name/1'), False)
        self.assertIs(type(_resolve(docs, 'p.json#/a~1b/~0name/2')), float)
        for ref in ('p.json', 'p.json#', 'p.json#/a~2b', 'p.json#/a~1b/~0name/-1',
                    'p.json#/a~1b/~0name/01', 'p.json#/a~1b/~0name/3',
                    'p.json#/a~1b/~0name/-', 'p.json#/missing', '../p.json#/a', 'p.json#/a#b'):
            with self.subTest(ref=ref):
                with self.assertRaises(AssertionError):
                    _resolve(docs, ref)
        # Omission, null, booleans and floating values survive strict decoding.
        refusal = decode_json(_read(self.document['packs'][2]['input']['path']).decode())
        cases = {c['case_id']: c for c in refusal['cases']}
        self.assertEqual(cases['V01_tolerance_omitted']['keywords'], {})
        self.assertIsNone(cases['V08_tolerance_null']['keywords']['tolerance'])
        self.assertIs(cases['V02_tolerance_true']['keywords']['tolerance'], True)
        self.assertIs(type(cases['V05_tolerance_integer_float']['keywords']['tolerance']), float)
