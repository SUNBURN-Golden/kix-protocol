"""One offline operation-bound synthetic lookup. Analog, NOT Toss.

The versioned fixture is internal tooling, not a protocol command or public API.
No network, credentials, persistence, economic application, retries or polling.
"""

import argparse
import json
from dataclasses import asdict, fields
from pathlib import Path

from fake_payment_lookup import FakePaymentLookup, SyntheticLookupFault, SyntheticLookupScope
from payment_lookup_router import PaymentLookupRouter
from provider_facts import (
    PROVENANCE, NormalizedPaymentHistory, OperationBindingStore, OperationRef,
    PaymentRef, ProviderFactsError,
)

LIMITATIONS = "Synthetic only; no authentication, durability, finality or payment-completion claims."


class FixtureError(ValueError):
    """Invalid internal configuration, before any lookup can take place."""


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(token):
    raise FixtureError("non-finite JSON constant")


def _decode(text):
    try:
        return json.loads(text, object_pairs_hook=_object_pairs, parse_constant=_reject_constant)
    except ValueError as exc:
        raise FixtureError("invalid JSON: " + str(exc)) from exc


def _fields(value, names, label):
    if type(value) is not dict or set(value) != set(names):
        raise FixtureError(label + ": expected exactly " + ", ".join(names))
    return value


def _list(value, label):
    if type(value) is not list:
        raise FixtureError(label + ": expected array")
    return value


def _reference(value, cls):
    names = tuple(field.name for field in fields(cls))
    _fields(value, names, cls.__name__)
    try:
        return cls(**value)
    except ProviderFactsError as exc:
        raise FixtureError(cls.__name__ + ": " + exc.code) from exc


def load_fixture(path):
    """Validate ALL declarations, then construct a fresh store and local fakes.

    Duplicate declarations are errors even if identical. Missing bindings,
    routes and recordings are permitted so the router can report unresolved.
    Recorded text is neither parsed nor changed here.
    """
    fixture = _fields(
        _decode(Path(path).read_text(encoding="utf-8")),
        ("fixture_version", "provenance", "bindings", "routes"), "fixture",
    )
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("fixture_version: expected integer 1")
    if fixture["provenance"] != PROVENANCE:
        raise FixtureError("provenance: expected " + PROVENANCE)

    binding_pairs = {}
    for entry in _list(fixture["bindings"], "bindings"):
        _fields(entry, ("operation_ref", "payment_ref"), "binding")
        operation = _reference(entry["operation_ref"], OperationRef)
        payment = _reference(entry["payment_ref"], PaymentRef)
        if operation in binding_pairs:
            raise FixtureError("duplicate operation binding")
        if (operation.provider, operation.account) != (payment.provider, payment.account):
            raise FixtureError("binding: BINDING_MISMATCH")
        binding_pairs[operation] = payment

    route_recordings = {}
    for entry in _list(fixture["routes"], "routes"):
        _fields(entry, ("scope", "recordings"), "route")
        scope = _reference(entry["scope"], SyntheticLookupScope)
        if scope in route_recordings:
            raise FixtureError("duplicate route scope")
        recordings = {}
        for recording in _list(entry["recordings"], "recordings"):
            if type(recording) is not dict:
                raise FixtureError("recording: expected object")
            alternative = "recorded_text" if "recorded_text" in recording else "fault"
            _fields(recording, ("payment_ref", alternative), "recording")
            payment = _reference(recording["payment_ref"], PaymentRef)
            if not scope.matches(payment):
                raise FixtureError("recording/route: BINDING_MISMATCH")
            if payment in recordings:
                raise FixtureError("duplicate recording payment_ref")
            value = recording[alternative]
            if type(value) is not str:
                raise FixtureError("recording: expected text or fault string")
            if alternative == "fault":
                try:
                    value = SyntheticLookupFault(value)
                except ValueError as exc:
                    raise FixtureError("recording: unsupported synthetic fault") from exc
            recordings[payment] = value
        route_recordings[scope] = recordings

    bindings = OperationBindingStore()
    for operation, payment in binding_pairs.items():
        bindings.bind(operation, payment)
    routes = {
        scope: FakePaymentLookup(scope=scope, recordings=recordings)
        for scope, recordings in route_recordings.items()
    }
    return bindings, routes


def lookup_once(bindings, routes, operation_ref):
    """Call the existing router once and serialize its result and call snapshots."""
    result = PaymentLookupRouter(bindings, routes=routes).lookup(operation_ref)
    output = {
        "provenance": result.provenance,
        "limitations": LIMITATIONS,
        "operation_ref": asdict(result.operation_ref),
        "payment_ref": result.payment_ref.as_dict() if result.payment_ref else None,
        "fake_calls": [
            {"scope": asdict(scope), "payment_refs": [ref.as_dict() for ref in routes[scope].calls]}
            for scope in sorted(routes, key=lambda s: (s.provider, s.account, s.environment))
        ],
    }
    if isinstance(result.result, NormalizedPaymentHistory):
        output["facts"] = [item.normalized_fact() for item in result.result.items]
        output["receipt"] = result.result.receipt.as_dict()
        output["item_hashes"] = result.result.item_hashes()
    else:
        output["unresolved"] = result.result.reason
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--fixture", required=True, action="append", help="local synthetic JSON fixture")
    parser.add_argument("--operation-ref", required=True, action="append", help="complete OperationRef JSON")
    args = parser.parse_args(argv)
    if len(args.fixture) != 1 or len(args.operation_ref) != 1:
        parser.error("--fixture and --operation-ref must each appear exactly once")
    try:
        operation = _reference(_decode(args.operation_ref[0]), OperationRef)
        bindings, routes = load_fixture(args.fixture[0])
    except (FixtureError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    # Programming errors are not caught or disguised as unresolved/config errors.
    output = lookup_once(bindings, routes, operation)
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
