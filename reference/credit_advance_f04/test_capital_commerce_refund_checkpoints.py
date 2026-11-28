"""Replay one frozen F04 face against three pinned Commerce receipts."""

from copy import deepcopy
from hashlib import sha256
import unittest

from credit_fixture import decode_json, exact_fields
from credit_fsm import CreditMachine
from settlement_credit_boundary_vectors import canonical
from settlement_variance import observe_settlement_variance
from test_capital_companion_evidence_index import (
    COMMERCE_RECEIPTS, COMMERCE_RECEIPTS_SHA256, FIXTURES, _read, _resolve,
)


PACK = FIXTURES + 'capital_commerce_refund_checkpoints_vectors_v1.json'
CLAIM_ID = 'claim-1'
TRADE_ID = 'trade-claim-1'
REFUND_FIELDS = (
    'refund_bearer_policy', 'refund_face', 'refund_accepted', 'refund_outstanding',
    'pg_adjustment_outstanding',
)
CHECKPOINTS = (
    # Case ID, source step index, applied operation, and expected refund fields.
    ('commit', 9, 'commit', ('NONE', 0, 0, 0, 0)),
    ('bind-refund', 14, 'bind_refund', ('REQUESTER', 4000, 0, 4000, 0)),
    ('observe-mock-acceptance', 15, 'observe_mock_cancel_acceptance',
     ('REQUESTER', 4000, 1500, 2500, 1500)),
)


