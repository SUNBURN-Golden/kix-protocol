"""Database-free checks for the on-sale admission layer.

These need no PostgreSQL and no psycopg. Every limit, capacity, TTL and key
here is a test fixture, not product policy (contract §10). The decision core
is exercised through its public snapshot/decide surface; no private layout is
asserted beyond the contract §4/§8 field names.
"""

from __future__ import annotations

import json
import unittest

from readiness.codec import canonical_json

from durable.budgets import CLASSES, BudgetSpec, ClassLimit
from durable.model import Usage

from onsale import tokens
from onsale.model import (
    CONSUMED, EXPIRED, ISSUED, OUTCOMES, REPLACED, AdmitRequest, AdmitSnapshot,
    EnqueueRequest, EnqueueSnapshot, GaConfigError, OnsaleLimits, ReissueRequest,
    ReissueSnapshot, command_id, decide_admit, decide_enqueue, decide_reissue,
    effective_remaining, first_result_canonical, hint_is_valid,
    negative_hint_document, payload_nbytes, payload_sha256, position_identity,
    propose_group, queue_ticket_id, validate_ga_config,
)
from onsale.router import STRATEGIES, HintRouter, RouterError

# Fixtures only. Not an approved limit of any kind.
BIG = ClassLimit(count=64, bytes=1_000_000, age_ms=10_000_000)
KEY = b'fixture-key-not-product'
KEY_VERSION = 'fixture-v1'
SHOW = 'fixture-show'
EPOCH = 3
MODE = 'GeneralAdmissionSharded'
CONFIG = {'mode': MODE, 'placement_version': 1, 'immutable_total': 4}


def limits(**override):
    values = dict(
        token_ttl_ms=1_000, hint_ttl_ms=500, max_queue_wait_ms=5_000,
        max_outstanding_tokens=8, max_sessions=8,
        group_max_count=4, group_max_bytes=1_000, group_max_wait_ms=50,
    )
    values.update(override)
    return OnsaleLimits(**values)


def spec(**override):
    per_class = {name: BIG for name in CLASSES}
    per_class.update(override)
    return BudgetSpec(**per_class)


def enqueue_request(nonce='n1', shard='s1', ccid='c1', principal='buyer-1'):
    return EnqueueRequest(SHOW, EPOCH, MODE, principal, ccid, nonce, shard)


def shard_row(remaining=2):
    return {'show_id': SHOW, 'epoch': EPOCH, 'shard_id': 's1',
            'initial_capacity': 2, 'remaining': remaining}


def enqueue_decision(now_ms=100, **snapshot_kwargs):
    snapshot = EnqueueSnapshot(config=dict(CONFIG), shard=shard_row(), **snapshot_kwargs)
    return decide_enqueue(snapshot, enqueue_request(), limits(), spec(), KEY, KEY_VERSION, now_ms)


def token_document(decision):
    return json.loads(decision.first_result)['token']


def admit_request(token, ccid='a1', principal='buyer-1'):
    return AdmitRequest(SHOW, EPOCH, MODE, principal, ccid, token)


def admit_snapshot(enq, now_ms=200, **override):
    values = dict(
        config=dict(CONFIG), shard=shard_row(), token=enq.token,
        token_state=ISSUED, token_state_seq=0, ticket=enq.ticket,
        ticket_sequence=1, session_count=0, hint_version=0, commit_position=3,
    )
    values.update(override)
    return AdmitSnapshot(**values)


def reissue_request(ticket, old_nonce='n1', new_nonce='n2', new_shard='s2', ccid='r1'):
    return ReissueRequest(SHOW, EPOCH, MODE, 'buyer-1', ccid, ticket,
                          old_nonce, new_nonce, new_shard)


def reissue_snapshot(enq, **override):
    values = dict(
        config=dict(CONFIG), old_token=enq.token, old_state=ISSUED, old_state_seq=0,
        ticket=enq.ticket, ticket_sequence=1,
        new_shard={'show_id': SHOW, 'epoch': EPOCH, 'shard_id': 's2',
                   'initial_capacity': 2, 'remaining': 2},
        new_token_exists=False, outstanding=1,
    )
    values.update(override)
    return ReissueSnapshot(**values)


class LimitsTests(unittest.TestCase):
    def test_every_bound_is_required(self):
        with self.assertRaises(TypeError):
            OnsaleLimits()
        values = limits().document()
        for name in values:
            partial = dict(values)
            del partial[name]
            with self.assertRaises(TypeError):
                OnsaleLimits(**partial)

    def test_bounds_must_be_positive_integers(self):
        for bad in (0, -1, True, 1.5, '3', None):
            with self.assertRaises(ValueError):
                limits(token_ttl_ms=bad)
            with self.assertRaises(ValueError):
                limits(max_sessions=bad)

    def test_document_is_the_pinned_shape(self):
        self.assertEqual(limits().document(), {
            'group_max_bytes': 1_000, 'group_max_count': 4, 'group_max_wait_ms': 50,
            'hint_ttl_ms': 500, 'max_outstanding_tokens': 8, 'max_queue_wait_ms': 5_000,
            'max_sessions': 8, 'token_ttl_ms': 1_000,
        })


