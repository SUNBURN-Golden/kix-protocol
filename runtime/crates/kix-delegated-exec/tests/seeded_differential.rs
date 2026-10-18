//! Seeded differential and invariant test for the in-memory delegated-execution map.
//!
//! Subject: `DelegatedShow` driven through its public API only. Reference: one
//! independent `kix_kernel_v5::Kernel` per page, built with the same page scope,
//! inventory, limits and fence, and driven with the same commands. Pre-kernel
//! refusals, cross-page bindings, GA slot allocation and the grant transitions
//! are predicted by a small model typed in from the module documentation of
//! `kix-delegated-exec` and `docs/contracts/RIGHTS_SCALE_PROFILE.md` sections
//! 5 and 10, not by calling the subject.
//!
//! This file was written with the source in view. Agreement is not an
//! independence proof and does not show that either side is free of a shared
//! mistake. In-memory only: no chain client, no durability, delegated execution
//! stays disabled. It asserts nothing about private layout.
//!
//! Generator choices that exclude documented-undefined behaviour (named, not
//! hidden):
//! - `Profile::exclude_late_ga_capture`: a matching capture at or after expiry
//!   on a still-owned GA hold is skipped. The map keeps the hold while the
//!   kernel releases the inventory (see `open_defect_*` below).
//! - capture event ids carry a page namespace, so one event key is only ever
//!   recorded on one page. Cross-page event keys and quarantine are not asserted.
//! - the LCG is the one of `kix-kernel-v5/tests/v4_differential.rs`, but `below`
//!   reads the high bits (`>> 33`): the low bits of this LCG are periodic.

mod common;

use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Debug;
use std::panic::{AssertUnwindSafe, catch_unwind};

use common::{amount, id, page};
use kix_delegated_exec::{
    DelegatedReserve, DelegatedShow, GrantState, MappingError, PageKind, PageSpec, RangeTable,
    ShowSelection, SlotHold,
};
use kix_kernel_v5::{
    AppliedReservation, CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel,
    KernelError, Limits, MAX_BUNDLE, ObservationOutcome, OrderState, ProviderOperation, Rejection,
    Reserve, ReserveOutcome, SEMANTICS_VERSION, Selection,
};
use kix_types::{Hash32, KixId};

const SEEDS: [u64; 8] = [1, 2, 7, 11, 42, 99, 0x51A6_E25B, 0x00C0_FFEE];
const STEPS: usize = 160;
const GRANT_BASE: u8 = 50;
const GHOST_ORDER: u8 = 250;

const REQ: u8 = 0x10;
const ORD: u8 = 0x11;
const OPN: u8 = 0x12;
const EVT: u8 = 0x13;

fn tag(kind: u8, n: u8) -> KixId {
    let mut bytes = [0_u8; 16];
    bytes[0] = kind;
    bytes[1] = n;
    KixId::from_bytes(bytes)
}

fn show_scope() -> KixId {
    id(9)
}

fn issuer() -> KixId {
    id(1)
}

fn page_scope(index: u32) -> KixId {
    id(index as u8 + 100)
}

fn grant_id(n: u8) -> KixId {
    id(GRANT_BASE + n % 3)
}

fn provider_op(n: u8) -> ProviderOperation {
    ProviderOperation {
        provider: id(20),
        account: id(21),
        operation: tag(OPN, n),
    }
}

// ---------------------------------------------------------------- generator

struct Gen {
    state: u64,
}

impl Gen {
    fn below(&mut self, n: u64) -> u64 {
        self.state = self
            .state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        (self.state >> 33) % n
    }
}

#[derive(Clone, Copy, Debug)]
enum NowMode {
    Advance(u64),
    Regress(u64),
}

#[derive(Clone, Copy, Debug)]
enum FenceMode {
    Current,
    Issuer,
    Delegate,
    Stale,
    Garbage,
    WrongSemantics,
}

#[derive(Clone, Copy, Debug)]
enum SelGen {
    Seats { first: u32, count: u16 },
    Ga { count: u32 },
}

#[derive(Clone, Copy, Debug)]
struct ReserveGen {
    principal: u8,
    req: u8,
    ord: u8,
    opn: u8,
    sel: SelGen,
    atoms: u8,
    expiry: u8,
    bad_epoch: bool,
    wrong_scope: bool,
}

#[derive(Clone, Copy, Debug)]
enum Op {
    Reserve(ReserveGen),
    Replay(u8),
    Mutate(u8, u8),
    Expire(u8),
    MarkUnknown(u8),
    Capture {
        op_pick: u8,
        evt: u8,
        ns: u8,
        amount: u8,
        evidence: u8,
    },
    Lookup(u8),
    CreateGrant {
        grant: u8,
        delegate: u8,
    },
    Delegate {
        grant: u8,
        page: u32,
    },
    Revoke {
        grant: u8,
    },
    Undelegate {
        grant: u8,
        page: u32,
    },
}

/// Self-contained: every index is resolved modulo the state at run time and a
/// step that finds nothing to act on is a no-op, so deleting steps stays valid.
#[derive(Clone, Copy, Debug)]
struct Step {
    now: NowMode,
    fence: FenceMode,
    op: Op,
}

#[derive(Clone)]
struct Profile {
    name: &'static str,
    pages: Vec<PageSpec>,
    limits: Limits,
    /// One page, no ctx defects, no pre-kernel refusals: the map must answer
    /// exactly like a bare kernel.
    strict: bool,
    delegation: bool,
    exclude_late_ga_capture: bool,
    /// Share of steps (percent) that are fresh reserves.
    reserve_pct: u64,
}

fn multi_pages() -> Vec<PageSpec> {
    vec![
        page(0, 0, 8, PageKind::Seat),
        page(1, 8, 16, PageKind::Seat),
        page(2, 20, 26, PageKind::Ga),
        page(3, 26, 40, PageKind::Ga),
        page(4, 40, 70, PageKind::Seat),
    ]
}

fn profiles() -> Vec<Profile> {
    let strict_limits = Limits {
        commands: 40,
        orders: 30,
        observations: 64,
    };
    let multi_limits = Limits {
        commands: 12,
        orders: 8,
        observations: 4,
    };
    vec![
        Profile {
            name: "one-page-seat",
            pages: vec![page(0, 0, 8, PageKind::Seat)],
            limits: strict_limits,
            strict: true,
            delegation: false,
            exclude_late_ga_capture: true,
            reserve_pct: 46,
        },
        Profile {
            name: "one-page-ga",
            pages: vec![page(0, 0, 6, PageKind::Ga)],
            limits: strict_limits,
            strict: true,
            delegation: false,
            exclude_late_ga_capture: true,
            reserve_pct: 46,
        },
        Profile {
            name: "multi-page",
            pages: multi_pages(),
            limits: multi_limits,
            strict: false,
            delegation: false,
            exclude_late_ga_capture: true,
            reserve_pct: 46,
        },
        Profile {
            name: "multi-page-delegated",
            pages: multi_pages(),
            limits: multi_limits,
            strict: false,
            delegation: true,
            exclude_late_ga_capture: true,
            reserve_pct: 30,
        },
        // Few reserves, so pages settle and the grant transitions (undelegate,
        // retry after a failed re-fence) get to run on them.
        Profile {
            name: "multi-page-delegated-settling",
            pages: multi_pages(),
            limits: multi_limits,
            strict: false,
            delegation: true,
            exclude_late_ga_capture: true,
            reserve_pct: 14,
        },
    ]
}

fn pick_small(g: &mut Gen, i: usize) -> u8 {
    if g.below(3) == 0 {
        1 + g.below(4) as u8
    } else {
        8 + (i % 200) as u8
    }
}

fn gen_selection(g: &mut Gen, profile: &Profile) -> SelGen {
    let seats: Vec<&PageSpec> = profile
        .pages
        .iter()
        .filter(|p| p.kind == PageKind::Seat)
        .collect();
    let gas: Vec<&PageSpec> = profile
        .pages
        .iter()
        .filter(|p| p.kind == PageKind::Ga)
        .collect();
    let use_seats = !seats.is_empty() && (gas.is_empty() || g.below(2) == 0);
    let roll = if profile.strict { 0 } else { g.below(20) };
    if use_seats {
        let p = seats[g.below(seats.len() as u64) as usize];
        let len = p.end - p.start;
        let count = [1_u16, 1, 2, 3][g.below(4) as usize].min(len as u16);
        match roll {
            0..=13 => SelGen::Seats {
                first: p.start + g.below(u64::from(len) - u64::from(count) + 1) as u32,
                count,
            },
            14 | 15 => SelGen::Seats {
                first: p.end - 1,
                count: 2 + g.below(2) as u16,
            },
            16 => SelGen::Seats {
                first: p.start,
                count: 65,
            },
            17 => SelGen::Seats {
                first: p.start,
                count: 0,
            },
            18 => SelGen::Seats {
                first: 1_000,
                count: 1,
            },
            _ => SelGen::Seats {
                first: gas.first().map_or(1_000, |p| p.start),
                count: 1,
            },
        }
    } else {
        let count = match roll {
            0..=14 => [1_u32, 1, 2, 3, 4][g.below(5) as usize],
            15 | 16 => 0,
            _ => 100,
        };
        SelGen::Ga { count }
    }
}

