"""Disposable local PostgreSQL and FoundationDB processes."""

from __future__ import annotations

import getpass
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import psycopg

from exploration.stage4.budget import (
    CPU_CORES,
    FDB_CACHE_MEMORY,
    FDB_MEMORY,
    FDB_PORT,
    FDB_STORAGE_MEMORY,
    POSTGRES_SHARED_BUFFERS,
)
from exploration.stage4.fdb_c import Database, FdbError

POSTGRES = '/usr/lib/postgresql/17/bin/postgres'
INITDB = '/usr/lib/postgresql/17/bin/initdb'
FDBSERVER = '/usr/sbin/fdbserver'
FDBCLI = '/usr/bin/fdbcli'
_REQUIRED_SETTINGS = {
    'fsync': 'on',
    'full_page_writes': 'on',
    'synchronous_commit': 'on',
    'autovacuum': 'off',
    'data_checksums': 'on',
}


def quiesce_package_fdb():
    """Stop the package default server. It is not a measurement subject."""
    proc = Path('/proc')
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / 'cmdline').read_bytes().replace(b'\x00', b' ')
        except OSError:
            continue
        if b'/etc/foundationdb/' not in raw and b'/var/lib/foundationdb' not in raw:
            continue
        if b'fdbserver' not in raw and b'fdbmonitor' not in raw and b'backup_agent' not in raw:
            continue
        pid = int(entry.name)
        try:
            os.kill(pid, signal.SIGTERM)
        except PermissionError:
            subprocess.run(['sudo', '-n', 'kill', str(pid)], check=False)
        except ProcessLookupError:
            pass


def _hwm_bytes(pid):
    try:
        text = Path('/proc/%s/status' % pid).read_text()
    except OSError:
        return 0
    for line in text.splitlines():
        if line.startswith('VmHWM:'):
            return int(line.split()[1]) * 1024
    return 0


def _du(path):
    total = 0
    root = Path(path)
    if not root.exists():
        return 0
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(dirpath, name))
            except OSError:
                continue
    return total


def _tail(path, limit=80):
    try:
        lines = Path(path).read_text(errors='replace').splitlines()
    except OSError:
        return ''
    return '\n'.join(lines[-limit:])