class GaConfigTests(unittest.TestCase):
    def test_sum_invariant_is_enforced_at_creation(self):
        with self.assertRaises(GaConfigError):
            validate_ga_config(5, {'s1': 2, 's2': 2})
        with self.assertRaises(GaConfigError):
            validate_ga_config(3, {'s1': 2, 's2': 2})
        self.assertEqual(validate_ga_config(4, {'s1': 2, 's2': 2}), {'s1': 2, 's2': 2})

    def test_empty_or_invalid_capacities_are_refused(self):
        for bad in ({}, None, [], {'s1': 0}, {'s1': -1}, {'s1': True}, {'s1': 1.5},
                    {'': 2}, {None: 2}):
            with self.assertRaises((GaConfigError, ValueError)):
                validate_ga_config(2, bad)
        for bad in (0, -1, True, 2.5, '4', None):
            with self.assertRaises(ValueError):
                validate_ga_config(bad, {'s1': 2})

    def test_returned_mapping_is_a_copy(self):
        original = {'s1': 2, 's2': 2}
        returned = validate_ga_config(4, original)
        returned['s1'] = 99
        self.assertEqual(original['s1'], 2)


class HintArithmeticTests(unittest.TestCase):
    def test_effective_remaining_clamps_at_zero(self):
        self.assertEqual(effective_remaining(5, 2), 3)
        self.assertEqual(effective_remaining(2, 5), 0)
        self.assertEqual(effective_remaining(0, 0), 0)

    def test_effective_remaining_rejects_bad_inputs(self):
        for bad in (-1, True, 1.5, '2', None):
            with self.assertRaises(ValueError):
                effective_remaining(bad, 0)
            with self.assertRaises(ValueError):
                effective_remaining(0, bad)

    def test_negative_hint_is_versioned_and_never_permanent(self):
        hint = negative_hint_document(
            shard_id='s1', inventory_epoch=EPOCH, version=2,
            source_commit_position=17, expires_at_ms=900,
        )
        self.assertEqual(hint, {
            'shardId': 's1', 'inventoryEpoch': EPOCH, 'version': 2,
            'sourceCommitPosition': 17, 'expiresAtMs': 900,
            'reason': 'SOLD_OUT', 'negative': True,
        })

    def test_hint_validity_is_epoch_and_expiry_bound(self):
        hint = negative_hint_document(
            shard_id='s1', inventory_epoch=EPOCH, version=1,
            source_commit_position=1, expires_at_ms=900,
        )
        self.assertTrue(hint_is_valid(hint, 899, EPOCH))
        self.assertFalse(hint_is_valid(hint, 900, EPOCH))
        self.assertFalse(hint_is_valid(hint, 100, EPOCH + 1))
        self.assertFalse(hint_is_valid(None, 100, EPOCH))
        self.assertFalse(hint_is_valid({'shardId': 's1'}, 100, EPOCH))


class IdentityTests(unittest.TestCase):
    def test_routing_changes_do_not_change_command_identity(self):
        first = enqueue_request(nonce='n1', shard='s1')
        second = enqueue_request(nonce='n2', shard='s2')
        self.assertEqual(
            command_id(first.show_id, first.inventory_epoch, first.inventory_mode,
                       first.principal, first.client_command_id),
            command_id(second.show_id, second.inventory_epoch, second.inventory_mode,
                       second.principal, second.client_command_id),
        )
        self.assertNotEqual(payload_sha256(first.payload()), payload_sha256(second.payload()))

    def test_scope_principal_and_client_id_all_change_identity(self):
        base = command_id(SHOW, EPOCH, MODE, 'buyer-1', 'c1')
        self.assertNotEqual(base, command_id('other-show', EPOCH, MODE, 'buyer-1', 'c1'))
        self.assertNotEqual(base, command_id(SHOW, EPOCH + 1, MODE, 'buyer-1', 'c1'))
        self.assertNotEqual(base, command_id(SHOW, EPOCH, 'ReservedSeating', 'buyer-1', 'c1'))
        self.assertNotEqual(base, command_id(SHOW, EPOCH, MODE, 'buyer-2', 'c1'))
        self.assertNotEqual(base, command_id(SHOW, EPOCH, MODE, 'buyer-1', 'c2'))

    def test_identity_inputs_are_validated(self):
        for bad in ('', None, 3):
            with self.assertRaises(ValueError):
                command_id(bad, EPOCH, MODE, 'buyer-1', 'c1')
        for bad in (-1, True, '3', None):
            with self.assertRaises(ValueError):
                command_id(SHOW, bad, MODE, 'buyer-1', 'c1')

    def test_position_identity_follows_the_ticket_not_the_routing(self):
        ticket = queue_ticket_id(SHOW, EPOCH, 'buyer-1', 'c1')
        self.assertEqual(position_identity(SHOW, EPOCH, ticket),
                         position_identity(SHOW, EPOCH, ticket))
        other = queue_ticket_id(SHOW, EPOCH, 'buyer-1', 'c2')
        self.assertNotEqual(position_identity(SHOW, EPOCH, ticket),
                            position_identity(SHOW, EPOCH, other))


