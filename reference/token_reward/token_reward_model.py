"""Offline reference predicates for reward–transaction coupling.

Deterministic and in-memory. No network, files, clock, bank, price source,
chain client, or storage engine. Amounts are synthetic KRW-denominated
points (F4). They are not a coin, a token atom, or a KRW payment.

Nothing here chooses a product policy number. Caps, ratios, period counts,
pool balances, and supply figures are arguments. Legal, tax, and accounting
conclusions are outside this module.

The helpers below follow reference/settlement_f01_f03/mock_settlement.py.
Suites are discovered on isolated sys.path entries, so this suite does not
import that module.

A matched figure is equality inside this process, not chain finality,
bank exactly-once, durability, or an independent verification. TL-4 owns
independent verification of TK-4, TK-7, TK-8, TK-12, and V6.
"""

from __future__ import annotations

import hashlib
import json

MONEY_MAX = 10**12
PROVENANCE = "MOCK_TOKEN_REWARD_ONLY"
LIFECYCLE = "IN_MEMORY_FSM"
UNIT = "POINT_F4"

# Identifier scheme prefix. This is not a reward rule version.
REWARD_ID_SCHEME = "reward-id-v1"

POOLS = (
    "CUSTOMER_DEPOSIT",
    "ORGANIZER_SETTLEMENT",
    "REFUND_RESERVE",
    "PROTOCOL_REVENUE",
    "TOKEN_TREASURY_REWARD",
)
POOL_NAMES = frozenset(POOLS)
SPENDABLE_POOLS = frozenset({"PROTOCOL_REVENUE", "TOKEN_TREASURY_REWARD"})
OBLIGATION_POOLS = frozenset({"CUSTOMER_DEPOSIT", "ORGANIZER_SETTLEMENT", "REFUND_RESERVE"})

ALWAYS_FALSE_FLAGS = (
    "token_issued",
    "onchain_recorded",
    "funds_executed",
    "krw_paid",
    "chain_finality",
    "durable",
    "legal_authority",
)

SOURCE_KINDS = frozenset({"SETTLEMENT", "RESALE", "RESERVATION"})
SOURCE_FINALITY_FLAGS = (
    "funds_executed",
    "bank_debit_observed",
    "legal_debtor_bound",
    "external_return_closed",
    "durable",
)

COLLATERAL_KINDS = frozenset({"KRW_GUARANTEE", "ESCROW", "TOKEN"})
SUPPLY_OPS = frozenset({"MINT", "ALLOCATE", "BURN", "HOLDER_BURN"})
SUPPLY_EVENT_FIELDS = frozenset(
    {"event_id", "op", "amount", "approved", "path_approved", "program"}
)
SUPPLY_REPORT_FIELDS = (
    "minted_total",
    "unapproved_mint",
    "allocated_total",
    "burned_total",
    "holder_burn_outside_layer",
    "layer_supply",
)

ALARM_MATCH = "MATCH"
ALARM_UNAPPROVED_MINT = "UNAPPROVED_MINT"
ALARM_UNAPPROVED_PATH = "UNAPPROVED_PATH"
ALARM_HOLDER_BURN = "HOLDER_BURN_OUTSIDE_LAYER"
ALARM_UNEXPLAINED = "UNEXPLAINED"
STOP_PAYOUT_ALARMS = frozenset({ALARM_UNAPPROVED_MINT, ALARM_UNAPPROVED_PATH})


class TokenRewardError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise TokenRewardError(code)


def _ident(value: object, code: str = "INVALID_ID") -> str:
    _require(type(value) is str and 0 < len(value) <= 100 and value.strip() == value, code)
    return value


def _money(value: object, *, positive: bool) -> int:
    code = "INVALID_AMOUNT" if positive else "INVALID_NONNEGATIVE"
    _require(type(value) is int, code)
    if positive:
        _require(0 < value <= MONEY_MAX, code)
    else:
        _require(0 <= value <= MONEY_MAX, code)
    return value


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _copy(value: object) -> object:
    return json.loads(_canonical(value))


