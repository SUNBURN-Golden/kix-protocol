"""Session forwarding coverage; underlying lifecycle predicates have existing tests."""

import inspect
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from reward_fsm import RewardMachine
from reward_session import RewardSession
from tl4_support import committed_view, funded_opening, hex_digest, human_approval, reward_key
from token_reward_model import TokenRewardError, reward_id


FIXTURES = Path(__file__).with_name("fixtures")
OPERATIONS = ("observe", "hold", "mark_eligible", "submit", "observe_transfer_effects",
              "reconcile_unknown", "observe_source_cancel", "observe_krw_refund",
              "supersede", "view", "reward_ids", "pool_view")


def requests(name):
    return [json.loads(line) for line in (FIXTURES / (name + ".jsonl")).read_text().splitlines()]


class RewardSessionTests(unittest.TestCase):
    def test_explicit_public_signatures_match_machine_including_optional_none(self):
        for operation in OPERATIONS:
            with self.subTest(operation=operation):
                self.assertEqual(inspect.signature(getattr(RewardSession, operation)),
                                 inspect.signature(getattr(RewardMachine, operation)))
        self.assertEqual({name for name in dir(RewardSession) if not name.startswith("_")},
                         set(OPERATIONS))

    def test_each_journey_matches_direct_machine_receipts_errors_and_reads(self):
        for journey in ("participation", "cancellation", "boundaries", "unknown_pending"):
            session = RewardSession(funded_opening())
            machine = RewardMachine(funded_opening())
            lines = requests(journey)
            if journey == "unknown_pending":
                lines += requests("unknown_resolution")
            for request in lines:
                operation, arguments = request["operation"], request["arguments"]
                with self.subTest(journey=journey, operation=operation, arguments=arguments):
                    try:
                        expected = getattr(machine, operation)(**arguments)
                    except TokenRewardError as error:
                        with self.assertRaises(TokenRewardError) as caught:
                            getattr(session, operation)(**arguments)
                        self.assertEqual(caught.exception.code, error.code)
                    else:
                        self.assertEqual(getattr(session, operation)(**arguments), expected)
                    self.assertEqual(session.pool_view(), machine.pool_view())
                    self.assertEqual(session.reward_ids(), machine.reward_ids())
                    for rid in machine.reward_ids():
                        self.assertEqual(session.view(rid), machine.view(rid))

    def test_optional_values_and_approval_omission_are_forwarded_without_rewriting(self):
        session = RewardSession(funded_opening())
        approval = human_approval()
        with patch.object(session, "_machine") as machine:
            session.mark_eligible("r", idempotency_key="e", window_closed=False,
                                  source_view=committed_view(), abuse_clear=False,
                                  abuse_kind="SELF_TRADE", recipient_cap=0, program_cap=None)
            self.assertEqual(machine.mark_eligible.call_args.kwargs["recipient_cap"], 0)
            self.assertIs(machine.mark_eligible.call_args.kwargs["window_closed"], False)
            session.submit("r", idempotency_key="s", approval_ref=approval,
                           signed_bytes_digest=hex_digest(1), spend_pool="PROTOCOL_REVENUE")
            forwarded = machine.submit.call_args.kwargs
            self.assertIs(forwarded["approval_ref"], approval)
            self.assertNotIn("prior_record", approval)
            self.assertIsNone(forwarded["budget_ceiling"])
            self.assertIsNone(forwarded["execution_permit"])
            self.assertEqual(len(machine.mock_calls), 2)

    def test_supersede_parity_and_omitted_versus_null_optionals(self):
        for nulls in (False, True):
            session, machine = RewardSession(funded_opening()), RewardMachine(funded_opening())
            rid = reward_id(**reward_key())
            steps = [
                ("observe", dict(reward_key=reward_key(), idempotency_key="o",
                                 source_view=committed_view(), rule_version="v1", amount=10,
                                 source_kind="RESERVATION")),
                ("hold", dict(reward_id_value=rid, idempotency_key="h")),
                ("mark_eligible", dict(reward_id_value=rid, idempotency_key="e",
                                       source_view=committed_view(), window_closed=True,
                                       abuse_clear=True, **({"recipient_cap": None,
                                       "program_cap": None, "abuse_kind": None} if nulls else {}))),
                ("submit", dict(reward_id_value=rid, idempotency_key="s",
                                approval_ref={**human_approval(), **({"prior_record": None} if nulls else {})},
                                signed_bytes_digest=hex_digest(1), spend_pool="PROTOCOL_REVENUE",
                                **({"budget_ceiling": None, "execution_permit": None} if nulls else {}))),
                ("observe_transfer_effects", dict(reward_id_value=rid, idempotency_key="f",
                                                   effects_digest=hex_digest(2), outcome="SUCCESS")),
                ("supersede", dict(reward_id_value=rid, idempotency_key="x",
                                   approval_ref=human_approval("supersession"), rule_version="v2")),
            ]
            for operation, arguments in steps:
                self.assertEqual(getattr(session, operation)(**arguments),
                                 getattr(machine, operation)(**arguments))
            self.assertEqual(session.view(rid), machine.view(rid))
            self.assertEqual(session.pool_view(), machine.pool_view())

    def test_no_implicit_opening_balances_and_sessions_are_isolated(self):
        with self.assertRaises(TypeError):
            RewardSession()
        with self.assertRaises(TokenRewardError):
            RewardSession({})
        first, second = RewardSession(funded_opening()), RewardSession(funded_opening())
        first.observe(**requests("participation")[0]["arguments"])
        self.assertEqual(second.reward_ids(), [])


if __name__ == "__main__":
    unittest.main()
