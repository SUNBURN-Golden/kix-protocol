"""Explicit synthetic transcript plus response-derived current reward reads."""

import argparse
from pathlib import Path

from reward_client import RewardClient, RewardClientStateError, RewardTransportUncertainty
from reward_fixture import FixtureError, decode_json
from token_reward_model import _canonical


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--requests", type=Path, required=True, help="caller-selected JSONL transcript")
    parser.add_argument("--cleanup-timeout", type=float, required=True)
    args = parser.parse_args(argv)
    try:
        with args.requests.open(encoding="utf-8") as lines:
            client = RewardClient.launch(args.fixture, cleanup_timeout=args.cleanup_timeout)
            try:
                def send(request):
                    reply = client.request(request)
                    print(_canonical(reply), flush=True)
                    return reply

                for line in lines:
                    reply = send(decode_json(line))
                    if "error" in reply:
                        return 1
                    if "receipt" in reply:
                        # This example explicitly chooses the next request after
                        # seeing the reply. The client inserts no reads.
                        current = send({"operation": "view", "arguments": {
                            "reward_id_value": reply["receipt"]["reward"]["reward_id"]}})
                        if "error" in current:
                            return 1
            finally:
                exit_code = client.close()
        return 0 if exit_code == 0 else 1
    except (RewardTransportUncertainty, RewardClientStateError, FixtureError,
            OSError, UnicodeError, ValueError) as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
