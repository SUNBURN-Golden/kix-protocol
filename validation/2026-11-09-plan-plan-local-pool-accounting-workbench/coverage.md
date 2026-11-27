# Coverage map recorded before new interface tests

Task: `plan-plan-local-pool-accounting-workbench`. Input is the supervisor's
node/design text in this session; no corresponding `docs/tasks/` document or issue.
Builder-authored, source-informed evidence, not independent verification.

| Requirement | Existing coverage | Interface gap to address |
|---|---|---|
| Explicit five-pool initialization, conservation | Sufficient model coverage: `reference/token_reward/test_reward_model.py:PoolConservationTests`, especially `test_opening_balances_are_required_and_not_defaulted` and `test_spendable_pools_conserve_across_explicit_orders` | Fixture forwarding and original constructor errors |
| Three obligation refusals, shortfall without borrowing | Sufficient model coverage: `PoolConservationTests.test_TL0_TK04_T1_forbidden_pools_do_not_fund_token_spend`, `test_shortfall_pauses_without_cross_pool_top_up`; `test_tl4_model_properties.PoolPropertyTests.test_TL4_TK04_obligation_spend_and_shortfall_leave_digest` | Parity through session/CLI/console with original codes |
| Rejection preserves complete state | Partial: TL-4 random pool scripts and `test_tl4_fuzz_boundaries.JunkAndJournalTests.test_TL4_junk_values_on_the_fenced_surface_raise_token_reward_error` | Session before/after snapshots for ordinary invalid values, overflow and refs |
| Returned snapshots isolated | Partial: `PoolConservationTests.test_caller_opening_dict_is_not_aliased`; reward snapshot tests concern a different interface | Mutate nested balances, credits and spends from each session method |
| Repeated references | Partial: `PoolPropertyTests.test_TL4_TK04_random_scripts_match_opening_plus_credits_minus_spends` repeats program refs | Direct-model parity for repeated source and program refs; no deduplication or receipts |
| Strict JSON and exact integers | Partial: shared `reward_fixture` parsers and `test_reward_cli.py` | New envelope/fixture shapes, duplicate keys, nonfinite/invalid Unicode, exact finite values passed to model |
| Confirmed one-call actions, decline, EOF and I/O | Not covered for this interface | Constructor/method spies, EOF at each prompt, preview write/flush failure and no redispatch |
| Real journeys | Not covered | Actual CLI/console subprocess fixtures including both permitted pools, all refusals, shortfall and explicit reads |
| Synthetic isolation/false claims | Partial: TL-4 import graph verifies model/FSM only | Output metadata, stdlib/local import inspection, no RewardMachine instantiation |
| Evidence and delivery gates | Existing repository policy | Actual commands, protected bytes, indexed record; A2 non-author exact-head review and KTX/KIX CI pending |
