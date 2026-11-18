"""Database-free checks for the stage-5 durable layer.

These need no PostgreSQL and no psycopg. Budget numbers here are test fixtures,
not product policy. Provider fields here are synthetic; no provider JSON field
name is built into the code under test.
"""

from __future__ import annotations

import hashlib
import inspect
import unittest
from pathlib import Path

from readiness.codec import canonical_json

from durable import model, normalize
from durable.budgets import CLASSES, BudgetError, BudgetSpec, ClassLimit
from durable.errors import AliasConflict, NormalizationError
from durable.model import Command, Snapshot, Usage, decide, payload_sha256
from durable.normalize import (
    DictAliasStore, ProviderItem, Scope, normalize_item, normalize_items, resolve_alias,
)

# Fixtures only. Not an approved limit of any kind.
FIX = ClassLimit(count=4, bytes=100_000, age_ms=1_000)
SCOPE = Scope('fixture-provider', 'fixture-account', 'fixture-env', 'fixture-profile-1')


def spec(**override):
    limits = {name: FIX for name in CLASSES}
    limits.update(override)
    return BudgetSpec(**limits)


def command(command_id='c1', slot='0', nonce='0', amount='10001', show='fixture-show'):
    return Command(command_id, show, slot, amount, 'buyer-1', nonce)


def item(key='k1', amount=10001, status='DONE', kind='capture', **extra):
    fields = dict(
        fact_key=key, kind=kind, amount_krw=amount, currency='KRW', method='fixture-method',
        status=status, occurred_at_text='2026-10-13T09:00:00', occurred_offset=None,
        operation={'provider': 'fixture-provider', 'account': 'fixture-account', 'operation': 'op-1'},
    )
    fields.update(extra)
    return ProviderItem(**fields)


class BudgetTests(unittest.TestCase):
    def test_budget_values_are_caller_supplied(self):
        with self.assertRaises(TypeError):
            BudgetSpec()
        with self.assertRaises(TypeError):
            ClassLimit()
        with self.assertRaises(TypeError):
            ClassLimit(count=1, bytes=1)
        limits = {name: FIX for name in CLASSES}
        del limits['cancel']
        with self.assertRaises(TypeError):
            BudgetSpec(**limits)
        with self.assertRaises(BudgetError):
            BudgetSpec(**{**{name: FIX for name in CLASSES}, 'cancel': 3})

    def test_values_must_be_non_negative_integers(self):
        for bad in (True, 1.5, '3', None, -1):
            with self.assertRaises(BudgetError):
                ClassLimit(count=bad, bytes=1, age_ms=1)
            with self.assertRaises(BudgetError):
                ClassLimit(count=1, bytes=bad, age_ms=1)
            with self.assertRaises(BudgetError):
                ClassLimit(count=1, bytes=1, age_ms=bad)

    def test_five_classes_are_named(self):
        self.assertEqual(CLASSES, ('inflow', 'completion', 'observation', 'cancel', 'recovery'))
        self.assertEqual(set(spec().document()), set(CLASSES))

    def test_check_reasons_and_order(self):
        budget = spec(inflow=ClassLimit(count=2, bytes=10, age_ms=5))
        check = budget.check
        self.assertEqual(check('inflow', used_count=1, used_bytes=5, oldest_open_ms=None, now_ms=0, extra_bytes=5), ('OK', None))
        self.assertEqual(check('inflow', used_count=2, used_bytes=0, oldest_open_ms=None, now_ms=0), ('CAPACITY', 'count'))
        self.assertEqual(check('inflow', used_count=1, used_bytes=6, oldest_open_ms=None, now_ms=0, extra_bytes=5), ('CAPACITY', 'bytes'))
        # count is tested before bytes, bytes before age
        self.assertEqual(check('inflow', used_count=2, used_bytes=99, oldest_open_ms=0, now_ms=99), ('CAPACITY', 'count'))
        self.assertEqual(check('inflow', used_count=0, used_bytes=99, oldest_open_ms=0, now_ms=99), ('CAPACITY', 'bytes'))
        self.assertEqual(check('inflow', used_count=0, used_bytes=0, oldest_open_ms=0, now_ms=6), ('CAPACITY', 'age'))
        # equality is acceptable for age
        self.assertEqual(check('inflow', used_count=0, used_bytes=0, oldest_open_ms=0, now_ms=5), ('OK', None))
        # a class with nothing open has no age
        self.assertEqual(check('inflow', used_count=0, used_bytes=0, oldest_open_ms=None, now_ms=10**9), ('OK', None))

    def test_unknown_class_is_refused(self):
        with self.assertRaises(BudgetError):
            spec().limit('wallet')

    def test_document_is_deterministic(self):
        self.assertEqual(canonical_json(spec().document()), canonical_json(spec().document()))
        other = spec(cancel=ClassLimit(count=9, bytes=9, age_ms=9))
        self.assertNotEqual(canonical_json(spec().document()), canonical_json(other.document()))


