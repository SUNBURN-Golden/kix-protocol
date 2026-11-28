"""Replay equal-sized settlement acceptance and credit repayment on fresh forks."""

from hashlib import sha256
import unittest

from credit_fixture import decode_json, exact_fields
from settlement_credit_boundary_vectors import PROVENANCE, replay_scenario_with_state
from test_capital_commerce_refund_checkpoints import CHECKPOINTS, CLAIM_ID, TRADE_ID
from test_capital_commerce_refund_checkpoints import PACK as CHECKPOINT_PACK
from test_capital_companion_evidence_index import COMMERCE_RECEIPTS, FIXTURES, ROOT, _resolve
from test_capital_operation_replay_vectors import dispatch, load, same, snapshot


PACK = FIXTURES + 'capital_refund_versus_repayment_vectors_v1.json'
COMMERCE_INPUTS = COMMERCE_RECEIPTS.replace('_receipts_', '_inputs_')
SOURCE_PATHS = (COMMERCE_INPUTS, COMMERCE_RECEIPTS, CHECKPOINT_PACK)
CASE_ID = 'linked-purchase-partial-refund'
IDENTITY = (CLAIM_ID, TRADE_ID, 'KRW')
ADVANCE = {
    'advance_id': 'advance-commerce-checkpoints',
    'amount': 10000,
    'beneficiary_role': 'fixture-beneficiary',
    'draw_id': 'draw-commerce-checkpoints',
}
GROUP = 'fixture-refund-versus-repayment'
LIMIT = 10000
REPAYMENT = {
    'advance_id': ADVANCE['advance_id'],
    'idempotency_key': 'repay-refund-comparison-1',
    'repay_id': 'repayment-note-1',
    'sequence': 1,
    'amount': 1500,
}
SETUP_OPERATIONS = (
    (5, 'initiate', 'initiate'),
    (6, 'settlement-authorize', 'authorize'),
    (8, 'capture', 'capture'),
    (9, 'commit', 'commit'),
    (14, 'bind-refund', 'bind_refund'),
)


def replay_checkpoint(advance, commands, face):
    advance_id = advance['advance_id']
    credit_steps = [
        ('offer', 'checkpoint-offer', {'face': face, 'amount': advance['amount'],
                                      'beneficiary_role': advance['beneficiary_role']}),
        ('approve', 'checkpoint-approve', {}),
        ('bind_settlement', 'checkpoint-bind', {'settlement_id': CLAIM_ID}),
        ('draw', 'checkpoint-draw', {'draw_id': advance['draw_id']}),
    ]
    settlement_steps = [
        {'step_id': step_id, 'target': 'settlement', 'operation': operation,
         'arguments': commands[operation]} for _, step_id, operation in SETUP_OPERATIONS
    ]
    steps = [
        {'step_id': operation, 'target': 'credit', 'operation': operation,
         'arguments': {'advance_id': advance_id, 'idempotency_key': key, **body}}
        for operation, key, body in credit_steps
    ]
    # Freeze the committed claim before the refund reaches the live settlement.
    return replay_scenario_with_state({'steps': settlement_steps[:-1] + steps + settlement_steps[-1:]})


