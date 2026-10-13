//! Seeded comparison of v5 against locked v4 on commands that exist in both.
//!
//! v5 was forked from v4 and this file was written with that source in view.
//! Agreement is not an independence proof and does not show that either side
//! is free of a shared mistake.

mod common;

use common::id;
use kix_types::{AssetAmount, AssetId, Hash32, RegistryVersion};

#[derive(Clone, Debug)]
enum Op {
    Reserve {
        n: u8,
        first: u16,
        count: u16,
        expiry: u64,
        atoms: u128,
    },
    Send(u8),
    Expire(u8),
    Capture {
        n: u8,
        event: u8,
        atoms: u128,
    },
    Owner {
        owner: u8,
        generation: u64,
    },
    Cancel(u64),
}

#[derive(Clone, Debug)]
struct Step {
    now_ms: u64,
    owner: u8,
    generation: u64,
    op: Op,
}

struct Gen {
    state: u64,
    now: u64,
    owner: u8,
    generation: u64,
    epoch: u64,
}

impl Gen {
    fn below(&mut self, n: u64) -> u64 {
        self.state = self
            .state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        self.state % n
    }
}

fn money(atoms: u128) -> AssetAmount {
    AssetAmount::checked(
        AssetId::from_bytes([7; 32]),
        atoms,
        u128::MAX,
        RegistryVersion::new(1).unwrap(),
        Hash32::from_bytes([8; 32]),
    )
    .unwrap()
}

fn history(seed: u64, steps: usize) -> Vec<Step> {
    let mut source = Gen {
        state: seed,
        now: 0,
        owner: 1,
        generation: 1,
        epoch: 1,
    };
    let mut out = Vec::with_capacity(steps);
    for _ in 0..steps {
        let now_ms = if source.below(11) == 0 {
            source.below(4)
        } else {
            source.now.saturating_add(1 + source.below(3))
        };
        source.now = now_ms;
        let owner = source.owner;
        let generation = source.generation;
        let kind = source.below(7);
        let op = match kind {
            0 | 1 => {
                let n = 1 + source.below(6) as u8;
                let atoms = [10_000_u128, 1, 20_000, 0][source.below(4) as usize];
                let expiry = if source.below(5) == 0 { now_ms } else { 50_000 };
                let first = source.below(8) as u16;
                Op::Reserve {
                    n,
                    first,
                    count: 1,
                    expiry,
                    atoms,
                }
            }
            2 => Op::Send(1 + source.below(6) as u8),
            3 => Op::Expire(1 + source.below(6) as u8),
            4 | 5 => {
                let n = 1 + source.below(6) as u8;
                let event = 1 + source.below(4) as u8;
                let atoms = [10_000_u128, 1, 20_000][source.below(3) as usize];
                Op::Capture { n, event, atoms }
            }
            _ => {
                if source.below(2) == 0 {
                    let next_owner = if source.below(2) == 0 {
                        source.owner
                    } else {
                        8
                    };
                    let next_gen = source.generation.saturating_add(1);
                    source.owner = next_owner;
                    source.generation = next_gen;
                    Op::Owner {
                        owner: next_owner,
                        generation: next_gen,
                    }
                } else {
                    let same = source.below(4) == 0;
                    let next = if same {
                        source.epoch
                    } else {
                        source.epoch.saturating_add(1)
                    };
                    if next > source.epoch {
                        source.epoch = next;
                    }
                    Op::Cancel(next)
                }
            }
        };
        out.push(Step {
            now_ms,
            owner,
            generation,
            op,
        });
    }
    out
}

macro_rules! make_kernel {
    ($ns:ident, $ga:expr) => {{
        let inventory = if $ga {
            $ns::Inventory::general_admission(6).unwrap()
        } else {
            $ns::Inventory::seats(&[8]).unwrap()
        };
        $ns::Kernel::new(
            id(9),
            $ns::ExecutionFence {
                owner: id(1),
                generation: 1,
            },
            1,
            inventory,
            $ns::Limits {
                commands: 8,
                orders: 6,
                observations: 4,
            },
        )
        .unwrap()
    }};
}

