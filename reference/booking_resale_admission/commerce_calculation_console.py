"""Guided local commerce calculations; no booking confirmation or settlement."""

import argparse
from pathlib import Path
import sys

from booking_console import decimal_amount, _diagnostic
from commerce_calculation_client import CommerceCalculationClient, codec, decode_input


def _json(value):
    return codec().canonical(value)


class ConsoleInputError(ValueError):
    pass


def _parse(payload):
    try:
        return decode_input(payload)
    except (_calculator_rejection(), UnicodeError) as error:
        raise ConsoleInputError(str(error)) from error


def _load(path):
    try:
        with Path(path).open('rb') as stream:
            return _parse(stream.read(codec().MAX_INPUT_BYTES + 1))
    except OSError as error:
        raise ConsoleInputError(str(error)) from error


def _integer(prompt, label):
    value = _parse(prompt(label).encode('utf-8'))
    if type(value) is not int:
        raise ConsoleInputError(label + ' must be an explicit CE1 integer')
    return value


def _compose_quote(prompt):
    """Encode caller-supplied schema 2 input, without calculating or repairing it."""
    from calculated_booking_quote_source import _calculator

    try:
        commerce = _calculator()['commerce']
        candidate = dict(schemaVersion=commerce.SCHEMA, orderId=prompt('orderId'),
                         orderVersion=_integer(prompt, 'orderVersion'))
        candidate['scope'] = {field: prompt('scope.' + field)
                              for field in ('issuerId', 'eventId', 'performanceId')}
        candidate['policyRef'] = prompt('policyRef')
        candidate['expiresAt'] = _integer(prompt, 'expiresAt (Unix milliseconds)')
        count = _integer(prompt, 'Explicit line count')
        if not 1 <= count <= commerce.MAX_LINES:
            raise ConsoleInputError('line count outside existing MAX_LINES bound')
        candidate['lines'] = []
        for index in range(count):
            prefix = 'lines[' + str(index) + '].'
            line = {field: prompt(prefix + field) for field in ('lineId', 'inventoryId')}
            asset = {field: prompt(prefix + 'gross.asset.' + field)
                     for field in ('namespace', 'reference')}
            asset['decimals'] = _integer(prompt, prefix + 'gross.asset.decimals')
            asset['maxAtoms'] = prompt(prefix + 'gross.asset.maxAtoms')
            line['gross'] = dict(asset=asset, atoms=prompt(prefix + 'gross.atoms'))
            candidate['lines'].append(line)
        count = _integer(prompt, 'Explicit discount count')
        if not 0 <= count <= commerce.MAX_RULES:
            raise ConsoleInputError('discount count outside existing MAX_RULES bound')
        candidate['discounts'] = []
        for index in range(count):
            prefix = 'discounts[' + str(index) + '].'
            rule = {field: prompt(prefix + field) for field in ('ruleId', 'bearerRef', 'kind', 'value')}
            eligible = _parse(prompt(prefix + 'eligibleLineIds (JSON string array)').encode('utf-8'))
            if type(eligible) is not list or any(type(item) is not str for item in eligible):
                raise ConsoleInputError('eligibleLineIds must be an explicit JSON array of strings')
            rule['eligibleLineIds'] = eligible
            cap = _parse(prompt(prefix + 'capAtoms (JSON string or null)').encode('utf-8'))
            if cap is not None and type(cap) is not str:
                raise ConsoleInputError('capAtoms must be an explicit JSON string or null')
            rule['capAtoms'] = cap
            candidate['discounts'].append(rule)
        return codec().canonical_bytes(candidate)
    except (_calculator_rejection(), UnicodeError) as error:
        raise ConsoleInputError(str(error)) from error


def _compose_legs(prompt):
    """Freeze explicit local input; business validation belongs to the driver."""
    from calculated_booking_quote_source import _calculator

    try:
        count = _integer(prompt, 'Explicit payment leg count')
        if not 0 <= count <= _calculator()['commerce'].MAX_LEGS:
            raise ConsoleInputError('payment leg count outside existing MAX_LEGS bound')
        candidate = []
        for index in range(count):
            prefix = 'legs[' + str(index) + '].'
            leg = {field: prompt(prefix + field) for field in ('legId', 'providerRef', 'routeRef')}
            asset = {field: prompt(prefix + 'amount.asset.' + field)
                     for field in ('namespace', 'reference')}
            asset['decimals'] = _integer(prompt, prefix + 'amount.asset.decimals')
            asset['maxAtoms'] = prompt(prefix + 'amount.asset.maxAtoms')
            leg['amount'] = dict(asset=asset, atoms=prompt(prefix + 'amount.atoms'))
            candidate.append(leg)
        return codec().canonical_bytes(candidate)
    except (_calculator_rejection(), UnicodeError) as error:
        raise ConsoleInputError(str(error)) from error