/// Fixed opening of every delegating history, so the failed-then-retried
/// transitions do not depend on the generator's luck: a re-fence refused by a
/// kernel clock (`Regress`), a partial revoke (page 0 cut, page 1 refused) and
/// the retries that complete each transition.
fn prologue() -> Vec<Step> {
    let adv = NowMode::Advance(1);
    let step = |now, op| Step {
        now,
        fence: FenceMode::Current,
        op,
    };
    vec![
        step(
            adv,
            Op::Reserve(ReserveGen {
                principal: 0,
                req: 1,
                ord: 1,
                opn: 1,
                sel: SelGen::Seats { first: 8, count: 1 },
                atoms: 0,
                expiry: 0,
                bad_epoch: false,
                wrong_scope: false,
            }),
        ),
        step(
            adv,
            Op::CreateGrant {
                grant: 0,
                delegate: 0,
            },
        ),
        step(NowMode::Regress(1_000), Op::Delegate { grant: 0, page: 1 }),
        step(adv, Op::Delegate { grant: 0, page: 0 }),
        step(adv, Op::Delegate { grant: 0, page: 1 }),
        step(NowMode::Regress(1), Op::Revoke { grant: 0 }),
        step(adv, Op::Revoke { grant: 0 }),
        step(
            NowMode::Regress(1_000),
            Op::Undelegate { grant: 0, page: 1 },
        ),
        step(adv, Op::Undelegate { grant: 0, page: 1 }),
        step(adv, Op::Undelegate { grant: 0, page: 0 }),
        // A second grant is cut while holding page 0, then a fresh reserve on
        // the cut page.
        step(
            adv,
            Op::CreateGrant {
                grant: 1,
                delegate: 1,
            },
        ),
        step(adv, Op::Delegate { grant: 1, page: 0 }),
        step(adv, Op::Delegate { grant: 1, page: 0 }),
        step(adv, Op::Revoke { grant: 1 }),
        step(
            adv,
            Op::Reserve(ReserveGen {
                principal: 0,
                req: 2,
                ord: 2,
                opn: 2,
                sel: SelGen::Seats { first: 0, count: 1 },
                atoms: 0,
                expiry: 2,
                bad_epoch: false,
                wrong_scope: false,
            }),
        ),
    ]
}

fn history(seed: u64, profile: &Profile) -> Vec<Step> {
    let mut g = Gen { state: seed };
    let npages = profile.pages.len() as u64;
    let mut out = if profile.delegation {
        prologue()
    } else {
        Vec::new()
    };
    for i in 0..STEPS {
        let (now, fence) = if profile.strict {
            (NowMode::Advance(1 + g.below(3)), FenceMode::Current)
        } else {
            let now = if g.below(100) < 14 {
                NowMode::Regress(1 + g.below(10))
            } else {
                NowMode::Advance(1 + g.below(3))
            };
            let fence = match g.below(100) {
                0..=79 => FenceMode::Current,
                80..=84 => FenceMode::Issuer,
                85..=89 => FenceMode::Delegate,
                90..=93 => FenceMode::Stale,
                94..=96 => FenceMode::Garbage,
                _ => FenceMode::WrongSemantics,
            };
            (now, fence)
        };
        let roll = g.below(100);
        let op = if roll < profile.reserve_pct {
            Op::Reserve(ReserveGen {
                principal: g.below(2) as u8,
                req: pick_small(&mut g, i),
                ord: pick_small(&mut g, i),
                opn: pick_small(&mut g, i),
                sel: gen_selection(&mut g, profile),
                atoms: g.below(8) as u8,
                expiry: g.below(5) as u8,
                bad_epoch: !profile.strict && g.below(25) == 0,
                wrong_scope: g.below(30) == 0 && (!profile.strict || g.below(3) == 0),
            })
        } else {
            // Remaining mass (percent): replay 8, mutate 6, expire 18, mark 13,
            // capture 22, lookup 6; with delegation the last 27 go to the grant
            // ops, without it they are expires.
            let r = g.below(100);
            let pick = g.below(256) as u8;
            let grant = g.below(3) as u8;
            match r {
                0..=7 => Op::Replay(pick),
                8..=13 => Op::Mutate(pick, g.below(4) as u8),
                14..=31 => Op::Expire(pick),
                32..=44 => Op::MarkUnknown(pick),
                45..=66 => Op::Capture {
                    op_pick: pick,
                    evt: g.below(5) as u8,
                    ns: g.below(npages) as u8,
                    amount: g.below(5) as u8,
                    evidence: g.below(3) as u8,
                },
                67..=72 => Op::Lookup(pick),
                _ if !profile.delegation => Op::Expire(pick),
                73..=76 => Op::CreateGrant {
                    grant,
                    delegate: g.below(6) as u8,
                },
                77..=85 => Op::Delegate {
                    grant,
                    page: g.below(npages + 1) as u32,
                },
                86..=91 => Op::Revoke { grant },
                _ => Op::Undelegate {
                    grant,
                    page: g.below(npages + 1) as u32,
                },
            }
        };
        // Grant transitions often run with a clock behind some page kernel's, so
        // the kernel refuses the re-fence and the transition must stay retryable.
        let now = match op {
            Op::Delegate { .. } | Op::Revoke { .. } | Op::Undelegate { .. }
                if !profile.strict && g.below(100) < 35 =>
            {
                NowMode::Regress(if g.below(2) == 0 {
                    1_000
                } else {
                    1 + g.below(30)
                })
            }
            _ => now,
        };
        out.push(Step { now, fence, op });
    }
    out
}

// ----------------------------------------------------------------- coverage

#[derive(Default)]
struct Coverage {
    labels: BTreeSet<String>,
}

impl Coverage {
    fn hit(&mut self, label: impl Into<String>) {
        self.labels.insert(label.into());
    }
}

// Exhaustive matches, no wildcard: a new variant breaks the build here.
fn kernel_label(e: KernelError) -> &'static str {
    match e {
        KernelError::InvalidConfiguration => "InvalidConfiguration",
        KernelError::UnsupportedSemantics => "UnsupportedSemantics",
        KernelError::ExecutionFenced => "ExecutionFenced",
        KernelError::ClockRegression => "ClockRegression",
        KernelError::WrongScope => "WrongScope",
        KernelError::CommandConflict => "CommandConflict",
        KernelError::Capacity => "Capacity",
        KernelError::UnknownOrder => "UnknownOrder",
        KernelError::InvalidTransition => "InvalidTransition",
        KernelError::UnknownOperation => "UnknownOperation",
        KernelError::ConditionNotSatisfied => "ConditionNotSatisfied",
        KernelError::StaleEvaluation => "StaleEvaluation",
        KernelError::AutomaticApprovalDisabled => "AutomaticApprovalDisabled",
        KernelError::AlreadyTerminated => "AlreadyTerminated",
        KernelError::HoldExists => "HoldExists",
        KernelError::UnknownHold => "UnknownHold",
    }
}

fn mapping_label(e: MappingError) -> String {
    let name = match e {
        MappingError::UnknownSlot => "UnknownSlot",
        MappingError::CrossPageBundle => "CrossPageBundle",
        MappingError::BundleTooLarge => "BundleTooLarge",
        MappingError::GaSpanningPages => "GaSpanningPages",
        MappingError::UnknownPage => "UnknownPage",
        MappingError::PageNotDelegated => "PageNotDelegated",
        MappingError::PageDelegated => "PageDelegated",
        MappingError::UnknownGrant => "UnknownGrant",
        MappingError::GrantExists => "GrantExists",
        MappingError::GrantClosed => "GrantClosed",
        MappingError::GrantOpen => "GrantOpen",
        MappingError::OutstandingReservations => "OutstandingReservations",
        MappingError::UnknownOrder => "UnknownOrder",
        MappingError::UnknownOperation => "UnknownOperation",
        MappingError::CommandConflict => "CommandConflict",
        MappingError::WrongScope => "WrongScope",
        MappingError::InvalidConfiguration => "InvalidConfiguration",
        MappingError::Kernel(k) => return format!("kernel:{}", kernel_label(k)),
    };
    format!("map:{name}")
}

fn rejection_label(r: Rejection) -> &'static str {
    match r {
        Rejection::InvalidRequest => "InvalidRequest",
        Rejection::BusinessFenced => "BusinessFenced",
        Rejection::Unavailable => "Unavailable",
        Rejection::OrderExists => "OrderExists",
        Rejection::OperationAlreadyBound => "OperationAlreadyBound",
        Rejection::OperationQuarantined => "OperationQuarantined",
    }
}

fn observation_label(o: ObservationOutcome) -> &'static str {
    match o {
        ObservationOutcome::PaymentConfirmed => "PaymentConfirmed",
        ObservationOutcome::ReturnRequired => "ReturnRequired",
        ObservationOutcome::Review => "Review",
        ObservationOutcome::DuplicateEffect => "DuplicateEffect",
        ObservationOutcome::Conflict => "Conflict",
    }
}

