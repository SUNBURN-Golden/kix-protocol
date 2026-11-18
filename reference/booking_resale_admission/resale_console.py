"""Guided synthetic resale over one explicitly launched local ticket desk."""

import argparse
import json
from pathlib import Path
import re
import sys

from booking_console import _diagnostic, _json, decimal_amount
from ticket_operations_client import TicketOperationsClient


# Prompt order is part of the documented terminal interface, not a wire catalogue.
_FIELDS = {
    'adopt_issued_from_booking': ('reservation_id', 'right_id'),
    'list_resale': ('offer_id', 'listing_id'),
    'list_resale_inputs': ('listing_id', 'right_id', 'version', 'seller_role',
                           'recipient_role', 'amount', 'expires_ms', 'reservation_id'),
    'hold_buy': ('hold_id', 'listing_id', 'buyer_role'),
    'release_hold': ('hold_id', 'buyer_role'),
    'cancel_listing': ('listing_id', 'seller_role'),
    'observe_recorded_payment': ('recording_id', 'listing_id'),
    'observe_resale_payment': ('listing_id', 'payment_ref', 'amount', 'buyer_role'),
    'bind_settlement': ('listing_id', 'settlement_id'),
    'accept_resale': ('transfer_id', 'listing_id'),
    'close': ('listing_id',),
    'reconcile': ('listing_id',),
    'set_clock': ('subject_id', 'now_ms'),
    'view': ('listing_id',),
    'view_right': ('right_id',),
    'view_presentation': ('right_id', 'version', 'holder_role'),
}
_VIEWS = {'view', 'view_right', 'view_presentation'}


class _InputError(ValueError):
    pass


class _TerminalReply(Exception):
    pass


def render_outcomes(reply, output_stream):
    """Summarize only returned fields; the complete desk envelope stays primary."""
    if 'error' in reply:
        return
    snapshot = 'receipt' in reply
    body = reply['receipt'] if snapshot else reply['view']
    label = 'Action snapshot' if snapshot else 'Current service observation'
    if snapshot:
        print('Historical action snapshot; request a view explicitly for current state.',
              file=output_stream)
    print(label + ': ' + _json({k: body[k] for k in ('duplicate', 'applied') if k in body}),
          file=output_stream)
    listing = body.get('listing', body if 'listing_id' in body else {})
    right = body.get('right', {})
    for name, source, fields in (
        ('Listing', listing, ('phase', 'amount', 'currency', 'expires_ms', 'hold_id', 'buyer_role')),
        ('Payment', listing, ('payment_ref', 'settlement_id', 'settlement_gate',
                              'mock_settlement_commit_observed')),
        ('Ownership', {k: listing[k] for k in ('holder_role', 'current_version', 'ownership_transferred',
                                               'venue_credential_reissued') if k in listing} | right
                      | {k: body[k] for k in ('venue_credential_reissued',) if k in body},
         ('holder_role', 'version', 'current_version', 'ownership_transferred', 'venue_credential_reissued')),
    ):
        values = {k: source[k] for k in fields if k in source}
        if values:
            print(label + ' ' + name + '=' + _json(values), file=output_stream)
    if 'amount' in listing:
        print(label + ' amount=' + decimal_amount(listing['amount'], 0) + ' integer KRW',
              file=output_stream)


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

    def field(name, *, nullable=False):
        hint = (' (synthetic; enter clock)' if name == 'subject_id' else
                ' (JSON string or explicit null)' if nullable else '')
        value = prompt(name + hint)
        if name in {'version', 'amount', 'expires_ms', 'now_ms'}:
            if re.fullmatch(r'[0-9]+', value) is None:
                raise _InputError(name + ' requires an explicit nonnegative decimal integer')
            try:
                return int(value)
            except ValueError as error:
                raise _InputError(name + ' integer is too long') from error
        if nullable:
            try:
                value = json.loads(value)
            except ValueError as error:
                raise _InputError(name + ' requires a JSON string or explicit null') from error
            if value is None:
                return None
            if type(value) is not str:
                raise _InputError(name + ' requires a JSON string or explicit null')
        if not value or value != value.strip():
            raise _InputError(name + ' requires an explicit value without surrounding whitespace')
        return value

    try:
        print('Local synthetic resale console — MOCK_GATE_ONLY, in-memory.\n'
              'Listing, synthetic payment observation, settlement and ownership transfer are separate actions.\n'
              'Receipts are action snapshots; only explicitly requested views observe current state.\n'
              'Product policy: UNDETERMINED — Astra/User; legal effects: UNDETERMINED — User/legal.',
              file=output_stream)
        print('Payment inputs are synthetic; provider authentication: UNDETERMINED — Toss/User.',
              file=output_stream)
        while True:
            print('Actions: ' + ', '.join(_FIELDS) + ', quit', file=output_stream)
            action = prompt('action')
            if action == 'quit':
                return int(rejected)
            if action not in _FIELDS:
                print('Unknown action; choose an action from the menu.', file=output_stream)
                continue
            try:
                arguments = {name: field(name, nullable=(
                    (name == 'reservation_id' and action == 'list_resale_inputs') or
                    (name == 'buyer_role' and action == 'observe_resale_payment')))
                    for name in _FIELDS[action]}
                mutation = action not in _VIEWS
                if mutation:
                    arguments['idempotency_key'] = field('idempotency_key')
                request = dict(surface='resale', operation=action, arguments=arguments)
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
