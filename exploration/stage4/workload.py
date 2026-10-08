"""Same synthetic business unit for every candidate. No chain writer."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from readiness.codec import canonical_json

from exploration.stage4.budget import (
    AMOUNT_FIXTURE,
    DEFAULT_BUDGET,
    SATURATION_BUDGET,
    SETTINGS,
    SHOW_ID,
    U128_MAX,
)

_AMOUNT = re.compile(r'^[0-9]{1,40}$')
WORKLOAD_ORDER = (
    'low-load-uniform',
    'uniform',
    'hot-seat',
    'same-command-retry',
    'history-growth',
    'saturation',
)


def validate_amount(text):
    if not isinstance(text, str) or _AMOUNT.fullmatch(text) is None:
        raise ValueError('amount must be a decimal string')
    if int(text) > U128_MAX:
        raise ValueError('amount exceeds u128')
    return text


@dataclass(frozen=True)
class Command:
    command_id: str
    slot: str
    amount_u128: str
    buyer: str
    payload_nonce: str

    def __post_init__(self):
        validate_amount(self.amount_u128)
        if not self.command_id or not self.slot or not self.buyer:
            raise ValueError('command identity')


def payload_body(command):
    return {
        'showId': SHOW_ID,
        'commandId': command.command_id,
        'slot': command.slot,
        'buyer': command.buyer,
        'amountU128': command.amount_u128,
        'nonce': command.payload_nonce,
        'chainWriter': False,
    }


def payload_canonical(command):
    return canonical_json(payload_body(command))


def payload_sha256(command):
    return hashlib.sha256(payload_canonical(command).encode('utf-8')).hexdigest()


def payload_nbytes(command):
    return len(payload_canonical(command).encode('utf-8'))


def first_result_body(outcome, command, *, order_id, intent_id):
    return {
        'explorationData': True,
        'protocolTruth': False,
        'productionConformance': False,
        'productionReadiness': False,
        'fundsExecuted': False,
        'chainWriter': False,
        'outcome': outcome,
        'commandId': command.command_id,
        'slot': command.slot if outcome == 'new_success' else None,
        'orderId': order_id,
        'orderAmountU128': command.amount_u128 if order_id else None,
        'externalIntentId': intent_id,
        'externalIntentKind': 'FIXTURE_NOT_DISPATCHED' if intent_id else None,
    }


def first_result_canonical(outcome, command, *, order_id, intent_id):
    return canonical_json(first_result_body(
        outcome, command, order_id=order_id, intent_id=intent_id,
    ))


@dataclass
class State:
    commands: dict
    slots: dict
    observation_count: int
    admitted_entries: int
    admitted_bytes: int
    max_entries: int
    max_bytes: int
    observation_budget: int


@dataclass
class Decision:
    outcome: str
    store_command: bool = False
    store_slot: bool = False
    store_observation: bool = False
    nbytes: int = 0
    first_result: str = ''
    order_id: str | None = None
    intent_id: str | None = None
    capacity_reason: str | None = None
    observation_id: str | None = None


def empty_state(budget):
    return State(
        commands={},
        slots={},
        observation_count=0,
        admitted_entries=0,
        admitted_bytes=0,
        max_entries=budget['max_entries'],
        max_bytes=budget['max_bytes'],
        observation_budget=budget['observation_budget'],
    )


def decide(state, command):
    """Pure admission decision. Replay and capacity do not add a business row."""
    digest = payload_sha256(command)
    existing = state.commands.get(command.command_id)
    if existing is not None:
        if existing['payload_sha256'] == digest:
            return Decision(outcome='replayed', first_result=existing['first_result'])
        nbytes = payload_nbytes(command)
        if state.observation_count >= state.observation_budget:
            return Decision(outcome='capacity', capacity_reason='observation_budget')
        if state.admitted_bytes + nbytes > state.max_bytes:
            return Decision(outcome='capacity', capacity_reason='byte_budget')
        return Decision(
            outcome='conflict_retained',
            store_observation=True,
            nbytes=nbytes,
            first_result=existing['first_result'],
            observation_id='obs-' + command.command_id + '-' + digest[:8],
        )
    nbytes = payload_nbytes(command)
    if state.admitted_entries >= state.max_entries or state.admitted_bytes + nbytes > state.max_bytes:
        reason = 'entry_budget' if state.admitted_entries >= state.max_entries else 'byte_budget'
        return Decision(outcome='capacity', capacity_reason=reason)
    if command.slot in state.slots:
        result = first_result_canonical('business_rejected', command, order_id=None, intent_id=None)
        return Decision(
            outcome='business_rejected',
            store_command=True,
            nbytes=nbytes,
            first_result=result,
        )
    order_id = 'order-' + command.command_id
    intent_id = 'intent-' + command.command_id
    result = first_result_canonical(
        'new_success', command, order_id=order_id, intent_id=intent_id,
    )
    return Decision(
        outcome='new_success',
        store_command=True,
        store_slot=True,
        nbytes=nbytes,
        first_result=result,
        order_id=order_id,
        intent_id=intent_id,
    )


def apply_memory(state, command, decision):
    if decision.store_command:
        state.commands[command.command_id] = {
            'payload_sha256': payload_sha256(command),
            'first_result': decision.first_result,
            'outcome': decision.outcome,
            'amount_u128': command.amount_u128,
            'admitted_bytes': decision.nbytes,
        }
        state.admitted_entries += 1
        state.admitted_bytes += decision.nbytes
    if decision.store_slot:
        state.slots[command.slot] = command.command_id
    if decision.store_observation:
        state.observation_count += 1
        state.admitted_bytes += decision.nbytes


def budget_for(name):
    if name == 'saturation':
        return dict(SATURATION_BUDGET)
    return dict(DEFAULT_BUDGET)


def commands_for(name):
    amount = AMOUNT_FIXTURE
    buyer = 'buyer-1'
    if name == 'low-load-uniform':
        return [Command('ll-%d' % i, str(i), amount, buyer, '0') for i in range(8)]
    if name == 'uniform':
        return [Command('uf-%d' % i, str(i % 4), amount, buyer, '0') for i in range(8)]
    if name == 'hot-seat':
        return [Command('hs-%d' % i, '0', amount, buyer, '0') for i in range(8)]
    if name == 'same-command-retry':
        command = Command('rt-0', '0', amount, buyer, '0')
        return [command for _ in range(5)]
    if name == 'history-growth':
        commands = [Command('hg-0', '0', amount, buyer, '0')]
        commands.extend(Command('hg-0', '0', amount, buyer, str(i)) for i in range(1, 6))
        return commands
    if name == 'saturation':
        commands = [Command('sa-%d' % i, str(i), amount, buyer, '0') for i in range(6)]
        commands.append(Command('sa-0', '0', amount, buyer, '0'))
        return commands
    raise KeyError(name)


def simulate(name):
    state = empty_state(budget_for(name))
    outcomes = []
    for command in commands_for(name):
        decision = decide(state, command)
        apply_memory(state, command, decision)
        outcomes.append(decision.outcome)
    return outcomes, state.admitted_entries, state.observation_count


def input_fingerprint():
    payload = {
        'budgets': {name: budget_for(name) for name in WORKLOAD_ORDER},
        'settings': SETTINGS,
        'workloads': {
            name: [command.__dict__ for command in commands_for(name)]
            for name in WORKLOAD_ORDER
        },
    }
    raw = canonical_json(payload).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def counts(outcomes):
    names = (
        'new_success', 'replayed', 'business_rejected', 'conflict_retained',
        'capacity', 'unknown', 'error',
    )
    return {name: outcomes.count(name) for name in names}


WARMUP_COMMANDS = (
    Command('warmup-0', '100', AMOUNT_FIXTURE, 'buyer-1', '0'),
    Command('warmup-1', '101', AMOUNT_FIXTURE, 'buyer-1', '0'),
)
U128_COMMAND = Command('u128-0', '9', str(U128_MAX), 'buyer-1', '0')
CRASH_COMMAND = Command('crash-0', '0', AMOUNT_FIXTURE, 'buyer-1', '0')

LOW_LOAD_NAME = 'low-load-uniform'
