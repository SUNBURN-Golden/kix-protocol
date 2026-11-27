"""Continue the pinned payment-reference checkpoint in two fresh mock hosts."""
from __future__ import annotations

import copy
import unittest

import test_commerce_journey_receipts as goldens
import test_commerce_payment_ref_scope_vectors as payment_scope
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import _canonical

ROOT = payment_scope.ROOT
BRA = payment_scope.BRA
FIXTURE = f'{BRA}/fixtures/commerce_cross_order_issuance_inputs_v1.json'
GOLDEN = ROOT / f'{BRA}/fixtures/commerce_cross_order_issuance_receipts_v1.json'
SOURCE_INPUT = payment_scope.FIXTURE
SOURCE_OUTPUT = payment_scope.GOLDEN.relative_to(ROOT).as_posix()
SOURCE_BLOBS = {
    SOURCE_INPUT: 'a923e6041fb801012950d9d8ebd81dd4af1dde6c',
    SOURCE_OUTPUT: 'dce42838bb24018e54271560f520ce984a8b6dc3',
}
CHECKPOINT = {
    'case_id': 'payment-ref-scope',
    'step_id': 'payment-2',
    'action': 'reservation_observe_payment',
    'input_ref': SOURCE_INPUT + '#/cases/0/steps/15/body',
    'outcome_ref': SOURCE_OUTPUT + '#/cases/0/steps/15',
}
STEP_ID = 'issue-order-2'
ACTION = 'reservation_issue'
SEMANTIC_STATUS = 'HOLD_SEMANTIC'
CONFLICT = 'ISSUANCE_BINDING_CONFLICT'
ISSUE_EXPECTATION = {
    'duplicate': False, 'applied': 'issue',
    'paths': {'evidence.kind': 1, 'evidence.chain_issued': False},
}
_assert_paths = payment_scope._assert_paths
_check = payment_scope.journey._check


def _resolve(documents, reference):
    path, pointer = reference.split('#/')
    node = documents[path]
    for part in pointer.split('/'):
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def _load_checkpoint(fixture):
    _check(fixture['checkpoint'] == CHECKPOINT, 'checkpoint references')
    documents, pins = {}, []
    for path, blob in SOURCE_BLOBS.items():
        raw = (ROOT / path).read_bytes()
        pin = goldens._pin(path, raw)
        _check(pin['gitBlob'] == blob, f'predecessor blob: {path}')
        documents[path] = goldens._decode(raw)
        pins.append(pin)
    _check(fixture['sources'] == pins, 'source byte pins')
    _check(documents[SOURCE_OUTPUT]['fixture'] == pins[0], 'predecessor fixture association')

    source_case, = documents[SOURCE_INPUT]['cases']
    output_case, = documents[SOURCE_OUTPUT]['cases']
    _check(source_case['id'] == output_case['id'] == CHECKPOINT['case_id'], 'checkpoint case identity')
    steps, outcomes = source_case['steps'], output_case['steps']
    _check(len(steps) == len(outcomes) == 16, 'checkpoint history length')
    for step in (steps[-1], outcomes[-1]):
        _assert_paths(step, {'id': CHECKPOINT['step_id'], 'action': CHECKPOINT['action']})
    _check(_resolve(documents, CHECKPOINT['input_ref']) is steps[-1]['body'], 'checkpoint input association')
    _check(_resolve(documents, CHECKPOINT['outcome_ref']) is outcomes[-1], 'checkpoint outcome association')
    _assert_paths(outcomes[9], {'id': 'reuse-primary', 'rejection_code': 'PAYMENT_BINDING_CONFLICT'})
    return steps, outcomes, pins


