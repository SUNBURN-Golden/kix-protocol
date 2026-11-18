"""Copy one selected local booking/resale amount into explicit initiation.

No lifecycle eligibility, policy defaults, identity derivation, cache or retry.
Source failures precede target mutation; target errors and receipts pass through.
"""

from mock_gates import GateError, _ident, _money


class SettlementInputSourceError(Exception):
    """Local source failure; not a protocol error or retained target key."""


class InvalidSettlementInputRecord(SettlementInputSourceError):
    """Missing, malformed or mismatched recorded settlement inputs."""


def _require(ok, message):
    if not ok:
        raise InvalidSettlementInputRecord(message)


class SettlementInputAdapter:
    def __init__(self, machine, *, booking_source=None, resale_source=None):
        self._machine = machine
        self._sources = {"booking": booking_source, "resale": resale_source}

    def _read(self, source, source_id):
        if source is None:
            raise SettlementInputSourceError("no local settlement input source configured")
        try:
            return source.view(source_id)
        except SettlementInputSourceError:
            raise
        except Exception as error:
            raise SettlementInputSourceError("settlement input view failed") from error

    def apply(self, *, source_kind, source_id, settlement_id, idempotency_key,
              trade_id, debtor_role, policy):
        _require(type(source_kind) is str and source_kind in self._sources,
                 "source_kind must be booking or resale")
        field = "reservation_id" if source_kind == "booking" else "listing_id"
        fields = {field, "amount", "currency"}
        if source_kind == "booking":
            fields.add("order_id")
        try:
            _ident(source_id)
            record = self._read(self._sources[source_kind], source_id)
            _require(type(record) is dict and fields <= record.keys(),
                     "missing or malformed settlement input record")
            _ident(record[field])
            _require(record[field] == source_id, "settlement input identity mismatch")
            if source_kind == "booking":
                _ident(record["order_id"])
            _money(record["amount"])
            _require(type(record["currency"]) is str and record["currency"] == "KRW",
                     "invalid settlement input currency")
        except GateError as error:
            raise InvalidSettlementInputRecord(error.code) from error
        # Exactly one existing target call, outside the source error boundary.
        return self._machine.initiate(
            settlement_id, idempotency_key=idempotency_key, trade_id=trade_id,
            gross=record["amount"], currency=record["currency"],
            debtor_role=debtor_role, policy=policy)
