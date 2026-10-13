"""accepted_through on the credit machine is the journal length only."""

import unittest

from credit_fsm import CreditMachine


class AcceptedThroughTests(unittest.TestCase):
    def test_reports_journal_length_and_leaves_the_guard_in_place(self):
        machine = CreditMachine()
        before = (machine.canonical_state(), machine.export_journal())
        report = machine.accepted_through()
        self.assertEqual(report, {"journal_entries": 0})
        self.assertNotIn("logical_time_ms", report)
        self.assertFalse(hasattr(machine, "_now"))
        self.assertEqual((machine.canonical_state(), machine.export_journal()), before)
        self.assertTrue(callable(machine._guard))
