"""Seeded, source-informed loopback journeys; synthetic fixtures only.

FAILURE_FORMAT: UTF-8 JSON {"seed": integer, "steps": [Step._asdict(), ...]}.
Every step stores its concrete body (including the observed claim/holder), so
replay does not regenerate dependencies. ``restart`` is an explicit grammar
token; all other tokens are ordinary catalogue calls. A mismatch includes this
JSON after remove-one-step shrinking. To replay a saved JSON file locally::

    case = SeededJourneyDifferentialTests('test_seeded_journeys_match_shadow_host')
    seed, steps = load_failure(Path('failure.json').read_text())
    case._run_sequence(steps)

The generator uses a separate public FSM host only to capture dependent fixture
inputs. The differential driver creates another shadow and the HTTP host.
"""
from __future__ import annotations

from copy import deepcopy
import json
import random
from typing import NamedTuple

from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from readiness.conformance import (
    ADMISSION_EXPIRES, EXPIRES, PAY, PRICE, REQ, SALE_PAY, T0,
    resale_adopt_body, settlement_policy, show_kwargs,
)

SEEDS = (1, 2, 3, 5, 8, 13, 21, 34)
STEPS_PER_SEED = 60
LANES = ('reservation', 'resale', 'admission', 'settlement', 'credit')


class Step(NamedTuple):
    kind: str
    lane: str
    operation_id: str
    actor: str
    action: str
    body: dict


def lane_steps(seed):
    """Concrete command grammar. Numbers/roles are existing test fixtures."""
    def step(lane, op, **body):
        key = f'{seed}-{lane}-{op}'
        return Step('forward', lane, key, 'operator', lane + '_' + op,
                    dict(idempotency_key=key, **body))

    adopt = dict(resale_adopt_body(), reservation_id='reserve-1', quote_ref='quote-1')
    return {
        'reservation': [
            step('reservation', 'set_clock', subject_id='clock', now_ms=T0),
            step('reservation', 'register_show', show_id='show-1', **show_kwargs()),
            step('reservation', 'hold', reservation_id='reserve-1', show_id='show-1',
                 slot=0, buyer_role='buyer-1', expires_ms=EXPIRES),
            step('reservation', 'confirm', order_id='order-1', reservation_id='reserve-1',
                 amount=PRICE, quote_ref='quote-1'),
            step('reservation', 'observe_payment', order_id='order-1', payment_ref=PAY, amount=PRICE),
            step('reservation', 'bind_settlement', reservation_id='reserve-1', settlement_id='claim-1'),
            step('reservation', 'issue', issuance_id='issue-1', order_id='order-1'),
        ],
        'settlement': [
            step('settlement', 'initiate', settlement_id='claim-1', trade_id='trade-1',
                 gross=PRICE, debtor_role='fixture-merchant', policy=settlement_policy()),
            step('settlement', 'authorize', settlement_id='claim-1'),
            step('settlement', 'capture', settlement_id='claim-1'),
            step('settlement', 'commit', settlement_id='claim-1', movement_id='move-1',
                 gross=PRICE, amount=PRICE - 500, fee=500, tax=0, held=0, adjustment=0),
            step('settlement', 'distribute', settlement_id='claim-1', order=['platform', 'organizer']),
        ],
        'resale': [
            step('resale', 'set_clock', subject_id='clock', now_ms=T0),
            step('resale', 'adopt_issued', right_id='issue-1', **adopt),
            step('resale', 'list_resale', listing_id='list-1', right_id='issue-1', version=1,
                 seller_role='buyer-1', recipient_role='buyer-2', amount=PRICE,
                 expires_ms=EXPIRES, reservation_id='reserve-1'),
            step('resale', 'observe_resale_payment', listing_id='list-1', payment_ref=SALE_PAY,
                 amount=PRICE, buyer_role='buyer-2'),
            step('resale', 'accept_resale', transfer_id='transfer-1', listing_id='list-1'),
            step('resale', 'close', listing_id='list-1'),
        ],
        'admission': [
            step('admission', 'set_clock', subject_id='clock', now_ms=T0),
            step('admission', 'adopt_issued', right_id='issue-1', **adopt),
            step('admission', 'authorize_admission', admission_id='admit-1', right_id='issue-1',
                 version=1, holder_role='buyer-1', gate_role='gate-a', request=REQ,
                 expires_ms=ADMISSION_EXPIRES),
            step('admission', 'consume', consume_id='consume-1', right_id='issue-1',
                 version=1, gate_role='gate-a', request=REQ),
        ],
        'credit': [
            step('credit', 'offer', advance_id='adv-1', face={}, amount=8000,
                 beneficiary_role='fixture-label'),
            step('credit', 'approve', advance_id='adv-1'),
            step('credit', 'bind_settlement', advance_id='adv-1', settlement_id='claim-1'),
            step('credit', 'draw', advance_id='adv-1', draw_id='draw-1'),
            step('credit', 'repay', advance_id='adv-1', repay_id='rep-1', sequence=1, amount=8000),
            step('credit', 'close', advance_id='adv-1'),
        ],
    }