class CapitalRefundVersusRepaymentTests(unittest.TestCase):
    def _source_commands(self, pack):
        same(list(SOURCE_PATHS), [pin['path'] for pin in pack['source_pins']])
        documents = {}
        for pin in pack['source_pins']:
            exact_fields(pin, {'path', 'sha256'}, 'source pin')
            raw = (ROOT / pin['path']).read_bytes()
            self.assertEqual(sha256(raw).hexdigest(), pin['sha256'], pin['path'])
            documents[pin['path']] = decode_json(raw.decode('utf-8'))

        checkpoints = documents[CHECKPOINT_PACK]
        same(ADVANCE, checkpoints['advance'])
        same(checkpoints['advance'], pack['advance'])
        refs = [
            f'{COMMERCE_RECEIPTS}#/cases/0/steps/{index}/receipt'
            for _, index, _, _ in CHECKPOINTS
        ]
        same(refs, pack['checkpoint_refs'])
        same([(case_id, ref) for (case_id, _, _, _), ref in zip(CHECKPOINTS, refs, strict=True)],
             [(case['case_id'], case['receipt_ref']) for case in checkpoints['cases']])
        for path in (COMMERCE_INPUTS, COMMERCE_RECEIPTS):
            self.assertEqual(documents[path]['cases'][0]['id'], CASE_ID)

        commands, receipts = {}, {}
        operations = (*SETUP_OPERATIONS, (15, 'observe-mock-acceptance', 'observe_mock_cancel_acceptance'))
        for index, step_id, operation in operations:
            fragment = f'#/cases/0/steps/{index}'
            step = _resolve(documents, COMMERCE_RECEIPTS + fragment)
            source = _resolve(documents, COMMERCE_INPUTS + fragment)
            action = 'settlement_' + operation
            self.assertEqual((step['id'], step['action']), (step_id, action))
            self.assertEqual((source['id'], source['action']), (step_id, action))
            self.assertEqual(step['input_ref'], COMMERCE_INPUTS + fragment + '/body')
            body = _resolve(documents, step['input_ref'])
            receipt = step['receipt']
            self.assertEqual(body['settlement_id'], CLAIM_ID)
            self.assertEqual(receipt['applied'], operation)
            self.assertIs(receipt['duplicate'], False)
            self.assertIs(receipt['funds_executed'], False)
            view = receipt['settlement']
            self.assertEqual((view['settlement_id'], view['trade_id'], view['currency']), IDENTITY)
            if index in (9, 14, 15):
                self.assertEqual(view['phase'], 'COMMITTED')
                claim = view['claim']
                self.assertEqual((claim['claim_id'], claim['trade_id'], claim['currency']), IDENTITY)
            commands[operation] = body
            receipts[operation] = receipt
        same({'settlement_id': CLAIM_ID, 'idempotency_key': 'accept-refund-claim-1',
              'source_id': 'mock-accept-1', 'amount': 1500},
             commands['observe_mock_cancel_acceptance'])
        return commands, receipts

    def _check_snapshot(self, state, face, accepted, refund_outstanding, repaid, credit_outstanding):
        settlement = state['settlement']['view']
        claim = settlement['claim']
        credit = state['credit']
        view, = credit['views']
        exposure = state['shared_exposure']
        self.assertEqual(settlement['phase'], 'COMMITTED')
        self.assertEqual(claim['refund_bearer_policy'], 'REQUESTER')
        same((4000, accepted, refund_outstanding, accepted, 10001),
             (claim['refund_face'], claim['refund_accepted'], claim['refund_outstanding'],
              claim['pg_adjustment_outstanding'], claim['confirmed_cash']))
        same(face, credit['journal'][0]['body']['face'])
        self.assertEqual(view['phase'], 'DRAWN')
        self.assertEqual(view['settlement_id'], CLAIM_ID)
        self.assertIs(view['mock_settlement_commit_observed'], True)
        self.assertIs(view['snapshot_frozen'], True)
        self.assertIs(credit['claim']['snapshot_frozen'], True)
        same((10000, repaid, credit_outstanding),
             (view['drawn_exposure'], view['repaid_exposure'], view['outstanding_exposure']))
        same({
            'group_drawn_exposure': 10000,
            'group_repaid_exposure': repaid,
            'group_outstanding_exposure': credit_outstanding,
            'group_open_face': 10001,
            'group_reserved_open': 10000,
            'group_residual_unreserved': 1,
        }, exposure['observable'])
        self.assertEqual((exposure['group_id'], exposure['limit']), (GROUP, LIMIT))
        same((1, 1), (exposure['advance_count'], exposure['claim_count']))
        self.assertIs(exposure['within_limit'], True)
        self.assertEqual(exposure['mapping'], {'code': 'SHARED_EXPOSURE_NOT_BOUND',
                                               'contract_status': 'NOT_BOUND', 'repair': 'NONE'})
        self.assertEqual(exposure['refund_component'], 'NOT_BOUND')
        self.assertIs(exposure['fail_closed'], True)
        for field in ('mutates_state', 'authorizes_exposure', 'legal_debtor_bound'):
            self.assertIs(exposure[field], False, field)
        for record in (settlement, claim, view):
            for field in ('funds_executed', 'bank_debit_observed', 'legal_debtor_bound'):
                self.assertIs(record[field], False, field)
        self.assertIs(claim['external_return_closed'], False)
        self.assertIs(view['repayment_observed'], False)

    def test_refund_versus_repayment(self):
        pack = load(ROOT / PACK)
        exact_fields(pack, {'fixture_version', 'fixture_kind', 'synthetic_only', 'provenance',
                            'source_pins', 'checkpoint_refs', 'advance', 'group_id', 'limit',
                            'before', 'cases'}, 'pack')
        same(('capital-refund-versus-repayment/1', 'SYNTHETIC_REFUND_VERSUS_REPAYMENT',
              True, PROVENANCE, GROUP, LIMIT),
             (pack['fixture_version'], pack['fixture_kind'], pack['synthetic_only'],
              pack['provenance'], pack['group_id'], pack['limit']))
        commands, receipts = self._source_commands(pack)
        face = receipts['commit']['settlement']['claim']
        scenario = {'advance_ids': [ADVANCE['advance_id']], 'claim_id': CLAIM_ID,
                    'group_id': pack['group_id'], 'limit': pack['limit']}
        branches = (
            ('mock_acceptance', 'settlement', 'observe_mock_cancel_acceptance', (1500, 2500, 0, 10000)),
            ('repayment_note', 'credit', 'repay', (0, 4000, 1500, 8500)),
        )
        for case, (case_id, target, operation, amounts) in zip(pack['cases'], branches, strict=True):
            with self.subTest(case=case_id):
                exact_fields(case, {'case_id', 'target', 'operation', 'arguments',
                                    'expected_result', 'after'}, case_id)
                same((case_id, target, operation), (case['case_id'], case['target'], case['operation']))
                setup, settlement, credit = replay_checkpoint(pack['advance'], commands, face)
                for row in setup:
                    self.assertEqual(set(row['result']), {'ok'}, row['step_id'])
                    if row['target'] == 'settlement':
                        same({'ok': receipts[row['operation']]}, row['result'])
                before = snapshot(scenario, settlement, credit)
                # Both fresh forks must reproduce the same complete checkpoint bytes.
                same(pack['before'], before)
                self._check_snapshot(before, face, 0, 4000, 0, 10000)
                self.assertEqual([entry['op'] for entry in before['settlement']['journal']],
                                 ['initiate', 'authorize', 'capture', 'commit', 'bind_refund'])
                self.assertEqual([entry['op'] for entry in before['credit']['journal']],
                                 ['offer', 'approve', 'bind_settlement', 'draw'])

                arguments = case['arguments']
                if target == 'settlement':
                    same(commands[operation], arguments)
                    result = {'ok': settlement.observe_mock_cancel_acceptance(**arguments)}
                    same({'ok': receipts[operation]}, result)
                    identity_field, untouched = 'settlement_id', 'credit'
                else:
                    same(REPAYMENT, arguments)
                    result = dispatch(credit, case)
                    self.assertIs(result['ok']['repayment_observed'], False)
                    identity_field, untouched = 'advance_id', 'settlement'

                same(case['expected_result'], result)
                receipt = result['ok']
                self.assertEqual(receipt['applied'], operation)
                self.assertIs(receipt['duplicate'], False)
                self.assertIs(receipt['funds_executed'], False)

                # snapshot observes shared exposure from this fork's own live credit view.
                after = snapshot(scenario, settlement, credit)
                same(case['after'], after)
                self._check_snapshot(after, face, *amounts)
                same(before[untouched], after[untouched])
                body = dict(arguments)
                entry = {'op': operation, identity_field: body.pop(identity_field),
                         'idempotency_key': body.pop('idempotency_key'), 'body': body}
                same(before[target]['journal'] + [entry], after[target]['journal'])