class PostgresCluster:
    def __init__(self, root):
        self.root = Path(root)
        self.data = self.root / 'data'
        self.sock = self.root / 'sock'
        self.log = self.root / 'postgres.log'
        self.proc = None
        self._log_handle = None
        self.peak_server_bytes = 0
        self.settings = None
        self.version = None

    def start(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.root.chmod(0o700)
        self.sock.mkdir(parents=True, exist_ok=True)
        self.sock.chmod(0o700)
        for stale in self.sock.glob('.s.PGSQL.*'):
            stale.unlink()
        if not (self.data / 'PG_VERSION').exists():
            self._initdb()
        self._launch()
        self._wait_ready()
        self.note_rss()
        self.settings = self.read_settings()
        self._assert_settings()
        self._assert_no_tcp()

    def connect(self):
        return psycopg.connect(
            host=str(self.sock),
            dbname='postgres',
            user=getpass.getuser(),
            autocommit=True,
            application_name='kix_stage4_exploration',
        )

    def wal_bytes(self):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0')",
            ).fetchone()
        return int(row[0])

    def disk_bytes(self):
        return _du(self.data) + _du(self.log)

    def note_rss(self):
        if self.proc is not None and self.proc.poll() is None:
            self.peak_server_bytes = max(self.peak_server_bytes, _hwm_bytes(self.proc.pid))

    def read_settings(self):
        names = (
            'fsync', 'full_page_writes', 'synchronous_commit', 'autovacuum',
            'data_checksums', 'listen_addresses', 'shared_buffers', 'server_version',
        )
        with self.connect() as conn:
            rows = conn.execute(
                'SELECT name, setting, unit FROM pg_settings WHERE name = ANY(%s)',
                (list(names),),
            ).fetchall()
            version = conn.execute('SELECT version()').fetchone()[0]
        self.version = version
        return {row[0]: {'setting': row[1], 'unit': row[2]} for row in rows}

    def stop(self):
        self._signal(signal.SIGTERM)

    def kill(self):
        self._signal(signal.SIGKILL)

    def _initdb(self):
        env = os.environ.copy()
        env['LC_ALL'] = 'C'
        completed = subprocess.run(
            [
                INITDB, '-D', str(self.data),
                '--username', getpass.getuser(),
                '--auth-local=trust', '--auth-host=reject',
                '--encoding=UTF8', '--locale=C', '--data-checksums',
            ],
            check=False, capture_output=True, text=True, env=env,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr[-2000:])
        conf = self.data / 'postgresql.conf'
        with conf.open('a') as handle:
            handle.write(
                "\nlisten_addresses = ''\n"
                "unix_socket_directories = '%s'\n"
                "fsync = on\n"
                "full_page_writes = on\n"
                "synchronous_commit = on\n"
                "autovacuum = off\n"
                "shared_buffers = %s\n"
                "work_mem = 4MB\n"
                "maintenance_work_mem = 32MB\n"
                "max_connections = 8\n"
                "max_wal_size = 64MB\n"
                "min_wal_size = 32MB\n"
                "huge_pages = off\n" % (self.sock, POSTGRES_SHARED_BUFFERS)
            )

    def _launch(self):
        self._close_log()
        self._log_handle = open(self.log, 'ab')
        cores = ','.join(str(core) for core in CPU_CORES)
        self.proc = subprocess.Popen(
            ['taskset', '-c', cores, POSTGRES, '-D', str(self.data)],
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    def _wait_ready(self):
        last = None
        for _ in range(100):
            if self.proc.poll() is not None:
                break
            try:
                conn = self.connect()
            except psycopg.OperationalError as exc:
                last = exc
                time.sleep(0.1)
                continue
            conn.close()
            return
        raise RuntimeError('postgres did not start\n%s\n%s' % (_tail(self.log), last))

    def _assert_settings(self):
        for name, expected in _REQUIRED_SETTINGS.items():
            observed = self.settings[name]['setting']
            if observed != expected:
                raise RuntimeError('%s=%s' % (name, observed))
        if self.settings['listen_addresses']['setting'] != '':
            raise RuntimeError('postgres listen_addresses is not empty')

    def _assert_no_tcp(self):
        completed = subprocess.run(['ss', '-ltn'], check=True, capture_output=True, text=True)
        for line in completed.stdout.splitlines():
            if ':5432' in line:
                raise RuntimeError('postgres TCP listener: %s' % line)

    def _signal(self, sig):
        proc = self.proc
        if proc is None or proc.poll() is not None:
            self._close_log()
            return
        try:
            os.killpg(os.getpgid(proc.pid), sig)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait(timeout=5)
        self._close_log()

    def _close_log(self):
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None


class FoundationCluster:
    def __init__(self, root):
        self.root = Path(root)
        self.data = self.root / 'data'
        self.logs = self.root / 'logs'
        self.cluster_file = self.root / 'fdb.cluster'
        self.marker = self.root / 'configured'
        self.proc = None
        self._log_handle = None
        self.db = None
        self.peak_server_bytes = 0
        self.status = None
        self.version = None

    def start(self):
        quiesce_package_fdb()
        self.root.mkdir(parents=True, exist_ok=True)
        self.root.chmod(0o700)
        self.data.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        first = not self.marker.exists()
        if first and not self.cluster_file.exists():
            self.cluster_file.write_text(
                'kixexplore:kixexplore@127.0.0.1:%d\n' % FDB_PORT,
            )
        self._launch()
        self._wait_port()
        self._open_database()
        if first:
            self._configure()
            self._set_health()
            self.marker.write_text('configured\n')
        else:
            self._wait_health()
        self.status = self._status()
        self._assert_local_listen()
        self.note_rss()
        self.version = _run_text([FDBSERVER, '-v'])

    def database(self):
        if self.db is None:
            raise RuntimeError('foundationdb database is closed')
        return self.db

    def disk_bytes(self):
        return _du(self.data) + _du(self.logs)

    def note_rss(self):
        if self.proc is not None and self.proc.poll() is None:
            self.peak_server_bytes = max(self.peak_server_bytes, _hwm_bytes(self.proc.pid))

    def stop(self):
        self._close_database()
        self._signal(signal.SIGTERM)

    def kill(self):
        self._close_database()
        self._signal(signal.SIGKILL)

    def _launch(self):
        self._close_log()
        stdout = self.logs / 'stdout.log'
        self._log_handle = open(stdout, 'ab')
        cores = ','.join(str(core) for core in CPU_CORES)
        self.proc = subprocess.Popen(
            [
                'taskset', '-c', cores, FDBSERVER,
                '-p', '127.0.0.1:%d' % FDB_PORT,
                '-l', '127.0.0.1:%d' % FDB_PORT,
                '-C', str(self.cluster_file),
                '-d', str(self.data),
                '-L', str(self.logs),
                '--memory', FDB_MEMORY,
                '--storage-memory', FDB_STORAGE_MEMORY,
                '--cache-memory', FDB_CACHE_MEMORY,
                '--logsize', '1MiB',
                '--maxlogssize', '8MiB',
            ],
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    def _wait_port(self):
        deadline = time.time() + 30
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError('fdbserver exited\n%s' % _tail(self.logs / 'stdout.log'))
            try:
                sock = socket.create_connection(('127.0.0.1', FDB_PORT), timeout=0.2)
            except OSError:
                time.sleep(0.1)
                continue
            sock.close()
            return
        raise RuntimeError('fdbserver port did not open\n%s' % _tail(self.logs / 'stdout.log'))

    def _open_database(self):
        self._close_database()
        last = None
        for _ in range(50):
            try:
                self.db = Database(str(self.cluster_file))
                return
            except FdbError as exc:
                last = exc
                time.sleep(0.2)
        raise RuntimeError('fdb database did not open: %s' % last)

    def _configure(self):
        last = ''
        deadline = time.time() + 40
        while time.time() < deadline:
            completed = subprocess.run(
                [FDBCLI, '-C', str(self.cluster_file), '--exec', 'configure new single ssd'],
                check=False, capture_output=True, text=True,
            )
            last = (completed.stdout + completed.stderr)[-2000:]
            if completed.returncode == 0 and 'ERROR' not in completed.stdout:
                return
            time.sleep(0.4)
        raise RuntimeError('fdb configure failed\n%s' % last)

    def _set_health(self):
        key = b'kixexp/health'
        tr = self.database().transaction()
        try:
            tr.set(key, b'1')
            tr.commit()
        finally:
            tr.close()
        self._wait_health()

    def _wait_health(self):
        deadline = time.time() + 30
        last = None
        while time.time() < deadline:
            tr = self.database().transaction()
            try:
                value = tr.get(b'kixexp/health', snapshot=True)
            except FdbError as exc:
                last = exc
                value = None
            finally:
                tr.close()
            if value == b'1':
                return
            time.sleep(0.2)
        raise RuntimeError('fdb health key missing: %s' % last)

    def _status(self):
        completed = subprocess.run(
            [FDBCLI, '-C', str(self.cluster_file), '--exec', 'status json'],
            check=False, capture_output=True, text=True,
        )
        text = completed.stdout.strip()
        if not text:
            return {'error': completed.stderr[-1000:]}
        import json
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return {'unparsed': text[:2000]}
        cluster = payload.get('cluster', {})
        return {
            'configuration': cluster.get('configuration'),
            'fault_tolerance': (
                cluster.get('fault_tolerance')
                or payload.get('fault_tolerance')
            ),
            'processes': len(cluster.get('processes', {})) if isinstance(cluster.get('processes'), dict) else None,
        }

    def _assert_local_listen(self):
        completed = subprocess.run(['ss', '-ltn'], check=True, capture_output=True, text=True)
        rows = [line for line in completed.stdout.splitlines() if ':%d' % FDB_PORT in line]
        if not rows:
            raise RuntimeError('fdb port is not listening')
        for line in rows:
            if '127.0.0.1:%d' % FDB_PORT not in line:
                raise RuntimeError('fdb is not bound to localhost: %s' % line)

    def _close_database(self):
        if self.db is not None:
            self.db.close()
            self.db = None

    def _signal(self, sig):
        proc = self.proc
        if proc is None or proc.poll() is not None:
            self._close_log()
            return
        try:
            os.killpg(os.getpgid(proc.pid), sig)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait(timeout=5)
        self._close_log()

    def _close_log(self):
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None


def _run_text(args):
    completed = subprocess.run(args, check=False, capture_output=True, text=True)
    return (completed.stdout or completed.stderr).strip()