class CapitalCommerceRefundCheckpointTests(unittest.TestCase):
    def setUp(self):
        raw = _read(PACK)
        self.pack = decode_json(raw.decode('utf-8'))
        self.assertEqual(canonical(self.pack), raw)
        exact_fields(self.pack, {'fixture_version', 'fixture_kind', 'synthetic_only',
                                 'contract', 'source_pins', 'advance', 'tolerance', 'cases'}, 'pack')
        self.assertEqual(self.pack['fixture_version'], 'capital-commerce-refund-checkpoints/1')
        self.assertEqual(self.pack['fixture_kind'], 'SYNTHETIC_COMMERCE_REFUND_CHECKPOINTS')
        self.assertIs(self.pack['synthetic_only'], True)
        self.assertEqual(self.pack['contract'], 'docs/contracts/CREDIT_ADVANCE_F04.md#7.11')
        self.assertEqual(self.pack['source_pins'],
                         [{'path': COMMERCE_RECEIPTS, 'sha256': COMMERCE_RECEIPTS_SHA256}])
        source_raw = _read(COMMERCE_RECEIPTS)
        self.assertEqual(sha256(source_raw).hexdigest(), COMMERCE_RECEIPTS_SHA256)
        source = decode_json(source_raw.decode('utf-8'))
        self.assertEqual(source['record_schema_version'], 'kix-commerce-linked-refund-receipts/1')
        self.assertEqual(source['cases'][0]['id'], 'linked-purchase-partial-refund')
        self.documents = {COMMERCE_RECEIPTS: source}

    def _settlement_for(self, case, checkpoint):
        case_id, index, operation, _refund = checkpoint
        exact_fields(case, {'case_id', 'receipt_ref', 'expected_result'}, case_id)
        self.assertEqual(case['case_id'], case_id, 'checkpoint ID/order')
        step_ref = f'{COMMERCE_RECEIPTS}#/cases/0/steps/{index}'
        self.assertEqual(case['receipt_ref'], step_ref + '/receipt',
                         f'{case_id} checkpoint receipt association')
        step = _resolve(self.documents, step_ref)
        self.assertEqual((step['id'], step['action']), (case_id, 'settlement_' + operation))
        receipt = _resolve(self.documents, case['receipt_ref'])
        self.assertEqual(receipt['applied'], operation)
        self.assertIs(receipt['duplicate'], False)
        self.assertIs(receipt['funds_executed'], False)
        settlement = receipt['settlement']
        claim = settlement['claim']
        self.assertEqual((settlement['settlement_id'], settlement['trade_id'], settlement['currency']),
                         (CLAIM_ID, TRADE_ID, 'KRW'))
        self.assertEqual((claim['claim_id'], claim['trade_id'], claim['currency']),
                         (CLAIM_ID, TRADE_ID, 'KRW'))
        self.assertEqual(settlement['phase'], 'COMMITTED')
        return settlement

    def _draw_credit(self, advance, settlement):
        # Economics prepends other reference directories to sys.path on import.
        # Load its test helpers after unittest has discovered the Capital suite.
        from test_economics_credit_consumer_vectors import _CapturedSettlementReader, _credit_snapshot

        exact_fields(advance, {'advance_id', 'draw_id', 'amount', 'beneficiary_role'}, 'advance')
        advance_id = advance['advance_id']
        face = settlement['claim']
        credit = CreditMachine(settlement_source=_CapturedSettlementReader({CLAIM_ID: settlement}))
        credit.offer(advance_id, idempotency_key='checkpoint-offer', face=face,
                     amount=advance['amount'], beneficiary_role=advance['beneficiary_role'])
        credit.approve(advance_id, idempotency_key='checkpoint-approve')
        credit.bind_settlement(advance_id, idempotency_key='checkpoint-bind', settlement_id=CLAIM_ID)
        credit.draw(advance_id, idempotency_key='checkpoint-draw', draw_id=advance['draw_id'])
        frozen = _credit_snapshot(credit, [advance_id], CLAIM_ID)
        self.assertEqual([entry['op'] for entry in frozen['journal']],
                         ['offer', 'approve', 'bind_settlement', 'draw'])
        self.assertEqual(canonical(frozen['journal'][0]['body']['face']), canonical(face))
        view, = frozen['views']
        self.assertEqual(view['phase'], 'DRAWN')
        self.assertIs(view['mock_settlement_commit_observed'], True)
        self.assertEqual((view['drawn_exposure'], view['outstanding_exposure'], view['repaid_exposure']),
                         (10000, 10000, 0))
        self.assertEqual(view['repayments'], [])
        self.assertIs(view['repayment_observed'], False)
        self.assertIs(frozen['claim']['snapshot_frozen'], True)
        self.assertEqual(frozen['claim']['open_face'], 10001)
        return credit, frozen

    def _replay(self, pack):
        from test_economics_credit_consumer_vectors import _credit_snapshot

        self.assertIs(type(pack['tolerance']), int)
        self.assertEqual(pack['tolerance'], 0)
        self.assertIs(type(pack['cases']), list)
        self.assertEqual(len(pack['cases']), len(CHECKPOINTS))
        settlements = [self._settlement_for(case, spec)
                       for case, spec in zip(pack['cases'], CHECKPOINTS, strict=True)]
        credit, frozen = self._draw_credit(pack['advance'], settlements[0])
        advance_id = pack['advance']['advance_id']
        baseline = canonical(frozen)
        for case, settlement, spec in zip(pack['cases'], settlements, CHECKPOINTS, strict=True):
            with self.subTest(case=case['case_id']):
                claim = settlement['claim']
                refund = {name: claim[name] for name in REFUND_FIELDS}
                self.assertEqual(canonical(refund), canonical(dict(zip(REFUND_FIELDS, spec[3], strict=True))))
                self.assertEqual(claim['refund_beneficiary'], 'buyer-1' if spec[3][0] == 'REQUESTER' else None)
                observation = observe_settlement_variance(claim, frozen['claim'], tolerance=pack['tolerance'])
                self.assertEqual(canonical({'ok': {**refund, 'observation': observation}}),
                                 canonical(case['expected_result']))
                self.assertEqual(observation['observable'],
                                 {'settlement_outstanding': 10001, 'credit_open_face': 10001})
                self.assertEqual((observation['variance'], observation['sign']), (0, 'ZERO'))
                self.assertIs(observation['within_tolerance'], True)
                self.assertEqual(observation['refund_component'], 'NOT_BOUND')
                self.assertEqual(observation['mapping'], {'code': 'SETTLEMENT_VARIANCE_NOT_BOUND',
                                                          'contract_status': 'NOT_BOUND', 'repair': 'NONE'})
                self.assertIs(observation['fail_closed'], True)
                self.assertIs(observation['mutates_state'], False)
                self.assertIs(observation['authorizes_exposure'], False)
                self.assertEqual(canonical(frozen), baseline)
                self.assertEqual(canonical(_credit_snapshot(credit, [advance_id], CLAIM_ID)), baseline)

    def test_checkpoint_replay(self):
        self._replay(self.pack)

    def test_swapped_checkpoint(self):
        pack = deepcopy(self.pack)
        commit, bind, acceptance = pack['cases']
        settlement = self._settlement_for(commit, CHECKPOINTS[0])
        _, frozen = self._draw_credit(pack['advance'], settlement)
        bind['receipt_ref'], acceptance['receipt_ref'] = acceptance['receipt_ref'], bind['receipt_ref']
        for case in (bind, acceptance):
            receipt = _resolve(self.documents, case['receipt_ref'])
            observation = observe_settlement_variance(receipt['settlement']['claim'], frozen['claim'],
                                                     tolerance=pack['tolerance'])
            self.assertEqual(observation['variance'], 0)
        with self.assertRaisesRegex(AssertionError, 'bind-refund checkpoint receipt association'):
            self._replay(pack)
