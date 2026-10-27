#!/usr/bin/env python3
"""Read-only preflight: can this host run the loopback HTTP gate suite?

Reports, without installing or changing anything, whether the host this
script runs on can do what ``integration_gate.test_http_gate`` needs
from the operating system before any gate code runs:

- create a ``socket(AF_INET, SOCK_STREAM)``;
- bind it to ``127.0.0.1`` port ``0`` (an ephemeral loopback port);
- listen on it and accept one connection made to it over loopback;
- do the same in a child ``python3 -I -c`` interpreter that reports the
  port it bound (the gate runs as a subprocess and announces its port).

Every socket is closed as soon as its probe step ends. Only
``127.0.0.1`` with port ``0`` is ever bound or connected to; no public
address is opened and no network call is made. ``integration_gate`` is
never imported or started. There is no retry and no polling; the child
is bounded by a timeout.

Output is one JSON object (``schema_version`` 1) with the interpreter
version and path, platform, per-step results for the in-process and
child probes, ``all_ok`` and fixed flags ``evidence_prep: true``,
``gate_suite_run: false``, ``host_selected: false`` and
``permission_granted: false``. Plain mode always exits ``0``, whatever
the probes observed. ``--require`` exits ``1`` when any probe failed.
``--self-test`` exits ``0`` on pass and ``1`` on failure. Invalid
command-line usage exits ``2``.

A passing report is host-context evidence that these operating-system
calls succeeded on this host at this time. It is not a host selection,
host permission, a ``test_http_gate`` result, CI evidence for any other
host or head, or a change to any evidence-map status. A plain run on a
CI runner reports that runner only.

``--self-test`` runs the report logic against injected fake socket and
subprocess factories (success, ``PermissionError`` at create, ``OSError``
at bind, child failure) with the real ``socket.socket``,
``subprocess.run`` and ``subprocess.Popen`` replaced by tripwires; it
opens no real socket and starts no process. Standard library only.
"""

from __future__ import annotations

import contextlib
import io
import json
import platform
import socket
import subprocess
import sys

BIND_HOST = '127.0.0.1'
BIND_PORT = 0
SCHEMA_VERSION = 1
CHILD_TIMEOUT_SECONDS = 10
SOCKET_TIMEOUT_SECONDS = 5
STEPS = ('create', 'bind', 'listen', 'connect')

CHILD_PROGRAM = '''\
import json, socket, sys
steps = {}
port = None
failed = None
def run(name, fn):
    global failed
    if failed:
        steps[name] = {"ok": False, "error": "skipped: %s failed" % failed}
        return None
    try:
        value = fn()
    except Exception as exc:
        steps[name] = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
        failed = name
        return None
    steps[name] = {"ok": True, "error": None}
    return value
server = run("create", lambda: socket.socket(socket.AF_INET, socket.SOCK_STREAM))
try:
    if server is not None:
        server.settimeout(5)
    run("bind", lambda: server.bind(('127.0.0.1', 0)))
    def listen():
        server.listen(1)
        return server.getsockname()[1]
    port = run("listen", listen)
    def connect():
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.settimeout(5)
            client.connect(('127.0.0.1', port))
            accepted, _ = server.accept()
            accepted.close()
        finally:
            client.close()
    run("connect", connect)
finally:
    if server is not None:
        server.close()
ok = failed is None
print(json.dumps({"ok": ok, "port": port, "steps": steps}, sort_keys=True))
sys.exit(0 if ok else 1)
'''


def _error(exc):
    return '%s: %s' % (type(exc).__name__, exc)


