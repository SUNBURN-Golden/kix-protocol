"""Fixture-driven offline tooling, not a protocol schema or public command.

Validate the entire fixture before constructing machines. Execute each explicit
step once, stopping on unexpected outcomes, retaining earlier effects.
"""

import argparse
import copy
import inspect
import json
import sys
from pathlib import Path

from local_finance_session import LocalFinanceSession, operation_method
from credit_fsm import CreditError
from settlement_fsm import SettlementError
from fake_statement_source import SyntheticStatementFault
from statement_source import (
    InvalidStatementRecord, StatementIdentityMismatch, StatementNotFound,
    StatementRecord, StatementSourceError,
)


class FixtureError(ValueError):
    """Invalid configuration, detected before dispatch."""


class ClaimSnapshotError(ValueError):
    """An explicit view did not supply a non-null claim to save."""


_DOMAIN_ERRORS = (CreditError, SettlementError, StatementSourceError)
_ERROR_TYPES = {error.__name__ for error in (
    CreditError, SettlementError, StatementSourceError, InvalidStatementRecord,
    StatementIdentityMismatch, StatementNotFound,
)}
_INTEGER_FIELDS = frozenset({
    "gross", "amount", "fee", "tax", "held", "adjustment", "fee_bps", "sequence",
    "face", "distributed", "outstanding", "cancelled_unpaid", "refund_face",
    "confirmed_cash", "recovery_due", "distributed_cash", "non_cash_accounted",
    "pg_adjustment_outstanding", "receivable_open", "refund_accepted",
    "refund_outstanding", "undistributed_cash",
})


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError("duplicate JSON object key: " + key)
        result[key] = value
    return result


def _reject_constant(token):
    raise FixtureError("non-finite JSON constant: " + token)


def decode_fixture(text):
    try:
        return json.loads(text, object_pairs_hook=_object_pairs, parse_constant=_reject_constant)
    except ValueError as error:
        raise FixtureError("invalid JSON: " + str(error)) from error


def _fields(value, required, optional=()):
    if type(value) is not dict or not set(required) <= set(value) <= set(required) | set(optional):
        raise FixtureError("expected fields " + repr(sorted(required)) + "; optional " + repr(sorted(optional)))


def _string(value, label):
    if type(value) is not str:
        raise FixtureError(label + " must be a string")


def _integers(value, *, body=False):
    """Encoding only; ranges, conservation and policy semantics stay in FSMs."""
    if type(value) is dict:
        for key, item in value.items():
            # offer.body.face is a snapshot object; obligation.face is an integer.
            if key in _INTEGER_FIELDS and not (body and key == "face" and type(item) is dict):
                if type(item) is not int:
                    raise FixtureError(key + " must be a JSON integer")
            _integers(item)
    elif type(value) is list:
        for item in value:
            _integers(item)


