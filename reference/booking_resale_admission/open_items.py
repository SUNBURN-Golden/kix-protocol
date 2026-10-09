"""Draft 0.2 records the owner adoption of the unfilled mock boundary.

Revision `BRA-OPEN-ITEMS-DRAFT-0.2`. JunTae adopted option A on 2026-10-09.
The reference module stays unfilled. Policy numbers stay UNDETERMINED.
This module does not authenticate actors, store a ShowConfig, approve a TTL,
apply a discount, consult payment attesters, define compensation, pay a
seller, or add a protocol command.
"""

from __future__ import annotations

REVISION = "BRA-OPEN-ITEMS-DRAFT-0.2"
CONTRACT_VERSION = "0.2"
MOCK_BOUNDARY = "UNFILLED"
ADOPTED_OPTION = "A"
ADOPTION_DECIDER = "JunTae"
ADOPTION_DATE = "2026-10-09"
POLICY_NUMBER_STATUS = "UNDETERMINED"

FORBIDDEN_COMMANDS = frozenset(
    {
        "authenticate",
        "revoke_actor",
        "revoke",
        "refund",
        "shield",
        "gift",
        "cancel_show",
        "consume_private",
        "delegate_session",
    }
)

_OPTION_KEYS = ("A", "B", "C")


def _item(
    item_id: str,
    *,
    recommendation: str,
    options: dict,
    current_refusal: tuple,
    non_claim_flags: tuple,
    forbidden_commands: tuple,
    observed_fixture: dict | None,
    undetermined: tuple,
    covered_by: tuple,
) -> dict:
    if recommendation != ADOPTED_OPTION or set(options) != set(_OPTION_KEYS):
        raise RuntimeError("MOCK_INVARIANT")
    return {
        "id": item_id,
        "mock_boundary": MOCK_BOUNDARY,
        "adopted_option": ADOPTED_OPTION,
        "adoption_decider": ADOPTION_DECIDER,
        "adoption_date": ADOPTION_DATE,
        "decided_value": None,
        "policy_number_status": POLICY_NUMBER_STATUS,
        "recommendation": recommendation,
        "options": options,
        "current_refusal": current_refusal,
        "non_claim_flags": non_claim_flags,
        "forbidden_commands": forbidden_commands,
        "observed_fixture": observed_fixture,
        "undetermined": undetermined,
        "covered_by": covered_by,
    }


def _undetermined(topic: str, owner: str) -> dict:
    if not topic.strip() or not owner.strip():
        raise RuntimeError("MOCK_INVARIANT")
    return {"topic": topic, "status": "UNDETERMINED", "owner": owner}


