"""Per-leg capture ledger: multiple intents, partial and multiple captures.

Admission reuses the unchanged stage-5 pure decision (``durable.model.decide``)
and the caller-supplied five-class ``BudgetSpec``. Command mapping:

- ``command_id`` = capture id (stable operation identity),
- ``show_id``    = ``order:group:leg`` scope,
- ``slot``       = capture id (each capture owns its slot, so several captures
  may share one leg; the leg's remaining capacity is checked separately),
- ``amount_u128``= decimal atoms (never narrowed),
- ``buyer``      = capture buyer, ``payload_nonce`` = caller nonce.

The external intent is ``FIXTURE_NOT_DISPATCHED``: no money moves here.

Semantics preserved from stage 5 / the locked kernel:

- replay returns the stored immutable first result before any availability
  check (a read-only stored-row probe decides this, so it also holds after a
  durable reopen when the process-local mirror is empty); a conflicting
  payload is retained once as observation evidence; capacity writes nothing;
- an over-capture attempt (confirmed + open + new > leg amount) is refused
  atomically with no writes, like capacity; for a new attempt the leg
  remainder is checked before the admission decision — on the durable path
  before the admission transaction — so it takes precedence over an
  inflow-capacity refusal; a later retry is a fresh attempt;
- a ``CONFIRMED`` completion moves the amount from open to confirmed; a
  ``FAILED`` completion releases the open reservation but retains the record;
  an ``UNKNOWN`` completion is retained and never releases the reservation;
- completion records are immutable: equal re-observation replays, a different
  one is refused without writes.

The ``cancel`` and ``recovery`` budget classes are required slots with no
writer in this revision (characterization, as in the onsale node). Inflow
entries stay open, exactly as the stage-5 unit leaves them; completion entries
are closed. The optional ``DurableCaptureLedger`` persists admission through
the unchanged ``DurableUnit`` (local pinned PostgreSQL); leg accounting and
completion records remain process-local fixture bookkeeping in this revision.
"""
import copy

from durable.budgets import BudgetSpec
from durable.model import (
    Command, Decision, Snapshot, Usage, decide, payload_nbytes, payload_sha256,
)
from readiness.codec import canonical_json

from reference.economics import EVIDENCE_CLASS, FLAGS, EconomicsLocalError

COMPLETION_OUTCOMES = ('CONFIRMED', 'FAILED', 'UNKNOWN')


def _result(outcome, **extra):
    result = {'outcome': outcome, 'evidenceClass': EVIDENCE_CLASS}
    result.update(FLAGS)
    result.update(extra)
    return result