def _digest(value: object) -> str:
    _require(type(value) is str and len(value) == 64, "DIGEST_INVALID")
    _require(all(character in "0123456789abcdef" for character in value), "DIGEST_INVALID")
    return value


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _false_flags() -> dict:
    return {name: False for name in ALWAYS_FALSE_FLAGS}


def reward_id(*, program: object, source_op_id: object, recipient: object, kind: object) -> str:
    """Derive the reward id from the stable tuple.

    Rule version is not an input. source_op_id is the caller's stable
    operation identity. This function has no fence parameter.
    """

    body = _canonical(
        {
            "kind": _ident(kind),
            "program": _ident(program),
            "recipient": _ident(recipient),
            "source_op_id": _ident(source_op_id),
        }
    )
    return REWARD_ID_SCHEME + ":" + _sha256_text(body)


def effect_id(reward_id_value: str, side: str, generation: int) -> str:
    digest = _sha256_text(
        _canonical({"generation": generation, "reward_id": reward_id_value, "side": side})
    )
    return side + "-effect-" + digest[:40]


class PoolLedger:
    """Per-pool credits and spends. Opening balances are caller-supplied.

    Token spend is accepted only from PROTOCOL_REVENUE and
    TOKEN_TREASURY_REWARD. A shortfall raises POOL_EXHAUSTED_PAUSED and
    does not move funds from another pool. There is no top-up method.
    """

    def __init__(self, opening_balances: object) -> None:
        _require(type(opening_balances) is dict, "POOL_BALANCES_REQUIRED")
        _require(set(opening_balances) == POOL_NAMES, "POOL_BALANCES_REQUIRED")
        self._credits: list[dict] = []
        self._spends: list[dict] = []
        self._balance: dict[str, int] = {}
        for pool in POOLS:
            amount = _money(opening_balances[pool], positive=False)
            self._balance[pool] = amount
            self._credits.append({"pool": pool, "amount": amount, "source_ref": "OPENING"})
        self._conserve()

    def credit(self, pool: object, amount: object, source_ref: object) -> dict:
        pool_name = self._pool(pool)
        points = _money(amount, positive=True)
        source = _ident(source_ref)
        _require(self._balance[pool_name] + points <= MONEY_MAX, "INVALID_AMOUNT")
        self._balance[pool_name] += points
        self._credits.append({"pool": pool_name, "amount": points, "source_ref": source})
        self._conserve()
        return self.view()

    def spend(self, pool: object, amount: object, program_ref: object) -> dict:
        pool_name = self._pool(pool)
        _require(pool_name in SPENDABLE_POOLS, "POOL_FORBIDDEN_FOR_TOKEN_SPEND")
        points = _money(amount, positive=True)
        program = _ident(program_ref)
        _require(self._balance[pool_name] >= points, "POOL_EXHAUSTED_PAUSED")
        self._balance[pool_name] -= points
        self._spends.append({"pool": pool_name, "amount": points, "program_ref": program})
        self._conserve()
        return self.view()

    def view(self) -> dict:
        self._conserve()
        return _copy(
            {
                "balances": {pool: self._balance[pool] for pool in POOLS},
                "credits": self._credits,
                "spends": self._spends,
            }
        )

    def canonical_state(self) -> str:
        return _canonical(self.view())

    def state_digest(self) -> str:
        return _sha256_text(self.canonical_state())

    def _pool(self, pool: object) -> str:
        _require(type(pool) is str and pool in POOL_NAMES, "POOL_UNKNOWN")
        return pool

    def _conserve(self) -> None:
        for pool in POOLS:
            credits = sum(item["amount"] for item in self._credits if item["pool"] == pool)
            spends = sum(item["amount"] for item in self._spends if item["pool"] == pool)
            _require(credits - spends == self._balance[pool], "MOCK_INVARIANT")
            _require(self._balance[pool] >= 0, "MOCK_INVARIANT")


