"""Single-writer, one-process-per-calculation client. No retry or execution.

Construction/import launches nothing. A transport or response validation failure
permanently fences the instance. Hash verification is not authenticated authority.
All arithmetic belongs to the unchanged commerce driver, never this client.
"""

from dataclasses import dataclass
import math
from pathlib import Path
import subprocess
import sys
import threading

from calculated_booking_quote_source import _calculator


def codec():
    return _calculator()['canonical_encoding']


def decode_input(payload):
    """Decode original bytes before any reserialization can lose token evidence."""
    return codec().decode_json(payload)


@dataclass(frozen=True)
class CalculationExchange:
    request_bytes: bytes
    reply_bytes: bytes
    returncode: int

    @property
    def response(self):
        # Every access is detached, including nested arrays and dictionaries.
        return decode_input(self.reply_bytes.removesuffix(b'\n'))


class CalculationClientStateError(RuntimeError):
    pass


class CalculationUncertainty(RuntimeError):
    def __init__(self, request_bytes, reply_bytes, returncode):
        super().__init__('calculation exchange uncertain; client fenced; no retry')
        self.request_bytes = request_bytes
        self.reply_bytes = reply_bytes
        self.returncode = returncode


def _check(predicate, message='invalid calculation response'):
    if not predicate:
        raise ValueError(message)


def _fields(value, names):
    _check(type(value) is dict and set(value) == set(names.split()))


def _ids(values):
    _check(type(values) is list)
    for value in values:
        codec().machine_id(value)
    _check(len(set(values)) == len(values))


def _atoms(value, asset):
    # Reuse the wire amount validator; no allocations/totals are computed here.
    _calculator()['assets'].Amount.from_dict(dict(asset=asset, atoms=value))


def _amount(value, asset):
    _fields(value, 'asset atoms')
    _check(value['asset'] == asset)
    _atoms(value['atoms'], asset)


def _allocations(value, ids, asset):
    _check(type(value) is dict and set(value) == set(ids))
    for atoms in value.values():
        _atoms(atoms, asset)


def _hashed(result, field, domain):
    _check(type(result.get(field)) is str)
    content = {key: value for key, value in result.items() if key != field}
    _check(codec().digest(domain, content) == result[field], 'response hash mismatch')


