"""Source-informed console boundary checks. Synthetic only; Analog, NOT Toss."""

import contextlib
from copy import deepcopy
from dataclasses import asdict, replace
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import payment_lookup_cli as cli
import payment_lookup_console as console
from fake_payment_lookup import FakePaymentLookup
from normalization_golden_vectors import GOLDEN_VECTORS
from payment_lookup_router import PaymentLookupRouter
from provider_facts import PROVENANCE, normalize_recorded_text
import synthetic_documents as documents


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / 'fixtures/payment_lookup.synthetic.json'
OPERATION = documents.OPERATION_REF
PAYMENT = documents.PAYMENT_REF_A


def journey(operation=OPERATION, submit='SUBMIT', ending='\n'):
    return ending.join([operation.provider, operation.account, operation.operation, submit, ''])


def payload(output, prefix):
    return json.loads(next(line[len(prefix):] for line in output.splitlines() if line.startswith(prefix)))


class PaymentLookupConsoleTests(unittest.TestCase):
    def setUp(self):
        self.bindings, self.routes = cli.load_fixture(FIXTURE)
        self.before_bytes = FIXTURE.read_bytes()
        self.out, self.err = io.StringIO(), io.StringIO()

    def tearDown(self):
        self.assertEqual(FIXTURE.read_bytes(), self.before_bytes)

    def run_console(self, text=None, **streams):
        return console.run_console(
            self.bindings, self.routes,
            input_stream=streams.get('input_stream', io.StringIO(journey() if text is None else text)),
            output_stream=streams.get('output_stream', self.out),
            error_stream=streams.get('error_stream', self.err),
        )

    def calls(self):
        return [ref for fake in self.routes.values() for ref in fake.calls]

    def test_scripted_transcripts_use_real_router(self):
        expected = {'paid': [15000], 'partial': [15000, 5000], 'full': [15000, 15000],
                    'timeout': 'LOOKUP_TIMEOUT', 'error': 'LOOKUP_ERROR', 'decline': None}
        for name, amounts in expected.items():
            with self.subTest(name=name):
                process = subprocess.run(
                    [sys.executable, str(ROOT / 'payment_lookup_console.py'), '--fixture', str(FIXTURE)],
                    input=(ROOT / f'fixtures/payment_lookup_console_{name}.txt').read_text(),
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual((process.returncode, process.stderr), (0, ''))
                self.assertIn('Analog, NOT Toss', process.stdout)
                self.assertIn('UNDETERMINED — Toss/User', process.stdout)
                self.assertIn(cli.LIMITATIONS, process.stdout)
                preview = payload(process.stdout, 'preview=')
                self.assertEqual(preview['operation_ref']['provider'], 'toss-synthetic')
                self.assertEqual(len(preview['payment_ref']), 5)
                if name == 'decline':
                    self.assertNotIn('result=', process.stdout)
                    continue
                result = payload(process.stdout, 'result=')
                self.assertEqual(result['operation_ref'], preview['operation_ref'])
                self.assertEqual(result['payment_ref'], preview['payment_ref'])
                self.assertEqual(sum(len(row['payment_refs']) for row in result['fake_calls']), 1)
                self.assertEqual(result['provenance'], PROVENANCE)
                self.assertEqual(result['limitations'], cli.LIMITATIONS)
                if isinstance(amounts, list):
                    self.assertEqual([item['item']['amount'] for item in result['facts']], amounts)
                    self.assertEqual(len(result['item_hashes']), len(amounts))
                else:
                    self.assertEqual(result['unresolved'], amounts)
                    self.assertNotIn('facts', result)

    def test_preview_is_flushed_before_submit_and_declines_never_lookup(self):
        owner = self

        class Input(io.StringIO):
            reads = 0

            def readline(self):
                self.reads += 1
                if self.reads == 4:
                    owner.assertEqual(owner.calls(), [])
                    preview = payload(owner.out.getvalue(), 'preview=')
                    owner.assertEqual(preview, {'operation_ref': asdict(OPERATION),
                                                'payment_ref': PAYMENT.as_dict()})
                    owner.assertEqual(flushed[-1], owner.out.getvalue())
                    owner.assertIn('preview=', flushed[-1])
                return super().readline()

        for decline in ('NO', '', 'submit', ' SUBMIT', 'SUBMIT ', 'SUBMIT\t'):
            self.out = io.StringIO()
            flushed = []
            with self.subTest(decline=decline), \
                 patch.object(cli, 'lookup_once') as lookup, \
                 patch.object(PaymentLookupRouter, 'lookup') as router, \
                 patch.object(FakePaymentLookup, 'lookup') as fake, \
                 patch.object(self.out, 'flush', side_effect=lambda: flushed.append(self.out.getvalue())):
                self.assertEqual(self.run_console(input_stream=Input(journey(submit=decline))), 0)
                lookup.assert_not_called()
                router.assert_not_called()
                fake.assert_not_called()
                self.assertIn('Declined', self.out.getvalue())

    def test_invalid_identifiers_and_eof_end_without_lookup(self):
        texts = ['', 'toss-synthetic\n', 'toss-synthetic\nmid_synthetic_001\n',
                 journey().rsplit('SUBMIT', 1)[0]]
        for field in ('provider', 'account', 'operation'):
            for value in ('', ' padded', 'padded ', 'x' * 101):
                values = dict(asdict(OPERATION), **{field: value})
                texts.append('\n'.join([*values.values(), 'SUBMIT', '']))
        for text in texts:
            with self.subTest(text=text), patch.object(cli, 'lookup_once') as lookup, \
                 patch.object(PaymentLookupRouter, 'lookup') as router, \
                 patch.object(FakePaymentLookup, 'lookup') as fake:
                self.assertEqual(self.run_console(text), 2)
                lookup.assert_not_called()
                router.assert_not_called()
                fake.assert_not_called()
        self.assertEqual(self.calls(), [])

    def test_submit_forwards_once_and_ignores_trailing_submissions(self):
        for operation in (OPERATION, replace(OPERATION, account='mid_synthetic_002')):
            self.bindings, self.routes = cli.load_fixture(FIXTURE)
            self.out = io.StringIO()
            with self.subTest(operation=operation), \
                 patch.object(cli, 'lookup_once', wraps=cli.lookup_once) as lookup, \
                 patch.object(PaymentLookupRouter, 'lookup', autospec=True,
                              side_effect=PaymentLookupRouter.lookup) as router, \
                 patch.object(FakePaymentLookup, 'lookup', autospec=True,
                              side_effect=FakePaymentLookup.lookup) as fake:
                self.assertEqual(self.run_console(journey(operation, ending='\r\n') + journey()), 0)
                lookup.assert_called_once_with(self.bindings, self.routes, operation)
                router.assert_called_once()
                self.assertEqual(router.call_args.args[1], operation)
                fake.assert_called_once()
                self.assertEqual(self.calls(), [self.bindings.lookup(operation)])
                self.assertEqual(payload(self.out.getvalue(), 'result=')['payment_ref'],
                                 self.bindings.lookup(operation).as_dict())

    def test_missing_binding_or_route_submits_once_with_zero_fake_calls(self):
        for missing in ('binding', 'route'):
            self.out = io.StringIO()
            operation = replace(OPERATION, operation='unbound_synthetic') if missing == 'binding' else OPERATION
            if missing == 'route':
                self.routes = {scope: fake for scope, fake in self.routes.items()
                               if scope.account != OPERATION.account}
            with self.subTest(missing=missing), \
                 patch.object(cli, 'lookup_once', wraps=cli.lookup_once) as lookup, \
                 patch.object(PaymentLookupRouter, 'lookup', autospec=True,
                              side_effect=PaymentLookupRouter.lookup) as router, \
                 patch.object(FakePaymentLookup, 'lookup', autospec=True,
                              side_effect=FakePaymentLookup.lookup) as fake:
                self.assertEqual(self.run_console(journey(operation)), 0)
                lookup.assert_called_once()
                router.assert_called_once()
                fake.assert_not_called()
            result = payload(self.out.getvalue(), 'result=')
            preview = payload(self.out.getvalue(), 'preview=')
            self.assertEqual(result['payment_ref'], preview['payment_ref'])
            self.assertEqual(result['unresolved'], 'BINDING_REQUIRED' if missing == 'binding'
                             else 'LOOKUP_ROUTE_MISSING')
            self.assertEqual(self.calls(), [])

    def load_document(self, document):
        config = json.loads(self.before_bytes)
        config['routes'][0]['recordings'][0]['recorded_text'] = json.dumps(document, ensure_ascii=False)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.json'
            path.write_text(json.dumps(config), encoding='utf-8')
            self.bindings, self.routes = cli.load_fixture(path)

    def test_display_preserves_literal_golden_bytes_and_hashes(self):
        for vector in GOLDEN_VECTORS:
            self.load_document(getattr(documents, vector['fixture']))
            self.out = io.StringIO()
            with self.subTest(case=vector['case']):
                self.assertEqual(self.run_console(), 0)
                result = payload(self.out.getvalue(), 'result=')
                position = vector['item_position']
                self.assertEqual(result['facts'][position], vector['expected_fact'])
                self.assertEqual(result['item_hashes'][position], vector['sha256_hex'])
                self.assertEqual(json.dumps(result['facts'][position], ensure_ascii=False, sort_keys=True,
                                            separators=(',', ':'), allow_nan=False).encode(),
                                 vector['canonical_utf8'])
                self.assertIs(type(result['facts'][position]['item']['amount']), int)
                self.assertEqual(result['receipt']['text'], '2026-10-01T12:00:05+09:00')

    def test_all_cancellations_and_terminal_controls_survive_rendering(self):
        document = deepcopy(documents.MULTIPLE_CANCELS)
        document['payment']['cancels'][0]['cancelReason'] = 'synthetic\x1b[31m\n\r\t'
        self.load_document(document)
        expected = cli.lookup_once(*cli.load_fixture(FIXTURE), OPERATION)
        history = normalize_recorded_text(PAYMENT, json.dumps(document))
        self.assertEqual(self.run_console(), 0)
        result = payload(self.out.getvalue(), 'result=')
        self.assertEqual(result['facts'], [item.normalized_fact() for item in history.items])
        self.assertEqual(result['item_hashes'], history.item_hashes())
        self.assertEqual(result['receipt'], history.receipt.as_dict())
        self.assertEqual(result['operation_ref'], expected['operation_ref'])
        self.assertNotIn('\x1b', self.out.getvalue())
        self.assertEqual(len(result['facts']), 3)

    def test_state_unchanged_with_populated_captures_and_review(self):
        item = normalize_recorded_text(PAYMENT, json.dumps(documents.PAID)).items[0]
        self.bindings.record_capture(OPERATION, PAYMENT, item)
        self.bindings.bind(OPERATION, documents.PAYMENT_REF_B)

        def snapshot():
            return deepcopy((self.bindings.binding_count(), self.bindings.lookup(OPERATION),
                             self.bindings.recorded_captures, self.bindings.review,
                             [(scope, dict(fake.recordings)) for scope, fake in self.routes.items()]))

        before = snapshot()
        with patch.object(self.bindings, 'bind', side_effect=AssertionError('must not bind')), \
             patch.object(self.bindings, 'record_capture', side_effect=AssertionError('must not capture')):
            self.assertEqual(self.run_console(), 0)
        self.assertEqual(snapshot(), before)
        self.assertEqual(self.calls(), [PAYMENT])
        self.assertEqual(payload(self.out.getvalue(), 'preview=')['payment_ref'], PAYMENT.as_dict())

    def test_terminal_read_failures_stop_before_submission(self):
        for position in range(1, 5):
            for error in (OSError('synthetic read'), KeyboardInterrupt()):
                stream = io.StringIO(journey() + journey())
                read = stream.readline
                count = 0

                def failing_read():
                    nonlocal count
                    count += 1
                    if count == position:
                        raise error
                    return read()

                with self.subTest(position=position, error=type(error).__name__), \
                     patch.object(stream, 'readline', side_effect=failing_read), \
                     patch.object(cli, 'lookup_once') as lookup:
                    self.assertEqual(self.run_console(input_stream=stream), 2)
                    lookup.assert_not_called()
                    self.assertEqual(count, position)

    def test_terminal_write_and_flush_failures_never_retry(self):
        # Seven writes: banner, three fields, preview, confirmation, result.
        for position in range(1, 8):
            for failure in ('write', 'flush', 'short', 'interrupt'):
                class Output(io.StringIO):
                    writes = 0

                    def write(self, value):
                        self.writes += 1
                        if self.writes == position and failure != 'flush':
                            if failure == 'short':
                                return len(value) - 1
                            if failure == 'interrupt':
                                raise KeyboardInterrupt()
                            raise BrokenPipeError('synthetic output')
                        return super().write(value)

                    def flush(self):
                        if self.writes == position and failure == 'flush':
                            raise OSError('synthetic flush')
                        return super().flush()

                self.bindings, self.routes = cli.load_fixture(FIXTURE)
                output = Output()
                # stderr itself may fail; it must remain best effort.
                with self.subTest(position=position, failure=failure), \
                     patch.object(cli, 'lookup_once', wraps=cli.lookup_once) as lookup, \
                     patch.object(self.err, 'write', side_effect=OSError('synthetic stderr')):
                    self.assertEqual(self.run_console(journey() + journey(), output_stream=output), 2)
                    self.assertEqual(lookup.call_count, int(position == 7))
                    self.assertEqual(output.writes, position)
                    self.assertEqual(len(self.calls()), int(position == 7))

    def test_lookup_and_render_errors_are_terminal(self):
        for error in (RuntimeError('synthetic bug'), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__), \
                 patch.object(PaymentLookupRouter, 'lookup', side_effect=error) as router, \
                 patch.object(cli, 'lookup_once', wraps=cli.lookup_once) as lookup:
                self.assertEqual(self.run_console(journey() + journey()), 2)
                lookup.assert_called_once()
                router.assert_called_once()
                self.assertEqual(self.calls(), [])
        # A failure after the selected fake has run must not try it again or
        # query the successful recording in the other merchant scope.
        original = FakePaymentLookup.lookup
        for error in (RuntimeError('synthetic post-call bug'), KeyboardInterrupt()):
            self.bindings, self.routes = cli.load_fixture(FIXTURE)

            def fail_after_call(fake, payment):
                original(fake, payment)
                raise error

            with self.subTest(after_call=type(error).__name__), \
                 patch.object(FakePaymentLookup, 'lookup', autospec=True,
                              side_effect=fail_after_call) as fake:
                self.assertEqual(self.run_console(journey() + journey()), 2)
                fake.assert_called_once()
                self.assertEqual(self.calls(), [PAYMENT])
        with patch.object(cli, 'lookup_once', return_value={'synthetic_unserializable': object()}) as lookup:
            self.assertEqual(self.run_console(journey() + journey()), 2)
            lookup.assert_called_once()

    def test_main_validates_configuration_before_input_or_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / 'invalid.json'
            config = json.loads(self.before_bytes)
            config['routes'][-1]['recordings'][-1]['unknown'] = True
            invalid.write_text(json.dumps(config))
            for args in ([], ['--fixture', str(FIXTURE), '--fixture', str(FIXTURE)],
                         ['--fixt', str(FIXTURE)], ['--fixture', str(FIXTURE), '--credentials', 'synthetic'],
                         ['--fixture', str(invalid)], ['--fixture', str(invalid.parent / 'absent')]):
                with self.subTest(args=args), contextlib.redirect_stdout(self.out), \
                     contextlib.redirect_stderr(self.err), patch.object(sys, 'stdin') as stdin, \
                     patch.object(console, 'run_console') as run, \
                     patch.object(cli, 'lookup_once') as lookup:
                    try:
                        result = console.main(args)
                    except SystemExit as exit_status:
                        result = exit_status.code
                    self.assertEqual(result, 2)
                    stdin.readline.assert_not_called()
                    run.assert_not_called()
                    lookup.assert_not_called()
            self.assertEqual(self.out.getvalue(), '')

    def test_main_loads_once_and_runs_one_journey(self):
        with contextlib.redirect_stdout(self.out), contextlib.redirect_stderr(self.err), \
             patch.object(sys, 'stdin', io.StringIO(journey() + journey())), \
             patch.object(cli, 'load_fixture', wraps=cli.load_fixture) as load, \
             patch.object(cli, 'lookup_once', wraps=cli.lookup_once) as lookup:
            self.assertEqual(console.main(['--fixture', str(FIXTURE)]), 0)
            load.assert_called_once_with(str(FIXTURE))
            lookup.assert_called_once()
        self.assertEqual(self.err.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