class DecisionTests(unittest.TestCase):
    def test_new_command_writes_the_whole_unit(self):
        decision = decide(Snapshot(), command(), spec(), 0)
        self.assertEqual(decision.outcome, 'new_success')
        self.assertTrue(all((
            decision.store_command, decision.store_slot, decision.store_order,
            decision.store_intent,
        )))
        self.assertFalse(decision.store_observation)
        self.assertEqual(decision.budget_class, 'inflow')
        self.assertEqual(decision.order_id, 'order-c1')
        self.assertEqual(decision.intent_id, 'intent-c1')

    def test_taken_slot_is_a_business_rejection_without_order(self):
        decision = decide(Snapshot(slot_holder='other'), command('c2'), spec(), 0)
        self.assertEqual(decision.outcome, 'business_rejected')
        self.assertTrue(decision.store_command)
        self.assertFalse(decision.store_slot or decision.store_order or decision.store_intent)

    def test_replay_returns_first_result_and_writes_nothing(self):
        first = decide(Snapshot(), command(), spec(), 0)
        existing = {'payload_sha256': payload_sha256(command()), 'first_result': first.first_result}
        replay = decide(Snapshot(existing=existing), command(), spec(), 0)
        self.assertEqual(replay.outcome, 'replayed')
        self.assertFalse(replay.writes)
        self.assertEqual(replay.first_result, first.first_result)

    def test_replay_is_free_when_inflow_is_full(self):
        full = {'inflow': Usage(count=4, nbytes=0)}
        existing = {'payload_sha256': payload_sha256(command()), 'first_result': 'R'}
        replay = decide(Snapshot(existing=existing, usage=full), command(), spec(), 0)
        self.assertEqual((replay.outcome, replay.first_result), ('replayed', 'R'))

    def test_conflicting_payload_is_retained_as_separate_evidence(self):
        existing = {'payload_sha256': payload_sha256(command()), 'first_result': 'R'}
        decision = decide(Snapshot(existing=existing), command(nonce='1'), spec(), 0)
        self.assertEqual(decision.outcome, 'conflict_retained')
        self.assertTrue(decision.store_observation)
        self.assertFalse(decision.store_command)
        self.assertEqual(decision.budget_class, 'observation')
        self.assertEqual(decision.first_result, 'R')
        again = decide(Snapshot(existing=existing, conflict_retained=True), command(nonce='1'), spec(), 0)
        self.assertEqual(again.outcome, 'conflict_retained')
        self.assertFalse(again.writes)

    def test_inflow_capacity_does_not_block_observation(self):
        usage = {'inflow': Usage(count=4)}
        refused = decide(Snapshot(usage=usage), command('c9'), spec(), 0)
        self.assertEqual((refused.outcome, refused.capacity_class, refused.capacity_reason),
                         ('capacity', 'inflow', 'count'))
        self.assertFalse(refused.writes)
        existing = {'payload_sha256': payload_sha256(command()), 'first_result': 'R'}
        admitted = decide(Snapshot(existing=existing, usage=usage), command(nonce='1'), spec(), 0)
        self.assertEqual(admitted.outcome, 'conflict_retained')
        self.assertTrue(admitted.writes)

    def test_observation_capacity_does_not_block_inflow(self):
        usage = {'observation': Usage(count=4)}
        existing = {'payload_sha256': payload_sha256(command()), 'first_result': 'R'}
        refused = decide(Snapshot(existing=existing, usage=usage), command(nonce='1'), spec(), 0)
        self.assertEqual((refused.outcome, refused.capacity_class), ('capacity', 'observation'))
        accepted = decide(Snapshot(usage=usage), command('c9'), spec(), 0)
        self.assertEqual(accepted.outcome, 'new_success')

    def test_age_of_the_oldest_open_entry_uses_the_callers_clock(self):
        usage = {'inflow': Usage(count=1, oldest_open_ms=100)}
        self.assertEqual(decide(Snapshot(usage=usage), command('n'), spec(), 1_100).outcome, 'new_success')
        late = decide(Snapshot(usage=usage), command('n'), spec(), 1_101)
        self.assertEqual((late.outcome, late.capacity_reason), ('capacity', 'age'))

    def test_u128_amounts_are_decimal_text(self):
        top = str(model.U128_MAX)
        self.assertEqual(command(amount=top).amount_u128, top)
        for bad in (str(model.U128_MAX + 1), '-1', '1.0', ' 1', '', '1e3', 5):
            with self.assertRaises(ValueError):
                command(amount=bad)

    def test_first_result_carries_only_false_production_flags(self):
        decision = decide(Snapshot(), command(), spec(), 0)
        body = __import__('json').loads(decision.first_result)
        for flag in ('protocolTruth', 'productionConformance', 'productionReadiness',
                     'productionEndpoint', 'fundsExecuted', 'chainWriter'):
            self.assertIs(body[flag], False)
        self.assertEqual(body['externalIntentKind'], 'FIXTURE_NOT_DISPATCHED')
        self.assertEqual(body['orderAmountU128'], '10001')

    def test_payload_digest_changes_with_the_payload(self):
        self.assertNotEqual(payload_sha256(command()), payload_sha256(command(nonce='1')))
        self.assertEqual(payload_sha256(command()), payload_sha256(command()))