def _validate_result(result, action, args):
    commerce = _calculator()['commerce']
    _check(type(result) is dict and result.get('schemaVersion') == commerce.SCHEMA
           and result.get('evidenceClass') == 'CALCULATION_ONLY')
    if action == 'simulate_quote':
        _fields(result, 'schemaVersion evidenceClass request asset lines totals quoteHash')
        _check(codec().canonical_bytes(result['request']) == codec().canonical_bytes(args), 'quote request binding mismatch')
        asset = result['asset']
        _calculator()['assets'].AssetSpec.from_dict(asset)
        _fields(result['totals'], 'grossAtoms discountAtoms payableAtoms')
        for value in result['totals'].values():
            _atoms(value, asset)
        _check(type(result['lines']) is list and 0 < len(result['lines']) <= commerce.MAX_LINES)
        _ids([row['lineId'] for row in result['lines']])
        _check([row['lineId'] for row in result['lines']] == sorted(line['lineId'] for line in args['lines']))
        original = {line['lineId']: line for line in args['lines']}
        rules = {rule['ruleId']: rule for rule in args['discounts']}
        for row in result['lines']:
            _fields(row, 'lineId inventoryId grossAtoms discountAtoms payableAtoms discounts')
            codec().machine_id(row['inventoryId'])
            line = original[row['lineId']]
            _check(row['inventoryId'] == line['inventoryId'] and asset == line['gross']['asset']
                   and row['grossAtoms'] == line['gross']['atoms'])
            for field in ('grossAtoms', 'discountAtoms', 'payableAtoms'):
                _atoms(row[field], asset)
            _check(type(row['discounts']) is list)
            for discount in row['discounts']:
                _fields(discount, 'ruleId bearerRef atoms')
                codec().machine_id(discount['ruleId'])
                codec().machine_id(discount['bearerRef'])
                rule = rules[discount['ruleId']]
                _check(discount['bearerRef'] == rule['bearerRef'] and row['lineId'] in rule['eligibleLineIds'])
                _atoms(discount['atoms'], asset)
        _hashed(result, 'quoteHash', commerce.QUOTE_HASH_DOMAIN)
        return
    quote = args['quote']
    asset = quote['asset']
    ids = [row['lineId'] for row in quote['lines']]
    _check(type(result['quoteHash']) is str and result['quoteHash'] == quote['quoteHash'],
           'quote hash binding mismatch')
    if action == 'plan_payments':
        _fields(result, 'schemaVersion evidenceClass quoteHash checkedAt legs planHash')
        _check(result['quoteHash'] == args['expected_quote_hash'])
        _check(type(result['checkedAt']) is int and result['checkedAt'] >= 0 and result['checkedAt'] == args['now'])
        _check(type(result['legs']) is list and len(result['legs']) == len(args['legs']) <= commerce.MAX_LEGS)
        _ids([leg['legId'] for leg in result['legs']])
        for leg, original in zip(result['legs'], args['legs']):
            _fields(leg, 'legId providerRef routeRef amount allocations')
            for field in ('providerRef', 'routeRef'):
                codec().machine_id(leg[field])
            _check(codec().canonical_bytes({key: leg[key] for key in original}) == codec().canonical_bytes(original))
            _amount(leg['amount'], asset)
            _allocations(leg['allocations'], ids, asset)
        _hashed(result, 'planHash', commerce.PAYMENT_PLAN_HASH_DOMAIN)
    else:
        _fields(result, 'schemaVersion evidenceClass policy quoteHash planHash lineIds grossReversed '
                'customerRefund originalRoutes discountBurdenReversal executionAuthorized requiredEvidence proposalHash')
        plan = args['payment_plan']
        _check(type(result['planHash']) is str and result['planHash'] == plan['planHash'] == args['expected_plan_hash'])
        _check(result['policy'] == 'FROZEN_LINE_PRICE_FULL_REVERSAL_V1')
        _ids(result['lineIds'])
        _check(0 < len(result['lineIds']) <= commerce.MAX_LINES and set(result['lineIds']) <= set(ids)
               and result['lineIds'] == sorted(args['line_ids']))
        _check(result['executionAuthorized'] is False)
        _check(result['requiredEvidence'] == ['CONFIRMED_ORIGINAL_PAYMENTS', 'CURRENT_LINE_RIGHT_STATE',
               'REFUND_POLICY_AUTHORITY', 'UNRESOLVED_REFUND_RESERVATIONS', 'CURRENT_PROVIDER_REFUNDABLE_CAPACITY'])
        for field in ('grossReversed', 'customerRefund'):
            _amount(result[field], asset)
        _check(type(result['discountBurdenReversal']) is dict)
        selected_bearers = {discount['bearerRef'] for row in quote['lines'] if row['lineId'] in result['lineIds']
                            for discount in row['discounts']}
        _check(set(result['discountBurdenReversal']) <= selected_bearers)
        for bearer, value in result['discountBurdenReversal'].items():
            codec().machine_id(bearer)
            _atoms(value, asset)
        _check(type(result['originalRoutes']) is list)
        _ids([route['legId'] for route in result['originalRoutes']])
        originals = {leg['legId']: leg for leg in plan['legs']}
        positions = []
        for route in result['originalRoutes']:
            _fields(route, 'legId providerRef routeRef amount allocations')
            for field in ('providerRef', 'routeRef'):
                codec().machine_id(route[field])
            original = originals[route['legId']]
            positions.append(next(i for i, leg in enumerate(plan['legs']) if leg['legId'] == route['legId']))
            _check(all(route[key] == original[key] for key in ('providerRef', 'routeRef')))
            _amount(route['amount'], asset)
            _allocations(route['allocations'], result['lineIds'], asset)
            _check(route['allocations'] == {key: original['allocations'][key] for key in result['lineIds']})
        _check(positions == sorted(positions))
        _hashed(result, 'proposalHash', commerce.REFUND_PROPOSAL_HASH_DOMAIN)


