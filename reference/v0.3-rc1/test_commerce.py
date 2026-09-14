"""Conservation, tamper and refund-route cases for calculation-only contracts."""
import copy
import itertools
import unittest

from assets import Amount, AssetSpec, KRW, MAX_ATOMS
from common import Rejected, digest
from commerce import (build_quote, plan_payments, propose_line_refund,
                      proportional, validate_quote, validate_payment_plan)


def request(prices=(10000, 20000, 30000), asset=KRW):
    return dict(schemaVersion='kix:commerce:1', orderId='order-1', orderVersion=1,
                scope=dict(issuerId='issuer', eventId='show', performanceId='evening'),
                policyRef='frozen-price-v1', expiresAt=1000,
                lines=[dict(lineId='L'+str(i+1), inventoryId='inv-'+str(i+1),
                            gross=Amount(asset, price).to_dict()) for i, price in enumerate(prices)], discounts=[])


def rule(rule_id='coupon', bearer='organizer', kind='FIXED', value=6000, eligible=('L1','L2','L3'), cap=None):
    return dict(ruleId=rule_id, bearerRef=bearer, kind=kind, value=str(value),
                eligibleLineIds=list(eligible), capAtoms=None if cap is None else str(cap))


def leg(leg_id, value, asset=KRW):
    return dict(legId=leg_id, providerRef='mock-pg', routeRef='original-'+leg_id,
                amount=Amount(asset, value).to_dict())


