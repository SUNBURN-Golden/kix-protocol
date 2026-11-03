"""Opt-in synthetic calculations; hashes convey no authenticated quote authority."""

from collections.abc import Mapping
from functools import lru_cache
import importlib.util
from pathlib import Path
import sys
from types import MappingProxyType

from booking_quote_source import InvalidBookingQuoteRecord
from mock_gates import GateError, _ident, _money


@lru_cache(maxsize=1)
def _calculator():
    """Load unchanged repository modules lazily, restoring all public bindings.

    These legacy modules use absolute sibling imports. Load in dependency order
    with temporary module bindings, never adding their directory to sys.path.
    Only code modules are retained; no calculated result is cached. This local
    desk, like its FSM, is a single-writer, in-process reference tool.
    """
    directory = Path(__file__).resolve().parents[1] / "v0.3-rc1"
    names = ("common", "canonical_encoding", "assets", "execution_contracts", "commerce")
    previous = {name: sys.modules.get(name) for name in names}
    loaded = {}
    try:
        for name in names:
            spec = importlib.util.spec_from_file_location(name, directory / f"{name}.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            loaded[name] = module
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    return loaded


def calculate_booking_quote(request_text: str) -> dict:
    """Decode bounded CE1 text and calculate exactly one undiscounted KRW line."""
    if type(request_text) is not str:
        raise InvalidBookingQuoteRecord("request_text must be text")
    modules = _calculator()
    try:
        request = modules["canonical_encoding"].decode_json(request_text.encode("utf-8"))
        if (type(request) is not dict or type(request.get("lines")) is not list
                or len(request["lines"]) != 1 or type(request.get("discounts")) is not list
                or request["discounts"]):
            raise InvalidBookingQuoteRecord("requires one line and no discount rules")
        # The unchanged calculator owns the full schema and exact atom parsing.
        quote = modules["commerce"].build_quote(request)
        if quote["asset"] != modules["assets"].KRW.to_dict():
            raise InvalidBookingQuoteRecord("requires the complete existing KRW asset specification")
        _money(int(quote["totals"]["payableAtoms"]))
    except (modules["common"].Rejected, GateError, UnicodeError) as error:
        raise InvalidBookingQuoteRecord(str(error)) from error
    return quote


class CalculatedBookingQuoteSource:
    provenance = "CALCULATION_ONLY"

    def __init__(self, *, requests: Mapping[str, dict]) -> None:
        if not isinstance(requests, Mapping):
            raise InvalidBookingQuoteRecord("requests must be a mapping")
        copied = {}
        for identity, entry in requests.items():
            try:
                _ident(identity)
                if type(entry) is not dict or set(entry) != {"reservation_id", "request_text"}:
                    raise InvalidBookingQuoteRecord("requires reservation_id and request_text")
                _ident(entry["reservation_id"])
                if type(entry["request_text"]) is not str:
                    raise InvalidBookingQuoteRecord("request_text must be text")
            except GateError as error:
                raise InvalidBookingQuoteRecord(str(error)) from error
            copied[identity] = MappingProxyType(dict(entry))
        self._requests = MappingProxyType(copied)
        self._calls: list[str] = []

    @property
    def requests(self) -> Mapping:
        return self._requests

    @property
    def calls(self) -> tuple[str, ...]:
        return tuple(self._calls)

    def fetch(self, recording_id: str) -> dict | None:
        self._calls.append(recording_id)
        entry = self._requests.get(recording_id)
        if entry is None:
            return None
        quote = calculate_booking_quote(entry["request_text"])
        return {"reservation_id": entry["reservation_id"],
                "amount": _money(int(quote["totals"]["payableAtoms"])),
                "quote_ref": quote["quoteHash"]}