def generate(seed):
    """Random topological interleaving with guaranteed boundaries and mutations.

    Odd seeds transfer before entry (both presentations stay stale); even seeds
    consume before listing (later resale refuses the consumed ticket). Randomness
    changes lane order, replay order and conflict values, never coverage promises.
    """
    rng = random.Random(seed)
    lanes = lane_steps(seed)
    host = FsmHost()
    steps = []

    def emit(step):
        step = step._replace(body=deepcopy(step.body))
        steps.append(step)
        try:
            host.call(step.action, deepcopy(step.body))
        except FsmRejected:
            pass

    def fresh(step, kind):
        return step._replace(kind=kind, operation_id=step.operation_id + '-' + kind,
                             body=dict(step.body, idempotency_key=step.body['idempotency_key'] + '-' + kind))

    # Later commands before any prerequisites; rejected keys differ from the
    # later legitimate attempts because FSMs retain the first rejection too.
    for lane, index in [('reservation', 3), ('resale', 5), ('admission', 3),
                        ('settlement', 2), ('credit', 3)]:
        emit(fresh(lanes[lane][index], 'out_of_order'))

    # Cross-lane dependencies supplement each lane's own order.
    deps = {
        ('settlement', 0): {('reservation', 5)},
        ('reservation', 6): {('settlement', 3)},
        ('resale', 1): {('reservation', 6)},
        ('admission', 1): {('resale', 1)},
        ('credit', 0): {('settlement', 3)},
        ('settlement', 4): {('credit', 5)},
    }
    if seed % 2:
        deps[('admission', 2)] = {('resale', 5)}
    else:
        deps[('resale', 2)] = {('admission', 3)}
    positions = dict.fromkeys(lanes, 0)
    done = set()
    early_issue = False
    while any(positions[lane] < len(lanes[lane]) for lane in lanes):
        eligible = [lane for lane in lanes if positions[lane] < len(lanes[lane])
                    and deps.get((lane, positions[lane]), set()) <= done]
        lane = rng.choice(eligible)
        index = positions[lane]
        step = lanes[lane][index]
        if step.action == 'settlement_commit' and not early_issue:
            emit(fresh(lanes['reservation'][6], 'before_commit'))
            early_issue = True
        if step.action == 'credit_offer':
            step = step._replace(body=dict(step.body, face=host.machines['settlement'].view('claim-1')['claim']))
        if step.action == 'admission_authorize_admission':
            right = host.machines['resale'].view_right('issue-1')['right']
            step = step._replace(body=dict(step.body, version=right['version'], holder_role=right['holder_role']))
        emit(step)
        # Every machine gets each FSM replay kind, while its accepted first
        # entry is still available. Reuse operationId with a fresh body key.
        if index == 0:
            # Mutate the clock subject, preserving the fixture clock/window.
            field = {'settlement': 'gross', 'credit': 'beneficiary_role'}.get(lane, 'subject_id')
            value = step.body[field]
            changed = value + rng.randint(1, 3) if isinstance(value, int) else value + '-other'
            mutations = [
                step._replace(kind='replay_identical'),
                step._replace(kind='replay_conflict', body=dict(step.body, **{field: changed})),
                step._replace(kind='opid_reuse', body=dict(step.body, **{field: changed},
                    idempotency_key=step.body['idempotency_key'] + '-new')),
            ]
            rng.shuffle(mutations)
            for mutation in mutations:
                emit(mutation)
        done.add((lane, index))
        positions[lane] += 1

    clock = Step('core', 'core', f'{seed}-core-clock', 'operator', 'advance_clock',
                 {'domain': load_catalogue().domain, 'now': 50})
    core_steps = [
        clock, clock._replace(kind='replay_identical'),
        clock._replace(kind='core_opid_conflict', body=dict(clock.body, now=51)),
        clock._replace(kind='out_of_order', operation_id=clock.operation_id + '-early',
                       body=dict(clock.body, now=49)),
    ]
    # Preserve core order while placing its steps between FSM calls. Both
    # paths must leave the other path's observable state alone.
    positions = sorted(rng.sample(range(len(steps) + 1), len(core_steps)))
    for position, step in reversed(list(zip(positions, core_steps))):
        steps.insert(position, step)
    steps.append(Step('restart', 'all', '', '', '', {}))
    # Stale work sees empty machines after restart. Then reusing a previously
    # accepted clock/key is new work again, rather than a cached duplicate.
    for lane, index in [('reservation', 6), ('resale', 5), ('admission', 3),
                        ('settlement', 2), ('credit', 3)]:
        step = lanes[lane][index]
        steps.append(step._replace(kind='after_restart'))
    steps.append(lanes['reservation'][0]._replace(kind='restart_bootstrap'))
    assert len(steps) == STEPS_PER_SEED
    return steps


def shrink(steps, fails):
    """Deterministically remove one step until no single removal still fails.

    ``fails`` must recognize the same differential mismatch, not schema errors,
    unavailable infrastructure, or an arbitrary exception from replay.
    """
    current = list(steps)
    if not fails(current):
        return current
    index = 0
    while index < len(current):
        candidate = current[:index] + current[index + 1:]
        if fails(candidate):
            current = candidate
            index = 0
        else:
            index += 1
    return current


def dump_failure(seed, steps):
    return json.dumps({'seed': seed, 'steps': [step._asdict() for step in steps]},
                      sort_keys=True, indent=2) + '\n'


def load_failure(blob):
    record = json.loads(blob)
    return record['seed'], [Step(**row) for row in record['steps']]
