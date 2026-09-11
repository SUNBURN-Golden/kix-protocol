"""Observed after-fix behavior; synthetic execution, not independent validation."""
import json
from common import Rejected,inventory_id
from test_v03 import V03Regressions
from test_core import Harness
from core import Core

def attempt(fn):
 try:return {'accepted':True,'result':fn()}
 except Rejected as e:return {'accepted':False,'error':str(e)}
def run():
 rows={}
 h=Harness();h.event();h.prepare();t=V03Regressions();t.h=h
 before=h.c.ingest('early',t.statement(),fixture_authenticated=True);h.capture(settle=False)
 after=h.c.apply_observation('early',fixture_authenticated=True)
 rows['R01']={'before':before['state'],'after':after['state'],'settled':h.c.snapshot()['trades']['primary']['settled'],'unposted':h.c.inbox_summary('show')['observedMovementAmountUnderReview']};h.c.db.close()
 for phases in [('CUSTOMER_CREDIT_CONFIRMED','FENCED_FAILURE'),('FENCED_FAILURE','CUSTOMER_CREDIT_CONFIRMED')]:
  h=Harness();t.h=h;t.refund()
  for phase in phases:h.observe('pg',phase,**({'fenceRef':'final','fenceProvenance':'synthetic_final_provider_fence'} if phase=='FENCED_FAILURE' else {}))
  rows['R02' if phases[0].startswith('CUSTOMER') else 'R07']={'order':phases,'effectState':h.c.snapshot()['effects']['pg']['state'],'replacement':attempt(lambda:h.effect('cash','primary','REFUND',100000))}
  h.c.db.close()
 h=Harness();t.h=h;t.partial();h.run('cancel_event',eventId='show');t.final()
 rows['R03']={'state':h.c.snapshot()['effects']['p']['state'],'applied':40000,'unexecutedFinal':h.c.snapshot()['effects']['p']['unexecutedFinalAmount'],'finance':h.c.view('finance-adapter','show','finance')}
 h.source('observe_return',effectId='p',paymentId='pay-primary',payer='organizer',amount=40000,currency='KRW',movementId='return')
 rows['R04']={'returned':h.c.snapshot()['effects']['p']['returned'],'recoveryOutstanding':h.c.view('finance-adapter','show','finance')['organizerRecoveryOutstanding']};h.c.db.close()
 h=Harness();h.event();h.purchase();h.run('complete_event',eventId='show');h.run('prepare_effect',effectId='p',tradeId='primary',kind='PAYOUT',amount=95000,allocationId='primary-0')
 try:h.c.execute('lost','operator','send_effect',dict(domain=Core.DOMAIN,effectId='p'),lose_response=True)
 except ConnectionError:pass
 claim=h.run('claim_effect',effectId='p',workerId='w',leaseSeconds=30)['result']
 out=h.run('dispatch_effect',effectId='p',workerId='w',claimGeneration=claim['claimGeneration'])['result']
 rows['R05']={'dispatch':out['dispatchDecision'],'requestHash':out['requestHash'],'sameDurableKey':out['idempotencyKey']==h.c.snapshot()['effects']['p']['idempotencyKey'],'realExternalSends':0};h.c.db.close()
 h=Harness();h.event();h.c.ingest('same',b'one');before=h.c.inbox_summary('show');attempt(lambda:h.c.ingest('same',b'two'));after=h.c.inbox_summary('show')
 rows['R06']={'before':before['evidenceDigest'],'after':after['evidenceDigest'],'rawConflictCount':after['globalRawConflictCount']};h.c.db.close()
 h=Harness();h.event();h.purchase();listing=h.run('create_listing','A',listingId='L',ticketId=h.right(),expectedVersion=1,amount=120000,expiresAt=86400)['result']
 rows['R08']=attempt(lambda:h.run('reserve_listing','B',listingId='L',listingHash=listing['termsHash'],tradeId='reserve',expiresAt=86400));h.c.db.close()
 h=Harness();h.event('a',['b/c']);h.event('a/b',['c']);rows['R09']={'inventoryCount':len(h.c.snapshot()['inventory']),'inventoryIds':sorted(h.c.snapshot()['inventory'])};h.c.db.close()
 return {'domain':Core.DOMAIN,'evidenceClass':'SYNTHETIC_REFERENCE_EXECUTION','results':rows}
if __name__=='__main__':
 from pathlib import Path
 Path('results/review_trace_v03.json').write_text(json.dumps(run(),sort_keys=True,ensure_ascii=False,indent=2)+'\n')
