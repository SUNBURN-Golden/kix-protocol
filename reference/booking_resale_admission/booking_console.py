"""Guided synthetic booking over one explicitly launched local ticket desk."""

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys

from ticket_operations_client import TicketOperationsClient


@dataclass(frozen=True)
class ConfirmationTarget:
    reservation_id: str
    order_id: str
    idempotency_key: str


@dataclass(frozen=True)
class PendingPreview:
    request_text: str
    target: ConfirmationTarget
    # Immutable serialized copy: callers cannot edit nested quote fields.
    quote_json: str


def _json(value):
    # Escaping preserves control characters, arbitrary Unicode and diagnostic bytes.
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)


def decimal_amount(atoms, decimals):
    """Render integer atoms exactly, without floating point or rounding."""
    value = str(atoms)
    sign = '-' if value.startswith('-') else ''
    digits = value.lstrip('-').zfill(decimals + 1)
    return sign + (digits if decimals == 0 else digits[:-decimals] + '.' + digits[-decimals:])


def render_quote(quote, output_stream):
    print('CALCULATION_ONLY preview; reservation confirmation is MOCK_GATE_ONLY.', file=output_stream)
    print('asset=' + _json(quote['asset']), file=output_stream)
    for label, amounts in [*(('line ' + _json(line['lineId']), line) for line in quote['lines']),
                           ('totals', quote['totals'])]:
        print(label + ': ' + ' '.join(
            field + '=' + amounts[field] + ' (decimal=' +
            decimal_amount(amounts[field], quote['asset']['decimals']) + ')'
            for field in ('grossAtoms', 'discountAtoms', 'payableAtoms')), file=output_stream)
    print('quoteHash=' + quote['quoteHash'], file=output_stream)
    # Retain all original fields, labels and false authority/finality flags.
    print('quote=' + _json(quote), file=output_stream)


def _diagnostic(error, stream, *, last_reply=None):
    details = []
    current = error
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        detail = {'type': type(current).__name__, 'message': str(current)}
        for field in ('request', 'request_bytes', 'reply_bytes'):
            if hasattr(current, field):
                value = getattr(current, field)
                detail[field] = repr(value) if isinstance(value, bytes) else value
        details.append(detail)
        current = current.__cause__ or (None if current.__suppress_context__ else current.__context__)
    try:
        print('FENCED: ' + _json({'exceptions': details, 'last_reply': last_reply}),
              file=stream, flush=True)
    except (OSError, ValueError, UnicodeError):
        # An unavailable diagnostic sink cannot authorize another submission.
        pass


class _TerminalReply(Exception):
    pass


class _ConsoleInputError(ValueError):
    pass