const REQUIRED_COMMANDS: [&str; 11] = [
    "cmd:reserve",
    "cmd:replay",
    "cmd:mutate",
    "cmd:expire",
    "cmd:mark_payment_unknown",
    "cmd:observe_capture",
    "cmd:order_lookup",
    "cmd:create_grant",
    "cmd:delegate_page",
    "cmd:revoke_grant",
    "cmd:undelegate_page",
];

const REQUIRED_MAPPING: [&str; 17] = [
    "UnknownSlot",
    "CrossPageBundle",
    "BundleTooLarge",
    "GaSpanningPages",
    "UnknownPage",
    "PageNotDelegated",
    "PageDelegated",
    "UnknownGrant",
    "GrantExists",
    "GrantClosed",
    "GrantOpen",
    "OutstandingReservations",
    "UnknownOrder",
    "UnknownOperation",
    "CommandConflict",
    "WrongScope",
    "InvalidConfiguration",
];

// Exempt from the guard, with the reason:
// - InvalidConfiguration: constructor-only (`Kernel::new`).
// - WrongScope: the map rewrites the scope to the page scope.
// - UnknownOrder / UnknownOperation: the map answers before the kernel.
// - the remaining kernel errors belong to commands outside the map's API.
const REQUIRED_KERNEL: [&str; 6] = [
    "UnsupportedSemantics",
    "ExecutionFenced",
    "ClockRegression",
    "CommandConflict",
    "Capacity",
    "InvalidTransition",
];

const REQUIRED_REJECTIONS: [&str; 6] = [
    "InvalidRequest",
    "BusinessFenced",
    "Unavailable",
    "OrderExists",
    "OperationAlreadyBound",
    "OperationQuarantined",
];

const REQUIRED_OBSERVATIONS: [&str; 5] = [
    "PaymentConfirmed",
    "ReturnRequired",
    "Review",
    "DuplicateEffect",
    "Conflict",
];

const REQUIRED_EXTRA: [&str; 17] = [
    "reserve:Held",
    "reserve:replayed",
    "reserve:synthesized-OrderExists",
    "reserve:synthesized-OperationAlreadyBound",
    "ga:hold",
    "ga:release",
    "expire:false",
    "grant:created",
    "grant:delegated",
    "grant:revoked",
    "grant:undelegated",
    "grant:revoke-partial",
    "grant:revoke-retry-completed",
    "grant:delegate-failed",
    "grant:delegate-retry-ok",
    "grant:undelegate-failed",
    "grant:undelegate-retry-ok",
];

fn required_labels() -> Vec<String> {
    let mut out: Vec<String> = REQUIRED_COMMANDS.iter().map(|s| s.to_string()).collect();
    out.extend(REQUIRED_MAPPING.iter().map(|s| format!("map:{s}")));
    out.extend(REQUIRED_KERNEL.iter().map(|s| format!("kernel:{s}")));
    out.extend(REQUIRED_REJECTIONS.iter().map(|s| format!("rejected:{s}")));
    out.extend(
        REQUIRED_OBSERVATIONS
            .iter()
            .map(|s| format!("observed:{s}")),
    );
    out.extend(REQUIRED_EXTRA.iter().map(|s| s.to_string()));
    out
}

// ----------------------------------------------------------------- subject

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Fault {
    None,
    /// Negative control: a replayed reserve claims it is a first application.
    FlipReplayed,
    /// Negative control: a real release reports `false`.
    ExpireFalse,
    /// Negative control: a refused closed-grant reserve is reported as held.
    ClosedAccepted,
}

type Called<T> = Result<Result<T, MappingError>, String>;

fn guarded<T>(f: impl FnOnce() -> T) -> Result<T, String> {
    catch_unwind(AssertUnwindSafe(f)).map_err(|payload| {
        let text = payload
            .downcast_ref::<&str>()
            .map(|s| s.to_string())
            .or_else(|| payload.downcast_ref::<String>().cloned())
            .unwrap_or_else(|| "non-string panic".to_string());
        format!("the map panicked: {text}")
    })
}

struct Subject {
    show: DelegatedShow,
    fault: Fault,
}

impl Subject {
    fn reserve(&mut self, ctx: Context, req: &DelegatedReserve) -> Called<AppliedReservation> {
        let fault = self.fault;
        let show = &mut self.show;
        let mut result = guarded(|| show.reserve(ctx, req))?;
        if fault == Fault::FlipReplayed
            && let Ok(applied) = &mut result
            && applied.replayed
        {
            applied.replayed = false;
        }
        if fault == Fault::ClosedAccepted && result == Err(MappingError::GrantClosed) {
            result = Ok(AppliedReservation {
                original: ReserveOutcome::Held(req.order_id),
                replayed: false,
            });
        }
        Ok(result)
    }

    fn expire(&mut self, ctx: Context, order: KixId) -> Called<bool> {
        let fault = self.fault;
        let show = &mut self.show;
        let mut result = guarded(|| show.expire(ctx, order))?;
        if fault == Fault::ExpireFalse && result == Ok(true) {
            result = Ok(false);
        }
        Ok(result)
    }

    fn mark(&mut self, ctx: Context, order: KixId) -> Called<()> {
        let show = &mut self.show;
        guarded(|| show.mark_payment_unknown(ctx, order))
    }

    fn observe(&mut self, ctx: Context, obs: &CaptureObservation) -> Called<ObservationOutcome> {
        let show = &mut self.show;
        guarded(|| show.observe_capture(ctx, obs.clone()))
    }
}

// ------------------------------------------------------------------- model

#[derive(Debug)]
struct PageModel {
    spec: PageSpec,
    kernel: Kernel,
    epoch: u64,
    grant: Option<KixId>,
    tombstoned: bool,
    orders: Vec<KixId>,
    free: BTreeSet<u32>,
}

#[derive(Debug)]
struct Stored {
    key: (KixId, KixId),
    req: DelegatedReserve,
    page: u32,
    original: ReserveOutcome,
}

enum Plan {
    Refuse(MappingError),
    Synth(Rejection),
    Kernel {
        page: u32,
        selection: Selection,
        fresh: bool,
    },
}

struct Model {
    pages: BTreeMap<u32, PageModel>,
    grants: BTreeMap<KixId, GrantState>,
    stored: Vec<Stored>,
    order_pages: BTreeMap<KixId, u32>,
    op_pages: BTreeMap<ProviderOperation, u32>,
    op_orders: BTreeMap<ProviderOperation, KixId>,
    event_pages: BTreeMap<(KixId, KixId, KixId), u32>,
    holds: BTreeMap<KixId, SlotHold>,
    known_orders: Vec<KixId>,
    known_ops: Vec<ProviderOperation>,
    clock: u64,
}

fn agrees<T: PartialEq>(map: &Result<T, MappingError>, reference: &Result<T, KernelError>) -> bool {
    match (map, reference) {
        (Ok(a), Ok(b)) => a == b,
        (Err(m), Err(k)) => {
            let analog = match m {
                MappingError::Kernel(e) => Some(*e),
                MappingError::WrongScope => Some(KernelError::WrongScope),
                MappingError::UnknownOrder => Some(KernelError::UnknownOrder),
                MappingError::UnknownOperation => Some(KernelError::UnknownOperation),
                MappingError::CommandConflict => Some(KernelError::CommandConflict),
                _ => None,
            };
            analog == Some(*k)
        }
        _ => false,
    }
}

impl Model {
    fn new(profile: &Profile) -> Self {
        let pages = profile
            .pages
            .iter()
            .map(|spec| {
                let len = spec.end - spec.start;
                let (inventory, free) = match spec.kind {
                    PageKind::Seat => (Inventory::seats(&[len as u16]).unwrap(), BTreeSet::new()),
                    PageKind::Ga => (
                        Inventory::general_admission(len).unwrap(),
                        (spec.start..spec.end).collect(),
                    ),
                };
                let kernel = Kernel::new(
                    page_scope(spec.index),
                    ExecutionFence {
                        owner: issuer(),
                        generation: 1,
                    },
                    1,
                    inventory,
                    profile.limits,
                )
                .unwrap();
                (
                    spec.index,
                    PageModel {
                        spec: *spec,
                        kernel,
                        epoch: 1,
                        grant: None,
                        tombstoned: false,
                        orders: Vec::new(),
                        free,
                    },
                )
            })
            .collect();
        Self {
            pages,
            grants: BTreeMap::new(),
            stored: Vec::new(),
            order_pages: BTreeMap::new(),
            op_pages: BTreeMap::new(),
            op_orders: BTreeMap::new(),
            event_pages: BTreeMap::new(),
            holds: BTreeMap::new(),
            known_orders: Vec::new(),
            known_ops: Vec::new(),
            clock: 0,
        }
    }

    fn fence(&self, p: u32) -> ExecutionFence {
        let page = &self.pages[&p];
        let owner = match page.grant {
            None => issuer(),
            Some(g) => {
                let state = self.grants[&g];
                if state.open || !page.tombstoned {
                    state.delegate
                } else {
                    g
                }
            }
        };
        ExecutionFence {
            owner,
            generation: page.epoch,
        }
    }

