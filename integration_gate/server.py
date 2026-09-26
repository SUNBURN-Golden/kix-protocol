"""Loopback HTTP transport for the published local-call envelope.

Binds to 127.0.0.1 only. Dispatches POST /x-kix-contract-only/local-call to
the in-memory reference Core.execute. Does not attach payment, KYC, venue,
or bank adapters. Not a production endpoint.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket
import sys
import threading

from integration_gate.catalogue import CatalogueError, load_catalogue, reference_types
from integration_gate.constants import (
    DEFAULT_TIMEOUT_SECONDS,
    HEADER_LIMIT_BYTES,
    HEALTH_PATH,
    LIVE_HTTP_SERVER_MODE,
    LOCAL_CALL_PATH,
    LOOPBACK_HOST,
    MAX_BODY_BYTES,
    READY_PATH,
)
from integration_gate.openapi_doc import validate as validate_gate_document
from integration_gate.schema import EnvelopeError, parse_envelope

ALLOWED_PATHS = frozenset({HEALTH_PATH, READY_PATH, LOCAL_CALL_PATH})
REASONS = {
    200: 'OK',
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


class GateServer(HTTPServer):
    allow_reuse_address = True

    def __init__(self, address, handler, catalogue, timeout_seconds, max_body_bytes):
        self.catalogue = catalogue
        self.request_timeout_seconds = timeout_seconds
        self.max_body_bytes = max_body_bytes
        self.core = None
        self.Rejected = None
        self._accepting = False
        self._core_failed = False
        self._core_lock = threading.Lock()
        super().__init__(address, handler)

    def ensure_core(self):
        if self._core_failed:
            raise GateStartupError('CORE_UNAVAILABLE')
        if self.core is not None:
            return
        with self._core_lock:
            if self.core is not None:
                return
            Core, Rejected = reference_types()
            core = Core()
            try:
                domain = core.snapshot().get('domain')
            except Exception as exc:
                self._core_failed = True
                _close_quietly(core)
                raise GateStartupError('CORE_UNAVAILABLE') from exc
            if domain != self.catalogue.domain:
                self._core_failed = True
                _close_quietly(core)
                raise GateStartupError('DOMAIN_MISMATCH')
            self.Rejected = Rejected
            self.core = core
            self._accepting = True

    def commands_enabled(self):
        return bool(self._accepting and self.core is not None and not self._core_failed)

    def set_accepting(self, value):
        """Latch used to separate liveness from readiness. Not an HTTP command."""
        self._accepting = bool(value)

    def close_reference_core(self):
        core = self.core
        self.core = None
        self._accepting = False
        _close_quietly(core)


class GateHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def handle(self):
        self.close_connection = True
        self.handle_one_request()

    def handle_one_request(self):
        self._sent = False
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

    def route(self):
        target = _raw_target(self.raw_requestline)
        if target is None:
            self._send(400, _error('BAD_REQUEST'))
            return
        path, separator, _query = target.partition('?')
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
        method = self.command
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

    def _health(self):
        self._send(200, {
            'status': 'up',
            'role': 'integration-gate',
            'liveHttpServer': LIVE_HTTP_SERVER_MODE,
            'production': False,
            'publicHost': False,
            'productionReadiness': False,
        })

    def _ready(self):
        try:
            self.server.ensure_core()
        except Exception:
            self._send(503, _not_ready())
            return
        if not self.server.commands_enabled():
            self._send(503, _not_ready())
            return
        try:
            snapshot = self.server.core.snapshot()
        except Exception:
            self._send(503, _not_ready())
            return
        if snapshot.get('domain') != self.server.catalogue.domain:
            self._send(503, _not_ready())
            return
        self._send(200, {
            'status': 'ready',
            'role': 'integration-gate',
            'liveHttpServer': LIVE_HTTP_SERVER_MODE,
            'production': False,
            'publicHost': False,
            'productionReadiness': False,
            'durable': False,
            'liveMoney': False,
            'commandCount': len(self.server.catalogue.names),
            'domain': self.server.catalogue.domain,
        })

    def _local_call(self):
        try:
            self.server.ensure_core()
        except Exception:
            self._send(503, _not_ready())
            return
        if not self.server.commands_enabled():
            self._send(503, _not_ready())
            return
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
        try:
            receipt = self.server.core.execute(operation_id, actor, action, body)
        except self.server.Rejected as exc:
            self._send(422, _error(str(exc)))
            return
        except Exception as exc:
            print('integration-gate internal error: ' + type(exc).__name__, file=sys.stderr)
            self._send(500, _error('INTERNAL_ERROR'))
            return
        self._send(200, receipt)

    def _send(self, status, payload, allow=None):
        if self._sent:
            return
        body = json.dumps(
            payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':')
        ).encode('utf-8')
        reason = REASONS.get(status, 'Error')
        lines = [
            'HTTP/1.0 %d %s' % (status, reason),
            'Content-Type: application/json; charset=utf-8',
            'Content-Length: %d' % len(body),
            'Connection: close',
            'Cache-Control: no-store',
            'X-Content-Type-Options: nosniff',
            'X-Kix-Transport: integration-gate',
            'X-Kix-Production-Endpoint: false',
        ]
        if allow:
            lines.append('Allow: ' + allow)
        packet = ('\r\n'.join(lines) + '\r\n\r\n').encode('ascii') + body
        self._sent = True
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
        'rejected': True,
        'role': 'integration-gate',
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


def build_server(host, port, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, max_body_bytes=MAX_BODY_BYTES, root=None):
    if host != LOOPBACK_HOST:
        raise GateStartupError('REFUSING_NON_LOOPBACK_BIND')
    if not isinstance(port, int) or port < 0 or port > 65535:
        raise GateStartupError('REFUSING_PORT')
    if timeout_seconds <= 0 or max_body_bytes < 1:
        raise GateStartupError('REFUSING_LIMITS')
    try:
        catalogue = load_catalogue(root)
    except CatalogueError as exc:
        raise GateStartupError(exc.code) from exc
    if validate_gate_document(root):
        raise GateStartupError('REFUSING_GATE_DOCUMENT')
    return GateServer((host, port), GateHandler, catalogue, timeout_seconds, max_body_bytes)


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
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not (0.05 <= args.timeout_seconds <= 120):
        print('REFUSING_LIMITS', file=sys.stderr)
        return 2
    if not (1 <= args.max_body_bytes <= 1048576):
        print('REFUSING_LIMITS', file=sys.stderr)
        return 2
    try:
        httpd = build_server(args.host, args.port, args.timeout_seconds, args.max_body_bytes)
    except GateStartupError as exc:
        print(exc.code, file=sys.stderr)
        return 2
    except OSError:
        print('REFUSING_BIND', file=sys.stderr)
        return 2
    host, port = httpd.server_address
    print('integration-gate listening %s %s' % (host, port), flush=True)
    try:
        httpd.serve_forever(poll_interval=0.05)
    except KeyboardInterrupt:
        return 0
    finally:
        httpd.server_close()
        httpd.close_reference_core()
    return 0
