"""Test-only fixture paths and assertions for Commerce tuple replay."""

from .mock_gates import _canonical as canonical

TABLE = "docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json"
VECTORS = "sdk/conformance/vectors/commerce-fixture-tuple.vectors.json"
INPUTS = "reference/booking_resale_admission/fixtures/commerce_journey_conformance_v1.json"
RECEIPTS = "reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json"
MARKET_RECEIPTS = "reference/booking_resale_admission/fixtures/commerce_market_full_receipts_v1.json"
BOOKING_BRANCH_RECEIPTS = "reference/booking_resale_admission/fixtures/commerce_booking_branch_receipts_v1.json"


def snapshot(host):
    return {
        name: (machine.canonical_state(), machine.export_journal())
        for name, machine in host.machines.items()
    }


def resolve_receipt_ref(test, vector, golden_steps):
    index = vector["input_index"]
    test.assertEqual(vector["expected"]["receipt_ref"], f"{RECEIPTS}#/steps/{index}/receipt")
    golden = golden_steps[index]
    test.assertEqual(golden["action"], vector["envelope"]["action"])
    return golden["receipt"]


def check_journal(test, spec, body, before, after, deltas):
    machine = spec["machine"]
    test.assertEqual(deltas.get(machine), 1)
    test.assertEqual(before.keys(), after.keys())
    test.assertTrue(deltas.keys() <= after.keys())
    for name, (state, journal) in after.items():
        old_state, old_journal = before[name]
        delta = deltas.get(name, 0)
        test.assertEqual(len(journal) - len(old_journal), delta, name)
        test.assertEqual(canonical(journal[:len(old_journal)]), canonical(old_journal), name)
        if delta == 0:
            test.assertEqual(state, old_state, name)
    entry = after[machine][1][-1]
    test.assertEqual(entry["op"], spec["op"])
    test.assertEqual(entry["idempotency_key"], body["idempotency_key"],
                     f"{machine} journal idempotency key")
    subject_key = "settlement_id" if machine == "settlement" else "subject_id"
    test.assertEqual(entry[subject_key], body[spec["subject_field"]])
