"""Evidence-based recovery of ONE interrupted local fixture payout.

Trusted local administration, synthetic PG/bank, trusted Sui RPC. No crash-site
input, no arbitrary state adoption, no historical-loss repair. The original
projection must match the durable pre-call witness. Recovery builds accounting
changes on a copy and journals the exact old/new fingerprints before installing
it. A process death during that installation can therefore be distinguished
from an unknown database change. Same-filesystem loss is still outside scope.
"""
import json
import os
import shutil
import sqlite3
import subprocess
import time
from contextlib import closing
from pathlib import Path

from common import canonical, digest, Rejected, require
from mock_provider import MockProvider, SCOPE
from paid_integration import PaidCoordinator
from storage_receipt import (StorageReceipt, StorageFault, connection_fingerprint,
                             directory_fingerprint, sync_directory, write_atomic)

HERE = Path(__file__).resolve().parent
CONTRACT = dict(id='kix-mock:stable-key:v1', scope=SCOPE, replaySafe=True,
                retention='UNLIMITED_FIXTURE', executionWindowSeconds=3600)


def read_json(path):
    return json.loads(path.read_text())


def readonly(path):
    return sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True, isolation_level=None)


def copy_database(source, target):
    """SQLite backup of a closed/serialized source, never a naked WAL file copy."""
    with closing(readonly(source)) as src, closing(sqlite3.connect(target)) as dst:
        src.backup(dst)
        dst.execute('PRAGMA journal_mode=DELETE')
    with open(target, 'rb') as stream:
        os.fsync(stream.fileno())
    sync_directory(target.parent)


def chain_context(endpoint, binding, submission):
    q = dict(action='recovery', endpoint=endpoint, binding=binding, submission=submission)
    r = subprocess.run(['node', str(HERE/'client/paid-chain.mjs')], input=canonical(q),
                       capture_output=True, text=True, timeout=45, cwd=HERE/'client')
    require(r.returncode == 0, 'CHAIN_QUERY_FAILED')
    result = json.loads(r.stdout)
    require(result['bindingHash'] == digest(binding), 'CHAIN_BINDING_MISMATCH')
    # Query time belongs in the report; it must not make identical facts stale.
    result.get('sale', {}).pop('observedAt', None)
    return result


