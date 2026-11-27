"""Builder-authored, deterministic, stdlib-only MOCK reward snapshots.

Only the TK-7 payout bound and TK-8 effect/state separation are explicit
contract predicates (class A). Copying, complete replay envelopes and snapshot
lifetime are source-informed characterizations (class B), not new contracts.
Fixture amounts, approval/fence slots and metadata select no owner policy.
"""

from copy import deepcopy
import unittest

from reward_fsm import ELIGIBLE, ISSUED, OBSERVED, UNKNOWN, RewardMachine
from tl4_support import committed_view, funded_opening, hex_digest, human_approval, reward_key
from token_reward_model import ALWAYS_FALSE_FLAGS, PROVENANCE, reward_id

AMOUNT = 4
DIGEST = hex_digest(1)
EFFECTS = hex_digest(3)


def approval(record_id):
    value = human_approval(record_id)
    # Raw fingerprints must match the normalized journal body on restore.
    value["prior_record"] = None
    return value


def source_view():
    value = committed_view()
    # Opaque synthetic metadata: probes deeper input copying than phase alone.
    value["snapshot_evidence"] = {"refs": ["source-slot-1"]}
    return value


def rid(label):
    return reward_id(**reward_key("op-snap-" + label))


def script_commands(phase):
    """Fresh arguments on each invocation, including every identical replay."""
    commands = []

    def add(key, op, subject, **body):
        commands.append((key, op, subject, body))

    def submit(key, label, record_id, digest=DIGEST, permit=None):
        add(key, "submit", rid(label), approval_ref=approval(record_id),
            signed_bytes_digest=digest, spend_pool="PROTOCOL_REVENUE",
            execution_permit=permit)

    if phase == 1:
        for label in ("a", "b"):
            add(label + "-obs", "observe", reward_key("op-snap-" + label),
                source_view=source_view(), rule_version="rule-v1", amount=AMOUNT,
                source_kind="SETTLEMENT")
            add(label + "-hold", "hold", rid(label))
            add(label + "-elig", "mark_eligible", rid(label), window_closed=True,
                source_view=source_view(), abuse_clear=True)
            submit(label + "-sub", label, "appr-" + label + "1")
            add(label + "-fx", "observe_transfer_effects", rid(label),
                effects_digest=EFFECTS, outcome="SUCCESS" if label == "a" else "UNKNOWN")
            if label == "a":
                add("a-krw", "observe_krw_refund", rid("a"),
                    source_view=source_view(), reason="KRW_REFUND")
            else:
                submit("b-resend", "b", "appr-b1", permit={
                    "fence_ref": "fence-slot-1", "signed_bytes_digest": DIGEST})
    else:
        assert phase == 2
        add("a-sup", "supersede", rid("a"), approval_ref=approval("appr-a2"),
            rule_version="rule-v2")
        submit("a-sub2", "a", "appr-a3", hex_digest(2))
        add("a-fx2", "observe_transfer_effects", rid("a"),
            effects_digest=EFFECTS, outcome="SUCCESS")
        add("b-rec", "reconcile_unknown", rid("b"),
            same_digest=DIGEST, resolution="SUCCESS")
    return commands


def invoke(machine, command):
    key, op, subject, body = command
    return getattr(machine, op)(subject, idempotency_key=key, **body)


def run_script(machine, record=None, phase=1):
    saved = {}
    for command in script_commands(phase):
        result = invoke(machine, command)
        saved[command[0]] = deepcopy(result)
        if record is not None:
            record(command, result)
    return saved


def mutate(test, obj, fn):
    before = deepcopy(obj)
    fn(obj)
    test.assertNotEqual(obj, before, "mutation must change the caller-owned object")