def collateral_recognized(liability_krw: object, collateral_items: object) -> dict:
    """Recognize KRW guarantee and escrow only.

    Token valuation is refused because no price source is defined. Token-only
    collateral against a KRW liability is rejected. A token item never adds
    to the recognized amount, including as supplemental excess.
    """

    liability = _money(liability_krw, positive=True)
    _require(type(collateral_items) is list, "COLLATERAL_TYPE")
    recognized = 0
    saw_token = False
    saw_krw = False
    for item in collateral_items:
        _require(type(item) is dict, "COLLATERAL_TYPE")
        _require("valuation" not in item, "PRICE_SOURCE_UNDEFINED")
        kind = item.get("kind")
        _require(type(kind) is str and kind in COLLATERAL_KINDS, "COLLATERAL_KIND_UNSUPPORTED")
        _require(set(item) == {"kind", "amount"}, "COLLATERAL_FIELDS")
        amount = _money(item["amount"], positive=True)
        if kind == "TOKEN":
            saw_token = True
            continue
        saw_krw = True
        _require(recognized + amount <= MONEY_MAX, "INVALID_AMOUNT")
        recognized += amount
    _require(not saw_token or saw_krw, "TOKEN_ONLY_COLLATERAL_REJECTED")
    return {
        "liability_krw": liability,
        "recognized_krw": recognized,
        "token_recognized": 0,
        "currency": "KRW",
    }


def net_residual_revenue(
    *,
    gross_revenue: object,
    refundable_window_revenue: object,
    customer_deposit_outlay: object,
    organizer_settlement_outlay: object,
    refund_reserve_outlay: object,
    operating_cost: object,
    loss_provision: object,
) -> int:
    """Net residual after the refundable window and the obligation order.

    Every argument is required. Revenue still inside the refundable window
    is excluded. No period length or ratio is applied here.
    """

    gross = _money(gross_revenue, positive=False)
    in_window = _money(refundable_window_revenue, positive=False)
    _require(in_window <= gross, "WINDOW_REVENUE_EXCEEDS_GROSS")
    deductions = (
        _money(customer_deposit_outlay, positive=False)
        + _money(organizer_settlement_outlay, positive=False)
        + _money(refund_reserve_outlay, positive=False)
        + _money(operating_cost, positive=False)
        + _money(loss_provision, positive=False)
    )
    eligible = gross - in_window
    _require(deductions <= eligible, "RESIDUAL_COMPONENTS_EXCEED_ELIGIBLE")
    _require(deductions <= MONEY_MAX, "INVALID_AMOUNT")
    return eligible - deductions


def reward_budget(
    *,
    cap: object,
    ratio_numerator: object,
    ratio_denominator: object,
    net_residual: object,
    periods: object,
) -> int:
    """min(cap, ratio × net residual) using integer floor division.

    periods is the caller-supplied N. It is not a multiplier. net_residual
    must already be the aggregate for those periods. None of the arguments
    has a default.
    """

    ceiling = _money(cap, positive=False)
    numerator = _money(ratio_numerator, positive=False)
    _require(type(ratio_denominator) is int and 0 < ratio_denominator <= MONEY_MAX, "INVALID_RATIO")
    residual = _money(net_residual, positive=False)
    _require(type(periods) is int and 0 < periods <= MONEY_MAX, "INVALID_PERIODS")
    scaled = residual * numerator // ratio_denominator
    _require(scaled <= MONEY_MAX, "INVALID_AMOUNT")
    if ceiling < scaled:
        return ceiling
    return scaled


def _supply_event(event: object) -> dict:
    _require(type(event) is dict and set(event) == SUPPLY_EVENT_FIELDS, "SUPPLY_EVENT_FIELDS")
    event_id = _ident(event["event_id"])
    op = event["op"]
    _require(type(op) is str and op in SUPPLY_OPS, "SUPPLY_OP_UNSUPPORTED")
    amount = _money(event["amount"], positive=True)
    _require(type(event["approved"]) is bool, "SUPPLY_APPROVAL_TYPE")
    _require(type(event["path_approved"]) is bool, "SUPPLY_PATH_TYPE")
    program = event["program"]
    if op in {"MINT", "ALLOCATE"}:
        program = _ident(program)
    elif op == "BURN":
        program = None if program is None else _ident(program)
    else:
        _require(program is None, "HOLDER_BURN_NOT_LAYER")
        _require(event["approved"] is False, "HOLDER_BURN_NOT_LAYER")
    return {
        "event_id": event_id,
        "op": op,
        "amount": amount,
        "approved": event["approved"],
        "path_approved": event["path_approved"],
        "program": program,
    }


