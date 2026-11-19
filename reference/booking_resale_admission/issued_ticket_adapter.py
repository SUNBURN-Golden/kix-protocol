"""Copy recorded booking/show inputs into one explicitly selected local adoption.

No lifecycle precheck, policy defaults, ownership lookup, cache or retry. Source
validation happens before target mutation; target errors and receipts pass through.
"""

from mock_gates import (
    CAPACITY_MAX, GATE_ROLE_LIMIT, GateError, _bps, _hex32, _ident, _money, _ms,
)


class IssuedTicketSourceError(Exception):
    """Local source read failure; not a protocol error or retained target key."""


class InvalidIssuedTicketRecord(IssuedTicketSourceError):
    """Missing, malformed or mismatched original issuance inputs."""


_BOOKING_FIELDS = {
    "reservation_id", "show_id", "slot", "buyer_role", "expires_ms", "order_id",
    "amount", "quote_ref", "payment_ref",
}
_SHOW_FIELDS = {
    "organizer_role", "capacity", "gate_roles", "primary_price", "resale_cap",
    "resale_allowed", "organizer_bps", "platform_bps",
}


def _require(ok, message):
    if not ok:
        raise InvalidIssuedTicketRecord(message)


def _record(value, fields, label):
    _require(type(value) is dict and fields <= value.keys(), f"missing or malformed {label}")
    return value


class IssuedTicketAdapter:
    def __init__(self, source, *, resale, admission):
        self._source = source
        self._targets = {"resale": resale, "admission": admission}

    def _read(self, method, identity):
        try:
            return getattr(self._source, method)(identity)
        except IssuedTicketSourceError:
            raise
        except Exception as error:
            raise IssuedTicketSourceError(f"issued ticket {method} failed") from error

    def apply(self, *, surface, reservation_id, right_id, idempotency_key) -> dict:
        _require(type(surface) is str and surface in self._targets,
                 "surface must be resale or admission")
        try:
            for value in (reservation_id, right_id, idempotency_key):
                _ident(value)
            view = _record(self._read("view", reservation_id),
                           _BOOKING_FIELDS | {"issuance_id", "right"}, "reservation")
            for field in ("reservation_id", "show_id", "buyer_role", "order_id", "issuance_id"):
                _ident(view[field])
            _require(view["reservation_id"] == reservation_id, "reservation identity mismatch")
            _require(view["issuance_id"] == right_id, "issuance identity mismatch")
            right = _record(view["right"], {"right_id", "show_id", "slot"}, "right")
            _ident(right["right_id"])
            _ident(right["show_id"])
            _require(right["right_id"] == right_id, "right identity mismatch")
            _require(right["show_id"] == view["show_id"], "right show mismatch")
            _require(type(view["slot"]) is int and type(right["slot"]) is int
                     and right["slot"] == view["slot"], "right slot mismatch")
            _ms(view["expires_ms"], "RESERVATION_WINDOW")
            _money(view["amount"])
            _hex32(view["payment_ref"], "PAYMENT_REF")
            if view["quote_ref"] is not None:
                _ident(view["quote_ref"])
            envelope = _record(self._read("view_show", view["show_id"]), {"show"}, "show view")
            show = _record(envelope["show"], _SHOW_FIELDS | {"show_id"}, "show")
            _ident(show["show_id"])
            _ident(show["organizer_role"])
            _require(show["show_id"] == view["show_id"], "show identity mismatch")
            _require(type(show["capacity"]) is int and 1 <= show["capacity"] <= CAPACITY_MAX,
                     "invalid capacity")
            _require(0 <= view["slot"] < show["capacity"], "invalid slot")
            gates = show["gate_roles"]
            _require(type(gates) is list and 0 < len(gates) <= GATE_ROLE_LIMIT,
                     "invalid gate_roles")
            for gate in gates:
                _ident(gate)
            _require(len(set(gates)) == len(gates), "duplicate gate_roles")
            _money(show["primary_price"])
            _money(show["resale_cap"])
            _require(type(show["resale_allowed"]) is bool, "invalid resale_allowed")
            _bps(show["organizer_bps"])
            _bps(show["platform_bps"])
            _require(show["organizer_bps"] + show["platform_bps"] <= 10000, "invalid bps sum")
        except GateError as error:
            raise InvalidIssuedTicketRecord(error.code) from error
        body = {field: view[field] for field in _BOOKING_FIELDS}
        body.update({field: show[field] for field in _SHOW_FIELDS})
        body["gate_roles"] = list(gates)
        # Deliberately outside source error handling: exactly one existing action.
        return self._targets[surface].adopt_issued(
            right_id, idempotency_key=idempotency_key, **body)
