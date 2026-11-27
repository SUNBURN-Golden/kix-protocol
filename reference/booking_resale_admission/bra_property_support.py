"""Seeded property harness for the booking, resale and admission machines.

unittest discover collects test*.py only, so this module is not a test.
Labels and helpers are harness-local. They are not protocol commands.
Numbers here are synthetic fixtures, not product policy values.
The builder wrote this file. A run is not an independent PASS.

Choices come only from fixed seeds, tuples and sorted lists. There is no wall
clock read, urandom, uuid or set iteration; injected clock values are synthetic.

Oracles read the ledger first. The ledger is fed only by accepted results, never
by the machines' private invariant checks.
"""

from __future__ import annotations

import copy
import json
import random

from admission_fsm import AdmissionError, AdmissionMachine
from mock_gates import (
    ADMISSION_WINDOW_MS,
    CAPACITY_MAX,
    NON_CLAIMS,
    OFFER_WINDOW_MS,
    GateError,
    MockGates,
    _canonical,
)
from open_items import forbidden_commands
from resale_fsm import ResaleError, ResaleMachine
from reservation_fsm import ReservationError, ReservationMachine

SEEDS = (1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233)
STEPS = 80
CAPACITIES = (1, 2, 3, 4, 8, CAPACITY_MAX)
BPS_PAIRS = ((0, 0), (10000, 0), (5000, 5000), (1, 1), (2500, 7500), (0, 10000))
BUYERS = ("buyer-a", "buyer-b", "buyer-c")
GATES = ("gate-1", "gate-2")
ORGANIZER = "organizer-1"
SHOW = "show-1"
PRICE = 10_001
RESALE_CAP = 20_000
LISTING_AMOUNTS = (1, 5_000, PRICE, RESALE_CAP)
EXTERNAL_LABELS = tuple(sorted(forbidden_commands())) + ("pg_charge", "venue_scan_gate", "REVOCATION", "VENUE_IDENTITY")
UNSTORED = frozenset({"MOCK_INVARIANT", "IDEMPOTENCY_CONFLICT", "INVALID_JOURNAL"})


def rng(seed):
    return random.Random(seed)


def hex_ref(number):
    return format(number, "064x")


def codes(fn):
    try:
        fn()
    except (GateError, ReservationError, ResaleError, AdmissionError) as error:
        return error.code
    return None


def check_flags(test, result):
    for name in NON_CLAIMS:
        test.assertIs(result[name], False, name)
    test.assertIs(result.get("economic_finality_claimed", False), False)
    test.assertIs(result.get("funds_executed", False), False)


def check_show_policy(test, show):
    test.assertLessEqual(show["organizer_bps"] + show["platform_bps"], 10000)
    test.assertLessEqual(0, show["organizer_bps"])
    test.assertLessEqual(0, show["platform_bps"])


