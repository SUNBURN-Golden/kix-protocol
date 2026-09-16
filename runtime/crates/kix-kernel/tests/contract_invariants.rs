#![allow(clippy::disallowed_methods)] // Test evidence I/O only; no production lint change.
//! Contract predicates over ONE locked kernel and its observed public history.
//! Does not import model_v4, its generator, check_context or rejection decision tree.
//! Derivations: docs/contracts/CONTRACT_INVARIANTS.md (INV-1..INV-5).

use std::fs;
use std::path::PathBuf;
use std::process::Command;

use kix_kernel::{
    AppliedReservation, CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel,
    KernelError, Limits, ObservationOutcome, Order, ProviderOperation, Reserve, ReserveOutcome,
    Selection,
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

const LOCKED: &str = "69564b166f0c27f9af5d8422f0a466b18d74c20f";

fn id(n: u64) -> KixId {
    let mut bytes = [0; 16];
    bytes[..8].copy_from_slice(&n.to_le_bytes());
    KixId::from_bytes(bytes)
}

fn money(n: u128) -> AssetAmount {
    AssetAmount::checked(
        AssetId::from_bytes([10; 32]),
        n,
        u128::MAX,
        RegistryVersion::new(1).unwrap(),
        Hash32::from_bytes([11; 32]),
    )
    .unwrap()
}

fn ctx(time: u64, generation: u64) -> Context {
    Context {
        fence: ExecutionFence {
            owner: id(90),
            generation,
        },
        now_ms: time,
        semantics_version: 4,
    }
}

#[derive(Clone, Copy, Debug)]
struct Fixture {
    ga: bool,
    limits: Limits,
}

impl Fixture {
    fn total(self) -> u32 {
        if self.ga { 6 } else { 70 }
    }
    fn kernel(self) -> Kernel {
        let inventory = if self.ga {
            Inventory::general_admission(6).unwrap()
        } else {
            Inventory::seats(&[65, 5]).unwrap()
        };
        Kernel::new(id(80), ctx(0, 1).fence, 1, inventory, self.limits).unwrap()
    }
    fn selection(self, first: u16, count: u16) -> Selection {
        if self.ga {
            Selection::GeneralAdmission {
                count: u32::from(count),
            }
        } else {
            Selection::Seats { first, count }
        }
    }
    fn request(self, n: u64, first: u16, count: u16, expiry: u64) -> Reserve {
        Reserve {
            id: CommandId {
                scope: id(80),
                principal: id(81),
                request: id(n),
            },
            order_id: id(10_000 + n),
            expected_business_epoch: 1,
            selection: self.selection(first, count),
            amount: money(1_000),
            quote_hash: Hash32::from_bytes([12; 32]),
            policy_hash: Hash32::from_bytes([13; 32]),
            expires_at_ms: expiry,
            payment: ProviderOperation {
                provider: id(82),
                account: id(83),
                operation: id(n),
            },
        }
    }
}

#[derive(Clone, Debug)]
enum Input {
    Reserve(Reserve),
    Send(KixId),
    Expire(KixId),
    Capture(CaptureObservation),
    Owner(ExecutionFence),
    Cancel(u64),
}

#[derive(Debug)]
enum Reply {
    Reserve(Result<AppliedReservation, KernelError>),
    Unit(Result<(), KernelError>),
    Expire(Result<bool, KernelError>),
    Capture(Result<ObservationOutcome, KernelError>),
}

#[derive(Default)]
struct Observer {
    known_orders: Vec<KixId>,
    originals: Vec<(Context, Reserve, ReserveOutcome)>,
    captured: Vec<(ProviderOperation, KixId, AssetAmount)>,
    capture_transitions: Vec<(ProviderOperation, usize)>,
    primary_calls: usize,
    replay_probes: usize,
    action_counts: [usize; 6],
}

#[derive(Clone, Debug)]
struct View {
    orders: Vec<Order>,
    remaining: u32,
    order_count: usize,
    events: usize,
    conflicts: usize,
    reserved: usize,
    quarantined: usize,
}

impl Observer {
    fn view(&self, k: &Kernel) -> View {
        View {
            orders: self
                .known_orders
                .iter()
                .filter_map(|key| k.order(*key).cloned())
                .collect(),
            remaining: k.remaining(),
            order_count: k.order_count(),
            events: k.observation_count(),
            conflicts: k.conflicts().len(),
            reserved: k.reserved_observation_count(),
            quarantined: k.quarantined_operation_count(),
        }
    }

    // These predicates do not predict the next reply or duplicate reserve's guard order.
    fn check(&self, view: &View, f: Fixture) -> Result<(), String> {
        // INV-1: all active owners are read from the SUT, not maintained as a shadow model.
        if view.order_count != view.orders.len() {
            return Err("INV-1 unobserved order".into());
        }
        let mut seats = vec![None; f.total() as usize];
        let mut ga_used = 0_u64;
        for order in &view.orders {
            if !order.inventory_owned {
                continue;
            }
            match order.request.selection {
                Selection::Seats { first, count } if !f.ga => {
                    let end = u32::from(first) + u32::from(count);
                    if count == 0 || count > 64 || end > 70 || (first < 65 && end > 65) {
                        return Err("INV-1 invalid occupied segment".into());
                    }
                    for slot in &mut seats[usize::from(first)..end as usize] {
                        if slot.replace(order.request.order_id).is_some() {
                            return Err("INV-1 two active owners for one seat".into());
                        }
                    }
                }
                Selection::GeneralAdmission { count } if f.ga => {
                    ga_used += u64::from(count);
                }
                _ => return Err("INV-1 inventory type mismatch".into()),
            }
        }
        let used = if f.ga {
            ga_used
        } else {
            seats.iter().filter(|v| v.is_some()).count() as u64
        };
        if used + u64::from(view.remaining) != u64::from(f.total()) {
            return Err("INV-1 inventory conservation".into());
        }
        // INV-2: observation budget is the SUM, not three independent caps.
        let budget = view
            .events
            .checked_add(view.conflicts)
            .and_then(|v| v.checked_add(view.reserved));
        if budget.is_none_or(|v| v > f.limits.observations)
            || view.order_count > f.limits.orders
            || self.originals.len() > f.limits.commands
            || view.quarantined > view.order_count
        {
            return Err("INV-2 bounded records violated".into());
        }
        // INV-4: a full provider/account/operation has at most one economic binding.
        let mut operations = Vec::new();
        for order in &view.orders {
            if operations.contains(&order.request.payment) {
                return Err("INV-4 operation rebound".into());
            }
            operations.push(order.request.payment);
        }
        if self.capture_transitions.iter().any(|(_, n)| *n > 1) {
            return Err("INV-4 capture applied more than once".into());
        }
        // INV-5: previously observed capture facts must persist with full asset context.
        for (operation, order_id, amount) in &self.captured {
            let current = view
                .orders
                .iter()
                .find(|o| o.request.order_id == *order_id)
                .ok_or("INV-5 captured order disappeared")?;
            if current.request.payment != *operation || current.captured != Some(*amount) {
                return Err("INV-5 captured fact changed or disappeared".into());
            }
        }
        Ok(())
    }

    fn run(&mut self, k: &mut Kernel, f: Fixture, context: Context, input: Input) {
        if let Input::Reserve(request) = &input
            && !self.known_orders.contains(&request.order_id)
        {
            self.known_orders.push(request.order_id);
        }
        let before = self.view(k);
        let family = match &input {
            Input::Reserve(_) => 0,
            Input::Send(_) => 1,
            Input::Expire(_) => 2,
            Input::Capture(_) => 3,
            Input::Owner(_) => 4,
            Input::Cancel(_) => 5,
        };
        self.action_counts[family] += 1;
        let reply = match &input {
            Input::Reserve(value) => Reply::Reserve(k.reserve(context, value.clone())),
            Input::Send(key) => Reply::Unit(k.mark_payment_unknown(context, *key)),
            Input::Expire(key) => Reply::Expire(k.expire(context, *key)),
            Input::Capture(value) => Reply::Capture(k.observe_capture(context, value.clone())),
            Input::Owner(next) => Reply::Unit(k.replace_owner(context, *next)),
            Input::Cancel(epoch) => Reply::Unit(k.cancel_scope(context, *epoch)),
        };
        // Record an OBSERVED first result. No expected rejection is computed here.
        if let (Input::Reserve(request), Reply::Reserve(Ok(applied))) = (&input, &reply) {
            if let Some((_, original, result)) = self
                .originals
                .iter()
                .find(|(_, old, _)| old.id == request.id)
            {
                assert_eq!(request, original, "INV-3 successful replay changed payload");
                assert_eq!(applied.original, *result, "INV-3 changed original result");
                assert!(applied.replayed, "INV-3 repeated command re-applied");
            } else {
                assert!(
                    !applied.replayed,
                    "INV-3 replay without an earlier observed result"
                );
                self.originals
                    .push((context, request.clone(), applied.original));
            }
        }
        // Read every result, including failures, to exercise state-changing Capacity paths.
        match &reply {
            Reply::Reserve(value) => {
                let _ = value.is_ok();
            }
            Reply::Unit(value) => {
                let _ = value.is_ok();
            }
            Reply::Expire(value) => {
                let _ = value.is_ok();
            }
            Reply::Capture(value) => {
                let _ = value.is_ok();
            }
        }
        let after = self.view(k);
        for order in &after.orders {
            let old = before
                .orders
                .iter()
                .find(|o| o.request.order_id == order.request.order_id);
            if order.captured.is_some() && old.is_none_or(|o| o.captured.is_none()) {
                assert!(
                    matches!(&input, Input::Capture(value) if value.operation == order.request.payment),
                    "INV-4 capture appeared without its observation"
                );
                if let Some((_, n)) = self
                    .capture_transitions
                    .iter_mut()
                    .find(|(op, _)| *op == order.request.payment)
                {
                    *n += 1;
                } else {
                    self.capture_transitions.push((order.request.payment, 1));
                }
            }
        }
        if let Input::Capture(value) = &input {
            for previous in &before.orders {
                if previous.request.payment == value.operation && previous.captured.is_some() {
                    let current = after
                        .orders
                        .iter()
                        .find(|o| o.request.order_id == previous.request.order_id)
                        .expect("INV-4 captured operation disappeared");
                    assert_eq!(
                        current.inventory_owned, previous.inventory_owned,
                        "INV-4 repeated capture changed inventory again"
                    );
                }
            }
        }
        // Check history BEFORE adding new capture observations to that history.
        self.check(&after, f).unwrap_or_else(|e| {
            panic!(
                "{e}; call={}; input={input:?}; reply={reply:?}",
                self.primary_calls
            )
        });
        for order in &after.orders {
            if let Some(value) = order.captured
                && !self
                    .captured
                    .iter()
                    .any(|(op, _, _)| *op == order.request.payment)
            {
                self.captured
                    .push((order.request.payment, order.request.order_id, value));
            }
        }
        // INV-3: a contract probe, not reference-model prediction. This covers original
        // rejections as well as success and uses the ORIGINAL (possibly stale) context.
        for (old_context, request, original) in &self.originals {
            let unchanged = k.clone(); // Read-only sentinel, NOT recovery evidence.
            let observed = k.reserve(*old_context, request.clone());
            assert_eq!(
                observed,
                Ok(AppliedReservation {
                    original: *original,
                    replayed: true
                }),
                "INV-3 original result"
            );
            assert_eq!(*k, unchanged, "INV-3 read-only replay mutated kernel state");
            self.replay_probes += 1;
        }
        self.check(&self.view(k), f).unwrap();
        self.primary_calls += 1;
    }
}

fn capture(request: &Reserve, event: u64) -> CaptureObservation {
    CaptureObservation {
        event_id: id(event),
        operation: request.payment,
        amount: request.amount,
        evidence_hash: Hash32::from_bytes([60; 32]),
    }
}

struct Generator(u64);
impl Generator {
    fn next(&mut self) -> u64 {
        self.0 = self
            .0
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        self.0 ^ (self.0 >> 33)
    }
}

fn output() -> PathBuf {
    let out = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../.local/verification/ktx");
    fs::create_dir_all(&out).unwrap();
    out
}

#[test]
fn five_contract_invariants_on_kernel_only_generated_histories() {
    let mut primary = 0;
    let mut probes = 0;
    let mut captures = 0;
    let mut totals = [0_usize; 6];
    for (fixture_id, f) in [
        Fixture {
            ga: false,
            limits: Limits {
                commands: 48,
                orders: 24,
                observations: 24,
            },
        },
        Fixture {
            ga: false,
            limits: Limits {
                commands: 2,
                orders: 8,
                observations: 1,
            },
        },
        Fixture {
            ga: true,
            limits: Limits {
                commands: 48,
                orders: 24,
                observations: 24,
            },
        },
        Fixture {
            ga: true,
            limits: Limits {
                commands: 8,
                orders: 3,
                observations: 2,
            },
        },
    ]
    .into_iter()
    .enumerate()
    {
        for seed in 1..=64_u64 {
            let mut k = f.kernel();
            let mut observer = Observer::default();
            let a = f.request(1, 0, 1, 40);
            let b = f.request(2, 1, 1, 80);
            let first = capture(&a, 500);
            let mut conflicting = first.clone();
            conflicting.operation = b.payment;
            let mut inputs = vec![
                (ctx(1, 1), Input::Reserve(a.clone())),
                (ctx(2, 1), Input::Send(a.order_id)),
                (ctx(3, 1), Input::Capture(first.clone())),
                (ctx(4, 1), Input::Reserve(b.clone())),
                (ctx(5, 1), Input::Capture(first.clone())),
                (ctx(6, 1), Input::Capture(conflicting)),
            ];
            let mut rng = Generator(seed);
            let mut generation = 1;
            // Stimuli depend only on seed and previously emitted inputs, never on Model.
            for index in 0..90_u64 {
                let time = index + 10;
                let n = 1 + rng.next() % 24;
                let mut request = f.request(
                    n,
                    (rng.next() % 72) as u16,
                    (rng.next() % 5) as u16,
                    time + 10,
                );
                if rng.next().is_multiple_of(13) {
                    request.amount = money(0);
                }
                let input = match index % 12 {
                    0..=3 => Input::Reserve(request),
                    4 => Input::Send(id(10_000 + n)),
                    5 => Input::Capture(capture(&request, 501 + n)),
                    6 => Input::Capture(first.clone()),
                    7 => {
                        let mut value = first.clone();
                        value.amount = money(999 + (rng.next() % 3) as u128);
                        value.operation = request.payment;
                        Input::Capture(value)
                    }
                    8 => Input::Expire(id(10_000 + n)),
                    9 => Input::Reserve(a.clone()),
                    10 => Input::Owner(ExecutionFence {
                        owner: id(90),
                        generation: generation + 1,
                    }),
                    _ if index > 72 => Input::Cancel(2 + index),
                    _ => Input::Capture(capture(&a, 900 + index)),
                };
                let mut context = ctx(time, generation);
                if index % 12 == 9 {
                    context = ctx(1, 1);
                }
                if index % 12 == 2 {
                    context.semantics_version = 1;
                }
                if matches!(input, Input::Owner(_)) {
                    generation += 1;
                }
                inputs.push((context, input));
            }
            for (context, input) in inputs {
                observer.run(&mut k, f, context, input);
            }
            assert!(
                !observer.captured.is_empty(),
                "fixture={fixture_id} seed={seed}: vacuous capture checks"
            );
            primary += observer.primary_calls;
            probes += observer.replay_probes;
            captures += observer.captured.len();
            for (sum, count) in totals.iter_mut().zip(observer.action_counts) {
                *sum += count;
            }
        }
    }
    assert_eq!(primary, 4 * 64 * 96);
    assert!(totals.iter().all(|n| *n > 0));
    fs::write(output().join("contract-invariants-summary.json"), format!(
        "{{\"kernel_blob\":\"{LOCKED}\",\"reference_model_used\":false,\"sequences\":256,\"primary_steps\":{primary},\"readonly_replay_probes\":{probes},\"capture_facts_observed\":{captures},\"action_counts\":{totals:?},\"properties\":[\"INV-1\",\"INV-2\",\"INV-3\",\"INV-4\",\"INV-5\"],\"failures\":0,\"scope\":\"finite kernel-only public-state/history predicates; not external ledger or proof of completeness\"}}\n"
    )).unwrap();
}

#[test]
fn contract_predicates_reject_corrupted_observations_not_kernel_mutations() {
    let f = Fixture {
        ga: false,
        limits: Limits {
            commands: 8,
            orders: 8,
            observations: 2,
        },
    };
    let mut k = f.kernel();
    let mut observer = Observer::default();
    let a = f.request(1, 0, 1, 100);
    observer.run(&mut k, f, ctx(1, 1), Input::Reserve(a.clone()));
    observer.run(&mut k, f, ctx(2, 1), Input::Capture(capture(&a, 500)));
    let view = observer.view(&k);
    let mut overlap = view.clone();
    let mut second = overlap.orders[0].clone();
    second.request.order_id = id(99_999);
    second.request.payment.operation = id(99_999);
    overlap.orders.push(second);
    overlap.order_count += 1;
    assert!(
        observer
            .check(&overlap, f)
            .unwrap_err()
            .starts_with("INV-1")
    );
    let mut budget = view.clone();
    budget.events = 3;
    assert!(observer.check(&budget, f).unwrap_err().starts_with("INV-2"));
    let mut lost = view.clone();
    lost.orders[0].captured = None;
    assert!(observer.check(&lost, f).unwrap_err().starts_with("INV-5"));
    observer.capture_transitions[0].1 = 2;
    assert!(observer.check(&view, f).unwrap_err().starts_with("INV-4"));
    fs::write(output().join("contract-predicate-sensitivity.txt"),
        "Synthetic observer views rejected: seat overlap, budget overflow, capture disappearance, double capture count. Neither kernel nor reference-model source was mutated. No claim of production fault injection.\n").unwrap();
}

#[test]
fn contract_test_source_identity_and_format_diagnostic() {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/contract_invariants.rs");
    let hash = Command::new("git")
        .arg("hash-object")
        .arg(&path)
        .output()
        .unwrap();
    assert!(hash.status.success());
    fs::write(
        output().join("contract-invariants-source-blob.txt"),
        hash.stdout,
    )
    .unwrap();
    let formatted = Command::new("rustfmt")
        .args([
            "--edition",
            "2024",
            "--emit",
            "stdout",
            "--config",
            "skip_children=true",
        ])
        .arg(&path)
        .output()
        .unwrap();
    assert!(formatted.status.success());
    fs::write(
        output().join("formatted-tests__contract_invariants.rs"),
        formatted.stdout,
    )
    .unwrap();
}