class TokenTests(unittest.TestCase):
    def unsigned(self):
        return {
            'showId': SHOW, 'queueTicketId': 'qt-1', 'queuePositionIdentity': 'qpos-1',
            'inventoryEpoch': EPOCH, 'inventoryMode': MODE, 'authorityPlacementVersion': 1,
            'shardId': 's1', 'nonce': 'n1', 'issuedAt': 100, 'expiresAt': 1_100,
            'keyVersion': KEY_VERSION,
        }

    def test_field_names_are_exactly_the_contract_fields(self):
        self.assertEqual(tokens.TOKEN_FIELDS, (
            'showId', 'queueTicketId', 'queuePositionIdentity', 'inventoryEpoch',
            'inventoryMode', 'authorityPlacementVersion', 'shardId', 'nonce',
            'issuedAt', 'expiresAt', 'signature', 'keyVersion',
        ))

    def test_sign_verify_roundtrip(self):
        signed = tokens.sign(self.unsigned(), KEY, KEY_VERSION)
        self.assertTrue(tokens.verify(signed, KEY))
        self.assertFalse(tokens.verify(signed, b'other-key'))

    def test_tampered_body_fails_verification(self):
        signed = tokens.sign(self.unsigned(), KEY, KEY_VERSION)
        for field, value in (('shardId', 's2'), ('expiresAt', 9_999),
                             ('queuePositionIdentity', 'qpos-2'), ('nonce', 'n2')):
            tampered = dict(signed)
            tampered[field] = value
            self.assertFalse(tokens.verify(tampered, KEY), field)

    def test_missing_fields_and_bad_keys_are_refused(self):
        unsigned = self.unsigned()
        del unsigned['nonce']
        with self.assertRaises(tokens.TokenError):
            tokens.sign(unsigned, KEY, KEY_VERSION)
        with self.assertRaises(tokens.TokenError):
            tokens.sign(self.unsigned(), b'', KEY_VERSION)
        with self.assertRaises(tokens.TokenError):
            tokens.sign(self.unsigned(), KEY, '')
        mismatched = self.unsigned()
        mismatched['keyVersion'] = 'other'
        with self.assertRaises(tokens.TokenError):
            tokens.sign(mismatched, KEY, KEY_VERSION)
        self.assertFalse(tokens.verify(None, KEY))
        self.assertFalse(tokens.verify({}, KEY))
        self.assertFalse(tokens.verify(self.unsigned(), KEY))

    def test_token_id_is_stable_per_ticket_and_nonce(self):
        self.assertEqual(tokens.token_id('qt-1', 'n1'), tokens.token_id('qt-1', 'n1'))
        self.assertNotEqual(tokens.token_id('qt-1', 'n1'), tokens.token_id('qt-1', 'n2'))
        with self.assertRaises(tokens.TokenError):
            tokens.token_id('', 'n1')


class GroupCommitTests(unittest.TestCase):
    def entries(self, count, nbytes=10, enqueued_ms=0):
        return [{'nbytes': nbytes, 'enqueued_ms': enqueued_ms} for _ in range(count)]

    def test_empty_pending_proposes_nothing(self):
        self.assertEqual(propose_group([], max_count=4, max_bytes=100,
                                       max_wait_ms=50, now_ms=10), 0)

    def test_count_boundary_first(self):
        self.assertEqual(propose_group(self.entries(6), max_count=4, max_bytes=10_000,
                                       max_wait_ms=50, now_ms=10), 4)

    def test_bytes_boundary_first(self):
        self.assertEqual(propose_group(self.entries(6, nbytes=30), max_count=100,
                                       max_bytes=100, max_wait_ms=50, now_ms=10), 4)

    def test_max_wait_boundary_first_under_low_load(self):
        entries = self.entries(6, enqueued_ms=0)
        self.assertEqual(propose_group(entries, max_count=100, max_bytes=10_000,
                                       max_wait_ms=50, now_ms=50), 1)
        self.assertEqual(propose_group(entries, max_count=100, max_bytes=10_000,
                                       max_wait_ms=50, now_ms=49), 6)

    def test_under_all_bounds_proposes_everything(self):
        self.assertEqual(propose_group(self.entries(3), max_count=4, max_bytes=100,
                                       max_wait_ms=50, now_ms=10), 3)

    def test_bounds_and_entries_are_validated(self):
        for bad in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                propose_group(self.entries(1), max_count=bad, max_bytes=100,
                              max_wait_ms=50, now_ms=10)
        with self.assertRaises(ValueError):
            propose_group([{'nbytes': -1, 'enqueued_ms': 0}], max_count=4,
                          max_bytes=100, max_wait_ms=50, now_ms=10)