class Ledger:
    """Shadow record fed only by accepted results (properties a, b, c, d)."""

    def __init__(self, test, capacity):
        self.t = test
        self.capacity = capacity
        self.held = {}  # holder id -> [slot, "held" | "issued"]
        self.orders = {}  # order id -> holder id
        self.paid = {}  # order id -> payment ref
        self.rights = {}  # right id -> {slot, version, state, holder, holder_id}
        self.consumed = set()  # (right id, version)
        self.bumps = 0

    def occupy(self, holder, slot):
        self.t.assertNotIn(holder, self.held)
        for other, (taken, _kind) in sorted(self.held.items()):
            self.t.assertNotEqual(taken, slot, f"slot {slot} has two active holders: {other}, {holder}")
        self.held[holder] = [slot, "held"]
        self.check_exclusive()

    def release(self, holder):
        self.t.assertEqual(self.held[holder][1], "held")
        del self.held[holder]

    def bind(self, order, holder):
        self.orders[order] = holder

    def pay(self, order, ref):
        self.t.assertIn(order, self.orders)
        self.paid[order] = ref

    def issue(self, order, right, ref, holder_role, slot):
        self.t.assertIn(order, self.orders, "issued without a bound order")
        self.t.assertIn(order, self.paid, "issued without an observed payment fact")
        self.t.assertEqual(ref, self.paid[order])
        holder = self.orders[order]
        self.t.assertEqual(self.held[holder], [slot, "held"])
        self.held[holder][1] = "issued"
        self.add_right(right, slot, holder_role, holder)

    def adopt(self, right, slot, ref, holder_role, result):
        self.t.assertEqual(result["right"]["last_payment"], ref)
        self.occupy(right, slot)
        self.paid["adopt:" + right] = ref
        self.held[right][1] = "issued"
        self.add_right(right, slot, holder_role, right)

    def add_right(self, right, slot, holder_role, holder_id):
        self.t.assertNotIn(right, self.rights)
        for other, row in sorted(self.rights.items()):
            self.t.assertNotEqual(row["slot"], slot, f"slot {slot} has two issued rights: {other}, {right}")
        self.rights[right] = {"slot": slot, "version": 1, "state": "ACTIVE", "holder": holder_role, "holder_id": holder_id}
        self.check_exclusive()

    def presentation(self, right, version):
        row = self.rights[right]
        self.t.assertEqual(row["state"], "ACTIVE", "presentation accepted on a consumed right")
        self.t.assertEqual(version, row["version"], "stale-version presentation accepted")
        return row

    def consume(self, right, version, version_after):
        self.t.assertNotIn((right, version), self.consumed, "a right version was consumed twice")
        row = self.presentation(right, version)
        self.consumed.add((right, version))
        row["version"] = version + 1
        row["state"] = "CONSUMED"
        self.t.assertEqual(version_after, row["version"])
        self.bumps += 1

    def listing(self, right, version, amount, cap):
        row = self.rights[right]
        self.t.assertEqual(version, row["version"], "listing accepted for a stale version")
        self.t.assertLessEqual(amount, cap, "resale price exceeds the show's resale cap")

    def transfer(self, right, version, version_after, recipient, evidence):
        row = self.presentation(right, version)
        self.t.assertEqual(evidence["from_role"], row["holder"])
        self.t.assertEqual(evidence["to_role"], recipient)
        row["version"] = version + 1
        row["holder"] = recipient
        self.t.assertEqual(version_after, row["version"])
        parts = (evidence["organizer_due"], evidence["platform_due"], evidence["seller_due"])
        self.t.assertTrue(all(part >= 0 for part in parts))
        self.t.assertEqual(sum(parts), evidence["amount"])
        self.bumps += 1

    def check_exclusive(self):
        by_slot = {}
        for holder, (slot, _kind) in sorted(self.held.items()):
            by_slot.setdefault(slot, []).append(holder)
        for slot, holders in sorted(by_slot.items()):
            self.t.assertEqual(len(holders), 1, f"slot {slot}: {holders}")
        issued = [row["slot"] for _right, row in sorted(self.rights.items())]
        self.t.assertEqual(len(issued), len(set(issued)))
        self.t.assertLessEqual(len(self.held), self.capacity, "held plus issued exceeds capacity")

    def check_rows(self, rows):
        by_slot = {}
        for holder, (slot, kind) in sorted(self.held.items()):
            by_slot[slot] = (holder, kind)
        taken = 0
        for row in rows:
            slot = row["slot"]
            if row["state"] == "FREE":
                self.t.assertNotIn(slot, by_slot, f"slot {slot} free in view but held in ledger")
                continue
            taken += 1
            self.t.assertIn(slot, by_slot, f"slot {slot} occupied in view but not in ledger")
            holder, kind = by_slot[slot]
            if row["state"] == "RESERVED":
                self.t.assertEqual((kind, row["reservation_id"]), ("held", holder))
            else:
                self.t.assertEqual(kind, "issued")
                self.t.assertEqual(row["right_id"], self.rights_of_holder(holder))
        self.t.assertEqual(taken, len(by_slot))

    def rights_of_holder(self, holder):
        for right, row in sorted(self.rights.items()):
            if row["holder_id"] == holder:
                return right
        return None

    def check_rights(self, views):
        for right, view in sorted(views.items()):
            row = self.rights[right]
            self.t.assertEqual((view["state"], view["version"], view["holder_role"]), (row["state"], row["version"], row["holder"]), right)
            self.t.assertEqual(view["slot"], row["slot"])


def _mutate(subject, kwargs):
    changed = dict(kwargs)
    for name in sorted(changed):
        if name == "idempotency_key":
            continue
        value = changed[name]
        if value is None:
            changed[name] = "x"
        elif type(value) is bool:
            changed[name] = not value
        elif type(value) is int:
            changed[name] = value + 1
        elif type(value) is str and len(value) == 64 and all(char in "0123456789abcdef" for char in value):
            changed[name] = ("1" if value[0] == "0" else "0") + value[1:]
        elif type(value) is str:
            changed[name] = value + "x"
        elif type(value) is list:
            changed[name] = value + ["x"]
        else:
            continue
        return subject, changed
    return (subject + "x" if type(subject) is str else subject + 1), changed


def _normal(result):
    body = copy.deepcopy(result)
    body["duplicate"] = None
    body["applied"] = None
    return body


