"""Builder-authored offline BRA normalization probes; synthetic fixtures only.

BOOKING_RESALE_ADMISSION_GATES §§9.4, 10.7, 11.5 define normalized live replay
and restored-state equality (A). Retry responses after restore are not explicitly
specified there: those comparisons are contract undefined (class B).
Owner policy values remain UNDETERMINED; no ticket/settlement source is bound.
"""

from copy import deepcopy
import unittest

from reservation_fsm import ReservationError, ReservationMachine
from resale_fsm import ResaleError, ResaleMachine
from admission_fsm import AdmissionError, AdmissionMachine
from bra_property_support import PRICE, SHOW, ORGANIZER, hex_ref
from mock_gates import OFFER_WINDOW_MS, ADMISSION_WINDOW_MS

ERROR = (ReservationError, ResaleError, AdmissionError)

DUPLICATE = ("ok", True, None)
CONFLICT = ("error", "IDEMPOTENCY_CONFLICT")


def outcome(fn):
    try:
        result = fn()
    except ERROR as error:
        return ("error", error.code)
    return ("ok", result["duplicate"], result["applied"])


def invoke(machine, command):
    op, subject, body = deepcopy(command)
    return getattr(machine, op)(subject, **body)


def probe(test, factory, restore, first, retries):
    machine = factory()
    test.assertEqual(outcome(lambda: invoke(machine, first)), ("ok", False, first[0]))
    state, journal = machine.canonical_state(), machine.export_journal()
    for retry, expected in retries:
        with test.subTest(first=first, retry=retry):
            test.assertEqual(outcome(lambda: invoke(machine, retry)), expected)
            test.assertEqual(machine.canonical_state(), state)
            test.assertEqual(machine.export_journal(), journal)
            restored = restore(deepcopy(journal))
            test.assertEqual(restored.canonical_state(), state)
            test.assertEqual(restored.state_digest(), machine.state_digest())
            test.assertEqual(outcome(lambda: invoke(restored, retry)), expected)
            test.assertEqual(restored.canonical_state(), state)
            test.assertEqual(restored.export_journal(), journal)


def command(op, subject, **body):
    return op, subject, dict(idempotency_key="probe", **body)


T0 = 1_000_000
EXPIRES = T0 + OFFER_WINDOW_MS


def show_body():
    return dict(organizer_role=ORGANIZER, capacity=2, gate_roles=["gate"],
                primary_price=PRICE, resale_cap=20_000, resale_allowed=True,
                organizer_bps=1, platform_bps=1)


def adopt_body():
    return dict(show_body(), show_id=SHOW, slot=0, buyer_role="buyer",
                expires_ms=EXPIRES, order_id="order", amount=PRICE, payment_ref=hex_ref(1))


def listing_body():
    return dict(right_id="right", version=1, seller_role="buyer", recipient_role="recipient",
                amount=PRICE, expires_ms=EXPIRES)


def authorization_body():
    return dict(right_id="right", version=1, holder_role="buyer", gate_role="gate",
                request=hex_ref(3), expires_ms=T0 + ADMISSION_WINDOW_MS)


def fixture(cls, stage):
    machine = cls()
    machine.set_clock("clock", idempotency_key="clock", now_ms=T0)
    if cls is ReservationMachine:
        machine.register_show(SHOW, idempotency_key="show", **show_body())
        machine.hold("reservation", idempotency_key="hold", show_id=SHOW, slot=0,
                     buyer_role="buyer", expires_ms=EXPIRES)
    elif stage != "empty":
        machine.adopt_issued("right", idempotency_key="adopt", **adopt_body())
        if stage == "listed":
            machine.list_resale("listing", idempotency_key="list", **listing_body())
        if stage == "authorized":
            machine.authorize_admission("admission", idempotency_key="authorize", **authorization_body())
    return machine


class VariantChecks:
    def check_variants(self, cls, stage, op, subject, body, field, control=None):
        variants = [command(op, subject, **body), command(op, subject, **body, **{field: None})]
        if control is not None:
            variants.append(command(op, subject, **body, **{field: control}))
        for index, first in enumerate(variants):
            retries = [(retry, DUPLICATE if index < 2 and n < 2 or index == n else CONFLICT)
                       for n, retry in enumerate(variants)]
            probe(self, lambda: fixture(cls, stage), cls.restore, first, retries)


class ReservationRestoreFingerprintCharacterizationTests(VariantChecks, unittest.TestCase):
    """§9.4 live replay/state restore A; post-restore retry contract undefined (B)."""

    def test_confirm_quote_ref(self):
        self.check_variants(ReservationMachine, "held", "confirm", "order",
                            dict(reservation_id="reservation", amount=PRICE), "quote_ref", "quote-1")


class ResaleRestoreFingerprintCharacterizationTests(VariantChecks, unittest.TestCase):
    """§10.7 live replay/state restore A; post-restore retry contract undefined (B)."""

    def test_adopt_optional_binding_fields(self):
        for field in ("reservation_id", "quote_ref"):
            self.check_variants(ResaleMachine, "empty", "adopt_issued", "right", adopt_body(), field)

    def test_list_resale_reservation_id(self):
        self.check_variants(ResaleMachine, "adopted", "list_resale", "listing", listing_body(), "reservation_id")

    def test_listed_payment_buyer_role(self):
        self.check_variants(ResaleMachine, "listed", "observe_resale_payment", "listing",
                            dict(payment_ref=hex_ref(2), amount=PRICE), "buyer_role")


class AdmissionRestoreFingerprintCharacterizationTests(VariantChecks, unittest.TestCase):
    """§11.5 live replay/state restore A; post-restore retry contract undefined (B)."""

    def test_adopt_optional_binding_fields(self):
        for field in ("reservation_id", "quote_ref"):
            self.check_variants(AdmissionMachine, "empty", "adopt_issued", "right", adopt_body(), field)

    def test_authorize_external_dependency(self):
        self.check_variants(AdmissionMachine, "adopted", "authorize_admission", "admission",
                            authorization_body(), "external_dependency")

    def test_consume_external_dependency(self):
        body = dict(right_id="right", version=1, gate_role="gate", request=hex_ref(3))
        self.check_variants(AdmissionMachine, "authorized", "consume", "consume", body, "external_dependency")


if __name__ == "__main__":
    unittest.main()