class EnqueueDecisionTests(unittest.TestCase):
    def test_success_issues_ticket_token_state_evidence_and_ledger(self):
        decision = enqueue_decision()
        self.assertEqual(decision.outcome, 'new_success')
        self.assertEqual(decision.budget_class, 'inflow')
        self.assertTrue(decision.writes)
        self.assertEqual(decision.ticket['seq'], 1)
        self.assertEqual(decision.issue_state['state'], ISSUED)
        self.assertEqual(decision.issue_state['seq'], 0)
        document = token_document(decision)
        self.assertEqual(set(document), set(tokens.TOKEN_FIELDS))
        self.assertTrue(tokens.verify(document, KEY))
        self.assertEqual(document['expiresAt'], 100 + limits().token_ttl_ms)
        self.assertEqual(document['queuePositionIdentity'], decision.ticket['position_identity'])
        evidence = decision.evidence
        for name in ('queue_ticket_id', 'position_identity', 'sequence', 'old_shard_id',
                     'shard_id', 'reason', 'issued_at_ms', 'expires_at_ms', 'outcome',
                     'command_id', 'at_ms'):
            self.assertIn(name, evidence)
        self.assertEqual(evidence['kind'], 'enqueue')
        self.assertEqual(evidence['sequence'], 1)
        entry_id, budget_class, nbytes, is_open = decision.ledger
        self.assertEqual((budget_class, is_open), ('inflow', True))
        self.assertEqual(nbytes, payload_nbytes(enqueue_request().payload()))
        self.assertTrue(entry_id.startswith('enq:'))

    def test_first_result_carries_the_false_flags(self):
        body = json.loads(enqueue_decision().first_result)
        self.assertTrue(body['localOnsaleFixtureOnly'])
        for name in ('protocolTruth', 'productionConformance', 'productionReadiness',
                     'productionEndpoint', 'fundsExecuted', 'chainWriter',
                     'delegatedExecution'):
            self.assertIs(body[name], False, name)

    def test_replay_returns_the_stored_first_result_and_writes_nothing(self):
        first = enqueue_decision()
        existing = {'payload_sha256': payload_sha256(enqueue_request().payload()),
                    'first_result': first.first_result}
        again = enqueue_decision(existing=existing)
        self.assertEqual(again.outcome, 'replayed')
        self.assertEqual(again.first_result, first.first_result)
        self.assertFalse(again.writes)

    def test_conflicting_payload_is_retained_once_as_observation(self):
        existing = {'payload_sha256': 'other-digest', 'first_result': 'stored'}
        snapshot = EnqueueSnapshot(existing=existing, config=dict(CONFIG), shard=shard_row())
        request = enqueue_request(nonce='different')
        first = decide_enqueue(snapshot, request, limits(), spec(), KEY, KEY_VERSION, 100)
        self.assertEqual(first.outcome, 'conflict_retained')
        self.assertEqual(first.first_result, 'stored')
        self.assertTrue(first.store_observation)
        self.assertEqual(first.budget_class, 'observation')
        retained = EnqueueSnapshot(existing=existing, conflict_retained=True,
                                   config=dict(CONFIG), shard=shard_row())
        second = decide_enqueue(retained, request, limits(), spec(), KEY, KEY_VERSION, 100)
        self.assertEqual(second.outcome, 'conflict_retained')
        self.assertFalse(second.writes)

    def test_inflow_budget_capacity_writes_nothing(self):
        tight = spec(inflow=ClassLimit(count=0, bytes=0, age_ms=0))
        snapshot = EnqueueSnapshot(config=dict(CONFIG), shard=shard_row())
        decision = decide_enqueue(snapshot, enqueue_request(), limits(), tight,
                                  KEY, KEY_VERSION, 100)
        self.assertEqual(decision.outcome, 'capacity')
        self.assertEqual(decision.budget_class, 'inflow')
        self.assertFalse(decision.writes)

    def test_outstanding_token_cap_is_capacity(self):
        decision = enqueue_decision(outstanding=limits().max_outstanding_tokens)
        self.assertEqual((decision.outcome, decision.capacity_reason),
                         ('capacity', 'outstanding_tokens'))
        self.assertFalse(decision.writes)

    def test_unknown_config_and_shard_are_business_rejections(self):
        decision = decide_enqueue(EnqueueSnapshot(shard=shard_row()), enqueue_request(),
                                  limits(), spec(), KEY, KEY_VERSION, 100)
        self.assertEqual((decision.outcome, decision.reason),
                         ('business_rejected', 'CONFIG_UNKNOWN'))
        self.assertTrue(decision.store_command)
        decision = decide_enqueue(EnqueueSnapshot(config=dict(CONFIG)), enqueue_request(),
                                  limits(), spec(), KEY, KEY_VERSION, 100)
        self.assertEqual((decision.outcome, decision.reason),
                         ('business_rejected', 'SHARD_UNKNOWN'))

    def test_mode_mismatch_is_config_unknown(self):
        snapshot = EnqueueSnapshot(config={'mode': 'ReservedSeating', 'placement_version': 1},
                                   shard=shard_row())
        decision = decide_enqueue(snapshot, enqueue_request(), limits(), spec(),
                                  KEY, KEY_VERSION, 100)
        self.assertEqual(decision.reason, 'CONFIG_UNKNOWN')


