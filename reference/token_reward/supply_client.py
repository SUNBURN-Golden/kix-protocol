"""One synthetic supply request per child; no retry, fallback or response timer.

Construction launches nothing. An uncertain transport permanently fences the
instance. cleanup_timeout is an explicit cleanup bound, never a policy value.
"""

from dataclasses import dataclass
import math
from pathlib import Path
import subprocess
import sys
import threading

from reward_fixture import FixtureError, decode_json, exact_fields, validate_json
from supply_reconciliation import NOTICE, OPERATIONS
from token_reward_model import (ALARM_HOLDER_BURN, ALARM_MATCH, ALARM_UNAPPROVED_MINT,
                                ALARM_UNAPPROVED_PATH, ALARM_UNEXPLAINED, PROVENANCE,
                                SUPPLY_REPORT_FIELDS, _canonical, _money, _supply_event)


class SupplyClientStateError(RuntimeError):
    """Rejected locally: busy, closed, terminal or uncertain; no child launched."""


class SupplyTransportUncertainty(RuntimeError):
    """Observed transport evidence; never a calculation result or retry permit."""

    def __init__(self, phase, request_bytes, stdout, stderr, returncode):
        super().__init__(f"local supply {phase} uncertain; client fenced")
        self.phase = phase
        self.request_bytes = request_bytes
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


@dataclass(frozen=True)
class SupplyResponse:
    reply: dict
    returncode: int
    stdout: bytes
    stderr: bytes


def validate_cleanup_timeout(value):
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and value > 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("cleanup_timeout must be a finite positive number")