macro_rules! apply_step {
    ($ns:ident, $kernel:expr, $step:expr, $ga:expr) => {{
        let ctx = $ns::Context {
            fence: $ns::ExecutionFence {
                owner: id($step.owner),
                generation: $step.generation,
            },
            now_ms: $step.now_ms,
            semantics_version: $ns::SEMANTICS_VERSION,
        };
        match &$step.op {
            Op::Reserve {
                n,
                first,
                count,
                expiry,
                atoms,
            } => {
                let (n, first, count, expiry, atoms) = (*n, *first, *count, *expiry, *atoms);
                let selection = if $ga {
                    $ns::Selection::GeneralAdmission {
                        count: u32::from(count),
                    }
                } else {
                    $ns::Selection::Seats { first, count }
                };
                let request = $ns::Reserve {
                    id: $ns::CommandId {
                        scope: id(9),
                        principal: id(2),
                        request: id(n),
                    },
                    order_id: id(n),
                    expected_business_epoch: 1,
                    selection,
                    amount: money(atoms),
                    quote_hash: Hash32::from_bytes([3; 32]),
                    policy_hash: Hash32::from_bytes([4; 32]),
                    expires_at_ms: expiry,
                    payment: $ns::ProviderOperation {
                        provider: id(20),
                        account: id(21),
                        operation: id(n),
                    },
                };
                format!("{:?}", $kernel.reserve(ctx, request))
            }
            Op::Send(n) => format!("{:?}", $kernel.mark_payment_unknown(ctx, id(*n))),
            Op::Expire(n) => format!("{:?}", $kernel.expire(ctx, id(*n))),
            Op::Capture { n, event, atoms } => {
                let (n, event, atoms) = (*n, *event, *atoms);
                let observation = $ns::CaptureObservation {
                    event_id: id(event),
                    operation: $ns::ProviderOperation {
                        provider: id(20),
                        account: id(21),
                        operation: id(n),
                    },
                    amount: money(atoms),
                    evidence_hash: Hash32::from_bytes([event; 32]),
                };
                format!("{:?}", $kernel.observe_capture(ctx, observation))
            }
            Op::Owner { owner, generation } => format!(
                "{:?}",
                $kernel.replace_owner(
                    ctx,
                    $ns::ExecutionFence {
                        owner: id(*owner),
                        generation: *generation,
                    },
                )
            ),
            Op::Cancel(epoch) => format!("{:?}", $kernel.cancel_scope(ctx, *epoch)),
        }
    }};
}

macro_rules! public_view {
    ($kernel:expr) => {{
        let mut rows = String::new();
        for n in 1_u8..=8 {
            match $kernel.order(id(n)) {
                None => rows.push_str(&format!("{n}:none;")),
                Some(order) => {
                    let captured = order.captured.map(|amount| amount.atoms()).unwrap_or(0);
                    rows.push_str(&format!(
                        "{n}:{:?}|{}|{}|{}|{:?}|{};",
                        order.state,
                        order.inventory_owned,
                        order.review_required,
                        captured,
                        order.submitted_under.owner,
                        order.submitted_under.generation
                    ));
                }
            }
        }
        let mut conflicts = String::new();
        for conflict in $kernel.conflicts() {
            conflicts.push_str(&format!(
                "{:?}/{:?}/{:?}/{:?}/{}/{:?};",
                conflict.event_id,
                conflict.operation.provider,
                conflict.operation.account,
                conflict.operation.operation,
                conflict.amount.atoms(),
                conflict.evidence_hash
            ));
        }
        format!(
            "rem={} orders={} obs={} res={} quar={} conflicts={conflicts} rows={rows}",
            $kernel.remaining(),
            $kernel.order_count(),
            $kernel.observation_count(),
            $kernel.reserved_observation_count(),
            $kernel.quarantined_operation_count()
        )
    }};
}

fn diverge(steps: &[Step], ga: bool) -> Result<(), String> {
    let mut v4 = make_kernel!(kix_kernel, ga);
    let mut v5 = make_kernel!(kix_kernel_v5, ga);
    for (index, step) in steps.iter().enumerate() {
        let left = apply_step!(kix_kernel, v4, step, ga);
        let right = apply_step!(kix_kernel_v5, v5, step, ga);
        if left != right {
            return Err(format!(
                "step {index} result\n step={step:?}\n v4={left}\n v5={right}"
            ));
        }
        let left_view = public_view!(v4);
        let right_view = public_view!(v5);
        if left_view != right_view {
            return Err(format!(
                "step {index} state\n step={step:?}\n v4={left_view}\n v5={right_view}"
            ));
        }
    }
    Ok(())
}

fn shrink(steps: &[Step], ga: bool) -> Vec<Step> {
    let mut current = steps.to_vec();
    let mut changed = true;
    while changed {
        changed = false;
        let mut index = 0;
        while index < current.len() {
            let mut trial = current.clone();
            trial.remove(index);
            if diverge(&trial, ga).is_err() {
                current = trial;
                changed = true;
            } else {
                index += 1;
            }
        }
    }
    current
}