class AdmitDecisionTests(unittest.TestCase):
    def test_success_consumes_the_token_once_and_decrements_the_shard(self):
        enq = enqueue_decision()
        request = admit_request(token_document(enq))
        decision = decide_admit(admit_snapshot(enq), request, limits(), spec(), KEY, 200)
        self.assertEqual(decision.outcome, 'new_success')
        self.assertEqual(decision.terminal['state'], CONSUMED)
        self.assertEqual(decision.terminal['seq'], 1)
        self.assertEqual(decision.shard_decrement, (SHOW, EPOCH, 's1'))
        self.assertEqual(decision.session['command_id'],
                         command_id(SHOW, EPOCH, MODE, 'buyer-1', 'a1'))
        self.assertEqual(decision.evidence['kind'], 'admit')
        self.assertEqual(decision.evidence['sequence'], 2)
        self.assertEqual(decision.evidence['outcome'], 'new_success')
        entry_id, budget_class, _, is_open = decision.ledger
        self.assertEqual((budget_class, is_open), ('inflow', False))
        self.assertTrue(entry_id.startswith('adm:'))
        self.assertEqual(decision.ledger_close, enq.token['ledger_entry_id'])
        body = json.loads(decision.first_result)
        self.assertEqual(body['queuePositionIdentity'], enq.ticket['position_identity'])

    def test_replay_and_conflict_paths(self):
        enq = enqueue_decision()
        request = admit_request(token_document(enq))
        digest = payload_sha256(request.payload())
        replay = decide_admit(admit_snapshot(enq, existing={
            'payload_sha256': digest, 'first_result': 'stored'}),
            request, limits(), spec(), KEY, 200)
        self.assertEqual((replay.outcome, replay.first_result), ('replayed', 'stored'))
        self.assertFalse(replay.writes)
        conflict = decide_admit(admit_snapshot(enq, existing={
            'payload_sha256': 'other', 'first_result': 'stored'}),
            request, limits(), spec(), KEY, 200)
        self.assertEqual(conflict.outcome, 'conflict_retained')
        self.assertTrue(conflict.store_observation)

    def test_bad_signature_is_refused_before_any_state(self):
        enq = enqueue_decision()
        tampered = token_document(enq)
        tampered['shardId'] = 's2'
        decision = decide_admit(admit_snapshot(enq), admit_request(tampered),
                                limits(), spec(), KEY, 200)
        self.assertEqual((decision.outcome, decision.reason),
                         ('business_rejected', 'TOKEN_SIGNATURE'))

    def test_wrong_scope_binding_is_refused(self):
        enq = enqueue_decision()
        document = token_document(enq)
        for field, value in (('showId', 'other-show'), ('inventoryEpoch', EPOCH + 1),
                             ('inventoryMode', 'ReservedSeating'),
                             ('authorityPlacementVersion', 99)):
            rebinding = dict(document)
            rebinding[field] = value
            rebinding = tokens.sign(rebinding, KEY, KEY_VERSION)
            decision = decide_admit(admit_snapshot(enq), admit_request(rebinding),
                                    limits(), spec(), KEY, 200)
            self.assertEqual(decision.reason, 'TOKEN_BINDING', field)

    def test_unknown_token_and_presented_vs_stored_mismatch(self):
        enq = enqueue_decision()
        missing = dict(token_document(enq))
        missing['nonce'] = 'never-issued'
        missing = tokens.sign(missing, KEY, KEY_VERSION)
        decision = decide_admit(admit_snapshot(enq, token=None), admit_request(missing),
                                limits(), spec(), KEY, 200)
        self.assertEqual(decision.reason, 'TOKEN_UNKNOWN')
        altered = dict(token_document(enq))
        altered['expiresAt'] = 99_999
        altered = tokens.sign(altered, KEY, KEY_VERSION)
        decision = decide_admit(admit_snapshot(enq), admit_request(altered),
                                limits(), spec(), KEY, 200)
        self.assertEqual(decision.reason, 'TOKEN_BINDING')

    def test_ticket_ownership_is_checked(self):
        enq = enqueue_decision()
        decision = decide_admit(admit_snapshot(enq), admit_request(
            token_document(enq), principal='buyer-2'), limits(), spec(), KEY, 200)
        self.assertEqual(decision.reason, 'TOKEN_BINDING')

    def test_terminal_states_are_refused_with_their_reason(self):
        enq = enqueue_decision()
        for state, reason in ((CONSUMED, 'TOKEN_CONSUMED'), (REPLACED, 'TOKEN_REPLACED'),
                              (EXPIRED, 'TOKEN_EXPIRED')):
            decision = decide_admit(admit_snapshot(enq, token_state=state, token_state_seq=1),
                                    admit_request(token_document(enq)),
                                    limits(), spec(), KEY, 200)
            self.assertEqual(decision.reason, reason, state)
            self.assertTrue(decision.store_command)

    def test_time_expiry_and_queue_wait_are_refused(self):
        enq = enqueue_decision()
        decision = decide_admit(admit_snapshot(enq), admit_request(token_document(enq)),
                                limits(), spec(), KEY, 100 + limits().token_ttl_ms)
        self.assertEqual(decision.reason, 'TOKEN_EXPIRED')
        decision = decide_admit(admit_snapshot(enq), admit_request(token_document(enq)),
                                limits(max_queue_wait_ms=50), spec(), KEY, 200)
        self.assertEqual(decision.reason, 'QUEUE_WAIT')

    def test_sold_out_shard_yields_a_versioned_negative_hint(self):
        enq = enqueue_decision()
        decision = decide_admit(admit_snapshot(enq, shard=shard_row(remaining=0),
                                                 hint_version=2, commit_position=17),
                                admit_request(token_document(enq)),
                                limits(), spec(), KEY, 200)
        self.assertEqual(decision.reason, 'SHARD_SOLD_OUT')
        self.assertIsNone(decision.shard_decrement)
        hint = decision.sold_hint
        self.assertEqual(hint['version'], 3)
        self.assertEqual(hint['sourceCommitPosition'], 17)
        self.assertEqual(hint['expiresAtMs'], 200 + limits().hint_ttl_ms)
        self.assertEqual(hint['inventoryEpoch'], EPOCH)
        self.assertTrue(hint['negative'])
        self.assertEqual(decision.hint['shard_id'], 's1')

    def test_session_cap_is_capacity_without_writes(self):
        enq = enqueue_decision()
        decision = decide_admit(admit_snapshot(enq, session_count=limits().max_sessions),
                                admit_request(token_document(enq)), limits(), spec(), KEY, 200)
        self.assertEqual((decision.outcome, decision.capacity_reason), ('capacity', 'sessions'))
        self.assertFalse(decision.writes)

    def test_inflow_saturation_does_not_touch_the_token(self):
        enq = enqueue_decision()
        tight = spec(inflow=ClassLimit(count=0, bytes=0, age_ms=0))
        decision = decide_admit(admit_snapshot(enq), admit_request(token_document(enq)),
                                limits(), tight, KEY, 200)
        self.assertEqual(decision.outcome, 'capacity')
        self.assertFalse(decision.writes)