def _validate_reply(raw, returncode, request):
    _check(raw.endswith(b'\n'), 'incomplete response')
    reply = decode_input(raw[:-1])
    _check(type(reply) is dict and type(reply.get('ok')) is bool)
    _check(reply.get('evidenceClass') == 'CALCULATION_ONLY')
    if reply['ok']:
        _fields(reply, 'ok evidenceClass result')
        _check(returncode == 0, 'inconsistent successful exit')
        _validate_result(reply['result'], request['action'], request['args'])
    else:
        _fields(reply, 'ok evidenceClass error')
        _check(returncode == 2 and type(reply['error']) is str and bool(reply['error']),
               'inconsistent rejection')


class CommerceCalculationClient:
    def __init__(self, *, cleanup_timeout):
        if (isinstance(cleanup_timeout, bool) or not isinstance(cleanup_timeout, (int, float))
                or not math.isfinite(cleanup_timeout) or cleanup_timeout <= 0):
            raise ValueError('cleanup_timeout must be finite and positive')
        self._cleanup_timeout = cleanup_timeout
        self._guard = threading.Lock()
        self._fenced = False
        self.uncertainty = None
        self._history = []
        self.last_exchange = None

    @property
    def history(self):
        """Historical successful exchanges; never authority to reuse a selection."""
        return tuple(self._history)

    def _reap(self, process):
        try:
            process.terminate()
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=self._cleanup_timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def request(self, envelope):
        if not self._guard.acquire(blocking=False):
            raise CalculationClientStateError('another calculation is outstanding')
        try:
            if self._fenced:
                raise CalculationClientStateError('client fenced')
            wire = codec().canonical_bytes(envelope)
            submitted = decode_input(wire)
            _fields(submitted, 'action args')
            _check(type(submitted['action']) is str and submitted['action'] in
                   {'simulate_quote', 'plan_payments', 'propose_line_refund'}, 'action not allowed')
            _check(type(submitted['args']) is dict)
            process = None
            raw = bytearray()
            try:
                driver = Path(__file__).resolve().parents[1] / 'v0.3-rc1' / 'commerce_driver.py'
                process = subprocess.Popen([sys.executable, str(driver)], stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE, shell=False)
                # The real driver reads until EOF. No persistent JSONL transport.
                written = process.stdin.write(wire)
                if written != len(wire):
                    raise OSError('short request write')
                process.stdin.close()
                while True:
                    chunk = process.stdout.read(1)
                    if not chunk:
                        break
                    raw.extend(chunk)
                    if len(raw) > codec().MAX_INPUT_BYTES + 1:
                        raise ValueError('response too large')
                returncode = process.wait()
                _validate_reply(bytes(raw), returncode, submitted)
                exchange = CalculationExchange(wire, bytes(raw), returncode)
                self.last_exchange = exchange
                if exchange.response['ok']:
                    self._history.append(exchange)
                return exchange
            except BaseException as error:
                self._fenced = True
                self.uncertainty = CalculationUncertainty(wire, bytes(raw),
                                                         None if process is None else process.returncode)
                if process is not None:
                    try:
                        self._reap(process)
                    except BaseException as cleanup_error:
                        self.uncertainty.cleanup_error = repr(cleanup_error)
                    self.uncertainty.returncode = process.returncode
                raise self.uncertainty from error
            finally:
                if process is not None:
                    for stream in (process.stdin, process.stdout):
                        if stream is not None:
                            try:
                                stream.close()
                            except OSError:
                                pass
        finally:
            self._guard.release()