def _validate_branches(fixture, predecessor_steps):
    catalogue = load_catalogue(ROOT)
    _assert_paths(fixture, {
        'fixture_version': 1, 'domain': catalogue.fsm_domain,
        'provenance': 'OFFLINE_CONFORMANCE_FIXTURE_ONLY',
        'semantic_consumer_status': SEMANTIC_STATUS,
    })
    distinct, collision = fixture['cases']
    keys = {step['body']['idempotency_key'] for step in predecessor_steps}
    schema = catalogue.fsm['commands'][ACTION]['schema']
    for case, case_id, issuance_id, key, expectation in (
        (distinct, 'distinct-issuance', 'issue-2', 'issue-order-2-distinct', {'expect': ISSUE_EXPECTATION}),
        (collision, 'issuance-collision', 'issue-1', 'issue-order-2-collision', {'expect_error': CONFLICT}),
    ):
        _check(case['id'] == case_id, 'branch case identity/order')
        step, = case['steps']
        body = {'order_id': 'order-2', 'issuance_id': issuance_id, 'idempotency_key': key}
        _check(_canonical(step) == _canonical(dict(id=STEP_ID, action=ACTION, body=body, **expectation)),
               f'branch command and expectation: {case_id}')
        errors = problems(step['body'], schema)
        _check(not errors, f'{case_id}: command schema: {errors}')
        _check(key not in keys, f'{case_id}: idempotency key is fresh at the checkpoint')
        keys.add(key)


def _replay_checkpoint(steps, outcomes):
    host, accepted = FsmHost(), {}
    for index, (step, expected) in enumerate(zip(steps, outcomes, strict=True)):
        step_id, action = step['id'], step['action']
        observed = {'id': step_id, 'action': action, 'input_ref': f'{SOURCE_INPUT}#/cases/0/steps/{index}/body'}
        try:
            observed['receipt'] = host.call(action, copy.deepcopy(step['body']))
        except FsmRejected as exc:
            _check(index == 9 and step_id == 'reuse-primary' and exc.code == 'PAYMENT_BINDING_CONFLICT',
                   f'predecessor step {step_id}: unexpected refusal {exc.code}')
            observed['rejection_code'] = exc.code
        else:
            accepted[step_id] = action
        snapshot = payment_scope._snapshot(host, accepted)
        observed['diagnostic_snapshot'] = snapshot['views']
        _check(_canonical(observed) == _canonical(expected), f'predecessor outcome: {step_id}')

    views = snapshot['views']
    _check(set(snapshot['machines']) == set(payment_scope.MACHINES), 'all five accepted journals are present')
    _assert_paths(views['reservation_2'], {
        'reservation_id': 'reserve-2', 'order_id': 'order-2', 'show_id': 'show-2', 'buyer_role': 'buyer-3',
        'phase': 'PAYMENT_NOTED', 'payment_ref': steps[-1]['body']['payment_ref'],
        'amount': steps[-1]['body']['amount'], 'issuance_id': None, 'right': None,
        'slot_state': 'RESERVED', 'slot_right_id': None,
    })
    _assert_paths(views['resale_right'], {
        'right.right_id': 'issue-1', 'right.show_id': 'show-1',
        'right.holder_role': 'buyer-2', 'right.version': 2, 'right.state': 'ACTIVE',
    })
    _assert_paths(views['listing'], {'listing_id': 'list-1', 'phase': 'TRANSFERRED', 'transfer_id': 'transfer-1'})
    return host, accepted, snapshot


def _assert_issued(body, receipt, before, after):
    _assert_paths(receipt, dict(ISSUE_EXPECTATION['paths'], duplicate=False, applied='issue'))
    issue_id = body['issuance_id']
    old, new = before['machines'], after['machines']
    expected_entry = {
        'op': 'issue', 'subject_id': issue_id, 'idempotency_key': body['idempotency_key'],
        'body': {'order_id': 'order-2'},
    }
    _check(_canonical(new['reservation']['journal']) == _canonical(old['reservation']['journal'] + [expected_entry]),
           'one reservation issue append with an intact prefix')
    for name in set(old) - {'reservation'}:
        _check(_canonical(new[name]) == _canonical(old[name]), f'{name} state, digest and journal preserved')

    views = after['views']
    paid = before['views']['reservation_2']
    _assert_paths(views['reservation_2'], {
        'reservation_id': 'reserve-2', 'order_id': 'order-2', 'phase': 'ISSUED', 'issuance_id': issue_id,
        'payment_ref': paid['payment_ref'], 'amount': paid['amount'],
        'slot_state': 'ISSUED', 'slot_right_id': issue_id, 'right.right_id': issue_id,
        'right.show_id': 'show-2', 'right.holder_role': 'buyer-3', 'right.version': 1, 'right.state': 'ACTIVE',
    })
    slots_with_rights = [slot for slot in views['show_2']['show']['slots'] if slot['right_id'] is not None]
    _check(slots_with_rights == [{
        'slot': paid['slot'], 'state': 'ISSUED', 'reservation_id': 'reserve-2', 'right_id': issue_id,
    }], 'exactly one issued right on show-2')
    _check(_canonical(receipt['reservation']) == _canonical(views['reservation_2']), 'issued reservation receipt')
    _check(_canonical(receipt['show']) == _canonical(views['show_2']['show']), 'issued slot receipt')


