"""Complete source-informed, in-process mock vectors; never updates goldens.

The fixture encoding is local comparison evidence, not a protocol encoding.
Import the journey module (not its TestCase) to avoid duplicate discovery.
"""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from unittest.mock import patch

import test_commerce_journey_conformance as journey
from integration_gate.catalogue import git_blob_id
from mock_gates import _canonical

ROOT = journey.ROOT
FIXTURE = "reference/booking_resale_admission/fixtures/commerce_journey_conformance_v1.json"
GOLDEN = ROOT / "reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json"

# Explicit allowlist: no self-hash, report hash, or commit/CI identity.
SOURCE_PATHS = frozenset({
    "reference/booking_resale_admission/test_commerce_journey_conformance.py",
    "integration_gate/fsm_host.py",
    "integration_gate/fsm_contract.py",
    "integration_gate/catalogue.py",
    "integration_gate/constants.py",
    "integration_gate/schema.py",
    "reference/booking_resale_admission/reservation_fsm.py",
    "reference/booking_resale_admission/resale_fsm.py",
    "reference/booking_resale_admission/admission_fsm.py",
    "reference/booking_resale_admission/mock_gates.py",
    "reference/settlement_f01_f03/settlement_fsm.py",
    "reference/settlement_f01_f03/mock_settlement.py",
    "reference/credit_advance_f04/credit_fsm.py",
    "reference/credit_advance_f04/mock_credit.py",
    "reference/credit_advance_f04/open_terms.py",
    "docs/contracts/openapi/fsm-command-contract.json",
    "reference/v0.3-rc1/protocol_contract.json",
    "docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json",
    "docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json",
})


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("non-finite JSON constant: " + value)


