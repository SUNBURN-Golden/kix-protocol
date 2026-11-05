"""Guided synthetic admission over one explicitly launched local ticket desk."""

import argparse
from pathlib import Path
import re
import sys

from booking_console import _diagnostic, _json
from ticket_operations_client import TicketOperationsClient


# Prompt order is part of the documented terminal interface, not a wire catalogue.
_FIELDS = {
    'authorize_admission_inputs': ('admission_id', 'right_id', 'version', 'holder_role',
                                   'gate_role', 'request', 'expires_ms'),
    'consume_inputs': ('consume_id', 'right_id', 'version', 'gate_role', 'request'),
    'view': ('right_id',),
    'view_credential': ('right_id', 'version', 'holder_role'),
    'set_clock': ('subject_id', 'now_ms'),
}
_CONFIRMATIONS = {'authorize_admission_inputs': 'AUTHORIZE', 'consume_inputs': 'CONSUME',
                  'set_clock': 'SET_CLOCK'}


class _InputError(ValueError):
    pass


class _TerminalReply(Exception):
    pass


def render_outcomes(reply, output_stream):
    """Keep historical action, stored credential and caller presentation distinct."""
    if 'error' in reply:
        return
    snapshot = 'receipt' in reply
    body = reply['receipt'] if snapshot else reply['view']
    label = 'Action snapshot' if snapshot else 'Current local observation'
    print(label + ': ' + _json({k: body[k] for k in ('duplicate', 'applied') if k in body}),
          file=output_stream)
    credential = body.get('credential', body if 'right_id' in body else {})
    for name, source, fields in (
        ('Stored credential', credential, ('phase', 'state', 'version', 'issued_version', 'holder_role')),
        ('Authorization', credential, ('admission_id', 'admission_expired', 'gate_role')),
        ('Consumption', credential, ('consume_id', 'version_after', 'terminal', 'slot_state')),
        ('Presentation', body.get('presentation', {}), ('version', 'holder_role', 'fresh', 'decision')),
    ):
        values = {k: source[k] for k in fields if k in source}
        if values:
            print(label + ' ' + name + '=' + _json(values), file=output_stream)
    if 'evidence' in body:
        print(label + ' Evidence=' + _json(body['evidence']), file=output_stream)


def run_console(client, *, input_stream, output_stream, error_stream):
    """Submit each selected action once. Caller owns child cleanup.

    Returns 0 clean, 1 after known refusals, 2 after terminal failure. No automatic
    reads, replay, restart, retry, clock changes or business compensation.
    """
    last_reply = None
    rejected = False

    def prompt(label):
        print(label + ': ', end='', file=output_stream, flush=True)
        line = input_stream.readline()
        if line == '':
            raise EOFError('terminal input ended; no further submissions')
        return line.removesuffix('\n').removesuffix('\r')

    def field(name):
        hint = ' (synthetic; enter clock)' if name == 'subject_id' else ''
        value = prompt(name + hint)
        if name in {'version', 'expires_ms', 'now_ms'}:
            if re.fullmatch(r'[0-9]+', value) is None:
                raise _InputError(name + ' requires an explicit nonnegative decimal integer')
            try:
                return int(value)
            except ValueError as error:
                raise _InputError(name + ' integer is too long') from error
        if not value or value != value.strip():
            raise _InputError(name + ' requires an explicit value without surrounding whitespace')
        return value

    try:
        print('Local synthetic admission console — MOCK_GATE_ONLY, IN_MEMORY_FSM.\n'
              'Authorization and consumption are separate explicit actions.\n'
              'Receipts are action snapshots; only explicitly requested views observe current state.\n'
              'A historical authorization or fresh presentation does not establish current admission authority.\n'
              'Admission timing and identity policy: UNDETERMINED — Astra/User; '
              'legal effects: UNDETERMINED — User/legal.', file=output_stream)
        while True:
            print('Actions: ' + ', '.join(_FIELDS) + ', quit', file=output_stream)
            action = prompt('action')
            if action == 'quit':
                return int(rejected)
            if action not in _FIELDS:
                print('Unknown action; choose an action from the menu.', file=output_stream)
                continue
            try:
                arguments = {name: field(name) for name in _FIELDS[action]}
                mutation = action in _CONFIRMATIONS
                if mutation:
                    arguments['idempotency_key'] = field('idempotency_key')
                request = dict(surface='admission', operation=action, arguments=arguments)
                if mutation:
                    print('proposed=' + _json(request), file=output_stream)
                    confirmation = _CONFIRMATIONS[action]
                    if prompt('Type literal ' + confirmation + ' to send once; anything else declines') != confirmation:
                        print('Declined; no request sent.', file=output_stream)
                        continue
            except _InputError as error:
                print('input_error=' + _json({'type': type(error).__name__, 'message': str(error)}),
                      file=output_stream)
                continue
            reply = client.request(request)
            last_reply = reply  # Save before output; display failure cannot erase a received result.
            print('desk=' + _json(reply), file=output_stream, flush=True)
            if 'error' in reply:
                rejected = True
                if (reply['surface'] is None or reply['operation'] is None or
                        reply['error'].get('type') in {'FixtureError', 'BookingInputError'}):
                    raise _TerminalReply('terminal desk error; original envelope retained')
            render_outcomes(reply, output_stream)
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, error_stream, last_reply=last_reply)
        return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', required=True, type=Path, help='caller-selected synthetic desk fixture')
    parser.add_argument('--cleanup-timeout', required=True, type=float,
                        help='finite positive child cleanup budget; not a response deadline')
    args = parser.parse_args(argv)
    try:
        client = TicketOperationsClient.launch(args.fixture, cleanup_timeout=args.cleanup_timeout)
    except ValueError as error:
        parser.error(str(error))
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, sys.stderr)
        return 2
    status = 2
    try:
        status = run_console(client, input_stream=sys.stdin, output_stream=sys.stdout, error_stream=sys.stderr)
    finally:
        try:
            child_status = client.close()
        except (Exception, KeyboardInterrupt) as error:
            _diagnostic(error, sys.stderr)
            status = 2
        else:
            if child_status != 0:
                try:
                    print('Child exit status=' + str(child_status), file=sys.stderr, flush=True)
                except (OSError, ValueError, UnicodeError):
                    pass
                status = status or 1
    return status


if __name__ == '__main__':
    raise SystemExit(main())
