"""Author-side seeded property checks for the booking, resale and admission gates.

Oracles come from docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md (sections 2-5,
9.3-9.6, 10.6-10.8, 11.4-11.6) and are fed only by accepted results, not by the
machines' private invariant checks. Sequences use fixed seeds, existing commands
and synthetic fixtures. Fixture numbers are not policy values. The builder wrote
this file. A pass is not an independent PASS, and MOCK_GATE_ONLY stays the
provenance: no chain currentness, no durable reservation, no real payment fact.

Properties, as lettered in the validation record:
(a) one active holder and one issued right per slot, held plus issued <= capacity
(b) issuance needs a bound order with an observed payment fact
(c) one consume per right version, version bumps, stale presentation rejected
(d) resale price <= resale cap, organizer + platform bps <= 10000
(e) a raising command leaves the state unchanged
(f) restore reproduces every prefix; same key repeats the first result
(g) reject_external leaves the journal unchanged
"""

from __future__ import annotations

import unittest
from unittest import mock

import mock_gates
from admission_fsm import AdmissionMachine
from bra_property_support import (
    BUYERS,
    EXTERNAL_LABELS,
    GATES,
    ORGANIZER,
    PRICE,
    RESALE_CAP,
    SEEDS,
    SHOW,
    AdmissionScript,
    GateScript,
    ResaleScript,
    ReservationScript,
    codes,
    hex_ref,
    prefix_restore,
)
from mock_gates import GateError, MockGates
from resale_fsm import ResaleMachine
from reservation_fsm import ReservationError, ReservationMachine


def _total(scripts, table, name):
    return sum(count for script in scripts for key, count in getattr(script, table).items() if (key if table == "accepted" else key[0]) == name)


def _rejections(scripts, code):
    return sum(count for script in scripts for (_op, got), count in script.rejected.items() if got == code)