class ReissueDecisionTests(unittest.TestCase):
    def test_reissue_preserves_rank_and_consumes_no_capacity(self):
        enq = enqueue_decision()
        request = reissue_request(enq.ticket['queue_ticket_id'])
        decision = decide_reissue(reissue_snapshot(enq), request, limits(), spec(),
                                  KEY, KEY_VERSION, 300)
        self.assertEqual(decision.outcome, 'new_success')
        self.assertEqual(decision.budget_class, 'recovery')
        self.assertEqual(decision.terminal['state'], REPLACED)
        self.assertEqual(decision.terminal['reason'], 'reissued')
        self.assertEqual(decision.terminal['seq'], 1)
        document = token_document(decision)
        self.assertEqual(document['queueTicketId'], enq.ticket['queue_ticket_id'])
        self.assertEqual(document['queuePositionIdentity'], enq.ticket['position_identity'])
        self.assertEqual(document['shardId'], 's2')
        self.assertEqual(document['nonce'], 'n2')
        self.assertEqual(document['expiresAt'], 300 + limits().token_ttl_ms)
        self.assertTrue(tokens.verify(document, KEY))
        self.assertIsNone(decision.shard_decrement)
        self.assertEqual(decision.evidence['kind'], 'reissue')
        self.assertEqual(decision.evidence['old_shard_id'], 's1')
        self.assertEqual(decision.evidence['shard_id'], 's2')
        self.assertEqual(decision.evidence['sequence'], 2)
        entry_id, budget_class, _, is_open = decision.ledger
        self.assertEqual((budget_class, is_open), ('recovery', True))
        self.assertTrue(entry_id.startswith('rei:'))
        self.assertEqual(decision.ledger_close, enq.token['ledger_entry_id'])

    def test_old_and_new_tokens_share_one_ticket_identity(self):
        enq = enqueue_decision()
        decision = decide_reissue(reissue_snapshot(enq),
                                  reissue_request(enq.ticket['queue_ticket_id']),
                                  limits(), spec(), KEY, KEY_VERSION, 300)
        old = token_document(enq)
        new = token_document(decision)
        self.assertEqual(old['queueTicketId'], new['queueTicketId'])
        self.assertEqual(old['queuePositionIdentity'], new['queuePositionIdentity'])
        self.assertNotEqual(old['nonce'], new['nonce'])
        self.assertNotEqual(old['expiresAt'], new['expiresAt'])

    def test_replay_and_conflict_paths(self):
        enq = enqueue_decision()
        request = reissue_request(enq.ticket['queue_ticket_id'])
        digest = payload_sha256(request.payload())
        replay = decide_reissue(reissue_snapshot(enq, existing={
            'payload_sha256': digest, 'first_result': 'stored'}),
            request, limits(), spec(), KEY, KEY_VERSION, 300)
        self.assertEqual((replay.outcome, replay.first_result), ('replayed', 'stored'))
        self.assertFalse(replay.writes)
        conflict = decide_reissue(reissue_snapshot(enq, existing={
            'payload_sha256': 'other', 'first_result': 'stored'}),
            request, limits(), spec(), KEY, KEY_VERSION, 300)
        self.assertEqual(conflict.outcome, 'conflict_retained')
        self.assertEqual(conflict.budget_class, 'observation')

    def test_refusals_keep_the_recovery_class(self):
        enq = enqueue_decision()
        request = reissue_request(enq.ticket['queue_ticket_id'])
        cases = (
            (reissue_snapshot(enq, ticket=None), 'TICKET_UNKNOWN'),
            (reissue_snapshot(enq, old_token=None), 'TOKEN_UNKNOWN'),
            (reissue_snapshot(enq, old_state=CONSUMED, old_state_seq=1), 'REISSUE_NOT_ISSUED'),
            (reissue_snapshot(enq, new_shard=None), 'SHARD_UNKNOWN'),
            (reissue_snapshot(enq, new_token_exists=True), 'NONCE_REUSE'),
        )
        for snapshot, reason in cases:
            decision = decide_reissue(snapshot, request, limits(), spec(),
                                      KEY, KEY_VERSION, 300)
            self.assertEqual((decision.outcome, decision.reason),
                             ('business_rejected', reason))
            self.assertEqual(decision.budget_class, 'recovery', reason)
            self.assertTrue(decision.store_command)
        expired = decide_reissue(reissue_snapshot(enq), request, limits(), spec(),
                                 KEY, KEY_VERSION, 100 + limits().token_ttl_ms)
        self.assertEqual((expired.reason, expired.budget_class), ('TOKEN_EXPIRED', 'recovery'))
        reuse = decide_reissue(reissue_snapshot(enq),
                               reissue_request(enq.ticket['queue_ticket_id'],
                                               old_nonce='n1', new_nonce='n1'),
                               limits(), spec(), KEY, KEY_VERSION, 300)
        self.assertEqual(reuse.reason, 'NONCE_REUSE')

    def test_wrong_principal_cannot_reissue(self):
        enq = enqueue_decision()
        request = ReissueRequest(SHOW, EPOCH, MODE, 'buyer-2', 'r1',
                                 enq.ticket['queue_ticket_id'], 'n1', 'n2', 's2')
        decision = decide_reissue(reissue_snapshot(enq), request, limits(), spec(),
                                  KEY, KEY_VERSION, 300)
        self.assertEqual(decision.reason, 'TICKET_UNKNOWN')

    def test_recovery_budget_and_outstanding_cap_are_capacity(self):
        enq = enqueue_decision()
        request = reissue_request(enq.ticket['queue_ticket_id'])
        tight = spec(recovery=ClassLimit(count=0, bytes=0, age_ms=0))
        decision = decide_reissue(reissue_snapshot(enq), request, limits(), tight,
                                  KEY, KEY_VERSION, 300)
        self.assertEqual((decision.outcome, decision.budget_class), ('capacity', 'recovery'))
        self.assertFalse(decision.writes)
        capped = decide_reissue(reissue_snapshot(
            enq, outstanding=limits().max_outstanding_tokens),
            request, limits(), spec(), KEY, KEY_VERSION, 300)
        self.assertEqual((capped.outcome, capped.capacity_reason),
                         ('capacity', 'outstanding_tokens'))

    def test_inflow_saturation_does_not_starve_reissue(self):
        enq = enqueue_decision()
        tight = spec(inflow=ClassLimit(count=0, bytes=0, age_ms=0))
        decision = decide_reissue(reissue_snapshot(enq),
                                  reissue_request(enq.ticket['queue_ticket_id']),
                                  limits(), tight, KEY, KEY_VERSION, 300)
        self.assertEqual(decision.outcome, 'new_success')


