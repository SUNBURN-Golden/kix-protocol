"""Strict JSONL interface to one synthetic, in-memory F4 reward session."""

import argparse
from contextlib import nullcontext
from pathlib import Path
import sys

from reward_fixture import FixtureError, decode_json, exact_fields, load_fixture, validate_json
from reward_session import RewardSession
from token_reward_model import PROVENANCE, TokenRewardError, _canonical


_IDENTITY = {"reward_id_value", "idempotency_key"}
# Explicit local selectors, not protocol commands or arbitrary attribute access.
# Method, required fields, optional fields, output field.
_DISPATCH = {
    "observe": (RewardSession.observe,
                {"reward_key", "idempotency_key", "source_view", "rule_version", "amount", "source_kind"},
                set(), "receipt"),
    "hold": (RewardSession.hold, _IDENTITY, set(), "receipt"),
    "mark_eligible": (RewardSession.mark_eligible,
                      _IDENTITY | {"window_closed", "source_view", "abuse_clear"},
                      {"abuse_kind", "recipient_cap", "program_cap"}, "receipt"),
    "submit": (RewardSession.submit,
               _IDENTITY | {"approval_ref", "signed_bytes_digest", "spend_pool"},
               {"budget_ceiling", "execution_permit"}, "receipt"),
    "observe_transfer_effects": (RewardSession.observe_transfer_effects,
                                 _IDENTITY | {"effects_digest", "outcome"}, set(), "receipt"),
    "reconcile_unknown": (RewardSession.reconcile_unknown,
                          _IDENTITY | {"same_digest", "resolution"}, set(), "receipt"),
    "observe_source_cancel": (RewardSession.observe_source_cancel,
                              _IDENTITY | {"source_view", "reason"}, set(), "receipt"),
    "observe_krw_refund": (RewardSession.observe_krw_refund,
                           _IDENTITY | {"source_view", "reason"}, set(), "receipt"),
    "supersede": (RewardSession.supersede,
                  _IDENTITY | {"approval_ref", "rule_version"}, set(), "receipt"),
    "view": (RewardSession.view, {"reward_id_value"}, set(), "view"),
    "reward_ids": (RewardSession.reward_ids, set(), set(), "reward_ids"),
    "pool_view": (RewardSession.pool_view, set(), set(), "pool_view"),
}
_APPROVAL = {"record_id", "generation", "authority_id", "actor_type", "action",
             "scope_ref", "evidence_refs"}


def dispatch_request(session: RewardSession, request: dict) -> dict:
    """Check the whole request shape before calling any session method once."""
    validate_json(request)
    exact_fields(request, {"operation", "arguments"}, "request")
    operation = request["operation"]
    if type(operation) is not str or operation not in _DISPATCH:
        raise FixtureError("unsupported session operation")
    method, required, optional, result_key = _DISPATCH[operation]
    arguments = request["arguments"]
    exact_fields(arguments, required, f"{operation} arguments", optional)
    if "reward_key" in arguments:
        exact_fields(arguments["reward_key"],
                     {"program", "source_op_id", "recipient", "kind"}, "reward_key")
    if "source_view" in arguments and type(arguments["source_view"]) is not dict:
        raise FixtureError("source_view must be an object")
    if "approval_ref" in arguments:
        approval = arguments["approval_ref"]
        exact_fields(approval, _APPROVAL, "approval_ref", {"prior_record"})
        if type(approval["evidence_refs"]) is not list:
            raise FixtureError("approval evidence_refs must be an array")
    if arguments.get("execution_permit") is not None:
        exact_fields(arguments["execution_permit"],
                     {"fence_ref", "signed_bytes_digest"}, "execution_permit")
    return {"operation": operation, "provenance": PROVENANCE,
            result_key: method(session, **arguments)}


def _error(operation, error):
    detail = ({"code": error.code} if isinstance(error, TokenRewardError)
              else {"type": type(error).__name__, "message": str(error)})
    return {"operation": operation, "provenance": PROVENANCE, "error": detail}


def _emit(value):
    print(_canonical(value), flush=True)


def run_requests(session: RewardSession, lines) -> int:
    rejected = False
    for line in lines:
        operation = None
        try:
            request = decode_json(line)
            if type(request) is dict and type(request.get("operation")) is str:
                operation = request["operation"]
            result = dispatch_request(session, request)
        except FixtureError as error:
            _emit(_error(operation, error))
            return 2
        except TokenRewardError as error:
            # A subsequent supplied line is the only way another call occurs.
            result = _error(operation, error)
            rejected = True
        _emit(result)
    return 1 if rejected else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--requests", required=True, help="JSONL path, or - for stdin")
    args = parser.parse_args(argv)
    try:
        session = load_fixture(args.fixture)
        requests = (nullcontext(sys.stdin) if args.requests == "-"
                    else Path(args.requests).open(encoding="utf-8"))
        with requests as lines:
            return run_requests(session, lines)
    except (FixtureError, TokenRewardError, OSError, UnicodeError) as error:
        _emit(_error(None, error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