def probe_loopback(socket_factory):
    """Create, bind, listen and connect over loopback; never raise.

    ``socket_factory(family, type)`` returns a socket-like object. Every
    socket created here is closed before this function returns.
    """
    steps = {}
    state = {'failed': None, 'port': None}

    def run(name, fn):
        if state['failed']:
            steps[name] = {'ok': False,
                           'error': 'skipped: %s failed' % state['failed']}
            return None
        try:
            value = fn()
        except Exception as exc:  # recorded, not raised: plain mode exits 0
            steps[name] = {'ok': False, 'error': _error(exc)}
            state['failed'] = name
            return None
        steps[name] = {'ok': True, 'error': None}
        return value

    server = run('create', lambda: socket_factory(socket.AF_INET,
                                                  socket.SOCK_STREAM))
    try:
        def bind():
            server.settimeout(SOCKET_TIMEOUT_SECONDS)
            server.bind((BIND_HOST, BIND_PORT))
        run('bind', bind)

        def listen():
            server.listen(1)
            return server.getsockname()[1]
        state['port'] = run('listen', listen)

        def connect():
            client = socket_factory(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client.settimeout(SOCKET_TIMEOUT_SECONDS)
                client.connect((BIND_HOST, state['port']))
                accepted, _ = server.accept()
                accepted.close()
            finally:
                client.close()
        run('connect', connect)
    finally:
        if server is not None:
            server.close()
    return {'ok': state['failed'] is None, 'port': state['port'],
            'steps': steps}


def child_command(executable):
    return [executable, '-I', '-c', CHILD_PROGRAM]


def _valid_port(port):
    return (isinstance(port, int) and not isinstance(port, bool)
            and 0 < port < 65536)


def probe_child(run_child, executable):
    """Run the child loopback probe through ``run_child``; never raise."""
    result = {'ok': False,
              'command': [executable, '-I', '-c', '<CHILD_PROGRAM>'],
              'returncode': None, 'port': None, 'steps': None,
              'stderr': None, 'error': None}
    try:
        completed = run_child(child_command(executable), check=False,
                              capture_output=True, text=True,
                              timeout=CHILD_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        result['error'] = 'timeout after %ds' % CHILD_TIMEOUT_SECONDS
        return result
    except Exception as exc:
        result['error'] = _error(exc)
        return result
    result['returncode'] = completed.returncode
    result['stderr'] = (completed.stderr or '').strip()
    lines = (completed.stdout or '').strip().splitlines()
    try:
        payload = json.loads(lines[-1]) if lines else None
    except ValueError as exc:
        result['error'] = 'unparseable child output: ' + _error(exc)
        return result
    if not isinstance(payload, dict):
        result['error'] = 'no JSON object on child stdout'
        return result
    result['port'] = payload.get('port')
    result['steps'] = payload.get('steps')
    if completed.returncode != 0:
        result['error'] = 'child exit %s' % completed.returncode
    elif payload.get('ok') is not True:
        result['error'] = 'child reported ok=false'
    elif not _valid_port(result['port']):
        result['error'] = 'child reported no valid port'
    else:
        result['ok'] = True
    return result


def host_info():
    return {
        'interpreter': {
            'version': platform.python_version(),
            'implementation': platform.python_implementation(),
            'executable': sys.executable,
        },
        'platform': {
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'platform': platform.platform(),
        },
    }


def build_report(info, socket_factory, run_child, mode):
    """Run both probes through the supplied factories and return the report."""
    in_process = probe_loopback(socket_factory)
    child = probe_child(run_child, info['interpreter']['executable'])
    all_ok = in_process['ok'] and child['ok']
    return {
        'schema_version': SCHEMA_VERSION,
        'tool': 'check_loopback_host',
        'mode': mode,
        'interpreter': info['interpreter'],
        'platform': info['platform'],
        'bind_host': BIND_HOST,
        'bind_port_requested': BIND_PORT,
        'in_process': in_process,
        'child': child,
        'all_ok': all_ok,
        'require_exit': 0 if all_ok else 1,
        'evidence_prep': True,
        'gate_suite_run': False,
        'host_selected': False,
        'permission_granted': False,
    }


def exit_code(report, require):
    return report['require_exit'] if require else 0


TOP_LEVEL_FIELDS = (
    'schema_version', 'tool', 'mode', 'interpreter', 'platform',
    'bind_host', 'bind_port_requested', 'in_process', 'child', 'all_ok',
    'require_exit', 'evidence_prep', 'gate_suite_run', 'host_selected',
    'permission_granted')


class FakeSocket:
    """Socket double for --self-test; records addresses and closes."""

    def __init__(self, world, role):
        self.world = world
        self.role = role
        self.closed = False
        world['sockets'].append(self)

    def _maybe_fail(self, stage):
        if self.world['fail_at'] == stage:
            raise self.world['exc']

    def settimeout(self, value):
        pass

    def bind(self, address):
        self.world['bound'].append(address)
        self._maybe_fail('bind')

    def listen(self, backlog):
        self._maybe_fail('listen')

    def getsockname(self):
        return (BIND_HOST, 40000)

    def connect(self, address):
        self.world['connected'].append(address)
        self._maybe_fail('connect')

    def accept(self):
        return FakeSocket(self.world, 'accepted'), (BIND_HOST, 40001)

    def close(self):
        self.closed = True


def _fake_world(fail_at=None, exc=None):
    world = {'fail_at': fail_at, 'exc': exc, 'sockets': [], 'bound': [],
             'connected': [], 'child_argv': []}

    def factory(family, kind):
        if family != socket.AF_INET or kind != socket.SOCK_STREAM:
            raise AssertionError('unexpected socket family/type')
        if world['fail_at'] == 'create':
            raise world['exc']
        return FakeSocket(world, 'socket')
    return world, factory


class _Completed:
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _fake_child(world, returncode, stdout, stderr=''):
    def run_child(argv, **kwargs):
        world['child_argv'].append((list(argv), kwargs))
        return _Completed(returncode, stdout, stderr)
    return run_child


def _child_ok_stdout(port=40002):
    return json.dumps({'ok': True, 'port': port, 'steps': {
        name: {'ok': True, 'error': None} for name in STEPS}}) + '\n'


FAKE_INFO = {
    'interpreter': {'version': '3.0.0', 'implementation': 'Fake',
                    'executable': '/fake/python3'},
    'platform': {'system': 'Fake', 'release': '0', 'machine': 'fake',
                 'platform': 'Fake-0-fake'},
}


def _self_test_cases():
    child_fail_stdout = json.dumps({'ok': False, 'port': None, 'steps': {
        'create': {'ok': False, 'error': 'PermissionError: [Errno 1] '
                   'Operation not permitted'}}}) + '\n'
    return [
        ('success', None, None,
         (0, _child_ok_stdout(), ''), True, None),
        ('PermissionError at create', 'create',
         PermissionError(1, 'Operation not permitted'),
         (0, _child_ok_stdout(), ''), False, 'create'),
        ('OSError at bind', 'bind',
         OSError(99, 'Cannot assign requested address'),
         (0, _child_ok_stdout(), ''), False, 'bind'),
        ('child failure (exit 1, REFUSING_BIND-style stderr)', None, None,
         (1, child_fail_stdout, 'REFUSING_BIND PermissionError'),
         False, 'child'),
        ('child malformed stdout', None, None,
         (0, 'not json\n', ''), False, 'child'),
        ('child ok without valid port', None, None,
         (0, _child_ok_stdout(port=0), ''), False, 'child'),
    ]


def _check_case(world, report, want_ok, failing):
    problems = []
    try:
        roundtrip = json.loads(json.dumps(report, sort_keys=True))
    except (TypeError, ValueError) as exc:
        return ['not JSON-serializable: ' + _error(exc)]
    for field in TOP_LEVEL_FIELDS:
        if field not in roundtrip:
            problems.append('missing field ' + field)
    if report['all_ok'] is not want_ok:
        problems.append('all_ok %r != %r' % (report['all_ok'], want_ok))
    if exit_code(report, require=False) != 0:
        problems.append('plain exit not 0')
    want_require = 0 if want_ok else 1
    if exit_code(report, require=True) != want_require:
        problems.append('--require exit %d != %d'
                        % (exit_code(report, True), want_require))
    if (report['evidence_prep'], report['gate_suite_run'],
            report['host_selected'], report['permission_granted']) != (
                True, False, False, False):
        problems.append('report flags wrong')
    steps = report['in_process']['steps']
    if sorted(steps) != sorted(STEPS):
        problems.append('in-process steps %s' % sorted(steps))
    if failing in STEPS:
        if steps[failing]['ok'] or not steps[failing]['error']:
            problems.append('%s step not recorded as failed' % failing)
        later = STEPS[STEPS.index(failing) + 1:]
        for name in later:
            if steps[name]['error'] != 'skipped: %s failed' % failing:
                problems.append('%s not skipped after %s' % (name, failing))
        for name in STEPS[:STEPS.index(failing)]:
            if not steps[name]['ok']:
                problems.append('%s should be ok before %s' % (name, failing))
    if failing == 'child':
        if report['child']['ok'] or not report['child']['error']:
            problems.append('child failure not recorded')
        if not report['in_process']['ok']:
            problems.append('in-process should pass in child case')
    if any(not s.closed for s in world['sockets']):
        problems.append('fake socket left open')
    # Literal values, not the module constants, so editing them is caught.
    if (report['bind_host'], report['bind_port_requested']) != (
            '127.0.0.1', 0):
        problems.append('report bind target %r' % (
            (report['bind_host'], report['bind_port_requested']),))
    for address in world['bound']:
        if address != ('127.0.0.1', 0):
            problems.append('bind address %r' % (address,))
    for address in world['connected']:
        if address[0] != '127.0.0.1':
            problems.append('connect address %r' % (address,))
    if len(world['child_argv']) != 1:
        problems.append('child run %d times' % len(world['child_argv']))
    else:
        argv, kwargs = world['child_argv'][0]
        if argv[:3] != ['/fake/python3', '-I', '-c'] or \
                argv[3] != CHILD_PROGRAM:
            problems.append('child argv %r' % argv[:3])
        if kwargs.get('timeout') != CHILD_TIMEOUT_SECONDS or \
                kwargs.get('shell'):
            problems.append('child kwargs %r' % kwargs)
    return problems


def self_test():
    """Exercise the report logic with fakes; open no socket, run no child."""
    tripped = []

    def tripwire(name):
        def refuse(*args, **kwargs):
            tripped.append(name)
            raise AssertionError('self-test touched real ' + name)
        return refuse

    saved = (socket.socket, subprocess.run, subprocess.Popen)
    socket.socket = tripwire('socket.socket')
    subprocess.run = tripwire('subprocess.run')
    subprocess.Popen = tripwire('subprocess.Popen')
    failures = 0
    try:
        try:
            compile(CHILD_PROGRAM, '<child>', 'exec')
        except SyntaxError as exc:
            failures += 1
            print('self-test: FAIL child program does not compile: %s'
                  % exc, file=sys.stderr)
        if "('127.0.0.1', 0)" not in CHILD_PROGRAM:
            failures += 1
            print('self-test: FAIL child program bind address',
                  file=sys.stderr)
        for name, fail_at, exc, child, want_ok, failing in \
                _self_test_cases():
            world, factory = _fake_world(fail_at, exc)
            run_child = _fake_child(world, *child)
            try:
                report = build_report(FAKE_INFO, factory, run_child,
                                      'self-test')
                problems = _check_case(world, report, want_ok, failing)
            except Exception as exc_:  # a raise is itself a failure
                problems = ['raised ' + _error(exc_)]
            if problems:
                failures += 1
                print('self-test: FAIL %s (%s)'
                      % (name, '; '.join(problems)), file=sys.stderr)
            else:
                print('self-test: caught %s' % name)
        with contextlib.redirect_stderr(io.StringIO()):
            usage_exit = main(['--bogus'])
        if usage_exit != 2:
            failures += 1
            print('self-test: FAIL usage exit', file=sys.stderr)
    finally:
        socket.socket, subprocess.run, subprocess.Popen = saved
    if tripped:
        failures += 1
        print('self-test: FAIL real factory called: %s' % tripped,
              file=sys.stderr)
    if failures:
        print('self-test: %d check(s) failed' % failures, file=sys.stderr)
        return 1
    print('self-test: pass')
    return 0


def main(argv):
    if argv == ['--self-test']:
        return self_test()
    if argv not in ([], ['--require']):
        print('usage: check_loopback_host.py [--require | --self-test]',
              file=sys.stderr)
        return 2
    # Looked up at call time so the self-test tripwires stay reliable.
    report = build_report(host_info(), socket.socket, subprocess.run, 'host')
    sys.stdout.write(json.dumps(report, sort_keys=True, indent=2) + '\n')
    return exit_code(report, require=argv == ['--require'])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