def run_console(client, *, input_stream, output_stream, error_stream):
    """Run prompts synchronously. Caller owns close(), including after failure.

    Returns 0 for clean exit, 1 after known refusals, 2 after terminal failure.
    No automatic request, retry, reread, clock, cleanup mutation or replacement.
    """
    last_reply = None
    rejected = False
    request_text = None
    target = None
    pending = None

    def prompt(label):
        print(label + ': ', end='', file=output_stream, flush=True)
        line = input_stream.readline()
        if line == '':
            raise EOFError('terminal input ended; no further submissions')
        return line.removesuffix('\n').removesuffix('\r')

    def fields(names):
        values = {}
        for name in names:
            hint = (' (synthetic; enter clock)' if name == 'subject_id' else
                    ' (synthetic)' if name.endswith(('_id', '_role', '_key')) else '')
            value = prompt(name + hint)
            if name in {'now_ms', 'expires_ms', 'slot'}:
                if re.fullmatch(r'[0-9]+', value) is None:
                    raise _ConsoleInputError(name + ' requires an explicit nonnegative integer')
                value = int(value)
            elif not value or value != value.strip():
                raise _ConsoleInputError(name + ' requires an explicit value without surrounding whitespace')
            values[name] = value
        return values

    def send(operation, arguments):
        nonlocal last_reply, rejected
        reply = client.request(dict(surface='booking', operation=operation, arguments=arguments))
        # Save before rendering: output failure must retain a received result.
        last_reply = reply
        print('desk=' + _json(reply), file=output_stream, flush=True)
        if 'error' in reply:
            rejected = True
            if (reply['surface'] is None or reply['operation'] is None or
                    reply['error'].get('type') in {'FixtureError', 'BookingInputError'}):
                raise _TerminalReply('terminal desk error; original envelope retained')
        return reply

    try:
        print('Local synthetic booking console — MOCK_GATE_ONLY, in-memory.\n'
              'Confirmation is a mock reservation action. Payment and chain issuance are separate.\n'
              'Product policy: UNDETERMINED — Astra/User; legal effects: UNDETERMINED — User/legal.',
              file=output_stream)
        while True:
            print('Actions: view_show, set_clock, hold, load_quote, target, preview, confirm, '
                  'view, release, cancel, quit', file=output_stream)
            action = prompt('action')
            try:
                if action == 'quit':
                    return int(rejected)
                if action == 'load_quote':
                    # Invalidate even if loading fails, or bytes are unchanged.
                    pending = None
                    request_text = None
                    path = prompt('UTF-8 quote file path (explicit load/reload)')
                    try:
                        request_text = Path(path).read_bytes().decode('utf-8')
                    except (OSError, UnicodeError) as error:
                        print('input_error=' + _json({'type': type(error).__name__, 'message': str(error)}),
                              file=output_stream)
                    else:
                        print('Quote text loaded unchanged; select target then preview.', file=output_stream)
                elif action == 'target':
                    pending = None
                    target = None
                    target = ConfirmationTarget(**fields(('reservation_id', 'order_id', 'idempotency_key')))
                    print('Confirmation identifiers set; another preview is required.', file=output_stream)
                elif action == 'preview':
                    pending = None
                    if request_text is None or target is None:
                        print('Load quote text and set target before preview.', file=output_stream)
                        continue
                    reply = send('preview_calculated_quote', {'request_text': request_text})
                    if 'quote' in reply:
                        pending = PendingPreview(request_text, target, _json(reply['quote']))
                        print('pending=' + _json(vars(pending.target)), file=output_stream)
                        render_quote(json.loads(pending.quote_json), output_stream)
                elif action == 'confirm':
                    snapshot, pending = pending, None  # consume before prompt/submission
                    if snapshot is None:
                        print('A new successful preview is required.', file=output_stream)
                        continue
                    print('Mock reservation confirmation target=' + _json(vars(snapshot.target)),
                          file=output_stream)
                    render_quote(json.loads(snapshot.quote_json), output_stream)
                    if prompt('Type literal CONFIRM to submit this snapshot; anything else declines') != 'CONFIRM':
                        print('Declined; no confirmation sent. Another preview is required.', file=output_stream)
                        continue
                    send('confirm_calculated_quote', dict(request_text=snapshot.request_text,
                                                          **vars(snapshot.target)))
                elif action in {'view_show', 'set_clock', 'hold', 'view', 'release', 'cancel'}:
                    names = {
                        'view_show': ('show_id',),
                        'set_clock': ('subject_id', 'now_ms', 'idempotency_key'),
                        'hold': ('reservation_id', 'show_id', 'slot', 'buyer_role', 'expires_ms', 'idempotency_key'),
                        'view': ('reservation_id',),
                        'release': ('reservation_id', 'idempotency_key'),
                        'cancel': ('reservation_id', 'idempotency_key'),
                    }[action]
                    send(action, fields(names))
                else:
                    print('Unknown action; choose an action from the menu.', file=output_stream)
            except _ConsoleInputError as error:
                print('input_error=' + _json({'type': type(error).__name__, 'message': str(error)}),
                      file=output_stream)
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
