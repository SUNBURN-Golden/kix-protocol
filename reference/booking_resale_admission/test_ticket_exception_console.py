"""Source-informed input/confirmation evidence for six existing desk selectors.

Service semantics remain covered by the session and real-child console suites.
"""

import io
import json
import unittest
from unittest.mock import Mock

import admission_console
import booking_console
import resale_console
import settlement_console


ACTIONS = [
    ('booking', booking_console, 'reconcile', ('reservation_id', 'idempotency_key'), 'RECONCILE'),
    ('resale', resale_console, 'reconcile', ('listing_id', 'idempotency_key'), 'SUBMIT'),
    ('admission', admission_console, 'reconcile', ('right_id', 'idempotency_key'), 'RECONCILE'),
    ('settlement', settlement_console, 'reconcile', ('settlement_id', 'idempotency_key'), 'SUBMIT'),
    ('settlement', settlement_console, 'fail', ('settlement_id', 'reason', 'idempotency_key'), 'SUBMIT'),
    ('settlement', settlement_console, 'cancel', ('settlement_id', 'reason', 'idempotency_key'), 'SUBMIT'),
]


def script(lines):
    return io.StringIO('\n'.join(lines) + '\n')


class TicketExceptionConsoleTests(unittest.TestCase):
    def test_explicit_opaque_fields_literal_single_use_confirmation_and_complete_errors(self):
        for surface, module, operation, names, confirmation in ACTIONS:
            args = {name: 'caller-☀-' + name for name in names}
            action = [operation, *args.values()]
            row = dict(surface=surface, operation=operation, arguments=args)
            for error in ({'code': 'IDEMPOTENCY_CONFLICT'},
                          {'type': 'OriginalLocalError', 'message': 'original "☀"\nerror\tbytes'}):
                with self.subTest(surface=surface, operation=operation, error=error):
                    reply = dict(surface=surface, operation=operation, error=error)
                    client = Mock()
                    client.request.return_value = reply
                    out, err = io.StringIO(), io.StringIO()
                    status = module.run_console(client, input_stream=script(
                        action + [confirmation.lower(), *action, confirmation,
                                  *action, 'no', 'quit']), output_stream=out, error_stream=err)
                    self.assertEqual((status, err.getvalue()), (1, ''))
                    client.request.assert_called_once_with(row)
                    proposed = 'proposed=' + json.dumps(row, sort_keys=True, ensure_ascii=True)
                    self.assertEqual(out.getvalue().count(proposed), 3)
                    self.assertEqual(out.getvalue().count('Declined; no request sent.'), 2)
                    self.assertIn('desk=' + json.dumps(reply, sort_keys=True), out.getvalue())
                    positions = [out.getvalue().index(name + (' (synthetic)' if surface == 'booking' else '') + ':')
                                 for name in names]
                    self.assertEqual(positions, sorted(positions))

    def test_every_field_requires_explicit_nonblank_unpadded_string(self):
        for surface, module, operation, names, _ in ACTIONS:
            for index in range(len(names)):
                for value in ('', ' ', ' padded', 'padded '):
                    with self.subTest(surface=surface, operation=operation, field=names[index], value=value):
                        client, out, err = Mock(), io.StringIO(), io.StringIO()
                        status = module.run_console(client, input_stream=script(
                            [operation, *['explicit'] * index, value, 'quit']),
                            output_stream=out, error_stream=err)
                        self.assertEqual((status, err.getvalue()), (0, ''))
                        client.request.assert_not_called()
                        self.assertIn('input_error=', out.getvalue())
                        self.assertNotIn('proposed=', out.getvalue())

    def test_missing_fields_and_interrupt_at_every_prompt_never_submit(self):
        for surface, module, operation, names, _ in ACTIONS:
            action = [operation, *['explicit'] * len(names)]
            for prefix_length in range(1, len(action) + 1):
                for failure in (None, KeyboardInterrupt('operator interrupt'), OSError('input unavailable')):
                    with self.subTest(surface=surface, operation=operation, prefix=prefix_length, failure=failure):
                        prefix = script(action[:prefix_length])
                        queued = script(['view', 'queued-subject', 'quit'])

                        class BrokenInput:
                            broken = False

                            def readline(self):
                                line = prefix.readline()
                                if line:
                                    return line
                                if not self.broken:
                                    self.broken = True
                                    if failure is not None:
                                        raise failure
                                    return ''
                                return queued.readline()

                        client, out, err = Mock(), io.StringIO(), io.StringIO()
                        status = module.run_console(client, input_stream=BrokenInput(),
                            output_stream=out, error_stream=err)
                        self.assertEqual(status, 2)
                        client.request.assert_not_called()
                        self.assertEqual(queued.read(), 'view\nqueued-subject\nquit\n')
                        self.assertIn('FENCED:', err.getvalue())


if __name__ == '__main__':
    unittest.main()