class SeededSequenceTests(unittest.TestCase):
    def play(self, cls):
        scripts = []
        for index, seed in enumerate(SEEDS):
            script = cls(self, seed, index)
            script.play()
            scripts.append(script)
        return scripts

    def test_gates_seeded_sequences(self):
        """(a)(b)(c)(d)(e) on MockGates directly, interleaved reserve, resale and entry."""
        scripts = self.play(GateScript)
        for name in ("reserve_slot", "cancel_reservation", "abort_order", "bind_order", "observe_payment_fact",
                     "issue", "list_resale", "cancel_listing", "observe_resale_payment", "accept_resale",
                     "authorize_admission", "consume_admission"):
            self.assertGreater(_total(scripts, "accepted", name), 0, name)
        for code in ("SLOT_OCCUPIED", "STALE_VERSION", "PAYMENT_FACT_REQUIRED", "RESALE_CAP", "ALREADY_CONSUMED"):
            self.assertGreater(_rejections(scripts, code), 0, code)
        for name in ("probe_replay", "probe_changed_body"):
            self.assertGreater(_total(scripts, "accepted", name), 0, name)
        self.assertGreater(sum(script.ledger.bumps for script in scripts), len(scripts))

    def test_reservation_seeded_sequences(self):
        """(a)(b)(c)(e)(f)(g) on ReservationMachine."""
        scripts = self.play(ReservationScript)
        for script in scripts:
            prefix_restore(self, script)
        for name in ("hold", "release", "cancel", "confirm", "observe_payment", "issue",
                     "authorize_admission", "consume", "reject_external"):
            self.assertGreater(_total(scripts, "accepted", name), 0, name)
        for code in ("SLOT_OCCUPIED", "ILLEGAL_TRANSITION", "STALE_VERSION", "ALREADY_CONSUMED"):
            self.assertGreater(_rejections(scripts, code), 0, code)
        for name in ("probe_replay", "probe_changed_body", "probe_rejected_repeat"):
            self.assertGreater(_total(scripts, "accepted", name), 0, name)

    def test_resale_seeded_sequences(self):
        """(a)(c)(d)(e)(f)(g) on ResaleMachine, including multi-hop version chains."""
        scripts = self.play(ResaleScript)
        for script in scripts:
            prefix_restore(self, script)
        for name in ("adopt_issued", "list_resale", "hold_buy", "release_hold", "cancel_listing",
                     "observe_resale_payment", "accept_resale", "close", "reject_external"):
            self.assertGreater(_total(scripts, "accepted", name), 0, name)
        for code in ("SLOT_OCCUPIED", "RESALE_CAP", "STALE_VERSION", "RIGHT_SALE_LOCKED"):
            self.assertGreater(_rejections(scripts, code), 0, code)
        for name in ("probe_replay", "probe_changed_body", "probe_rejected_repeat"):
            self.assertGreater(_total(scripts, "accepted", name), 0, name)
        self.assertGreater(max(max(row["version"] for row in script.ledger.rights.values()) for script in scripts if script.ledger.rights), 2)

    def test_admission_seeded_sequences(self):
        """(a)(c)(e)(f)(g) on AdmissionMachine."""
        scripts = self.play(AdmissionScript)
        for script in scripts:
            prefix_restore(self, script)
        for name in ("adopt_issued", "authorize_admission", "consume", "reject_external"):
            self.assertGreater(_total(scripts, "accepted", name), 0, name)
        for code in ("SLOT_OCCUPIED", "STALE_VERSION", "ALREADY_CONSUMED", "VENUE_SOURCE_UNAVAILABLE"):
            self.assertGreater(_rejections(scripts, code), 0, code)
        for name in ("probe_replay", "probe_changed_body", "probe_rejected_repeat"):
            self.assertGreater(_total(scripts, "accepted", name), 0, name)

    def test_same_seed_same_sequence(self):
        """Fixed seeds: two runs of the same seed give the same journal and digests."""
        first = ReservationScript(self, SEEDS[2], 2)
        first.play()
        second = ReservationScript(self, SEEDS[2], 2)
        second.play()
        self.assertEqual(first.machine.export_journal(), second.machine.export_journal())
        self.assertEqual(first.digests, second.digests)
        self.assertEqual(first.rejected, second.rejected)


class ExternalAndPaymentTests(unittest.TestCase):
    def test_g_reject_external_for_each_kind_leaves_state_unchanged(self):
        """(g) every external label, on a machine that already holds state."""
        for index, cls in enumerate((ReservationScript, ResaleScript, AdmissionScript)):
            script = cls(self, SEEDS[index], index)
            script.play(12)
            machine = script.machine
            before = (machine.export_journal(), machine.canonical_state(), machine.state_digest())
            for label in EXTERNAL_LABELS:
                self.assertEqual(codes(lambda label=label: machine.reject_external(label)), "EXTERNAL_UNSUPPORTED")
            self.assertEqual(codes(lambda: machine.reject_external(" ")), "INVALID_ID")
            self.assertEqual(before, (machine.export_journal(), machine.canonical_state(), machine.state_digest()))

    def test_b_payment_fact_alone_is_not_funds(self):
        """(b) an observed payment fact does not move funds or finalize."""
        script = GateScript(self, SEEDS[3], 3)
        script.setup()
        script.run("reserve_slot", "res-1", show_id=SHOW, slot=0, buyer_role=BUYERS[0], expires_ms=1_000)
        script.run("bind_order", "ord-1", reservation_id="res-1", amount=PRICE)
        self.assertEqual(codes(lambda: script.target.issue("tix-1", order_id="ord-1")), "PAYMENT_FACT_REQUIRED")
        paid = script.run("observe_payment_fact", hex_ref(7), order_id="ord-1", amount=PRICE)
        self.assertIs(paid["funds_executed"], False)
        self.assertEqual(paid["order"]["state"], "OPEN")
        issued = script.run("issue", "tix-1", order_id="ord-1")
        self.assertEqual(issued["evidence"]["payment_ref"], hex_ref(7))
        self.assertIs(issued["evidence"]["chain_issued"], False)