class IsolationChecks:
    """Shared checks, with no collected tests or private machine access."""

    def setUp(self):
        self.subject = RewardMachine(funded_opening())
        self.control = RewardMachine(funded_opening())

    def assert_predicates(self, machine):
        """Class A: TK-7/TK-8; synthetic spend/flag checks support the evidence."""
        keys = {entry["idempotency_key"] for entry in machine.export_journal()}
        payouts = 0
        for label in ("a", "b"):
            if label + "-obs" not in keys:
                continue
            view = machine.view(rid(label))
            expected = (int("a-fx" in keys) + int("a-fx2" in keys)
                        if label == "a" else int("b-rec" in keys))
            self.assertEqual(view["payout_effect_count"], expected)
            self.assertLessEqual(expected, 1 + view["supersession_count"])
            self.assertEqual(view["source_op_id"], "op-snap-" + label)
            self.assertEqual(view["reward_id"], rid(label))
            self.assertNotIn(view["krw_effect_id"], view["token_effect_ids"])
            self.assertNotEqual(view["krw_effect_id"], view["token_effect_id"])
            if label == "a" and "a-krw" in keys:
                self.assertEqual(view["krw_phase"], "KRW_REFUND_NOTED")
            if label == "a" and "a-fx2" in keys:
                self.assertEqual(expected, 1 + view["supersession_count"])
                self.assertIs(view["payout_effects"][1]["supersession"], True)
            if label == "b" and "b-resend" in keys:
                self.assertEqual(view["resend_count"], 1)
                self.assertEqual(view["phase"], ISSUED if "b-rec" in keys else UNKNOWN)
            self.assertEqual(view["provenance"], PROVENANCE)
            for flag in ALWAYS_FALSE_FLAGS:
                self.assertIs(view[flag], False)
            payouts += expected
        pool = machine.pool_view()
        self.assertEqual(len(pool["spends"]), payouts)
        self.assertEqual(sum(item["amount"] for item in pool["spends"]), AMOUNT * payouts)
        self.assertEqual(pool["balances"]["PROTOCOL_REVENUE"],
                         funded_opening()["PROTOCOL_REVENUE"] - AMOUNT * payouts)

    def assert_matches_control(self, subject=None):
        subject = self.subject if subject is None else subject
        self.assertEqual(subject.reward_ids(), self.control.reward_ids())
        for reward in self.control.reward_ids():
            self.assertEqual(subject.view(reward), self.control.view(reward))
        self.assertEqual(subject.pool_view(), self.control.pool_view())
        self.assertEqual(subject.canonical_state(), self.control.canonical_state())
        self.assertEqual(subject.state_digest(), self.control.state_digest())
        self.assertEqual(subject.export_journal(), self.control.export_journal())
        self.assert_predicates(subject)

    def assert_replays(self, machine, saved):
        """Class B: compare complete historical envelopes, not current views."""
        before = machine.state_digest()
        for command in script_commands(1) + script_commands(2):
            key = command[0]
            if key not in saved:
                continue
            with self.subTest(replay=key):
                self.assertEqual(invoke(machine, command),
                                 {**saved[key], "duplicate": True, "applied": None})
        self.assertEqual(machine.state_digest(), before)
        self.assert_predicates(machine)

    def advance_pair(self, phase):
        saved = run_script(self.subject, phase=phase)
        self.assertEqual(saved, run_script(self.control, phase=phase))
        self.assert_matches_control()
        if phase == 1:
            for field in ("phase", "token_outcome", "token_effect_ids", "payout_effects"):
                self.assertEqual(saved["a-fx"]["reward"][field], saved["a-krw"]["reward"][field])
            self.assertEqual(saved["a-krw"]["reward"]["krw_phase"], "KRW_REFUND_NOTED")
        return saved

    def checked_mutation(self, obj, fn, machine=None):
        mutate(self, obj, fn)
        self.assert_matches_control(machine)

    def corrupt_reward(self, view, machine=None):
        def change(obj, fn):
            self.checked_mutation(obj, fn, machine)

        change(view["source_view"]["snapshot_evidence"]["refs"], lambda x: x.append("forged-source"))
        change(view["source_view"], lambda x: x.update(phase="MUTATED"))
        if view["approval_ref"] is not None:
            refs = view["approval_ref"]["evidence_refs"]
            change(refs, lambda x: x.append("forged-evidence"))
            change(refs, lambda x: x.__setitem__(0, "replaced-evidence"))
        for supersession in view["supersessions"]:
            change(supersession["approval_ref"]["evidence_refs"], lambda x: x.append("forged-sup"))
            change(supersession, lambda x: x.update(rule_version="forged-rule"))
        effects = view["payout_effects"]
        if effects:
            change(effects[0], lambda x: x.update(outcome="FAILED"))
        change(effects, lambda x: x.append({"effect_id": "forged", "outcome": "SUCCESS"}))
        change(effects, lambda x: x.clear())
        change(view["token_effect_ids"], lambda x: x.append(view["krw_effect_id"]))

    def corrupt_result(self, result, machine=None):
        self.corrupt_reward(result["reward"], machine)
        if result["effect"] is not None:
            effect = result["effect"]
            for field in ("effect_id", "token_effect_id", "krw_effect_id", "krw_phase"):
                if field in effect:
                    self.checked_mutation(effect, lambda x, field=field: x.update({field: "forged"}), machine)
        self.checked_mutation(result, lambda x: x.pop("reward"), machine)

    def corrupt_journal(self, journal, machine=None):
        for entry in journal:
            body = entry["body"]
            if "approval_ref" in body:
                self.checked_mutation(body["approval_ref"]["evidence_refs"],
                                      lambda x: x.append("forged-journal"), machine)
            if "source_view" in body:
                self.checked_mutation(body["source_view"]["snapshot_evidence"]["refs"],
                                      lambda x: x.append("forged-journal"), machine)
            if "reward_key" in body:
                self.checked_mutation(body["reward_key"], lambda x: x.update(recipient="forged"), machine)
            if body.get("execution_permit") is not None:
                self.checked_mutation(body, lambda x: x.pop("execution_permit"), machine)
        self.checked_mutation(journal[0]["body"]["source_view"], lambda x: x.update(phase="MUTATED"), machine)
        self.checked_mutation(journal[0], lambda x: x.update(reward_id="forged"), machine)


