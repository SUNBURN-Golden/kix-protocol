"""Loopback HTTP transport for the published local-call envelope.

Binds to 127.0.0.1 only. Dispatches POST /x-kix-contract-only/local-call to
the reference Core.execute. An optional process-local readiness journal can
replay committed receipts after restart. That journal is not protocol truth.
Does not attach payment, KYC, venue, or bank adapters. Not a production endpoint.
Opt-in CORS for http://127.0.0.1:5173 is off unless --browser-origin is set.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import queue
import re
import secrets
from socketserver import ThreadingMixIn
import socket
import sys
import threading
import time

from integration_gate.audit import emit
from integration_gate.catalogue import CatalogueError, load_catalogue, reference_types
from integration_gate.constants import (
    BROWSER_ALLOWED_ORIGIN,
    BROWSER_ALLOWED_REQUEST_HEADERS,
    CORRELATION_HEADER,
    DEFAULT_TIMEOUT_SECONDS,
    HEADER_LIMIT_BYTES,
    HEALTH_PATH,
    LIVE_HTTP_SERVER_MODE,
    LOCAL_CALL_PATH,
    LOOPBACK_HOST,
    MAX_BODY_BYTES,
    MAX_IN_FLIGHT,
    MAX_JOURNAL_BYTES,
    MAX_JOURNAL_RECORDS,
    ORIGIN_HEADER,
    READY_PATH,
    TRACE_HEADER,
)
from integration_gate.openapi_doc import validate as validate_gate_document
from integration_gate.recovery import replay_core
from integration_gate.schema import EnvelopeError, parse_envelope
from readiness.codec import receipt_digest
from readiness.migrate import SCHEMA_VERSION
from readiness.policy import AdmitGate
from readiness.store import ReadinessStore, StoreError

ALLOWED_PATHS = frozenset({HEALTH_PATH, READY_PATH, LOCAL_CALL_PATH})
TRACE_TOKEN = re.compile(r'[A-Za-z0-9._:-]{1,64}')
REASONS = {
    200: 'OK',
    204: 'No Content',
    400: 'Bad Request',
    404: 'Not Found',
    405: 'Method Not Allowed',
    408: 'Request Timeout',
    411: 'Length Required',
    413: 'Payload Too Large',
    414: 'URI Too Long',
    415: 'Unsupported Media Type',
    417: 'Expectation Failed',
    422: 'Unprocessable Entity',
    431: 'Request Header Fields Too Large',
    500: 'Internal Server Error',
    503: 'Service Unavailable',
    505: 'HTTP Version Not Supported',
}


class GateStartupError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class CoreBusy(Exception):
    pass


class GateServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = False
    block_on_close = True

    def __init__(
        self,
        address,
        handler,
        catalogue,
        timeout_seconds,
        max_body_bytes,
        store,
        max_in_flight,
        max_journal_records,
        max_journal_bytes,
        browser_origin=None,
    ):
        self.browser_origin = browser_origin
        self.catalogue = catalogue
        self.request_timeout_seconds = timeout_seconds
        self.max_body_bytes = max_body_bytes
        self.store = store
        self.max_in_flight = max_in_flight
        self.max_journal_records = max_journal_records
        self.max_journal_bytes = max_journal_bytes
        self.core = None
        self.Rejected = None
        self._accepting = False
        self._core_failed = False
        self._diverged = False
        self._draining = False
        self.admit = AdmitGate(max_in_flight)
        self._handlers = 0
        self._closed_core = False
        self._admit_lock = threading.Lock()
        self._handler_cv = threading.Condition(self._admit_lock)
        self._jobs = queue.Queue()
        self.request_queue_size = min(max_in_flight, 16)
        super().__init__(address, handler)
        self._worker = threading.Thread(target=self._core_loop, name='gate-core')
        self._worker.start()

    def _core_loop(self):
        while True:
            job = self._jobs.get()
            if job is None:
                return
            job()

    def on_core(self, fn, timeout):
        if threading.get_ident() == self._worker.ident:
            return fn()
        if not self._worker.is_alive():
            self._mark_diverged()
            raise CoreBusy()
        done = threading.Event()
        box = {}

        def job():
            try:
                box['value'] = fn()
            except BaseException as exc:
                box['error'] = exc
            finally:
                done.set()

        self._jobs.put(job)
        if not done.wait(timeout):
            self._mark_diverged()
            raise CoreBusy()
        if 'error' in box:
            raise box['error']
        return box['value']

    def recover_now(self):
        try:
            self.on_core(self._ensure_core_on_worker, 30)
        except GateStartupError:
            raise
        except StoreError as exc:
            raise GateStartupError(exc.code) from exc
        except CoreBusy as exc:
            raise GateStartupError('CORE_UNAVAILABLE') from exc
        except Exception as exc:
            raise GateStartupError('CORE_UNAVAILABLE') from exc

    def _ensure_core_on_worker(self):
        with self._admit_lock:
            if self._core_failed:
                raise GateStartupError('CORE_UNAVAILABLE')
            if self.core is not None:
                return
        Core, Rejected = reference_types()
        core = Core()
        try:
            domain = core.snapshot().get('domain')
        except Exception as exc:
            self._fail_unpublished(core)
            raise GateStartupError('CORE_UNAVAILABLE') from exc
        if domain != self.catalogue.domain:
            self._fail_unpublished(core)
            raise GateStartupError('DOMAIN_MISMATCH')
        if self.store is not None:
            try:
                replay_core(core, self.store.records)
            except Exception as exc:
                self._fail_unpublished(core)
                if isinstance(exc, StoreError):
                    raise GateStartupError(exc.code) from exc
                raise GateStartupError('JOURNAL_CORRUPT') from exc
        with self._admit_lock:
            self.Rejected = Rejected
            self.core = core
            if not self._draining and not self._diverged and not self._core_failed:
                self._accepting = True

    def _fail_unpublished(self, core):
        with self._admit_lock:
            self._core_failed = True
            self._accepting = False
            self.core = None
        _close_quietly(core)

    def _mark_diverged(self):
        with self._admit_lock:
            self._diverged = True
            self._accepting = False

    def commands_enabled(self):
        with self._admit_lock:
            return bool(
                self._accepting
                and self.core is not None
                and not self._core_failed
                and not self._diverged
                and not self._draining
            )

    def blocked(self):
        with self._admit_lock:
            if self._draining or self._diverged or self._core_failed:
                return True
            if self.core is not None and not self._accepting:
                return True
            return False

    def try_admit(self):
        with self._admit_lock:
            if self._draining or self._diverged or self._core_failed:
                return 'NOT_READY'
            if self.core is not None and not self._accepting:
                return 'NOT_READY'
            return self.admit.try_admit()

    def release_admit(self):
        with self._admit_lock:
            self.admit.release()

    def note_handler_enter(self):
        with self._admit_lock:
            self._handlers += 1

    def note_handler_exit(self):
        with self._admit_lock:
            if self._handlers > 0:
                self._handlers -= 1
            self._handler_cv.notify_all()

    def begin_drain(self):
        with self._admit_lock:
            self._draining = True
            self._accepting = False

    def set_accepting(self, value):
        """Latch used to separate liveness from readiness. Not an HTTP command."""
        with self._admit_lock:
            if self._draining or self._diverged or self._core_failed:
                self._accepting = False
                return
            self._accepting = bool(value)

    def perform(self, operation_id, actor, action, body):
        observation = _journal_observation('not_attempted', self.store)
        self._ensure_core_on_worker()
        if not self.commands_enabled():
            observation['journalDecision'] = 'not_attempted'
            observation['admit'] = 'NOT_READY'
            return 503, _not_ready(), observation
        fresh = self.store is None or not self.store.has_operation(operation_id)
        if self.store is not None and fresh:
            code, limit = self.store.budget_decision(
                self.max_body_bytes + 2048,
                self.max_journal_records,
                self.max_journal_bytes,
            )
            if code != 'OK':
                observation['journalDecision'] = 'budget_rejected'
                observation['budgetLimit'] = limit
                return 503, _error('JOURNAL_BUDGET'), observation
        before = _command_count(self.core)
        try:
            receipt = self.core.execute(operation_id, actor, action, body)
        except self.Rejected as exc:
            observation['journalDecision'] = 'inactive' if self.store is None else 'not_attempted'
            return 422, _error(str(exc)), observation
        except Exception as exc:
            print('integration-gate internal error: ' + type(exc).__name__, file=sys.stderr)
            observation['journalDecision'] = 'not_attempted'
            return 500, _error('INTERNAL_ERROR'), observation
        after = _command_count(self.core)
        if self.store is None:
            observation['journalDecision'] = 'inactive'
            return 200, receipt, observation
        if after == before:
            if fresh:
                self._mark_diverged()
                observation['journalDecision'] = 'diverged'
                return 503, _error('DURABILITY_DIVERGENCE'), observation
            observation['journalDecision'] = 'replayed'
            return 200, receipt, observation
        if after != before + 1 or not fresh:
            self._mark_diverged()
            observation['journalDecision'] = 'diverged'
            return 503, _error('DURABILITY_DIVERGENCE'), observation
        try:
            self.store.append({
                'kind': 'core_commit',
                'machine': 'integration_core',
                'operationId': operation_id,
                'actor': actor,
                'action': action,
                'body': body,
                'receiptDigest': receipt_digest(receipt),
            })
        except StoreError:
            self._mark_diverged()
            observation['journalDecision'] = 'diverged'
            return 503, _error('DURABILITY_DIVERGENCE'), observation
        observation['journalDecision'] = 'appended'
        return 200, receipt, observation

    def ready_view(self):
        self._ensure_core_on_worker()
        if not self.commands_enabled():
            raise GateStartupError('NOT_READY')
        snapshot = self.core.snapshot()
        journal_records = None if self.store is None else len(self.store.records)
        return snapshot, journal_records

    def close_reference_core(self):
        if self._closed_core:
            return
        self._closed_core = True
        self.begin_drain()
        if self._worker.is_alive():
            def job():
                core = self.core
                with self._admit_lock:
                    self.core = None
                    self._accepting = False
                _close_quietly(core)
            try:
                self.on_core(job, 2)
            except Exception:
                pass
            self._jobs.put(None)
            self._worker.join(timeout=2)
        if self.store is not None:
            self.store.close()
            self.store = None

    def audit(self, **fields):
        try:
            emit(sys.stderr, **fields)
        except Exception:
            print('integration-gate audit failed', file=sys.stderr)


class GateHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def handle(self):
        self.close_connection = True
        self.handle_one_request()

    def handle_one_request(self):
        self._sent = False
        self._cors = False
        self._status = 0
        self._error_code = None
        self._route_path = ''
        self._operation_id = None
        self._action = None
        self.request_id = _new_trace_id()
        self.correlation_id = self.request_id
        self._observation = {'admit': 'probe', 'journalDecision': 'probe', 'queued': 0}
        if self.server.store is not None:
            self._observation['schemaVersion'] = SCHEMA_VERSION
        started = time.monotonic()
        self.server.note_handler_enter()
        try:
            self.connection.settimeout(self.server.request_timeout_seconds)
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self._send(414, _error('URI_TOO_LONG'))
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                if not self._sent:
                    self._send(400, _error('BAD_REQUEST'))
                return
            self.close_connection = True
            self._adopt_trace_headers()
            self.route()
            self.wfile.flush()
        except (TimeoutError, socket.timeout):
            self.close_connection = True
            if not self._sent:
                try:
                    self._send(408, _error('REQUEST_TIMEOUT'))
                    self.wfile.flush()
                except Exception:
                    pass
        except Exception as exc:
            if not self._sent:
                print('integration-gate internal error: ' + type(exc).__name__, file=sys.stderr)
                try:
                    self._send(500, _error('INTERNAL_ERROR'))
                    self.wfile.flush()
                except Exception:
                    pass
        finally:
            if self._sent:
                self.server.audit(
                    event='http_request',
                    requestId=self.request_id,
                    correlationId=self.correlation_id,
                    method=getattr(self, 'command', ''),
                    path=_clip(self._route_path),
                    status=self._status,
                    durationMs=int((time.monotonic() - started) * 1000),
                    error=self._error_code,
                    operationId=self._operation_id,
                    action=self._action,
                    localFileJournal=self.server.store is not None,
                    **self._observation,
                )
            self.server.note_handler_exit()

    def route(self):
        if self.server.browser_origin is not None and not _loopback_host_header(
            self.headers, self.server.server_address[1]
        ):
            self._send(400, _error('BAD_REQUEST'))
            return
        target = _raw_target(self.raw_requestline)
        if target is None:
            self._send(400, _error('BAD_REQUEST'))
            return
        path, separator, _query = target.partition('?')
        self._route_path = path
        if separator:
            self._send(400, _error('QUERY_NOT_ALLOWED'))
            return
        if path not in ALLOWED_PATHS:
            self._send(404, _error('NOT_FOUND'))
            return
        if len(self.headers.as_string()) > HEADER_LIMIT_BYTES:
            self._send(431, _error('HEADER_TOO_LARGE'))
            return
        if self.headers.get('Transfer-Encoding'):
            self._send(400, _error('UNSUPPORTED_TRANSFER'))
            return
        if self.headers.get('Expect'):
            self._send(417, _error('EXPECTATION_FAILED'))
            return
        if _origin_is_allowed(self.headers, self.server.browser_origin):
            self._cors = True
        method = self.command
        if method == 'OPTIONS' and self.server.browser_origin is not None:
            if self._preflight(path):
                return
            self._cors = False
        if path in (HEALTH_PATH, READY_PATH):
            if method != 'GET':
                self._send(405, _error('METHOD_NOT_ALLOWED'), allow='GET')
                return
            if path == HEALTH_PATH:
                self._health()
            else:
                self._ready()
            return
        if method != 'POST':
            self._send(405, _error('METHOD_NOT_ALLOWED'), allow='POST')
            return
        self._local_call()

    def send_error(self, code, message=None, explain=None):
        mapped = {
            400: 'BAD_REQUEST',
            414: 'URI_TOO_LONG',
            431: 'HEADER_TOO_LARGE',
            505: 'HTTP_VERSION_NOT_SUPPORTED',
        }
        status = int(code)
        self._send(status, _error(mapped.get(status, 'BAD_REQUEST')))

    def log_message(self, fmt, *args):
        return

    def _preflight(self, path):
        if not _preflight_acceptable(self.headers, path, self.server.browser_origin):
            return False
        self._cors = True
        allow = 'POST' if path == LOCAL_CALL_PATH else 'GET'
        self._send(204, None, allow=allow, preflight=True)
        return True

    def _adopt_trace_headers(self):
        request = _trace_token(self.headers.get(TRACE_HEADER))
        if request is not None:
            self.request_id = request
        correlation = _trace_token(self.headers.get(CORRELATION_HEADER))
        self.correlation_id = correlation if correlation is not None else self.request_id

    def _health(self):
        self._send(200, _probe('up', self.server))

    def _ready(self):
        if self.server.blocked():
            self._send(503, _not_ready())
            return
        try:
            snapshot, journal_records = self.server.on_core(
                self.server.ready_view,
                self.server.request_timeout_seconds,
            )
        except (CoreBusy, GateStartupError, StoreError):
            self._send(503, _not_ready())
            return
        except Exception:
            self._send(503, _not_ready())
            return
        if snapshot.get('domain') != self.server.catalogue.domain:
            self._send(503, _not_ready())
            return
        body = _probe('ready', self.server)
        body.update({
            'durable': False,
            'liveMoney': False,
            'commandCount': len(self.server.catalogue.names),
            'domain': self.server.catalogue.domain,
            'localFileJournal': journal_records is not None,
        })
        if journal_records is not None:
            body['journalRecords'] = journal_records
        self._send(200, body)

    def _local_call(self):
        decision = self.server.try_admit()
        admitted = self.server.admit.view()
        self._observation = {
            'admit': decision,
            'journalDecision': 'not_attempted',
            'inFlight': admitted['inFlight'],
            'maxInFlight': admitted['maxInFlight'],
            'queued': admitted['queued'],
        }
        if self.server.store is not None:
            self._observation['schemaVersion'] = SCHEMA_VERSION
        if decision != 'OK':
            payload = _error('OVERLOADED') if decision == 'OVERLOADED' else _not_ready()
            self._send(503, payload)
            return
        try:
            length, length_error = _content_length(self.headers, self.server.max_body_bytes)
            if length_error is not None:
                status, code = length_error
                self._send(status, _error(code))
                return
            if not _json_media(self.headers.get('Content-Type')):
                self._send(415, _error('UNSUPPORTED_MEDIA_TYPE'))
                return
            raw = self.rfile.read(length)
            if len(raw) != length:
                self._send(400, _error('INCOMPLETE_BODY'))
                return
            if raw.startswith(b'\xef\xbb\xbf'):
                self._send(400, _error('INVALID_JSON'))
                return
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                self._send(400, _error('INVALID_JSON'))
                return
            try:
                payload = json.loads(text, object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
            except DuplicateKey:
                self._send(400, _error('DUPLICATE_KEY'))
                return
            except (json.JSONDecodeError, RecursionError, ValueError):
                self._send(400, _error('INVALID_JSON'))
                return
            try:
                operation_id, actor, action, body = parse_envelope(payload, self.server.catalogue.commands)
            except EnvelopeError as exc:
                body_out = _error(exc.error)
                if exc.detail:
                    body_out['detail'] = exc.detail[:500]
                self._send(400, body_out)
                return
            self._operation_id = operation_id
            self._action = action
            if self.server.blocked():
                self._send(503, _not_ready())
                return
            try:
                status, response, observation = self.server.on_core(
                    lambda: self.server.perform(operation_id, actor, action, body),
                    self.server.request_timeout_seconds,
                )
                observation['admit'] = 'OK'
                observation['inFlight'] = admitted['inFlight']
                observation['maxInFlight'] = admitted['maxInFlight']
                observation['queued'] = 0
                self._observation = observation
            except CoreBusy:
                self._send(503, _error('CORE_BUSY'))
                return
            except GateStartupError:
                self._send(503, _not_ready())
                return
            self._send(status, response)
        finally:
            self.server.release_admit()

    def _send(self, status, payload, allow=None, preflight=False):
        if self._sent:
            return
        reason = REASONS.get(status, 'Error')
        lines = ['HTTP/1.0 %d %s' % (status, reason)]
        if status == 204:
            body = b''
        else:
            body = json.dumps(
                payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':')
            ).encode('utf-8')
            lines.append('Content-Type: application/json; charset=utf-8')
            lines.append('Content-Length: %d' % len(body))
        lines.extend([
            'Connection: close',
            'Cache-Control: no-store',
            'X-Content-Type-Options: nosniff',
            'X-Kix-Transport: integration-gate',
            'X-Kix-Production-Endpoint: false',
            'X-Kix-Protocol-Truth: false',
            'X-Kix-Production-Conformance: false',
            'X-Request-Id: ' + self.request_id,
            'X-Correlation-Id: ' + self.correlation_id,
        ])
        if self._cors:
            lines.append('Access-Control-Allow-Origin: ' + BROWSER_ALLOWED_ORIGIN)
            lines.append('Vary: Origin')
        if preflight:
            lines.append('Access-Control-Allow-Methods: ' + allow)
            lines.append(
                'Access-Control-Allow-Headers: ' + ', '.join(BROWSER_ALLOWED_REQUEST_HEADERS)
            )
        if allow:
            lines.append('Allow: ' + allow)
        packet = ('\r\n'.join(lines) + '\r\n\r\n').encode('ascii') + body
        self._sent = True
        self._status = status
        if isinstance(payload, dict) and isinstance(payload.get('error'), str):
            self._error_code = payload['error']
        self.close_connection = True
        self.wfile.write(packet)


class DuplicateKey(ValueError):
    pass


def _reject_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateKey()
        obj[key] = value
    return obj


def _reject_constant(_value):
    raise ValueError('non-standard JSON number')


def _error(code):
    return {'error': code, 'rejected': True}


def _not_ready():
    return {
        'error': 'NOT_READY',
        'production': False,
        'productionReadiness': False,
        'productionConformance': False,
        'protocolTruth': False,
        'rejected': True,
        'role': 'integration-gate',
    }


def _probe(status, server):
    return {
        'status': status,
        'role': 'integration-gate',
        'liveHttpServer': LIVE_HTTP_SERVER_MODE,
        'production': False,
        'publicHost': False,
        'productionReadiness': False,
        'productionConformance': False,
        'protocolTruth': False,
        'localFileJournal': server.store is not None,
    }


def _raw_target(raw_requestline):
    try:
        line = str(raw_requestline, 'iso-8859-1').rstrip('\r\n')
    except UnicodeError:
        return None
    words = line.split()
    if len(words) < 2:
        return None
    return words[1]


def _content_length(headers, limit):
    values = headers.get_all('Content-Length')
    if not values:
        return None, (411, 'CONTENT_LENGTH_REQUIRED')
    if len(values) != 1:
        return None, (400, 'BAD_CONTENT_LENGTH')
    text = values[0].strip()
    if text != '0' and (not text.isdigit() or text.startswith('0')):
        return None, (400, 'BAD_CONTENT_LENGTH')
    length = int(text)
    if length > limit:
        return None, (413, 'BODY_TOO_LARGE')
    return length, None


def _json_media(value):
    if not value:
        return False
    parts = [part.strip() for part in value.split(';')]
    if parts[0].lower() != 'application/json':
        return False
    for param in parts[1:]:
        if not param or '=' not in param:
            return False
        name, _, raw = param.partition('=')
        if name.strip().lower() != 'charset':
            return False
        if raw.strip().strip('"').lower() != 'utf-8':
            return False
    return True


def _close_quietly(core):
    if core is None:
        return
    try:
        core.db.close()
    except Exception:
        pass


def _command_count(core):
    return core.db.execute('SELECT COUNT(*) FROM commands').fetchone()[0]


def _new_trace_id():
    return secrets.token_hex(16)


def _trace_token(value):
    if not isinstance(value, str):
        return None
    if TRACE_TOKEN.fullmatch(value) is None:
        return None
    return value


def _clip(path):
    if len(path) > 200:
        return path[:200]
    return path


def _journal_observation(decision, store):
    observation = {
        'admit': 'OK',
        'journalDecision': 'inactive' if store is None else decision,
        'queued': 0,
    }
    if store is not None:
        observation['schemaVersion'] = SCHEMA_VERSION
    return observation


def _one_header(headers, name):
    values = headers.get_all(name)
    if values is None or len(values) != 1:
        return None
    return values[0]


def _loopback_host_header(headers, port):
    host = _one_header(headers, 'Host')
    if host is None:
        return False
    return host == LOOPBACK_HOST or host == '%s:%d' % (LOOPBACK_HOST, port)


def _origin_is_allowed(headers, browser_origin):
    if browser_origin is None:
        return False
    return _one_header(headers, ORIGIN_HEADER) == browser_origin


def _requested_headers_allowed(headers):
    values = headers.get_all('Access-Control-Request-Headers')
    if values is None:
        return True
    if len(values) != 1 or values[0].strip() == '':
        return False
    tokens = [part.strip().lower() for part in values[0].split(',')]
    if '' in tokens or len(tokens) != len(set(tokens)):
        return False
    return set(tokens).issubset(BROWSER_ALLOWED_REQUEST_HEADERS)


def _preflight_acceptable(headers, path, browser_origin):
    if not _origin_is_allowed(headers, browser_origin):
        return False
    expected = 'POST' if path == LOCAL_CALL_PATH else 'GET'
    if _one_header(headers, 'Access-Control-Request-Method') != expected:
        return False
    if headers.get_all('Access-Control-Request-Private-Network') is not None:
        return False
    return _requested_headers_allowed(headers)


def build_server(
    host,
    port,
    timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    max_body_bytes=MAX_BODY_BYTES,
    root=None,
    readiness_dir=None,
    max_in_flight=MAX_IN_FLIGHT,
    max_journal_records=MAX_JOURNAL_RECORDS,
    max_journal_bytes=MAX_JOURNAL_BYTES,
    browser_origin=None,
):
    if host != LOOPBACK_HOST:
        raise GateStartupError('REFUSING_NON_LOOPBACK_BIND')
    if browser_origin is not None and browser_origin != BROWSER_ALLOWED_ORIGIN:
        raise GateStartupError('REFUSING_BROWSER_ORIGIN')
    if not isinstance(port, int) or port < 0 or port > 65535:
        raise GateStartupError('REFUSING_PORT')
    if timeout_seconds <= 0 or max_body_bytes < 1:
        raise GateStartupError('REFUSING_LIMITS')
    if not isinstance(max_in_flight, int) or not 1 <= max_in_flight <= 64:
        raise GateStartupError('REFUSING_LIMITS')
    if not isinstance(max_journal_records, int) or not 1 <= max_journal_records <= 100000:
        raise GateStartupError('REFUSING_LIMITS')
    if not isinstance(max_journal_bytes, int) or max_journal_bytes < max_body_bytes:
        raise GateStartupError('REFUSING_LIMITS')
    try:
        catalogue = load_catalogue(root)
    except CatalogueError as exc:
        raise GateStartupError(exc.code) from exc
    if validate_gate_document(root):
        raise GateStartupError('REFUSING_GATE_DOCUMENT')
    store = None
    if readiness_dir is not None:
        try:
            store = ReadinessStore.open(readiness_dir)
        except StoreError as exc:
            raise GateStartupError(exc.code) from exc
    try:
        return GateServer(
            (host, port),
            GateHandler,
            catalogue,
            timeout_seconds,
            max_body_bytes,
            store,
            max_in_flight,
            max_journal_records,
            max_journal_bytes,
            browser_origin=browser_origin,
        )
    except Exception:
        if store is not None:
            store.close()
        raise


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            'Non-production loopback KIX integration gate. '
            'Not a public host and not a production endpoint.'
        )
    )
    parser.add_argument('--host', default=LOOPBACK_HOST)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--timeout-seconds', type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument('--max-body-bytes', type=int, default=MAX_BODY_BYTES)
    parser.add_argument('--max-in-flight', type=int, default=MAX_IN_FLIGHT)
    parser.add_argument('--readiness-dir', default=None)
    parser.add_argument('--browser-origin', action='append')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    browser_origins = args.browser_origin
    if browser_origins is not None and len(browser_origins) != 1:
        print('REFUSING_BROWSER_ORIGIN', file=sys.stderr)
        return 2
    browser_origin = None if browser_origins is None else browser_origins[0]
    if not (0.05 <= args.timeout_seconds <= 120):
        print('REFUSING_LIMITS', file=sys.stderr)
        return 2
    if not (1 <= args.max_body_bytes <= 1048576):
        print('REFUSING_LIMITS', file=sys.stderr)
        return 2
    if not (1 <= args.max_in_flight <= 64):
        print('REFUSING_LIMITS', file=sys.stderr)
        return 2
    try:
        httpd = build_server(
            args.host,
            args.port,
            args.timeout_seconds,
            args.max_body_bytes,
            readiness_dir=args.readiness_dir,
            max_in_flight=args.max_in_flight,
            browser_origin=browser_origin,
        )
    except GateStartupError as exc:
        print(exc.code, file=sys.stderr)
        return 2
    except OSError:
        print('REFUSING_BIND', file=sys.stderr)
        return 2
    try:
        httpd.recover_now()
    except GateStartupError as exc:
        print(exc.code, file=sys.stderr)
        httpd.server_close()
        httpd.close_reference_core()
        return 2
    host, port = httpd.server_address
    print('integration-gate listening %s %s' % (host, port), flush=True)

    def _request_stop(_signum, _frame):
        threading.Thread(target=httpd.shutdown, name='gate-shutdown', daemon=True).start()

    import signal
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)
    try:
        httpd.serve_forever(poll_interval=0.05)
    except KeyboardInterrupt:
        return 0
    finally:
        httpd.begin_drain()
        httpd.server_close()
        httpd.close_reference_core()
    return 0
