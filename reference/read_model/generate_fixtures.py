"""Deterministic candidate fixture vectors for the approved read-model queries.

Generates committed JSON expected-answer vectors for the 13 owner-decided
query names in docs/contracts/READ_MODEL_QUERIES.md draft 0.1:

    list_shows, get_show, get_booking, list_bookings,
    get_right, get_presentation, list_open_listings, get_listing,
    get_admission, get_credential,
    get_settlement, get_credit_advance, get_credit_claim.

The vectors are CANDIDATE EVIDENCE ONLY. The read-model implementation
(program node `read-model-reference`) is not merged; these fixtures are not
conformance evidence. There is no query implementation here: point-query
answers are the literal dicts the existing `view*` methods return, and
list-query answers come from a fixture-side page/cursor model marked
FIXTURE_CURSOR_V1. Every value the contract leaves UNDETERMINED stays
NOT_BOUND: the open-listing phase predicate, limit default/cap, cursor
lifetime, sort key, visibility matrix values, cursor/snapshot error code
names and the query_digest hash algorithm. The five ReadObservationV1 keys
(source_cut, projection_watermark, snapshot_digest, observed_receipt_refs,
producer_manifest_digest) and the section-6 candidates subject_scope and
profile_revision are RESERVED and absent from every emitted vector.

Fixture helpers are named `expected_*`; no `def list_shows(`,
`def list_bookings(` or `def list_open_listings(` exists in this file, so
the READ_MODEL_SOURCE_MAP.md absence anchors keep their meaning.

Determinism: every nondeterministic-looking input is derived from
`random.Random(SEED)`; iteration is sorted-only; output uses the machines'
own canonical JSON convention (mock_gates.py `json.dumps(sort_keys=True,
ensure_ascii=False, separators=(",",":"), allow_nan=False)`). Re-running
`generate_fixtures.py` (or `--check`) reproduces the committed bytes.
Standard library only; no network, no wall clock.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _rel in (
    "reference/booking_resale_admission",
    "reference/settlement_f01_f03",
    "reference/credit_advance_f04",
):
    _path = str(ROOT / _rel)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from admission_fsm import AdmissionError, AdmissionMachine  # noqa: E402
from credit_fsm import CreditError, CreditMachine  # noqa: E402
from mock_gates import ADMISSION_WINDOW_MS, OFFER_WINDOW_MS  # noqa: E402
from reservation_fsm import ReservationError, ReservationMachine  # noqa: E402
from resale_fsm import ResaleError, ResaleMachine  # noqa: E402
from settlement_fsm import SettlementError, SettlementMachine  # noqa: E402

SEED = 20261020
FIXTURE_VERSION = "0.1"
READ_SCHEMA_VERSION = "0.1"
FIXTURE_MODE = "REFERENCE_IN_MEMORY"
ORDERING = "identifier-asc"
ORDERING_LABEL = "FIXTURE_ORDERING identifier-asc; sort key UNDETERMINED"
CURSOR_FORMAT = "FIXTURE_CURSOR_V1"
NOT_BOUND = "NOT_BOUND"
RECOMMENDATION = "RECOMMENDATION_NOT_DECISION"

# Keys reserved for ReadObservationV1 (READ_MODEL_QUERIES.md section 3) and
# the section-6 candidates that share the same owner. They must never appear
# in an emitted vector; the stdlib self-check asserts their absence.
RESERVED_KEYS = frozenset(
    {
        "source_cut",
        "projection_watermark",
        "snapshot_digest",
        "observed_receipt_refs",
        "producer_manifest_digest",
        "subject_scope",
        "profile_revision",
    }
)

QUERY_NAMES = (
    "list_shows",
    "get_show",
    "get_booking",
    "list_bookings",
    "get_right",
    "get_presentation",
    "list_open_listings",
    "get_listing",
    "get_admission",
    "get_credential",
    "get_settlement",
    "get_credit_advance",
    "get_credit_claim",
)

T0 = 1_000_000
PRICE_A = 10_001
PRICE_B = 5_000
RESALE_CAP = 20_000
FINAL_CLOCK = T0 + 500_000

SHOW_SUMMARY_KEYS = (
    "show_id",
    "currency",
    "capacity",
    "primary_price",
    "resale_allowed",
    "open",
)
BOOKING_SUMMARY_KEYS = (
    "reservation_id",
    "phase",
    "terminal",
    "show_id",
    "slot",
    "expires_ms",
    "expired",
)
LISTING_SUMMARY_KEYS = (
    "listing_id",
    "show_id",
    "amount",
    "currency",
    "expires_ms",
    "expired",
    "phase",
)

POINT_ERRORS = (
    ReservationError,
    ResaleError,
    AdmissionError,
    SettlementError,
    CreditError,
)


def _canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def _copy(value: object) -> object:
    return json.loads(_canonical(value))


class FixtureQueryError(Exception):
    """Modeled list-query rejection. The code name stays NOT_BOUND: the
    draft fixes no cursor/snapshot/limit error code name."""

    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind


def _ident_ok(value: object) -> bool:
    return type(value) is str and 0 < len(value) <= 100 and value.strip() == value


def _raiser(name):
    def _call(*_args, **_kwargs):
        raise RuntimeError("fixture source down: " + name)

    return _call


class _Down:
    """A source whose methods always fail without a protocol code, so the
    admission machine reports the matching *_SOURCE_UNAVAILABLE decision."""

    def __getattr__(self, name):
        return _raiser(name)


class _Breakable:
    """Delegating source that can be switched to fail closed."""

    def __init__(self, target):
        self._target = target
        self.down = False

    def __getattr__(self, name):
        if self.down:
            return _raiser(name)
        return getattr(self._target, name)


def _policy() -> dict:
    return {
        "kind": "PRIMARY_FEE_BPS",
        "fee_bps": 250,
        "residual_payee": "organizer-1",
        "fee_payee": "platform-1",
    }


def build_scenario(seed: int = SEED) -> dict:
    """Drive all five machines through public REPLAYABLE commands only.

    Returns the machine set plus the bookkeeping the vector builders need.
    Re-running with the same seed produces byte-identical journals, states
    and views.
    """
    rng = random.Random(seed)
    pay = lambda: f"{rng.getrandbits(256):064x}"  # noqa: E731
    req = lambda: f"{rng.getrandbits(256):064x}"  # noqa: E731
    key_i = iter(range(10_000))
    key = lambda name: f"fx-{next(key_i)}-{name}"  # noqa: E731

    settle = SettlementMachine()
    resv = ReservationMachine(settlement_source=settle)
    resale = ResaleMachine(ticket_source=resv, settlement_source=settle)
    adm = AdmissionMachine(
        ticket_source=resv, ownership_source=resale, settlement_source=settle
    )
    adm_venue = AdmissionMachine(ticket_source=resv, venue_source=object())
    adm_rev = AdmissionMachine(ticket_source=resv, revocation_source=object())
    adm_own = AdmissionMachine(ticket_source=resv, ownership_source=_Down())
    tick_break = _Breakable(resv)
    adm_tick = AdmissionMachine(ticket_source=tick_break)
    adm_settle_down = AdmissionMachine(ticket_source=resv, settlement_source=_Down())
    adm_settle_missing = AdmissionMachine(ticket_source=resv)
    credit = CreditMachine(settlement_source=settle)

    machines = {
        "reservation": resv,
        "resale": resale,
        "admission": adm,
        "admission_venue": adm_venue,
        "admission_revocation": adm_rev,
        "admission_ownership_down": adm_own,
        "admission_ticket_down": adm_tick,
        "admission_settlement_down": adm_settle_down,
        "admission_settlement_missing": adm_settle_missing,
        "settlement": settle,
        "credit": credit,
    }

    for name, machine in machines.items():
        if name in ("settlement", "credit"):
            continue  # these machines have no clock
        machine.set_clock("clock", idempotency_key=key(f"clock-{name}"), now_ms=T0)

    # --- settlement book: one case per phase variant --------------------
    policy = _policy()

    def book(sid: str, gross: int, stop: str) -> None:
        settle.initiate(
            sid,
            idempotency_key=key(f"init-{sid}"),
            trade_id=f"trade-{sid}",
            gross=gross,
            debtor_role="merchant-1",
            policy=policy,
        )
        if stop == "INITIATED":
            return
        settle.authorize(sid, idempotency_key=key(f"auth-{sid}"))
        settle.capture(sid, idempotency_key=key(f"cap-{sid}"))
        if stop == "CAPTURED":
            return
        fee = gross * policy["fee_bps"] // 10000
        settle.commit(
            sid,
            idempotency_key=key(f"commit-{sid}"),
            movement_id=f"move-{sid}",
            gross=gross,
            amount=gross - fee,
            fee=fee,
            tax=0,
            held=0,
            adjustment=0,
        )

    book("settle-1", PRICE_A, "COMMITTED")  # bound on resv-a1 -> MOCK_COMMIT_OBSERVED
    book("settle-2", 7_777, "CAPTURED")  # populated claim, not committed
    book("settle-3", 5_555, "INITIATED")  # claim null
    book("settle-adm", PRICE_A, "COMMITTED")  # bound on resv-a6
    book("settle-resale", 12_000, "COMMITTED")  # bound on listing list-r2
    book("settle-credit", 100_000, "COMMITTED")  # face + bind for adv-1

    # --- shows -----------------------------------------------------------
    resv.register_show(
        "show-a",
        idempotency_key=key("show-a"),
        organizer_role="organizer-1",
        capacity=12,
        gate_roles=["gate-a", "gate-b"],
        primary_price=PRICE_A,
        resale_cap=RESALE_CAP,
        resale_allowed=True,
        organizer_bps=100,
        platform_bps=50,
    )
    resv.register_show(
        "show-b",
        idempotency_key=key("show-b"),
        organizer_role="organizer-2",
        capacity=2,
        gate_roles=["gate-c"],
        primary_price=PRICE_B,
        resale_cap=1,
        resale_allowed=False,
        organizer_bps=0,
        platform_bps=0,
    )
    shows = {"show-a": PRICE_A, "show-b": PRICE_B}

    # --- reservation cases ------------------------------------------------
    reservations = []  # (reservation_id, show_id, slot, buyer, expires, stop)

    def hold(rid, show_id, slot, buyer, expires):
        resv.hold(
            rid,
            idempotency_key=key(f"hold-{rid}"),
            show_id=show_id,
            slot=slot,
            buyer_role=buyer,
            expires_ms=expires,
        )

    def issue_path(rid, show_id, slot, buyer, expires, settle_id=None):
        hold(rid, show_id, slot, buyer, expires)
        order = f"order-{rid}"
        resv.confirm(
            order,
            idempotency_key=key(f"confirm-{rid}"),
            reservation_id=rid,
            amount=shows[show_id],
        )
        resv.observe_payment(
            order,
            idempotency_key=key(f"pay-{rid}"),
            payment_ref=pay(),
            amount=shows[show_id],
        )
        if settle_id is not None:
            resv.bind_settlement(
                rid, idempotency_key=key(f"bind-{rid}"), settlement_id=settle_id
            )
        right = f"right-{rid.split('-', 1)[1]}"
        resv.issue(right, idempotency_key=key(f"issue-{rid}"), order_id=order)
        return right

    EXP = T0 + OFFER_WINDOW_MS
    right_a1 = issue_path("resv-a1", "show-a", 0, "buyer-1", EXP, settle_id="settle-1")
    right_a2 = issue_path("resv-a2", "show-a", 1, "buyer-2", EXP)
    hold("resv-a3", "show-a", 2, "buyer-1", T0 + 1)  # expired HELD at final clock
    hold("resv-a4", "show-a", 3, "buyer-3", T0 + 10)  # expired CONFIRMED at final clock
    resv.confirm(
        "order-resv-a4",
        idempotency_key=key("confirm-resv-a4"),
        reservation_id="resv-a4",
        amount=PRICE_A,
    )
    resv.bind_settlement(
        "resv-a4", idempotency_key=key("bind-resv-a4"), settlement_id="settle-2"
    )
    hold("resv-a5", "show-a", 4, "buyer-3", EXP)
    resv.confirm(
        "order-resv-a5",
        idempotency_key=key("confirm-resv-a5"),
        reservation_id="resv-a5",
        amount=PRICE_A,
    )
    resv.cancel("resv-a5", idempotency_key=key("cancel-resv-a5"))
    right_a6 = issue_path("resv-a6", "show-a", 5, "buyer-6", EXP, settle_id="settle-adm")
    right_a7 = issue_path("resv-a7", "show-a", 6, "buyer-7", EXP)
    right_a8 = issue_path("resv-a8", "show-a", 7, "buyer-8", EXP)
    right_a9 = issue_path("resv-a9", "show-a", 8, "buyer-9", EXP)
    right_a10 = issue_path("resv-a10", "show-a", 9, "buyer-10", EXP)
    right_a11 = issue_path("resv-a11", "show-a", 10, "buyer-11", EXP)
    right_a12 = issue_path("resv-a12", "show-a", 11, "buyer-12", EXP)
    right_a13 = issue_path("resv-a13", "show-a", 4, "buyer-13", EXP)  # freed slot 4
    hold("resv-b1", "show-b", 0, "buyer-2", EXP)
    reservations = [
        "resv-a1", "resv-a2", "resv-a3", "resv-a4", "resv-a5", "resv-a6",
        "resv-a7", "resv-a8", "resv-a9", "resv-a10", "resv-a11", "resv-a12",
        "resv-a13", "resv-b1",
    ]

    def adopt_body(rid):
        view = resv.view(rid)
        show = resv.view_show(view["show_id"])["show"]
        return {
            "show_id": view["show_id"],
            "organizer_role": show["organizer_role"],
            "capacity": show["capacity"],
            "gate_roles": list(show["gate_roles"]),
            "primary_price": show["primary_price"],
            "resale_cap": show["resale_cap"],
            "resale_allowed": show["resale_allowed"],
            "organizer_bps": show["organizer_bps"],
            "platform_bps": show["platform_bps"],
            "slot": view["slot"],
            "buyer_role": view["buyer_role"],
            "expires_ms": view["expires_ms"],
            "order_id": view["order_id"],
            "amount": view["amount"],
            "quote_ref": view["quote_ref"],
            "payment_ref": view["payment_ref"],
            "reservation_id": rid,
        }

    # --- resale: adopt rights and drive listings ---------------------------
    for rid in ("resv-a1", "resv-a6", "resv-a7", "resv-a8", "resv-a9",
                "resv-a10", "resv-a11", "resv-a13"):
        right = f"right-{rid.split('-', 1)[1]}"
        resale.adopt_issued(right, idempotency_key=key(f"resale-adopt-{rid}"), **adopt_body(rid))

    def list_resale(lid, rid, amount, expires=EXP, recipient=None):
        right = f"right-{rid.split('-', 1)[1]}"
        seller = resv.view(rid)["buyer_role"]
        resale.list_resale(
            lid,
            idempotency_key=key(f"list-{lid}"),
            right_id=right,
            version=1,
            seller_role=seller,
            recipient_role=recipient or f"buyer-{lid.split('-', 1)[1]}",
            amount=amount,
            expires_ms=expires,
            reservation_id=rid,
        )

    list_resale("list-r1", "resv-a1", 15_000, recipient="buyer-2")
    resale.hold_buy(
        "hold-r1",
        idempotency_key=key("hold-r1"),
        listing_id="list-r1",
        buyer_role="buyer-2",
    )
    resale.observe_resale_payment(
        "list-r1",
        idempotency_key=key("salepay-r1"),
        payment_ref=pay(),
        amount=15_000,
        buyer_role="buyer-2",
    )
    resale.accept_resale("transfer-r1", idempotency_key=key("transfer-r1"), listing_id="list-r1")
    resale.close("list-r1", idempotency_key=key("close-r1"))
    list_resale("list-r2", "resv-a8", 12_000, recipient="buyer-2x")
    resale.hold_buy(
        "hold-r2",
        idempotency_key=key("hold-r2"),
        listing_id="list-r2",
        buyer_role="buyer-2x",
    )
    resale.observe_resale_payment(
        "list-r2",
        idempotency_key=key("salepay-r2"),
        payment_ref=pay(),
        amount=12_000,
        buyer_role="buyer-2x",
    )
    resale.bind_settlement(
        "list-r2", idempotency_key=key("bind-r2"), settlement_id="settle-resale"
    )
    resale.accept_resale("transfer-r2", idempotency_key=key("transfer-r2"), listing_id="list-r2")
    list_resale("list-r3", "resv-a9", 9_000, recipient="buyer-3x")
    resale.cancel_listing(
        "list-r3", idempotency_key=key("cancel-r3"), seller_role="buyer-9"
    )
    list_resale("list-r4", "resv-a10", 11_000, expires=T0 + 100)  # expired at final clock
    list_resale("list-r5", "resv-a11", 13_000, recipient="buyer-5x")
    resale.hold_buy(
        "hold-r5",
        idempotency_key=key("hold-r5"),
        listing_id="list-r5",
        buyer_role="buyer-5x",
    )
    list_resale("list-r6", "resv-a7", 14_000, recipient="buyer-6x")  # live LISTED
    list_resale("list-r7", "resv-a13", 16_000, recipient="buyer-7x")  # live LISTED

    # --- admission: adopt, authorize, consume --------------------------------
    for rid in ("resv-a2", "resv-a6", "resv-a7", "resv-a12"):
        right = f"right-{rid.split('-', 1)[1]}"
        adm.adopt_issued(right, idempotency_key=key(f"adm-adopt-{rid}"), **adopt_body(rid))
    for machine, tag in (
        (adm_venue, "venue"),
        (adm_rev, "rev"),
        (adm_own, "own"),
        (adm_tick, "tick"),
        (adm_settle_down, "setdown"),
        (adm_settle_missing, "setmiss"),
    ):
        machine.adopt_issued(
            right_a6, idempotency_key=key(f"adm-{tag}-adopt"), **adopt_body("resv-a6")
        )

    request_a2 = req()
    adm.authorize_admission(
        "admit-a2",
        idempotency_key=key("admit-a2"),
        right_id=right_a2,
        version=1,
        holder_role="buyer-2",
        gate_role="gate-a",
        request=request_a2,
        expires_ms=T0 + ADMISSION_WINDOW_MS,
    )
    adm.consume(
        "consume-a2",
        idempotency_key=key("consume-a2"),
        right_id=right_a2,
        version=1,
        gate_role="gate-a",
        request=request_a2,
    )
    adm.authorize_admission(
        "admit-a12",
        idempotency_key=key("admit-a12"),
        right_id=right_a12,
        version=1,
        holder_role="buyer-12",
        gate_role="gate-b",
        request=req(),
        expires_ms=T0 + ADMISSION_WINDOW_MS,  # expired at final clock
    )

    # --- credit advance ------------------------------------------------------
    face = settle.view("settle-credit")["claim"]
    credit.offer(
        "adv-1",
        idempotency_key=key("offer-adv-1"),
        face=face,
        amount=30_000,
        beneficiary_role="buyer-1",
    )
    credit.approve("adv-1", idempotency_key=key("approve-adv-1"))
    credit.bind_settlement(
        "adv-1", idempotency_key=key("bind-adv-1"), settlement_id="settle-credit"
    )
    credit.draw("adv-1", idempotency_key=key("draw-adv-1"), draw_id="draw-1")
    credit.repay(
        "adv-1",
        idempotency_key=key("repay-adv-1"),
        repay_id="repay-1",
        sequence=1,
        amount=10_000,
    )
    credit.offer(
        "adv-2",
        idempotency_key=key("offer-adv-2"),
        face=face,
        amount=40_000,
        beneficiary_role="buyer-3",
    )

    # --- snapshot-change cursor bump -----------------------------------------
    # Mint cursors against the pre-bump snapshot, then let an accepted command
    # (the final set_clock) move the snapshot. Vectors are evaluated after.
    snapshot_before = {}
    for name in ("reservation", "resale"):
        machine = machines[name]
        snapshot_before[name] = {
            "journal_entries": len(machine.export_journal()),
            "state_digest": machine.state_digest(),
        }

    # accepted commands: advance clocks so lazy expiry is observable
    adm.set_clock("clock", idempotency_key=key("clock-adm-final"), now_ms=FINAL_CLOCK)
    resale.set_clock("clock", idempotency_key=key("clock-resale-final"), now_ms=FINAL_CLOCK)
    resv.set_clock("clock", idempotency_key=key("clock-resv-final"), now_ms=FINAL_CLOCK)

    # break the switchable ticket source only after every scenario command ran
    tick_break.down = True

    return {
        "seed": seed,
        "machines": machines,
        "reservations": reservations,
        "shows": sorted(shows),
        "rights": {
            "a1": right_a1, "a2": right_a2, "a6": right_a6, "a7": right_a7,
            "a12": right_a12,
        },
        "request_a2": request_a2,
        "snapshot_before": snapshot_before,
    }


# --------------------------------------------------------------------------
# vector model
# --------------------------------------------------------------------------

def _watermark(machine) -> dict:
    accepted = {"journal_entries": len(machine.export_journal())}
    now = getattr(machine, "_now", None)
    if now is not None:
        accepted["logical_time_ms"] = now
    return accepted


def _envelope(machine, query: str, input_norm: dict, body: object) -> dict:
    return {
        "accepted_through": _watermark(machine),
        "body": body,
        "fixture_mode": FIXTURE_MODE,
        "query_digest": NOT_BOUND,
        "query_input_canonical": _canonical(input_norm),
        "read_schema_version": READ_SCHEMA_VERSION,
    }


def _point_vector(query, scope_class, actor, machine, subject, call, kwargs=None):
    kwargs = kwargs or {}
    input_norm = {
        "actor": actor,
        "kwargs": kwargs,
        "query": query,
        "subject_id": subject,
    }
    try:
        body = call(subject, **kwargs)
    except POINT_ERRORS as error:
        expected = {"error_code": error.code, "error_kind": type(error).__name__}
    else:
        expected = {"ok": _envelope(machine, query, input_norm, body)}
    return {
        "actor": actor,
        "input": {"kwargs": kwargs, "subject_id": subject},
        "query": query,
        "scope_class": scope_class,
        "expected": expected,
    }


def _snapshot(machine) -> dict:
    return {
        "journal_entries": len(machine.export_journal()),
        "state_digest": machine.state_digest(),
    }


def expected_mint_cursor(query: str, scope: dict, snapshot: dict, position: int) -> str:
    return _canonical(
        {
            "cursor_format": CURSOR_FORMAT,
            "ordering": ORDERING,
            "position": position,
            "query": query,
            "scope": scope,
            "snapshot": snapshot,
        }
    )


def _parse_cursor(text):
    try:
        cursor = json.loads(text)
    except (TypeError, ValueError):
        raise FixtureQueryError("CURSOR_MISMATCH") from None
    if type(cursor) is not dict or cursor.get("cursor_format") != CURSOR_FORMAT:
        raise FixtureQueryError("CURSOR_MISMATCH")
    if cursor.get("ordering") != ORDERING:
        raise FixtureQueryError("CURSOR_MISMATCH")
    if type(cursor.get("position")) is not int or cursor["position"] < 0:
        raise FixtureQueryError("CURSOR_MISMATCH")
    snapshot = cursor.get("snapshot")
    if (
        type(snapshot) is not dict
        or type(snapshot.get("journal_entries")) is not int
        or type(snapshot.get("state_digest")) is not str
    ):
        raise FixtureQueryError("CURSOR_MISMATCH")
    return cursor


def expected_page(query, scope, rows, snapshot, *, fixture_limit, cursor=None):
    if type(fixture_limit) is not int or fixture_limit < 1:
        raise FixtureQueryError("INVALID_LIMIT")
    position = 0
    if cursor is not None:
        parsed = _parse_cursor(cursor)
        if parsed["query"] != query or parsed["scope"] != scope:
            raise FixtureQueryError("CURSOR_MISMATCH")
        if parsed["snapshot"] != snapshot:
            raise FixtureQueryError("SNAPSHOT_CHANGED")
        position = parsed["position"]
        if position > len(rows):
            raise FixtureQueryError("CURSOR_MISMATCH")
    entries = rows[position : position + fixture_limit]
    truncated = position + fixture_limit < len(rows)
    next_cursor = (
        expected_mint_cursor(query, scope, snapshot, position + fixture_limit)
        if truncated
        else None
    )
    return {"entries": entries, "next_cursor": next_cursor, "truncated": truncated}


def _list_vectors(query, scope_class, actor, machine, full_rows, project,
                  *, filters=None, extra_pages=()):
    """Population, pages and cursor cases for one list query.

    `full_rows` are the machine's public per-row views (from
    canonical_state); `project` maps one to the recommended summary subset.
    Every number here is a fixture parameter — no contract value is bound.
    """
    filters = filters or {}
    snapshot = _snapshot(machine)

    def rows_for(scope_filters):
        rows = full_rows
        for name, value in sorted(scope_filters.items()):
            if name not in ("buyer_role",):
                raise FixtureQueryError("INVALID_ID")
            if not _ident_ok(value):
                raise FixtureQueryError("INVALID_ID")
            rows = [row for row in rows if row.get(name) == value]
        return rows

    scopes = [
        {"actor": actor, "filters": {}},
    ]
    for spec in extra_pages:
        scopes.append({"actor": spec["actor"], "filters": spec["filters"]})

    pages = []
    for scope in scopes:
        rows = rows_for(scope["filters"])
        cursor = None
        for _ in range(len(rows) // 2 + 2):
            page_input = {"cursor": cursor, "filters": scope["filters"], "fixture_limit": 2}
            try:
                body = expected_page(
                    query, scope, [project(r) for r in rows], snapshot,
                    fixture_limit=2, cursor=cursor,
                )
            except FixtureQueryError as error:
                expected = {"error_kind": error.kind, "error_code": NOT_BOUND}
                cursor = None
            else:
                expected = {"ok": _envelope(machine, query,
                                            {"actor": actor, "input": page_input, "query": query},
                                            body)}
                cursor = body["next_cursor"]
            pages.append(
                {
                    "actor": scope["actor"],
                    "input": page_input,
                    "scope": scope,
                    "expected": expected,
                }
            )
            if cursor is None:
                break

    # error pages: bad filter value, nonpositive limit
    pages.append(
        {
            "actor": actor,
            "input": {"cursor": None, "filters": {"buyer_role": " "}, "fixture_limit": 2},
            "scope": scopes[0],
            "expected": {"error_kind": "INVALID_ID", "error_code": "INVALID_ID"},
        }
    )
    pages.append(
        {
            "actor": actor,
            "input": {"cursor": None, "filters": {}, "fixture_limit": 0},
            "scope": scopes[0],
            "expected": {"error_kind": "INVALID_LIMIT", "error_code": NOT_BOUND},
        }
    )

    return {
        "scopes": scopes,
        "pages": pages,
        "population": [{"id": r.get("listing_id") or r.get("reservation_id") or r.get("show_id"),
                        "row": project(r)} for r in full_rows],
        "snapshot": snapshot,
    }


def _cursor_cases(query, scope, machine, rows, project, snapshot_before, fixture_limit=2):
    """Cursor accept/reject cases against the final machine snapshot."""
    snapshot = _snapshot(machine)
    cases = []

    def case(name, cursor):
        try:
            body = expected_page(
                query, scope, [project(r) for r in rows], snapshot,
                fixture_limit=fixture_limit, cursor=cursor,
            )
        except FixtureQueryError as error:
            expected = {"error_kind": error.kind, "error_code": NOT_BOUND}
        else:
            expected = {"ok": _envelope(
                machine, query,
                {"actor": scope["actor"], "cursor": cursor, "query": query}, body)}
        cases.append({"input": {"cursor": cursor}, "name": name, "expected": expected})

    fresh = expected_mint_cursor(query, scope, snapshot, fixture_limit)
    case("continue_same_tuple", fresh)
    case("malformed_cursor", "not-a-cursor")
    case("query_mismatch", expected_mint_cursor("get_booking", scope, snapshot, fixture_limit))
    case(
        "scope_mismatch",
        expected_mint_cursor(query, {"actor": "other-fixture", "filters": {}}, snapshot, fixture_limit),
    )
    case(
        "ordering_mismatch",
        _canonical({
            "cursor_format": CURSOR_FORMAT,
            "ordering": "slot-desc",
            "position": fixture_limit,
            "query": query,
            "scope": scope,
            "snapshot": snapshot,
        }),
    )
    case(
        "position_out_of_range",
        expected_mint_cursor(query, scope, snapshot, len(rows) + 1),
    )
    case(
        "snapshot_changed_after_accept",
        expected_mint_cursor(query, scope, snapshot_before, fixture_limit),
    )
    return cases


# --------------------------------------------------------------------------
# per-domain builders
# --------------------------------------------------------------------------

def _reservation_doc(S) -> dict:
    resv = S["machines"]["reservation"]
    canonical = json.loads(resv.canonical_state())
    queries = {}

    queries["get_show"] = {
        "kind": "point",
        "vectors": [
            _point_vector("get_show", "public listing", "fixture-public", resv,
                          sid, resv.view_show)
            for sid in ("show-a", "show-b", "show-zz", " ")
        ],
    }

    buyers = {row["reservation_id"]: row["buyer_role"] for row in canonical["reservations"]}
    booking_subjects = (
        "resv-a1", "resv-a2", "resv-a3", "resv-a4", "resv-a5",
        "resv-a6", "resv-b1", "resv-zz", " ",
    )
    queries["get_booking"] = {
        "kind": "point",
        "vectors": [
            _point_vector(
                "get_booking", "owner or holder",
                buyers.get(rid, "fixture-viewer"),
                resv, rid, resv.view,
            )
            for rid in booking_subjects
        ],
    }

    show_rows = canonical["shows"]
    list_shows = _list_vectors(
        "list_shows", "public listing", "fixture-public", resv, show_rows,
        lambda row: {k: row[k] for k in SHOW_SUMMARY_KEYS},
    )
    scope = list_shows["scopes"][0]
    list_shows["cursor_cases"] = _cursor_cases(
        "list_shows", scope, resv, show_rows,
        lambda row: {k: row[k] for k in SHOW_SUMMARY_KEYS},
        S["snapshot_before"]["reservation"],
    )
    list_shows["visibility"] = {
        "recommended_subset": {
            "label": RECOMMENDATION,
            "row_ids": [row["show_id"] for row in show_rows],
        },
        "scope_class": "public listing",
        "value": NOT_BOUND,
    }
    queries["list_shows"] = {"kind": "list", **list_shows}

    booking_rows = canonical["reservations"]
    list_bookings = _list_vectors(
        "list_bookings", "owner or holder", "buyer-1", resv, booking_rows,
        lambda row: {k: row[k] for k in BOOKING_SUMMARY_KEYS},
        extra_pages=({"actor": "buyer-1", "filters": {"buyer_role": "buyer-1"}},),
    )
    scope = list_bookings["scopes"][0]
    list_bookings["cursor_cases"] = _cursor_cases(
        "list_bookings", scope, resv, booking_rows,
        lambda row: {k: row[k] for k in BOOKING_SUMMARY_KEYS},
        S["snapshot_before"]["reservation"],
    )
    list_bookings["visibility"] = {
        "recommended_subset": {
            "actor": "buyer-1",
            "label": RECOMMENDATION,
            "row_ids": [r["reservation_id"] for r in booking_rows if r["buyer_role"] == "buyer-1"],
        },
        "scope_class": "owner or holder",
        "value": NOT_BOUND,
    }
    queries["list_bookings"] = {"kind": "list", **list_bookings}

    return {
        "domain": "reservation",
        "fixture_version": FIXTURE_VERSION,
        "ordering": ORDERING_LABEL,
        "queries": queries,
        "watermark": _watermark(resv),
    }


def _resale_doc(S) -> dict:
    resale = S["machines"]["resale"]
    canonical = json.loads(resale.canonical_state())
    queries = {}

    queries["get_right"] = {
        "kind": "point",
        "vectors": [
            _point_vector("get_right", "owner or holder", actor, resale, rid, resale.view_right)
            for actor, rid in (
                ("buyer-2", "right-a1"),   # transferred: version 2, new holder
                ("buyer-7", "right-a7"),   # live listing bound
                ("fixture-viewer", "right-zz"),
                ("fixture-viewer", " "),
            )
        ],
    }

    queries["get_presentation"] = {
        "kind": "point",
        "vectors": [
            _point_vector(
                "get_presentation", "owner or holder", actor, resale, rid,
                resale.view_presentation,
                kwargs={"version": version, "holder_role": holder},
            )
            for actor, rid, version, holder in (
                ("buyer-2", "right-a1", 2, "buyer-2"),   # matches after transfer
                ("buyer-1", "right-a1", 1, "buyer-1"),   # stale version/holder
                ("buyer-7", "right-a7", 1, "buyer-7"),   # live listing blocks match
                ("buyer-9", "right-a9", 1, "buyer-9"),   # matches (listing cancelled)
                ("fixture-viewer", "right-zz", 1, "buyer-9"),
                ("fixture-viewer", " ", 1, "buyer-9"),
            )
        ],
    }

    listing_subjects = ("list-r1", "list-r2", "list-r3", "list-r4", "list-r5",
                        "list-r6", "list-r7", "list-zz", " ")
    queries["get_listing"] = {
        "kind": "point",
        "vectors": [
            _point_vector("get_listing", "owner or holder", "fixture-viewer",
                          resale, lid, resale.view)
            for lid in listing_subjects
        ],
    }

    listing_rows = canonical["listings"]
    list_open = _list_vectors(
        "list_open_listings", "public listing", "fixture-public", resale, listing_rows,
        lambda row: {k: row[k] for k in LISTING_SUMMARY_KEYS},
    )
    scope = list_open["scopes"][0]
    list_open["cursor_cases"] = _cursor_cases(
        "list_open_listings", scope, resale, listing_rows,
        lambda row: {k: row[k] for k in LISTING_SUMMARY_KEYS},
        S["snapshot_before"]["resale"],
    )
    list_open["open_phase_predicate"] = NOT_BOUND
    list_open["visibility"] = {
        "recommended_subset": {
            "label": RECOMMENDATION,
            "row_ids": [
                r["listing_id"]
                for r in listing_rows
                if r["phase"] == "LISTED" and not r["expired"] and r["attached"]
            ],
        },
        "scope_class": "public listing",
        "value": NOT_BOUND,
    }
    queries["list_open_listings"] = {"kind": "list", **list_open}

    return {
        "domain": "resale",
        "fixture_version": FIXTURE_VERSION,
        "ordering": ORDERING_LABEL,
        "queries": queries,
        "watermark": _watermark(resale),
    }


def _admission_doc(S) -> dict:
    adm = S["machines"]["admission"]
    queries = {}

    queries["get_admission"] = {
        "kind": "point",
        "vectors": [
            _point_vector("get_admission", "gate role", actor, adm, rid, adm.view)
            for actor, rid in (
                ("gate-a", "right-a2"),    # consumed
                ("gate-b", "right-a12"),   # authorized, expired at final clock
                ("buyer-6", "right-a6"),   # eligible
                ("buyer-7", "right-a7"),   # eligible, listing-locked
                ("fixture-viewer", "right-zz"),
                ("fixture-viewer", " "),
            )
        ],
    }

    credential_specs = [
        ("admission", adm, "buyer-6", "right-a6", {"version": 1, "holder_role": "buyer-6"}),
        ("admission", adm, "buyer-6", "right-a6", {"version": 2, "holder_role": "buyer-6"}),
        ("admission", adm, "buyer-6", "right-a6", {"version": 1, "holder_role": "buyer-99"}),
        ("admission", adm, "buyer-7", "right-a7", {"version": 1, "holder_role": "buyer-7"}),
        ("admission", adm, "buyer-2", "right-a2", {"version": 1, "holder_role": "buyer-2"}),
        ("admission_venue", S["machines"]["admission_venue"], "buyer-6", "right-a6",
         {"version": 1, "holder_role": "buyer-6"}),
        ("admission_revocation", S["machines"]["admission_revocation"], "buyer-6", "right-a6",
         {"version": 1, "holder_role": "buyer-6"}),
        ("admission_ownership_down", S["machines"]["admission_ownership_down"], "buyer-6",
         "right-a6", {"version": 1, "holder_role": "buyer-6"}),
        ("admission_ticket_down", S["machines"]["admission_ticket_down"], "buyer-6",
         "right-a6", {"version": 1, "holder_role": "buyer-6"}),
        ("admission_settlement_down", S["machines"]["admission_settlement_down"], "buyer-6",
         "right-a6", {"version": 1, "holder_role": "buyer-6"}),
        ("admission_settlement_missing", S["machines"]["admission_settlement_missing"], "buyer-6",
         "right-a6", {"version": 1, "holder_role": "buyer-6"}),
        ("admission", adm, "fixture-viewer", "right-zz", {"version": 1, "holder_role": "buyer-6"}),
        ("admission", adm, "fixture-viewer", " ", {"version": 1, "holder_role": "buyer-6"}),
    ]
    queries["get_credential"] = {
        "kind": "point",
        "vectors": [
            _point_vector("get_credential", "gate role", actor, machine, rid,
                          machine.view_credential, kwargs=kwargs)
            for _name, machine, actor, rid, kwargs in credential_specs
        ],
    }
    # record which machine produced each vector, for the self-check replay map
    for (name, _m, _a, _r, _k), vector in zip(credential_specs, queries["get_credential"]["vectors"]):
        vector["fixture_machine"] = name

    return {
        "domain": "admission",
        "fixture_version": FIXTURE_VERSION,
        "queries": queries,
        "watermark": _watermark(adm),
    }


def _settlement_doc(S) -> dict:
    settle = S["machines"]["settlement"]
    return {
        "domain": "settlement",
        "fixture_version": FIXTURE_VERSION,
        "queries": {
            "get_settlement": {
                "kind": "point",
                "vectors": [
                    _point_vector("get_settlement", "organizer", "organizer-1",
                                  settle, sid, settle.view)
                    for sid in ("settle-1", "settle-2", "settle-3", "settle-zz", " ")
                ],
            },
        },
        "watermark": _watermark(settle),
    }


def _credit_doc(S) -> dict:
    credit = S["machines"]["credit"]
    return {
        "domain": "credit",
        "fixture_version": FIXTURE_VERSION,
        "queries": {
            "get_credit_advance": {
                "kind": "point",
                "vectors": [
                    _point_vector("get_credit_advance", "owner or holder", actor,
                                  credit, aid, credit.view)
                    for actor, aid in (
                        ("buyer-1", "adv-1"),
                        ("buyer-3", "adv-2"),
                        ("fixture-viewer", "adv-zz"),
                        ("fixture-viewer", " "),
                    )
                ],
            },
            "get_credit_claim": {
                "kind": "point",
                "vectors": [
                    _point_vector("get_credit_claim", "owner or holder", "buyer-1",
                                  credit, cid, credit.view_claim)
                    for cid in ("settle-credit", "claim-zz", " ")
                ],
            },
        },
        "watermark": _watermark(credit),
    }


def build_documents(seed: int = SEED) -> tuple[dict, dict]:
    """Replay the scenario and return ({filename: document}, scenario)."""
    S = build_scenario(seed)
    docs = {
        "reservation.json": _reservation_doc(S),
        "resale.json": _resale_doc(S),
        "admission.json": _admission_doc(S),
        "settlement.json": _settlement_doc(S),
        "credit.json": _credit_doc(S),
    }
    watermarks = {
        name: _watermark(machine) for name, machine in S["machines"].items()
    }
    manifest = {
        "files": {
            name: {"sha256": hashlib.sha256((_canonical(doc) + "\n").encode("utf-8")).hexdigest()}
            for name, doc in sorted(docs.items())
        },
        "fixture_mode": FIXTURE_MODE,
        "fixture_version": FIXTURE_VERSION,
        "generator": "reference/read_model/generate_fixtures.py",
        "queries": {name: ("list" if name.startswith("list_") else "point") for name in QUERY_NAMES},
        "read_schema_version": READ_SCHEMA_VERSION,
        "seed": seed,
        "status": "CANDIDATE_FIXTURES; read-model implementation not merged; not conformance evidence",
        "watermarks": watermarks,
    }
    docs["manifest.json"] = manifest
    return docs, S


def main(argv) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(HERE / "vectors"),
                        help="output directory for the committed vectors")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--check", action="store_true",
                        help="regenerate in memory and compare bytes to the committed files")
    args = parser.parse_args(argv)

    docs, _S = build_documents(args.seed)
    out = Path(args.out)
    if args.check:
        problems = []
        for name, doc in sorted(docs.items()):
            target = out / name
            rendered = _canonical(doc) + "\n"
            if not target.is_file():
                problems.append("missing " + name)
                continue
            if target.read_bytes() != rendered.encode("utf-8"):
                problems.append("bytes differ: " + name)
        if problems:
            for problem in problems:
                print("fixture check failed: " + problem, file=sys.stderr)
            return 1
        print("fixture vectors ok: files=%d seed=%d" % (len(docs), args.seed))
        return 0

    out.mkdir(parents=True, exist_ok=True)
    for name, doc in sorted(docs.items()):
        (out / name).write_text(_canonical(doc) + "\n", encoding="utf-8")
    print("wrote %d vector files to %s (seed=%d)" % (len(docs), out, args.seed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