class Recovery:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.pending = self.directory/'storage-command-pending.json'
        self.receipt = self.directory/'storage-receipt.json'
        self.cases = self.directory/'recovery-cases'

    def inspect(self):
        # The same local lock as normal CLI; begin() would reject the pending
        # command, so recovery validates it below instead. No DB writes here.
        with StorageReceipt(self.directory, {'action': 'recovery_inspect'}):
            return self._inspect()

    def _inspect(self):
        report = dict(format='kix-local-recovery-plan-v1', observedAt=time.time(),
                      decision='HOLD', reason='INSUFFICIENT_EVIDENCE',
                      followUp='Preserve evidence; reconcile source records before retry.',
                      providerContract=CONTRACT, source='LOCAL_FIXTURE_ONLY')
        try:
            p = read_json(self.pending)
            report['pendingHash'] = digest(p)
            report['originalCommand'] = p.get('request')
            require(digest(p.get('request')) == p['requestHash'], 'ORIGINAL_COMMAND_MISSING_OR_CHANGED')
            require(p['previousReceiptHash'] == digest(read_json(self.receipt)), 'PREVIOUS_RECEIPT_CHANGED')
            w = p.get('execution')
            require(w is not None, 'PRE_CALL_WITNESS_MISSING')
            eid = w['effectId']
            require(p['request']['action'] == 'send_effect' and p['request']['params']['eid'] == eid,
                    'RECOVERY_TARGET_MISMATCH')
            report['databases'] = directory_fingerprint(self.directory)
            require(report['databases']['projection.sqlite'] == w['databases']['projection.sqlite'],
                    'PROJECTION_DIVERGED_FROM_WITNESS')
            with closing(readonly(self.directory/'projection.sqlite')) as db:
                state = json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
                def item(key):
                    row = db.execute('SELECT body FROM integration_items WHERE id=?', (key,)).fetchone()
                    return json.loads(row[0]) if row else None
                x = state['effects'][eid]
                tid = x['trade']
                b, sub = item('binding-'+tid), item('submission-'+tid)
                final_row = db.execute('SELECT body FROM integration_final WHERE trade_id=?', (tid,)).fetchone()
                final = json.loads(final_row[0]) if final_row else None
            report.update(effectId=eid, tradeId=tid, originalRequest=x['request'],
                          requestBytes=x['requestBytes'], requestHash=x['requestHash'],
                          idempotencyKey=x['idempotencyKey'], binding=b, submission=sub,
                          ledger=dict(effect=x, trade=state['trades'][tid], balances=state['balances'],
                                      commandSequence=len(state['events_log'])),
                          replayUntil=w['replayUntil'])
            require(x['kind'] == 'PAYOUT' and x['sent'] and x['dispatch']['attempts'] == 1,
                    'ONLY_FIRST_INTERRUPTED_PAYOUT_SUPPORTED')
            require(x['state'] == 'OUTCOME_UNKNOWN' and not x['appliedAmount'] and not x['conflict'],
                    'EFFECT_STATE_REQUIRES_MANUAL_RECONCILIATION')
            permit = w['permit']
            require(x['requestBytes'] == canonical(x['request']) and x['requestHash'] == digest(x['request'])
                    and all(permit[k] == x[k] for k in ('requestBytes','requestHash','idempotencyKey')),
                    'DURABLE_REQUEST_CONFLICT')
            with closing(readonly(self.directory/'mock-provider.sqlite')) as db:
                rows = [list(row) for row in db.execute('SELECT * FROM operations ORDER BY key')]
            report['providerRows'] = rows
            key = x['idempotencyKey']
            require([r for r in rows if r[0] != key] == [r for r in w['providerRows'] if r[0] != key],
                    'UNRELATED_PROVIDER_STATE_CHANGED')
            matches = [r for r in rows if r[0] == key]
            fact = json.loads(matches[0][3]) if matches else None
            report['providerResult'] = fact
            report['providerLookup'] = dict(scope=SCOPE, key=key, requestHash=x['requestHash'],
                                            result='FOUND' if fact else 'NOT_FOUND')
            if fact:
                row = matches[0]
                require(row[1] == x['requestHash'] and row[2] == x['requestBytes']
                        and fact['request'] == x['request'] and fact['requestHash'] == x['requestHash']
                        and fact['idempotencyKey'] == key and fact['provenance'] == 'MOCK_PROVIDER_ONLY'
                        and fact['operationId'] == 'mock-'+digest([SCOPE,key]), 'PROVIDER_BINDING_CONFLICT')
                require(fact['status'] in ('PENDING','SUCCESS') and type(fact['funds']) is bool
                        and not fact['settlement'], 'PROVIDER_EVIDENCE_CONFLICT')
            require(sub and final and final['state'] == 'EXECUTED_SUCCESS', 'CHAIN_SUBMISSION_OR_FINAL_MISSING')
            context = chain_context(p['request']['endpoint'], b, sub)
            report['chain'] = context
            sale = context['sale']
            require(context['bindingHash'] == digest(b) and sale['state'] == 'EXECUTED_SUCCESS'
                    and all(sale[k] == final[k] for k in ('digest','rawHash','allocation')),
                    'CHAIN_EVIDENCE_UNKNOWN_OR_CONFLICTING')
            require(type(context['showOpen']) is bool, 'CHAIN_SHOW_STATE_UNKNOWN')
            if fact:
                report.update(decision='LINK_EXISTING', reason='PROVIDER_EXECUTION_FOUND')
            else:
                r = state['trades'][tid]
                require(context['showOpen'] and state['events'][r['event']]['status'] == 'COMPLETED'
                        and not r['reversalRequested'] and x['allocationVersion'] == r['allocationVersion'],
                        'PAYOUT_NO_LONGER_ALLOWED')
                require(x['amount'] <= -state['balances'][x['owed']], 'OBLIGATION_CHANGED')
                require(CONTRACT['scope'] == x['request']['scope'] and CONTRACT['replaySafe'],
                        'NOT_FOUND_DOES_NOT_ESTABLISH_SAFE_REPLAY')
                require(time.time() < w['replayUntil'] and state['clock'] < x['dispatch']['idempotencyUntil'],
                        'REPLAY_WINDOW_EXPIRED')
                report.update(decision='REPLAY_SAME_REQUEST', reason='SAME_KEY_CONTRACT_AND_CURRENT_GUARDS_VALID')
        except (Rejected, KeyError, TypeError, ValueError, OSError, sqlite3.Error, subprocess.SubprocessError) as error:
            report.update(decision='HOLD', reason=str(error))
        # Includes every premise used for authorization, not the inspection time.
        report['planId'] = digest({k:v for k,v in report.items() if k != 'observedAt'})
        return report

    def _case(self, plan_id):
        require(isinstance(plan_id, str) and len(plan_id) == 64
                and all(c in '0123456789abcdef' for c in plan_id), 'INVALID_PLAN_ID')
        return self.cases/plan_id

    def apply(self, plan_id):
        from paid_archive import ensure_live
        ensure_live(self.directory)
        with StorageReceipt(self.directory, {'action':'recovery_apply', 'planId':plan_id}):
            case = self._case(plan_id)
            journal_path = case/'journal.json'
            if journal_path.exists():
                journal = read_json(journal_path)
                if journal['phase'] == 'DONE':
                    return dict(journal['result'], replay=True)
                if journal['phase'] == 'INSTALL_READY':
                    return self._install(case, journal)
            plan = self._inspect()
            if plan['planId'] != plan_id:
                return dict(decision='HOLD', reason='STALE_RECOVERY_PLAN', currentPlan=plan)
            case.mkdir(parents=True, exist_ok=True)
            if plan['decision'] == 'HOLD':
                write_atomic(case/'hold.json', plan)
                return plan
            # These snapshots preserve the original state. Subsequent normal
            # commands remain fenced by the original pending record.
            if not (case/'before').exists():
                (case/'before').mkdir()
                for name in ('projection.sqlite','mock-provider.sqlite'):
                    copy_database(self.directory/name, case/'before'/name)
            journal = dict(format='kix-local-recovery-journal-v1', phase='INTENT', plan=plan,
                           pending=read_json(self.pending), previousReceipt=read_json(self.receipt))
            write_atomic(journal_path, journal)
            # Requery AFTER durable intent and immediately before any submission.
            fresh = self._inspect()
            if fresh['planId'] != plan_id:
                return dict(decision='HOLD', reason='STALE_RECOVERY_PLAN', currentPlan=fresh)
            if plan['decision'] == 'REPLAY_SAME_REQUEST':
                provider = MockProvider(str(self.directory/'mock-provider.sqlite'))
                try:
                    provider.submit(plan['idempotencyKey'], json.loads(plan['requestBytes']))
                finally:
                    provider.db.close()
            # A crash above leaves INTENT + the original pending record. Next
            # inspection observes the provider, never an injected crash label.
            observed = self._inspect()
            if observed['decision'] != 'LINK_EXISTING':
                write_atomic(case/'hold-after-call.json', observed)
                return observed
            return self._prepare_install(case, journal, observed)

    def _prepare_install(self, case, journal, observed):
        candidate = case/'candidate'
        # An incomplete private candidate is never adopted as the original.
        if candidate.exists():
            shutil.rmtree(candidate)
        candidate.mkdir()
        for name in ('projection.sqlite','mock-provider.sqlite'):
            copy_database(self.directory/name, candidate/name)
        require(directory_fingerprint(candidate) == observed['databases'], 'SNAPSHOT_CHANGED_REPLAN')
        c = PaidCoordinator(candidate)
        try:
            c._evidence(observed['chain'])
            if not observed['chain']['showOpen']:
                c._run('recovery-cancel-'+observed['tradeId'], 'operator', 'cancel_event',
                       eventId=observed['binding']['showId'])
            # All accounting changes happen on the copy. A killed process here
            # leaves the live projection and its reservations unchanged.
            c.sync_effect(observed['effectId'])
            audit = dict(planId=journal['plan']['planId'], decision=journal['plan']['decision'],
                         originalRequest=observed['originalRequest'], providerResult=observed['providerResult'],
                         chain=observed['chain'], evidenceHash=observed['planId'])
            c._save('recovery-'+journal['plan']['planId'], audit)
            s = c.core.snapshot()
            result = dict(decision='RECOVERED', recoveryId=journal['plan']['planId'],
                          authorization=journal['plan']['decision'], originalRequest=observed['originalRequest'],
                          providerResult=observed['providerResult'], chain=observed['chain'],
                          effect=s['effects'][observed['effectId']], trade=s['trades'][observed['tradeId']],
                          balances=s['balances'], journalEntries=len(s['journal']),
                          remainingDuties=dict(payout=x_remaining(s, observed['effectId']),
                            customerRefund=max(0,s['trades'][observed['tradeId']]['refundDue']-s['trades'][observed['tradeId']]['refunded']),
                            recoveryReceivables={k:v for k,v in s['balances'].items() if k.startswith('recoverable:') and v}),
                          remainingDuty='PENDING_PROVIDER_RESULT' if s['effects'][observed['effectId']]['state'] != 'DONE' else 'NONE_FOR_THIS_PAYOUT')
        finally:
            c.close()
        copy_database(candidate/'projection.sqlite', case/'install.sqlite')
        with closing(readonly(case/'install.sqlite')) as db:
            candidate_hash = connection_fingerprint(db)
        # Recheck both external premises and the live ledger before authorizing
        # installation. A late payout/cancellation requires a fresh plan.
        fresh = self._inspect()
        if fresh['planId'] != observed['planId']:
            write_atomic(case/'stale-before-install.json', fresh)
            return dict(decision='HOLD', reason='STALE_RECOVERY_PLAN', currentPlan=fresh)
        journal.update(phase='INSTALL_READY', observed=observed, candidateHash=candidate_hash,
                       beforeHash=observed['databases']['projection.sqlite'], result=result)
        write_atomic(case/'journal.json', journal)
        return self._install(case, journal)

    def _install(self, case, journal):
        live = self.directory/'projection.sqlite'
        with closing(readonly(live)) as db:
            current = connection_fingerprint(db)
            row = db.execute('SELECT body FROM integration_items WHERE id=?',
                             ('recovery-'+journal['plan']['planId'],)).fetchone()
        if not self.pending.exists():
            # Death after pending removal (or a later normal command): recognize
            # the recorded recovery; never overwrite a subsequent receipt.
            require(row is not None and json.loads(row[0])['planId'] == journal['plan']['planId'],
                    'RECOVERY_PENDING_MISSING_WITHOUT_COMMIT')
            return self._done(case, journal)
        require(read_json(self.pending) == journal['pending'], 'RECOVERY_PENDING_CHANGED')
        if current == journal['beforeHash']:
            fresh = self._inspect()
            if fresh['planId'] != journal['observed']['planId']:
                # Nothing installed: allow a new evidence-bound plan. Keep the
                # old journal/snapshots as evidence instead of clearing pending.
                return dict(decision='HOLD', reason='STALE_RECOVERY_PLAN', currentPlan=fresh)
            with closing(readonly(case/'install.sqlite')) as db:
                require(connection_fingerprint(db) == journal['candidateHash'], 'RECOVERY_CANDIDATE_CHANGED')
            # Let SQLite checkpoint its own committed WAL under the exclusive
            # command lock. Never unlink a live WAL to make replacement work.
            with closing(sqlite3.connect(live, isolation_level=None)) as db:
                require(connection_fingerprint(db) == journal['beforeHash'], 'RECOVERY_CHECKPOINT_STATE_CHANGED')
                db.execute('PRAGMA synchronous=FULL')
                require(db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0] == 0,
                        'RECOVERY_CHECKPOINT_BUSY')
                require(connection_fingerprint(db) == journal['beforeHash'], 'RECOVERY_CHECKPOINT_STATE_CHANGED')
            # All readers/writers must obey the local command lock. Refuse a
            # remaining WAL instead of removing an unexamined journal.
            for suffix in ('-wal','-journal'):
                path = Path(str(live)+suffix)
                require(not path.exists() or path.stat().st_size == 0, 'RECOVERY_LIVE_JOURNAL_PRESENT')
            os.replace(case/'install.sqlite', live)
            sync_directory(self.directory)
        else:
            require(current == journal['candidateHash'], 'RECOVERY_INSTALL_STATE_CONFLICT')
        return self._acknowledge(case, journal)

    def _acknowledge(self, case, journal):
        databases = directory_fingerprint(self.directory)
        require(databases['projection.sqlite'] == journal['candidateHash'], 'RECOVERY_INSTALLED_STATE_CHANGED')
        receipt = dict(format='kix-local-storage-receipt-v1', sequence=journal['previousReceipt']['sequence']+1,
                       requestHash=journal['pending']['requestHash'], databases=databases,
                       recoveryId=journal['plan']['planId'], evidenceHash=journal['observed']['planId'])
        existing = read_json(self.receipt)
        require(existing == journal['previousReceipt'] or existing.get('recoveryId') == receipt['recoveryId'],
                'RECOVERY_RECEIPT_CHANGED')
        # Installation already committed. Later external changes are not new
        # submission authority; normal reconciliation must observe them.
        write_atomic(self.receipt, receipt)
        self.pending.unlink()
        sync_directory(self.directory)
        return self._done(case, journal)

    def _done(self, case, journal):
        from paid_archive import Archive
        archive = Archive.for_source(self.directory)
        if archive:
            archive.publish('RECOVERY_ACK')
        journal['phase'] = 'DONE'
        write_atomic(case/'journal.json', journal)
        return journal['result']


def x_remaining(state, eid):
    x = state['effects'][eid]
    return x['amount']-x['appliedAmount']