def _decode(raw):
    document = json.loads(
        raw.decode("utf-8"), object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    # Also reject overflowing JSON numbers (e.g. 1e999).
    _canonical(document)
    return document


def _read(path):
    return (ROOT / path).read_bytes()


def _pin(path, raw):
    return {
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "gitBlob": git_blob_id(raw),
    }


def _inputs(read=_read):
    fixture_raw = read(FIXTURE)
    return (
        fixture_raw,
        _pin(FIXTURE, fixture_raw),
        [_pin(path, read(path)) for path in sorted(SOURCE_PATHS)],
    )


def _observe(fixture_raw, fixture_pin, sources):
    fixture = _decode(fixture_raw)
    ids = [step["id"] for step in fixture["steps"]]
    journey._check(len(ids) == len(set(ids)) == 44, "expected 44 unique input steps")
    _host, receipts, refusals = journey._drive(fixture)
    journey._check(not (receipts.keys() & refusals.keys()), "overlapping outcomes")
    journey._check(receipts.keys() | refusals.keys() == set(ids), "missing/extra outcomes")
    steps = []
    for i, step in enumerate(fixture["steps"]):
        outcome = {
            "id": step["id"],
            "action": step["action"],
            "input_ref": FIXTURE + "#/steps/%d/body" % i,
        }
        if step["id"] in receipts:
            outcome["receipt"] = receipts[step["id"]]
        else:
            outcome["rejection_code"] = refusals[step["id"]]
        steps.append(outcome)
    return {
        "record_schema_version": "kix-commerce-journey-receipts/1",
        "record_kind": "IN_PROCESS_MOCK_RECEIPT_VECTORS",
        "normative": False,
        "fixture": fixture_pin,
        "sources": sources,
        "steps": steps,
    }


def compare_receipts(golden_bytes, read=_read):
    """Verify pins before replay, then compare independently derived raw bytes.

    Read injection is only for in-memory drift controls. No write/update mode.
    A mismatch requires diagnosis and reviewed evidence, never auto-regeneration.
    """
    expected = _decode(golden_bytes)
    fixture_raw, fixture_pin, sources = _inputs(read)
    journey._check(expected["fixture"] == fixture_pin, "fixture pin drift")
    journey._check(expected["sources"] == sources, "source pin drift/set/order mismatch")
    observed = _observe(fixture_raw, fixture_pin, sources)
    journey._check(
        _canonical(observed).encode("utf-8") == golden_bytes,
        "complete canonical receipt bytes differ",
    )
    return observed


class CommerceJourneyReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = GOLDEN.read_bytes()
        cls.document = _decode(cls.raw)
        cls.fixture = _decode(_read(FIXTURE))

    def test_complete_output_bytes(self):
        compare_receipts(self.raw)

    def test_step_mapping(self):
        steps = self.document["steps"]
        self.assertEqual(len(steps), 44)
        self.assertEqual(len({step["id"] for step in steps}), 44)
        receipts = {}
        refusals = {}
        for i, (source, vector) in enumerate(zip(self.fixture["steps"], steps)):
            self.assertEqual(vector["id"], source["id"])
            self.assertEqual(vector["action"], source["action"])
            self.assertEqual(vector["input_ref"], FIXTURE + "#/steps/%d/body" % i)
            path, pointer = vector["input_ref"].split("#")
            resolved = _decode(_read(path))
            for segment in pointer.lstrip("/").split("/"):
                resolved = resolved[int(segment)] if isinstance(resolved, list) else resolved[segment]
            self.assertEqual(resolved, source["body"])
            key = "rejection_code" if "expect_error" in source else "receipt"
            self.assertEqual(set(vector), {"id", "action", "input_ref", key})
            (refusals if key == "rejection_code" else receipts)[vector["id"]] = vector[key]
        self.assertEqual(len(receipts), 39)
        self.assertEqual(refusals, journey.ADVERSE_REFUSALS)
        self.assertFalse(receipts.keys() & refusals.keys())

    def test_source_pins(self):
        _raw, fixture_pin, sources = _inputs()
        self.assertEqual(self.document["fixture"], fixture_pin)
        self.assertEqual(self.document["sources"], sources)
        self.assertEqual({pin["path"] for pin in sources}, SOURCE_PATHS)
        self.assertEqual(len(sources), len(SOURCE_PATHS))

    def test_output_mutations_fail_comparison(self):
        # Mutate actual runner output, including fields outside old expect.paths.
        host, original, refusals = journey._drive(self.fixture)
        cases = (
            ("change nested field", lambda r: r["issue-B"]["reservation"].update(issuance_id="changed")),
            ("add nested field", lambda r: r["issue-B"]["reservation"].update(unexpected=None)),
            ("remove nested field", lambda r: r["issue-B"]["reservation"].pop("issuance_id")),
            ("false is not zero", lambda r: r["issue-B"]["evidence"].update(chain_issued=0)),
            ("change null", lambda r: r["replay-consume-B"].update(applied="consume")),
        )
        for label, mutate in cases:
            receipts = copy.deepcopy(original)
            mutate(receipts)
            with self.subTest(label=label), patch.object(journey, "_drive", return_value=(host, receipts, refusals)):
                with self.assertRaisesRegex(AssertionError, "canonical receipt bytes differ"):
                    compare_receipts(self.raw)
        changed_refusals = dict(refusals, **{"double-consume": "CHANGED"})
        with patch.object(journey, "_drive", return_value=(host, original, changed_refusals)):
            with self.assertRaisesRegex(AssertionError, "canonical receipt bytes differ"):
                compare_receipts(self.raw)

    def test_step_mutations_fail_comparison(self):
        def reorder(steps):
            steps[0], steps[1] = steps[1], steps[0]

        cases = (
            ("omit", lambda s: s.pop()),
            ("duplicate", lambda s: s.append(copy.deepcopy(s[0]))),
            ("reorder", reorder),
            ("input reference", lambda s: s[0].update(input_ref=FIXTURE + "#/steps/1/body")),
            ("action", lambda s: s[0].update(action="changed")),
            ("id", lambda s: s[0].update(id="changed")),
        )
        for label, mutate in cases:
            document = copy.deepcopy(self.document)
            mutate(document["steps"])
            with self.subTest(label=label), self.assertRaisesRegex(AssertionError, "canonical receipt bytes differ"):
                compare_receipts(_canonical(document).encode("utf-8"))

    def test_pin_mutations_fail_before_execution(self):
        cases = (
            ("omit source", lambda d: d["sources"].pop()),
            ("duplicate source", lambda d: d["sources"].append(d["sources"][0])),
            ("extra source", lambda d: d["sources"].append(_pin("extra.py", b""))),
            ("sha256", lambda d: d["sources"][0].update(sha256="0" * 64)),
            ("git blob", lambda d: d["sources"][0].update(gitBlob="0" * 40)),
            ("fixture", lambda d: d["fixture"].update(sha256="0" * 64)),
        )
        for label, mutate in cases:
            document = copy.deepcopy(self.document)
            mutate(document)
            with self.subTest(label=label), patch.object(journey, "_drive") as drive:
                with self.assertRaisesRegex(AssertionError, "pin drift"):
                    compare_receipts(_canonical(document).encode("utf-8"))
                drive.assert_not_called()
        # Byte-only drift must fail even if Python behavior would be identical.
        for path in (FIXTURE, *sorted(SOURCE_PATHS)):
            def drifted_read(candidate):
                raw = _read(candidate)
                return raw + b"\n" if candidate == path else raw

            with self.subTest(drift=path), patch.object(journey, "_drive") as drive:
                with self.assertRaisesRegex(AssertionError, "pin drift"):
                    compare_receipts(self.raw, read=drifted_read)
                drive.assert_not_called()

    def test_strict_json_and_canonical_serialization(self):
        bad = (
            b'{', b'\xff', b'{"steps":[],"steps":[]}',
            b'{"nested":{"x":1,"x":2}}', b'{"x":NaN}',
            b'{"x":Infinity}', b'{"x":-Infinity}', b'{"x":1e999}',
            self.raw + b'{}',
        )
        for raw in bad:
            with self.subTest(raw=raw[:60]), self.assertRaises((ValueError, UnicodeError)):
                compare_receipts(raw)
        for raw in (self.raw + b"\n", json.dumps(self.document, indent=2).encode("utf-8")):
            with self.subTest(noncanonical=raw[:60]), self.assertRaisesRegex(AssertionError, "canonical receipt bytes differ"):
                compare_receipts(raw)


if __name__ == "__main__":
    unittest.main()
