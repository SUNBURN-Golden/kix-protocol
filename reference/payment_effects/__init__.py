"""Synthetic local payment effect desk around the unchanged v0.3-rc1 Core.

This package exposes no new protocol command and connects no settlement or
Finance FSM. ``send_effect`` is a local intent, not a transmission.
"""

from .payment_effect_fixture import (
    FixtureError,
    decode_json,
    load_fixture,
    session_from_fixture,
    validate_fixture,
)
from .payment_effect_session import (
    EFFECT_ACTIONS,
    Core,
    PaymentEffectLocalError,
    PaymentEffectSession,
    PaymentEffectSessionClosed,
    Rejected,
)

__all__ = [
    "Core",
    "EFFECT_ACTIONS",
    "FixtureError",
    "PaymentEffectLocalError",
    "PaymentEffectSession",
    "PaymentEffectSessionClosed",
    "Rejected",
    "decode_json",
    "load_fixture",
    "session_from_fixture",
    "validate_fixture",
]
