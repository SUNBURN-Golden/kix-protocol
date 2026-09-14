"""S05: separate-filesystem checkpoints and RECONCILIATION-ONLY restoration.

Trusted single-host fixture administration, not remote storage authentication.
The archive must be on a different filesystem from the live working directory.
Whole-host loss, rollback of the archive itself and malicious administrators are
outside this profile. Provider backups are observations, never a live bank.
"""
import base64
import fcntl
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
from contextlib import closing, contextmanager
from pathlib import Path

from common import canonical, digest, require, Rejected
from storage_receipt import (StorageFault, directory_fingerprint,
                             connection_fingerprint, write_atomic, sync_directory)

BINDING = 'archive-binding.json'
POINTER = 'archive-pointer.json'
RESTORED = 'restored-from-archive.json'
DATABASES = ('projection.sqlite', 'mock-provider.sqlite')
RECORDS = ('storage-receipt.json', 'storage-command-pending.json')
HERE = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text())


def ro(path):
    return sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True,
                           isolation_level=None, timeout=10)


def sql_copy(source, destination):
    with closing(ro(source)) as src, closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)
        dst.execute('PRAGMA journal_mode=DELETE')
    with open(destination, 'rb') as stream:
        os.fsync(stream.fileno())


def state_of(directory):
    directory = Path(directory)
    dbs = {}
    for name in DATABASES:
        if (directory/name).exists():
            with closing(ro(directory/name)) as db:
                dbs[name] = connection_fingerprint(db)
    return dict(databases=dbs, records={name:read_json(directory/name)
                for name in RECORDS if (directory/name).exists()})


def ensure_live(directory):
    if (Path(directory)/RESTORED).exists():
        raise StorageFault('ARCHIVE_RESTORE_IS_RECONCILIATION_ONLY')


