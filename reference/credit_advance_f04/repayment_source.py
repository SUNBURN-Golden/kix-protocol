"""Internal synthetic repayment interface; no bank receipt or wire semantics."""

from typing import Protocol, TypedDict


class RepaymentRecord(TypedDict):
    """Existing FSM inputs. Numeric validation belongs to the FSM alone."""

    advance_id: str
    repay_id: str
    sequence: object
    amount: object


class RepaymentSource(Protocol):
    def fetch(self, advance_id: str, repay_id: str) -> dict | None:
        """Return the selected synthetic note or absence; never infer a repayment."""
        ...


class RepaymentSourceError(Exception):
    """Local source failure, not a protocol error or external repayment fact."""


class RepaymentNotFound(RepaymentSourceError):
    """The explicitly requested synthetic recording is absent."""


class InvalidRepaymentRecord(RepaymentSourceError):
    """A record is not a document with exactly the required fields."""


class RepaymentIdentityMismatch(RepaymentSourceError):
    """A record is bound to another advance or repayment identity."""