class RejectedAdoptCharacterizationTests(unittest.TestCase):
    """Owner-authorized characterization, separate from the property oracles.

    This checkout predates the atomic-adopt fix on main. A reused order/payment
    can leave an unjournaled occupied slot. Record that precise legacy outcome;
    on a fixed checkout assert atomicity directly. Neither outcome invents
    contract semantics. The legacy branch is not evidence for property (e).
    See the validation record's owner decision and class C/B findings.
    """

    @staticmethod
    def adopt(slot, order, ref):
        return dict(
            show_id=SHOW, organizer_role=ORGANIZER, capacity=3, gate_roles=list(GATES),
            primary_price=PRICE, resale_cap=RESALE_CAP, resale_allowed=True,
            organizer_bps=100, platform_bps=100, slot=slot, buyer_role=BUYERS[0],
            expires_ms=1_000, order_id=order, amount=PRICE, payment_ref=ref,
        )

    def check_rejection(self, machine_cls, conflict):
        machine = machine_cls()
        machine.adopt_issued("tix-1", idempotency_key="k1", **self.adopt(0, "ord-1", hex_ref(1)))
        digest, state, journal = machine.state_digest(), machine.canonical_state(), machine.export_journal()
        if conflict == "ORDER_BINDING_CONFLICT":
            body = self.adopt(1, "ord-1", hex_ref(2))
        else:
            body = self.adopt(1, "ord-2", hex_ref(1))
        rejected = codes(lambda: machine.adopt_issued("tix-2", idempotency_key="k2", **body))
        self.assertEqual(rejected, conflict)
        self.assertEqual(machine.export_journal(), journal)
        after = (machine.state_digest(), machine.canonical_state())
        restored = machine_cls.restore(journal)
        self.assertEqual((restored.state_digest(), restored.canonical_state()), (digest, state))
        # Public follow-up distinguishes hidden Admission gate residue from
        # true atomicity even when canonical_state omits the private slot.
        retry = self.adopt(1, "ord-3", hex_ref(3))
        restored.adopt_issued("tix-3", idempotency_key="k3", **retry)
        later = codes(lambda: machine.adopt_issued("tix-3", idempotency_key="k3", **retry))
        if later is None:
            self.assertEqual(after, (digest, state), "rejected adopt changed state")
            self.assertEqual(machine.canonical_state(), restored.canonical_state())
            self.assertEqual(machine.state_digest(), restored.state_digest())
        else:
            # Exact legacy characterization authorized by the owner, not a
            # relaxed assertion inside the seeded rejection/restore oracle.
            self.assertEqual(later, "SLOT_OCCUPIED")
            self.assertEqual(machine.export_journal(), journal)
            if machine_cls is ResaleMachine:
                self.assertNotEqual(after[0], digest)
                self.assertNotEqual(after[1], state)
            else:
                self.assertEqual(after, (digest, state))

    def test_rejected_adopt_resale_characterization(self):
        for conflict in ("ORDER_BINDING_CONFLICT", "PAYMENT_BINDING_CONFLICT"):
            with self.subTest(conflict=conflict):
                self.check_rejection(ResaleMachine, conflict)

    def test_rejected_adopt_admission_characterization(self):
        for conflict in ("ORDER_BINDING_CONFLICT", "PAYMENT_BINDING_CONFLICT"):
            with self.subTest(conflict=conflict):
                self.check_rejection(AdmissionMachine, conflict)

    def test_failed_adopt_without_partial_materialization_is_atomic(self):
        """Control: rejections raised before any gate mutation do leave state unchanged."""
        for machine_cls in (ResaleMachine, AdmissionMachine):
            machine = machine_cls()
            machine.adopt_issued("tix-1", idempotency_key="k1", **self.adopt(0, "ord-1", hex_ref(1)))
            digest = machine.state_digest()
            self.assertEqual(
                codes(lambda: machine.adopt_issued("tix-2", idempotency_key="k2", **self.adopt(0, "ord-2", hex_ref(2)))),
                "SLOT_OCCUPIED",
            )
            self.assertEqual(
                codes(lambda: machine.adopt_issued("tix-3", idempotency_key="k3", **self.adopt(3, "ord-3", hex_ref(3)))),
                "SLOT",
            )
            self.assertEqual(machine.state_digest(), digest)