def _pick_lines(prompt, snapshot, output_stream):
    """Display returned rows and encode literal selections; calculate nothing."""
    from calculated_booking_quote_source import _calculator

    print('quoteHash=' + snapshot['quoteHash'], file=output_stream)
    print('asset=' + _json(snapshot['asset']), file=output_stream)
    for row in snapshot['lines']:
        print('refund_line=' + _json({field: row[field] for field in
              ('lineId', 'inventoryId', 'grossAtoms', 'discountAtoms', 'payableAtoms')}), file=output_stream)
    try:
        count = _integer(prompt, 'Explicit selected line count')
        if not 0 <= count <= _calculator()['commerce'].MAX_LINES:
            raise ConsoleInputError('selected line count outside existing MAX_LINES bound')
        candidate = [prompt('line_ids[' + str(index) + ']') for index in range(count)]
        return codec().canonical_bytes(candidate)
    except (_calculator_rejection(), UnicodeError) as error:
        raise ConsoleInputError(str(error)) from error


def _render(exchange, stream):
    response = exchange.response
    print('driver=' + _json(response), file=stream, flush=True)
    if response['ok'] and 'totals' in response['result']:
        result = response['result']
        print('payableAtoms=' + result['totals']['payableAtoms'] + ' decimal=' +
              decimal_amount(result['totals']['payableAtoms'], result['asset']['decimals']), file=stream)