class RewardReplayIsolationTests(IsolationChecks, unittest.TestCase):
    """TK-7/TK-8 class A; envelope/copy assertions remain class B."""

    def test_mutated_first_results_do_not_change_state_or_replay(self):
        raw = {}
        saved = run_script(self.subject, lambda command, result: raw.update({command[0]: result}))
        self.assertEqual(saved, run_script(self.control))
        self.assert_replays(self.subject, saved)
        for result in raw.values():
            self.corrupt_result(result)
            self.assert_replays(self.subject, saved)
        later = {}
        saved.update(run_script(self.subject, lambda command, result: later.update({command[0]: result}), phase=2))
        run_script(self.control, phase=2)
        for result in later.values():
            self.corrupt_result(result)
            self.assert_replays(self.subject, saved)
        self.assert_matches_control()

    def test_mutated_duplicate_results_do_not_change_later_replays(self):
        saved = self.advance_pair(1)
        for phase in (1, 2):
            if phase == 2:
                saved.update(self.advance_pair(2))
            for command in script_commands(1) + (script_commands(2) if phase == 2 else []):
                duplicate = invoke(self.subject, command)
                self.assertEqual(duplicate, {**saved[command[0]], "duplicate": True, "applied": None})
                self.corrupt_result(duplicate)
                self.assert_replays(self.subject, saved)

    def test_restore_replays_complete_first_envelopes(self):
        saved = self.advance_pair(1)
        submits = [entry for entry in self.subject.export_journal() if entry["op"] == "submit"]
        self.assertEqual(len(submits), 3)
        for entry in submits:
            self.assertIn("prior_record", entry["body"]["approval_ref"])
            self.assertIsNone(entry["body"]["approval_ref"]["prior_record"])
        self.assertEqual(saved["a-obs"]["reward"]["phase"], OBSERVED)
        self.assertEqual(saved["a-obs"]["reward"]["accepted_entries"], 1)
        self.assert_replays(self.subject, saved)
        restored = RewardMachine.restore(self.subject.export_journal(), opening_balances=funded_opening())
        self.assert_matches_control(restored)
        self.assert_replays(restored, saved)
        saved.update(self.advance_pair(2))
        run_script(restored, phase=2)
        self.assert_matches_control(restored)
        self.assert_replays(restored, saved)
        restored = RewardMachine.restore(self.subject.export_journal(), opening_balances=funded_opening())
        self.assert_matches_control(restored)
        self.assert_replays(restored, saved)
        self.corrupt_result(invoke(restored, script_commands(2)[-1]), restored)
        self.assert_replays(restored, saved)
        self.assert_matches_control(restored)


