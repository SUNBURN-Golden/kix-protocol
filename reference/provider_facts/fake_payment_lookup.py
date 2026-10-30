"""Deterministic in-memory lookup fake. Analog, NOT Toss; no authentication.

Recordings are immutable text, never provider responses. Explicit fault markers
need no clock, network, timeout policy, queue consumption or automatic retry.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from provider_facts import PaymentRef, ProviderFactsError


@dataclass(frozen=True)
class SyntheticLookupScope:
    """Explicit local fixture configuration, never an account authorization."""

    provider: str
    account: str
    environment: str

    def __post_init__(self) -> None:
        for value in (self.provider, self.account, self.environment):
            if not (type(value) is str and 0 < len(value) <= 100 and value.strip() == value):
                raise ProviderFactsError("INVALID_SYNTHETIC_SCOPE")

    def matches(self, payment_ref: PaymentRef) -> bool:
        return (payment_ref.provider, payment_ref.account, payment_ref.environment) == (
            self.provider, self.account, self.environment,
        )


class SyntheticLookupFault(Enum):
    TIMEOUT = "synthetic_timeout"
    ERROR = "synthetic_lookup_error"


class FakeLookupError(Exception):
    """Explicit synthetic lookup failure, with no absence/finality meaning."""


_NOT_FOUND_TEXT = (
    '{"source":"synthetic_authenticated_lookup_fixture","outcome":"not_found"}'
)


class FakePaymentLookup:
    """One fixed text/fault per complete PaymentRef; calls are observable.

    Constructor input is copied. Public recordings and scope are read-only;
    calls returns an immutable snapshot. Repeated explicit calls do not consume
    or rewrite recordings. A missing key returns a synthetic not-found body.
    """

    def __init__(
        self, *, scope: SyntheticLookupScope,
        recordings: Mapping[PaymentRef, str | SyntheticLookupFault],
    ) -> None:
        if type(scope) is not SyntheticLookupScope:
            raise TypeError("scope must be SyntheticLookupScope")
        copied = dict(recordings)
        for payment_ref, recording in copied.items():
            if type(payment_ref) is not PaymentRef:
                raise TypeError("recording keys must be PaymentRef")
            if type(recording) not in (str, SyntheticLookupFault):
                raise TypeError("recordings must be text or SyntheticLookupFault")
        self._scope = scope
        self._recordings = MappingProxyType(copied)
        self._calls: list[PaymentRef] = []

    @property
    def scope(self) -> SyntheticLookupScope:
        return self._scope

    @property
    def recordings(self) -> Mapping[PaymentRef, str | SyntheticLookupFault]:
        return self._recordings

    @property
    def calls(self) -> tuple[PaymentRef, ...]:
        return tuple(self._calls)

    def lookup(self, payment_ref: PaymentRef) -> str:
        if type(payment_ref) is not PaymentRef:
            raise ProviderFactsError("INVALID_PAYMENT_REF")
        self._calls.append(payment_ref)
        if not self.scope.matches(payment_ref):
            raise FakeLookupError("synthetic scope mismatch")
        recording = self.recordings.get(payment_ref, _NOT_FOUND_TEXT)
        if recording is SyntheticLookupFault.TIMEOUT:
            raise TimeoutError("synthetic timeout")
        if recording is SyntheticLookupFault.ERROR:
            raise FakeLookupError("synthetic lookup error")
        return recording
