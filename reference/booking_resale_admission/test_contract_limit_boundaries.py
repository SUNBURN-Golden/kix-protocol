"""Direct BRA §1 input boundaries; synthetic offline fixtures, no policy changes."""

import unittest

from admission_fsm import AdmissionError, AdmissionMachine
from mock_gates import GateError, MockGates
from reservation_fsm import ReservationError, ReservationMachine
from resale_fsm import ResaleError, ResaleMachine


class _Str(str):
    pass


def show(gate, show_id="show-1", **changes):
    body = dict(
        organizer_role="organizer", capacity=2, gate_roles=["gate-a"],
        primary_price=10_001, resale_cap=20_000, resale_allowed=True,
        organizer_bps=1, platform_bps=1,
    )
    body.update(changes)
    return gate.register_show(show_id, **body)


MACHINES = (
    (ReservationMachine, ReservationError),
    (ResaleMachine, ResaleError),
    (AdmissionMachine, AdmissionError),
)


class ContractLimitBoundaryTests(unittest.TestCase):
    def test_gate_identifier_length_100_accepted_101_rejected(self):
        for field in ("show_id", "organizer_role"):
            with self.subTest(field=field):
                gate = MockGates()
                accepted = show(gate, **{field: "s" * 100})
                self.assertEqual(accepted["show"][field], "s" * 100)
                before = gate.view_show(accepted["show"]["show_id"])
                with self.assertRaises(GateError) as caught:
                    show(gate, **{field: "s" * 101})
                self.assertEqual(caught.exception.code, "INVALID_ID")
                self.assertEqual(gate.view_show(accepted["show"]["show_id"]), before)

    def test_gate_identifier_rejects_str_subclass_and_bool(self):
        for field in ("show_id", "organizer_role"):
            for bad in (_Str("show-1"), True):
                with self.subTest(field=field, kind=type(bad).__name__):
                    gate = MockGates()
                    show(gate)
                    before = gate.view_show("show-1")
                    with self.assertRaises(GateError) as caught:
                        show(gate, **{field: bad})
                    self.assertEqual(caught.exception.code, "INVALID_ID")
                    self.assertEqual(gate.view_show("show-1"), before)

    def test_gate_amount_10_12_accepted_and_plus_one_rejected(self):
        for field in ("primary_price", "resale_cap"):
            with self.subTest(field=field):
                gate = MockGates()
                self.assertEqual(show(gate, **{field: 10**12})["show"][field], 10**12)
                before = gate.view_show("show-1")
                with self.assertRaises(GateError) as caught:
                    show(gate, "show-2", **{field: 10**12 + 1})
                self.assertEqual(caught.exception.code, "INVALID_AMOUNT")
                self.assertEqual(gate.view_show("show-1"), before)

    def test_gate_clock_10_15_accepted_and_plus_one_rejected(self):
        self.assertEqual(MockGates().set_clock(10**15)["logical_time_ms"], 10**15)
        gate = MockGates()
        with self.assertRaises(GateError) as caught:
            gate.set_clock(10**15 + 1)
        self.assertEqual(caught.exception.code, "CLOCK")
        self.assertEqual(gate.set_clock(0)["logical_time_ms"], 0)

    def test_fsm_identifier_boundaries(self):
        for field in ("show_id", "organizer_role"):
            machine = ReservationMachine()
            accepted = show(machine, idempotency_key="accepted", **{field: "s" * 100})
            self.assertEqual(accepted["show"][field], "s" * 100)
            for index, bad in enumerate(("s" * 101, _Str("other"), True)):
                with self.subTest(field=field, kind=type(bad).__name__, index=index):
                    before = machine.export_journal()
                    # Distinct keys avoid replaying a same-text fingerprint.
                    with self.assertRaises(ReservationError) as caught:
                        show(machine, idempotency_key=f"bad-{index}", **{field: bad})
                    self.assertEqual(caught.exception.code, "INVALID_ID")
                    self.assertEqual(machine.export_journal(), before)

        for factory, error in MACHINES:
            machine = factory()
            accepted = machine.set_clock("clock", idempotency_key="k" * 100, now_ms=0)
            self.assertEqual(accepted["applied"], "set_clock")
            for bad in ("k" * 101, _Str("subclass-key"), True):
                with self.subTest(machine=factory.__name__, key_type=type(bad).__name__):
                    before = machine.export_journal()
                    with self.assertRaises(error) as caught:
                        machine.set_clock("clock", idempotency_key=bad, now_ms=0)
                    self.assertEqual(caught.exception.code, "INVALID_ID")
                    self.assertEqual(machine.export_journal(), before)

    def test_fsm_amount_boundaries(self):
        for field in ("primary_price", "resale_cap"):
            with self.subTest(field=field):
                machine = ReservationMachine()
                accepted = show(machine, idempotency_key="accepted", **{field: 10**12})
                self.assertEqual(accepted["show"][field], 10**12)
                before = machine.export_journal()
                with self.assertRaises(ReservationError) as caught:
                    show(machine, "show-2", idempotency_key="rejected", **{field: 10**12 + 1})
                self.assertEqual(caught.exception.code, "INVALID_AMOUNT")
                self.assertEqual(machine.export_journal(), before)

    def test_fsm_clock_boundaries(self):
        for factory, error in MACHINES:
            with self.subTest(machine=factory.__name__):
                accepted = factory().set_clock("clock", idempotency_key="max", now_ms=10**15)
                self.assertEqual(accepted["logical_time_ms"], 10**15)
                machine = factory()
                before = machine.export_journal()
                with self.assertRaises(error) as caught:
                    machine.set_clock("clock", idempotency_key="too-large", now_ms=10**15 + 1)
                self.assertEqual(caught.exception.code, "CLOCK")
                self.assertEqual(machine.export_journal(), before)
                self.assertEqual(
                    machine.set_clock("clock", idempotency_key="zero", now_ms=0)["logical_time_ms"], 0
                )


if __name__ == "__main__":
    unittest.main()
