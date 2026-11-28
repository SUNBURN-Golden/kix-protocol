"""Replay two statement component splits from the pinned L1 refund checkpoint."""
from pathlib import Path
import unittest

from credit_fixture import exact_fields
from settlement_credit_boundary_vectors import replay_scenario_with_state
from settlement_fsm import SettlementError
from test_capital_later_statement_vectors import (
    FIXTURE as L1_INPUT, FIXTURE_SHA256, ROOT, VECTORS as L1_OUTPUT, VECTORS_SHA256,
    check_execution_flags, validate_fixture,
)
from test_capital_operation_replay_vectors import PROVENANCE, load, same, sha
from test_capital_refund_composition_vectors import snapshot

PACK = Path(__file__).resolve().parent / 'fixtures/capital_statement_component_identity_vectors_v1.json'
SOURCE_PINS = ((L1_INPUT, FIXTURE_SHA256), (L1_OUTPUT, VECTORS_SHA256))
SPLITS = {'fee': {'fee': 3_000, 'held': 0}, 'held': {'fee': 0, 'held': 3_000}}
CONFLICT_KEY = 'stmt-2-other-split'


class CapitalStatementComponentIdentityTests(unittest.TestCase):
    def test_statement_component_identity(self):
        pack = load(PACK)
        exact_fields(pack, {'fixture_version', 'fixture_kind', 'synthetic_only', 'provenance',
                            'source_pins', 'checkpoint_ref', 'cases'}, 'pack')
        same(['capital-statement-component-identity/1', 'SYNTHETIC_STATEMENT_COMPONENT_IDENTITY',
              True, PROVENANCE],
             [pack[k] for k in ('fixture_version', 'fixture_kind', 'synthetic_only', 'provenance')])
        same([{'path': path.relative_to(ROOT).as_posix(), 'sha256': digest}
              for path, digest in SOURCE_PINS], pack['source_pins'])
        for path, digest in SOURCE_PINS:
            self.assertEqual(sha(path.read_bytes()), digest, path.name)

        inputs = validate_fixture(load(L1_INPUT))
        l1 = load(L1_OUTPUT)['scenarios'][0]
        same(L1_OUTPUT.relative_to(ROOT).as_posix() + '#/scenarios/0/history/1/snapshot',
             pack['checkpoint_ref'])
        prefix = inputs['setup_steps'] + inputs['steps'][:2]
        statement = inputs['steps'][2]['arguments']
        same({**SPLITS['fee'], 'settlement_id': 'claim-1', 'idempotency_key': 'stmt-2',
              'movement_id': 'part-2', 'gross': 40_000, 'amount': 37_000,
              'tax': 0, 'adjustment': 0}, statement)
        self.assertNotIn(CONFLICT_KEY, {s['arguments']['idempotency_key']
                                       for s in prefix + [inputs['steps'][2]]})
        same(list(SPLITS), [case['case_id'] for case in pack['cases']])

        observations = []
        for i, case in enumerate(pack['cases']):
            case_id = case['case_id']
            with self.subTest(case=case_id):
                exact_fields(case, {'case_id', 'arguments', 'expected_result', 'after',
                                    'journal_ref', 'conflict'}, case_id)
                exact_fields(case['conflict'], {'arguments', 'expected_result'}, 'conflict')
                same({**statement, **SPLITS[case_id]}, case['arguments'])
                receipts, settlement, credit = replay_scenario_with_state({'steps': prefix})
                self.assertTrue(all('ok' in row['result'] for row in receipts))
                same(l1['setup_results'], receipts[:8])
                same([row['result'] for row in l1['history'][:2]],
                     [row['result'] for row in receipts[8:]])
                before = snapshot(inputs, settlement, credit)
                same(l1['history'][1]['snapshot'], before)
                journal = before['settlement']['journal']
                self.assertEqual(len(journal), 6)
                self.assertEqual(len(before['credit']['journal']), 4)
                self.assertNotIn('part-2', {entry['body'].get('movement_id') for entry in journal})

                result = settlement.observe_statement(**case['arguments'])
                same(case['expected_result'], {'ok': result})
                same([False, 'observe_statement'], [result['duplicate'], result['applied']])
                after = snapshot(inputs, settlement, credit)
                same(case['after'], after)
                if case_id == 'fee':
                    same(l1['history'][2]['result'], {'ok': result})
                    same(l1['history'][2]['snapshot'], after)

                body = dict(case['arguments'], adjustment_reason=None)
                entry = {'op': 'observe_statement', 'settlement_id': body.pop('settlement_id'),
                         'idempotency_key': body.pop('idempotency_key'), 'body': body}
                same(journal + [entry], after['settlement']['journal'])
                same(PACK.relative_to(ROOT).as_posix() + f'#/cases/{i}/after/settlement/journal/{len(journal)}',
                     case['journal_ref'])
                same(before['credit'], after['credit'])
                self._check_arithmetic_and_observers(after)
                check_execution_flags(self, after)
                observations.append([after['settlement']['view']['claim'], after['credit'],
                                     after['variance'], after['shared_exposure']])

                other = pack['cases'][1 - i]['case_id']
                same({**statement, **SPLITS[other], 'idempotency_key': CONFLICT_KEY},
                     case['conflict']['arguments'])
                with self.assertRaises(SettlementError) as refused:
                    settlement.observe_statement(**case['conflict']['arguments'])
                self.assertEqual(refused.exception.code, 'STATEMENT_BINDING_CONFLICT')
                same({'error': {'type': type(refused.exception).__name__, 'code': refused.exception.code}},
                     case['conflict']['expected_result'])
                # This compares both accepted journals as well as the public views and observers.
                same(after, snapshot(inputs, settlement, credit))

        if len(observations) == 2:
            same(*observations)

    def _check_arithmetic_and_observers(self, after):
        claim = after['settlement']['view']['claim']
        totals = {'confirmed_cash': 60_000 + 37_000, 'non_cash_accounted': 3_000,
                  'receivable_open': 100_000 - (60_000 + 40_000), 'distributed_cash': 60_000,
                  'undistributed_cash': 37_000, 'refund_outstanding': 10_000,
                  'refund_bearer_policy': 'REQUESTER'}
        same(totals, {key: claim[key] for key in totals})
        face = after['credit']['claim']
        advance = after['credit']['views'][0]
        same([True, 100_000, 60_000],
             [face['snapshot_frozen'], face['open_face'], face['confirmed_cash_on_face']])
        same([15_000, 15_000, 0],
             [advance[k] for k in ('drawn_exposure', 'outstanding_exposure', 'repaid_exposure')])

        variance, exposure = after['variance'], after['shared_exposure']
        same([35_000, 5_000], [line['outstanding'] for line in claim['obligations']])
        same([(35_000 + 5_000) - 100_000, 0, False, 97_000 - 60_000],
             [variance['variance'], variance['tolerance'], variance['within_tolerance'],
              variance['companion']['cash_delta']])
        same([100_000, True, 15_000, 15_000, 0],
             [exposure['limit'], exposure['within_limit'],
              *[exposure['observable'][f'group_{k}_exposure'] for k in ('drawn', 'outstanding', 'repaid')]])
        for observed, code in ((variance, 'SETTLEMENT_VARIANCE_NOT_BOUND'),
                               (exposure, 'SHARED_EXPOSURE_NOT_BOUND')):
            same({'code': code, 'contract_status': 'NOT_BOUND', 'repair': 'NONE'}, observed['mapping'])
            same(['NOT_BOUND', True, False, False],
                 [observed[k] for k in ('refund_component', 'fail_closed', 'mutates_state', 'authorizes_exposure')])
