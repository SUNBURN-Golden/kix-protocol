"""Author-side fuzz and repository-boundary checks.

Labels are harness-local, not protocol commands. A pass is not an independent
PASS. The wording scan is an aid. TK-11 stays a human review. The TK-9 scan
is a name scan, not a proof.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

from reward_fsm import RewardMachine
from tl4_support import JUNK, committed_view, funded_opening, hex_digest, reward_key
from token_reward_model import (
    POOLS,
    PoolLedger,
    TokenRewardError,
    collateral_recognized,
    effect_id,
    net_residual_revenue,
    reconcile_supply,
    reward_budget,
    reward_id,
    supply_report,
)

REPO = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".venv", "target", "node_modules", "__pycache__", ".local"}
# not a claim list by itself. The scan skips a line that carries one of these markers.
NEGATION_MARKERS = ("않", "아니", "없", "not", "no ")
CLAIM_NEEDLES = ("legal", "return", "liquidity", "price-keeping", "production-ready", "합법", "인허가", "투자수익", "유동성", "가격 유지", "가격유지")  # not a claim list by itself
SUITES = (
    "settlement_f01_f03",
    "booking_resale_admission",
    "credit_advance_f04",
    "ai_delegation",
)


class JunkAndJournalTests(unittest.TestCase):
    def _ledger(self, ledger, call):
        before = ledger.state_digest()
        try:
            call()
        except TokenRewardError:
            self.assertEqual(ledger.state_digest(), before)
        except Exception as error:
            raise AssertionError(type(error).__name__) from error

    def _machine(self, machine, call):
        digest = machine.state_digest()
        journal = machine.export_journal()
        try:
            call()
        except TokenRewardError:
            self.assertEqual(machine.state_digest(), digest)
            self.assertEqual(machine.export_journal(), journal)
        except Exception as error:
            raise AssertionError(type(error).__name__) from error

    def test_TL4_junk_values_on_the_fenced_surface_raise_token_reward_error(self):
        """Junk values either are accepted or raise TokenRewardError.

        A TokenRewardError leaves canonical state and the journal unchanged.
        effect_id is not in this surface. Its non-canonical behaviour is a
        separate characterization. Labels are harness-local.
        """

        for junk in JUNK:
            ledger = PoolLedger({pool: 3 for pool in POOLS})
            self._ledger(ledger, lambda junk=junk: ledger.credit(junk, 1, "src"))
            self._ledger(ledger, lambda junk=junk: ledger.credit("PROTOCOL_REVENUE", junk, "src"))
            self._ledger(ledger, lambda junk=junk: ledger.credit("PROTOCOL_REVENUE", 1, junk))
            self._ledger(ledger, lambda junk=junk: ledger.spend(junk, 1, "program-1"))
            self._ledger(ledger, lambda junk=junk: ledger.spend("PROTOCOL_REVENUE", junk, "program-1"))
            self._expect_fenced(lambda junk=junk: collateral_recognized(junk, []))
            self._expect_fenced(lambda junk=junk: collateral_recognized(1, junk if type(junk) is list else [junk]))
            self._expect_fenced(lambda junk=junk: reward_id(program=junk, source_op_id="a", recipient="b", kind="c"))
            self._expect_fenced(lambda junk=junk: supply_report(junk))
            self._expect_fenced(lambda junk=junk: reconcile_supply(junk, 0))
            self._expect_fenced(
                lambda junk=junk: reward_budget(
                    cap=junk,
                    ratio_numerator=1,
                    ratio_denominator=2,
                    net_residual=1,
                    periods=1,
                )
            )
            self._expect_fenced(
                lambda junk=junk: net_residual_revenue(
                    gross_revenue=junk,
                    refundable_window_revenue=0,
                    customer_deposit_outlay=0,
                    organizer_settlement_outlay=0,
                    refund_reserve_outlay=0,
                    operating_cost=0,
                    loss_provision=0,
                )
            )
            machine = RewardMachine(funded_opening())
            key = reward_key()
            view = committed_view()
            self._machine(machine, lambda junk=junk: machine.observe(junk, idempotency_key="k", source_view=view, rule_version="v", amount=1, source_kind="SETTLEMENT"))
            self._machine(machine, lambda junk=junk: machine.observe(key, idempotency_key=junk, source_view=view, rule_version="v", amount=1, source_kind="SETTLEMENT"))
            self._machine(machine, lambda junk=junk: machine.observe(key, idempotency_key="k2", source_view=junk, rule_version="v", amount=1, source_kind="SETTLEMENT"))
            self._machine(machine, lambda junk=junk: machine.hold(junk, idempotency_key="h"))
            self._machine(machine, lambda junk=junk: machine.view(junk))
            self._machine(machine, lambda junk=junk: machine.reject_external(junk))
            self._machine(
                machine,
                lambda junk=junk: machine.submit(
                    "missing-reward-id",
                    idempotency_key="s",
                    approval_ref=junk,
                    signed_bytes_digest=hex_digest(1),
                    spend_pool="PROTOCOL_REVENUE",
                ),
            )

    def _expect_fenced(self, call):
        try:
            call()
        except TokenRewardError:
            return
        except Exception as error:
            raise AssertionError(type(error).__name__) from error

    def test_TL4_effect_id_noncanonical_input_is_characterized(self):
        """Contract-undefined. effect_id does not document an error class.

        A set argument raises TypeError. This is an author-side characterization
        (AGENTS §8.B). The product module is not patched from this harness.
        """

        with self.assertRaises(TypeError):
            effect_id("reward", "token", set())

    def test_TL4_mutated_journals_raise_token_reward_error(self):
        machine = RewardMachine(funded_opening())
        machine.observe(
            reward_key(),
            idempotency_key="obs-1",
            source_view=committed_view(),
            rule_version="rule-a",
            amount=4,
            source_kind="SETTLEMENT",
        )
        machine.hold(machine.reward_ids()[0], idempotency_key="hold-1")
        original = machine.export_journal()
        opening = funded_opening()
        mutations = []
        for entry in original:
            for key in ("op", "idempotency_key", "reward_id", "body"):
                dropped = dict(entry)
                dropped.pop(key)
                mutations.append(dropped)
            wrong_op = dict(entry)
            wrong_op["op"] = 1
            mutations.append(wrong_op)
            unknown = dict(entry)
            unknown["op"] = "not-an-op"
            mutations.append(unknown)
            swapped = dict(entry)
            swapped["reward_id"] = "swapped-reward-id"
            mutations.append(swapped)
            extra = dict(entry)
            extra["extra"] = 1
            mutations.append(extra)
            bad_body = dict(entry)
            bad_body["body"] = []
            mutations.append(bad_body)
        mutations.append({"op": "hold", "idempotency_key": "k", "reward_id": "missing", "body": {"nope": set()}})
        for mutation in mutations:
            with self.assertRaises(TokenRewardError):
                RewardMachine.restore([mutation], opening_balances=opening)
        with self.assertRaises(TokenRewardError):
            RewardMachine.restore({"not": "a list"}, opening_balances=opening)
        empty = RewardMachine.restore([], opening_balances=opening)
        self.assertEqual(empty.state_digest(), RewardMachine(opening).state_digest())
        restored = RewardMachine.restore(original, opening_balances=opening)
        self.assertEqual(restored.state_digest(), machine.state_digest())


class RepoBoundaryTests(unittest.TestCase):
    def test_TL4_TK02_T1_only_the_locked_move_manifest_exists(self):
        """TL1-TK02-T1 repo-state slice. No second Move manifest. Not a package proof."""

        found = []
        for path in REPO.rglob("Move.toml"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            found.append(path.relative_to(REPO).as_posix())
        self.assertEqual(found, ["reference/v0.3-rc1/sui/Move.toml"])

    def test_TL4_reference_import_graph_does_not_couple_token_reward(self):
        """Product modules import stdlib and the sibling model only.

        The pre-existing dynamic import of settlement_fsm inside test_reward_fsm
        is a committed-view read. It is not a product import, and this check
        does not rewrite that test.
        """

        allowed_local = {"token_reward_model", "reward_fsm"}
        for name in ("token_reward_model.py", "reward_fsm.py"):
            tree = ast.parse((REPO / "reference" / "token_reward" / name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                else:
                    continue
                for module in modules:
                    root = module.split(".")[0]
                    self.assertTrue(
                        root in sys.stdlib_module_names or root in allowed_local,
                        module,
                    )
        for suite in SUITES:
            for path in (REPO / "reference" / suite).rglob("*.py"):
                tree = ast.parse(path.read_text())
                for node in ast.walk(tree):
                    modules = []
                    if isinstance(node, ast.Import):
                        modules = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        modules = [node.module]
                    for module in modules:
                        self.assertNotIn("token_reward", module)

    def test_TL4_TK09_name_scan_of_gas_and_sponsor_is_not_a_proof(self):
        """TL0-TK09-T1. Name scan, not a proof. The gas path is not verifiable without a package."""

        for name in ("token_reward_model.py", "reward_fsm.py"):
            text = (REPO / "reference" / "token_reward" / name).read_text().lower()
            self.assertNotIn("gas", text)
            self.assertNotIn("sponsor", text)

    def test_TL4_TK11_wording_scan_is_an_aid_on_the_new_artifacts(self):
        """TL0-TK11-T1. Aid only. A skipped negation line is not a human review.

        A Python line whose stripped text starts with the return keyword is not an affirmative claim, so that line is skipped. TK-11 itself stays a human review.
        """

        paths = [
            REPO / "docs" / "decisions" / "TL4_THREAT_MODEL_20261009.md",
            REPO / "validation" / "2026-10-09-tl-4-token-layer-verification" / "README.md",
            REPO / "reference" / "token_reward" / "tl4_support.py",
            REPO / "reference" / "token_reward" / "test_tl4_model_properties.py",
            REPO / "reference" / "token_reward" / "test_tl4_fsm_properties.py",
            REPO / "reference" / "token_reward" / "test_tl4_fuzz_boundaries.py",
        ]
        hits = []
        for path in paths:
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if any(marker in line for marker in NEGATION_MARKERS):
                    continue
                if path.suffix == ".py" and line.strip().startswith("return"):  # not a claim; keyword skip
                    continue
                lowered = line.lower()
                for needle in CLAIM_NEEDLES:
                    if needle in line or needle in lowered:
                        hits.append("%s:%s:%s" % (path.name, lineno, needle))
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
