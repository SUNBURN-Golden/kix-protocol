"""One explicit, sequential, synthetic in-memory payment effect session.

The session owns a private SQLite ``:memory:`` database created by the unchanged
``reference/v0.3-rc1`` Core. It forwards only the four already-published effect
commands and supplies no policy, retry, dispatch or accounting behaviour of its
own. ``send_effect`` records a local intent; this module performs no network I/O.
"""

from __future__ import annotations

import copy
from pathlib import Path
import sys


def _load_reference_types():
    """Import the frozen Core without copying or modifying its source tree."""
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from integration_gate.catalogue import reference_types

    return reference_types()


Core, Rejected = _load_reference_types()

# Exactly the four published effect commands this local desk exposes.
EFFECT_ACTIONS = frozenset(
    {"prepare_effect", "send_effect", "abort_effect", "observe_effect"}
)


class PaymentEffectLocalError(ValueError):
    """A local tooling refusal, not a Core protocol/domain rejection."""


class PaymentEffectSessionClosed(PaymentEffectLocalError):
    """The session was used after ``close()``."""


def _selectors(name, values):
    if type(values) is not list or any(type(value) is not str for value in values):
        raise PaymentEffectLocalError(f"{name} must be an array of identifiers")
    return values


class PaymentEffectSession:
    """Forward explicit caller inputs once against one private in-memory Core."""

    def __init__(self, core):
        self._core = core
        self._closed = False

    @classmethod
    def from_fixture(cls, fixture):
        """Validate and initialize a fresh session from an explicit fixture."""
        if __package__:
            from .payment_effect_fixture import session_from_fixture
        else:
            from payment_effect_fixture import session_from_fixture

        return session_from_fixture(fixture)

    def _require_open(self):
        if self._closed:
            raise PaymentEffectSessionClosed("local payment effect session is closed")

    def execute(self, operation_id, actor, action, body):
        """Forward one effect command; Core receipts, errors and replay are unchanged."""
        self._require_open()
        if type(action) is not str or action not in EFFECT_ACTIONS:
            raise PaymentEffectLocalError(
                "unsupported local effect action: %r" % (action,)
            )
        return self._core.execute(operation_id, actor, action, copy.deepcopy(body))

    def view(self, *, effect_ids, trade_ids, accounts):
        """Return detached copies selected from one Core snapshot; never execute."""
        self._require_open()
        effect_ids = _selectors("effectIds", effect_ids)
        trade_ids = _selectors("tradeIds", trade_ids)
        accounts = _selectors("accounts", accounts)

        snapshot = self._core.snapshot()
        effects = snapshot["effects"]
        trades = snapshot["trades"]
        balances = snapshot["balances"]
        return {
            "effects": {
                effect_id: (copy.deepcopy(effects[effect_id])
                            if effect_id in effects else None)
                for effect_id in effect_ids
            },
            "trades": {
                trade_id: (copy.deepcopy(trades[trade_id])
                           if trade_id in trades else None)
                for trade_id in trade_ids
            },
            "balances": {
                account: balances.get(account, 0) for account in accounts
            },
        }

    def close(self):
        """Close the owned database exactly once; repeated calls are harmless."""
        if not self._closed:
            self._closed = True
            self._core.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