class CaptureLedger:
    """In-memory capture admission + leg accounting over the pure decision."""

    def __init__(self, budgets):
        if not isinstance(budgets, BudgetSpec):
            raise EconomicsLocalError('BUDGET_SPEC_REQUIRED')
        self._budgets = budgets
        self._legs = {}        # (order, group, leg) -> amount int
        self._leg_state = {}   # key -> {'confirmed': int, 'open': int}
        self._commands = {}    # capture_id -> admission row
        self._slots = {}       # (show_id, slot) -> capture_id
        self._conflicts = {}   # (capture_id, digest) -> observation evidence
        self._completions = {}  # capture_id -> immutable completion record
        self._usage = {}       # class -> Usage
        self._open = {}        # class -> {entry_id: now_ms}

    # -- legs -------------------------------------------------------------
    def add_leg(self, order_id, group_id, leg_id, amount):
        key = (order_id, group_id, leg_id)
        if key in self._legs:
            raise EconomicsLocalError('LEG_EXISTS')
        if type(amount) is not int or isinstance(amount, bool) or amount <= 0:
            raise EconomicsLocalError('LEG_AMOUNT_INVALID')
        self._legs[key] = amount
        self._leg_state[key] = {'confirmed': 0, 'open': 0}

    def leg_view(self, order_id, group_id, leg_id):
        key = (order_id, group_id, leg_id)
        if key not in self._legs:
            raise EconomicsLocalError('UNKNOWN_LEG')
        state = self._leg_state[key]
        amount = self._legs[key]
        return {'orderId': order_id, 'groupId': group_id, 'legId': leg_id,
                'amount': amount, 'confirmed': state['confirmed'],
                'open': state['open'],
                'remaining': amount - state['confirmed'] - state['open']}

    def fully_captured(self, order_id, group_id, leg_id):
        view = self.leg_view(order_id, group_id, leg_id)
        return view['confirmed'] == view['amount']

    # -- admission ----------------------------------------------------------
    def _has_admission(self, capture_id):
        """Read-only probe for a stored admission row. Replay and conflict
        resolution must see it before any availability check runs."""
        return capture_id in self._commands

    def _admit(self, command, snapshot, now_ms):
        return decide(snapshot, command, self._budgets, now_ms)

    def _usage_of(self, budget_class):
        return self._usage.get(budget_class) or Usage()

    def _snapshot(self, command):
        digest = payload_sha256(command)
        return Snapshot(
            existing=self._commands.get(command.command_id),
            slot_holder=self._slots.get((command.show_id, command.slot)),
            conflict_retained=(command.command_id, digest) in self._conflicts,
            usage={name: copy.copy(usage) for name, usage in self._usage.items()},
        )

    def submit(self, *, order_id, group_id, leg_id, capture_id, amount,
               buyer, nonce, now_ms):
        key = (order_id, group_id, leg_id)
        if type(now_ms) is not int or isinstance(now_ms, bool) or now_ms < 0:
            raise EconomicsLocalError('CAPTURE_TIME_INVALID')
        if type(amount) is not int or isinstance(amount, bool) or amount <= 0:
            raise EconomicsLocalError('CAPTURE_AMOUNT_INVALID')
        try:
            command = Command(command_id=capture_id, show_id=':'.join(key),
                              slot=capture_id, amount_u128=str(amount),
                              buyer=buyer, payload_nonce=nonce)
        except ValueError:
            raise EconomicsLocalError('CAPTURE_COMMAND_INVALID') from None
        if not self._has_admission(capture_id):
            # New-attempt availability checks never run before replay: a
            # stored admission row means the decision below is a replay or
            # conflict, never a new admission.
            if key not in self._legs:
                raise EconomicsLocalError('UNKNOWN_LEG')
            state = self._leg_state[key]
            if amount + state['confirmed'] + state['open'] > self._legs[key]:
                # Atomic refusal before any write, exactly like capacity.
                # This must precede _admit: on the durable path admission
                # is a committed transaction, so checking afterwards would
                # refuse after a write and poison the capture id's retry.
                raise EconomicsLocalError('OVER_CAPTURE')
        snapshot = self._snapshot(command)
        decision = self._admit(command, snapshot, now_ms)
        if decision.outcome in ('unknown', 'error'):
            return _result(decision.outcome, captureId=capture_id,
                           error=getattr(decision, 'capacity_reason', None))
        self._apply(command, decision, key, amount, now_ms)
        return _result(decision.outcome, captureId=capture_id,
                       first_result=decision.first_result,
                       order_id=decision.order_id, intent_id=decision.intent_id,
                       capacity_class=decision.capacity_class,
                       capacity_reason=decision.capacity_reason)

    def _apply(self, command, decision, key, amount, now_ms):
        digest = payload_sha256(command)
        if decision.store_command:
            self._commands[command.command_id] = {
                'payload_sha256': digest,
                'first_result': decision.first_result,
                'outcome': decision.outcome,
                'key': key if decision.outcome == 'new_success' else None,
                'amount': amount,
            }
            self._bump(decision.budget_class, decision.nbytes, now_ms,
                       is_open=decision.store_intent,
                       entry_id='cmd:' + command.command_id)
        if decision.store_slot:
            self._slots[(command.show_id, command.slot)] = command.command_id
        if decision.store_order and decision.outcome == 'new_success':
            self._leg_state[key]['open'] += amount
        if decision.store_observation:
            self._conflicts[(command.command_id, digest)] = {
                'observation_id': decision.observation_id,
                'nbytes': decision.nbytes, 'now_ms': now_ms,
            }
            self._bump('observation', decision.nbytes, now_ms, is_open=False,
                       entry_id='obs:' + decision.observation_id)

    def _bump(self, budget_class, nbytes, now_ms, *, is_open, entry_id):
        usage = self._usage.setdefault(budget_class, Usage())
        usage.count += 1
        usage.nbytes += nbytes
        if is_open:
            opened = self._open.setdefault(budget_class, {})
            opened[entry_id] = now_ms
            usage.oldest_open_ms = min(opened.values())

    # -- completion ---------------------------------------------------------
    def complete(self, capture_id, *, outcome, source_id, now_ms):
        row = self._commands.get(capture_id)
        if row is None or row['outcome'] != 'new_success':
            raise EconomicsLocalError('CAPTURE_NOT_ADMITTED')
        if outcome not in COMPLETION_OUTCOMES:
            raise EconomicsLocalError('COMPLETION_OUTCOME_INVALID')
        if type(source_id) is not str or not source_id.strip():
            raise EconomicsLocalError('COMPLETION_SOURCE_INVALID')
        if type(now_ms) is not int or isinstance(now_ms, bool) or now_ms < 0:
            raise EconomicsLocalError('COMPLETION_TIME_INVALID')
        record = {'captureId': capture_id, 'outcome': outcome,
                  'sourceId': source_id, 'nowMs': now_ms}
        existing = self._completions.get(capture_id)
        if existing is not None:
            if (existing['outcome'], existing['sourceId']) == (outcome, source_id):
                return _result('replayed', completion=copy.deepcopy(existing))
            raise EconomicsLocalError('COMPLETION_BINDING_CONFLICT')
        nbytes = len(canonical_json(record).encode('utf-8'))
        usage = self._usage_of('completion')
        code, reason = self._budgets.check(
            'completion', used_count=usage.count, used_bytes=usage.nbytes,
            oldest_open_ms=usage.oldest_open_ms, now_ms=now_ms,
            extra_bytes=nbytes)
        if code != 'OK':
            return _result('capacity', capacity_class='completion',
                           capacity_reason=reason)
        self._completions[capture_id] = record
        self._bump('completion', nbytes, now_ms, is_open=False,
                   entry_id='completion:' + capture_id)
        key = row['key']
        state = self._leg_state[key]
        if outcome == 'CONFIRMED':
            state['open'] -= row['amount']
            state['confirmed'] += row['amount']
        elif outcome == 'FAILED':
            state['open'] -= row['amount']
        # UNKNOWN: the reservation is retained; nothing is released.
        return _result('completed', completion=copy.deepcopy(record))

    # -- views --------------------------------------------------------------
    def view(self):
        return {
            'evidenceClass': EVIDENCE_CLASS,
            **FLAGS,
            'budgets': self._budgets.document(),
            'legs': [self.leg_view(*key) for key in sorted(self._legs)],
            'captures': {capture_id: copy.deepcopy(row)
                         for capture_id, row in sorted(self._commands.items())},
            'completions': copy.deepcopy(self._completions),
            'conflicts': [{'captureId': capture_id, 'payloadSha256': digest,
                           **copy.deepcopy(evidence)}
                          for (capture_id, digest), evidence
                          in sorted(self._conflicts.items())],
            'usage': {name: {'count': usage.count, 'bytes': usage.nbytes,
                             'oldestOpenMs': usage.oldest_open_ms}
                      for name, usage in sorted(self._usage.items())},
        }


