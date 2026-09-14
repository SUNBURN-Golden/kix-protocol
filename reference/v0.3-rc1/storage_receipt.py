"""Fail-closed continuity receipts for the serialized, LOCAL paid fixture.

The sidecar must survive a database rollback to detect it. This does not fix
storage corruption, protect simultaneous rollback of all files, or certify
power-loss durability. Unfinished commands require offline reconciliation.
"""
import fcntl
import json
import os
import sqlite3
from pathlib import Path
from common import canonical, digest, Rejected

DATABASES = ("projection.sqlite", "mock-provider.sqlite")


class StorageFault(Rejected):
    pass


def connection_fingerprint(db):
    if db.in_transaction:
        raise StorageFault("STORAGE_CHECK_REQUIRES_COMMITTED_STATE")
    try:
        db.execute("BEGIN")
        if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise StorageFault("STORAGE_RECOVERY_REQUIRED:INTEGRITY")
        tables = {}
        schema = db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        for name, sql in schema:
            escaped = name.replace('"', '""')
            rows = db.execute('SELECT * FROM "' + escaped + '"').fetchall()
            values = sorted(canonical([{"blob": v.hex()} if isinstance(v, bytes) else v for v in row]) for row in rows)
            tables[name] = dict(schema=sql, rows=values)
        return digest(tables)
    except sqlite3.Error as error:
        raise StorageFault("STORAGE_RECOVERY_REQUIRED:DATABASE_ERROR") from error
    finally:
        if db.in_transaction:
            db.execute("ROLLBACK")


def coordinator_fingerprint(coordinator):
    return {DATABASES[0]: connection_fingerprint(coordinator.core.db),
            DATABASES[1]: connection_fingerprint(coordinator.provider.db)}


def directory_fingerprint(directory):
    result = {}
    for name in DATABASES:
        path = Path(directory) / name
        if not path.is_file():
            raise StorageFault("STORAGE_RECOVERY_REQUIRED:MISSING_DATABASE")
        try:
            db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, isolation_level=None, timeout=10)
            try:
                result[name] = connection_fingerprint(db)
            finally:
                db.close()
        except sqlite3.Error as error:
            raise StorageFault("STORAGE_RECOVERY_REQUIRED:DATABASE_ERROR") from error
    return result


def sync_directory(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_atomic(path, value):
    temporary = path.with_name(path.name + "." + str(os.getpid()) + ".pending")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(canonical(value) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


class StorageReceipt:
    """Serialize one local CLI command; never bless unknown existing state."""
    def __init__(self, directory, request):
        self.directory = Path(directory)
        self.request_hash = digest(request)
        self.receipt_path = self.directory / "storage-receipt.json"
        self.pending_path = self.directory / "storage-command-pending.json"
        self.lock = None
        self.previous = None

    def __enter__(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = os.open(self.directory / "storage.lock", os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            os.close(self.lock)
            self.lock = None
            raise StorageFault("STORAGE_COMMAND_ALREADY_RUNNING") from error
        return self

    def begin(self):
        if self.pending_path.exists():
            raise StorageFault("STORAGE_RECOVERY_REQUIRED:UNFINISHED_COMMAND")
        existing = any((self.directory / name).exists() for name in DATABASES)
        if self.receipt_path.exists():
            try:
                self.previous = json.loads(self.receipt_path.read_text())
                if (self.previous["format"] != "kix-local-storage-receipt-v1"
                        or type(self.previous["sequence"]) is not int or self.previous["sequence"] < 1):
                    raise ValueError("receipt format")
                expected = self.previous["databases"]
            except (ValueError, KeyError, TypeError) as error:
                raise StorageFault("STORAGE_RECOVERY_REQUIRED:INVALID_RECEIPT") from error
            if directory_fingerprint(self.directory) != expected:
                raise StorageFault("STORAGE_RECOVERY_REQUIRED:ACKNOWLEDGED_STATE_CHANGED")
        elif existing:
            raise StorageFault("STORAGE_RECOVERY_REQUIRED:UNTRACKED_DATABASE")
        write_atomic(self.pending_path, dict(format="kix-local-storage-pending-v1", requestHash=self.request_hash,
                     previousReceiptHash=digest(self.previous) if self.previous else None))

    def finish(self, coordinator):
        if not self.pending_path.exists():
            raise StorageFault("STORAGE_RECOVERY_REQUIRED:MISSING_PENDING_COMMAND")
        expected = coordinator_fingerprint(coordinator)
        coordinator.close()
        if directory_fingerprint(self.directory) != expected:
            raise StorageFault("STORAGE_RECOVERY_REQUIRED:STATE_CHANGED_ON_CLOSE")
        receipt = dict(format="kix-local-storage-receipt-v1", sequence=(self.previous["sequence"] if self.previous else 0)+1,
                       requestHash=self.request_hash, databases=expected)
        write_atomic(self.receipt_path, receipt)
        self.pending_path.unlink()
        sync_directory(self.directory)
        return dict(sequence=receipt["sequence"], receiptHash=digest(receipt))

    def __exit__(self, *_):
        if self.lock is not None:
            os.close(self.lock)
            self.lock = None
