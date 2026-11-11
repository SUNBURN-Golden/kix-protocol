"""Self-check for the committed read-model candidate fixture vectors.

Replays the generate_fixtures.py scenario into fresh machines and asserts:

- the committed JSON bytes are reproduced exactly (deterministic seed);
- every point-query expected `ok` body equals the live `view*` output, and
  every error vector raises the stored code on the recorded machine;
- every list population, page and cursor case matches the recomputed
  fixture model (FIXTURE_CURSOR_V1);
- the five ReadObservationV1 keys and the section-6 candidates
  (subject_scope, profile_revision) are absent from every vector;
- the always-false NON_CLAIMS / credit _flags stay false in every `ok`
  body, and no ok envelope is missing accepted_through;
- the vector calls do not mutate: canonical_state(), export_journal() and
  logical_time_ms are unchanged across each view call (RMQ section 8).

These are candidate fixtures only: the read-model implementation is not
merged and this file asserts equality with the current in-memory FSM
views, not conformance to a decided read model.
"""

import json
import sys
import unittest
from pathlib import Path

_DIR = Path(__file__).resolve().parent
for _rel in (
    _DIR,
    _DIR.parent / "settlement_f01_f03",
    _DIR.parent / "credit_advance_f04",
    _DIR.parent / "read_model",
):
    if str(_rel) not in sys.path:
        sys.path.insert(1, str(_rel))  # Keep this suite first for default discovery.

import generate_fixtures as fx  # noqa: E402
from mock_gates import NON_CLAIMS  # noqa: E402
from mock_credit import _flags as credit_flags  # noqa: E402

VECTORS = _DIR.parent / "read_model" / "vectors"

ALWAYS_FALSE = set(NON_CLAIMS) | set(credit_flags()) | {
    "economic_finality_claimed",
    "chain_issued",
    "venue_credential_reissued",
    "offline_admission",
    "admission_routing_production",
    "funds_executed",
    "bank_debit_observed",
    "legal_debtor_bound",
    "admission_granted",
    "provider_authorization_executed",
    "durable",
    "right_cancelled",
    "external_return_closed",
    "chain_owner_current",
    "cross_channel_exclusive",
    "ownership_mutated",
    "ticket_ownership_authoritative",
    "underwriting_executed",
    "kyc_executed",
    "buyer_evidence_available",
    "mock_settlement_commit_observed_off",  # sentinel never present; guards set algebra
}
ALWAYS_FALSE.discard("mock_settlement_commit_observed_off")


def _walk(value):
    if type(value) is dict:
        for k, v in value.items():
            yield k, v
            yield from _walk(v)
    elif type(value) is list:
        for item in value:
            yield from _walk(item)


class ReadModelFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, cls.S = fx.build_documents()
        cls.committed = {
            name: (VECTORS / name).read_text(encoding="utf-8")
            for name in (
                "reservation.json",
                "resale.json",
                "admission.json",
                "settlement.json",
                "credit.json",
                "manifest.json",
            )
        }

    def test_committed_bytes_are_reproduced(self):
        for name, doc in self.docs.items():
            self.assertEqual(self.committed[name], fx._canonical(doc) + "\n", name)

    def test_manifest_sha256_matches_committed_files(self):
        manifest = json.loads(self.committed["manifest.json"])
        import hashlib

        for name, meta in manifest["files"].items():
            digest = hashlib.sha256(self.committed[name].encode("utf-8")).hexdigest()
            self.assertEqual(meta["sha256"], digest, name)

    def test_every_expected_answer_replays_against_the_generating_model(self):
        """Each stored vector equals what the live machines answer now."""
        machines = self.S["machines"]
        dispatch = {
            ("reservation", "get_show"): ("reservation", "view_show"),
            ("reservation", "get_booking"): ("reservation", "view"),
            ("resale", "get_right"): ("resale", "view_right"),
            ("resale", "get_presentation"): ("resale", "view_presentation"),
            ("resale", "get_listing"): ("resale", "view"),
            ("admission", "get_admission"): ("admission", "view"),
            ("admission", "get_credential"): (None, "view_credential"),
            ("settlement", "get_settlement"): ("settlement", "view"),
            ("credit", "get_credit_advance"): ("credit", "view"),
            ("credit", "get_credit_claim"): ("credit", "view_claim"),
        }
        checked = 0
        for name in ("reservation", "resale", "admission", "settlement", "credit"):
            doc = self.docs[name + ".json"]
            for qname, query in doc["queries"].items():
                if query["kind"] != "point":
                    continue
                machine_key, method = dispatch[(name, qname)]
                for vector in query["vectors"]:
                    machine = machines[machine_key or vector.get("fixture_machine", "admission")]
                    call = getattr(machine, method)
                    before = (
                        machine.canonical_state(),
                        machine.export_journal(),
                        getattr(machine, "_now", None),
                    )
                    try:
                        body = call(vector["input"]["subject_id"], **vector["input"]["kwargs"])
                    except fx.POINT_ERRORS as error:
                        expected = {"error_code": error.code, "error_kind": type(error).__name__}
                    else:
                        expected = {"ok": fx._envelope(
                            machine, qname,
                            {"actor": vector["actor"],
                             "kwargs": vector["input"]["kwargs"],
                             "query": qname,
                             "subject_id": vector["input"]["subject_id"]},
                            body)}
                    after = (
                        machine.canonical_state(),
                        machine.export_journal(),
                        getattr(machine, "_now", None),
                    )
                    self.assertEqual(before, after, (name, qname, vector["input"]))
                    self.assertEqual(vector["expected"], expected, (name, qname, vector["input"]))
                    checked += 1
        self.assertGreaterEqual(checked, 40)

    def test_list_pages_and_cursor_cases_recompute(self):
        for name, query in (
            ("reservation", "list_shows"),
            ("reservation", "list_bookings"),
            ("resale", "list_open_listings"),
        ):
            doc = self.docs[name + ".json"]["queries"][query]
            for page in doc["pages"]:
                expected = page["expected"]
                scope = page["scope"]
                machine = self.S["machines"]["reservation" if name == "reservation" else "resale"]
                canonical = json.loads(machine.canonical_state())
                rows = canonical["shows" if query == "list_shows"
                                 else "reservations" if query == "list_bookings"
                                 else "listings"]
                keys = (fx.SHOW_SUMMARY_KEYS if query == "list_shows"
                        else fx.BOOKING_SUMMARY_KEYS if query == "list_bookings"
                        else fx.LISTING_SUMMARY_KEYS)
                filt = page["input"]["filters"]
                if filt and (set(filt) - {"buyer_role"} or not all(fx._ident_ok(v) for v in filt.values())):
                    self.assertEqual(expected["error_kind"], "INVALID_ID")
                    continue
                rows = [r for r in rows if all(r.get(k) == v for k, v in filt.items())]
                try:
                    body = fx.expected_page(
                        query, scope, [{k: r[k] for k in keys} for r in rows],
                        fx._snapshot(machine),
                        fixture_limit=page["input"]["fixture_limit"],
                        cursor=page["input"]["cursor"],
                    )
                except fx.FixtureQueryError as error:
                    self.assertEqual(expected["error_kind"], error.kind, (query, page["input"]))
                else:
                    self.assertEqual(expected["ok"]["body"], body, (query, page["input"]))
            for case in doc["cursor_cases"]:
                machine = self.S["machines"]["reservation" if name == "reservation" else "resale"]
                canonical = json.loads(machine.canonical_state())
                rows = canonical["shows" if query == "list_shows"
                                 else "reservations" if query == "list_bookings"
                                 else "listings"]
                keys = (fx.SHOW_SUMMARY_KEYS if query == "list_shows"
                        else fx.BOOKING_SUMMARY_KEYS if query == "list_bookings"
                        else fx.LISTING_SUMMARY_KEYS)
                try:
                    body = fx.expected_page(
                        query, doc["scopes"][0] if "scopes" in doc else doc["pages"][0]["scope"],
                        [{k: r[k] for k in keys} for r in rows],
                        fx._snapshot(machine),
                        fixture_limit=2, cursor=case["input"]["cursor"],
                    )
                except fx.FixtureQueryError as error:
                    self.assertEqual(case["expected"]["error_kind"], error.kind, case["name"])
                else:
                    self.assertEqual(case["expected"]["ok"]["body"], body, case["name"])

    def test_reserved_envelope_keys_absent_and_flags_false(self):
        for name, doc in self.docs.items():
            for key, value in _walk(doc):
                self.assertNotIn(key, fx.RESERVED_KEYS, (name, key))
        for name in ("reservation", "resale", "admission", "settlement", "credit"):
            doc = self.docs[name + ".json"]
            for qname, query in doc["queries"].items():
                vectors = query.get("vectors", []) + query.get("pages", [])
                for vector in vectors:
                    expected = vector["expected"]
                    if "ok" not in expected:
                        continue
                    ok = expected["ok"]
                    self.assertEqual(ok["read_schema_version"], fx.READ_SCHEMA_VERSION)
                    self.assertEqual(ok["fixture_mode"], fx.FIXTURE_MODE)
                    self.assertEqual(ok["query_digest"], fx.NOT_BOUND)
                    self.assertIn("journal_entries", ok["accepted_through"])
                    if name in ("reservation", "resale", "admission"):
                        self.assertIn("logical_time_ms", ok["accepted_through"])
                    else:
                        self.assertNotIn("logical_time_ms", ok["accepted_through"])
                    for key, value in _walk(ok["body"]):
                        if key in ALWAYS_FALSE:
                            self.assertIs(value, False, (name, qname, key))

    def test_two_replays_are_byte_identical(self):
        docs2, _ = fx.build_documents()
        for name in self.docs:
            self.assertEqual(fx._canonical(self.docs[name]), fx._canonical(docs2[name]), name)

    def test_open_phase_predicate_stays_not_bound(self):
        doc = self.docs["resale.json"]["queries"]["list_open_listings"]
        self.assertEqual(doc["open_phase_predicate"], fx.NOT_BOUND)
        self.assertEqual(doc["visibility"]["value"], fx.NOT_BOUND)
        for name in ("reservation", "resale"):
            for qname, query in self.docs[name + ".json"]["queries"].items():
                if query["kind"] == "list":
                    self.assertEqual(query["visibility"]["value"], fx.NOT_BOUND)
                    self.assertEqual(
                        query["visibility"]["recommended_subset"]["label"],
                        fx.RECOMMENDATION,
                    )


if __name__ == "__main__":
    unittest.main()
