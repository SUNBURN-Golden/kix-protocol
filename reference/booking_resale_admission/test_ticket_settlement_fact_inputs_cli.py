"""File/stdin request-time facts, compared line by line with direct FSM controls."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_ticket_settlement_fact_inputs import (FactInputEvidence, FIXTURE, HERE,
                                                changed, path, rows)
from test_ticket_operations_session import machines, snapshot
from ticket_operations_cli import run_requests
from ticket_operations_fixture import load_fixture


class TicketSettlementFactInputsCliTests(FactInputEvidence, unittest.TestCase):
    def cli(self, fixture, selector, stdin=None):
        return subprocess.run([sys.executable, str(HERE/'ticket_operations_cli.py'),
            '--fixture', str(fixture), '--requests', str(selector)], input=stdin,
            capture_output=True, text=True, check=False)

    def test_file_stdin_journeys_and_domain_continuation(self):
        for name, status in (('journey', 0), ('boundaries', 1)):
            for omitted in (False, True):
                with self.subTest(name=name, omitted=omitted):
                    value = json.loads(FIXTURE.read_text())
                    for field in ('offers', 'payments', 'presentations', 'statements', 'cancel_acceptances'):
                        self.assertEqual(value[field], [])
                    if omitted:
                        del value['statements'], value['cancel_acceptances']
                    self.graph(value)
                    expected = [self.step(row) for row in rows(name)]
                    with tempfile.TemporaryDirectory() as directory:
                        fixture = Path(directory)/'session.json'
                        fixture.write_text(json.dumps(value))
                        # In-process stream proves state/journal parity too.
                        session = load_fixture(fixture)
                        with redirect_stdout(io.StringIO()) as output:
                            self.assertEqual(run_requests(session, path(name).read_text().splitlines()), status)
                        self.assertEqual([json.loads(line) for line in output.getvalue().splitlines()], expected)
                        self.assertEqual(snapshot(machines(session)), snapshot(self.control))
                        self.assertTrue(all(source.calls == () for source in self.sources(session)))
                        for selector, stdin in ((path(name), None), ('-', path(name).read_text())):
                            result = self.cli(fixture, selector, stdin)
                            self.assertEqual((result.returncode, result.stderr), (status, ''))
                            self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], expected)

    def test_structural_failures_stop_before_next_explicit_line(self):
        commit, statement, accept = rows()[0], rows()[2], rows()[6]
        texts = [json.dumps(statement | dict(arguments={k: v for k, v in statement['arguments'].items()
                                                       if k != 'adjustment_reason'})),
                 json.dumps(changed(accept, extra=0)),
                 json.dumps(statement).replace('3801', 'NaN'),
                 json.dumps(accept).replace('"source_id":', '"source_id": "duplicate", "source_id":'),
                 '[]', '{']
        for bad in texts:
            for as_file in (False, True):
                text = json.dumps(commit)+'\n'+bad+'\n'+json.dumps(statement)+'\n'
                with tempfile.TemporaryDirectory() as directory:
                    requests = Path(directory)/'requests.jsonl'
                    requests.write_text(text)
                    result = self.cli(FIXTURE, requests if as_file else '-', None if as_file else text)
                self.assertEqual((result.returncode, result.stderr), (2, ''))
                output = [json.loads(line) for line in result.stdout.splitlines()]
                self.assertEqual(len(output), 2)
                self.assertEqual(output[0]['receipt']['settlement']['phase'], 'COMMITTED')
                self.assertEqual(output[1]['error']['type'], 'FixtureError')