def run_console(client, *, input_stream, output_stream, error_stream):
    """0 clean exit/decline/EOF; 1 known input/calculation refusal; 2 fenced.

    All selections and history are process-local. Retained exchanges are frozen
    bytes, and all subsequent requests decode fresh copies of those exact bytes.
    Input changes invalidate active dependents before reading replacement inputs.
    """
    quote_input = legs = selected = None
    quote = plan = refund = None
    history = []
    rejected = False
    last_reply = None

    def prompt(label):
        print(label + ': ', end='', file=output_stream, flush=True)
        line = input_stream.readline()
        if line == '':
            raise EOFError
        return line.removesuffix('\n').removesuffix('\r')

    def submit(action, args, literal):
        nonlocal rejected, last_reply
        envelope = dict(action=action, args=args)
        print('proposed=' + _json(envelope), file=output_stream)
        if prompt('Type literal ' + literal + ' to calculate once; anything else declines') != literal:
            print('Declined; no calculation submitted.', file=output_stream)
            return None
        exchange = client.request(envelope)
        # Retain before any rendering, including failing output sinks.
        last_reply = exchange.response
        if last_reply['ok']:
            history.append(exchange)
        else:
            rejected = True
        _render(exchange, output_stream)
        return exchange if last_reply['ok'] else None

    try:
        print('Local synthetic commerce console — CALCULATION_ONLY; in-memory.\n'
              'No booking confirmation, payment, refund execution or settlement.\n'
              'Product policy: UNDETERMINED — Astra/User.\n'
              'Legal/accounting treatment: UNDETERMINED — User/designated advisers.', file=output_stream)
        while True:
            print('Actions: load_quote, compose_quote, simulate_quote, load_legs, compose_legs, plan_payments, select_lines, '
                  'pick_lines, propose_line_refund, show, quit', file=output_stream)
            action = prompt('action')
            try:
                if action == 'quit':
                    return int(rejected)
                if action == 'load_quote':
                    quote_input = quote = plan = refund = selected = None
                    value = _load(prompt('Quote request JSON file path'))
                    if type(value) is not dict:
                        raise ConsoleInputError('quote request must be an object')
                    quote_input = codec().canonical_bytes(value)
                    print('Quote input loaded; active quote, plan and line selections invalidated.', file=output_stream)
                elif action == 'compose_quote':
                    quote_input = quote = plan = refund = selected = None
                    quote_input = _compose_quote(prompt)
                    print('composed_quote=' + quote_input.decode('utf-8'), file=output_stream)
                elif action == 'simulate_quote':
                    quote = plan = refund = selected = None
                    if quote_input is None:
                        print('Load a quote request first.', file=output_stream)
                        continue
                    quote = submit(action, decode_input(quote_input), 'SUBMIT_QUOTE')
                elif action == 'load_legs':
                    legs = plan = refund = selected = None
                    value = _load(prompt('Payment legs JSON array file path'))
                    if type(value) is not list:
                        raise ConsoleInputError('payment legs must be an array')
                    legs = codec().canonical_bytes(value)
                    print('Legs loaded; active plan and line selections invalidated.', file=output_stream)
                elif action == 'compose_legs':
                    legs = plan = refund = selected = None
                    legs = _compose_legs(prompt)
                    print('composed_legs=' + legs.decode('utf-8'), file=output_stream)
                elif action == 'plan_payments':
                    plan = refund = selected = None
                    if quote is None or legs is None:
                        print('A successful active quote and loaded legs are required.', file=output_stream)
                        continue
                    now = _parse(prompt('Explicit synthetic now (Unix milliseconds)').encode('utf-8'))
                    if type(now) is not int or now < 0:
                        raise ConsoleInputError('now must be an explicit nonnegative safe JSON integer')
                    snapshot = quote.response['result']
                    plan = submit(action, dict(quote=snapshot, legs=decode_input(legs),
                                              expected_quote_hash=snapshot['quoteHash'], now=now), 'SUBMIT_PLAN')
                elif action == 'select_lines':
                    selected = refund = None
                    value = _parse(prompt('Explicit line IDs JSON array').encode('utf-8'))
                    if type(value) is not list or any(type(item) is not str for item in value):
                        raise ConsoleInputError('line IDs must be an array of strings')
                    selected = codec().canonical_bytes(value)
                    print('Line selection loaded; submit separately for driver validation.', file=output_stream)
                elif action == 'pick_lines':
                    selected = refund = None
                    if quote is None:
                        print('A successful active quote is required to pick lines.', file=output_stream)
                        continue
                    selected = _pick_lines(prompt, quote.response['result'], output_stream)
                    print('selected_lines=' + selected.decode('utf-8'), file=output_stream)
                    print('Line selection loaded; submit separately for driver validation.', file=output_stream)
                elif action == 'propose_line_refund':
                    refund = None
                    if quote is None or plan is None or selected is None:
                        print('Active quote, plan and explicit line selection are required.', file=output_stream)
                        continue
                    snapshot = plan.response['result']
                    refund = submit(action, dict(quote=quote.response['result'], payment_plan=snapshot,
                                                line_ids=decode_input(selected),
                                                expected_plan_hash=snapshot['planHash']), 'SUBMIT_REFUND')
                elif action == 'show':
                    print('active=' + _json({name: None if exchange is None else exchange.response['result'][field]
                          for name, exchange, field in (('quote', quote, 'quoteHash'), ('plan', plan, 'planHash'),
                                                        ('refund', refund, 'proposalHash'))}), file=output_stream)
                    print('Historical successful exchanges (not active selections):', file=output_stream)
                    for exchange in history:
                        _render(exchange, output_stream)
                else:
                    print('Unknown local action; no calculation submitted.', file=output_stream)
            except ConsoleInputError as error:
                rejected = True
                print('input_error=' + _json(dict(type=type(error).__name__, message=str(error))), file=output_stream)
    except EOFError:
        print('EOF; no further calculations submitted.', file=output_stream)
        return int(rejected)
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, error_stream, last_reply=last_reply)
        return 2


def _calculator_rejection():
    # CE1 input refusals remain local; transport uncertainty is terminal.
    from calculated_booking_quote_source import _calculator
    return _calculator()['common'].Rejected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cleanup-timeout', required=True, type=float,
                        help='positive child cleanup budget; not a business or response deadline')
    args = parser.parse_args(argv)
    try:
        client = CommerceCalculationClient(cleanup_timeout=args.cleanup_timeout)
    except ValueError as error:
        parser.error(str(error))
    return run_console(client, input_stream=sys.stdin, output_stream=sys.stdout, error_stream=sys.stderr)


if __name__ == '__main__':
    raise SystemExit(main())
