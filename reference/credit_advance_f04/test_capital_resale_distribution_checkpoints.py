"""Replay two settlement claims and one ownership receipt against frozen F04 credit."""

from copy import deepcopy
import unittest

from credit_fixture import decode_json, exact_fields
from credit_fsm import CreditMachine
from settlement_credit_boundary_vectors import canonical
from settlement_variance import observe_settlement_variance
from test_capital_companion_evidence_index import (
    FIXTURES, RESALE_JOURNEY_INPUT, RESALE_JOURNEY_RECEIPTS, RESALE_SDK_VECTORS,
    _read, _resale_checkpoint_sources, _resolve,
)


PACK = FIXTURES + 'capital_resale_distribution_checkpoints_vectors_v1.json'
CLAIM_ID = 'settle-resale'
TRADE_ID = 'trade-resale-A'
CHECKPOINTS = (
    # Case ID, SDK vector index, journey step index, command action, receipt operation.
    ('settle-resale-commit', 19, 23, 'settlement_commit', 'commit'),
    ('accept-A', 20, 24, 'resale_accept_resale', 'accept_resale'),
    ('distribute-resale', 21, 25, 'settlement_distribute', 'distribute'),
)


class CapitalResaleDistributionCheckpointTests(unittest.TestCase):
    def setUp(self):
        raw = _read(PACK)
        self.pack = decode_json(raw.decode('utf-8'))
        self.assertEqual(canonical(self.pack), raw)
        exact_fields(self.pack, {'fixture_version', 'fixture_kind', 'synthetic_only',
                                 'contract', 'source_pins', 'advance', 'tolerance', 'cases'}, 'pack')
        self.assertEqual(self.pack['fixture_version'], 'capital-resale-distribution-checkpoints/1')
        self.assertEqual(self.pack['fixture_kind'], 'SYNTHETIC_RESALE_DISTRIBUTION_CHECKPOINTS')
        self.assertIs(self.pack['synthetic_only'], True)
        self.assertEqual(self.pack['contract'], 'docs/contracts/CREDIT_ADVANCE_F04.md#7.11')
        self.documents = _resale_checkpoint_sources(self.pack['source_pins'], _read)

    def _receipt_for(self, case, checkpoint):
        case_id, vector_index, step_index, action, applied = checkpoint
        exact_fields(case, {'case_id', 'receipt_ref', 'expected_result'}, case_id)
        self.assertEqual(case['case_id'], case_id, 'checkpoint ID/order')
        step_ref = f'{RESALE_JOURNEY_RECEIPTS}#/steps/{step_index}'
        receipt_ref = step_ref + '/receipt'
        self.assertEqual(case['receipt_ref'], receipt_ref, f'{case_id} checkpoint receipt association')

        vector = _resolve(self.documents, f'{RESALE_SDK_VECTORS}#/vectors/{vector_index}')
        self.assertEqual(vector['id'], f'booking-resale/{case_id}')
        self.assertEqual((vector['context'], vector['commerce_step']), ('booking-resale', case_id))
        self.assertEqual(vector['input_index'], step_index)
        self.assertEqual(vector['envelope']['action'], action)
        self.assertEqual((vector['expected']['kind'], vector['expected']['receipt_ref']), ('accept', receipt_ref))

        step = _resolve(self.documents, step_ref)
        self.assertEqual((step['id'], step['action']), (case_id, action))
        input_step_ref = f'{RESALE_JOURNEY_INPUT}#/steps/{step_index}'
        input_step = _resolve(self.documents, input_step_ref)
        self.assertEqual((input_step['id'], input_step['action']), (case_id, action))
        self.assertEqual(step['input_ref'], input_step_ref + '/body')
        self.assertEqual(canonical(vector['envelope']['body']),
                         canonical(_resolve(self.documents, step['input_ref'])))

        receipt = _resolve(self.documents, case['receipt_ref'])
        self.assertEqual(receipt['applied'], applied)
        self.assertIs(receipt['duplicate'], False)
        self.assertIs(receipt['funds_executed'], False)
        return receipt

    def _settlement_observation(self, receipt, frozen_claim, tolerance, outstanding, distributed_cash):
        settlement = receipt['settlement']
        self.assertEqual((settlement['settlement_id'], settlement['trade_id'], settlement['currency']),
                         (CLAIM_ID, TRADE_ID, 'KRW'))
        self.assertEqual(settlement['phase'], 'COMMITTED')
        claim = settlement['claim']
        self.assertEqual((claim['claim_id'], claim['trade_id'], claim['currency']), (CLAIM_ID, TRADE_ID, 'KRW'))
        self.assertEqual(claim['distributed_cash'], distributed_cash)
        obligations = [{key: row[key] for key in ('payee', 'outstanding')} for row in claim['obligations']]
        self.assertEqual([(row['payee'], row['outstanding']) for row in obligations],
                         list(zip(('organizer-1', 'platform-1'), outstanding, strict=True)))

        observation = observe_settlement_variance(claim, frozen_claim, tolerance=tolerance)
        self.assertEqual(observation['mapping'], {'code': 'SETTLEMENT_VARIANCE_NOT_BOUND',
                                                  'contract_status': 'NOT_BOUND', 'repair': 'NONE'})
        self.assertEqual(observation['refund_component'], 'NOT_BOUND')
        self.assertIs(observation['fail_closed'], True)
        self.assertIs(observation['mutates_state'], False)
        self.assertIs(observation['authorizes_exposure'], False)
        return {'obligations': obligations, 'observation': observation}

    def _ownership_observation(self, receipt):
        listing, evidence, right = receipt['listing'], receipt['evidence'], receipt['right']
        self.assertIs(listing['ownership_transferred'], True)
        self.assertIs(type(right['version']), int)
        ownership = {'settlement_id': listing['settlement_id'], 'listing_id': listing['listing_id'],
                     'transfer_id': evidence['transfer_id'], 'right_id': right['right_id'],
                     'holder_role': right['holder_role'], 'version': right['version']}
        self.assertEqual(ownership, {'settlement_id': CLAIM_ID, 'listing_id': 'listing-A',
                                     'transfer_id': 'transfer-A-2', 'right_id': 'issue-A',
                                     'holder_role': 'buyer-B', 'version': 2})
        return ownership

    def _replay(self, pack):
        # Import after unittest discovery because Economics prepends reference directories.
        from test_economics_credit_consumer_vectors import _CapturedSettlementReader, _credit_snapshot

        self.assertIs(type(pack['tolerance']), int)
        self.assertEqual(pack['tolerance'], 0)
        self.assertIs(type(pack['cases']), list)
        self.assertEqual(len(pack['cases']), len(CHECKPOINTS))
        receipts = [self._receipt_for(case, spec) for case, spec in zip(pack['cases'], CHECKPOINTS, strict=True)]
        advance = pack['advance']
        exact_fields(advance, {'advance_id', 'draw_id', 'amount', 'beneficiary_role'}, 'advance')
        advance_id = advance['advance_id']
        committed = receipts[0]['settlement']
        face = committed['claim']
        committed_face_bytes = canonical(face)
        credit = CreditMachine(settlement_source=_CapturedSettlementReader({CLAIM_ID: committed}))
        credit.offer(advance_id, idempotency_key='resale-checkpoint-offer', face=face,
                     amount=advance['amount'], beneficiary_role=advance['beneficiary_role'])
        credit.approve(advance_id, idempotency_key='resale-checkpoint-approve')
        credit.bind_settlement(advance_id, idempotency_key='resale-checkpoint-bind', settlement_id=CLAIM_ID)
        credit.draw(advance_id, idempotency_key='resale-checkpoint-draw', draw_id=advance['draw_id'])

        frozen = _credit_snapshot(credit, [advance_id], CLAIM_ID)
        baseline = canonical(frozen)
        self.assertEqual([entry['op'] for entry in frozen['journal']], ['offer', 'approve', 'bind_settlement', 'draw'])
        self.assertEqual(canonical(frozen['journal'][0]['body']['face']), committed_face_bytes)
        view, = frozen['views']
        self.assertEqual(view['phase'], 'DRAWN')
        self.assertIs(view['mock_settlement_commit_observed'], True)
        self.assertEqual((view['drawn_exposure'], view['outstanding_exposure'], view['repaid_exposure']),
                         (10000, 10000, 0))
        self.assertEqual(view['repayments'], [])
        self.assertIs(view['repayment_observed'], False)
        frozen_claim = frozen['claim']
        self.assertIs(frozen_claim['snapshot_frozen'], True)
        self.assertEqual((frozen_claim['claim_id'], frozen_claim['trade_id'], frozen_claim['currency'],
                          frozen_claim['open_face']), (CLAIM_ID, TRADE_ID, 'KRW', 12000))

        for case, receipt in zip(pack['cases'], receipts, strict=True):
            with self.subTest(case=case['case_id']):
                if case['case_id'] == 'accept-A':
                    result = self._ownership_observation(receipt)
                else:
                    at_commit = case['case_id'] == 'settle-resale-commit'
                    result = self._settlement_observation(receipt, frozen_claim, pack['tolerance'],
                                                          (11880, 120) if at_commit else (0, 0),
                                                          0 if at_commit else 12000)
                    observation = result['observation']
                    self.assertEqual((observation['variance'], observation['sign']),
                                     (0, 'ZERO') if at_commit else (-12000, 'NEGATIVE'))
                    self.assertIs(observation['within_tolerance'], at_commit)
                self.assertEqual(canonical({'ok': result}), canonical(case['expected_result']))
                self.assertEqual(canonical(frozen), baseline)
                self.assertEqual(canonical(_credit_snapshot(credit, [advance_id], CLAIM_ID)), baseline)

    def test_checkpoint_replay(self):
        self._replay(self.pack)

    def test_crossed_receipt_pointer(self):
        pack = deepcopy(self.pack)
        commit, _, distribution = pack['cases']
        commit['receipt_ref'], distribution['receipt_ref'] = distribution['receipt_ref'], commit['receipt_ref']
        for case in (commit, distribution):
            claim = _resolve(self.documents, case['receipt_ref'])['settlement']['claim']
            self.assertEqual((claim['claim_id'], claim['trade_id']), (CLAIM_ID, TRADE_ID))
        with self.assertRaisesRegex(AssertionError, 'settle-resale-commit checkpoint receipt association'):
            self._replay(pack)
