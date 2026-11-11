"""Strict JSONL interface to one synthetic, in-memory payment effect session.

One fixture initializes one private in-memory Core. Request lines are either a
four-field effect command or an explicit local view record. ``send_effect`` is a
local intent only: this process performs no provider, bank, chain or network I/O.
"""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import sys

if __package__:
    from .payment_effect_fixture import (
        FixtureError,
        decode_json,
        exact_fields,
        load_fixture,
        validate_json,
    )
    from .payment_effect_session import (
        EFFECT_ACTIONS,
        PaymentEffectLocalError,
        PaymentEffectSessionClosed,
        Rejected,
    )
else:
    from payment_effect_fixture import (
        FixtureError,
        decode_json,
        exact_fields,
        load_fixture,
        validate_json,
    )
    from payment_effect_session import (
        EFFECT_ACTIONS,
        PaymentEffectLocalError,
        PaymentEffectSessionClosed,
        Rejected,
    )

EVIDENCE_CLASS = "synthetic"
NOTICE = (
    "Synthetic local payment effect desk. send_effect records a local intent only; "
    "no provider, bank, chain or network transmission occurs."
)

_COMMAND_FIELDS = {"operationId", "actor", "action", "body"}
_VIEW_FIELDS = {"effectIds", "tradeIds", "accounts"}


def _local_error(error):
    return {
        "localError": {
            "type": type(error).__name__,
            "message": str(error),
        }
    }


def _rejection(error):
    # Preserve the Core rejection text unchanged; do not re-label it.
    return {"error": str(error), "rejected": True}


def _emit(value):
    frame = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ) + "\n"
    if sys.stdout.write(frame) != len(frame):
        raise OSError("short JSON frame write")
    sys.stdout.flush()


def _view(session, selectors):
    exact_fields(selectors, _VIEW_FIELDS, "view")
    for name in sorted(_VIEW_FIELDS):
        value = selectors[name]
        if type(value) is not list or any(type(item) is not str for item in value):
            raise FixtureError(f"view {name} must be an array of identifiers")
    return {
        "evidenceClass": EVIDENCE_CLASS,
        "notice": NOTICE,
        "view": session.view(
            effect_ids=selectors["effectIds"],
            trade_ids=selectors["tradeIds"],
            accounts=selectors["accounts"],
        ),
    }


def dispatch_request(session, request):
    """Validate one local request shape, then forward it unchanged once."""
    validate_json(request)
    if type(request) is not dict:
        raise FixtureError("request must be an object")
    if "view" in request:
        exact_fields(request, {"view"}, "request")
        return _view(session, request["view"])
    exact_fields(request, _COMMAND_FIELDS, "request")
    action = request["action"]
    if type(action) is not str or action not in EFFECT_ACTIONS:
        raise FixtureError("unsupported local effect action: %r" % (action,))
    receipt = session.execute(
        request["operationId"], request["actor"], action, request["body"]
    )
    return {
        "evidenceClass": EVIDENCE_CLASS,
        "notice": NOTICE,
        "receipt": receipt,
    }


def run_requests(session, lines):
    """Process lines sequentially. Core rejections continue; framing errors stop."""
    rejected = False
    while True:
        try:
            line = next(lines)
        except StopIteration:
            return 1 if rejected else 0
        except (OSError, UnicodeError) as error:
            _emit(_local_error(error))
            return 2
        try:
            request = decode_json(line)
            result = dispatch_request(session, request)
        except FixtureError as error:
            _emit(_local_error(error))
            return 2
        except Rejected as error:
            result = _rejection(error)
            rejected = True
        except (PaymentEffectLocalError, PaymentEffectSessionClosed) as error:
            _emit(_local_error(error))
            return 2
        _emit(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--requests", required=True, help="JSONL path, or - for stdin")
    args = parser.parse_args(argv)

    session = None
    try:
        session = load_fixture(args.fixture)
        requests = (
            nullcontext(sys.stdin)
            if args.requests == "-"
            else Path(args.requests).open(encoding="utf-8")
        )
        with requests as lines:
            return run_requests(session, lines)
    except (FixtureError, Rejected, OSError, UnicodeError, PaymentEffectLocalError) as error:
        try:
            _emit(_local_error(error))
        except (OSError, UnicodeError):
            pass
        return 2
    finally:
        if session is not None:
            session.close()


if __name__ == "__main__":
    raise SystemExit(main())
