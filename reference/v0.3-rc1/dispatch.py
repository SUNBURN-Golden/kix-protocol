"""Durable dispatcher contract. Fixture claims/lookups; performs NO network I/O.

A lease fences coordinator grants, not a worker that already obtained a request.
Provider same-key replay guarantees are still required. One-hour replay window
and 30-second lookup freshness are explicit synthetic contract constants.
"""
from common import require, ident, digest, canonical
from finance import TERMINAL


class DispatchMixin:
    def _claim_effect(self,b):
        self.role('operator'); x=self.s['effects'][b['effectId']]; d=x['dispatch']
        require(x['sent'] and x['state'] not in TERMINAL and x['state']!='EVIDENCE_CONFLICT','EFFECT_NOT_CLAIMABLE')
        require(not d['worker'] or self.s['clock']>=d['leaseUntil'],'DISPATCH_ALREADY_CLAIMED')
        require(1<=b['leaseSeconds']<=60,'INVALID_CLAIM_LEASE')
        d['claimGeneration']+=1; d['worker']=ident(b['workerId']); d['leaseUntil']=self.s['clock']+b['leaseSeconds']
        return dict(effectId=b['effectId'],claimGeneration=d['claimGeneration'],leaseUntil=d['leaseUntil'],
                    idempotencyKey=x['idempotencyKey'],requestHash=x['requestHash'],
                    providerOperationId=x['providerOperationId'],attempts=d['attempts'])

    def _observe_dispatch_lookup(self,b):
        self.source(b); eid=b['effectId']; x=self.s['effects'][eid]; d=x['dispatch']
        require(b['idempotencyKey']==x['idempotencyKey'] and b['requestHash']==x['requestHash'],'LOOKUP_REQUEST_MISMATCH')
        require(x['sent'] and d['attempts']>0 and b['observedAt']<=self.s['clock']
                and b['observedAt']>=d['permits'][-1]['at'],'LOOKUP_TIME_MISMATCH')
        require(b['result'] in ('FOUND','NOT_FOUND_REPLAY_SAFE','UNKNOWN'),'LOOKUP_RESULT_UNSUPPORTED')
        if not self.evidence('dispatch-lookup',b['lookupRef'],b): return {'duplicate':True}
        if b['result']=='FOUND': self.bind_provider_operation(eid,x,b['providerOperationId'])
        d['lookup']=dict(result=b['result'],ref=b['lookupRef'],observedAt=b['observedAt'],attempt=d['attempts'],used=False)
        return {'lookupResult':b['result']}

    def _dispatch_effect(self,b):
        self.role('operator'); eid=b['effectId']; x=self.s['effects'][eid]; d=x['dispatch']; r=self.trade(x['trade'])
        require(d['worker']==b['workerId'] and d['claimGeneration']==b['claimGeneration']
                and self.s['clock']<d['leaseUntil'],'STALE_DISPATCH_CLAIM')
        require(x['sent'] and x['state'] not in TERMINAL,'DISPATCH_TERMINAL')
        require(not any(y['owed']==x['owed'] and y['state']=='EVIDENCE_CONFLICT' for y in self.s['effects'].values()),'OBLIGATION_EVIDENCE_CONFLICT')
        valid=x['kind']!='PAYOUT' or (self.event(r['event'])['status']=='COMPLETED'
                and not r['reversalRequested'] and x['allocationVersion']==r['allocationVersion'])
        require(valid and x['amount']-x['appliedAmount']<=-self.balance(x['owed']),'DISPATCH_OBLIGATION_CHANGED')
        require(x['requestBytes']==canonical(x['request']) and x['requestHash']==digest(x['request']),'DURABLE_REQUEST_CHANGED')
        require(self.s['clock']<d['idempotencyUntil'],'IDEMPOTENCY_WINDOW_EXPIRED_QUERY_ONLY')
        if d['attempts']:
            q=d['lookup']
            require(x['providerOperationId'] is None and q and q['result']=='NOT_FOUND_REPLAY_SAFE'
                    and not q['used'] and q['attempt']==d['attempts']
                    and 0<=self.s['clock']-q['observedAt']<=30,'SOURCE_LOOKUP_REQUIRED_QUERY_ONLY')
            q['used']=True
        d['attempts']+=1
        d['permits'].append(dict(operation=self.op,at=self.s['clock'],generation=d['claimGeneration']))
        return dict(effectId=eid,dispatchDecision='SUBMIT_SAME_REQUEST',idempotencyKey=x['idempotencyKey'],
                    requestBytes=x['requestBytes'],requestHash=x['requestHash'],attempt=d['attempts'],
                    contract='fixture:stable-key-replay:1h:v1')
