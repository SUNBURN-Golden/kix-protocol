"""Guided synthetic settlement over one explicitly launched local ticket desk."""

import argparse
import json
from pathlib import Path
import re
import sys

from booking_console import _diagnostic, _json
from admission_fixture import decode_json
from ticket_operations_client import TicketOperationsClient


# Terminal prompt order only; all selectors already exist on the shared desk.
_STATEMENT = ('settlement_id', 'movement_id', 'gross', 'amount', 'fee', 'tax',
              'held', 'adjustment', 'adjustment_reason')
_FIELDS = {
    'initiate_from_booking': ('settlement_id', 'reservation_id', 'trade_id', 'debtor_role', 'policy'),
    'initiate_from_resale': ('settlement_id', 'listing_id', 'trade_id', 'debtor_role', 'policy'),
    'authorize': ('settlement_id',),
    'capture': ('settlement_id',),
    'commit': _STATEMENT,
    'observe_statement': _STATEMENT,
    'commit_recorded_statement': ('settlement_id', 'movement_id'),
    'observe_recorded_statement': ('settlement_id', 'movement_id'),
    'distribute': ('settlement_id', 'order'),
    'bind_refund': ('settlement_id', 'refund_id', 'amount', 'beneficiary_role', 'reason'),
    'observe_mock_cancel_acceptance': ('settlement_id', 'source_id', 'amount'),
    'observe_recorded_cancel_acceptance': ('settlement_id', 'source_id'),
    'view': ('settlement_id',),
}
_AMOUNTS = {'gross', 'amount', 'fee', 'tax', 'held', 'adjustment'}


class _InputError(ValueError):
    pass


class _TerminalReply(Exception):
    pass


def render_outcomes(reply, output_stream):
    """Display service integers directly, without computing financial outcomes."""
    if 'error' in reply:
        return
    snapshot = 'receipt' in reply
    body = reply['receipt'] if snapshot else reply['view']
    settlement = body['settlement'] if snapshot else body
    label = 'Action snapshot' if snapshot else 'Current service observation'
    print(label + ': ' + _json({k: body[k] for k in ('duplicate', 'applied') if k in body}),
          file=output_stream)
    print(label + ' Settlement=' + _json({k: v for k, v in settlement.items() if k != 'claim'}),
          file=output_stream)
    claim = settlement['claim']
    if claim is None:
        print(label + ' claim data unavailable (claim=null).', file=output_stream)
        return
    for name, fields in (
        ('Cash', ('confirmed_cash', 'distributed_cash', 'undistributed_cash')),
        ('Statement position', ('receivable_open', 'non_cash_accounted')),
        ('Refund', ('refund_face', 'refund_accepted', 'refund_outstanding',
                    'refund_bearer_policy', 'distribution_blocked')),
        ('PG adjustment', ('pg_adjustment_outstanding',)),
        ('Distribution', ('distribution_order',)),
    ):
        print(label + ' ' + name + '=' + _json({k: claim[k] for k in fields}), file=output_stream)
    for obligation in claim['obligations']:
        print(label + ' Allocation=' + _json({k: obligation[k] for k in
              ('payee', 'face', 'distributed', 'cancelled_unpaid', 'recovery_due', 'outstanding')}),
              file=output_stream)


def run_console(client, *, input_stream, output_stream, error_stream):
    """Send each confirmed action once; caller owns close(), including on failure.

    Return 0 clean, 1 after known refusals, 2 after terminal failure. No automatic
    requests, retry, sequencing, reads, child replacement or compensation.
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
        hint = (' (JSON array of strings; explicit order)' if name == 'order' else
                ' (JSON object; explicit synthetic policy)' if name == 'policy' else
                ' (JSON string or explicit null)' if name == 'adjustment_reason' else '')
        value = prompt(name + hint)
        if name == 'policy':
            try:
                value = decode_json(value)
            except ValueError as error:
                raise _InputError('policy requires a JSON object: ' + str(error)) from error
            if type(value) is not dict:
                raise _InputError('policy requires a JSON object')
            return value
        if name in _AMOUNTS:
            if re.fullmatch(r'-?[0-9]+', value) is None:
                raise _InputError(name + ' requires an explicit decimal integer')
            try:
                return int(value)
            except ValueError as error:
                raise _InputError(name + ' integer is too long') from error
        if name in {'order', 'adjustment_reason'}:
            try:
                value = json.loads(value)
            except ValueError as error:
                raise _InputError(name + ' requires ' + hint.strip(' ()')) from error
            if name == 'order':
                if type(value) is not list or any(type(item) is not str for item in value):
                    raise _InputError('order requires a JSON array of strings')
            elif value is not None and type(value) is not str:
                raise _InputError('adjustment_reason requires a JSON string or explicit null')
            return value
        if not value or value != value.strip():
            raise _InputError(name + ' requires an explicit value without surrounding whitespace')
        return value

    try:
        print('Local synthetic settlement console — MOCK_SETTLEMENT_ONLY, in-memory.\n'
              'Receipts are action snapshots; select view explicitly for a current service observation.\n'
              'Acceptance means synthetic cancellation acceptance; not real refund completion.\n'
              'Distribution/refund policy: UNDETERMINED — Astra/User.\n'
              'Accounting/legal effects: UNDETERMINED — User/designated advisers.', file=output_stream)
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
                mutation = action != 'view'
                if mutation:
                    arguments['idempotency_key'] = field('idempotency_key')
                request = dict(surface='settlement', operation=action, arguments=arguments)
                if mutation:
                    print('proposed=' + _json(request), file=output_stream)
                    if prompt('Type literal SUBMIT to send once; anything else declines') != 'SUBMIT':
                        print('Declined; no request sent.', file=output_stream)
                        continue
            except _InputError as error:
                print('input_error=' + _json({'type': type(error).__name__, 'message': str(error)}),
                      file=output_stream)
                continue
            reply = client.request(request)
            last_reply = reply  # Preserve the received envelope before any rendering can fail.
            print('desk=' + _json(reply), file=output_stream, flush=True)
            if 'error' in reply:
                rejected = True
                if (reply['surface'] is None or reply['operation'] is None or
                        reply['error'].get('type') in {'FixtureError', 'BookingInputError'}):
                    raise _TerminalReply('terminal desk error; original envelope retained')
            if action in {'observe_mock_cancel_acceptance', 'observe_recorded_cancel_acceptance'}:
                print('synthetic cancellation acceptance; not real refund completion', file=output_stream)
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
