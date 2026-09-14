"""Exact typed bindings and real legacy command rejection/authority boundaries."""
import copy
from dataclasses import FrozenInstanceError
import itertools
import unittest

from assets import Amount, AssetSpec, KRW, MAX_ATOMS
from canonical_encoding import canonical_bytes, decode_json
from common import Rejected
from commerce import SCHEMA, build_quote, plan_payments, propose_line_refund
from core import Core
from execution_contracts import (
    AdmissionEpoch, AssetAmount, BasisPoints, DurationSeconds, Generation,
    LegacyKRWAdapter, Quantity, RegistryContext, Sequence, TimestampMs, Version,
    LEGACY_CORE_DOMAIN, LEGACY_KRW_LIMIT,
)


USDC = AssetSpec("fixture-token", "sui:localnet:package::coin::USDC", 6, MAX_ATOMS)
COUNTERS = (TimestampMs, Sequence, Version, Quantity, Generation,
            AdmissionEpoch, DurationSeconds, BasisPoints)


def registry(*assets, version=1, source="fixture:approved-assets:v1", domain=LEGACY_CORE_DOMAIN):
    return RegistryContext(Version(version), source, domain, assets or (KRW, USDC))


class TypedCounterTests(unittest.TestCase):
    def test_each_counter_has_exact_bounds_and_decimal_wire_roundtrip(self):
        for kind in COUNTERS:
            for n in (0, 1, kind.MAX):
                with self.subTest(kind=kind.__name__, n=n):
                    value = kind(n)
                    self.assertEqual(kind.from_wire(value.to_wire()), value)
                    self.assertEqual(value.to_wire(), str(n))
                    self.assertIs(type(value), kind)
            for n in (True, False, 1.0, -1, kind.MAX + 1, "1", None):
                with self.subTest(kind=kind.__name__, invalid=n), self.assertRaises(Rejected):
                    kind(n)
            for wire in (True, 1, 1.0, "01", "+1", "-0", "-1", "1.0", "1e3", " 1", "1\n", "\u0661", "", str(kind.MAX + 1)):
                with self.subTest(kind=kind.__name__, wire=wire), self.assertRaises(Rejected):
                    kind.from_wire(wire)

    def test_counter_contexts_are_runtime_distinct_and_cannot_be_money(self):
        ctx = registry()
        for first, second in itertools.permutations(COUNTERS, 2):
            with self.subTest(first=first.__name__, second=second.__name__):
                self.assertNotEqual(first(1), second(1))
                with self.assertRaises(Rejected):
                    first(second(1))
        for kind in COUNTERS:
            with self.subTest(kind=kind.__name__):
                with self.assertRaises(Rejected):
                    AssetAmount(KRW.asset_id, kind(1), ctx)
                with self.assertRaises(Rejected):
                    Amount(KRW, kind(1))
                with self.assertRaises(TypeError):
                    int(kind(1))
                with self.assertRaises(TypeError):
                    kind(1) + kind(1)
        self.assertEqual(TimestampMs.MAX, 2**63 - 1)
        self.assertEqual(Sequence.MAX, 2**64 - 1)
        self.assertEqual(Version.MAX, 2**32 - 1)
        self.assertEqual(Quantity.MAX, 2**32 - 1)
        self.assertEqual(BasisPoints.MAX, 10000)

    def test_registry_version_requires_its_own_type_and_a_positive_revision(self):
        for bad in (1, True, "1", Sequence(1), Generation(1), Version(0)):
            with self.subTest(bad=bad), self.assertRaisesRegex(Rejected, "INVALID_ASSET_REGISTRY_VERSION"):
                RegistryContext(bad, "fixture:assets", LEGACY_CORE_DOMAIN, (KRW,))