class ArchiveStore:
    def __init__(self, root, stream):
        require(isinstance(stream, str) and re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', stream),
                'INVALID_ARCHIVE_STREAM')
        self.root = Path(root).resolve(strict=True)
        self.directory = self.root/stream
        self.stream = stream

    @contextmanager
    def locked(self, create=False):
        if create:
            self.directory.mkdir(mode=0o700, exist_ok=True)
            sync_directory(self.root)
        require(self.directory.is_dir(), 'ARCHIVE_UNAVAILABLE')
        fd = os.open(self.directory/'archive.lock', os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(fd)

    def latest(self, expected=None):
        head = read_json(self.directory/'head.json')
        require(expected is None or head['checkpoint'] == expected, 'STALE_ARCHIVE_CHECKPOINT')
        current, sequence = head['checkpoint'], head['sequence']
        latest = None
        # Check every link. Missing latest/corrupt data must never fall back to
        # an older internally valid checkpoint.
        while current is not None:
            require(isinstance(current, str) and re.fullmatch('[0-9a-f]{64}', current), 'INVALID_ARCHIVE_HASH')
            entry = read_json(self.directory/(current+'.json'))
            require(digest(entry) == current and entry['sequence'] == sequence
                    and entry['stream'] == self.stream, 'ARCHIVE_CHAIN_CONFLICT')
            require(entry['stateHash'] == digest(entry['state']), 'ARCHIVE_STATE_CONFLICT')
            if latest is None:
                latest = entry
            current, sequence = entry['previous'], sequence-1
        require(sequence == 0, 'ARCHIVE_CHAIN_INCOMPLETE')
        return head, latest


class Archive:
    """Called while the existing live CLI command lock is held."""
    def __init__(self, source, config):
        self.source = Path(source).resolve()
        self.config = config
        require(set(config) == {'root','stream'}, 'INVALID_ARCHIVE_CONFIG')
        self.store = ArchiveStore(config['root'], config['stream'])
        require(self.store.root.stat().st_dev != self.source.stat().st_dev,
                'ARCHIVE_REQUIRES_SEPARATE_FILESYSTEM')
        require(not self.store.root.is_relative_to(self.source)
                and not self.source.is_relative_to(self.store.root), 'ARCHIVE_PATH_OVERLAP')

    @classmethod
    def for_source(cls, source, requested=None):
        source = Path(source)
        try:
            existing = read_json(source/BINDING) if (source/BINDING).exists() else None
            if existing is not None:
                require(requested is None or requested == existing, 'ARCHIVE_BINDING_CHANGED')
                archive = cls(source, existing)
                # A missing store for an enrolled source is never initialized.
                require((archive.store.directory/'head.json').exists(), 'ARCHIVE_UNAVAILABLE')
                return archive
            if requested is None:
                return None
            ensure_live(source)
            archive = cls(source, requested)
            with archive.store.locked(create=True):
                require(not (archive.store.directory/'head.json').exists(), 'ARCHIVE_STREAM_ALREADY_EXISTS')
            # Enrollment precedes all new external calls. It is not a claim
            # that requests accepted before this boundary were backed up.
            write_atomic(source/BINDING, requested)
            archive.publish('ENROLL', initial=True)
            return archive
        except (OSError, ValueError, Rejected, sqlite3.Error) as error:
            raise StorageFault('ARCHIVE_REQUIRED:'+str(error)) from error

    def check(self):
        with self.store.locked():
            head, entry = self.store.latest()
            require(read_json(self.source/POINTER) == head, 'ARCHIVE_POINTER_DIVERGED')
            require(digest(state_of(self.source)) == entry['stateHash'], 'ARCHIVE_ACKNOWLEDGED_STATE_DIVERGED')

    def anchor(self):
        """Recovery may observe newer provider facts, but never an old head."""
        with self.store.locked():
            head, _ = self.store.latest()
            require(read_json(self.source/POINTER) == head, 'ARCHIVE_POINTER_DIVERGED')
            return head

    def publish(self, boundary, initial=False):
        with self.store.locked(create=initial):
            has_head = (self.store.directory/'head.json').exists()
            head, entry = self.store.latest() if has_head else (None, None)
            before = state_of(self.source)
            state_hash = digest(before)
            # Recover loss of the local acknowledgement after the archive's
            # head advanced, only when the complete semantic state matches.
            if entry and entry['stateHash'] == state_hash:
                write_atomic(self.source/POINTER, head)
                return head
            pointer = read_json(self.source/POINTER) if (self.source/POINTER).exists() else None
            require(pointer == head, 'ARCHIVE_POINTER_DIVERGED')
            require(has_head or initial, 'ARCHIVE_UNAVAILABLE')
            databases = {}
            with tempfile.TemporaryDirectory(prefix='kix-archive-copy-') as tmp:
                for name in before['databases']:
                    dest = Path(tmp)/name
                    sql_copy(self.source/name, dest)
                    with closing(ro(dest)) as db:
                        require(connection_fingerprint(db) == before['databases'][name], 'ARCHIVE_COPY_CHANGED')
                    raw = dest.read_bytes()
                    databases[name] = dict(sha256=hashlib.sha256(raw).hexdigest(),
                                           base64=base64.b64encode(raw).decode())
            require(state_of(self.source) == before, 'ARCHIVE_SOURCE_CHANGED')
            item = dict(format='kix-separate-fs-checkpoint-v1', stream=self.store.stream,
                        sequence=head['sequence']+1 if head else 1,
                        previous=head['checkpoint'] if head else None, boundary=boundary,
                        state=before, stateHash=state_hash, databases=databases,
                        providerBackupRole='HISTORICAL_OBSERVATION_ONLY',
                        failureScope='LIVE_WORKING_DIRECTORY_LOSS_NOT_WHOLE_HOST')
            checkpoint = digest(item)
            write_atomic(self.store.directory/(checkpoint+'.json'), item)
            new_head = dict(checkpoint=checkpoint, sequence=item['sequence'])
            write_atomic(self.store.directory/'head.json', new_head)
            write_atomic(self.source/POINTER, new_head)
            return new_head


def _decode(entry, target):
    require(entry['format'] == 'kix-separate-fs-checkpoint-v1', 'ARCHIVE_FORMAT')
    require(set(entry['databases']) <= set(DATABASES)
            and set(entry['state']['records']) <= set(RECORDS), 'ARCHIVE_FILE_SET')
    for name, value in entry['databases'].items():
        raw = base64.b64decode(value['base64'], validate=True)
        require(hashlib.sha256(raw).hexdigest() == value['sha256'], 'ARCHIVE_BYTES_CHANGED')
        fd = os.open(target/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    for name, value in entry['state']['records'].items():
        write_atomic(target/name, value)
    require(state_of(target) == entry['state'], 'RESTORE_STATE_CONFLICT')


def restore(root, stream, target, checkpoint=None):
    """Use only the separate archive; never reads the old working directory."""
    store = ArchiveStore(root, stream)
    target = Path(target).resolve()
    require(not target.is_relative_to(store.root) and not store.root.is_relative_to(target),
            'RESTORE_PATH_OVERLAP')
    with store.locked():
        head, entry = store.latest(checkpoint)
        marker = dict(format='kix-reconciliation-only-restore-v1', archiveRoot=str(store.root),
                      stream=stream, head=head, stateHash=entry['stateHash'],
                      moneyExecutionAllowed=False)
        if target.exists():
            require((target/RESTORED).is_file() and read_json(target/RESTORED) == marker
                    and digest(state_of(target)) == entry['stateHash'], 'RESTORE_TARGET_EXISTS_OR_CHANGED')
            return dict(decision='RESTORED_READ_ONLY', checkpoint=head, repeated=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        candidate = Path(tempfile.mkdtemp(prefix='.kix-restore-', dir=target.parent))
        try:
            _decode(entry, candidate)
            write_atomic(candidate/RESTORED, marker)
            sync_directory(candidate)
            require(store.latest()[0] == head, 'STALE_ARCHIVE_CHECKPOINT')
            os.rename(candidate, target)
            sync_directory(target.parent)
        finally:
            if candidate.exists():
                shutil.rmtree(candidate)
        return dict(decision='RESTORED_READ_ONLY', checkpoint=head, repeated=False)


def reconcile(target, provider_database):
    """Rebuild a view from a LIVE external provider observation; never submit.

S03's original request/binding/chain checks are reused on a temporary candidate.
Even when same-key replay could be safe, this restored profile has no authority
to resume a writer. The output is an evidence report, not an execution permit.
"""
    from paid_recovery import Recovery
    from paid_integration import PaidCoordinator
    target, provider_database = Path(target).resolve(), Path(provider_database).resolve(strict=True)
    marker = read_json(target/RESTORED)
    require(provider_database.is_file() and not provider_database.is_relative_to(target),
            'LIVE_PROVIDER_MUST_BE_EXTERNAL')
    store = ArchiveStore(marker['archiveRoot'], marker['stream'])
    require(not provider_database.is_relative_to(store.root), 'ARCHIVE_COPY_IS_NOT_LIVE_PROVIDER')
    with store.locked():
        head, entry = store.latest(marker['head']['checkpoint'])
        require(marker['head'] == head and digest(state_of(target)) == marker['stateHash'] == entry['stateHash'],
                'RESTORED_SOURCE_CHANGED')
        result = dict(format='kix-archive-reconciliation-v1', checkpoint=head,
                      decision='HOLD', moneyExecutionAllowed=False,
                      providerSource='EXTERNAL_LIVE_MOCK_DATABASE', originalState=entry['state'],
                      evidenceScope='TRUSTED_LOCAL_PROVIDER_AND_SUI_RPC')
        with tempfile.TemporaryDirectory(prefix='kix-reconcile-') as tmp:
            candidate = Path(tmp)
            _decode(entry, candidate)
            (candidate/'mock-provider.sqlite').unlink(missing_ok=True)
            sql_copy(provider_database, candidate/'mock-provider.sqlite')
            with closing(ro(provider_database)) as db:
                provider_hash = connection_fingerprint(db)
            with closing(ro(candidate/'mock-provider.sqlite')) as db:
                require(connection_fingerprint(db) == provider_hash, 'LIVE_PROVIDER_CHANGED_DURING_COPY')
            recovery = Recovery(candidate)
            plan = recovery.inspect()
            result.update(plan=plan, providerHash=provider_hash)
            if plan['decision'] == 'LINK_EXISTING':
                c = PaidCoordinator(candidate)
                try:
                    c._evidence(plan['chain'])
                    if not plan['chain']['showOpen']:
                        c._run('archive-cancel-'+plan['tradeId'], 'operator', 'cancel_event',
                               eventId=plan['binding']['showId'])
                    c.sync_effect(plan['effectId'])
                    state = c.core.snapshot()
                    trade, effect = state['trades'][plan['tradeId']], state['effects'][plan['effectId']]
                    view = dict(effect=effect, trade=trade, balances=state['balances'],
                                remainingDuties=dict(payout=effect['amount']-effect['appliedAmount'],
                                  customerRefund=max(0,trade['refundDue']-trade['refunded']),
                                  recoveryReceivables={k:v for k,v in state['balances'].items()
                                                      if k.startswith('recoverable:') and v}))
                    result.update(decision='RECONCILED_VIEW', view=view)
                finally:
                    c.close()
            else:
                result['reason'] = ('RESTORED_WRITER_NOT_AUTHORIZED' if plan['decision'] == 'REPLAY_SAME_REQUEST'
                                    else plan['reason'])
            # The report also fails closed if its live premises changed while
            # the accounting view was computed.
            with closing(ro(provider_database)) as db:
                require(connection_fingerprint(db) == provider_hash, 'LIVE_PROVIDER_CHANGED_RECONCILE_AGAIN')
            with tempfile.TemporaryDirectory(prefix='kix-recheck-') as second:
                second = Path(second); _decode(entry, second)
                (second/'mock-provider.sqlite').unlink(missing_ok=True)
                sql_copy(provider_database, second/'mock-provider.sqlite')
                require(Recovery(second).inspect()['planId'] == plan['planId'], 'STALE_RECONCILIATION_PLAN')
        require(store.latest()[0] == head, 'STALE_ARCHIVE_CHECKPOINT')
        require(state_of(target) == entry['state'], 'RESTORED_SOURCE_CHANGED')
        result['reportHash'] = digest({k:v for k,v in result.items() if k != 'plan'} |
                                      {'planId':result['plan']['planId']})
        return result
