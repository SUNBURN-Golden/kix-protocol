# Existing coverage map (recorded before adding console tests)

Task: `plan-plan-local-supply-console`; task input is the supplied inline node
specification and design, not a file under `docs/tasks/` or a GitHub issue.

| Requirement | Prior coverage / classification | Console gap to exercise |
|---|---|---|
| Arithmetic, bounds, conservation, holder burn and alarm classes | Sufficient: `test_reward_model.SupplyTests` (`test_v6_supply_recompute_and_alarm_classes`, tamper, duplicate and explicit chain-figure tests); `test_tl4_model_properties.SupplyPropertyTests` (V6 random streams, allocation and tamper/holder/stop cases) | Reuse these models and fixture requests as the oracle; no console arithmetic |
| Complete results, original codes, report forwarding without repair | Sufficient for dispatcher; partial for console: `test_supply_reconciliation.SupplyDispatchTests` (complete parity/identity, domain exceptions, metadata and numeric rejection) | Real dispatcher wrapper, returned report identity, deliberately missing/altered totals |
| Existing file/stdin CLI semantics | Sufficient: `test_supply_cli.SupplyCliTests` (all fixture parity, numeric/Unicode/malformed data, usage and import inactivity) | Run unchanged; preserve CLI bytes |
| File-free composition, preview, separate calculation and comparison | Not covered | Stream and executable transcripts, complete request previews and two literal confirmations |
| MATCH, holder burn, unexplained, unapproved mint/path | Sufficient model/dispatcher coverage; console not covered | Compose existing fixtures through prompts and compare complete real replies |
| Simultaneous causes | Partial, characterization only: `SupplyDispatchTests.test_complete_result_parity_forwarding_and_input_preservation`, TL-4 §6.B | Preserve observed `UNAPPROVED_PATH`, without defining policy precedence |
| Editing, replacement and declined/failed calculation invalidate selections | Not covered | Show active state after each boundary; no reconciliation of old report |
| Explicit inputs and zero/one dispatch per action | Not covered for console | Invalid scalars, field omissions, EOF/cancel/interruption at every prompt; single calls on confirmation including failures |
| Labels, complete output, displayed stop flag | Partial: existing dispatcher/CLI envelopes | Preserve full envelopes; all three labels visible; no action follows alarm |
| Runnable documentation, discovery and local evidence | Not covered for console | Fixtures, subprocess captures, command ledger, offline doc/discovery checkers |

All paths above are under `reference/token_reward/`. These are author-side,
source-informed tests, not independent A2 review or production evidence.
