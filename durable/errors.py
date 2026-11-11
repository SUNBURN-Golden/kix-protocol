"""Error types for the durable layer. No psycopg import."""

from __future__ import annotations

from readiness.store import StoreError


class CommitUnknown(StoreError):
    """The commit call failed after it was sent. The effect may or may not exist."""

    def __init__(self):
        super().__init__('COMMIT_UNKNOWN')


class Backpressure(Exception):
    """Nothing was acknowledged. The caller must not send a receipt ACK."""

    def __init__(self, code, budget_class=None, reason=None):
        super().__init__(code)
        self.code = code
        self.budget_class = budget_class
        self.reason = reason


class UnknownOperation(Exception):
    """Apply hook signal: no authoritative operation-order binding is known yet."""


class NormalizationError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class AliasConflict(StoreError):
    def __init__(self):
        super().__init__('ALIAS_CONFLICT')