class NormalizeTests(unittest.TestCase):
    def test_batch_yields_one_fact_and_identity_per_item(self):
        items = [item('k1'), item('k2', kind='cancel', amount=300, status='PARTIAL'), item('k3', amount=7)]
        facts = normalize_items(SCOPE, items)
        store = DictAliasStore()
        ids = [resolve_alias(store, f.scope_key, f.fact_key) for f in facts]
        self.assertEqual(len(set(ids)), 3)
        self.assertEqual(len({f.evidence_hash for f in facts}), 3)
        self.assertEqual([f.fact['kind'] for f in facts], ['capture', 'cancel', 'capture'])
        self.assertEqual(facts[1].fact['amountKrw'], 300)
        for event_item_id in ids:
            self.assertEqual(len(bytes.fromhex(event_item_id)), 16)

    def test_redelivery_of_the_same_fact_keeps_alias_and_hash(self):
        store = DictAliasStore()
        first = normalize_item(SCOPE, item())
        again = normalize_item(SCOPE, item())
        self.assertEqual(first.evidence_hash, again.evidence_hash)
        self.assertEqual(resolve_alias(store, first.scope_key, first.fact_key),
                         resolve_alias(store, again.scope_key, again.fact_key))
        self.assertEqual(len(store.by_key), 1)

    def test_evidence_hash_is_sha256_of_the_normalized_fact(self):
        fact = normalize_item(SCOPE, item())
        self.assertEqual(fact.evidence_hash, hashlib.sha256(canonical_json(fact.fact).encode()).hexdigest())

    def test_transmission_and_receive_data_are_not_inputs(self):
        self.assertEqual(
            set(inspect.signature(normalize_item).parameters), {'scope', 'item'},
        )
        fields = set(inspect.signature(ProviderItem).parameters)
        for banned in ('transmission_id', 'delivery_id', 'received_ms', 'retry_count', 'ack_time'):
            self.assertNotIn(banned, fields)
        self.assertEqual(
            set(normalize_item(SCOPE, item()).fact),
            {'amountKrw', 'currency', 'factKey', 'kind', 'method', 'occurredAtText',
             'occurredOffset', 'operation', 'scope', 'status'},
        )

    def test_changed_content_under_the_same_key_is_a_different_hash_not_a_new_identity(self):
        store = DictAliasStore()
        a = normalize_item(SCOPE, item('k1', amount=100))
        b = normalize_item(SCOPE, item('k1', amount=200))
        self.assertNotEqual(a.evidence_hash, b.evidence_hash)
        self.assertEqual(resolve_alias(store, a.scope_key, a.fact_key),
                         resolve_alias(store, b.scope_key, b.fact_key))

    def test_a_later_status_under_a_new_key_is_a_new_item(self):
        store = DictAliasStore()
        a = normalize_item(SCOPE, item('k1', status='DONE'))
        b = normalize_item(SCOPE, item('k1-cancel', status='CANCELED', kind='cancel'))
        self.assertNotEqual(resolve_alias(store, a.scope_key, a.fact_key),
                            resolve_alias(store, b.scope_key, b.fact_key))

    def test_amount_must_be_a_krw_integer(self):
        for bad in (100.0, 100.5, '100', True, False, None, -1, model.U128_MAX + 1):
            with self.assertRaises(NormalizationError, msg=repr(bad)):
                normalize_item(SCOPE, item(amount=bad))
        self.assertEqual(normalize_item(SCOPE, item(amount=0)).fact['amountKrw'], 0)
        self.assertEqual(normalize_item(SCOPE, item(amount=model.U128_MAX)).fact['amountKrw'], model.U128_MAX)

    def test_offsetless_time_is_not_given_a_zone(self):
        bare = normalize_item(SCOPE, item(occurred_at_text='2026-10-13T09:00:00', occurred_offset=None))
        self.assertEqual(bare.fact['occurredAtText'], '2026-10-13T09:00:00')
        self.assertIsNone(bare.fact['occurredOffset'])
        zoned = normalize_item(SCOPE, item(occurred_at_text='2026-10-13T09:00:00', occurred_offset='+09:00'))
        self.assertEqual(zoned.fact['occurredOffset'], '+09:00')
        self.assertNotEqual(bare.evidence_hash, zoned.evidence_hash)
        with self.assertRaises(NormalizationError):
            normalize_item(SCOPE, item(occurred_at_text=''))
        with self.assertRaises(NormalizationError):
            normalize_item(SCOPE, item(occurred_offset=9))

    def test_currency_method_and_status_stay_on_the_item(self):
        fact = normalize_item(SCOPE, item(currency='USD', method='m-2', status='S-9')).fact
        self.assertEqual((fact['currency'], fact['method'], fact['status']), ('USD', 'm-2', 'S-9'))

    def test_scope_separates_identities(self):
        store = DictAliasStore()
        other = Scope('fixture-provider', 'fixture-account', 'other-env', 'fixture-profile-1')
        a = normalize_item(SCOPE, item())
        b = normalize_item(other, item())
        self.assertNotEqual(a.scope_key, b.scope_key)
        self.assertNotEqual(a.evidence_hash, b.evidence_hash)
        self.assertEqual(len({resolve_alias(store, a.scope_key, 'k1'),
                              resolve_alias(store, b.scope_key, 'k1')}) , 2)
        with self.assertRaises(NormalizationError):
            Scope('p', '', 'e', 'v')

    def test_alias_collision_is_refused_and_the_first_mapping_stays(self):
        store = DictAliasStore()
        fixed = lambda _scope, _key: 'ab' * 16  # noqa: E731
        self.assertEqual(resolve_alias(store, 's', 'k1', fixed), 'ab' * 16)
        with self.assertRaises(AliasConflict):
            resolve_alias(store, 's', 'k2', fixed)
        self.assertEqual(store.get('s', 'k1'), 'ab' * 16)
        self.assertIsNone(store.get('s', 'k2'))
        self.assertEqual(resolve_alias(store, 's', 'k1', fixed), 'ab' * 16)

    def test_operation_reference_shape_is_checked(self):
        with self.assertRaises(NormalizationError):
            normalize_item(SCOPE, item(operation={'provider': 'p'}))
        self.assertIsNone(normalize_item(SCOPE, item(operation=None)).fact['operation'])

    def test_no_provider_json_field_name_is_built_in(self):
        source = Path(normalize.__file__).read_text()
        for name in ('paymentKey', 'transactionKey', 'lastTransactionKey', 'orderId', 'cancels'):
            self.assertNotIn(name, source)


if __name__ == '__main__':
    unittest.main()