class Script:
    ERR = None
    KEYED = True
    EXTERNAL = True
    EXTERNAL_KW = False

    def __init__(self, test, seed, index):
        self.t = test
        self.seed = seed
        self.random = rng(seed)
        self.capacity = CAPACITIES[index % len(CAPACITIES)]
        self.organizer_bps, self.platform_bps = BPS_PAIRS[index % len(BPS_PAIRS)]
        self.ledger = Ledger(test, self.capacity)
        self.now = 0
        self.counter = 0
        self.refs = 0
        self.accepted = {}
        self.rejected = {}
        self.last = None
        self.history = []
        self.last_rejected = None
        self.digests = []
        self.states = []
        self.auth = {}

    # --- identifiers --------------------------------------------------
    def uid(self, prefix):
        self.counter += 1
        return f"{prefix}-{self.counter}"

    def ref(self):
        self.refs += 1
        return hex_ref(self.refs)

    def pick(self, items, prefer=()):
        pool = prefer if prefer and self.random.random() < 0.8 else items
        return self.random.choice(pool) if pool else None

    def need(self, value, stage):
        """With no entity to act on, usually run the stage that creates one."""
        if value is None and self.random.random() < 0.85:
            getattr(self, "do_" + stage)()
            return True
        return False

    def other_buyer(self, role):
        return self.random.choice([name for name in BUYERS if name != role])

    # --- hooks the subclasses fill -----------------------------------
    def snap(self):
        raise NotImplementedError

    def log(self):
        return None

    def on_accept(self, op, subject, kwargs, result):
        raise NotImplementedError

    def check(self):
        raise NotImplementedError

    def tally(self, table, key):
        table[key] = table.get(key, 0) + 1

    # --- command runner ----------------------------------------------
    def untouched(self, before, log, label):
        self.t.assertEqual(self.snap(), before, f"{label}: state changed")
        if log is not None:
            self.t.assertEqual(self.log(), log, f"{label}: journal changed")

    def run(self, op, subject, **kwargs):
        if self.KEYED:
            kwargs.setdefault("idempotency_key", self.uid("key"))
        before, log = self.snap(), self.log()
        try:
            result = getattr(self.target, op)(subject, **kwargs)
        except self.ERR as error:
            self.t.assertIs(type(error.code), str)
            self.untouched(before, log, f"{op} rejected {error.code}")
            self.tally(self.rejected, (op, error.code))
            if self.KEYED and error.code not in UNSTORED:
                self.last_rejected = (op, subject, dict(kwargs), error.code)
            return None
        check_flags(self.t, result)
        if result["duplicate"]:
            self.untouched(before, log, f"{op} duplicate")
            return result
        if log is not None:
            after = self.log()
            self.t.assertEqual(after[:-1], log)
            self.t.assertEqual(after[-1]["op"], op)
            self.digests.append(self.snap())
            self.states.append(self.machine.canonical_state())
        self.on_accept(op, subject, kwargs, result)
        self.tally(self.accepted, op)
        self.last = (op, subject, dict(kwargs), result)
        if self.KEYED:
            self.history.append(copy.deepcopy(self.last))
        self.check()
        return result

    # --- probes ------------------------------------------------------
    def probe_replay(self):
        if self.last is None:
            return
        # Replay an older receipt after intervening commands, rather than only
        # the latest response. FSM contracts 9.4 / 10.7 / 11.5 freeze the first
        # response even when current views have moved on.
        receipt = self.history[len(self.history) // 2] if self.KEYED else self.last
        op, subject, kwargs, first = receipt
        if not self.KEYED and op == "set_clock":
            return
        before, log = self.snap(), self.log()
        again = getattr(self.target, op)(subject, **kwargs)
        check_flags(self.t, again)
        self.t.assertIs(again["duplicate"], True)
        self.t.assertIsNone(again["applied"])
        if self.KEYED:
            self.t.assertEqual(_normal(again), _normal(first), f"{op}: repeat did not return the first result")
        elif "evidence" in first:
            self.t.assertEqual(again["evidence"], first["evidence"])
        self.untouched(before, log, f"{op} repeat")
        self.tally(self.accepted, "probe_replay")
        changed_subject, changed = _mutate(subject, kwargs)
        try:
            getattr(self.target, op)(changed_subject, **changed)
        except self.ERR as error:
            if self.KEYED:
                self.t.assertEqual(error.code, "IDEMPOTENCY_CONFLICT")
        else:
            self.t.fail(f"{op}: changed body accepted")
        self.untouched(before, log, f"{op} changed body")
        self.tally(self.accepted, "probe_changed_body")

    def probe_rejected_repeat(self):
        if self.last_rejected is None:
            return
        op, subject, kwargs, code = self.last_rejected
        before, log = self.snap(), self.log()
        self.t.assertEqual(codes(lambda: getattr(self.target, op)(subject, **kwargs)), code)
        self.untouched(before, log, f"{op} rejected repeat")
        self.tally(self.accepted, "probe_rejected_repeat")

    def probe_external(self):
        before, log = self.snap(), self.log()
        for label in EXTERNAL_LABELS:
            self.t.assertEqual(codes(lambda label=label: self.target.reject_external(label)), "EXTERNAL_UNSUPPORTED")
        self.t.assertEqual(codes(lambda: self.target.reject_external(" ")), "INVALID_ID")
        self.untouched(before, log, "reject_external")
        self.tally(self.accepted, "reject_external")

    # --- sequence ----------------------------------------------------
    def step(self):
        name = self.random.choice(self.WEIGHTS)
        getattr(self, "do_" + name)()
        roll = self.random.random()
        if roll < 0.25:
            self.probe_replay()
        elif roll < 0.35 and self.KEYED:
            self.probe_rejected_repeat()
        elif roll < 0.45 and self.EXTERNAL:
            self.probe_external()

    def play(self, steps=STEPS):
        if self.log() is not None:
            self.digests.append(self.snap())
            self.states.append(self.machine.canonical_state())
        self.setup()
        for step in range(steps):
            try:
                self.step()
            except AssertionError as error:
                raise AssertionError(f"{type(self).__name__} seed={self.seed} step={step}: {error}") from error
        self.finish()

    def setup(self):
        pass

    def finish(self):
        self.check()

    def clock(self, value):
        if self.KEYED:
            return self.run("set_clock", "clock", now_ms=value)
        return self.run("set_clock", value)

    def do_clock(self):
        if self.now > 0 and self.random.random() < 0.15:
            self.clock(self.now - 1)
            return
        value = self.now + self.random.choice((0, 0, 0, 1, 1_000, 1_000, 1_000, 30_000, 30_000, 300_000))
        if self.clock(value) is not None:
            self.now = value


class PresentationOps:
    """authorize and consume, shared by the gate, reservation and admission scripts."""

    AUTH_OP = "authorize_admission"
    CONSUME_OP = "consume"
    ISSUE_STAGE = "issue"

    def pick_right(self):
        rights = sorted(self.ledger.rights)
        live = [name for name in rights if self.ledger.rights[name]["state"] == "ACTIVE"]
        return self.pick(rights, live)

    def presented_version(self, right):
        row = self.ledger.rights.get(right)
        if row is None:
            return 1
        roll = self.random.random()
        if roll < 0.75:
            return row["version"]
        return max(0, row["version"] + self.random.choice((-1, 1)))

    def do_auth(self):
        right = self.pick_right()
        if self.need(right, self.ISSUE_STAGE):
            return
        right = right or "tix-none"
        row = self.ledger.rights.get(right)
        holder = row["holder"] if row and self.random.random() < 0.85 else self.random.choice(BUYERS)
        gate = self.random.choice(GATES) if self.random.random() < 0.95 else "gate-x"
        window = ADMISSION_WINDOW_MS + 1 if self.random.random() < 0.08 else self.random.choice((ADMISSION_WINDOW_MS, 30_000))
        kwargs = dict(
            right_id=right,
            version=self.presented_version(right),
            holder_role=holder,
            gate_role=gate,
            request=self.ref(),
            expires_ms=self.now + window,
        )
        if self.EXTERNAL_KW and self.random.random() < 0.08:
            kwargs["external_dependency"] = self.random.choice(("REVOCATION", "VENUE_IDENTITY"))
        self.run(self.AUTH_OP, self.uid("adm"), **kwargs)

    def do_consume(self):
        right = self.pick_right()
        if self.need(right, "auth"):
            return
        right = right or "tix-none"
        request, gate = self.auth.get(right, (self.ref(), self.random.choice(GATES)))
        if self.random.random() < 0.1:
            request = self.ref()
        if self.random.random() < 0.1:
            gate = self.random.choice(GATES)
        kwargs = dict(right_id=right, version=self.presented_version(right), gate_role=gate, request=request)
        if self.EXTERNAL_KW and self.random.random() < 0.08:
            kwargs["external_dependency"] = "VENUE_IDENTITY"
        self.run(self.CONSUME_OP, self.uid("use"), **kwargs)

    def accept_presentation(self, op, kwargs, result):
        if op == self.AUTH_OP:
            row = self.ledger.presentation(kwargs["right_id"], kwargs["version"])
            self.t.assertEqual(kwargs["holder_role"], row["holder"])
            self.t.assertIn(kwargs["gate_role"], GATES)
            self.auth[kwargs["right_id"]] = (kwargs["request"], kwargs["gate_role"])
            return True
        if op == self.CONSUME_OP:
            self.ledger.consume(kwargs["right_id"], kwargs["version"], result["evidence"]["version_after"])
            return True
        return False


class GateScript(PresentationOps, Script):
    """Drives MockGates directly. There is no digest, so the snapshot is the
    private state serialised. That is implementation-state characterization."""

    ERR = GateError
    KEYED = False
    EXTERNAL = False
    AUTH_OP = "authorize_admission"
    CONSUME_OP = "consume_admission"
    WEIGHTS = (
        ("clock",) * 2 + ("reserve",) * 5 + ("cancel",) + ("bind",) * 4 + ("abort",)
        + ("pay",) * 4 + ("issue",) * 4 + ("list",) * 3 + ("cancel_listing",) + ("pay_resale",) * 3
        + ("accept",) * 3 + ("auth",) * 3 + ("consume",) * 3
    )

    def __init__(self, test, seed, index, gates=None):
        super().__init__(test, seed, index)
        self.target = gates if gates is not None else MockGates()
        self.res = {}
        self.ordered = {}
        self.pending = {}
        self.listings = {}

    def snap(self):
        return _canonical(vars(self.target))

    def setup(self):
        result = self.target.register_show(
            SHOW,
            organizer_role=ORGANIZER,
            capacity=self.capacity,
            gate_roles=list(GATES),
            primary_price=PRICE,
            resale_cap=RESALE_CAP,
            resale_allowed=True,
            organizer_bps=self.organizer_bps,
            platform_bps=self.platform_bps,
        )
        check_flags(self.t, result)
        check_show_policy(self.t, result["show"])
        before = self.snap()
        self.t.assertEqual(
            codes(lambda: self.target.register_show(
                SHOW, organizer_role=ORGANIZER, capacity=self.capacity, gate_roles=list(GATES),
                primary_price=PRICE, resale_cap=RESALE_CAP, resale_allowed=True,
                organizer_bps=10000, platform_bps=1,
            )),
            "BPS_SUM",
        )
        self.t.assertEqual(self.snap(), before)

    def do_reserve(self):
        slot = self.random.randrange(self.capacity) if self.random.random() < 0.9 else self.capacity
        window = OFFER_WINDOW_MS + 1 if self.random.random() < 0.08 else self.random.choice((OFFER_WINDOW_MS, 300_000, 60_000))
        self.run("reserve_slot", self.uid("res"), show_id=SHOW, slot=slot, buyer_role=self.random.choice(BUYERS), expires_ms=self.now + window)

    def do_cancel(self):
        rid = self.pick(sorted(self.res), [r for r in sorted(self.res) if r not in self.ordered])
        if self.need(rid, "reserve"):
            return
        self.run("cancel_reservation", rid or "res-none")

    def do_bind(self):
        rid = self.pick(sorted(self.res), [r for r in sorted(self.res) if r not in self.ordered])
        if self.need(rid, "reserve"):
            return
        amount = PRICE if self.random.random() < 0.9 else PRICE + 1
        self.run("bind_order", self.uid("ord"), reservation_id=rid or "res-none", amount=amount)

    def do_abort(self):
        order = self.pick(sorted(self.pending), [o for o in sorted(self.pending) if o not in self.ledger.paid])
        if self.need(order, "bind"):
            return
        self.run("abort_order", order or "ord-none")

    def do_pay(self):
        order = self.pick(sorted(self.pending), [o for o in sorted(self.pending) if o not in self.ledger.paid])
        if self.need(order, "bind"):
            return
        amount = PRICE if self.random.random() < 0.9 else PRICE + 1
        self.run("observe_payment_fact", self.ref(), order_id=order or "ord-none", amount=amount)

    def do_issue(self):
        order = self.pick(sorted(self.pending), [o for o in sorted(self.pending) if o in self.ledger.paid])
        if self.need(order, "pay"):
            return
        self.run("issue", self.uid("tix"), order_id=order or "ord-none")

    def do_list(self):
        right = self.pick_right()
        if self.need(right, self.ISSUE_STAGE):
            return
        right = right or "tix-none"
        row = self.ledger.rights.get(right)
        seller = row["holder"] if row and self.random.random() < 0.9 else self.random.choice(BUYERS)
        recipient = self.other_buyer(seller) if self.random.random() < 0.9 else seller
        amount = RESALE_CAP + 1 if self.random.random() < 0.1 else self.random.choice(LISTING_AMOUNTS)
        self.run(
            "list_resale", self.uid("lst"), right_id=right, version=self.presented_version(right),
            seller_role=seller, recipient_role=recipient, amount=amount,
            expires_ms=self.now + self.random.choice((OFFER_WINDOW_MS, 100_000, 1_000)),
        )

    def do_cancel_listing(self):
        listing = self.pick(sorted(self.listings))
        if self.need(listing, "list"):
            return
        seller = self.listings[listing]["seller"] if listing else "buyer-a"
        self.run("cancel_listing", listing or "lst-none", seller_role=seller)

    def do_pay_resale(self):
        unpaid = [name for name in sorted(self.listings) if not self.listings[name]["paid"]]
        listing = self.pick(sorted(self.listings), unpaid)
        if self.need(listing, "list"):
            return
        amount = self.listings[listing]["amount"] if listing else PRICE
        if self.random.random() < 0.1:
            amount += 1
        self.run("observe_resale_payment", self.ref(), listing_id=listing or "lst-none", amount=amount)

    def do_accept(self):
        paid = [name for name in sorted(self.listings) if self.listings[name]["paid"]]
        listing = self.pick(sorted(self.listings), paid)
        if self.need(listing, "pay_resale"):
            return
        self.run("accept_resale", self.uid("xfer"), listing_id=listing or "lst-none")

    def on_accept(self, op, subject, kwargs, result):
        show = result.get("show")
        if show is not None:
            check_show_policy(self.t, show)
        if op == "set_clock":
            self.now = kwargs.get("now_ms", self.now)
        elif op == "reserve_slot":
            self.ledger.occupy(subject, kwargs["slot"])
            self.res[subject] = kwargs
        elif op in ("cancel_reservation", "abort_order"):
            holder = subject if op == "cancel_reservation" else self.ledger.orders[subject]
            self.ledger.release(holder)
            self.res.pop(holder, None)
            self.pending.pop(subject, None)
        elif op == "bind_order":
            self.ledger.bind(subject, kwargs["reservation_id"])
            self.ordered[kwargs["reservation_id"]] = subject
            self.pending[subject] = kwargs["reservation_id"]
        elif op == "observe_payment_fact":
            self.ledger.pay(kwargs["order_id"], subject)
        elif op == "issue":
            evidence = result["evidence"]
            holder = self.ledger.orders[kwargs["order_id"]]
            self.ledger.issue(kwargs["order_id"], subject, evidence["payment_ref"], evidence["holder_role"], evidence["slot"])
            self.pending.pop(kwargs["order_id"], None)
            self.t.assertEqual(self.res[holder]["slot"], evidence["slot"])
        elif op == "list_resale":
            self.ledger.listing(kwargs["right_id"], kwargs["version"], kwargs["amount"], RESALE_CAP)
            self.listings[subject] = {"right": kwargs["right_id"], "seller": kwargs["seller_role"], "recipient": kwargs["recipient_role"], "amount": kwargs["amount"], "paid": False}
        elif op == "cancel_listing":
            self.listings.pop(subject, None)
        elif op == "observe_resale_payment":
            self.listings[kwargs["listing_id"]]["paid"] = True
        elif op == "accept_resale":
            evidence = result["evidence"]
            listing = self.listings.pop(kwargs["listing_id"])
            self.ledger.transfer(listing["right"], evidence["version_after"] - 1, evidence["version_after"], listing["recipient"], evidence)
        else:
            self.t.assertTrue(self.accept_presentation(op, kwargs, result), op)

    def check(self):
        shown = self.target.view_show(SHOW)["show"]
        check_show_policy(self.t, shown)
        self.ledger.check_rows(shown["slots"])
        views = {}
        for right in sorted(self.ledger.rights):
            view = self.target.view_right(right)["right"]
            views[right] = view
        self.ledger.check_rights(views)


class ReservationScript(PresentationOps, Script):
    ERR = ReservationError
    WEIGHTS = (
        ("clock",) * 2 + ("hold",) * 5 + ("release",) + ("confirm",) * 4 + ("cancel",)
        + ("pay",) * 4 + ("issue",) * 4 + ("auth",) * 3 + ("consume",) * 3
    )

    def __init__(self, test, seed, index):
        super().__init__(test, seed, index)
        self.target = self.machine = ReservationMachine()
        self.res = {}
        self.orders = {}

    def snap(self):
        return self.machine.state_digest()

    def log(self):
        return self.machine.export_journal()

    def setup(self):
        kwargs = dict(
            organizer_role=ORGANIZER, capacity=self.capacity, gate_roles=list(GATES),
            primary_price=PRICE, resale_cap=RESALE_CAP, resale_allowed=True,
            organizer_bps=10000, platform_bps=1,
        )
        self.t.assertIsNone(self.run("register_show", SHOW, **kwargs))
        kwargs.update(organizer_bps=self.organizer_bps, platform_bps=self.platform_bps)
        self.t.assertIsNotNone(self.run("register_show", SHOW, **kwargs))

    def do_hold(self):
        slot = self.random.randrange(self.capacity) if self.random.random() < 0.9 else self.capacity
        window = OFFER_WINDOW_MS + 1 if self.random.random() < 0.08 else self.random.choice((OFFER_WINDOW_MS, 300_000, 60_000))
        self.run("hold", self.uid("res"), show_id=SHOW, slot=slot, buyer_role=self.random.choice(BUYERS), expires_ms=self.now + window)

    def open_reservations(self):
        return [r for r in sorted(self.res) if r not in self.orders.values()]

    def do_release(self):
        rid = self.pick(sorted(self.res), self.open_reservations())
        if self.need(rid, "hold"):
            return
        self.run("release", rid or "res-none")

    def do_confirm(self):
        rid = self.pick(sorted(self.res), self.open_reservations())
        if self.need(rid, "hold"):
            return
        amount = PRICE if self.random.random() < 0.9 else PRICE + 1
        self.run("confirm", self.uid("ord"), reservation_id=rid or "res-none", amount=amount)

    def do_cancel(self):
        order = self.pick(sorted(self.orders), [o for o in sorted(self.orders) if o not in self.ledger.paid])
        if self.need(order, "confirm"):
            return
        rid = self.orders[order] if order else "res-none"
        self.run("cancel", rid)

    def do_pay(self):
        order = self.pick(sorted(self.orders), [o for o in sorted(self.orders) if o not in self.ledger.paid])
        if self.need(order, "confirm"):
            return
        amount = PRICE if self.random.random() < 0.9 else PRICE + 1
        ref = self.ref()
        if self.random.random() < 0.1 and self.ledger.paid:
            ref = self.ledger.paid[sorted(self.ledger.paid)[0]]
        self.run("observe_payment", order or "ord-none", payment_ref=ref, amount=amount)

    def do_issue(self):
        order = self.pick(sorted(self.orders), [o for o in sorted(self.orders) if o in self.ledger.paid])
        if self.need(order, "pay"):
            return
        self.run("issue", self.uid("tix"), order_id=order or "ord-none")

    def on_accept(self, op, subject, kwargs, result):
        if op == "set_clock":
            return
        if op == "register_show":
            check_show_policy(self.t, result["show"])
        elif op == "hold":
            self.ledger.occupy(subject, kwargs["slot"])
            self.res[subject] = kwargs
        elif op == "release":
            self.ledger.release(subject)
            self.res.pop(subject)
        elif op == "confirm":
            self.ledger.bind(subject, kwargs["reservation_id"])
            self.orders[subject] = kwargs["reservation_id"]
        elif op == "cancel":
            self.ledger.release(subject)
            self.res.pop(subject)
            for order in sorted(self.orders):
                if self.orders[order] == subject:
                    del self.orders[order]
        elif op == "observe_payment":
            self.ledger.pay(subject, kwargs["payment_ref"])
        elif op == "issue":
            evidence = result["evidence"]
            self.ledger.issue(kwargs["order_id"], subject, evidence["payment_ref"], evidence["holder_role"], evidence["slot"])
        else:
            self.t.assertTrue(self.accept_presentation(op, kwargs, result), op)

    def check(self):
        shown = self.machine.view_show(SHOW)["show"]
        check_show_policy(self.t, shown)
        self.ledger.check_rows(shown["slots"])
        views = {}
        for rid in sorted(self.res):
            view = self.machine.view(rid)
            self.t.assertIs(view["funds_executed"], False)
            self.t.assertIs(view["economic_finality_claimed"], False)
            if view["phase"] in ("PAYMENT_NOTED", "ISSUED", "ADMISSION_AUTHORIZED", "CONSUMED"):
                self.t.assertIsNotNone(view["payment_ref"])
            if view["right"] is not None:
                views[view["right"]["right_id"]] = view["right"]
        self.ledger.check_rights(views)


class StandaloneScript(PresentationOps, Script):
    """Resale and admission machines share the adopt_issued entry."""

    ISSUE_STAGE = "adopt"

    def adopt_kwargs(self, slot=None):
        kwargs = dict(
            show_id=SHOW, organizer_role=ORGANIZER, capacity=self.capacity, gate_roles=list(GATES),
            primary_price=PRICE, resale_cap=RESALE_CAP, resale_allowed=True,
            organizer_bps=self.organizer_bps, platform_bps=self.platform_bps,
            slot=self.random.randrange(self.capacity) if slot is None else slot,
            buyer_role=self.random.choice(BUYERS), expires_ms=self.now + OFFER_WINDOW_MS,
            order_id=self.uid("ord"), amount=PRICE, payment_ref=self.ref(),
        )
        roll = self.random.random()
        if roll < 0.06:
            kwargs["slot"] = self.capacity
        elif roll < 0.12:
            kwargs["amount"] = PRICE + 1
        elif roll < 0.18:
            kwargs["organizer_bps"], kwargs["platform_bps"] = 10000, 1
        elif roll < 0.24:
            kwargs["payment_ref"] = "zz"
        elif roll < 0.30:
            kwargs["expires_ms"] = self.now + OFFER_WINDOW_MS + 1
        elif roll < 0.36:
            kwargs["resale_cap"] = RESALE_CAP + 1
        return kwargs

    def do_adopt(self):
        self.run("adopt_issued", self.uid("tix"), **self.adopt_kwargs())

    def accept_adopt(self, subject, kwargs, result):
        self.ledger.adopt(subject, kwargs["slot"], kwargs["payment_ref"], kwargs["buyer_role"], result)
        right = result["right"]
        self.t.assertEqual((right["state"], right["version"], right["last_amount"]), ("ACTIVE", 1, PRICE))


class ResaleScript(StandaloneScript):
    ERR = ResaleError
    WEIGHTS = (
        ("clock",) * 2 + ("adopt",) * 4 + ("list",) * 4 + ("hold_buy",) * 3 + ("release_hold",)
        + ("cancel_listing",) + ("pay",) * 3 + ("accept",) * 4 + ("close",)
    )

    def __init__(self, test, seed, index):
        super().__init__(test, seed, index)
        self.target = self.machine = ResaleMachine()
        self.listings = {}
        self.holds = {}

    def snap(self):
        return self.machine.state_digest()

    def log(self):
        return self.machine.export_journal()

    def do_list(self):
        right = self.pick_right()
        if self.need(right, self.ISSUE_STAGE):
            return
        right = right or "tix-none"
        row = self.ledger.rights.get(right)
        seller = row["holder"] if row and self.random.random() < 0.9 else self.random.choice(BUYERS)
        recipient = self.other_buyer(seller) if self.random.random() < 0.9 else seller
        amount = RESALE_CAP + 1 if self.random.random() < 0.1 else self.random.choice(LISTING_AMOUNTS)
        self.run(
            "list_resale", self.uid("lst"), right_id=right, version=self.presented_version(right),
            seller_role=seller, recipient_role=recipient, amount=amount,
            expires_ms=self.now + self.random.choice((OFFER_WINDOW_MS, 100_000, 1_000)),
        )

    def listing_phase(self, name):
        return self.machine.view(name)["phase"]

    def do_hold_buy(self):
        listed = [n for n in sorted(self.listings) if self.listing_phase(n) == "LISTED"]
        name = self.pick(sorted(self.listings), listed)
        if self.need(name, "list"):
            return
        buyer = self.listings[name]["recipient"] if name and self.random.random() < 0.9 else self.random.choice(BUYERS)
        self.run("hold_buy", self.uid("hold"), listing_id=name or "lst-none", buyer_role=buyer)

    def do_release_hold(self):
        hold = self.pick(sorted(self.holds))
        if self.need(hold, "hold_buy"):
            return
        buyer = self.listings[self.holds[hold]]["recipient"] if hold else "buyer-a"
        self.run("release_hold", hold or "hold-none", buyer_role=buyer)

    def do_cancel_listing(self):
        name = self.pick(sorted(self.listings))
        if self.need(name, "list"):
            return
        seller = self.listings[name]["seller"] if name else "buyer-a"
        self.run("cancel_listing", name or "lst-none", seller_role=seller)

    def do_pay(self):
        open_names = [n for n in sorted(self.listings) if self.listing_phase(n) in ("LISTED", "BUY_HELD")]
        name = self.pick(sorted(self.listings), open_names)
        if self.need(name, "list"):
            return
        amount = self.listings[name]["amount"] if name else PRICE
        if self.random.random() < 0.1:
            amount += 1
        self.run("observe_resale_payment", name or "lst-none", payment_ref=self.ref(), amount=amount)

    def do_accept(self):
        paid = [n for n in sorted(self.listings) if self.listing_phase(n) == "PAYMENT_NOTED"]
        name = self.pick(sorted(self.listings), paid)
        if self.need(name, "pay"):
            return
        self.run("accept_resale", self.uid("xfer"), listing_id=name or "lst-none")

    def do_close(self):
        done = [n for n in sorted(self.listings) if self.listing_phase(n) == "TRANSFERRED"]
        name = self.pick(sorted(self.listings), done)
        if self.need(name, "accept"):
            return
        self.run("close", name or "lst-none")

    def on_accept(self, op, subject, kwargs, result):
        if op == "set_clock":
            return
        if op == "adopt_issued":
            self.accept_adopt(subject, kwargs, result)
        elif op == "list_resale":
            self.ledger.listing(kwargs["right_id"], kwargs["version"], kwargs["amount"], RESALE_CAP)
            self.listings[subject] = {"right": kwargs["right_id"], "seller": kwargs["seller_role"], "recipient": kwargs["recipient_role"], "amount": kwargs["amount"]}
        elif op == "hold_buy":
            self.holds[subject] = kwargs["listing_id"]
        elif op == "release_hold":
            self.holds.pop(subject)
        elif op == "accept_resale":
            evidence = result["evidence"]
            listing = self.listings[kwargs["listing_id"]]
            old = self.ledger.rights[listing["right"]]
            old_holder, old_version = old["holder"], old["version"]
            self.ledger.transfer(listing["right"], old_version, evidence["version_after"], listing["recipient"], evidence)
            stale = self.machine.view_presentation(listing["right"], version=old_version, holder_role=old_holder)
            self.t.assertIs(stale["presentation"]["matches_current_right"], False, "stale presentation still matches")
            fresh = self.machine.view_presentation(listing["right"], version=old_version + 1, holder_role=listing["recipient"])
            self.t.assertIs(fresh["presentation"]["matches_current_right"], True)
        elif op in ("observe_resale_payment", "cancel_listing", "close"):
            pass
        else:
            self.t.fail(op)

    def check(self):
        shown = json.loads(self.machine.canonical_state())["shows"]
        rows = []
        for show in shown:
            check_show_policy(self.t, show)
            self.t.assertEqual(show["capacity"], self.capacity)
            rows = show["slots"]
        if shown:
            self.ledger.check_rows(rows)
        views = {}
        for right in sorted(self.ledger.rights):
            reply = self.machine.view_right(right)
            self.t.assertIs(reply["ticket"]["funds_executed"], False)
            views[right] = reply["right"]
        self.ledger.check_rights(views)
        self.t.assertLessEqual(len(self.ledger.rights), self.capacity)


class AdmissionScript(StandaloneScript):
    ERR = AdmissionError
    EXTERNAL_KW = True
    WEIGHTS = ("clock",) * 2 + ("adopt",) * 5 + ("auth",) * 5 + ("consume",) * 5

    def __init__(self, test, seed, index):
        super().__init__(test, seed, index)
        self.target = self.machine = AdmissionMachine()

    def snap(self):
        return self.machine.state_digest()

    def log(self):
        return self.machine.export_journal()

    def on_accept(self, op, subject, kwargs, result):
        if op == "set_clock":
            return
        if op == "adopt_issued":
            self.accept_adopt(subject, kwargs, result)
        else:
            self.t.assertIsNone(kwargs.get("external_dependency"), "an external dependency was accepted")
            self.t.assertTrue(self.accept_presentation(op, kwargs, result), op)

    def check(self):
        views = {}
        slots = []
        for right in sorted(self.ledger.rights):
            view = self.machine.view(right)
            self.t.assertEqual((view["slot_state"], view["slot_right_id"]), ("ISSUED", right))
            slots.append(view["slot"])
            views[right] = view
        self.t.assertEqual(len(slots), len(set(slots)))
        self.ledger.check_rights(views)
        self.t.assertLessEqual(len(slots), self.capacity)


def prefix_restore(test, script):
    """Contracts 9.4 / 10.7 / 11.5: state and digest agree at every prefix."""
    journal = script.machine.export_journal()
    test.assertEqual(len(script.digests), len(journal) + 1)
    test.assertEqual(len(script.states), len(journal) + 1)
    cls = type(script.machine)
    for k in range(len(journal) + 1):
        restored = cls.restore(journal[:k])
        test.assertEqual(restored.state_digest(), script.digests[k], f"prefix {k}")
        test.assertEqual(restored.canonical_state(), script.states[k], f"prefix {k}")
    test.assertEqual(cls.restore(journal).canonical_state(), script.machine.canonical_state())
