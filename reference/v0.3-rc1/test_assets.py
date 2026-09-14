"""Exact amount regressions for multi-asset contract boundaries."""
import copy
import json
import unittest

from assets import Amount, AssetRegistry, AssetSpec, KRW, MAX_ATOMS, from_decimal
from common import Rejected


class AssetContractTests(unittest.TestCase):
    def setUp(self):
        # Explicit fixture identities: these are not deployed token addresses.
        self.token = AssetSpec("chain", "fixture:sui:network-a:coin-usd", 6, MAX_ATOMS)

    def test_large_amount_round_trips_through_json_as_decimal_text(self):
        original = Amount(self.token, 2**100 + 123456789)
        wire = json.loads(json.dumps(original.to_dict()))
        self.assertIs(type(wire["atoms"]), str)
        self.assertIs(type(wire["asset"]["maxAtoms"]), str)
        self.assertEqual(Amount.from_dict(wire), original)
        self.assertEqual(Amount.from_dict(Amount(self.token, MAX_ATOMS).to_dict()).atoms,
                         MAX_ATOMS)

    def test_precision_is_exact_from_zero_to_38_places(self):
        for decimals in (0, 1, 6, 18, 38):
            asset = AssetSpec("fixture", "precision-" + str(decimals), decimals, MAX_ATOMS)
            for atoms in (0, 1, 10, 123456789, 2**100 + 1, MAX_ATOMS):
                with self.subTest(decimals=decimals, atoms=atoms):
                    value = Amount(asset, atoms)
                    self.assertEqual(from_decimal(asset, value.decimal_string()), value)
        self.assertEqual(from_decimal(self.token, "1.200000").decimal_string(), "1.2")
        self.assertEqual(Amount.from_decimal(self.token, "0.000001").atoms, 1)
        self.assertEqual(from_decimal(KRW, "100000").atoms, 100000)

    def test_amount_constructor_rejects_non_integer_and_out_of_range_values(self):
        for atoms in (-1, MAX_ATOMS + 1, True, False, 1.0, float("nan"), "1", None):
            with self.subTest(atoms=atoms), self.assertRaises(Rejected):
                Amount(self.token, atoms)

    def test_wire_rejects_ambiguous_integer_encodings_and_schema_changes(self):
        for text in ("01", "00", "+1", "-0", "-1", "1e6", "1.0", " 1", "1\n",
                     "١", "", "0" * 4000, 1, 1.0, True, None):
            wire = Amount(self.token, 1).to_dict()
            wire["atoms"] = text
            with self.subTest(text=str(text)[:50]), self.assertRaises(Rejected):
                Amount.from_dict(wire)
        for key in ("extra", "currency"):
            wire = Amount(self.token, 1).to_dict()
            wire[key] = "unexpected"
            with self.assertRaises(Rejected):
                Amount.from_dict(wire)
        with self.assertRaises(Rejected):
            Amount.from_dict({"atoms": "1"})

    def test_decimal_parser_rejects_float_exponent_rounding_and_noncanonical_text(self):
        for text in ("01", ".5", "1.", "-0", "+1", "1e6", "1E6", "NaN", "Infinity",
                     " 1", "1 ", "1\n", "０", "١", "", "0" * 4000,
                     1, 1.0, float("nan"), True, None):
            with self.subTest(text=str(text)[:50]), self.assertRaises(Rejected):
                from_decimal(self.token, text)
        for text in ("0.0000001", "1.0000000"):
            with self.assertRaisesRegex(Rejected, "PRECISION"):
                from_decimal(self.token, text)
        with self.assertRaises(Rejected):
            from_decimal(KRW, "1.0")
        with self.assertRaises(Rejected):
            from_decimal(self.token, str(MAX_ATOMS))

    def test_add_subtract_preserve_exact_atoms_and_enforce_limits(self):
        a, b = Amount(self.token, 2**80), Amount(self.token, 11)
        self.assertEqual(((a + b) - b), a)
        self.assertEqual(a.sub(a), Amount(self.token, 0))
        self.assertEqual(Amount(self.token, MAX_ATOMS).add(Amount(self.token, 0)).atoms,
                         MAX_ATOMS)
        with self.assertRaisesRegex(Rejected, "OVERFLOW"):
            Amount(self.token, MAX_ATOMS).add(b)
        with self.assertRaisesRegex(Rejected, "UNDERFLOW"):
            b.sub(a)
        with self.assertRaisesRegex(Rejected, "OPERAND"):
            a.add(11)

    def test_same_symbol_on_distinct_networks_is_not_the_same_asset(self):
        other = AssetSpec("chain", "fixture:sui:network-b:coin-usd", 6, MAX_ATOMS)
        self.assertNotEqual(self.token.asset_id, other.asset_id)
        for operation in (Amount(self.token, 2).add, Amount(self.token, 2).sub):
            with self.assertRaisesRegex(Rejected, "ASSET_MISMATCH"):
                operation(Amount(other, 1))
        with self.assertRaisesRegex(Rejected, "ASSET_MISMATCH"):
            Amount(KRW, 2).add(Amount(self.token, 1))

    def test_identity_binds_metadata_and_registry_prevents_reinterpretation(self):
        registry = AssetRegistry()
        self.assertEqual(registry.register(self.token), self.token)
        self.assertEqual(registry.register(AssetSpec.from_dict(self.token.to_dict())), self.token)
        self.assertEqual(registry.get(self.token.namespace, self.token.reference), self.token)
        variants = (
            AssetSpec(self.token.namespace, self.token.reference, 18, MAX_ATOMS),
            AssetSpec(self.token.namespace, self.token.reference, 6, MAX_ATOMS - 1),
        )
        for changed in variants:
            with self.subTest(changed=changed):
                self.assertNotEqual(self.token.asset_id, changed.asset_id)
                with self.assertRaisesRegex(Rejected, "METADATA_CONFLICT"):
                    registry.register(changed)
                with self.assertRaisesRegex(Rejected, "ASSET_MISMATCH"):
                    Amount(self.token, 1).add(Amount(changed, 1))
        self.assertEqual(registry.get(self.token.namespace, self.token.reference), self.token)
        with self.assertRaisesRegex(Rejected, "NOT_REGISTERED"):
            registry.get("chain", "missing-network")

    def test_asset_metadata_rejects_ambiguous_identifiers_and_invalid_limits(self):
        for namespace in ("Fiat", "", "1fiat", "fiat:krw", "a" * 64, True, None):
            with self.subTest(namespace=namespace), self.assertRaises(Rejected):
                AssetSpec(namespace, "KRW", 0, MAX_ATOMS)
        for reference in ("", " KRW", "KRW ", "K RW", "K\nRW", "K\u200bRW",
                          "e\u0301", "a" * 257, "가" * 200, True, None):
            with self.subTest(reference=reference), self.assertRaises(Rejected):
                AssetSpec("fiat", reference, 0, MAX_ATOMS)
        for decimals in (-1, 39, True, 1.0, "6", None):
            with self.subTest(decimals=decimals), self.assertRaises(Rejected):
                AssetSpec("fiat", "KRW", decimals, MAX_ATOMS)
        for limit in (0, -1, MAX_ATOMS + 1, True, 1.0, "100", None):
            with self.subTest(limit=limit), self.assertRaises(Rejected):
                AssetSpec("fiat", "KRW", 0, limit)

    def test_asset_wire_requires_string_limit_and_no_implicit_schema_fields(self):
        original = self.token.to_dict()
        for change in ({"maxAtoms": 100}, {"maxAtoms": "0100"}, {"maxAtoms": "1e3"},
                       {"maxAtoms": str(MAX_ATOMS + 1)}, {"maxAtoms": "0"},
                       {"decimals": True}, {"ticker": "USD"}):
            wire = copy.deepcopy(original)
            wire.update(change)
            with self.subTest(change=change), self.assertRaises(Rejected):
                AssetSpec.from_dict(wire)
        del original["reference"]
        with self.assertRaises(Rejected):
            AssetSpec.from_dict(original)


if __name__ == "__main__":
    unittest.main()
