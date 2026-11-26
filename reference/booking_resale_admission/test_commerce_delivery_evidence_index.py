"""Check the offline links to caller observations and producer evidence."""

from collections import Counter
from copy import deepcopy
import unittest

from test_commerce_companion_evidence_index import _resolve, _same
from test_commerce_journey_receipts import _decode, _pin, _read


INDEX = "docs/status/COMMERCE_DELIVERY_EVIDENCE_INDEX_V1.json"
BINDING = "docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json"
VECTORS = "sdk/conformance/vectors/commerce-fixture-tuple.vectors.json"
GRANTS = "sdk/conformance/vectors/producer-grant-selection.vectors.json"
FIXTURE_DIR = "reference/booking_resale_admission/fixtures"
ADMISSION = f"{FIXTURE_DIR}/commerce_admission_lost_reply_v1.json"
REFUSAL = f"{FIXTURE_DIR}/commerce_withheld_resale_refusal_v1.json"
REFUND = f"{FIXTURE_DIR}/commerce_refund_acceptance_lost_reply_v1.json"

# Source identities and positions come from the individual fixture replays.
FIXTURES = {
    f"{FIXTURE_DIR}/commerce_payment_observation_lost_reply_v1.json": (
        "booking-admission/payment-B", 26,
    ),
    f"{FIXTURE_DIR}/commerce_issuance_lost_reply_v1.json": ("booking-admission/issue-B", 28),
    f"{FIXTURE_DIR}/commerce_transfer_lost_reply_v1.json": ("resale-market/market-accept", 63),
    ADMISSION: ("booking-admission/consume-B", 32),
    REFUND: ("booking-refund/observe-mock-acceptance", 49),
    REFUSAL: ("booking-resale/accept-A-before-commit", 18),
    f"{FIXTURE_DIR}/commerce_cancel_lost_reply_v1.json": ("booking-refund/cancel-C", 39),
}
RECEIPT_SOURCES = {
    "source_booking_branch_receipts": f"{FIXTURE_DIR}/commerce_booking_branch_receipts_v1.json",
    "source_journey_receipts": f"{FIXTURE_DIR}/commerce_journey_receipts_v1.json",
    "source_market_receipts": f"{FIXTURE_DIR}/commerce_market_full_receipts_v1.json",
}
PAIRED_LOSSES = {"loss-before-dispatch": "before_dispatch", "loss-after-dispatch": "after_dispatch"}
REFUSAL_CASES = {
    "refusal-delivered": "none",
    "loss-before-dispatch": "before_dispatch",
    "refusal-withheld-after-dispatch": "after_dispatch",
}
NOT_BOUND = {"status": "NOT_BOUND", "vector_id": None}


class CommerceDeliveryEvidenceIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = _decode(_read(INDEX))
        sources = {path: _read(path) for path in (*FIXTURES, VECTORS, BINDING, GRANTS)}
        cls.documents = {path: _decode(raw) for path, raw in sources.items()}
        cls.pins = {path: _pin(path, raw) for path, raw in sources.items()}
        cls.receipt_pins = {path: _pin(path, _read(path)) for path in RECEIPT_SOURCES.values()}

    def assert_delivery_index(self, index):
        self.assertEqual(set(index), {
            "record_schema_version", "normative", "consumer", "pins", "fixtures",
            "unpublished_reads_ref", "recovery_ref",
        })
        self.assertEqual(index["record_schema_version"], "kix-commerce-delivery-evidence-index/1")
        self.assertIs(index["normative"], False)
        self.assertEqual(index["consumer"], "kix-commerce-apps")
        self.assertEqual(Counter(pin["path"] for pin in index["pins"]), Counter(self.pins.keys()))
        for pin in index["pins"]:
            self.assertEqual(pin, self.pins[pin["path"]], pin["path"])

        rows = index["fixtures"]
        self.assertEqual(Counter(row["fixture_path"] for row in rows), Counter(FIXTURES.keys()))
        outcomes = Counter()
        for row in rows:
            outcomes.update(self.check_fixture(row, self.documents[row["fixture_path"]]))
        self.assertEqual(outcomes, {"UNKNOWN": 14, "business-reject": 1})

    def check_fixture(self, row, fixture):
        self.assertEqual(set(row), {"fixture_path", "source_vector_id", "source_vector_ref", "cases"})
        path = row["fixture_path"]
        vector_id, position = FIXTURES[path]
        expected_pin = {**self.pins[VECTORS], "id": vector_id}
        if path == ADMISSION:
            del expected_pin["gitBlob"]
        else:
            self.assertEqual(fixture["recovery_lookup"], "NOT_BOUND")
        self.assertEqual(fixture["source_vector"], expected_pin)
        for field, pin in fixture.items():
            if field.startswith("source_") and field.endswith("_receipts"):
                self.assertEqual(pin, self.receipt_pins[RECEIPT_SOURCES[field]], field)

        self.assertEqual(row["source_vector_id"], vector_id)
        self.assertEqual(row["source_vector_ref"], f"{VECTORS}#/vectors/{position}")
        vector = _resolve(self.documents, row["source_vector_ref"])
        self.assertEqual(vector["id"], vector_id)
        envelope = vector["envelope"]

        expected_cases = REFUSAL_CASES if path == REFUSAL else PAIRED_LOSSES
        source_cases = fixture["cases"]
        source_keys = Counter((case["id"], case["fault_point"]) for case in source_cases)
        index_keys = Counter((case["case_id"], case["fault_point"]) for case in row["cases"])
        self.assertEqual(source_keys, Counter(expected_cases.items()), "fixture case coverage")
        self.assertEqual(index_keys, source_keys, "index case coverage")
        cases_by_id = {case["case_id"]: case for case in row["cases"]}
        outcomes = []
        for position, source_case in enumerate(source_cases):
            case_id = source_case["id"]
            case = cases_by_id[case_id]
            self.assertEqual(set(case), {
                "case_id", "fault_point", "caller_observation_ref", "producer_evidence_ref",
            })
            case_ref = f"{path}#/cases/{position}"
            caller_ref = f"{case_ref}/expected_caller" if path == REFUSAL else f"{path}#/expected_caller"
            self.assertEqual(case["caller_observation_ref"], caller_ref, f"{case_id} caller pointer")
            self.assertEqual(case["producer_evidence_ref"], f"{case_ref}/producer_evidence",
                             f"{case_id} producer pointer")
            caller = _resolve(self.documents, case["caller_observation_ref"])
            producer = _resolve(self.documents, case["producer_evidence_ref"])
            self.assertIsInstance(producer, dict, case_id)
            expected_caller = {
                "operationId": envelope["operationId"],
                "idempotency_key": envelope["body"]["idempotency_key"],
                "outcome": "UNKNOWN",
                "receipt": None,
                "attempts": 1,
                "follow_up_calls": 0,
            }
            if case_id == "refusal-delivered":
                expected_caller.update(outcome="business-reject", rejection_code="SETTLEMENT_NOT_COMMITTED")
            self.assertTrue(_same(caller, expected_caller), f"{case_id} caller outcome: {caller!r}")
            outcomes.append(caller["outcome"])
        return outcomes

    def assert_unavailable_bindings(self, index, documents):
        self.assertEqual(index["unpublished_reads_ref"], f"{BINDING}#/readQueries/items")
        self.assertEqual(index["recovery_ref"], f"{GRANTS}#/cases/27")
        reads = _resolve(documents, index["unpublished_reads_ref"])
        self.assertTrue(_same(documents[BINDING]["readQueries"]["count"], 13))
        read_names = Counter(item["name"] for item in reads)
        self.assertEqual(len(read_names), 13, "unique unpublished reads")
        self.assertEqual(len(reads), 13, "unpublished read count")
        for item in reads:
            self.assertEqual(item["status"], "NOT_BOUND", item["name"])

        grant_cases = documents[GRANTS]["cases"]
        read_cases = [case for case in grant_cases if case["request"]["kind"] == "read"]
        self.assertEqual(Counter(case["request"]["name"] for case in read_cases), read_names)
        for case in read_cases:
            self.assertEqual(case["expect"], NOT_BOUND, case["id"])

        recovery = _resolve(documents, index["recovery_ref"])
        matches = [case for case in grant_cases if case["request"]["kind"] == "proposed_recovery"]
        self.assertEqual(len(matches), 1)
        self.assertIs(recovery, matches[0])
        self.assertEqual(recovery["id"], "proposed-uncertain-operation-recovery")
        self.assertEqual(recovery["expect"], NOT_BOUND)

    def test_complete_index(self):
        self.assert_delivery_index(self.index)

    def test_duplicate_case_replacing_a_case(self):
        row = deepcopy(next(row for row in self.index["fixtures"] if row["fixture_path"] == REFUND))
        row["cases"][0] = deepcopy(row["cases"][1])
        with self.assertRaisesRegex(AssertionError, "index case coverage"):
            self.check_fixture(row, self.documents[REFUND])

    def test_crossed_pointers(self):
        row = next(row for row in self.index["fixtures"] if row["fixture_path"] == REFUSAL)
        for field, first_id, second_id, error in (
            ("caller_observation_ref", "loss-before-dispatch", "refusal-withheld-after-dispatch", "caller pointer"),
            ("producer_evidence_ref", "refusal-delivered", "refusal-withheld-after-dispatch", "producer pointer"),
        ):
            with self.subTest(field=field):
                crossed = deepcopy(row)
                cases = {case["case_id"]: case for case in crossed["cases"]}
                first, second = cases[first_id], cases[second_id]
                self.assertEqual(_resolve(self.documents, first[field]), _resolve(self.documents, second[field]))
                first[field], second[field] = second[field], first[field]
                with self.assertRaisesRegex(AssertionError, error):
                    self.check_fixture(crossed, self.documents[REFUSAL])

    def test_producer_evidence_cannot_replace_caller_observation(self):
        hidden_refund = self.documents[REFUND]["cases"][1]["producer_evidence"]["hidden_receipt_ref"]
        for path, substitute in (
            (REFUND, hidden_refund),
            (REFUSAL, f"{REFUSAL}#/cases/2/producer_evidence/refusal_codes/0"),
            (REFUND, f"{ADMISSION}#/expected_caller"),
        ):
            with self.subTest(path=path, substitute=substitute):
                documents = self.documents | {
                    receipt_path: _decode(_read(receipt_path)) for receipt_path in self.receipt_pins
                }
                self.assertIsNotNone(_resolve(documents, substitute))
                row = deepcopy(next(row for row in self.index["fixtures"] if row["fixture_path"] == path))
                withheld = next(case for case in row["cases"] if case["fault_point"] == "after_dispatch")
                withheld["caller_observation_ref"] = substitute
                with self.assertRaisesRegex(AssertionError, "caller pointer"):
                    self.check_fixture(row, self.documents[path])

    def test_unavailable_bindings(self):
        self.assert_unavailable_bindings(self.index, self.documents)

    def test_missing_or_promoted_bindings(self):
        binding = deepcopy(self.documents[BINDING])
        del binding["readQueries"]["items"][0]
        with self.assertRaisesRegex(AssertionError, "unique unpublished reads"):
            self.assert_unavailable_bindings(self.index, self.documents | {BINDING: binding})

        binding = deepcopy(self.documents[BINDING])
        binding["readQueries"]["items"][0]["status"] = "SEMANTIC_CONFORMANCE"
        with self.assertRaisesRegex(AssertionError, "NOT_BOUND"):
            self.assert_unavailable_bindings(self.index, self.documents | {BINDING: binding})

        grants = deepcopy(self.documents[GRANTS])
        grants["cases"][27]["expect"] = {"status": "SEMANTIC_CONFORMANCE", "vector_id": "made-up"}
        with self.assertRaisesRegex(AssertionError, "NOT_BOUND"):
            self.assert_unavailable_bindings(self.index, self.documents | {GRANTS: grants})