class AssetBindingTests(unittest.TestCase):
    def test_u128_compact_and_full_record_roundtrip_preserve_exact_identity(self):
        ctx = registry()
        for n in (0, 1, 2**53 + 1, 2**64 + 1, MAX_ATOMS):
            with self.subTest(n=n):
                amount = AssetAmount.from_amount(Amount(USDC, n), registry=ctx)
                wire = decode_json(canonical_bytes(amount.to_dict()))
                self.assertEqual(wire, dict(assetId=USDC.asset_id, atoms=str(n)))
                self.assertEqual(AssetAmount.from_dict(wire, registry=ctx), amount)
                record = decode_json(canonical_bytes(amount.to_record()))
                self.assertEqual(record["asset"], USDC.to_dict())
                self.assertEqual(record["assetRegistryVersion"], "1")
                self.assertEqual(record["source"], ctx.source)
                self.assertEqual(record["domain"], ctx.domain)
                self.assertEqual(record["registryHash"], ctx.registry_hash)
                self.assertEqual(AssetAmount.from_record(record, registry=ctx), amount)
                with self.assertRaises(TypeError):
                    int(amount)

    def test_amount_and_context_are_immutable_and_exports_have_no_aliases(self):
        ctx = registry()
        amount = AssetAmount(KRW.asset_id, 7, ctx)
        for obj, field, value in ((amount, "atoms", 9), (ctx, "source", "attacker"),
                                  (ctx, "asset_registry_version", Version(2)),
                                  (ctx, "approved_assets", (USDC,))):
            with self.subTest(field=field), self.assertRaises((FrozenInstanceError, AttributeError)):
                setattr(obj, field, value)
        record = amount.to_record()
        record["asset"]["decimals"] = 6
        record["amount"]["atoms"] = "999"
        exported = ctx.to_dict()
        exported["assets"].clear()
        self.assertEqual(amount.atoms, 7)
        self.assertEqual(amount.asset, KRW)
        self.assertEqual(len(ctx.approved_assets), 2)
        self.assertEqual(registry(USDC, KRW), ctx)

    def test_wire_rejects_noncanonical_numbers_unknown_fields_and_counter_values(self):
        ctx = registry()
        for bad in (True, False, 1, 1.0, -1, "-1", "01", "-0", "1.0", "1e6", "+1", " 1", "1\n", "\u0661", "", str(MAX_ATOMS + 1), Sequence(1)):
            with self.subTest(bad=bad), self.assertRaises(Rejected):
                AssetAmount.from_dict(dict(assetId=USDC.asset_id, atoms=bad), registry=ctx)
        for bad in (dict(asset=USDC.to_dict(), atoms="1"),
                    dict(assetId=USDC.asset_id, atoms="1", currency="KRW"),
                    dict(assetId=USDC.asset_id),
                    dict(assetId=USDC.asset_id, atoms="1", executionAuthorized=True)):
            with self.subTest(bad=bad), self.assertRaises(Rejected):
                AssetAmount.from_dict(bad, registry=ctx)
        for n in (True, 1.0, -1, MAX_ATOMS + 1):
            with self.subTest(n=n), self.assertRaises(Rejected):
                AssetAmount(USDC.asset_id, n, ctx)

    def test_missing_or_unapproved_context_never_self_authorizes(self):
        for missing in (None, {}, {"assets": [USDC.to_dict()]}, USDC):
            with self.subTest(missing=missing), self.assertRaisesRegex(Rejected, "REGISTRY_CONTEXT_REQUIRED"):
                AssetAmount.from_dict(dict(assetId=USDC.asset_id, atoms="1"), registry=missing)
        with self.assertRaisesRegex(Rejected, "ASSET_NOT_APPROVED_IN_CONTEXT"):
            AssetAmount.from_amount(Amount(USDC, 1), registry=registry(KRW))
        with self.assertRaisesRegex(Rejected, "APPROVED_ASSET_CONFIG_REQUIRED"):
            RegistryContext(Version(1), "fixture:assets", LEGACY_CORE_DOMAIN, [KRW])
        with self.assertRaisesRegex(Rejected, "APPROVED_ASSET_CONFIG_REQUIRED"):
            RegistryContext(Version(1), "fixture:assets", LEGACY_CORE_DOMAIN, ())

    def test_full_record_rejects_version_source_domain_and_spec_rebinding(self):
        ctx = registry()
        amount = AssetAmount(USDC.asset_id, 10**6, ctx)
        record = amount.to_record()
        for changed in (registry(version=2), registry(source="fixture:other"),
                        registry(domain="kix:other:1")):
            with self.subTest(changed=changed), self.assertRaises(Rejected):
                AssetAmount.from_record(record, registry=changed)
        mutations = (
            lambda r: r.update(assetRegistryVersion="2"),
            lambda r: r.update(source="fixture:other"),
            lambda r: r.update(domain="kix:other:1"),
            lambda r: r["asset"].update(decimals=5),
            lambda r: r["asset"].update(maxAtoms=str(MAX_ATOMS - 1)),
            lambda r: r["asset"].update(reference="sui:mainnet:package::coin::USDC"),
            lambda r: r["asset"].update(namespace="another-token"),
            lambda r: r["amount"].update(assetId=KRW.asset_id),
            lambda r: r.update(executionAuthorized=True),
        )
        for mutate in mutations:
            bad = copy.deepcopy(record)
            mutate(bad)
            with self.subTest(bad=bad), self.assertRaises(Rejected):
                AssetAmount.from_record(bad, registry=ctx)

    def test_metadata_conflict_limits_and_machine_contexts_are_rejected(self):
        altered = AssetSpec(USDC.namespace, USDC.reference, 5, MAX_ATOMS)
        with self.assertRaisesRegex(Rejected, "APPROVED_ASSET_METADATA_CONFLICT"):
            registry(USDC, altered)
        with self.assertRaisesRegex(Rejected, "DUPLICATE_APPROVED_ASSET"):
            registry(KRW, KRW)
        limited = AssetSpec("fixture-token", "fixture:limited", 2, 100)
        with self.assertRaisesRegex(Rejected, "INVALID_ASSET_AMOUNT"):
            AssetAmount(limited.asset_id, 101, registry(limited))
        for bad in ("", "registry with space", "\u00e9", "a\x00b"):
            with self.subTest(bad=bad), self.assertRaises(Rejected):
                registry(source=bad)

    def test_record_pins_entire_approved_set_even_when_selected_asset_and_header_match(self):
        ctx = registry(KRW, USDC)
        amount = AssetAmount(KRW.asset_id, 1, ctx)
        record = amount.to_record()
        extra = AssetSpec("fiat", "USD", 2, MAX_ATOMS)
        altered = AssetSpec(USDC.namespace, USDC.reference, USDC.decimals, MAX_ATOMS - 1)
        for changed in (registry(KRW, USDC, extra), registry(KRW), registry(KRW, altered)):
            with self.subTest(changed=changed), self.assertRaisesRegex(Rejected, "ASSET_REGISTRY_CONFIG_MISMATCH"):
                AssetAmount.from_record(record, registry=changed)
            with self.subTest(adapter_context=changed), self.assertRaisesRegex(Rejected, "LEGACY_REGISTRY_CONTEXT_MISMATCH"):
                LegacyKRWAdapter(ctx, enabled=True).to_legacy_krw(AssetAmount(KRW.asset_id, 1, changed))
            self.assertNotEqual(changed.registry_hash, ctx.registry_hash)
        reordered = registry(USDC, KRW)
        self.assertEqual(reordered.registry_hash, ctx.registry_hash)
        self.assertEqual(AssetAmount.from_record(record, registry=reordered), amount)
        bad = copy.deepcopy(record)
        bad["registryHash"] = registry(KRW).registry_hash
        with self.assertRaisesRegex(Rejected, "ASSET_REGISTRY_CONFIG_MISMATCH"):
            AssetAmount.from_record(bad, registry=ctx)
        del bad["registryHash"]
        with self.assertRaisesRegex(Rejected, "INVALID_EXECUTION_AMOUNT_RECORD"):
            AssetAmount.from_record(bad, registry=ctx)


class LegacyBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.ctx = registry()
        self.adapter = LegacyKRWAdapter(self.ctx, enabled=True)
        self.core = Core()
        self.addCleanup(self.core.db.close)
        policy = dict(primaryPrice=1000000, resaleCap=1500000, primaryFeeBps=500,
                      resaleFeeBps=300, resaleOrganizerBps=200, resaleAllowed=True,
                      refundProfile="FULL_CHAIN_UNWIND_FIXTURE")
        event = self.core.execute("create-event", "operator", "create_event", dict(
            domain=Core.DOMAIN, eventId="show", organizer="organizer", policy=policy, seats=["A1"]))
        self.inventory_id = event["result"]["inventoryIds"][0]

    def prepare_body(self, amount):
        return dict(domain=Core.DOMAIN, tradeId="trade", buyer="buyer", amount=amount,
                    expectedVersion=0, inventoryId=self.inventory_id, expectedInventoryVersion=0)

    def test_adapter_requires_explicit_opt_in_exact_approved_spec_and_domain(self):
        for enabled in (False, None, 1, "true"):
            with self.subTest(enabled=enabled), self.assertRaisesRegex(Rejected, "REQUIRES_OPT_IN"):
                LegacyKRWAdapter(self.ctx, enabled=enabled)
        for missing in (None, {}, KRW):
            with self.subTest(missing=missing), self.assertRaisesRegex(Rejected, "REGISTRY_CONTEXT_REQUIRED"):
                LegacyKRWAdapter(missing, enabled=True)
        with self.assertRaisesRegex(Rejected, "LEGACY_KRW_DOMAIN_MISMATCH"):
            LegacyKRWAdapter(registry(domain="kix:execution:1"), enabled=True)
        for impostor in (AssetSpec("fiat", "KRW", 1, MAX_ATOMS),
                         AssetSpec("fiat", "KRW", 0, LEGACY_KRW_LIMIT),
                         AssetSpec("fiat", "KRW", 0, MAX_ATOMS - 1),
                         AssetSpec("fiat", "krw", 0, MAX_ATOMS),
                         AssetSpec("token", "KRW", 0, MAX_ATOMS), USDC):
            with self.subTest(impostor=impostor), self.assertRaises(Rejected):
                LegacyKRWAdapter(registry(impostor), enabled=True)

    def test_one_usdc_never_becomes_one_million_krw_at_real_core_entrypoint(self):
        calculated = Amount.from_decimal(USDC, "1.000000")
        checked = AssetAmount.from_amount(calculated, registry=self.ctx)
        self.assertEqual(checked.atoms, 1000000)
        before = self.core.snapshot()
        with self.assertRaisesRegex(Rejected, "LEGACY_KRW_ASSET_MISMATCH"):
            self.adapter.to_legacy_krw(checked)
        for incoming in (calculated.to_dict(), checked.to_dict(), checked.to_record(), checked):
            with self.subTest(incoming=incoming), self.assertRaisesRegex(Rejected, "INVALID_INTEGER:amount"):
                self.core.execute("reject-usdc", "buyer", "prepare_trade", self.prepare_body(incoming))
        self.assertEqual(self.core.snapshot(), before)
        self.assertEqual(self.core.db.execute("SELECT count(*) FROM commands").fetchone()[0], 1)

    def test_only_exact_krw_exports_and_legacy_amount_cap_is_independent(self):
        for n in (0, 1, LEGACY_KRW_LIMIT):
            out = self.adapter.to_legacy_krw(AssetAmount(KRW.asset_id, n, self.ctx))
            self.assertIs(type(out), int)
            self.assertEqual(out, n)
        for n in (LEGACY_KRW_LIMIT + 1, MAX_ATOMS):
            with self.subTest(n=n), self.assertRaisesRegex(Rejected, "LEGACY_KRW_AMOUNT_OVERFLOW"):
                self.adapter.to_legacy_krw(AssetAmount(KRW.asset_id, n, self.ctx))
        for invalid in (1, True, Amount(KRW, 1), {"assetId": KRW.asset_id, "atoms": "1"}, Sequence(1)):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(Rejected, "CHECKED_ASSET_AMOUNT_REQUIRED"):
                self.adapter.to_legacy_krw(invalid)
        for changed in (registry(version=2), registry(source="fixture:unapproved-source"),
                        registry(domain="kix:other:1"), registry(KRW)):
            with self.subTest(changed=changed), self.assertRaisesRegex(Rejected, "LEGACY_REGISTRY_CONTEXT_MISMATCH"):
                self.adapter.to_legacy_krw(AssetAmount(KRW.asset_id, 1, changed))

    def test_opted_in_krw_reaches_unchanged_core_without_new_numeric_acceptance(self):
        checked = AssetAmount.from_amount(Amount(KRW, 1000000), registry=self.ctx)
        primitive = self.adapter.to_legacy_krw(checked)
        before = self.core.snapshot()
        for changed in (dict(expectedVersion=Version(0)), dict(amount=True),
                        dict(amount=1.0), dict(amount=LEGACY_KRW_LIMIT + 1)):
            body = self.prepare_body(primitive)
            body.update(changed)
            with self.subTest(changed=changed), self.assertRaisesRegex(Rejected, "INVALID_INTEGER"):
                self.core.execute("bad-field", "buyer", "prepare_trade", body)
        self.assertEqual(self.core.snapshot(), before)
        self.core.execute("prepare-valid", "buyer", "prepare_trade", self.prepare_body(primitive))
        state = self.core.snapshot()
        self.assertEqual(state["trades"]["trade"]["amount"], 1000000)
        self.assertEqual(state["trades"]["trade"]["currency"], "KRW")
        self.assertFalse(state["trades"]["trade"]["captured"])
        self.assertEqual(state["journal"], [])

    def test_calculated_proposal_and_bound_money_grant_no_source_or_execution_authority(self):
        before = self.core.snapshot()
        request = dict(schemaVersion=SCHEMA, orderId="order", orderVersion=1,
                       scope=dict(issuerId="issuer", eventId="show", performanceId="main"),
                       policyRef="frozen-price-v1", expiresAt=1000,
                       lines=[dict(lineId="line", inventoryId=self.inventory_id,
                                   gross=Amount(KRW, 1000000).to_dict())], discounts=[])
        quote = build_quote(request)
        legs = [dict(legId="card", providerRef="fixture-pg", routeRef="original-card",
                     amount=Amount(KRW, 1000000).to_dict())]
        plan = plan_payments(quote, legs, quote["quoteHash"], 1)
        proposal = propose_line_refund(quote, plan, ["line"], plan["planHash"])
        self.assertFalse(proposal["executionAuthorized"])
        self.assertEqual(proposal["evidenceClass"], "CALCULATION_ONLY")
        self.assertEqual(self.core.snapshot(), before)
        with self.assertRaisesRegex(Rejected, "CHECKED_ASSET_AMOUNT_REQUIRED"):
            self.adapter.to_legacy_krw(proposal)
        with self.assertRaisesRegex(Rejected, "INVALID_EXECUTION_AMOUNT_RECORD"):
            AssetAmount.from_record(proposal, registry=self.ctx)
        checked = AssetAmount.from_amount(Amount.from_dict(proposal["customerRefund"]), registry=self.ctx)
        amount = self.adapter.to_legacy_krw(checked)
        prepared = self.core.execute("prepare-valid", "buyer", "prepare_trade", self.prepare_body(amount))
        capture = dict(domain=Core.DOMAIN, tradeId="trade", orderId=prepared["result"]["externalOrderId"],
                       paymentId="pay", amount=amount, currency="KRW", buyer="buyer",
                       scope=Core.SCOPE, provenance="synthetic")
        before_capture = self.core.snapshot()
        with self.assertRaisesRegex(Rejected, "UNAUTHORIZED_FIXTURE_ACTOR"):
            self.core.execute("capture-from-calculation", "calculation", "capture", capture)
        missing_source = dict(capture)
        missing_source.pop("scope")
        with self.assertRaisesRegex(Rejected, "MISSING_FIELDS:scope"):
            self.core.execute("capture-without-source", "pg-adapter", "capture", missing_source)
        self.assertEqual(self.core.snapshot(), before_capture)
        self.assertEqual(self.core.snapshot()["journal"], [])
        self.assertFalse(self.core.snapshot()["trades"]["trade"]["captured"])


if __name__ == "__main__":
    unittest.main()
