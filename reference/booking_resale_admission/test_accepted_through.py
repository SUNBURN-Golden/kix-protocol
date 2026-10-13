"""accepted_through reports journal length and the existing clock. It does not move either."""

import unittest

from admission_fsm import AdmissionMachine
from reservation_fsm import ReservationMachine
from resale_fsm import ResaleMachine


class AcceptedThroughTests(unittest.TestCase):
    def test_clocked_machines_report_journal_and_time_without_mutation(self):
        for machine in (ReservationMachine(), ResaleMachine(), AdmissionMachine()):
            before = (machine.canonical_state(), machine.export_journal(), machine._now)
            self.assertEqual(
                machine.accepted_through(),
                {"journal_entries": 0, "logical_time_ms": 0},
            )
            self.assertEqual(
                (machine.canonical_state(), machine.export_journal(), machine._now),
                before,
            )