def _skip_guard(*skipped):
    real = mock_gates._require

    def wrapper(ok, code):
        if not ok and code in skipped:
            return
        real(ok, code)

    return mock.patch.object(mock_gates, "_require", wrapper)


class UnguardedConsumeGates(MockGates):
    """In-memory copy with the single-consume guard removed: a second consume is accepted again."""

    def consume_admission(self, consume_id, **kwargs):
        right = self._rights.get(kwargs["right_id"])
        if right is None or right["state"] != "CONSUMED" or consume_id in self._consumes:
            return super().consume_admission(consume_id, **kwargs)
        evidence = {"consume_id": consume_id, "right_id": right["right_id"], "version_after": right["version"],
                    "decision": "CONSUMED_ONCE"}
        return self._env(applied="consume_admission", evidence=evidence, right=self._right_view(right))


class NegativeControlTests(unittest.TestCase):
    """Each oracle must fail when its guard is removed from an in-memory copy."""

    def script(self, gates=None, capacity=2):
        script = GateScript(self, 1, 0, gates)
        script.capacity = capacity
        script.ledger.capacity = capacity
        script.setup()
        return script

    def double_holder(self, script):
        script.run("reserve_slot", "res-1", show_id=SHOW, slot=0, buyer_role=BUYERS[0], expires_ms=1_000)
        script.run("reserve_slot", "res-2", show_id=SHOW, slot=0, buyer_role=BUYERS[1], expires_ms=1_000)

    def test_control_double_holder(self):
        clean = self.script(capacity=1)
        self.double_holder(clean)
        self.assertEqual(clean.rejected[("reserve_slot", "SLOT_OCCUPIED")], 1)
        with _skip_guard("SLOT_OCCUPIED"):
            patched = self.script(capacity=1)
            with self.assertRaisesRegex(AssertionError, "two active holders"):
                self.double_holder(patched)

    def consume_chain(self, script):
        script.run("reserve_slot", "res-1", show_id=SHOW, slot=0, buyer_role=BUYERS[0], expires_ms=1_000)
        script.run("bind_order", "ord-1", reservation_id="res-1", amount=PRICE)
        script.run("observe_payment_fact", hex_ref(1), order_id="ord-1", amount=PRICE)
        script.run("issue", "tix-1", order_id="ord-1")
        script.run("authorize_admission", "adm-1", right_id="tix-1", version=1, holder_role=BUYERS[0],
                   gate_role=GATES[0], request=hex_ref(2), expires_ms=1_000)
        script.run("consume_admission", "use-1", right_id="tix-1", version=1, gate_role=GATES[0], request=hex_ref(2))
        script.run("consume_admission", "use-2", right_id="tix-1", version=1, gate_role=GATES[0], request=hex_ref(2))

    def test_control_double_consume(self):
        clean = self.script()
        self.consume_chain(clean)
        self.assertEqual(clean.rejected[("consume_admission", "ALREADY_CONSUMED")], 1)
        patched = self.script(UnguardedConsumeGates())
        with self.assertRaisesRegex(AssertionError, "consumed twice"):
            self.consume_chain(patched)

    def test_control_issue_without_payment(self):
        def attempt(script):
            script.run("reserve_slot", "res-1", show_id=SHOW, slot=0, buyer_role=BUYERS[0], expires_ms=1_000)
            script.run("bind_order", "ord-1", reservation_id="res-1", amount=PRICE)
            script.run("issue", "tix-1", order_id="ord-1")

        clean = self.script()
        attempt(clean)
        self.assertEqual(clean.rejected[("issue", "PAYMENT_FACT_REQUIRED")], 1)
        # the private invariant would also object after the mutation, so its backstop is removed too
        with _skip_guard("PAYMENT_FACT_REQUIRED", "MOCK_INVARIANT"):
            patched = self.script()
            with self.assertRaisesRegex(AssertionError, "without an observed payment fact"):
                attempt(patched)

    def test_control_resale_cap(self):
        def attempt(script):
            script.run("reserve_slot", "res-1", show_id=SHOW, slot=0, buyer_role=BUYERS[0], expires_ms=1_000)
            script.run("bind_order", "ord-1", reservation_id="res-1", amount=PRICE)
            script.run("observe_payment_fact", hex_ref(1), order_id="ord-1", amount=PRICE)
            script.run("issue", "tix-1", order_id="ord-1")
            script.run("list_resale", "lst-1", right_id="tix-1", version=1, seller_role=BUYERS[0],
                       recipient_role=BUYERS[1], amount=RESALE_CAP + 1, expires_ms=1_000)

        clean = self.script()
        attempt(clean)
        self.assertEqual(clean.rejected[("list_resale", "RESALE_CAP")], 1)
        with _skip_guard("RESALE_CAP"):
            patched = self.script()
            with self.assertRaisesRegex(AssertionError, "exceeds the show's resale cap"):
                attempt(patched)

    def first_failure(self, make_gates, *skipped):
        """Seeded sequences over an in-memory copy with guards removed: first AssertionError text."""
        for index, seed in enumerate(SEEDS):
            try:
                with _skip_guard(*skipped):
                    GateScript(self, seed, index, make_gates()).play()
            except AssertionError as error:
                return str(error)
        return None

    def test_seeded_sequences_find_each_removed_guard(self):
        """The random interleavings, not only the scripted scenarios, reach the oracles."""
        self.assertIsNone(self.first_failure(MockGates))
        self.assertRegex(self.first_failure(UnguardedConsumeGates), "consumed twice|consumed right")
        self.assertRegex(self.first_failure(MockGates, "SLOT_OCCUPIED"), "two active holders|state changed|journal changed")
        self.assertRegex(self.first_failure(MockGates, "RESALE_CAP"), "exceeds the show's resale cap")
        self.assertRegex(self.first_failure(MockGates, "STALE_VERSION"), "stale")

    def test_control_rejection_mutates_state(self):
        """(e) a command that applies and then raises must be caught by the oracle."""

        class Mutating(ReservationMachine):
            def release(self, reservation_id, *, idempotency_key):
                super().release(reservation_id, idempotency_key=idempotency_key)
                raise ReservationError("LATE_FAILURE")

        def attempt(script):
            script.setup()
            script.run("hold", "res-1", show_id=SHOW, slot=0, buyer_role=BUYERS[0], expires_ms=1_000)
            script.run("release", "res-1")

        clean = ReservationScript(self, 1, 0)
        attempt(clean)
        self.assertEqual(clean.accepted["release"], 1)
        patched = ReservationScript(self, 1, 0)
        patched.target = patched.machine = Mutating()
        with self.assertRaisesRegex(AssertionError, "journal changed|state changed"):
            attempt(patched)


class FixtureTests(unittest.TestCase):
    def test_fixtures_stay_inside_the_contract_range(self):
        self.assertTrue(all(1 <= capacity <= mock_gates.CAPACITY_MAX for capacity in (1, 2, 3, 4, 8, 16)))
        self.assertLessEqual(PRICE, RESALE_CAP)
        self.assertIsInstance(GateError("X").code, str)


if __name__ == "__main__":
    unittest.main()