ITEMS = (
    _item(
        "actor-authentication-revocation",
        recommendation="A",
        options={
            "A": "Role labels are not authority. This mock does not authenticate or revoke them.",
            "B": "Accept a caller-supplied proof and authenticate in memory. That chooses an auth scheme.",
            "C": "Bind labels to an external identity provider. Credentials, a public endpoint, and KYC stay locked.",
        },
        current_refusal=(),
        non_claim_flags=("role_authenticated", "organizer_authenticated"),
        forbidden_commands=("authenticate", "revoke_actor", "revoke"),
        observed_fixture=None,
        undetermined=(
            _undetermined(
                "legal treatment of identity and KYC for role labels",
                "사용자와 법률·개인정보 담당",
            ),
        ),
        covered_by=(
            "test_mock_gates.GateTests.test_primary_reservation_order_and_issuance_evidence",
        ),
    ),
    _item(
        "durable-show-config",
        recommendation="A",
        options={
            "A": "ShowConfig stays in process memory. durable remains false.",
            "B": "Persist on a later local backend. Stage 5 and the storage-engine lock come first.",
            "C": "Treat the chain Show as the durable config. This mock does not claim chain finality.",
        },
        current_refusal=(),
        non_claim_flags=("durable",),
        forbidden_commands=(),
        observed_fixture=None,
        undetermined=(),
        covered_by=(
            "test_mock_gates.GateTests.test_primary_reservation_order_and_issuance_evidence",
        ),
    ),
    _item(
        "approved-reservation-ttl",
        recommendation="A",
        options={
            "A": "Keep 900_000ms and 120_000ms as named fixtures. Neither number is an approved product TTL.",
            "B": "Astra names a product reservation TTL in milliseconds. This revision supplies no number.",
            "C": "Adopt lifecycle reservationSeconds 1..900. That changes the unit and is a product policy.",
        },
        current_refusal=("RESERVATION_WINDOW", "LISTING_WINDOW", "ADMISSION_WINDOW"),
        non_claim_flags=(),
        forbidden_commands=(),
        observed_fixture={
            "reservation_window_ms": 900_000,
            "admission_window_ms": 120_000,
            "source": "rights offer and authorize_admission constants",
            "approved": False,
        },
        undetermined=(
            _undetermined(
                "whether a statute sets a maximum hold",
                "사용자와 법률 담당",
            ),
        ),
        covered_by=("test_mock_gates.GateTests.test_show_registration_bounds",),
    ),
    _item(
        "discounts-and-coupons",
        recommendation="A",
        options={
            "A": "The order amount must equal primary_price. This mock does not apply a discount or coupon.",
            "B": "Reduce the amount by a caller-supplied discount. That chooses a pricing policy.",
            "C": "Recompute a quote through reference/v0.3-rc1/commerce.py. This mock does not.",
        },
        current_refusal=("PRIMARY_PRICE_MISMATCH",),
        non_claim_flags=("discount_applied", "quote_policy_approved"),
        forbidden_commands=(),
        observed_fixture=None,
        undetermined=(
            _undetermined(
                "tax and accounting treatment of discounts and coupons",
                "사용자와 세무·회계 담당",
            ),
        ),
        covered_by=(
            "test_mock_gates.GateTests.test_price_binding_rejects_mismatch_and_conflicting_replay",
            "test_reservation_fsm.ReservationFsmTests.test_unbound_issue_is_memory_evidence_without_economic_finality",
        ),
    ),
    _item(
        "payment-attesters-authority",
        recommendation="A",
        options={
            "A": "An injected 32-byte fact is an observation, not attester authority. There is no attester set.",
            "B": "Reject a fact that a configured attester set did not sign. This revision builds no allowlist.",
            "C": "Call Toss or a live PG to attest. Live PG calls stay locked.",
        },
        current_refusal=(),
        non_claim_flags=("provider_fact_live",),
        forbidden_commands=(),
        observed_fixture={"register_show_accepts_payment_attesters": False},
        undetermined=(
            _undetermined(
                "Toss attester and webhook signature meaning",
                "사용자와 토스 기술 담당 (I02, I04)",
            ),
        ),
        covered_by=(),
    ),
    _item(
        "compensation-after-payment-fact",
        recommendation="A",
        options={
            "A": "Keep COMPENSATION_UNDEFINED. Create no compensation, refund, or inventory-return record.",
            "B": "Add a mock compensation state that is not a refund obligation. That is a new state.",
            "C": "Define a refund obligation and an inventory return. This revision does not create a legal duty.",
        },
        current_refusal=("COMPENSATION_UNDEFINED",),
        non_claim_flags=("compensation_defined",),
        forbidden_commands=(),
        observed_fixture=None,
        undetermined=(
            _undetermined(
                "legal refund obligation after a payment fact",
                "사용자와 법률 담당",
            ),
            _undetermined(
                "accounting treatment of that obligation",
                "사용자와 회계 담당",
            ),
        ),
        covered_by=(
            "test_mock_gates.GateTests.test_payment_fact_is_not_funds_and_expiry_does_not_compensate",
            "test_reservation_fsm.ReservationFsmTests.test_cancel_before_payment_frees_and_payment_blocks_compensation",
        ),
    ),
    _item(
        "resale-failure-compensation-seller-payout",
        recommendation="A",
        options={
            "A": "Keep the face-value split and the refusal. seller_due is not a seller payout.",
            "B": "Record a mock seller payable. That chooses a payout policy.",
            "C": "Call settlement distribute. This mock does not call settlement commands, and a live payout stays locked.",
        },
        current_refusal=("LISTING_NOT_OPEN", "COMPENSATION_UNDEFINED"),
        non_claim_flags=("funds_executed", "compensation_defined"),
        forbidden_commands=(),
        observed_fixture={"seller_due_is_payout": False},
        undetermined=(
            _undetermined(
                "legal, tax, and accounting treatment of a seller payout",
                "사용자와 법률·세무·회계 담당",
            ),
            _undetermined(
                "merchant scope of resale proceeds",
                "사용자와 토스 영업 담당 (I03)",
            ),
        ),
        covered_by=(
            "test_mock_gates.GateTests.test_resale_listing_transfer_records_allocation_face_only",
            "test_resale_fsm.ResaleFsmTests.test_stale_listing_policy_and_expiry_do_not_transfer",
            "test_resale_fsm.ResaleFsmTests.test_buy_hold_is_optional_and_cancel_order_decides_the_race",
        ),
    ),
    _item(
        "refund-revoke-shield-gift-cancel-show",
        recommendation="A",
        options={
            "A": "Do not add refund, revoke, shield, gift, or cancel_show. Generation stays 1.",
            "B": "Add those names as mock transitions. They would be new protocol commands.",
            "C": "Alias them onto cancel or consume. That redefines commands this revision does not redefine.",
        },
        current_refusal=("CANCEL_AFTER_ISSUE", "COMPENSATION_UNDEFINED"),
        non_claim_flags=(),
        forbidden_commands=("refund", "revoke", "shield", "gift", "cancel_show"),
        observed_fixture={"generation": 1},
        undetermined=(
            _undetermined(
                "legal effect of refund, revocation, and show cancellation",
                "사용자와 법률 담당",
            ),
        ),
        covered_by=(
            "test_mock_gates.GateTests.test_primary_reservation_order_and_issuance_evidence",
            "test_reservation_fsm.ReservationFsmTests.test_cancel_after_issue_and_duplicate_consume",
        ),
    ),
    _item(
        "consume-private-delegated-sessions",
        recommendation="A",
        options={
            "A": "Keep the public authorize and consume path. No private proof and no delegated session.",
            "B": "Set private_proof_verified from a caller-supplied blob. That claims a verification this mock does not perform.",
            "C": "Run zk_gate consume_private or open a delegated session. That is new auth semantics.",
        },
        current_refusal=(),
        non_claim_flags=("private_proof_verified",),
        forbidden_commands=("consume_private", "delegate_session"),
        observed_fixture=None,
        undetermined=(
            _undetermined(
                "privacy treatment of a delegated session",
                "사용자와 법률·개인정보 담당",
            ),
        ),
        covered_by=(
            "test_admission_fsm.AdmissionFsmTests.test_catalogue_has_no_new_admission_command",
            "test_admission_fsm.AdmissionFsmTests.test_external_sources_fail_closed_without_being_read",
        ),
    ),
)


def item(item_id: str) -> dict:
    for row in ITEMS:
        if row["id"] == item_id:
            return row
    raise KeyError(item_id)


def forbidden_commands() -> frozenset:
    names = set(FORBIDDEN_COMMANDS)
    for row in ITEMS:
        names.update(row["forbidden_commands"])
    return frozenset(names)