def supply_report(events: object) -> dict:
    """Recompute layer supply from mint, allocate, and burn records.

    New mint changes layer supply. allocate does not. Holder burn is recorded
    and is not subtracted here. The chain figure is not an input.
    """

    _require(type(events) is list, "SUPPLY_EVENTS_TYPE")
    minted = 0
    unapproved_mint = 0
    allocated = 0
    burned = 0
    holder_burn = 0
    copied: list[dict] = []
    seen: set[str] = set()
    for raw in events:
        event = _supply_event(raw)
        _require(event["event_id"] not in seen, "SUPPLY_EVENT_DUPLICATE")
        seen.add(event["event_id"])
        amount = event["amount"]
        if event["op"] == "MINT":
            if event["approved"]:
                _require(minted + amount <= MONEY_MAX, "INVALID_AMOUNT")
                minted += amount
            else:
                _require(unapproved_mint + amount <= MONEY_MAX, "INVALID_AMOUNT")
                unapproved_mint += amount
        elif event["op"] == "ALLOCATE":
            _require(allocated + amount <= MONEY_MAX, "INVALID_AMOUNT")
            allocated += amount
        elif event["op"] == "BURN":
            if event["approved"]:
                _require(amount <= minted - burned, "SUPPLY_CONSERVATION")
                burned += amount
            # An unapproved burn does not reduce layer supply.
        else:
            _require(holder_burn + amount <= MONEY_MAX, "INVALID_AMOUNT")
            holder_burn += amount
        copied.append(event)
    layer_supply = minted - burned
    _require(layer_supply >= 0, "SUPPLY_CONSERVATION")
    return {
        "events": copied,
        "minted_total": minted,
        "unapproved_mint": unapproved_mint,
        "allocated_total": allocated,
        "burned_total": burned,
        "holder_burn_outside_layer": holder_burn,
        "layer_supply": layer_supply,
        "figure": "SYNTHETIC_SUPPLY_FIGURE",
    }


def reconcile_supply(offchain: object, chain_supply: object) -> dict:
    """Compare a supplied chain figure with an independently recomputed report.

    chain_supply is a synthetic integer. Nothing is read from a chain.
    HOLDER_BURN_OUTSIDE_LAYER is not a mismatch. Unapproved mint and an
    unapproved path set stop_payout.
    """

    _require(type(offchain) is dict and type(offchain.get("events")) is list, "SUPPLY_REPORT_MISMATCH")
    recomputed = supply_report(offchain["events"])
    for field in SUPPLY_REPORT_FIELDS:
        _require(offchain.get(field) == recomputed[field], "SUPPLY_REPORT_MISMATCH")
    chain = _money(chain_supply, positive=False)
    layer = recomputed["layer_supply"]
    holder = recomputed["holder_burn_outside_layer"]
    unapproved = recomputed["unapproved_mint"]
    path_bad = any(not event["path_approved"] for event in recomputed["events"])
    if path_bad:
        alarm = ALARM_UNAPPROVED_PATH
        mismatch = True
        stop_payout = True
    elif unapproved > 0:
        alarm = ALARM_UNAPPROVED_MINT
        mismatch = True
        stop_payout = True
    elif holder > 0 and chain == layer - holder:
        alarm = ALARM_HOLDER_BURN
        mismatch = False
        stop_payout = False
    elif chain == layer:
        alarm = ALARM_MATCH
        mismatch = False
        stop_payout = False
    else:
        alarm = ALARM_UNEXPLAINED
        mismatch = True
        stop_payout = False
    _require(stop_payout is (alarm in STOP_PAYOUT_ALARMS), "MOCK_INVARIANT")
    return {
        "alarm": alarm,
        "mismatch": mismatch,
        "stop_payout": stop_payout,
        "offchain_supply": layer,
        "chain_supply": chain,
        "figure": "SYNTHETIC_SUPPLY_FIGURE",
    }