class RouterTests(unittest.TestCase):
    def observation(self, shard, effective, hint=None):
        return {'shardId': shard, 'observedRemaining': effective,
                'outstandingUnexpiredTokens': 0, 'effectiveRemaining': effective,
                'negativeHint': hint}

    def test_strategy_and_rng_are_required_and_validated(self):
        import random
        with self.assertRaises(RouterError):
            HintRouter('uniform_random', random.Random(1))
        with self.assertRaises(RouterError):
            HintRouter('capacity_aware', None)
        self.assertEqual(STRATEGIES, ('capacity_aware', 'power_of_two'))

    def test_capacity_aware_picks_the_largest_effective_hint(self):
        import random
        router = HintRouter('capacity_aware', random.Random(7))
        observations = [self.observation('s1', 1), self.observation('s2', 5),
                        self.observation('s3', 3)]
        self.assertEqual(router.route(observations, inventory_epoch=EPOCH, now_ms=100), 's2')

    def test_power_of_two_stays_within_the_sampled_pair(self):
        import random
        router = HintRouter('power_of_two', random.Random(7))
        observations = [self.observation('s1', 1), self.observation('s2', 5),
                        self.observation('s3', 3)]
        for _ in range(20):
            chosen = router.route(observations, inventory_epoch=EPOCH, now_ms=100)
            self.assertIn(chosen, ('s1', 's2', 's3'))

    def test_valid_negative_hint_excludes_the_shard(self):
        import random
        hint = negative_hint_document(shard_id='s2', inventory_epoch=EPOCH, version=1,
                                      source_commit_position=1, expires_at_ms=900)
        observations = [self.observation('s1', 1), self.observation('s2', 5, hint)]
        for strategy in STRATEGIES:
            router = HintRouter(strategy, random.Random(3))
            self.assertEqual(router.route(observations, inventory_epoch=EPOCH, now_ms=100), 's1')

    def test_expired_or_wrong_epoch_hint_is_ignored_not_permanent(self):
        import random
        expired = negative_hint_document(shard_id='s2', inventory_epoch=EPOCH, version=1,
                                         source_commit_position=1, expires_at_ms=50)
        other_epoch = negative_hint_document(shard_id='s2', inventory_epoch=EPOCH + 1,
                                             version=1, source_commit_position=1,
                                             expires_at_ms=900)
        for hint in (expired, other_epoch):
            observations = [self.observation('s1', 1), self.observation('s2', 5, hint)]
            router = HintRouter('capacity_aware', random.Random(3))
            self.assertEqual(router.route(observations, inventory_epoch=EPOCH, now_ms=100), 's2')

    def test_no_routable_shard_returns_none(self):
        import random
        router = HintRouter('capacity_aware', random.Random(3))
        self.assertIsNone(router.route([self.observation('s1', 0)],
                                       inventory_epoch=EPOCH, now_ms=100))
        self.assertIsNone(router.route([], inventory_epoch=EPOCH, now_ms=100))

    def test_router_never_mutates_observations(self):
        import random
        observations = [self.observation('s1', 2), self.observation('s2', 3)]
        before = canonical_json(observations)
        for strategy in STRATEGIES:
            HintRouter(strategy, random.Random(5)).route(
                observations, inventory_epoch=EPOCH, now_ms=100)
        self.assertEqual(canonical_json(observations), before)


class VocabularyTests(unittest.TestCase):
    def test_outcome_vocabulary_matches_stage_five(self):
        self.assertEqual(OUTCOMES, (
            'replayed', 'conflict_retained', 'capacity', 'business_rejected',
            'new_success', 'unknown',
        ))

    def test_first_result_canonical_is_stable_json_with_flags(self):
        text = first_result_canonical('new_success', {'commandId': 'cmd-1'})
        self.assertEqual(text, canonical_json(json.loads(text)))
        self.assertIs(json.loads(text)['protocolTruth'], False)

    def test_usage_shape_is_the_durable_one(self):
        usage = Usage(count=1, nbytes=2, oldest_open_ms=3)
        self.assertEqual((usage.count, usage.nbytes, usage.oldest_open_ms), (1, 2, 3))


if __name__ == '__main__':
    unittest.main()