    fn grant_closed(&self, p: u32) -> bool {
        self.pages[&p].grant.is_some_and(|g| !self.grants[&g].open)
    }

    fn unresolved(&self, p: u32) -> bool {
        let page = &self.pages[&p];
        page.orders.iter().any(|o| {
            page.kernel.order(*o).is_some_and(|order| {
                matches!(order.state, OrderState::Held | OrderState::PaymentUnknown)
            })
        })
    }

    fn ctx(&self, mode: FenceMode, p: u32, now: u64) -> Context {
        let current = self.fence(p);
        let (fence, semantics_version) = match mode {
            FenceMode::Current => (current, SEMANTICS_VERSION),
            FenceMode::Issuer => (
                ExecutionFence {
                    owner: issuer(),
                    generation: current.generation,
                },
                SEMANTICS_VERSION,
            ),
            FenceMode::Delegate => (
                ExecutionFence {
                    owner: self.pages[&p]
                        .grant
                        .map_or(id(60), |g| self.grants[&g].delegate),
                    generation: current.generation,
                },
                SEMANTICS_VERSION,
            ),
            FenceMode::Stale => (
                ExecutionFence {
                    owner: issuer(),
                    generation: 1,
                },
                SEMANTICS_VERSION,
            ),
            FenceMode::Garbage => (
                ExecutionFence {
                    owner: id(77),
                    generation: 99,
                },
                SEMANTICS_VERSION,
            ),
            FenceMode::WrongSemantics => (current, 4),
        };
        Context {
            fence,
            now_ms: now,
            semantics_version,
        }
    }

    fn first_page(&self) -> u32 {
        *self.pages.keys().next().unwrap()
    }

    fn plan_reserve(&self, req: &DelegatedReserve) -> Plan {
        if req.id.scope != show_scope() {
            return Plan::Refuse(MappingError::WrongScope);
        }
        let key = (req.id.principal, req.id.request);
        if let Some(stored) = self.stored.iter().find(|s| s.key == key) {
            let page = &self.pages[&stored.page];
            let selection = match req.selection {
                ShowSelection::GeneralAdmission { count } => Selection::GeneralAdmission { count },
                ShowSelection::Seats { first, count } => {
                    let end = first.checked_add(u32::from(count));
                    match end {
                        Some(end)
                            if page.spec.kind == PageKind::Seat
                                && first >= page.spec.start
                                && end <= page.spec.end =>
                        {
                            Selection::Seats {
                                first: (first - page.spec.start) as u16,
                                count,
                            }
                        }
                        _ => return Plan::Refuse(MappingError::CommandConflict),
                    }
                }
            };
            return Plan::Kernel {
                page: stored.page,
                selection,
                fresh: false,
            };
        }
        let (target, selection) = match req.selection {
            ShowSelection::Seats { first, count } => {
                if count > MAX_BUNDLE {
                    return Plan::Refuse(MappingError::BundleTooLarge);
                }
                let Some(page) = self
                    .pages
                    .values()
                    .find(|p| p.spec.start <= first && first < p.spec.end)
                else {
                    return Plan::Refuse(MappingError::UnknownSlot);
                };
                if page.spec.kind != PageKind::Seat {
                    return Plan::Refuse(MappingError::UnknownSlot);
                }
                match first.checked_add(u32::from(count)) {
                    Some(end) if end <= page.spec.end => (
                        page.spec.index,
                        Selection::Seats {
                            first: (first - page.spec.start) as u16,
                            count,
                        },
                    ),
                    _ => return Plan::Refuse(MappingError::CrossPageBundle),
                }
            }
            ShowSelection::GeneralAdmission { count } => {
                let Some(page) = self
                    .pages
                    .values()
                    .filter(|p| p.spec.kind == PageKind::Ga && p.kernel.remaining() >= count)
                    .min_by_key(|p| p.spec.start)
                else {
                    return Plan::Refuse(MappingError::GaSpanningPages);
                };
                (page.spec.index, Selection::GeneralAdmission { count })
            }
        };
        if self.grant_closed(target) {
            return Plan::Refuse(MappingError::GrantClosed);
        }
        if self
            .order_pages
            .get(&req.order_id)
            .is_some_and(|p| *p != target)
        {
            return Plan::Synth(Rejection::OrderExists);
        }
        if self
            .op_pages
            .get(&req.payment)
            .is_some_and(|p| *p != target)
        {
            return Plan::Synth(Rejection::OperationAlreadyBound);
        }
        Plan::Kernel {
            page: target,
            selection,
            fresh: true,
        }
    }
}

fn kernel_request(req: &DelegatedReserve, page: u32, selection: Selection) -> Reserve {
    Reserve {
        id: CommandId {
            scope: page_scope(page),
            principal: req.id.principal,
            request: req.id.request,
        },
        order_id: req.order_id,
        expected_business_epoch: req.expected_business_epoch,
        selection,
        amount: req.amount,
        quote_hash: req.quote_hash,
        policy_hash: req.policy_hash,
        expires_at_ms: req.expires_at_ms,
        payment: req.payment,
    }
}

// ----------------------------------------------------------------- harness

const ATOMS: [u128; 8] = [10_000, 10_000, 10_000, 10_000, 10_000, 1, 20_000, 0];
const EXPIRY: [u64; 5] = [0, 2, 6, 25, 60];
const CAPTURE_ATOMS: [u128; 5] = [10_000, 10_000, 10_000, 1, 20_000];

struct Harness<'a> {
    profile: &'a Profile,
    subject: Subject,
    m: Model,
    cov: &'a mut Coverage,
    failed_transitions: BTreeSet<(&'static str, KixId, u32)>,
}

impl<'a> Harness<'a> {
    fn new(profile: &'a Profile, fault: Fault, cov: &'a mut Coverage) -> Self {
        let show = DelegatedShow::new(
            show_scope(),
            issuer(),
            RangeTable::new(&profile.pages).unwrap(),
            1,
            profile.limits,
            page_scope,
        )
        .unwrap();
        Self {
            profile,
            subject: Subject { show, fault },
            m: Model::new(profile),
            cov,
            failed_transitions: BTreeSet::new(),
        }
    }

    fn show(&self) -> &DelegatedShow {
        &self.subject.show
    }

    fn pick_order(&self, pick: u8) -> KixId {
        if self.m.known_orders.is_empty() || pick % 8 == 7 {
            tag(ORD, GHOST_ORDER)
        } else {
            self.m.known_orders[usize::from(pick) % self.m.known_orders.len()]
        }
    }

    fn step(&mut self, i: usize, step: &Step) -> Result<(), String> {
        let now = match step.now {
            NowMode::Advance(d) => {
                self.m.clock += d;
                self.m.clock
            }
            NowMode::Regress(k) => self.m.clock.saturating_sub(k),
        };
        self.apply(step, now)
            .map_err(|e| format!("step {i} {step:?}: {e}"))?;
        self.check_state()
            .map_err(|e| format!("after step {i} {step:?}: {e}"))?;
        self.check_replays()
            .map_err(|e| format!("after step {i} {step:?}: {e}"))
    }

    fn apply(&mut self, step: &Step, now: u64) -> Result<(), String> {
        match step.op {
            Op::Reserve(g) => {
                let req = self.build_reserve(&g, now);
                if !self.m.known_orders.contains(&req.order_id) {
                    self.m.known_orders.push(req.order_id);
                }
                if !self.m.known_ops.contains(&req.payment) {
                    self.m.known_ops.push(req.payment);
                }
                self.do_reserve(step, now, req, "reserve")
            }
            Op::Replay(pick) => {
                if self.m.stored.is_empty() {
                    return Ok(());
                }
                let req = self.m.stored[usize::from(pick) % self.m.stored.len()]
                    .req
                    .clone();
                self.do_reserve(step, now, req, "replay")
            }
            Op::Mutate(pick, kind) => {
                if self.m.stored.is_empty() {
                    return Ok(());
                }
                let mut req = self.m.stored[usize::from(pick) % self.m.stored.len()]
                    .req
                    .clone();
                match kind {
                    0 => req.amount = amount(req.amount.atoms() + 1),
                    1 => {
                        req.selection = ShowSelection::Seats {
                            first: 1_000_000,
                            count: 1,
                        }
                    }
                    2 => req.selection = ShowSelection::GeneralAdmission { count: 1 },
                    _ => req.expires_at_ms += 1,
                }
                self.do_reserve(step, now, req, "mutate")
            }
            Op::Expire(pick) => self.do_expire(step, now, self.pick_order(pick)),
            Op::MarkUnknown(pick) => self.do_mark(step, now, self.pick_order(pick)),
            Op::Capture {
                op_pick,
                evt,
                ns,
                amount: amount_pick,
                evidence,
            } => self.do_capture(step, now, op_pick, evt, ns, amount_pick, evidence),
            Op::Lookup(pick) => self.do_lookup(self.pick_order(pick)),
            Op::CreateGrant { grant, delegate } => self.do_create_grant(grant, delegate),
            Op::Delegate { grant, page } => self.do_delegate(now, grant_id(grant), page),
            Op::Revoke { grant } => self.do_revoke(now, grant_id(grant)),
            Op::Undelegate { grant, page } => self.do_undelegate(now, grant_id(grant), page),
        }
    }

