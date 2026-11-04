"""Caller-configured synthetic ticket journey; MOCK_GATE_ONLY, non-production."""

import argparse
import json
from pathlib import Path

from ticket_operations_client import TicketOperationsClient, TicketDeskTransportUncertainty


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    for name in ("offer-id", "listing-id", "list-key", "cancel-key"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--cleanup-timeout", type=float, required=True)
    args = parser.parse_args(argv)
    try:
        client = TicketOperationsClient.launch(args.fixture, cleanup_timeout=args.cleanup_timeout)
    except ValueError as error:
        parser.error(str(error))
    try:
        try:
            def send(operation, arguments):
                reply = client.request(dict(surface="resale", operation=operation, arguments=arguments))
                print(json.dumps(reply, sort_keys=True, allow_nan=False), flush=True)
                return reply

            listed = send("list_resale", dict(offer_id=args.offer_id, listing_id=args.listing_id,
                                              idempotency_key=args.list_key))
            if "error" in listed:
                return 1
            listing = listed["receipt"]["listing"]
            identity = dict(listing_id=listing["listing_id"])
            if "error" in send("view", identity):
                return 1
            if "error" in send("cancel_listing", dict(**identity, seller_role=listing["seller_role"],
                                                       idempotency_key=args.cancel_key)):
                return 1
            if "error" in send("view", identity):
                return 1
        finally:
            exit_code = client.close()
    except TicketDeskTransportUncertainty as error:
        # Local diagnostic only: no invented business error and no resend.
        parser.exit(2, f"{error}\n")
    # A child that exits nonzero during cleanup means the journey is not clean.
    return 0 if exit_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