#[test]
fn seeded_histories_match_v4_on_shared_commands() {
    const SEEDS: [u64; 8] = [1, 2, 7, 11, 42, 99, 0x51A6_E25B, 0x00C0_FFEE];
    for ga in [false, true] {
        for seed in SEEDS {
            let steps = history(seed, 48);
            if let Err(detail) = diverge(&steps, ga) {
                let shrunk = shrink(&steps, ga);
                panic!(
                    "v4/v5 differential mismatch seed={seed} ga={ga}\n{detail}\nshrunk {} steps: {shrunk:#?}",
                    shrunk.len()
                );
            }
        }
    }
}

#[test]
fn version_4_context_is_rejected_by_v5_without_state_change() {
    assert_eq!(kix_kernel::SEMANTICS_VERSION, 4);
    assert_eq!(kix_kernel_v5::SEMANTICS_VERSION, 5);
    let mut kernel = make_kernel!(kix_kernel_v5, false);
    let request = kix_kernel_v5::Reserve {
        id: kix_kernel_v5::CommandId {
            scope: id(9),
            principal: id(2),
            request: id(1),
        },
        order_id: id(1),
        expected_business_epoch: 1,
        selection: kix_kernel_v5::Selection::Seats { first: 0, count: 1 },
        amount: money(10_000),
        quote_hash: Hash32::from_bytes([3; 32]),
        policy_hash: Hash32::from_bytes([4; 32]),
        expires_at_ms: 100,
        payment: kix_kernel_v5::ProviderOperation {
            provider: id(20),
            account: id(21),
            operation: id(1),
        },
    };
    let ctx = kix_kernel_v5::Context {
        fence: kix_kernel_v5::ExecutionFence {
            owner: id(1),
            generation: 1,
        },
        now_ms: 1,
        semantics_version: kix_kernel_v5::SEMANTICS_VERSION,
    };
    kernel.reserve(ctx, request.clone()).unwrap();
    let before = kernel.clone();
    let old = kix_kernel_v5::Context {
        semantics_version: 4,
        now_ms: 2,
        ..ctx
    };
    assert_eq!(
        kernel.reserve(old, request.clone()),
        Err(kix_kernel_v5::KernelError::UnsupportedSemantics)
    );
    assert_eq!(
        kernel.mark_payment_unknown(old, id(1)),
        Err(kix_kernel_v5::KernelError::UnsupportedSemantics)
    );
    assert_eq!(
        kernel.observe_capture(
            old,
            kix_kernel_v5::CaptureObservation {
                event_id: id(1),
                operation: request.payment,
                amount: request.amount,
                evidence_hash: Hash32::from_bytes([1; 32]),
            }
        ),
        Err(kix_kernel_v5::KernelError::UnsupportedSemantics)
    );
    let decision = kix_kernel_v5::Terminate {
        decision_id: id(10),
        order_id: id(1),
        evaluated: kix_kernel_v5::OperationSnapshot {
            state: kix_kernel_v5::OrderState::Held,
            captured: None,
            review_required: false,
            reserved_slot: false,
            observations: 0,
            retained_conflicts: 0,
        },
        evaluation: kix_kernel_v5::ClosureEvaluation {
            c: [kix_kernel_v5::ConditionEvidence {
                holds: true,
                evidence_hash: Hash32::from_bytes([1; 32]),
            }; 5],
        },
        authority: kix_kernel_v5::Authority {
            authority_id: id(30),
            generation: 1,
            actor: kix_kernel_v5::ActorKind::Human,
            principal: id(40),
        },
        rule_hash: Hash32::from_bytes([6; 32]),
    };
    assert_eq!(
        kernel.terminate(old, decision),
        Err(kix_kernel_v5::KernelError::UnsupportedSemantics)
    );
    assert_eq!(kernel, before);
}

#[test]
fn version_5_context_is_rejected_by_v4() {
    let mut kernel = make_kernel!(kix_kernel, false);
    let before = kernel.clone();
    let ctx = kix_kernel::Context {
        fence: kix_kernel::ExecutionFence {
            owner: id(1),
            generation: 1,
        },
        now_ms: 1,
        semantics_version: 5,
    };
    let request = kix_kernel::Reserve {
        id: kix_kernel::CommandId {
            scope: id(9),
            principal: id(2),
            request: id(1),
        },
        order_id: id(1),
        expected_business_epoch: 1,
        selection: kix_kernel::Selection::Seats { first: 0, count: 1 },
        amount: money(10_000),
        quote_hash: Hash32::from_bytes([3; 32]),
        policy_hash: Hash32::from_bytes([4; 32]),
        expires_at_ms: 100,
        payment: kix_kernel::ProviderOperation {
            provider: id(20),
            account: id(21),
            operation: id(1),
        },
    };
    assert_eq!(
        kernel.reserve(ctx, request),
        Err(kix_kernel::KernelError::UnsupportedSemantics)
    );
    assert_eq!(kernel, before);
}
