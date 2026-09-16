#!/usr/bin/env python3
"""Reproducible calculation evidence, never PG or chain execution evidence."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'reference/v0.3-rc1'))
from assets import Amount, AssetSpec, KRW, MAX_ATOMS
from commerce_driver import dispatch
from commerce import SCHEMA
from common import Rejected, canonical


def run():
    request = dict(schemaVersion=SCHEMA,orderId='bundle-three',orderVersion=1,
                   scope=dict(issuerId='fixture-issuer',eventId='fixture-show',performanceId='evening'),
                   policyRef='frozen-line-price-v1',expiresAt=1000,
                   lines=[dict(lineId=f'L{i}',inventoryId=f'inv-{i}',gross=Amount(KRW,price).to_dict())
                          for i,price in enumerate((10000,20000,30000),1)],
                   discounts=[dict(ruleId='coupon',bearerRef='organizer',kind='FIXED',value='6000',
                                   eligibleLineIds=['L1','L2','L3'],capAtoms=None),
                              dict(ruleId='member',bearerRef='platform',kind='BPS',value='1000',
                                   eligibleLineIds=['L1','L2','L3'],capAtoms=None)])
    quote=dispatch(dict(action='simulate_quote',args=request))['result']
    legs=[dict(legId=name,providerRef='mock-pg',routeRef='original-'+name,amount=Amount(KRW,value).to_dict())
          for name,value in [('card',30000),('bank',18600)]]
    plan=dispatch(dict(action='plan_payments',args=dict(quote=quote,legs=legs,
                   expected_quote_hash=quote['quoteHash'],now=999)))['result']
    refund=dispatch(dict(action='propose_line_refund',args=dict(quote=quote,payment_plan=plan,
                     line_ids=['L2'],expected_plan_hash=plan['planHash'])))['result']
    assert quote['totals']['payableAtoms']=='48600'
    assert refund['customerRefund']['atoms']=='16200'
    assert [row['amount']['atoms'] for row in refund['originalRoutes']]==['10000','6200']
    rejected=[]
    for action in ('send_effect','execute_refund','sign_transaction'):
        try: dispatch(dict(action=action,args={}))
        except Rejected as error: rejected.append(dict(action=action,reason=str(error)))
        else: raise AssertionError('execution action allowed')
    precision=[]
    for decimals in (0,2,6,18):
        asset=AssetSpec('fixture-asset',f'local:precision-{decimals}',decimals,MAX_ATOMS)
        value=Amount(asset,9007199254740993)
        assert Amount.from_dict(value.to_dict())==value
        assert Amount.from_decimal(asset,value.decimal_string())==value
        precision.append(dict(amount=value.to_dict(),decimal=value.decimal_string()))
    return dict(format='kix-commerce-validation-v1',evidenceClass='CALCULATION_ONLY',
                quote=quote,paymentPlan=plan,lineReversalProposal=refund,
                precisionRoundTrips=precision,rejectedExecutionActions=rejected,
                actualPGCalls=0,actualChainCalls=0,ledgerMutations=0,
                limitations=['No money was captured or refunded.',
                             'No issuance or cancellation was attempted.',
                             'No LLM was invoked and no autonomous execution authority was issued.',
                             'Calculated discount reversals are not confirmed sponsor receivables.'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',required=True)
    args=parser.parse_args();result=run();target=Path(args.report)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(canonical(dict(result='PASS',evidenceClass=result['evidenceClass'],report=str(target),
                         payable='48600',selectedLineRefund='16200',externalCalls=0)))


if __name__=='__main__': main()
