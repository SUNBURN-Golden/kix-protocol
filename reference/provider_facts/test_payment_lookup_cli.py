"""Source-informed offline CLI boundary tests. Analog, NOT Toss.

Reuse literal normalization goldens; no provider or production claims.
"""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

import payment_lookup_cli as cli
import synthetic_documents as documents
from fake_payment_lookup import FakePaymentLookup
from normalization_golden_vectors import GOLDEN_VECTORS
from payment_lookup_router import PaymentLookupRouter
from provider_facts import OperationBindingStore, normalize_recorded_text


CLI = Path(__file__).with_name("payment_lookup_cli.py").resolve()
OPERATION = asdict(documents.OPERATION_REF)
PAYMENT = documents.PAYMENT_REF_A.as_dict()
SCOPE = {key: PAYMENT[key] for key in ("provider", "account", "environment")}


def fixture(recorded_text=None):
    """Alternate scope succeeds with reused payment/order keys, even on A's fault."""
    other_payment = dict(PAYMENT, account="aaa_other_synthetic_mid")
    return {
        "fixture_version": 1,
        "provenance": "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY",
        "bindings": [{"operation_ref": dict(OPERATION), "payment_ref": dict(PAYMENT)}],
        # Reverse sort order deliberately; output order is independent of registration.
        "routes": [
            {"scope": dict(SCOPE), "recordings": [{
                "payment_ref": dict(PAYMENT),
                "recorded_text": json.dumps(documents.PAID, ensure_ascii=False)
                if recorded_text is None else recorded_text,
            }]},
            {"scope": dict(SCOPE, account=other_payment["account"]), "recordings": [{
                "payment_ref": other_payment, "recorded_text": json.dumps(documents.PAID),
            }]},
        ],
    }


def invalid_fixtures():
    base = fixture()
    yield "root type", []
    # Each structural object is strict about missing/unknown fields and type.
    paths = [(), ("bindings", 0), ("bindings", 0, "operation_ref"),
             ("bindings", 0, "payment_ref"), ("routes", 0), ("routes", 0, "scope"),
             ("routes", 0, "recordings", 0), ("routes", 0, "recordings", 0, "payment_ref")]
    for path in paths:
        original = base
        for key in path:
            original = original[key]
        for key in original:
            changed = deepcopy(base)
            target = changed
            for part in path:
                target = target[part]
            del target[key]
            yield f"missing {path}/{key}", changed
        changed = deepcopy(base)
        target = changed
        for part in path:
            target = target[part]
        target["unknown"] = "synthetic"
        yield f"unknown {path}", changed
        if path:
            changed = deepcopy(base)
            target = changed
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = []
            yield f"object type {path}", changed

    value_paths = [
        (("fixture_version",), (True, 1.0, 2, "1", None)),
        (("provenance",), ("real", None, [])),
        (("bindings",), ({}, None)),
        (("routes",), ({}, None)),
        (("routes", 0, "recordings"), ({}, None)),
        (("routes", 0, "recordings", 0, "recorded_text"), ({}, None, 3)),
    ]
    for ref_path, keys in (
        (("bindings", 0, "operation_ref"), OPERATION),
        (("bindings", 0, "payment_ref"), PAYMENT),
        (("routes", 0, "scope"), SCOPE),
        (("routes", 0, "recordings", 0, "payment_ref"), PAYMENT),
    ):
        for key in keys:
            value_paths.append((ref_path + (key,), ("", " leading", "trailing ", "x" * 101, 1, True, None)))
    for path, values in value_paths:
        for value in values:
            changed = deepcopy(base)
            target = changed
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = value
            yield f"value {path}/{value!r}", changed

    for conflict in (False, True):
        changed = deepcopy(base)
        duplicate = deepcopy(changed["bindings"][0])
        if conflict:
            duplicate["payment_ref"]["order_id"] = "different_synthetic_order"
        changed["bindings"].append(duplicate)
        yield f"duplicate binding conflict={conflict}", changed
        changed = deepcopy(base)
        duplicate = deepcopy(changed["routes"][0])
        if conflict:
            duplicate["recordings"] = []
        changed["routes"].append(duplicate)
        yield f"duplicate scope conflict={conflict}", changed
        changed = deepcopy(base)
        duplicate = deepcopy(changed["routes"][0]["recordings"][0])
        if conflict:
            duplicate["recorded_text"] = "different text"
        changed["routes"][0]["recordings"].append(duplicate)
        yield f"duplicate recording conflict={conflict}", changed

    for dimension in ("provider", "account"):
        changed = deepcopy(base)
        changed["bindings"][0]["payment_ref"][dimension] = "different_synthetic"
        yield "binding mismatch " + dimension, changed
    for dimension in SCOPE:
        changed = deepcopy(base)
        changed["routes"][1]["recordings"][0]["payment_ref"][dimension] = "different_synthetic"
        yield "unused trailing route mismatch " + dimension, changed
    for value in ("timeout", "", 1, None, [], {}):
        changed = deepcopy(base)
        recording = changed["routes"][1]["recordings"][0]
        del recording["recorded_text"]
        recording["fault"] = value
        yield "invalid fault " + repr(value), changed
    changed = deepcopy(base)
    changed["routes"][1]["recordings"][0]["fault"] = "synthetic_timeout"
    yield "both recording alternatives", changed


class PaymentLookupCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "new-synthetic-fixture.json"

    def write(self, config):
        self.path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    def invoke(self, operation=OPERATION, extra=()):
        before = self.path.read_bytes()
        process = subprocess.run(
            [sys.executable, str(CLI), "--fixture", str(self.path),
             "--operation-ref", json.dumps(operation), *extra],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        self.assertEqual(self.path.read_bytes(), before)
        return process

    def result(self, config, operation=OPERATION):
        self.write(config)
        process = self.invoke(operation)
        self.assertEqual((process.returncode, process.stderr), (0, ""))
        self.assertEqual(len(process.stdout.splitlines()), 1)
        result = json.loads(process.stdout)
        self.assertEqual(result["operation_ref"], operation)
        self.assertEqual(result["provenance"], "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY")
        self.assertEqual(result["limitations"], cli.LIMITATIONS)
        self.assertEqual(process.stdout, json.dumps(
            result, ensure_ascii=False, sort_keys=True, allow_nan=False,
        ) + "\n")
        scopes = [row["scope"] for row in result["fake_calls"]]
        self.assertEqual(scopes, sorted(scopes, key=lambda s: (s["provider"], s["account"], s["environment"])))
        return result

    def assert_calls(self, result, expected):
        actual = [ref for row in result["fake_calls"] for ref in row["payment_refs"]]
        self.assertEqual(actual, expected)
        for row in result["fake_calls"]:
            for ref in row["payment_refs"]:
                self.assertEqual(row["scope"], {key: ref[key] for key in SCOPE})

    def test_all_literal_golden_vectors_through_subprocess(self):
        for vector in GOLDEN_VECTORS:
            with self.subTest(case=vector["case"]):
                text = " \n" + json.dumps(getattr(documents, vector["fixture"]), ensure_ascii=False, indent=2) + "\t\n"
                result = self.result(fixture(text))
                position = vector["item_position"]
                self.assertEqual(result["payment_ref"], PAYMENT)
                self.assertEqual(result["facts"][position], vector["expected_fact"])
                self.assertEqual(result["item_hashes"][position], vector["sha256_hex"])
                fact_bytes = json.dumps(result["facts"][position], sort_keys=True, ensure_ascii=False,
                                        separators=(",", ":"), allow_nan=False).encode("utf-8")
                self.assertEqual(fact_bytes, vector["canonical_utf8"])
                self.assertIs(type(result["facts"][position]["item"]["amount"]), int)
                self.assertEqual(result["receipt"], {
                    "text": "2026-10-01T12:00:05+09:00", "offset": "+09:00", "status": "OFFSET_RECORDED",
                })
                self.assertNotIn("unresolved", result)
                self.assertNotIn("item_hashes", result["facts"][position])
                self.assert_calls(result, [PAYMENT])

    def test_full_cancellation_keeps_payment_and_cancel(self):
        result = self.result(fixture(json.dumps(documents.CANCELED_AFTER_DONE)))
        # Detailed independent expected history is already in test_payment_lookup.
        self.assertEqual([(f["item"]["kind"], f["item"]["amount"]) for f in result["facts"]],
                         [("payment", 15000), ("cancel", 15000)])
        self.assertEqual(len(result["item_hashes"]), 2)
        self.assert_calls(result, [PAYMENT])

    def test_unresolved_original_scope_only_and_recorded_text_opaque(self):
        for text, reason in (
            ("not JSON \n 카드", "DOCUMENT_JSON"), ("[]", "DOCUMENT_TYPE"),
            (documents.FLOAT_AMOUNT_TEXT, "FLOAT_TOKEN"),
            (documents.EXPONENT_AMOUNT_TEXT, "FLOAT_TOKEN"),
            (json.dumps(documents.UNVERIFIED_SIGNAL), "UNVERIFIED_SOURCE"),
            (json.dumps(documents.NOT_FOUND), "LOOKUP_NOT_FOUND"),
        ):
            with self.subTest(reason=reason, text=text):
                config = fixture(text)
                self.write(config)
                bindings, routes = cli.load_fixture(self.path)
                fake = next(fake for scope, fake in routes.items() if asdict(scope) == SCOPE)
                self.assertEqual(fake.recordings[documents.PAYMENT_REF_A], text)
                self.assertEqual(fake.calls, ())
                result = self.result(config)
                self.assertEqual(result["unresolved"], reason)
                self.assertEqual(result["payment_ref"], PAYMENT)
                self.assertNotIn("facts", result)
                self.assertNotIn("receipt", result)
                self.assertNotIn("item_hashes", result)
                self.assert_calls(result, [PAYMENT])
        for fault, reason in (("synthetic_timeout", "LOOKUP_TIMEOUT"),
                              ("synthetic_lookup_error", "LOOKUP_ERROR"), (None, "LOOKUP_NOT_FOUND")):
            config = fixture()
            config["routes"][0]["recordings"] = ([] if fault is None else [
                {"payment_ref": PAYMENT, "fault": fault},
            ])
            result = self.result(config)
            self.assertEqual(result["unresolved"], reason)
            self.assert_calls(result, [PAYMENT])

    def test_missing_binding_route_and_empty_configuration(self):
        config = fixture()
        config["bindings"] = []
        result = self.result(config)
        self.assertEqual((result["unresolved"], result["payment_ref"]), ("BINDING_REQUIRED", None))
        self.assert_calls(result, [])
        for routes in ([], [fixture()["routes"][1]]):
            config = fixture()
            config["routes"] = routes
            result = self.result(config)
            self.assertEqual((result["unresolved"], result["payment_ref"]), ("LOOKUP_ROUTE_MISSING", PAYMENT))
            self.assert_calls(result, [])
        config["bindings"] = []
        config["routes"] = []
        self.assert_calls(self.result(config), [])

    def test_new_fixture_complete_identities_route_in_each_dimension(self):
        for dimension in ("provider", "account", "environment", "order_id", "payment_key"):
            with self.subTest(dimension=dimension):
                config = fixture()
                payment = dict(PAYMENT, **{dimension: "new_synthetic_value"})
                operation = dict(OPERATION)
                if dimension in ("provider", "account"):
                    operation[dimension] = payment[dimension]
                else:
                    operation["operation"] = "new_synthetic_operation"
                document = deepcopy(documents.PAID)
                document["payment"]["paymentKey"] = payment["payment_key"]
                document["payment"]["orderId"] = payment["order_id"]
                config["bindings"].append({"operation_ref": operation, "payment_ref": payment})
                recording = {"payment_ref": payment, "recorded_text": json.dumps(document)}
                if dimension in SCOPE:
                    config["routes"].append({"scope": {key: payment[key] for key in SCOPE}, "recordings": [recording]})
                else:
                    config["routes"][0]["recordings"].append(recording)
                result = self.result(config, operation)
                self.assertEqual(result["payment_ref"], payment)
                self.assertEqual(result["facts"][0]["payment_ref"], payment)
                self.assert_calls(result, [payment])

    def test_invalid_entire_configuration_precedes_all_lookup_and_binding(self):
        for label, config in invalid_fixtures():
            with self.subTest(case=label):
                self.write(config)
                with patch.object(PaymentLookupRouter, "lookup") as router, \
                     patch.object(FakePaymentLookup, "lookup") as fake, \
                     patch.object(OperationBindingStore, "bind") as bind, \
                     contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()) as out:
                    with self.assertRaises(SystemExit) as caught:
                        cli.main(["--fixture", str(self.path), "--operation-ref", json.dumps(OPERATION)])
                    self.assertEqual(caught.exception.code, 2)
                    self.assertEqual(out.getvalue(), "")
                    router.assert_not_called()
                    fake.assert_not_called()
                    bind.assert_not_called()
                process = self.invoke()
                self.assertEqual((process.returncode, process.stdout), (2, ""))
                self.assertIn("error:", process.stderr)

    def test_duplicate_json_keys_and_invalid_json_are_configuration_errors(self):
        base = json.dumps(fixture())
        for raw in (
            "{", base + " trailing", base.replace('"fixture_version": 1', '"fixture_version": NaN'),
            base.replace('"fixture_version": 1', '"fixture_version": Infinity'),
            base.replace('"fixture_version": 1', '"fixture_version": 1, "fixture_version": 1'),
            base.replace('"operation": "op_synthetic_0001"', '"operation": "op_synthetic_0001", "operation": "other"'),
            base.replace('"recorded_text":', '"recorded_text": "unused", "recorded_text":', 1),
        ):
            with self.subTest(raw=raw):
                self.path.write_text(raw, encoding="utf-8")
                with self.assertRaises(cli.FixtureError):
                    cli.load_fixture(self.path)
                process = self.invoke()
                self.assertEqual((process.returncode, process.stdout), (2, ""))
                self.assertIn("error:", process.stderr)

    def test_usage_operation_and_file_errors(self):
        self.write(fixture())
        for operation in ({}, dict(OPERATION, environment="untrusted"), dict(OPERATION, operation=1), [],
                          dict(OPERATION, operation=" padded ")):
            process = self.invoke(operation)
            self.assertEqual((process.returncode, process.stdout), (2, ""))
        for extra in (("--fixture", str(self.path)), ("--operation-ref", json.dumps(OPERATION)),
                      ("--provider", "synthetic"), ("--fixt", str(self.path))):
            process = self.invoke(extra=extra)
            self.assertEqual((process.returncode, process.stdout), (2, ""))
        for args in ([], ["--fixture", str(self.path)],
                     ["--fixture", str(self.path), "--operation-ref", "{"],
                     ["--fixture", str(self.path), "--operation-ref", '{"provider":"a","provider":"b","account":"c","operation":"d"}']):
            process = subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True, timeout=10)
            self.assertEqual((process.returncode, process.stdout), (2, ""))
        for path in (self.path.parent / "absent.json", self.path.parent, self.path):
            if path == self.path:
                path.write_bytes(b"\xff")
            process = subprocess.run([sys.executable, str(CLI), "--fixture", str(path),
                                      "--operation-ref", json.dumps(OPERATION)],
                                     capture_output=True, text=True, timeout=10)
            self.assertEqual((process.returncode, process.stdout), (2, ""))
            self.assertIn("error:", process.stderr)

    def test_lookup_once_preserves_nonempty_history_and_calls_router_once(self):
        self.write(fixture())
        bindings, routes = cli.load_fixture(self.path)
        operation, payment = documents.OPERATION_REF, documents.PAYMENT_REF_A
        item = normalize_recorded_text(payment, json.dumps(documents.PAID)).items[0]
        bindings.record_capture(operation, payment, item)
        bindings.bind(operation, documents.PAYMENT_REF_B)
        missing = replace(operation, operation="missing_synthetic")

        def snapshot():
            return deepcopy((bindings.binding_count(), bindings.lookup(operation), bindings.lookup(missing),
                             bindings.recorded_captures, bindings.review,
                             [(scope, dict(fake.recordings)) for scope, fake in routes.items()]))

        before = snapshot()
        with patch.object(PaymentLookupRouter, "lookup", autospec=True,
                          side_effect=PaymentLookupRouter.lookup) as router, \
             patch.object(bindings, "bind", side_effect=AssertionError("lookup must not bind")), \
             patch.object(bindings, "record_capture", side_effect=AssertionError("lookup must not capture")):
            result = cli.lookup_once(bindings, routes, operation)
            router.assert_called_once()
            self.assertEqual(router.call_args.args[1], operation)
        self.assertEqual(snapshot(), before)
        self.assert_calls(result, [PAYMENT])
        # Call output reports actual cumulative snapshots for reusable callers.
        again = cli.lookup_once(bindings, routes, operation)
        self.assert_calls(again, [PAYMENT, PAYMENT])
        self.assertEqual(snapshot(), before)
        selected_snapshot = next(row for row in result["fake_calls"] if row["scope"] == SCOPE)
        self.assertEqual(selected_snapshot["payment_refs"], [PAYMENT])

    def test_unexpected_programming_error_propagates(self):
        self.write(fixture())
        with patch.object(PaymentLookupRouter, "lookup", side_effect=RuntimeError("synthetic bug")), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            with self.assertRaisesRegex(RuntimeError, "synthetic bug"):
                cli.main(["--fixture", str(self.path), "--operation-ref", json.dumps(OPERATION)])
            self.assertEqual(out.getvalue(), "")

    def test_shipped_fixture_is_runnable(self):
        shipped = CLI.parent / "fixtures" / "payment_lookup.synthetic.json"
        self.write(json.loads(shipped.read_text(encoding="utf-8")))
        process = self.invoke()
        self.assertEqual((process.returncode, process.stderr), (0, ""))
        self.assertEqual(json.loads(process.stdout)["facts"][0], GOLDEN_VECTORS[0]["expected_fact"])


if __name__ == "__main__":
    unittest.main()
