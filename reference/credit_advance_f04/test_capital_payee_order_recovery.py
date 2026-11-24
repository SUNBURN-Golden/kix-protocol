"""Compare the pinned R1 history with one fresh replay using the other payee order."""
from __future__ import annotations

import copy
import unittest

from credit_fixture import exact_fields
from test_capital_refund_composition_vectors import (
    FIXTURE, FIXTURE_SHA256, ROOT, VECTORS, VECTORS_SHA256, checkpoints, load,
    replay, same, sha,
)

PACK = FIXTURE.with_name('capital_payee_order_recovery_vectors_v1.json')
SCENARIO_ID = 'R1_full_refund_after_partial_distribution'
CASE_ORDERS = (
    ('r1_fee_first', ['fee-r1', 'res-r1']),
    ('r1_residual_first', ['res-r1', 'fee-r1']),
)
REFUND_CHECKPOINTS = ('refund-full', 'accept-full')


def assert_payee_rows(expected, actual):
    same(sorted(expected, key=lambda row: row['payee']),
         sorted(actual, key=lambda row: row['payee']))


def assert_conservation(obligations):
    for row in obligations:
        accounted = row['distributed'] + row['cancelled_unpaid'] + row['outstanding']
        if row['face'] != accounted:
            raise AssertionError(f"face conservation failed for {row['payee']}")


class CapitalPayeeOrderRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pack = load(PACK)
        exact_fields(pack, {'fixture_version', 'fixture_kind', 'synthetic_only', 'source_pins',
                            'scenario_id', 'input_ref', 'baseline_ref', 'cases'}, 'comparison pack')
        same(['capital-payee-order-recovery/1', 'SYNTHETIC_PAYEE_ORDER_RECOVERY', True, SCENARIO_ID],
             [pack['fixture_version'], pack['fixture_kind'], pack['synthetic_only'], pack['scenario_id']])
        input_path, baseline_path = (path.relative_to(ROOT).as_posix() for path in (FIXTURE, VECTORS))
        same([{'path': input_path, 'sha256': FIXTURE_SHA256},
              {'path': baseline_path, 'sha256': VECTORS_SHA256}], pack['source_pins'])
        same([input_path + '#/scenarios/0', baseline_path + '#/scenarios/0'],
             [pack['input_ref'], pack['baseline_ref']])
        same(FIXTURE_SHA256, sha(FIXTURE.read_bytes()))
        same(VECTORS_SHA256, sha(VECTORS.read_bytes()))
        inputs = load(FIXTURE)['scenarios'][0]
        baseline = load(VECTORS)['scenarios'][0]
        same([SCENARIO_ID, SCENARIO_ID], [inputs['scenario_id'], baseline['scenario_id']])

        cls.cases = pack['cases']
        same([list(case) for case in CASE_ORDERS], [[c['case_id'], c['order']] for c in cls.cases])
        same(cls.cases[0]['order'], inputs['steps'][0]['arguments']['order'])
        residual_inputs = copy.deepcopy(inputs)
        residual_inputs['steps'][0]['arguments']['order'] = list(cls.cases[1]['order'])
        residual = replay(residual_inputs)
        same(baseline['setup_results'], residual['setup_results'])
        same(baseline['initial_snapshot'], residual['initial_snapshot'])

        cls.histories = (baseline, residual)
        cls.states = []
        step_ids = ['distribute', *REFUND_CHECKPOINTS]
        for history in cls.histories:
            same(step_ids, [row['step_id'] for row in history['history']])
            cls.states.append(dict(zip(['initial', *step_ids], checkpoints(history), strict=True)))

    def test_order_pair(self):
        frozen = self.states[0]['initial']
        distributions = ({'fee-r1': 5_000, 'res-r1': 5_000}, {'fee-r1': 0, 'res-r1': 10_000})
        for case, history, states, distribution in zip(self.cases, self.histories, self.states,
                                                       distributions, strict=True):
            exact_fields(case, {'case_id', 'order', 'expected_result'}, 'comparison case')
            exact_fields(case['expected_result'], {'ok'}, 'comparison result envelope')
            expected = case['expected_result']['ok']
            exact_fields(expected, set(REFUND_CHECKPOINTS), 'comparison checkpoints')
            distribute = next(row for row in history['history'] if row['step_id'] == 'distribute')
            same(distribution, distribute['result']['ok']['effect'])
            for step_id, current in states.items():
                with self.subTest(case=case['case_id'], checkpoint=step_id):
                    same(frozen['credit'], current['credit'])
                    same(frozen['shared_exposure'], current['shared_exposure'])
                    claim = current['settlement']['view']['claim']
                    assert_conservation(claim['obligations'])
                    if step_id in REFUND_CHECKPOINTS:
                        self.assert_full_refund(expected[step_id], claim, current['variance'], step_id)

        for step_id in REFUND_CHECKPOINTS:
            same(self.states[0][step_id]['variance'], self.states[1][step_id]['variance'])

    def assert_full_refund(self, expected, claim, variance, step_id):
        exact_fields(expected, {'obligations', 'recovery_due', 'variance'}, step_id)
        obligations = claim['obligations']
        assert_payee_rows(expected['obligations'], obligations)
        same([10_000, -100_000], [expected['recovery_due'], expected['variance']])
        same(expected['recovery_due'], claim['recovery_due'])
        same(claim['recovery_due'], sum(row['recovery_due'] for row in obligations))
        for row in obligations:
            same(row['distributed'], row['recovery_due'])
        same([10_000, 100_000, 'FIXTURE_FULL_GROSS_RECLASS', True],
             [claim[k] for k in ('confirmed_cash', 'refund_face', 'refund_bearer_policy',
                                 'fixture_reclassified')])
        same(100_000 if step_id == 'accept-full' else 0, claim['refund_accepted'])
        same(expected['variance'], variance['variance'])
        same([0, 10_000], [variance['companion']['cash_delta'], variance['companion']['recovery_delta']])

    def test_swapped_payee_attribution(self):
        expected = self.cases[1]['expected_result']['ok']
        for step_id in REFUND_CHECKPOINTS:
            with self.subTest(checkpoint=step_id):
                actual = self.states[1][step_id]['settlement']['view']['claim']['obligations']
                swapped = copy.deepcopy(actual)
                payees = {row['payee']: row for row in swapped}
                fee, residual = payees['fee-r1'], payees['res-r1']
                fee['recovery_due'], residual['recovery_due'] = residual['recovery_due'], fee['recovery_due']
                same(10_000, sum(row['recovery_due'] for row in swapped))
                assert_conservation(swapped)
                assert_payee_rows(expected[step_id]['obligations'], actual)
                with self.assertRaises(AssertionError):
                    assert_payee_rows(expected[step_id]['obligations'], swapped)

                missing_cancellation = copy.deepcopy(actual)
                next(row for row in missing_cancellation if row['payee'] == 'fee-r1')['cancelled_unpaid'] = 0
                with self.assertRaisesRegex(AssertionError, 'face conservation failed for fee-r1'):
                    assert_conservation(missing_cancellation)


if __name__ == '__main__':
    unittest.main()
