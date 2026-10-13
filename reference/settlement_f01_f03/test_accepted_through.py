"""accepted_through on the settlement machine is the journal length only."""

import unittest

from settlement_fsm import SettlementMachine


class AcceptedThroughTests(unittest.TestCase):
    def test_reports_journal_length_and_omits_a_clock(self):
        machine = SettlementMachine()
        before = (machine.canonical_state(), machine.export_journal())
        report = machine.accepted_through()
        self.assertEqual(report, {"journal_entries": 0})
        self.assertNotIn("logical_time_ms", report)
        self.assertFalse(hasattr(machine, "_now"))
        self.assertEqual((machine.canonical_state(), machine.export_journal()), before)