class SupplyClient:
    """Own at most one child/exchange. Call close() or use a context manager.

    Reads block until completion or caller interruption. Interrupt the requesting
    caller before cleanup; concurrent requests/close reject without launching.
    """

    def __init__(self, *, cleanup_timeout):
        validate_cleanup_timeout(cleanup_timeout)
        self._cleanup_timeout = cleanup_timeout
        self._guard = threading.Lock()
        self._process = None
        self._closed = self._terminal = False
        self.uncertainty = None

    @staticmethod
    def _validate_request(request):
        validate_json(request)
        exact_fields(request, {"operation", "arguments"}, "request")
        operation = request['operation']
        if type(operation) is not str or operation not in OPERATIONS:
            raise FixtureError("unsupported supply operation")
        fields = {"events"} if operation == 'supply_report' else {"offchain", "chain_supply"}
        exact_fields(request['arguments'], fields, 'arguments')

    @staticmethod
    def _reply(raw, returncode, request):
        if type(returncode) is not int:
            raise FixtureError('missing or invalid exit status')
        reply = decode_json(raw.decode('utf-8'))
        if type(reply) is not dict:
            raise FixtureError('response must be an object')
        payload = set(reply) & {'result', 'error'}
        if len(payload) != 1:
            raise FixtureError('response requires exactly one payload')
        exact_fields(reply, {'operation', 'provenance', 'evidence_class', 'notice'} | payload,
                     'response')
        if (reply['operation'] != request['operation'] or reply['provenance'] != PROVENANCE
                or reply['evidence_class'] != 'CALCULATION_ONLY' or reply['notice'] != NOTICE):
            raise FixtureError('response operation or synthetic metadata mismatch')
        if returncode in (1, 2):
            fields = {'code'} if returncode == 1 else {'type', 'message'}
            if payload != {'error'}:
                raise FixtureError('error exit requires error payload')
            exact_fields(reply['error'], fields, 'response error')
            if any(type(reply['error'][field]) is not str for field in fields):
                raise FixtureError('error values must be strings')
        elif returncode == 0 and payload == {'result'}:
            result = reply['result']
            if request['operation'] == 'supply_report':
                exact_fields(result, {'events', 'figure', *SUPPLY_REPORT_FIELDS}, 'report')
                if type(result['events']) is not list:
                    raise FixtureError('report events must be an array')
                for event in result['events']:
                    _supply_event(event)  # Shape/predicates only; never calculate totals.
                for field in SUPPLY_REPORT_FIELDS:
                    _money(result[field], positive=False)
                if _canonical(result['events']) != _canonical(request['arguments']['events']):
                    raise FixtureError('returned events differ from submitted events')
            else:
                exact_fields(result, {'alarm', 'mismatch', 'stop_payout', 'offchain_supply',
                                      'chain_supply', 'figure'}, 'comparison')
                if (type(result['alarm']) is not str or result['alarm'] not in {
                        ALARM_MATCH, ALARM_HOLDER_BURN, ALARM_UNEXPLAINED,
                        ALARM_UNAPPROVED_MINT, ALARM_UNAPPROVED_PATH}
                        or type(result['mismatch']) is not bool
                        or type(result['stop_payout']) is not bool):
                    raise FixtureError('invalid comparison types')
                for field in ('offchain_supply', 'chain_supply'):
                    _money(result[field], positive=False)
                if _canonical(result['chain_supply']) != _canonical(request['arguments']['chain_supply']):
                    raise FixtureError('returned chain_supply differs from submitted value')
            if result['figure'] != 'SYNTHETIC_SUPPLY_FIGURE':
                raise FixtureError('invalid figure label')
        else:
            raise FixtureError('unexpected exit status or payload')
        return reply

    def _cleanup(self):
        """Terminate, drain and reap an interrupted child with bounded escalation."""
        process = self._process
        if process is None:
            return b'', b''
        try:
            try:
                process.terminate()
            except ProcessLookupError:
                pass  # It exited between interruption and cleanup.
            try:
                return process.communicate(timeout=self._cleanup_timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                return process.communicate(timeout=self._cleanup_timeout)
        except BaseException:
            # A second interruption must still attempt to reap the owned child.
            process.kill()
            process.wait(timeout=self._cleanup_timeout)
            raise
        finally:
            for pipe in (process.stdin, process.stdout, process.stderr):
                if pipe is not None:
                    pipe.close()
            if process.returncode is not None:
                self._process = None

    def request(self, request):
        if not self._guard.acquire(blocking=False):
            raise SupplyClientStateError('another request or cleanup is outstanding')
        try:
            if self._closed or self._terminal:
                raise SupplyClientStateError('client is closed, terminal or uncertain')
            self._validate_request(request)
            wire = (_canonical(request) + '\n').encode('utf-8')
            submitted = decode_json(wire.decode('utf-8'))
            phase, stdout, stderr, returncode = 'launch', b'', b'', None
            try:
                command = [sys.executable, str(Path(__file__).with_name('supply_cli.py').resolve()),
                           '--request', '-']
                self._process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                 shell=False)
                phase = 'communicate'
                stdout, stderr = self._process.communicate(input=wire)
                returncode = self._process.returncode
                phase = 'decode'
                reply = self._reply(stdout, returncode, submitted)
                self._terminal = returncode == 2
                self._process = None  # communicate closed pipes and reaped the child.
                return SupplyResponse(reply, returncode, stdout, stderr)
            except BaseException as error:
                self._terminal = True
                uncertainty = SupplyTransportUncertainty(phase, wire, stdout, stderr, returncode)
                # Timeout/I/O implementations may expose bytes already observed.
                for field, attribute in (('stdout', 'output'), ('stderr', 'stderr')):
                    observed = getattr(error, attribute, None)
                    if isinstance(observed, bytes):
                        setattr(uncertainty, field, observed)
                self.uncertainty = uncertainty
                try:
                    process = self._process
                    if process is not None:
                        if process.returncode is None:
                            stdout, stderr = self._cleanup()
                        else:
                            # Reaped does not imply communicate finished draining
                            # or closing pipes when it raised an I/O exception.
                            for pipe in (process.stdin, process.stdout, process.stderr):
                                if pipe is not None:
                                    pipe.close()
                            self._process = None
                        uncertainty.stdout = stdout or uncertainty.stdout
                        uncertainty.stderr = stderr or uncertainty.stderr
                        uncertainty.returncode = process.returncode
                except BaseException as cleanup_error:
                    uncertainty.returncode = process.returncode
                    for field, attribute in (('stdout', 'output'), ('stderr', 'stderr')):
                        observed = getattr(cleanup_error, attribute, None)
                        if isinstance(observed, bytes):
                            setattr(uncertainty, field, observed)
                    uncertainty.add_note(f'cleanup raised {type(cleanup_error).__name__}: {cleanup_error}')
                raise uncertainty from error
        finally:
            self._guard.release()

    def close(self):
        if not self._guard.acquire(blocking=False):
            raise SupplyClientStateError('another request or cleanup is outstanding')
        try:
            self._terminal = self._closed = True
            self._cleanup()
        finally:
            self._guard.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