class RewardCopyIsolationCharacterizationTests(IsolationChecks, unittest.TestCase):
    """Class B: input/view/export copying and retained snapshot lifetime."""

    def test_mutated_inputs_after_call_are_detached(self):
        saved = {}
        for phase in (1, 2):
            for command, untouched in zip(script_commands(phase), script_commands(phase)):
                result = invoke(self.subject, command)
                self.assertEqual(result, invoke(self.control, untouched))
                saved[command[0]] = deepcopy(result)
                _, op, subject, body = command
                if op == "observe":
                    self.checked_mutation(subject, lambda x: x.update(recipient="forged-input"))
                if "source_view" in body:
                    self.checked_mutation(body["source_view"]["snapshot_evidence"]["refs"],
                                          lambda x: x.append("forged-input"))
                if "approval_ref" in body:
                    self.checked_mutation(body["approval_ref"]["evidence_refs"],
                                          lambda x: x.append("forged-input"))
                if body.get("execution_permit") is not None:
                    self.checked_mutation(body["execution_permit"],
                                          lambda x: x.update(fence_ref="forged-input", signed_bytes_digest=hex_digest(9)))
                self.assert_replays(self.subject, saved)
        self.assert_matches_control()

    def test_mutated_views_and_pool_views_are_detached(self):
        saved = self.advance_pair(1)
        saved.update(self.advance_pair(2))
        for reward in self.subject.reward_ids():
            self.corrupt_reward(self.subject.view(reward))
        pool = self.subject.pool_view()
        self.checked_mutation(pool["balances"], lambda x: x.update(PROTOCOL_REVENUE=999))
        self.checked_mutation(pool["spends"][0], lambda x: x.update(amount=999))
        self.checked_mutation(pool["credits"], lambda x: x.clear())
        self.assert_replays(self.subject, saved)

    def test_mutated_journal_bodies_do_not_reach_state_or_restore(self):
        saved = self.advance_pair(1)
        saved.update(self.advance_pair(2))
        self.corrupt_journal(self.subject.export_journal())
        self.assert_replays(self.subject, saved)
        # Discard corrupt exports; restore only a fresh unmodified journal.
        restore_input = self.subject.export_journal()
        restored = RewardMachine.restore(restore_input, opening_balances=funded_opening())
        self.assert_matches_control(restored)
        self.corrupt_journal(restore_input, restored)
        self.assert_replays(restored, saved)
        self.assert_matches_control(restored)

    def test_retained_snapshots_survive_later_transitions(self):
        first = {}
        saved = run_script(self.subject, lambda command, result: first.update({command[0]: result}))
        self.assertEqual(saved, run_script(self.control))
        snapshots = [*first.values(), self.subject.view(rid("a")),
                     self.subject.view(rid("b")), self.subject.pool_view(), self.subject.export_journal()]
        frozen = deepcopy(snapshots)
        self.assert_replays(self.subject, saved)
        # Advance one command at a time, including the intermediate supersede phase.
        for command, untouched in zip(script_commands(2), script_commands(2)):
            result = invoke(self.subject, command)
            self.assertEqual(result, invoke(self.control, untouched))
            saved[command[0]] = deepcopy(result)
            self.assertEqual(snapshots, frozen)
            self.assert_matches_control()
            self.assert_replays(self.subject, saved)
            if command[0] == "a-sup":
                self.assertEqual(self.subject.view(rid("a"))["phase"], ELIGIBLE)
                self.assertEqual(frozen[-4]["phase"], ISSUED)
        a, b = self.subject.view(rid("a")), self.subject.view(rid("b"))
        self.assertEqual(a["rule_version"], "rule-v2")
        self.assertEqual(a["payout_effect_count"], 2)
        self.assertEqual(b["phase"], ISSUED)
        self.assertEqual(frozen[-3]["phase"], UNKNOWN)
        for old, fresh in zip(frozen[-4:], [a, b, self.subject.pool_view(), self.subject.export_journal()]):
            self.assertNotEqual(old, fresh)


if __name__ == "__main__":
    unittest.main()