def _drive_branch(step, index, host, accepted, before):
    body = step['body']
    outcome = {'id': step['id'], 'action': step['action'], 'input_ref': f'{FIXTURE}#/cases/{index}/steps/0/body'}
    try:
        receipt = host.call(step['action'], copy.deepcopy(body))
    except FsmRejected as exc:
        _check(exc.code == step.get('expect_error'), f'branch {index}: unexpected refusal {exc.code}')
        outcome['rejection_code'] = exc.code
    else:
        _check('expect' in step, f'branch {index}: expected refusal was accepted')
        outcome['receipt'] = copy.deepcopy(receipt)

    after = payment_scope._snapshot(host, accepted)
    if 'rejection_code' in outcome:
        _check(_canonical(after) == _canonical(before), 'collision changed state, digests, accepted journals or views')
    else:
        _assert_issued(body, receipt, before, after)
    for name in ('resale_right', 'listing', 'reservation', 'show'):
        _check(_canonical(after['views'][name]) == _canonical(before['views'][name]), f'show-1 {name} preserved')
    for machine in ('reservation', 'admission'):
        journal = after['machines'][machine]['journal']
        _check(all(entry['op'] != 'consume' for entry in journal), f'no consumption in {machine} journal')
    for view in ('reservation', 'reservation_2'):
        _assert_paths(after['views'][view], {'consume_id': None})
    for node in payment_scope.journey._walk([outcome.get('receipt', {}), after['views']]):
        for flag in payment_scope.FALSE_FLAGS & node.keys():
            _check(node[flag] is False, f'branch {index}: authority flag {flag}')
    outcome['diagnostic_snapshot'] = after
    return outcome


def _observe():
    raw = (ROOT / FIXTURE).read_bytes()
    fixture = goldens._decode(raw)
    _check(_canonical(fixture).encode('utf-8') == raw, 'canonical input bytes differ')
    steps, outcomes, sources = _load_checkpoint(fixture)
    _validate_branches(fixture, steps)
    cases, checkpoints = [], []
    for index, case in enumerate(fixture['cases']):
        host, accepted, before = _replay_checkpoint(steps, outcomes)
        checkpoints.append(_canonical(before))
        step, = case['steps']
        outcome = _drive_branch(step, index, host, accepted, before)
        _check(_resolve({FIXTURE: fixture}, outcome['input_ref']) is step['body'], 'branch input association')
        cases.append({'id': case['id'], 'steps': [outcome]})
    _check(checkpoints[0] == checkpoints[1], 'independent branches began at identical checkpoints')
    return {
        'record_schema_version': 'kix-commerce-cross-order-issuance-receipts/1',
        'record_kind': 'IN_PROCESS_MOCK_RECEIPT_VECTORS',
        'normative': False,
        'semantic_consumer_status': SEMANTIC_STATUS,
        'diagnostic_snapshot_kind': 'TEST_HARNESS_EVIDENCE',
        'fixture': goldens._pin(FIXTURE, raw),
        'sources': sources,
        'checkpoint': fixture['checkpoint'],
        'cases': cases,
    }


class CommerceCrossOrderIssuanceVectorTests(unittest.TestCase):
    def test_complete_output_bytes_and_references(self):
        self.assertTrue(_canonical(_observe()).encode('utf-8') == GOLDEN.read_bytes(),
                        'complete canonical cross-order issuance outcomes differ')


if __name__ == '__main__':
    unittest.main()