def validate_fixture(fixture):
    """Return detached steps/recordings after full structural validation."""
    _fields(fixture, {"fixture_version", "synthetic", "statements", "steps"})
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("fixture_version must be integer 1")
    if fixture["synthetic"] is not True:
        raise FixtureError("synthetic must be true")
    if type(fixture["statements"]) is not list or type(fixture["steps"]) is not list:
        raise FixtureError("statements and steps must be arrays")
    recordings = {}
    for item in fixture["statements"]:
        _fields(item, {"settlement_id", "movement_id"}, {"record", "fault"})
        for field in ("settlement_id", "movement_id"):
            _string(item[field], field)
        identity = (item["settlement_id"], item["movement_id"])
        if identity in recordings:
            raise FixtureError("duplicate recording identity")
        if ("record" in item) == ("fault" in item):
            raise FixtureError("statement needs exactly one of record or fault")
        if "record" in item:
            record = item["record"]
            _fields(record, StatementRecord.__required_keys__)
            _string(record["settlement_id"], "record.settlement_id")
            _string(record["movement_id"], "record.movement_id")
            if record["adjustment_reason"] is not None:
                _string(record["adjustment_reason"], "adjustment_reason")
            _integers(record)
            # Identity equality is the adapter's responsibility, not a new rule.
            recordings[identity] = json.dumps(record, allow_nan=False)
        else:
            try:
                recordings[identity] = SyntheticStatementFault(item["fault"])
            except (ValueError, TypeError) as error:
                raise FixtureError("unsupported synthetic statement fault") from error

    saved = set()
    for step in fixture["steps"]:
        _fields(step, {"target", "operation"}, {
            "settlement_id", "advance_id", "claim_id", "idempotency_key", "body",
            "expect_error", "save_claim_as", "face_ref",
        })
        target, operation = step["target"], step["operation"]
        _string(target, "target")
        _string(operation, "operation")
        if target not in ("settlement", "credit"):
            raise FixtureError("unsupported target")
        view = operation == "view" or (target == "credit" and operation == "view_claim")
        identity = "claim_id" if operation == "view_claim" else (
            "settlement_id" if target == "settlement" else "advance_id")
        required = {"target", "operation", identity}
        optional = {"expect_error"}
        if view:
            if target == "settlement":
                optional.add("save_claim_as")
        else:
            required.update({"idempotency_key", "body"})
            if target == "credit" and operation == "offer":
                optional.add("face_ref")
        _fields(step, required, optional)
        _string(step[identity], identity)
        if "expect_error" in step:
            expected = step["expect_error"]
            _fields(expected, {"type"}, {"code"})
            if type(expected["type"]) is not str or expected["type"] not in _ERROR_TYPES:
                raise FixtureError("expect_error must name an existing domain exception")
            if "code" in expected:
                _string(expected["code"], "expect_error.code")
        if view:
            if "save_claim_as" in step:
                name = step["save_claim_as"]
                _string(name, "save_claim_as")
                if name in saved:
                    raise FixtureError("saved claim names cannot be overwritten")
                saved.add(name)
            continue
        _string(step["idempotency_key"], "idempotency_key")
        body = step["body"]
        if type(body) is not dict:
            raise FixtureError("body must be an object")
        try:
            method = operation_method(target, operation)
            arguments = dict(body)
            if "face_ref" in step:
                _string(step["face_ref"], "face_ref")
                if step["face_ref"] not in saved or "face" in body:
                    raise FixtureError("face_ref needs an earlier save and excludes body.face")
                arguments["face"] = {}  # Only bind the signature; never fabricate an executed face.
            inspect.signature(method).bind(None, step[identity], idempotency_key=step["idempotency_key"], **arguments)
        except (ValueError, TypeError) as error:
            raise FixtureError("invalid operation/body: " + str(error)) from error
        _integers(body, body=True)
        for key, value in body.items():
            if key in {"face", "policy", "order", "product"} or key in _INTEGER_FIELDS:
                continue
            _string(value, "body." + key)
        if "face" in body and type(body["face"]) is not dict:
            raise FixtureError("face must be an object")
        if "policy" in body:
            _fields(body["policy"], {"kind", "fee_bps", "residual_payee", "fee_payee"})
            for key in ("kind", "residual_payee", "fee_payee"):
                _string(body["policy"][key], "policy." + key)
        if "order" in body:
            if type(body["order"]) is not list or any(type(part) is not str for part in body["order"]):
                raise FixtureError("order must be an array of strings")
    return recordings, copy.deepcopy(fixture["steps"])


def execute_fixture(fixture):
    """Return (JSON-compatible report, exit status). No dispatch on config error."""
    recordings, steps = validate_fixture(fixture)
    session = LocalFinanceSession(recordings=recordings)
    snapshots, records = {}, []
    ok = True
    for index, step in enumerate(steps):
        target, operation = step["target"], step["operation"]
        record = dict(step_index=index, target=target, operation=operation)
        try:
            if operation == "view":
                if target == "settlement":
                    value = session.settlement_view(step["settlement_id"])
                else:
                    value = session.credit_view(step["advance_id"])
                record["view"] = value
                if "save_claim_as" in step:
                    if value.get("claim") is None:
                        raise ClaimSnapshotError("view has no claim to save")
                    snapshots[step["save_claim_as"]] = copy.deepcopy(value["claim"])
            elif operation == "view_claim":
                record["view"] = session.credit_claim_view(step["claim_id"])
            else:
                body = copy.deepcopy(step["body"])
                if "face_ref" in step:
                    if step["face_ref"] not in snapshots:
                        raise ClaimSnapshotError("earlier view did not save a claim")
                    body["face"] = copy.deepcopy(snapshots[step["face_ref"]])
                if target == "settlement":
                    value = session.settlement(operation, step["settlement_id"], idempotency_key=step["idempotency_key"], **body)
                else:
                    value = session.credit(operation, step["advance_id"], idempotency_key=step["idempotency_key"], **body)
                record["receipt"] = value
            matched = "expect_error" not in step
        except Exception as error:
            record["error"] = dict(type=type(error).__name__, message=str(error))
            if hasattr(error, "code"):
                record["error"]["code"] = error.code
            expected = step.get("expect_error", {})
            matched = (isinstance(error, _DOMAIN_ERRORS)
                       and expected.get("type") == type(error).__name__
                       and ("code" not in expected or expected["code"] == getattr(error, "code", None)))
        record["expectation_met"] = matched
        record["source_calls"] = list(session.statement_source.calls)
        records.append(record)
        if not matched:
            ok = False
            break
    return dict(fixture_version=1, synthetic=True, ok=ok, results=records,
                source_calls=list(session.statement_source.calls)), 0 if ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        fixture = decode_fixture(args.fixture.read_text(encoding="utf-8"))
        report, status = execute_fixture(fixture)
    except (FixtureError, OSError, UnicodeError) as error:
        print(json.dumps(dict(ok=False, error=dict(type=type(error).__name__, message=str(error)))))
        return 2
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return status


if __name__ == "__main__":
    sys.exit(main())
