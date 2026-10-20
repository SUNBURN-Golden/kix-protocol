#!/usr/bin/env python3
"""Read-only preflight check for the stage-5 pinned host prerequisites.

Reports, without installing or changing anything, whether the host this
script runs on meets the ``k-stage5-durable-tx`` acceptance prerequisites
named in the blocked node's DECISION_REQUIRED record
(``/workspace/kix-run/state/k-stage5-durable-tx.decision.md``,
``validation/2026-10-13-k-stage5-durable-tx/README.md``):

- executable PostgreSQL binaries at
  ``/usr/lib/postgresql/17/bin/postgres`` and
  ``/usr/lib/postgresql/17/bin/initdb``, each reporting the exact banner
  ``<name> (PostgreSQL) 17.11 (Debian 17.11-0+deb13u1)`` for ``--version``
  (the adopted local non-production pin,
  ``docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md``);
- ``psycopg`` importable by this interpreter's ``python3``, major
  version exactly ``3``;
- ``taskset`` and ``ss`` executable on ``PATH``;
- CPU cores ``0`` and ``1`` inside the process affinity mask
  (``os.sched_getaffinity(0)``).

Output is one JSON object per line: one ``type="check"`` line per
prerequisite with ``status`` ``"PASS"`` or ``"FAIL"``, then a
``type="summary"`` line with ``schema_version`` 1, ``mode``,
overall ``status``, ``evidence_prep: true`` and
``acceptance_run: false``. Every prerequisite is probed even if another
fails; there is no retry and no polling. Exit status is ``0`` when all
checks pass, ``1`` when any check (or the self-test) fails, ``2`` for
invalid command-line usage.

A PASS is evidence that the named prerequisites were observed on this
host. It is not stage-5 acceptance, host qualification, provisioning
approval, durability evidence or production readiness; this run prepares
option-1 evidence for the blocked node and runs no acceptance suite.

``--self-test`` injects synthetic observations and never probes the
actual host. Standard library only.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

POSTGRES_DIR = '/usr/lib/postgresql/17/bin'
POSTGRES_BINARIES = ('postgres', 'initdb')
EXPECTED_VERSION_SUFFIX = ' (PostgreSQL) 17.11 (Debian 17.11-0+deb13u1)'
PATH_TOOLS = ('taskset', 'ss')
REQUIRED_CORES = frozenset({0, 1})
PROBE_TIMEOUT_SECONDS = 10
SCHEMA_VERSION = 1


def _run_command(args):
    """Run ``args`` (no shell, captured output, bounded) and return a dict."""
    try:
        completed = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except OSError as exc:
        return {'ok': False, 'error': '%s: %s' % (type(exc).__name__, exc)}
    except subprocess.TimeoutExpired:
        return {'ok': False,
                'error': 'timeout after %ds' % PROBE_TIMEOUT_SECONDS}
    return {
        'ok': completed.returncode == 0,
        'returncode': completed.returncode,
        'stdout': completed.stdout.strip(),
        'stderr': completed.stderr.strip(),
    }


def collect_host():
    """Gather host observations; every failure is recorded, never raised."""
    observations = {}
    for name in POSTGRES_BINARIES:
        path = os.path.join(POSTGRES_DIR, name)
        entry = {'path': path, 'present': os.path.isfile(path),
                 'executable': os.access(path, os.X_OK)}
        if entry['executable']:
            entry['version'] = _run_command([path, '--version'])
        observations[name] = entry
    observations['psycopg'] = _run_command(
        [sys.executable, '-B', '-c',
         'import psycopg; print(psycopg.__version__)'])
    for tool in PATH_TOOLS:
        observations[tool] = {'resolved': shutil.which(tool)}
    try:
        affinity = sorted(os.sched_getaffinity(0))
        observations['cpu_affinity'] = {'available': True, 'cpus': affinity}
    except (AttributeError, OSError) as exc:
        observations['cpu_affinity'] = {
            'available': False,
            'error': '%s: %s' % (type(exc).__name__, exc)}
    return observations


def _check_binary(name, entry):
    expected = name + EXPECTED_VERSION_SUFFIX
    result = {'id': name, 'expected': expected, 'observed': entry}
    if not entry['present']:
        result.update(status='FAIL', reason='file not present')
    elif not entry['executable']:
        result.update(status='FAIL', reason='not executable')
    elif not entry['version']['ok']:
        version = entry['version']
        reason = version.get('error') or 'non-zero exit %s' % version[
            'returncode']
        result.update(status='FAIL', reason=reason)
    elif entry['version']['stdout'] != expected:
        result.update(status='FAIL', reason='version banner mismatch')
    else:
        result.update(status='PASS', reason='exact pin banner')
    return result


def _check_psycopg(entry):
    result = {'id': 'psycopg',
              'expected': 'importable psycopg, major version 3',
              'observed': entry}
    if not entry['ok']:
        reason = entry.get('error') or 'import failed: %s' % (
            entry['stderr'] or 'exit %s' % entry['returncode'])
        result.update(status='FAIL', reason=reason)
        return result
    version = entry['stdout']
    major = version.split('.', 1)[0]
    if major == '3':
        result.update(status='PASS', reason='psycopg %s' % version)
    else:
        result.update(status='FAIL',
                      reason='unparseable or wrong major version: %r'
                      % version)
    return result


def _check_tool(name, entry):
    result = {'id': name, 'expected': 'executable on PATH',
              'observed': entry}
    if entry['resolved']:
        result.update(status='PASS', reason=entry['resolved'])
    else:
        result.update(status='FAIL', reason='not found on PATH')
    return result


def _check_affinity(entry):
    result = {'id': 'cpu_affinity',
              'expected': 'cores 0 and 1 in sched_getaffinity(0)',
              'observed': entry}
    if not entry['available']:
        result.update(status='FAIL', reason=entry['error'])
    elif REQUIRED_CORES <= set(entry['cpus']):
        result.update(status='PASS',
                      reason='cores %s available' % entry['cpus'])
    else:
        result.update(status='FAIL',
                      reason='required cores %s not in affinity %s'
                      % (sorted(REQUIRED_CORES), entry['cpus']))
    return result


def evaluate_host(observations):
    """Return one result dict per prerequisite, in a fixed order."""
    results = [
        _check_binary('postgres', observations['postgres']),
        _check_binary('initdb', observations['initdb']),
        _check_psycopg(observations['psycopg']),
        _check_tool('taskset', observations['taskset']),
        _check_tool('ss', observations['ss']),
        _check_affinity(observations['cpu_affinity']),
    ]
    for result in results:
        result['type'] = 'check'
    return results


def emit_report(results, mode, stream):
    """Serialize check lines then the summary line as JSON objects."""
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = len(results) - passed
    for result in results:
        stream.write(json.dumps(result, sort_keys=True) + '\n')
    summary = {
        'type': 'summary',
        'schema_version': SCHEMA_VERSION,
        'mode': mode,
        'status': 'PASS' if failed == 0 else 'FAIL',
        'evidence_prep': True,
        'acceptance_run': False,
        'checks_passed': passed,
        'checks_failed': failed,
    }
    stream.write(json.dumps(summary, sort_keys=True) + '\n')
    return 0 if failed == 0 else 1


def _binary_obs(version=None, present=True, executable=True):
    entry = {'path': os.path.join(POSTGRES_DIR, 'NAME'),
             'present': present, 'executable': executable}
    if version is not None:
        entry['version'] = version
    return entry


def _fake_observations(**overrides):
    good = {'ok': True, 'returncode': 0,
            'stderr': ''}
    obs = {
        'postgres': _binary_obs(
            dict(good, stdout='postgres' + EXPECTED_VERSION_SUFFIX)),
        'initdb': _binary_obs(
            dict(good, stdout='initdb' + EXPECTED_VERSION_SUFFIX)),
        'psycopg': dict(good, stdout='3.2.3'),
        'taskset': {'resolved': '/usr/bin/taskset'},
        'ss': {'resolved': '/usr/bin/ss'},
        'cpu_affinity': {'available': True, 'cpus': [0, 1, 2, 3]},
    }
    for key, value in overrides.items():
        obs[key] = value
    return obs


def self_test():
    """Check the evaluator catches each synthetic break; probe nothing."""
    ok_banner = {'ok': True, 'returncode': 0,
                 'stdout': 'postgres' + EXPECTED_VERSION_SUFFIX,
                 'stderr': ''}
    bad = {'ok': False, 'returncode': 1, 'stdout': '',
           'stderr': 'boom'}
    cases = [
        ('all prerequisites pass', _fake_observations(), 'PASS', 0),
        ('postgres binary missing',
         _fake_observations(postgres=_binary_obs(present=False,
                                                 executable=False)),
         'FAIL', 1),
        ('postgres binary not executable',
         _fake_observations(postgres=_binary_obs(executable=False)),
         'FAIL', 1),
        ('postgres --version exits non-zero',
         _fake_observations(postgres=_binary_obs(bad)), 'FAIL', 1),
        ('postgres --version times out',
         _fake_observations(postgres=_binary_obs(
             {'ok': False, 'error': 'timeout after 10s'})), 'FAIL', 1),
        ('wrong upstream version 17.10',
         _fake_observations(postgres=_binary_obs(dict(
             ok_banner, stdout='postgres (PostgreSQL) 17.10 '
             '(Debian 17.10-0+deb13u1)'))), 'FAIL', 1),
        ('wrong version 17.110 (no substring match)',
         _fake_observations(postgres=_binary_obs(dict(
             ok_banner, stdout='postgres (PostgreSQL) 17.110 '
             '(Debian 17.110-0+deb13u1)'))), 'FAIL', 1),
        ('wrong debian revision deb13u2',
         _fake_observations(postgres=_binary_obs(dict(
             ok_banner, stdout='postgres (PostgreSQL) 17.11 '
             '(Debian 17.11-0+deb13u2)'))), 'FAIL', 1),
        ('missing debian revision',
         _fake_observations(postgres=_binary_obs(dict(
             ok_banner, stdout='postgres (PostgreSQL) 17.11'))),
         'FAIL', 1),
        ('trailing suffix on banner',
         _fake_observations(postgres=_binary_obs(dict(
             ok_banner, stdout='postgres' + EXPECTED_VERSION_SUFFIX
             + ' extra'))), 'FAIL', 1),
        ('initdb banner mismatches independently',
         _fake_observations(initdb=_binary_obs(dict(
             ok_banner, stdout='initdb (PostgreSQL) 17.10 '
             '(Debian 17.10-0+deb13u1)'))), 'FAIL', 1),
        ('psycopg import fails',
         _fake_observations(psycopg={
             'ok': False, 'returncode': 1, 'stdout': '',
             'stderr': 'ModuleNotFoundError: No module named psycopg'}),
         'FAIL', 1),
        ('psycopg probe times out (error-key dict)',
         _fake_observations(psycopg={
             'ok': False, 'error': 'timeout after 10s'}),
         'FAIL', 1),
        ('psycopg major version 2',
         _fake_observations(psycopg=dict(ok_banner, stdout='2.9.10')),
         'FAIL', 1),
        ('psycopg major version 4',
         _fake_observations(psycopg=dict(ok_banner, stdout='4.0')),
         'FAIL', 1),
        ('psycopg version unparseable',
         _fake_observations(psycopg=dict(ok_banner, stdout='unknown')),
         'FAIL', 1),
        ('taskset missing from PATH',
         _fake_observations(taskset={'resolved': None}), 'FAIL', 1),
        ('ss missing from PATH',
         _fake_observations(ss={'resolved': None}), 'FAIL', 1),
        ('core 1 outside affinity mask',
         _fake_observations(cpu_affinity={'available': True,
                                          'cpus': [0, 2, 3]}),
         'FAIL', 1),
        ('affinity API unavailable',
         _fake_observations(cpu_affinity={
             'available': False,
             'error': 'AttributeError: sched_getaffinity'}), 'FAIL', 1),
    ]
    failures = 0
    for name, observations, want_status, want_exit in cases:
        import io
        stream = io.StringIO()
        results = evaluate_host(observations)
        exit_code = emit_report(results, 'self-test', stream)
        lines = [json.loads(line) for line in stream.getvalue().splitlines()]
        summary = lines[-1]
        checks = lines[:-1]
        problems = []
        if exit_code != want_exit:
            problems.append('exit %d != %d' % (exit_code, want_exit))
        if summary['status'] != want_status:
            problems.append('status %s != %s'
                            % (summary['status'], want_status))
        if len(checks) != 6:
            problems.append('expected 6 check lines, got %d' % len(checks))
        for field in ('schema_version', 'evidence_prep',
                      'acceptance_run', 'checks_passed', 'checks_failed'):
            if field not in summary:
                problems.append('summary missing %s' % field)
        if summary.get('evidence_prep') is not True or \
                summary.get('acceptance_run') is not False:
            problems.append('report flags wrong')
        if want_status == 'FAIL' and not any(
                c['status'] == 'FAIL' for c in checks):
            problems.append('no per-item FAIL line emitted')
        if problems:
            failures += 1
            print('self-test: FAIL %s (%s)' % (name, '; '.join(problems)),
                  file=sys.stderr)
        else:
            print('self-test: caught %s' % name)
    if failures:
        print('self-test: %d case(s) failed' % failures, file=sys.stderr)
        return 1
    print('self-test: pass')
    return 0


def main(argv):
    if argv == ['--self-test']:
        return self_test()
    if argv:
        print('usage: check_stage5_host.py [--self-test]', file=sys.stderr)
        return 2
    return emit_report(evaluate_host(collect_host()), 'host', sys.stdout)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
