"""Strict JSONL transport for explicit local settlement input selectors."""

from contextlib import redirect_stdout
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_ticket_settlement_inputs as inputs
from test_ticket_settlement_inputs import (
    FIXTURE, HERE, SELECTORS, initiation, path, rows,
)
from test_ticket_operations_session import machines, snapshot
from ticket_operations_cli import run_requests
from ticket_operations_fixture import load_fixture
from ticket_operations_session import TicketSettlementSession


class TicketSettlementInputsCliTests(unittest.TestCase):
    def cli(self, selector, stdin=None, fixture=FIXTURE):
        return subprocess.run([sys.executable, str(HERE/'ticket_operations_cli.py'),
            '--fixture', str(fixture), '--requests', str(selector)], input=stdin,
            text=True, capture_output=True, check=False)

    def test_file_stdin_transcripts_match_direct_control_and_api(self):
        for name in ('booking', 'resale', 'boundaries'):
            control = inputs.TicketSettlementInputsTests()
            control.graph()
            expected = []
            for row in rows(name):
                result = control.step(row)
                expected.append(dict(surface=row['surface'], operation=row['operation']) | result)
            for selector, stdin in ((path(name), None), ('-', path(name).read_text())):
                result = self.cli(selector, stdin)
                self.assertEqual((result.returncode, result.stderr), (1 if name=='boundaries' else 0, ''))
                self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], expected)

    def test_structural_errors_stop_before_read_even_after_prior_success(self):
        for op, (kind, field, _) in SELECTORS.items():
            session = load_fixture(FIXTURE)
            row = initiation(kind)
            args = row['arguments']
            bad_args = [None, [], args | dict(extra=0), args | dict(gross=1), args | dict(currency='KRW'),
                        *[{k:v for k,v in args.items() if k != f} for f in args]]
            texts = [json.dumps(row | dict(arguments=bad)) for bad in bad_args]
            texts += [json.dumps(row | dict(operation=bad)) for bad in ('initiate_from_right','__init__',[],None)]
            texts += [json.dumps(row).replace('"policy": {', '"policy": {"fee_bps": 0,')]
            texts += [json.dumps(row).replace('"fee_bps": 500', '"fee_bps": '+n)
                      for n in ('NaN', 'Infinity', '-Infinity', '1e999')]
            before = snapshot(machines(session))
            for text in texts:
                with self.subTest(text=text), \
                        patch.object(machines(session)[1], 'view', side_effect=AssertionError('booking read')), \
                        patch.object(machines(session)[2], 'view', side_effect=AssertionError('resale read')), \
                        redirect_stdout(io.StringIO()) as output:
                    status = run_requests(session, [text, json.dumps(initiation())])
                self.assertEqual(status, 2)
                self.assertEqual(len(output.getvalue().splitlines()), 1)
                self.assertEqual(json.loads(output.getvalue())['error']['type'], 'FixtureError')
                self.assertEqual(snapshot(machines(session)), before)
            prefix = json.dumps(dict(surface='booking', operation='view', arguments=dict(reservation_id='reserve-2')))
            text = prefix+'\n'+json.dumps(row | dict(arguments=args | dict(currency='KRW')))+'\n'+prefix+'\n'
            with tempfile.TemporaryDirectory() as directory:
                file = Path(directory)/'bad.jsonl'
                file.write_text(text)
                for selector, stdin in ((file,None),('-',text)):
                    result = self.cli(selector, stdin)
                    self.assertEqual((result.returncode,result.stderr),(2,''))
                    self.assertEqual(len(result.stdout.splitlines()),2)

    def test_source_and_target_refusals_continue_and_missing_sources_preserve_manual_mode(self):
        for op, (kind, field, index) in SELECTORS.items():
            row = initiation(kind)
            for fault in ('exception', 'mismatch', 'unconfigured'):
                session = load_fixture(FIXTURE)
                source = machines(session)[index]
                before = snapshot(machines(session))
                if fault == 'unconfigured':
                    session.settlement = TicketSettlementSession(machines(session)[0])
                options = (dict(side_effect=TimeoutError('immediate')) if fault != 'mismatch'
                           else dict(return_value={field:'other','order_id':'order','amount':1,'currency':'KRW'}))
                view = dict(surface='settlement',operation='view',arguments=dict(settlement_id='claim-1'))
                with patch.object(source,'view',**options) as read, redirect_stdout(io.StringIO()) as output:
                    status = run_requests(session,[json.dumps(row),json.dumps(view)])
                self.assertEqual(status,1)
                result = [json.loads(line) for line in output.getvalue().splitlines()]
                self.assertEqual(len(result),2)
                self.assertEqual(result[0]['error']['type'],
                                 'InvalidSettlementInputRecord' if fault=='mismatch' else 'SettlementInputSourceError')
                self.assertEqual(read.call_count,0 if fault=='unconfigured' else 1)
                self.assertEqual(snapshot(machines(session)),before)
                if fault == 'unconfigured':
                    # No source dependency was added to manual initiation.
                    args = {k:v for k,v in initiation()['arguments'].items() if k != 'reservation_id'}
                    session.settlement.initiate(**args, gross=10001, currency='KRW')
            # Executable file/stdin malformed/unconfirmed booking is available through setup.
        value = json.loads(FIXTURE.read_text())
        value['setup'] = [e for e in value['setup'] if e['subject_id']!='order-2']
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)/'unconfirmed.json'
            fixture.write_text(json.dumps(value))
            text = json.dumps(initiation())+'\n'+json.dumps(view)+'\n'
            requests = Path(directory)/'requests.jsonl'
            requests.write_text(text)
            for selector, stdin in ((requests,None),('-',text)):
                result = self.cli(selector, stdin, fixture)
                self.assertEqual((result.returncode,result.stderr),(1,''))
                result = [json.loads(line) for line in result.stdout.splitlines()]
                self.assertEqual(len(result),2)
                self.assertEqual(result[0]['error']['type'],'InvalidSettlementInputRecord')


if __name__ == '__main__':
    unittest.main()
