from common import inventory_id
"""Offline reproducible verification, bounded mutations, and acceptance traces."""
from pathlib import Path
import hashlib
import io
import json
import platform
import sqlite3
import sys
import unittest
import cryptography

from core import Core
from test_core import Harness
from contracts import schema
from mutation_check import run as run_mutations

ROOT=Path(__file__).resolve().parent
RESULTS=ROOT/'results'


def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n')


def traces():
    cases={}
    h=Harness(); h.event(); h.purchase(); h.run('complete_event',eventId='show')
    h.run('prepare_effect',effectId='p',tradeId='primary',kind='PAYOUT',amount=95000,allocationId='primary-0')
    h.run('cancel_event',eventId='show'); send=h.run('send_effect',effectId='p')['result']
    cases['cancel_before_first_send']=dict(dispatch=send,finance=h.c.view('finance-adapter','show','finance'))
    h.c.db.close()
    h=Harness(); h.event(); h.purchase(); h.run('complete_event',eventId='show')
    h.effect('p','primary','PAYOUT',95000,'primary-0'); h.run('cancel_event',eventId='show')
    cases['cancel_after_send_intent']=h.c.view('finance-adapter','show','finance'); h.c.db.close()
    h=Harness(); h.event(); h.purchase(settle=False); h.run('cancel_event',eventId='show')
    h.effect('r','primary','REFUND',100000,routeProfile='PG_ORIGINAL_CANCEL_FIXTURE'); h.observe('r','PG_CANCELLED')
    cases['pg_cancel_no_settlement']=dict(finance=h.c.view('finance-adapter','show','finance'),balances=h.c.snapshot()['balances'])
    h.source('adjust_pg_cancel',tradeId='primary',paymentId='pay-primary',amount=100000,currency='KRW',contractRef='fixture:pg-cancel:v1',basis='RECEIVABLE_NETTING',movementId='pg-adjust')
    h.observe('r','CUSTOMER_CREDIT_CONFIRMED')
    cases['pg_cancel_adjusted']=dict(finance=h.c.view('finance-adapter','show','finance'),balances=h.c.snapshot()['balances']); h.c.db.close()
    h=Harness(); h.event(); h.purchase(); old=h.right(); h.run('refund_ticket','A',ticketId=old,expectedVersion=1); h.refund_all()
    h.run('release_inventory',inventoryId=inventory_id('organizer','show','main','A1'),closedRightId=old,expectedInventoryVersion=1); h.purchase('new-sale',buyer='B')
    s=h.c.snapshot(); cases['seat_reissued']=dict(inventory=s['inventory'],rights=s['tickets'],oldRight=old,newRight=h.right())
    export=h.c.export_replay(); rebuilt=Core.rebuild_fixture(export)
    cases['local_rebuild']=dict(sameState=rebuilt.snapshot()==s,authenticity=export['authenticity'],chainFinalityVerified=False)
    rebuilt.db.close(); h.c.db.close()
    return dict(domain=Core.DOMAIN,evidence='synthetic reference execution only',cases=cases)


def main():
    RESULTS.mkdir(exist_ok=True)
    stream=io.StringIO(); suite=unittest.defaultTestLoader.discover(str(ROOT),pattern='test*.py')
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (RESULTS/'tests.txt').write_text(stream.getvalue())
    if not tests.wasSuccessful(): print(stream.getvalue()); return 1
    mutations=run_mutations(RESULTS)
    if not mutations['allDetected']: print('A bounded mutation survived; inspect results/mutation_results.json'); return 1
    dump(RESULTS/'acceptance_trace.json',traces())
    dump(ROOT/'protocol_contract.json',schema())
    verification=dict(version='0.3-rc1',domain=Core.DOMAIN,testsRun=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors),
        testsPassed=tests.wasSuccessful(),selectedMutations=len(mutations['results']),selectedMutationsDetected=sum(x['detected'] for x in mutations['results']),
        python=platform.python_version(),sqlite=sqlite3.sqlite_version,cryptography=cryptography.__version__,
        externalNetworkCalls=0,realMoneyMoved=False,suiSourceIncluded=True,suiBuildVerified=False,suiJourneyExecuted=False,zeroKnowledgeSourceIncluded=True,zeroKnowledgeProofGenerated=False,overallStatus='REFERENCE_VERIFIED_CHAIN_EXECUTION_BLOCKED',
        canonicalRightsAuthority='local SQLite reference model',recoveryClass='unsigned local command/evidence export',
        retainedV01Cases=31,newBehavioralCases=tests.testsRun-31)
    dump(RESULTS/'verification.json',verification)
    files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*'))
           if p.is_file() and '__pycache__' not in p.parts and p.name!='manifest.sha256.json' and p.suffix not in ('.db','.pyc')}
    dump(RESULTS/'manifest.sha256.json',files)
    print(json.dumps(verification,ensure_ascii=False,sort_keys=True))
    return 0


if __name__=='__main__': sys.exit(main())
