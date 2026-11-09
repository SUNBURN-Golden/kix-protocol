"""Compose synthetic supply events and compare one returned report in memory."""

import argparse
import re
import sys

from reward_fixture import FixtureError, decode_json, validate_json
from supply_reconciliation import NOTICE, dispatch_request, supply_output
from token_reward_model import TokenRewardError, _canonical, _money, _supply_event


_ACTIONS = ('add_event', 'replace_event', 'replace_events', 'show',
            'calculate', 'reconcile', 'quit')


class _Cancelled(Exception):
    pass


def run_console(*, input_stream, output_stream, error_stream) -> int:
    """Use literal confirmations; never dispatch previews, edits or retries.

    0: clean quit (declines/cancellation allowed); 1: sticky dispatch domain
    rejection; 2: sticky invalid input or terminal input/I/O/interruption failure.
    """
    events = active_report = active_comparison = None
    status = 0
    operation = None

    def tell(message):
        print(message, file=error_stream, flush=True)

    def prompt(label):
        print(label + ': ', end='', file=error_stream, flush=True)
        line = input_stream.readline()
        if line == '':
            raise EOFError('input ended; no further dispatch')
        raw = line.removesuffix('\n').removesuffix('\r')
        if raw == ':cancel':
            raise _Cancelled()
        validate_json(raw)
        return raw

    def integer(label, *, positive=False, supply_amount=True):
        raw = prompt(label + ' (explicit decimal integer)')
        if re.fullmatch(r'-?[0-9]+', raw) is None:
            raise FixtureError(label + ' requires an explicit decimal integer')
        try:
            number = int(raw)
        except ValueError as error:
            raise FixtureError(label + ' integer is too long') from error
        if supply_amount:
            return _money(number, positive=positive)
        if number < 0:
            raise FixtureError(label + ' requires a nonnegative integer')
        return number

    def event():
        value = {'event_id': prompt('event_id (verbatim string)'),
                 'op': prompt('op (MINT / ALLOCATE / BURN / HOLDER_BURN)'),
                 'amount': integer('amount', positive=True)}
        for field in ('approved', 'path_approved'):
            raw = prompt(field + ' (literal true / false; synthetic assertion)')
            if raw not in ('true', 'false'):
                raise FixtureError(field + ' requires literal true or false')
            value[field] = raw == 'true'
        program = decode_json(prompt('program (explicit JSON string or null)'))
        if program is not None and type(program) is not str:
            raise FixtureError('program requires a JSON string or null')
        value['program'] = program
        validate_json(value)
        _supply_event(value)  # Individual predicates only; no report arithmetic.
        return value

    def emit(reply):
        print(_canonical(reply), file=output_stream, flush=True)

    def input_error(error):
        if isinstance(error, TokenRewardError):
            detail = {'code': error.code}
        else:
            detail = {'type': type(error).__name__, 'message': str(error)}
        emit(supply_output(operation, error=detail))

    try:
        tell('Local supply console — MOCK_TOKEN_REWARD_ONLY / CALCULATION_ONLY / '
             'SYNTHETIC_SUPPLY_FIGURE\n' + NOTICE + '\n'
             'State is in memory. :cancel abandons the current action. '
             'show displays active selections; no calculation occurs on editing.')
        while True:
            operation = None
            tell('Actions: ' + ', '.join(_ACTIONS))
            try:
                action = prompt('action')
                if action == 'quit':
                    return status
                if action not in _ACTIONS:
                    raise FixtureError('choose an action from the menu')
                if action == 'show':
                    tell('active=' + _canonical({'events': events, 'report': active_report,
                                                 'comparison': active_comparison}))
                    continue
                if action in ('add_event', 'replace_event', 'replace_events'):
                    # Invalidate immediately, even if editing fails or is cancelled.
                    active_report = active_comparison = None
                    if action == 'replace_events':
                        count = integer('event count (zero explicitly selects [])', supply_amount=False)
                        staged = [event() for _ in range(count)]
                    elif action == 'add_event':
                        staged = ([] if events is None else list(events)) + [event()]
                    else:
                        if not events:
                            raise FixtureError('replace_event requires composed events')
                        tell('events=' + _canonical(list(enumerate(events, start=1))))
                        position = integer('event position (1-based)', positive=True)
                        if position > len(events):
                            raise FixtureError('position is outside the displayed events')
                        staged = list(events)
                        staged[position - 1] = event()
                    events = staged  # Install only a complete edit, preserving order.
                    tell('Events selected. Active report and comparison cleared.')
                    continue
                if action == 'calculate':
                    active_report = active_comparison = None
                    operation = 'supply_report'
                    if events is None:
                        raise FixtureError('compose events first; replace_events with count 0 selects []')
                    request = {'operation': operation, 'arguments': {'events': events}}
                    confirmation = 'CALCULATE'
                else:
                    active_comparison = None
                    operation = 'reconcile_supply'
                    if active_report is None:
                        raise FixtureError('calculate a report successfully first')
                    chain_supply = integer('chain_supply (SYNTHETIC_SUPPLY_FIGURE)')
                    request = {'operation': operation, 'arguments': {
                        'offchain': active_report, 'chain_supply': chain_supply}}
                    confirmation = 'RECONCILE'
                validate_json(request)
                tell('proposed=' + _canonical(request))
                if prompt('Type literal ' + confirmation + ' to dispatch once; anything else declines') != confirmation:
                    tell('Declined; no request sent. Previous result selection cleared.')
                    continue
            except _Cancelled:
                tell('Cancelled; no request sent. Invalidated selections remain cleared.')
                continue
            except (FixtureError, TokenRewardError) as error:
                status = 2
                input_error(error)
                continue

            # The only dispatcher call. Failures never cause an automatic retry.
            try:
                reply = dispatch_request(request)
            except TokenRewardError as error:
                status = max(status, 1)
                emit(supply_output(operation, error={'code': error.code}))
                continue
            except FixtureError as error:
                input_error(error)
                return 2
            emit(reply)  # Preserve the entire response, including metadata.
            if operation == 'supply_report':
                active_report = reply['result']  # Forward this exact object later.
            else:
                active_comparison = reply['result']
    except (Exception, KeyboardInterrupt) as error:
        # Stop on terminal failures, including failed preview/result writes.
        # Best-effort diagnostics cannot authorize another dispatch.
        try:
            message = str(error).encode('utf-8', errors='backslashreplace').decode('utf-8')
            tell('terminal_error=' + _canonical({'type': type(error).__name__, 'message': message}))
        except (Exception, KeyboardInterrupt):
            pass
        return 2


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    # Incremental strict UTF-8 decoding: invalid later input cannot be read ahead
    # by a buffered text wrapper before an earlier confirmed action completes.
    class UTF8Lines:
        def readline(self):
            return sys.stdin.buffer.readline().decode('utf-8')

    return run_console(input_stream=UTF8Lines() if hasattr(sys.stdin, 'buffer') else sys.stdin,
                       output_stream=sys.stdout, error_stream=sys.stderr)


if __name__ == '__main__':
    raise SystemExit(main())