    fn build_reserve(&self, g: &ReserveGen, now: u64) -> DelegatedReserve {
        DelegatedReserve {
            id: CommandId {
                scope: if g.wrong_scope { id(77) } else { show_scope() },
                principal: id(2 + g.principal),
                request: tag(REQ, g.req),
            },
            order_id: tag(ORD, g.ord),
            expected_business_epoch: if g.bad_epoch { 2 } else { 1 },
            selection: match g.sel {
                SelGen::Seats { first, count } => ShowSelection::Seats { first, count },
                SelGen::Ga { count } => ShowSelection::GeneralAdmission { count },
            },
            amount: amount(ATOMS[usize::from(g.atoms) % ATOMS.len()]),
            quote_hash: Hash32::from_bytes([3; 32]),
            policy_hash: Hash32::from_bytes([4; 32]),
            expires_at_ms: now + EXPIRY[usize::from(g.expiry) % EXPIRY.len()],
            payment: provider_op(g.opn),
        }
    }

    fn record<T: Debug>(&mut self, got: &Result<T, MappingError>) {
        if let Err(e) = got {
            self.cov.hit(mapping_label(*e));
        }
    }

    fn do_reserve(
        &mut self,
        step: &Step,
        now: u64,
        req: DelegatedReserve,
        family: &str,
    ) -> Result<(), String> {
        self.cov.hit(format!("cmd:{family}"));
        let plan = self.m.plan_reserve(&req);
        let strict = self.profile.strict;
        let page_for_ctx = match &plan {
            Plan::Kernel { page, .. } => *page,
            _ => self.m.first_page(),
        };
        let ctx = self.m.ctx(step.fence, page_for_ctx, now);
        match plan {
            Plan::Refuse(error) => {
                if strict && error != MappingError::WrongScope {
                    return Ok(());
                }
                let got = self.subject.reserve(ctx, &req)?;
                if got != Err(error) {
                    return Err(format!(
                        "pre-kernel refusal: contract says {error:?}, map answered {got:?}"
                    ));
                }
                if strict {
                    let first = self.m.first_page();
                    let kreq =
                        kernel_request(&req, first, Selection::GeneralAdmission { count: 1 });
                    let kreq = Reserve {
                        id: CommandId {
                            scope: req.id.scope,
                            ..kreq.id
                        },
                        ..kreq
                    };
                    let want = self
                        .m
                        .pages
                        .get_mut(&first)
                        .unwrap()
                        .kernel
                        .reserve(ctx, kreq);
                    if !agrees(&got, &want) {
                        return Err(format!("bare kernel answered {want:?}, map {got:?}"));
                    }
                }
                self.record(&got);
                Ok(())
            }
            Plan::Synth(rejection) => {
                let got = self.subject.reserve(ctx, &req)?;
                let want = Ok(AppliedReservation {
                    original: ReserveOutcome::Rejected(rejection),
                    replayed: false,
                });
                if got != want {
                    return Err(format!(
                        "cross-page binding: contract says {want:?}, map answered {got:?}"
                    ));
                }
                self.cov.hit(format!(
                    "reserve:synthesized-{}",
                    rejection_label(rejection)
                ));
                self.cov
                    .hit(format!("rejected:{}", rejection_label(rejection)));
                Ok(())
            }
            Plan::Kernel {
                page,
                selection,
                fresh,
            } => {
                let got = self.subject.reserve(ctx, &req)?;
                let kreq = kernel_request(&req, page, selection);
                let want = self
                    .m
                    .pages
                    .get_mut(&page)
                    .unwrap()
                    .kernel
                    .reserve(ctx, kreq);
                if !agrees(&got, &want) {
                    return Err(format!(
                        "page {page}: bare kernel answered {want:?}, map answered {got:?}"
                    ));
                }
                if fresh && self.m.grant_closed(page) && got.is_ok() {
                    return Err("a fresh reserve was accepted on a cut page".into());
                }
                self.record(&got);
                let Ok(applied) = want else {
                    return Ok(());
                };
                match applied.original {
                    ReserveOutcome::Held(_) => self.cov.hit("reserve:Held"),
                    ReserveOutcome::Rejected(r) => {
                        self.cov.hit(format!("rejected:{}", rejection_label(r)))
                    }
                }
                if applied.replayed {
                    self.cov.hit("reserve:replayed");
                    if fresh {
                        return Err("fresh command reported replayed".into());
                    }
                }
                if fresh {
                    self.m.stored.push(Stored {
                        key: (req.id.principal, req.id.request),
                        req: req.clone(),
                        page,
                        original: applied.original,
                    });
                } else if !applied.replayed {
                    return Err("stored command was applied again".into());
                }
                if !applied.replayed
                    && let ReserveOutcome::Held(order) = applied.original
                {
                    self.bind(page, order, &req)?;
                }
                Ok(())
            }
        }
    }

    fn bind(&mut self, page: u32, order: KixId, req: &DelegatedReserve) -> Result<(), String> {
        self.m.order_pages.insert(order, page);
        self.m.op_pages.insert(req.payment, page);
        self.m.op_orders.insert(req.payment, order);
        let pm = self.m.pages.get_mut(&page).unwrap();
        pm.orders.push(order);
        if let ShowSelection::GeneralAdmission { count } = req.selection {
            let mut slots = BTreeSet::new();
            for _ in 0..count {
                let Some(slot) = pm.free.pop_first() else {
                    return Err(format!(
                        "GA page {page}: kernel accepted a hold of {count} but fewer free slots remain"
                    ));
                };
                slots.insert(slot);
            }
            self.m.holds.insert(
                order,
                SlotHold {
                    page_index: page,
                    slots,
                },
            );
            self.cov.hit("ga:hold");
        }
        Ok(())
    }

    fn do_expire(&mut self, step: &Step, now: u64, order: KixId) -> Result<(), String> {
        self.cov.hit("cmd:expire");
        let Some(&page) = self.m.order_pages.get(&order) else {
            let ctx = self.m.ctx(step.fence, self.m.first_page(), now);
            let got = self.subject.expire(ctx, order)?;
            if got != Err(MappingError::UnknownOrder) {
                return Err(format!("unbound order: expected UnknownOrder, got {got:?}"));
            }
            if self.profile.strict {
                let first = self.m.first_page();
                let want = self
                    .m
                    .pages
                    .get_mut(&first)
                    .unwrap()
                    .kernel
                    .expire(ctx, order);
                if !agrees(&got, &want) {
                    return Err(format!("bare kernel answered {want:?}, map {got:?}"));
                }
            }
            self.record(&got);
            return Ok(());
        };
        let ctx = self.m.ctx(step.fence, page, now);
        let got = self.subject.expire(ctx, order)?;
        let want = self
            .m
            .pages
            .get_mut(&page)
            .unwrap()
            .kernel
            .expire(ctx, order);
        if !agrees(&got, &want) {
            return Err(format!(
                "page {page}: bare kernel answered {want:?}, map answered {got:?}"
            ));
        }
        self.cut_check_fact("expire", step, page, &got)?;
        self.record(&got);
        match want {
            Ok(true) => {
                self.cov.hit("expire:true");
                if let Some(hold) = self.m.holds.remove(&order) {
                    self.m.pages.get_mut(&page).unwrap().free.extend(hold.slots);
                    self.cov.hit("ga:release");
                }
            }
            Ok(false) => self.cov.hit("expire:false"),
            Err(_) => {}
        }
        Ok(())
    }

    /// After the cut, releases and fact recording continue under the held
    /// tombstone fence: with the model's current fence they never answer
    /// `GrantClosed` or `ExecutionFenced`.
    fn cut_check_fact<T: Debug>(
        &self,
        what: &str,
        step: &Step,
        page: u32,
        got: &Result<T, MappingError>,
    ) -> Result<(), String> {
        if matches!(step.fence, FenceMode::Current)
            && matches!(
                got,
                Err(MappingError::GrantClosed)
                    | Err(MappingError::Kernel(KernelError::ExecutionFenced))
            )
        {
            return Err(format!(
                "{what} on page {page} was fenced or closed under the current fence: {got:?}"
            ));
        }
        Ok(())
    }