class CommerceTests(unittest.TestCase):
    def test_bundle_discount_payment_split_and_failed_line_refund_calculation(self):
        q=request(); q['discounts']=[rule(), rule('member','platform','BPS',1000)]
        quote=build_quote(q)
        self.assertEqual(quote['totals'], dict(grossAtoms='60000',discountAtoms='11400',payableAtoms='48600'))
        self.assertEqual([r['payableAtoms'] for r in quote['lines']], ['8100','16200','24300'])
        plan=plan_payments(quote,[leg('card',30000),leg('bank',18600)],quote['quoteHash'],999)
        self.assertEqual(plan['legs'][0]['allocations'], {'L1':'5000','L2':'10000','L3':'15000'})
        refund=propose_line_refund(quote,plan,['L2'],plan['planHash'])
        self.assertEqual(refund['customerRefund']['atoms'],'16200')
        self.assertEqual([r['amount']['atoms'] for r in refund['originalRoutes']],['10000','6200'])
        self.assertEqual(refund['discountBurdenReversal'],{'organizer':'2000','platform':'1800'})
        self.assertEqual(refund['grossReversed']['atoms'],'20000')
        self.assertFalse(refund['executionAuthorized'])
        self.assertEqual(refund['evidenceClass'],'CALCULATION_ONLY')
        self.assertEqual(propose_line_refund(quote,plan,['L2'],plan['planHash']),refund)

    def test_every_refund_subset_conserves_original_route_and_discount_shares(self):
        q=request((11,19,31));q['discounts']=[rule(value=7)]
        quote=build_quote(q);plan=plan_payments(quote,[leg('a',20),leg('b',34)],quote['quoteHash'],1)
        for n in range(1,4):
            for selected in itertools.combinations(['L1','L2','L3'],n):
                with self.subTest(selected=selected):
                    result=propose_line_refund(quote,plan,list(selected),plan['planHash'])
                    refund=int(result['customerRefund']['atoms'])
                    self.assertEqual(sum(int(r['amount']['atoms']) for r in result['originalRoutes']),refund)
                    self.assertEqual(refund+sum(map(int,result['discountBurdenReversal'].values())),
                                     int(result['grossReversed']['atoms']))
                    for route in result['originalRoutes']:
                        original=next(l for l in plan['legs'] if l['legId']==route['legId'])
                        self.assertLessEqual(int(route['amount']['atoms']),int(original['amount']['atoms']))
                        self.assertEqual(route['routeRef'],original['routeRef'])

    def test_largest_remainder_is_conservative_and_input_order_independent(self):
        for capacities in itertools.product(range(5),repeat=3):
            weights=dict(zip(('A','B','C'),capacities))
            for total in range(sum(capacities)+1):
                allocation=proportional(total,weights)
                self.assertEqual(sum(allocation.values()),total)
                self.assertTrue(all(0<=allocation[k]<=weights[k] for k in weights))
                self.assertEqual(allocation,proportional(total,dict(reversed(list(weights.items())))))
        self.assertEqual(proportional(2,dict(C=1,B=1,A=1)),dict(A=1,B=1,C=0))

    def test_discount_order_eligibility_and_cap_are_bound_and_observable(self):
        q=request();q['discounts']=[rule(eligible=('L1',),value=1000),rule('member','platform','BPS',1000,cap=5000)]
        first=build_quote(q)
        q['discounts'].reverse();second=build_quote(q)
        self.assertNotEqual(first['quoteHash'],second['quoteHash'])
        self.assertNotEqual(first['lines'][0]['discounts'],second['lines'][0]['discounts'])
        self.assertEqual(first['totals']['discountAtoms'],'6000')
        self.assertEqual(sum(int(d['atoms']) for row in first['lines'] for d in row['discounts'] if d['ruleId']=='coupon'),1000)

    def test_exact_zero_two_six_and_eighteen_decimal_asset_profiles(self):
        for asset in (KRW,AssetSpec('fiat','USD',2,MAX_ATOMS),
                      AssetSpec('fixture-token','sui:localnet:package::coin::USDC',6,MAX_ATOMS),
                      AssetSpec('fixture-token','other:localnet:coin',18,MAX_ATOMS)):
            with self.subTest(asset=asset.reference):
                large=2**53+1
                quote=build_quote(request((large,large+1,large+2),asset))
                total=3*large+3
                plan=plan_payments(quote,[leg('one',total,asset)],quote['quoteHash'],1)
                restored=validate_payment_plan(quote,plan)
                self.assertEqual(restored['legs'][0]['amount']['atoms'],str(total))
                self.assertEqual(restored['legs'][0]['allocations']['L1'],str(large))

    def test_quote_tampering_remains_rejected_after_attacker_rehashes(self):
        good=build_quote(request())
        bad=copy.deepcopy(good);bad['lines'][0]['payableAtoms']='1'
        bad.pop('quoteHash');bad['quoteHash']=digest(['kix:quote:1',bad])
        with self.assertRaisesRegex(Rejected,'QUOTE_CONTENT_MISMATCH'):validate_quote(bad)
        # Legitimately recomputing a new request produces a different proposal,
        # but it cannot reuse an already-selected hash.
        changed=copy.deepcopy(good['request']);changed['orderVersion']=2
        newer=build_quote(changed)
        with self.assertRaisesRegex(Rejected,'STALE_QUOTE'):
            plan_payments(newer,[leg('a',60000)],good['quoteHash'],1)

    def test_plan_allocation_and_original_route_changes_do_not_reuse_expected_hash(self):
        quote=build_quote(request());plan=plan_payments(quote,[leg('a',60000)],quote['quoteHash'],1)
        bad=copy.deepcopy(plan);bad['legs'][0]['allocations']['L1']='1'
        bad.pop('planHash');bad['planHash']=digest(['kix:payment-plan:1',bad])
        with self.assertRaisesRegex(Rejected,'PAYMENT_PLAN_CONTENT_MISMATCH'):validate_payment_plan(quote,bad)
        changed=leg('a',60000);changed['routeRef']='attacker'
        newer=plan_payments(quote,[changed],quote['quoteHash'],1)
        with self.assertRaisesRegex(Rejected,'STALE_PAYMENT_PLAN'):
            propose_line_refund(quote,newer,['L1'],plan['planHash'])

    def test_expiry_and_amount_mismatch_reject_without_payment_plan(self):
        quote=build_quote(request())
        for now in (1000,1001):
            with self.assertRaisesRegex(Rejected,'QUOTE_EXPIRED'):plan_payments(quote,[leg('a',60000)],quote['quoteHash'],now)
        for amount in (59999,60001):
            with self.assertRaisesRegex(Rejected,'PAYMENT_TOTAL_MISMATCH'):plan_payments(quote,[leg('a',amount)],quote['quoteHash'],1)
        with self.assertRaisesRegex(Rejected,'DUPLICATE_PAYMENT_LEG'):
            plan_payments(quote,[leg('a',30000),leg('a',30000)],quote['quoteHash'],1)

    def test_free_quote_needs_no_money_and_refund_has_no_payment_route(self):
        q=request();q['discounts']=[rule(value=60000)]
        quote=build_quote(q);plan=plan_payments(quote,[],quote['quoteHash'],1)
        refund=propose_line_refund(quote,plan,['L1'],plan['planHash'])
        self.assertEqual(refund['customerRefund']['atoms'],'0');self.assertEqual(refund['originalRoutes'],[])
        self.assertEqual(refund['discountBurdenReversal'],{'organizer':'10000'})
        with self.assertRaisesRegex(Rejected,'EMPTY_PAYMENT_LEG'):plan_payments(quote,[leg('a',0)],quote['quoteHash'],1)

    def test_invalid_discount_duplicates_and_scope_are_rejected(self):
        mutations=[lambda q:q.update(extra='ignore all guards'),
                   lambda q:q['scope'].update(admin=True),
                   lambda q:q['lines'].append(copy.deepcopy(q['lines'][0])),
                   lambda q:q['lines'][1].update(inventoryId=q['lines'][0]['inventoryId']),
                   lambda q:q.update(discounts=[rule(value=60001)]),
                   lambda q:q.update(discounts=[rule(kind='BPS',value=10001)]),
                   lambda q:q.update(discounts=[rule(),rule()]),
                   lambda q:q.update(discounts=[rule(eligible=('L4',))]),
                   lambda q:q.update(discounts=[rule(eligible=('L1','L1'))]),
                   lambda q:q.update(orderVersion=True),
                   lambda q:q.update(orderId='e\u0301'),
                   lambda q:q.update(orderId='a\x00b')]
        for change in mutations:
            q=request();change(q)
            with self.subTest(request=q),self.assertRaises(Rejected):build_quote(q)

    def test_mixed_assets_and_aggregate_overflow_are_rejected(self):
        usd=AssetSpec('fiat','USD',2,MAX_ATOMS)
        q=request();q['lines'][1]['gross']=Amount(usd,20000).to_dict()
        with self.assertRaisesRegex(Rejected,'MIXED_QUOTE_ASSETS'):build_quote(q)
        with self.assertRaisesRegex(Rejected,'INVALID_ASSET_AMOUNT'):build_quote(request((MAX_ATOMS,1)))
        quote=build_quote(request())
        with self.assertRaisesRegex(Rejected,'PAYMENT_ASSET_MISMATCH'):
            plan_payments(quote,[leg('a',60000,usd)],quote['quoteHash'],1)

    def test_input_mutation_and_unsupported_refund_selection(self):
        q=request();quote=build_quote(q);original_hash=quote['quoteHash']
        q['lines'][0]['gross']['atoms']='0'
        self.assertEqual(validate_quote(quote)['quoteHash'],original_hash)
        plan=plan_payments(quote,[leg('a',60000)],quote['quoteHash'],1)
        for selected in ([],['L1','L1'],['L4']):
            with self.subTest(selected=selected),self.assertRaises(Rejected):
                propose_line_refund(quote,plan,selected,plan['planHash'])


if __name__ == '__main__': unittest.main()