class DurableCaptureLedger(CaptureLedger):
    """Capture admission persisted by the unchanged stage-5 DurableUnit.

    The unit owns identity, payload sha256, first result, slot, intent and the
    budget ledger in one serializable transaction on the pinned local
    PostgreSQL. Leg accounting and completion records stay process-local in
    this revision; after a reopen, admission replay still returns the stored
    first result from the database. New-attempt preconditions (leg existence
    and remainder) are checked before the unit's admission transaction; the
    stored-row probe is read-only, so a refused attempt starts no transaction
    that writes.
    """

    def __init__(self, unit):
        super().__init__(unit.spec)
        self._unit = unit

    def _has_admission(self, capture_id):
        # The database is authoritative: after a reopen the process-local
        # mirror is empty, but a stored admission still replays before any
        # availability check. read_amount is the unit's read-only probe.
        return self._unit.read_amount(capture_id) is not None

    def _admit(self, command, snapshot, now_ms):
        result = self._unit.apply(command, now_ms)
        outcome = result['outcome']
        if outcome in ('unknown', 'error'):
            return Decision(outcome=outcome,
                            capacity_reason=result.get('error'))
        digest = payload_sha256(command)
        return Decision(
            outcome=outcome,
            budget_class='inflow' if outcome in ('new_success', 'business_rejected') else (
                'observation' if outcome == 'conflict_retained' else None),
            store_command=outcome in ('new_success', 'business_rejected'),
            store_slot=outcome == 'new_success',
            store_order=outcome == 'new_success',
            store_intent=outcome == 'new_success',
            store_observation=(outcome == 'conflict_retained'
                               and not snapshot.conflict_retained),
            nbytes=payload_nbytes(command),
            first_result=result['first_result'],
            order_id=result['order_id'],
            intent_id=result['intent_id'],
            observation_id=('obs-' + command.command_id + '-' + digest
                            if outcome == 'conflict_retained' else None),
            capacity_class=result['capacity_class'],
            capacity_reason=result['capacity_reason'],
        )