    fn do_mark(&mut self, step: &Step, now: u64, order: KixId) -> Result<(), String> {
        self.cov.hit("cmd:mark_payment_unknown");
        let Some(&page) = self.m.order_pages.get(&order) else {
            let ctx = self.m.ctx(step.fence, self.m.first_page(), now);
            let got = self.subject.mark(ctx, order)?;
            if got != Err(MappingError::UnknownOrder) {
                return Err(format!("unbound order: expected UnknownOrder, got {got:?}"));
            }
            if self.profile.strict {
                let first = self.m.first_page();
                let want = self
                    .m
                    .pages
                    .get_mut(&first)
                    .unwrap()
                    .kernel
                    .mark_payment_unknown(ctx, order);
                if !agrees(&got, &want) {
                    return Err(format!("bare kernel answered {want:?}, map {got:?}"));
                }
            }
            self.record(&got);
            return Ok(());
        };
        let ctx = self.m.ctx(step.fence, page, now);
        let got = self.subject.mark(ctx, order)?;
        if self.m.grant_closed(page) {
            // A new external send is never authorized after the cut: the map
            // refuses before the kernel, so the answer is GrantClosed (a kernel
            // ExecutionFenced would also keep the send closed, but is not the
            // documented answer).
            if got != Err(MappingError::GrantClosed) {
                return Err(format!(
                    "contract says GrantClosed on cut page {page}, map answered {got:?}"
                ));
            }
            self.record(&got);
            return Ok(());
        }
        let want = self
            .m
            .pages
            .get_mut(&page)
            .unwrap()
            .kernel
            .mark_payment_unknown(ctx, order);
        if !agrees(&got, &want) {
            return Err(format!(
                "page {page}: bare kernel answered {want:?}, map answered {got:?}"
            ));
        }
        self.record(&got);
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    fn do_capture(
        &mut self,
        step: &Step,
        now: u64,
        op_pick: u8,
        evt: u8,
        ns: u8,
        amount_pick: u8,
        evidence: u8,
    ) -> Result<(), String> {
        self.cov.hit("cmd:observe_capture");
        let operation = if self.m.known_ops.is_empty() || op_pick % 8 == 7 {
            provider_op(GHOST_ORDER)
        } else {
            self.m.known_ops[usize::from(op_pick) % self.m.known_ops.len()]
        };
        let namespace = self
            .m
            .op_pages
            .get(&operation)
            .copied()
            .unwrap_or(u32::from(ns));
        let observation = CaptureObservation {
            event_id: tag(EVT, evt.wrapping_mul(8).wrapping_add(namespace as u8)),
            operation,
            amount: amount(CAPTURE_ATOMS[usize::from(amount_pick) % CAPTURE_ATOMS.len()]),
            evidence_hash: Hash32::from_bytes([5 + evidence % 2; 32]),
        };
        let key = (operation.provider, operation.account, observation.event_id);
        let target = self
            .m
            .op_pages
            .get(&operation)
            .or_else(|| self.m.event_pages.get(&key))
            .copied();
        let Some(page) = target else {
            let ctx = self.m.ctx(step.fence, self.m.first_page(), now);
            let got = self.subject.observe(ctx, &observation)?;
            if got != Err(MappingError::UnknownOperation) {
                return Err(format!(
                    "unbound operation, unseen event: expected UnknownOperation, got {got:?}"
                ));
            }
            if self.profile.strict {
                let first = self.m.first_page();
                let want = self
                    .m
                    .pages
                    .get_mut(&first)
                    .unwrap()
                    .kernel
                    .observe_capture(ctx, observation);
                if !agrees(&got, &want) {
                    return Err(format!("bare kernel answered {want:?}, map {got:?}"));
                }
            }
            self.record(&got);
            return Ok(());
        };
        let ctx = self.m.ctx(step.fence, page, now);
        if self.profile.exclude_late_ga_capture
            && self.m.pages[&page].spec.kind == PageKind::Ga
            && let Some(order) = self
                .m
                .op_orders
                .get(&operation)
                .and_then(|o| self.m.pages[&page].kernel.order(*o))
            && order.inventory_owned
            && order.captured.is_none()
            && order.request.amount.atoms() == observation.amount.atoms()
            && ctx.now_ms >= order.request.expires_at_ms
        {
            self.cov.hit("excluded:late-ga-capture");
            return Ok(());
        }
        let got = self.subject.observe(ctx, &observation)?;
        let want = self
            .m
            .pages
            .get_mut(&page)
            .unwrap()
            .kernel
            .observe_capture(ctx, observation);
        if !agrees(&got, &want) {
            return Err(format!(
                "page {page}: bare kernel answered {want:?}, map answered {got:?}"
            ));
        }
        self.cut_check_fact("observe_capture", step, page, &got)?;
        self.record(&got);
        if let Ok(outcome) = want {
            self.cov
                .hit(format!("observed:{}", observation_label(outcome)));
            self.m.event_pages.insert(key, page);
        }
        Ok(())
    }

    fn do_lookup(&mut self, order: KixId) -> Result<(), String> {
        self.cov.hit("cmd:order_lookup");
        let want = self
            .m
            .order_pages
            .get(&order)
            .and_then(|p| self.m.pages[p].kernel.order(order));
        if self.show().order(order) != want {
            return Err(format!(
                "order lookup differs: map {:?}, kernel {want:?}",
                self.show().order(order)
            ));
        }
        if self.show().slot_hold(order) != self.m.holds.get(&order) {
            return Err("slot_hold differs from the lowest-free allocation".into());
        }
        Ok(())
    }

    fn do_create_grant(&mut self, grant: u8, delegate: u8) -> Result<(), String> {
        self.cov.hit("cmd:create_grant");
        let g = grant_id(grant);
        let d = match delegate {
            0 | 2 => id(60),
            1 | 3 => id(61),
            4 => issuer(),
            _ => g,
        };
        let mut allowed = Vec::new();
        if self.m.grants.contains_key(&g) {
            allowed.push(MappingError::GrantExists);
        }
        if g == issuer() || d == issuer() || d == g {
            allowed.push(MappingError::InvalidConfiguration);
        }
        let show = &mut self.subject.show;
        let got = guarded(|| show.create_grant(g, d))?;
        match got {
            Ok(()) if allowed.is_empty() => {
                self.m.grants.insert(
                    g,
                    GrantState {
                        delegate: d,
                        generation: 1,
                        open: true,
                    },
                );
                self.cov.hit("grant:created");
            }
            Err(e) if allowed.contains(&e) => self.cov.hit(mapping_label(e)),
            other => {
                return Err(format!(
                    "create_grant({g:?}, {d:?}): violated {allowed:?}, map answered {other:?}"
                ));
            }
        }
        Ok(())
    }

    fn do_delegate(&mut self, now: u64, g: KixId, p: u32) -> Result<(), String> {
        self.cov.hit("cmd:delegate_page");
        let mut allowed = Vec::new();
        let grant = self.m.grants.get(&g).copied();
        match grant {
            None => allowed.push(MappingError::UnknownGrant),
            Some(state) if !state.open => allowed.push(MappingError::GrantClosed),
            Some(_) => {}
        }
        if !self.m.pages.contains_key(&p) {
            allowed.push(MappingError::UnknownPage);
        } else {
            if self.m.pages[&p].grant.is_some() {
                allowed.push(MappingError::PageDelegated);
            }
            if self.m.unresolved(p) {
                allowed.push(MappingError::OutstandingReservations);
            }
        }
        let show = &mut self.subject.show;
        let got = guarded(|| show.delegate_page(now, g, p))?;
        if !allowed.is_empty() {
            return match got {
                Err(e) if allowed.contains(&e) => {
                    self.cov.hit(mapping_label(e));
                    Ok(())
                }
                other => Err(format!(
                    "delegate_page({g:?}, {p}): violated {allowed:?}, map answered {other:?}"
                )),
            };
        }
        let delegate = grant.unwrap().delegate;
        let epoch = self.m.pages[&p].epoch;
        let next = ExecutionFence {
            owner: delegate,
            generation: epoch + 1,
        };
        let current = Context {
            fence: ExecutionFence {
                owner: issuer(),
                generation: epoch,
            },
            now_ms: now,
            semantics_version: SEMANTICS_VERSION,
        };
        let want = self
            .m
            .pages
            .get_mut(&p)
            .unwrap()
            .kernel
            .replace_owner(current, next);
        match (&got, want) {
            (Ok(fence), Ok(())) if *fence == next => {
                let pm = self.m.pages.get_mut(&p).unwrap();
                pm.epoch += 1;
                pm.grant = Some(g);
                pm.tombstoned = false;
                self.cov.hit("grant:delegated");
                if self.failed_transitions.remove(&("delegate", g, p)) {
                    self.cov.hit("grant:delegate-retry-ok");
                }
                Ok(())
            }
            (Err(MappingError::Kernel(a)), Err(b)) if *a == b => {
                self.cov.hit(mapping_label(MappingError::Kernel(b)));
                self.cov.hit("grant:delegate-failed");
                self.failed_transitions.insert(("delegate", g, p));
                Ok(())
            }
            (got, want) => Err(format!(
                "delegate_page({g:?}, {p}): kernel re-fence {want:?}, map answered {got:?}"
            )),
        }
    }

    fn do_revoke(&mut self, now: u64, g: KixId) -> Result<(), String> {
        self.cov.hit("cmd:revoke_grant");
        let show = &mut self.subject.show;
        let got = guarded(|| show.revoke_grant(now, g))?;
        let Some(state) = self.m.grants.get(&g).copied() else {
            if got != Err(MappingError::UnknownGrant) {
                return Err(format!("unknown grant: map answered {got:?}"));
            }
            self.cov.hit("map:UnknownGrant");
            return Ok(());
        };
        let pending: Vec<u32> = self
            .m
            .pages
            .values()
            .filter(|pm| pm.grant == Some(g) && !pm.tombstoned)
            .map(|pm| pm.spec.index)
            .collect();
        let was_open = state.open;
        if was_open {
            let entry = self.m.grants.get_mut(&g).unwrap();
            entry.open = false;
            entry.generation += 1;
        } else if pending.is_empty() {
            if got != Err(MappingError::GrantClosed) {
                return Err(format!(
                    "closed grant, nothing pending: map answered {got:?}"
                ));
            }
            self.cov.hit("map:GrantClosed");
            return Ok(());
        }
        let mut expected: Result<(), MappingError> = Ok(());
        for p in &pending {
            let pm = self.m.pages.get_mut(p).unwrap();
            let ctx = Context {
                fence: ExecutionFence {
                    owner: state.delegate,
                    generation: pm.epoch,
                },
                now_ms: now,
                semantics_version: SEMANTICS_VERSION,
            };
            let next = ExecutionFence {
                owner: g,
                generation: pm.epoch + 1,
            };
            match pm.kernel.replace_owner(ctx, next) {
                Ok(()) => {
                    pm.epoch += 1;
                    pm.tombstoned = true;
                }
                Err(e) => {
                    expected = Err(MappingError::Kernel(e));
                    break;
                }
            }
        }
        if got != expected {
            return Err(format!(
                "revoke_grant({g:?}): kernel re-fences say {expected:?}, map answered {got:?}"
            ));
        }
        match expected {
            Ok(()) => {
                self.cov.hit("grant:revoked");
                if !was_open && !pending.is_empty() {
                    self.cov.hit("grant:revoke-retry-completed");
                }
            }
            Err(e) => {
                self.cov.hit(mapping_label(e));
                self.cov.hit("grant:revoke-partial");
            }
        }
        Ok(())
    }

    fn do_undelegate(&mut self, now: u64, g: KixId, p: u32) -> Result<(), String> {
        self.cov.hit("cmd:undelegate_page");
        let mut allowed = Vec::new();
        let grant = self.m.grants.get(&g).copied();
        match grant {
            None => allowed.push(MappingError::UnknownGrant),
            Some(state) if state.open => allowed.push(MappingError::GrantOpen),
            Some(_) => {}
        }
        if !self.m.pages.contains_key(&p) {
            allowed.push(MappingError::UnknownPage);
        } else {
            if self.m.pages[&p].grant != Some(g) {
                allowed.push(MappingError::PageNotDelegated);
            }
            if self.m.unresolved(p) {
                allowed.push(MappingError::OutstandingReservations);
            }
        }
        let show = &mut self.subject.show;
        let got = guarded(|| show.undelegate_page(now, g, p))?;
        if !allowed.is_empty() {
            return match got {
                Err(e) if allowed.contains(&e) => {
                    self.cov.hit(mapping_label(e));
                    Ok(())
                }
                other => Err(format!(
                    "undelegate_page({g:?}, {p}): violated {allowed:?}, map answered {other:?}"
                )),
            };
        }
        let delegate = grant.unwrap().delegate;
        let (epoch, tombstoned) = {
            let pm = &self.m.pages[&p];
            (pm.epoch, pm.tombstoned)
        };
        let next = ExecutionFence {
            owner: issuer(),
            generation: epoch + 1,
        };
        let current = Context {
            fence: ExecutionFence {
                owner: if tombstoned { g } else { delegate },
                generation: epoch,
            },
            now_ms: now,
            semantics_version: SEMANTICS_VERSION,
        };
        let want = self
            .m
            .pages
            .get_mut(&p)
            .unwrap()
            .kernel
            .replace_owner(current, next);
        match (&got, want) {
            (Ok(fence), Ok(())) if *fence == next => {
                let pm = self.m.pages.get_mut(&p).unwrap();
                pm.epoch += 1;
                pm.grant = None;
                pm.tombstoned = false;
                self.cov.hit("grant:undelegated");
                if self.failed_transitions.remove(&("undelegate", g, p)) {
                    self.cov.hit("grant:undelegate-retry-ok");
                }
                Ok(())
            }
            (Err(MappingError::Kernel(a)), Err(b)) if *a == b => {
                self.cov.hit(mapping_label(MappingError::Kernel(b)));
                self.cov.hit("grant:undelegate-failed");
                self.failed_transitions.insert(("undelegate", g, p));
                Ok(())
            }
            (got, want) => Err(format!(
                "undelegate_page({g:?}, {p}): kernel re-fence {want:?}, map answered {got:?}"
            )),
        }
    }

    /// Every stored command replays on its pinned page under any fence and
    /// clock, even after capacity shifts, and the replay mutates nothing.
    fn check_replays(&mut self) -> Result<(), String> {
        for index in 0..self.m.stored.len() {
            let s = &self.m.stored[index];
            let (req, original) = (s.req.clone(), s.original);
            let fence = if index % 2 == 0 {
                ExecutionFence {
                    owner: id(77),
                    generation: 99,
                }
            } else {
                ExecutionFence {
                    owner: issuer(),
                    generation: 1,
                }
            };
            let ctx = Context {
                fence,
                now_ms: 0,
                semantics_version: SEMANTICS_VERSION,
            };
            let got = self.subject.reserve(ctx, &req)?;
            let want = Ok(AppliedReservation {
                original,
                replayed: true,
            });
            if got != want {
                return Err(format!(
                    "stored command {:?} did not replay: expected {want:?}, got {got:?}",
                    s_key(&req)
                ));
            }
        }
        Ok(())
    }

    fn check_state(&self) -> Result<(), String> {
        let show = self.show();
        let m = &self.m;
        let mut bound_ops: BTreeMap<ProviderOperation, (u32, KixId)> = BTreeMap::new();
        let mut total = 0;
        for (&p, pm) in &m.pages {
            let kernel = show
                .page_kernel(p)
                .ok_or_else(|| format!("page {p} has no kernel"))?;
            if kernel != &pm.kernel {
                return Err(format!(
                    "page {p}: map kernel differs from the independent kernel\n map: {kernel:?}\n ref: {:?}",
                    pm.kernel
                ));
            }
            if show.page_fence(p) != Some(m.fence(p)) {
                return Err(format!(
                    "page {p}: fence {:?}, contract says {:?}",
                    show.page_fence(p),
                    m.fence(p)
                ));
            }
            if show.grant_of_page(p) != pm.grant {
                return Err(format!(
                    "page {p}: grant_of_page {:?}, model {:?}",
                    show.grant_of_page(p),
                    pm.grant
                ));
            }
            let remaining = pm.kernel.remaining();
            if show.remaining(p) != Some(remaining) {
                return Err(format!("page {p}: remaining differs"));
            }
            total += remaining;
            let len = pm.spec.end - pm.spec.start;
            let mut owned = BTreeSet::new();
            let mut owned_seats = 0_u32;
            let mut held_slots = BTreeSet::new();
            for &o in &m.known_orders {
                let Some(order) = kernel.order(o) else {
                    continue;
                };
                if m.order_pages.get(&o) != Some(&p) {
                    return Err(format!("order {o:?} is on page {p} but bound elsewhere"));
                }
                if let Some((q, other)) = bound_ops.insert(order.request.payment, (p, o)) {
                    return Err(format!(
                        "operation {:?} is bound twice: page {q} order {other:?} and page {p} order {o:?}",
                        order.request.payment
                    ));
                }
                match order.request.selection {
                    Selection::Seats { first, count } => {
                        if count > MAX_BUNDLE
                            || count == 0
                            || u32::from(first) + u32::from(count) > len
                        {
                            return Err(format!(
                                "order {o:?}: bundle {first}+{count} exceeds page {p}"
                            ));
                        }
                        if order.inventory_owned {
                            for seat in first..first + count {
                                if !owned.insert(seat) {
                                    return Err(format!("page {p}: seat {seat} is owned twice"));
                                }
                            }
                            owned_seats += u32::from(count);
                        }
                    }
                    Selection::GeneralAdmission { count } => {
                        let hold = show.slot_hold(o);
                        if let Some(hold) = hold {
                            if hold.page_index != p
                                || hold.slots.len() != count as usize
                                || hold
                                    .slots
                                    .iter()
                                    .any(|s| *s < pm.spec.start || *s >= pm.spec.end)
                            {
                                return Err(format!("order {o:?}: malformed hold {hold:?}"));
                            }
                            for slot in &hold.slots {
                                if !held_slots.insert(*slot) {
                                    return Err(format!("page {p}: slot {slot} is held twice"));
                                }
                            }
                        }
                    }
                }
            }
            match pm.spec.kind {
                PageKind::Seat => {
                    if show.ga_free_slots(p).is_some() {
                        return Err(format!("seat page {p} has a GA free set"));
                    }
                    if owned_seats + remaining != len {
                        return Err(format!(
                            "seat page {p}: owned {owned_seats} + remaining {remaining} != {len}"
                        ));
                    }
                }
                PageKind::Ga => {
                    let free = show
                        .ga_free_slots(p)
                        .ok_or_else(|| format!("GA page {p} has no free set"))?;
                    if free != &pm.free {
                        return Err(format!(
                            "GA page {p}: free {free:?}, lowest-free model {:?}",
                            pm.free
                        ));
                    }
                    if free.len() + held_slots.len() != len as usize
                        || !free.is_disjoint(&held_slots)
                    {
                        return Err(format!(
                            "GA page {p}: free {} + held {} != size {len} or not disjoint",
                            free.len(),
                            held_slots.len()
                        ));
                    }
                    if free.len() as u32 != remaining {
                        return Err(format!(
                            "GA page {p}: free {} but kernel remaining {remaining}",
                            free.len()
                        ));
                    }
                }
            }
        }
        if show.total_remaining() != total {
            return Err("total_remaining differs".into());
        }
        for n in 0..3 {
            let g = grant_id(n);
            if show.grant(g) != m.grants.get(&g).copied() {
                return Err(format!(
                    "grant {g:?}: map {:?}, model {:?}",
                    show.grant(g),
                    m.grants.get(&g)
                ));
            }
        }
        for &o in &m.known_orders {
            let holders = m
                .pages
                .values()
                .filter(|pm| pm.kernel.order(o).is_some())
                .count();
            if holders > 1 {
                return Err(format!("order {o:?} is held by {holders} pages"));
            }
        }
        Ok(())
    }
}

fn s_key(req: &DelegatedReserve) -> (KixId, KixId) {
    (req.id.principal, req.id.request)
}

// ------------------------------------------------------------ run and shrink

fn run(profile: &Profile, steps: &[Step], fault: Fault, cov: &mut Coverage) -> Result<(), String> {
    let mut harness = Harness::new(profile, fault, cov);
    for (i, step) in steps.iter().enumerate() {
        harness.step(i, step)?;
    }
    Ok(())
}

fn fails(profile: &Profile, steps: &[Step], fault: Fault) -> bool {
    run(profile, steps, fault, &mut Coverage::default()).is_err()
}

fn shrink(profile: &Profile, steps: &[Step], fault: Fault) -> Vec<Step> {
    let mut current = steps.to_vec();
    let mut changed = true;
    while changed {
        changed = false;
        let mut index = 0;
        while index < current.len() {
            let mut trial = current.clone();
            trial.remove(index);
            if fails(profile, &trial, fault) {
                current = trial;
                changed = true;
            } else {
                index += 1;
            }
        }
    }
    current
}

struct Failure {
    message: String,
    original: usize,
    shrunk: Vec<Step>,
}

fn check_seed(
    profile: &Profile,
    seed: u64,
    fault: Fault,
    cov: &mut Coverage,
) -> Result<(), Failure> {
    let steps = history(seed, profile);
    let Err(detail) = run(profile, &steps, fault, cov) else {
        return Ok(());
    };
    let shrunk = shrink(profile, &steps, fault);
    Err(Failure {
        message: format!(
            "delegated-exec differential mismatch profile={} seed={seed}\n{detail}\nshrunk {} steps: {shrunk:#?}",
            profile.name,
            shrunk.len()
        ),
        original: steps.len(),
        shrunk,
    })
}

fn check_profile(name: &str, fault: Fault, cov: &mut Coverage) -> Result<(), Failure> {
    let profile = profiles().into_iter().find(|p| p.name == name).unwrap();
    for seed in SEEDS {
        check_seed(&profile, seed, fault, cov)?;
    }
    Ok(())
}

fn assert_clean(name: &str) {
    if let Err(failure) = check_profile(name, Fault::None, &mut Coverage::default()) {
        panic!("{}", failure.message);
    }
}

#[test]
fn one_page_seat_matches_a_bare_kernel() {
    assert_clean("one-page-seat");
}

#[test]
fn one_page_ga_matches_a_bare_kernel() {
    assert_clean("one-page-ga");
}

#[test]
fn multi_page_matches_independent_page_kernels() {
    assert_clean("multi-page");
}

#[test]
fn delegation_cut_invariants_under_interleaved_transitions() {
    assert_clean("multi-page-delegated");
    assert_clean("multi-page-delegated-settling");
}

#[test]
fn coverage_guard_every_family_rejection_and_grant_transition_occurs() {
    assert!(SEEDS.len() >= 8 && STEPS >= 100);
    let mut cov = Coverage::default();
    for profile in profiles() {
        for seed in SEEDS {
            if let Err(failure) = check_seed(&profile, seed, Fault::None, &mut cov) {
                panic!("{}", failure.message);
            }
        }
    }
    let required = required_labels();
    let missing: Vec<&String> = required
        .iter()
        .filter(|l| !cov.labels.contains(*l))
        .collect();
    println!(
        "coverage: {} profiles x {} seeds x {} steps; {} of {} required labels hit",
        profiles().len(),
        SEEDS.len(),
        STEPS,
        required.len() - missing.len(),
        required.len()
    );
    for label in &cov.labels {
        println!("  hit {label}");
    }
    assert!(missing.is_empty(), "labels never hit: {missing:?}");
}

// --------------------------------------------------------- negative controls

/// A test-side wrapper perturbs one answer; the differential must fail, name
/// the seed and print a shrunk history that still fails and passes unperturbed.
fn negative_control(name: &str, fault: Fault) {
    let profile = profiles().into_iter().find(|p| p.name == name).unwrap();
    for seed in SEEDS {
        let Err(failure) = check_seed(&profile, seed, fault, &mut Coverage::default()) else {
            continue;
        };
        assert!(
            failure.message.contains(&format!("seed={seed}")),
            "message lacks the seed"
        );
        assert!(!failure.shrunk.is_empty() && failure.shrunk.len() <= failure.original);
        assert!(
            fails(&profile, &failure.shrunk, fault),
            "shrunk history stopped failing"
        );
        assert!(
            !fails(&profile, &failure.shrunk, Fault::None),
            "shrunk history fails without the fault"
        );
        println!(
            "negative control {fault:?}: first failure at seed={seed}, shrunk {} of {} steps\n{}",
            failure.shrunk.len(),
            failure.original,
            failure
                .message
                .lines()
                .take(2)
                .collect::<Vec<_>>()
                .join("\n")
        );
        return;
    }
    panic!("fault {fault:?} was never detected on profile {name}");
}

#[test]
fn negative_control_flipped_replay_flag_is_detected() {
    negative_control("multi-page", Fault::FlipReplayed);
}

#[test]
fn negative_control_expire_reporting_false_is_detected() {
    negative_control("one-page-seat", Fault::ExpireFalse);
}

#[test]
fn negative_control_closed_grant_reserve_accepted_is_detected() {
    negative_control("multi-page-delegated", Fault::ClosedAccepted);
}

// ------------------------------------------------- open-defect characterization

/// CHARACTERIZATION OF AN OPEN DEFECT, not a contract assertion (AGENTS 8.B).
/// A matching capture at or after expiry on a held GA order makes the kernel
/// release the inventory (`ReturnRequired`), but the map keeps the slot hold
/// and its free set. The next GA reserve then pops an empty free set.
/// When this test starts failing the defect is fixed: delete it and the
/// `exclude_late_ga_capture` switch.
#[test]
fn open_defect_late_ga_capture_leaves_map_free_set_behind_the_kernel() {
    let mut show = common::show(RangeTable::new(&[page(0, 0, 4, PageKind::Ga)]).unwrap());
    let held = show
        .reserve(common::ctx(1), &common::ga_reserve(1, 4))
        .unwrap();
    assert_eq!(held.original, ReserveOutcome::Held(id(1)));
    let late = CaptureObservation {
        event_id: id(60),
        operation: ProviderOperation {
            provider: id(20),
            account: id(21),
            operation: id(1),
        },
        amount: amount(10_000),
        evidence_hash: Hash32::from_bytes([5; 32]),
    };
    assert_eq!(
        show.observe_capture(common::ctx(150), late),
        Ok(ObservationOutcome::ReturnRequired)
    );
    assert_eq!(
        show.remaining(0),
        Some(4),
        "the kernel released the inventory"
    );
    assert!(
        show.ga_free_slots(0).unwrap().is_empty(),
        "the map free set did not follow"
    );
    let mut next = common::ga_reserve(2, 1);
    next.expires_at_ms = 1_000;
    let outcome = catch_unwind(AssertUnwindSafe(|| show.reserve(common::ctx(151), &next)));
    assert!(
        outcome.is_err(),
        "the map no longer panics: the defect is fixed"
    );
}

/// The same open defect found by the differential itself: with the exclusion
/// switched off the one-page GA profile reports the free set falling behind the
/// kernel's remaining (or the map panic itself). Delete with the
/// test above when the defect is fixed.
#[test]
fn open_defect_is_found_by_the_differential_when_not_excluded() {
    let mut profile = profiles()
        .into_iter()
        .find(|p| p.name == "one-page-ga")
        .unwrap();
    profile.exclude_late_ga_capture = false;
    for seed in SEEDS {
        if let Err(failure) = check_seed(&profile, seed, Fault::None, &mut Coverage::default()) {
            assert!(
                failure.message.contains("kernel remaining")
                    || failure.message.contains("the map panicked"),
                "{}",
                failure.message
            );
            println!(
                "open defect via the differential: seed={seed}, shrunk {} of {} steps",
                failure.shrunk.len(),
                failure.original
            );
            return;
        }
    }
    panic!("no seed reached the late GA capture: the defect is fixed or the generator changed");
}
