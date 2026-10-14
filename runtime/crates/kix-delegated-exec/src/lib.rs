#![forbid(unsafe_code)]
#![deny(
    clippy::disallowed_types,
    clippy::disallowed_methods,
    clippy::float_arithmetic
)]
//! KIX delegated-execution mapping layer. NOT a service.
//!
//! This crate maps the extended rights-scale profile's page model
//! (`docs/contracts/RIGHTS_SCALE_PROFILE.md` §3, §5, §10) onto
//! `kix-kernel-v5` `Kernel` instances. One `InventoryPage` or GA slot-range
//! shard corresponds to exactly one kernel `Inventory`, so a show larger than
//! the kernel's `MAX_SEATS = 4,096` is run as a set of pages whose kernels are
//! operated concurrently under one map. These are the draft mapping rules this
//! node (rs-3b) records for the Astra architecture audit; they do not amend the
//! contract by themselves.
//!
//! Draft mapping rules (contract §5, §10 items 7-8):
//!
//! - Seat page `[start, end)` maps to `Inventory::seats(&[end - start])`, one
//!   kernel segment. Show slot `i` maps to kernel seat `i - start`.
//! - GA page `[start, end)` maps to `Inventory::general_admission(end - start)`.
//!   The executor picks the `count` lowest free show slots inside the page
//!   range (deterministic lowest-free-slot allocation) and records the
//!   `order_id -> (page, slot set)` hold. A successful `expire` returns the
//!   set. `free + held == end - start` is the off-chain mirror of RS-C02.
//! - A seat `Seats { first, count }` selection must lie inside one page's
//!   range (`CrossPageBundle` otherwise) and `count` must not exceed the
//!   kernel's `MAX_BUNDLE` (`BundleTooLarge`). A GA request no single GA page
//!   can serve is `GaSpanningPages`. All three fail before any kernel call;
//!   nothing is mutated.
//! - Command identity: a show-level command
//!   `CommandId { scope = show scope, principal, request }` is translated to
//!   the kernel command `CommandId { scope = page scope, principal, request }`
//!   of the page that owns the routed slot. The range table is immutable, so
//!   identical show-level bytes deterministically reach the same kernel and
//!   its first-result replay applies. The map additionally rejects the same
//!   `(principal, request)` pair routed to a different page as
//!   `CommandConflict`, which is the cross-page half of the kernel's own
//!   conflict rule.
//! - Delegation mirrors `GrantControl` (rs-3a): `delegate_page` replaces the
//!   page kernel's fence owner with the grant's delegate and bumps a per-page
//!   delegation epoch; `revoke_grant` closes the grant and replaces every
//!   delegated page's owner with the grant id itself (a held tombstone no
//!   caller can command under); `undelegate_page` restores the issuer owner
//!   at a strictly greater epoch. Stored first results still replay after the
//!   cut because the kernel checks the command record before the fence, so
//!   pre-cut commitments are preserved while new commands under the old fence
//!   get `KernelError::ExecutionFenced` and new consumption is refused with
//!   `GrantClosed` before any kernel call.
//!
//! What this crate is not: it performs no I/O, clock reads, random generation,
//! replication, consensus, storage, or chain access. It does not authenticate
//! principals, delegates, or grants; grant state is a caller-maintained
//! in-memory mirror, not a chain read. Delegated execution stays disabled at
//! runtime (`runtime/ARCHITECTURE.toml` `delegated_execution_enabled = false`);
//! nothing here is a wire, OpenAPI, or command-catalogue name. Grant
//! expiry/TTL, allowed-operation sets, and the page size P stay undefined
//! (contract §10.8, §4). A GA page's free set is per-slot memory; the
//! contract does not bound GA page size and this crate does not choose one.

use std::collections::{BTreeMap, BTreeSet};

use kix_kernel_v5::{
    AppliedReservation, CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel,
    KernelError, Limits, MAX_BUNDLE, MAX_SEATS, ObservationOutcome, Order, ProviderOperation,
    Reserve, ReserveOutcome, SEMANTICS_VERSION, Selection,
};
use kix_types::{AssetAmount, Hash32, KixId};

/// Kind of one page in the immutable range table.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PageKind {
    /// Reserved seating; show slots map to kernel seat indices.
    Seat,
    /// General admission; the kernel keeps a quantity counter and the map
    /// keeps the free-slot set for the chain's anonymous slot range.
    Ga,
}

/// One entry of the chain's sealed range table, mirrored off-chain.
/// `start..end` is the half-open show-slot interval the page owns.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PageSpec {
    pub index: u32,
    pub start: u32,
    pub end: u32,
    pub kind: PageKind,
}

/// Ordered, non-overlapping, non-empty page table. Every show slot has at most
/// one owning page (the single original authority of blueprint §6 rule 1).
/// The table is immutable once built, mirroring the sealed on-chain table.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RangeTable {
    pages: Vec<PageSpec>,
}

impl RangeTable {
    /// Builds the table from caller-supplied pages. The input order does not
    /// matter; the table is sorted by `start` and checked for empty pages,
    /// duplicate indices, overlaps, and seat pages larger than `MAX_SEATS`.
    pub fn new(pages: &[PageSpec]) -> Result<Self, MappingError> {
        if pages.is_empty() {
            return Err(MappingError::InvalidConfiguration);
        }
        let mut pages = pages.to_vec();
        pages.sort_by_key(|page| page.start);
        let mut indices = BTreeSet::new();
        let mut previous_end = None;
        for page in &pages {
            if page.start >= page.end || !indices.insert(page.index) {
                return Err(MappingError::InvalidConfiguration);
            }
            if page.kind == PageKind::Seat && page.end - page.start > u32::from(MAX_SEATS) {
                return Err(MappingError::InvalidConfiguration);
            }
            if let Some(end) = previous_end
                && page.start < end
            {
                return Err(MappingError::InvalidConfiguration);
            }
            previous_end = Some(page.end);
        }
        Ok(Self { pages })
    }

    /// The page owning `slot`, if any.
    pub fn page_of(&self, slot: u32) -> Option<&PageSpec> {
        self.pages
            .iter()
            .find(|page| page.start <= slot && slot < page.end)
    }

    pub fn pages(&self) -> &[PageSpec] {
        &self.pages
    }
}

/// Show-level selection a caller asks the map to route. `first` is a show slot
/// number in `[0, capacity)`, not a kernel-local seat index.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ShowSelection {
    Seats { first: u32, count: u16 },
    GeneralAdmission { count: u32 },
}

/// A show-level reserve command. `id.scope` is the show's business scope; the
/// map rewrites it to the owning page's scope before calling the kernel.
/// Every other field passes through unchanged into the kernel `Reserve`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DelegatedReserve {
    pub id: CommandId,
    pub order_id: KixId,
    pub expected_business_epoch: u64,
    pub selection: ShowSelection,
    pub amount: AssetAmount,
    pub quote_hash: Hash32,
    pub policy_hash: Hash32,
    pub expires_at_ms: u64,
    pub payment: ProviderOperation,
}

/// In-memory mirror of one `GrantControl` (rs-3a). `generation` starts at 1
/// and advances once at the cut; `open` is the currentness bit the delegated
/// paths check. Not a chain read and not an authenticated object.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct GrantState {
    pub delegate: KixId,
    pub generation: u64,
    pub open: bool,
}

/// The show slots a GA hold occupies inside one page.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SlotHold {
    pub page_index: u32,
    pub slots: BTreeSet<u32>,
}

/// Errors raised by the mapping layer before or instead of a kernel call.
/// `Kernel` wraps a `KernelError` the owning page's kernel returned.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MappingError {
    /// The slot is outside every page range, or a seat selection names a slot
    /// owned by a GA page.
    UnknownSlot,
    /// A seat bundle would cross a page boundary. Rejected before any kernel
    /// call; partial multi-page effects do not exist.
    CrossPageBundle,
    /// `count` exceeds the kernel `MAX_BUNDLE`.
    BundleTooLarge,
    /// No single GA page can serve the request (including: no GA page exists).
    GaSpanningPages,
    /// The page index is not in the range table.
    UnknownPage,
    /// The page is not delegated to the named grant.
    PageNotDelegated,
    /// The page is already delegated to a grant.
    PageDelegated,
    /// The grant id is not known to this show.
    UnknownGrant,
    /// A grant with this id already exists.
    GrantExists,
    /// The grant exists but is closed: new commitments and new external sends
    /// are refused. Stored first results still replay inside the kernel.
    GrantClosed,
    /// `undelegate_page` requires a closed grant.
    GrantOpen,
    /// The page carries unresolved reservations (kernel `Held` or
    /// `PaymentUnknown` orders): it is not delegatable and, after the cut,
    /// not a "validated unused remainder" (RS-C07b mirror).
    OutstandingReservations,
    /// The order id is not tracked by this show.
    UnknownOrder,
    /// The operation identity is bound to no page and its event key was never
    /// recorded, so no kernel can be routed to.
    UnknownOperation,
    /// The same `(principal, request)` command identity routed to a different
    /// page than before, or the request named a scope that is not this show.
    CommandConflict,
    /// The request's command scope is not this show's scope.
    WrongScope,
    /// The owning page's kernel returned this error.
    Kernel(KernelError),
    /// The range table, scopes, grant or caller-supplied parameters are
    /// internally inconsistent.
    InvalidConfiguration,
}

#[derive(Debug)]
struct Page {
    spec: PageSpec,
    scope: KixId,
    kernel: Kernel,
    /// Per-page delegation epoch. It is the kernel fence generation and
    /// strictly increases on every authority transition for this page.
    epoch: u64,
    grant: Option<KixId>,
    orders: BTreeSet<KixId>,
    /// Free show slots for GA pages; `None` for seat pages.
    ga_free: Option<BTreeSet<u32>>,
}

/// One show run as a map of page kernels. Owns the kernels, the in-memory
/// grant mirror, the cross-page command index, and the GA slot bookkeeping.
#[derive(Debug)]
pub struct DelegatedShow {
    scope: KixId,
    issuer: KixId,
    table: RangeTable,
    pages: BTreeMap<u32, Page>,
    grants: BTreeMap<KixId, GrantState>,
    /// `(principal, request)` -> page index, recorded when the kernel stores
    /// the command. The cross-page half of the command-conflict rule.
    routed_commands: BTreeMap<(KixId, KixId), u32>,
    order_pages: BTreeMap<KixId, u32>,
    operation_pages: BTreeMap<ProviderOperation, u32>,
    /// `(provider, account, event_id)` -> page index, for conflict routing of
    /// observations whose operation is not bound on this show.
    event_pages: BTreeMap<(KixId, KixId, KixId), u32>,
    ga_holds: BTreeMap<KixId, SlotHold>,
}

impl DelegatedShow {
    /// Builds one kernel per page. `page_scope` derives each page's business
    /// scope (the adapter derives it from the show id and page index); all
    /// scopes must be distinct. Each page kernel starts under the issuer
    /// authority at delegation epoch 1. `business_epoch` and `limits` are
    /// caller-supplied and shared by the pages.
    pub fn new(
        scope: KixId,
        issuer: KixId,
        table: RangeTable,
        business_epoch: u64,
        limits: Limits,
        page_scope: impl Fn(u32) -> KixId,
    ) -> Result<Self, MappingError> {
        if business_epoch == 0
            || limits.commands == 0
            || limits.orders == 0
            || limits.observations == 0
        {
            return Err(MappingError::InvalidConfiguration);
        }
        let mut pages = BTreeMap::new();
        let mut scopes = BTreeSet::new();
        for spec in table.pages() {
            let scope = page_scope(spec.index);
            if !scopes.insert(scope) {
                return Err(MappingError::InvalidConfiguration);
            }
            let length = spec.end - spec.start;
            let (inventory, ga_free) = match spec.kind {
                PageKind::Seat => (
                    Inventory::seats(&[
                        u16::try_from(length).map_err(|_| MappingError::InvalidConfiguration)?
                    ])
                    .map_err(MappingError::Kernel)?,
                    None,
                ),
                PageKind::Ga => (
                    Inventory::general_admission(length).map_err(MappingError::Kernel)?,
                    Some((spec.start..spec.end).collect()),
                ),
            };
            let kernel = Kernel::new(
                scope,
                ExecutionFence {
                    owner: issuer,
                    generation: 1,
                },
                business_epoch,
                inventory,
                limits,
            )
            .map_err(MappingError::Kernel)?;
            pages.insert(
                spec.index,
                Page {
                    spec: *spec,
                    scope,
                    kernel,
                    epoch: 1,
                    grant: None,
                    orders: BTreeSet::new(),
                    ga_free,
                },
            );
        }
        Ok(Self {
            scope,
            issuer,
            table,
            pages,
            grants: BTreeMap::new(),
            routed_commands: BTreeMap::new(),
            order_pages: BTreeMap::new(),
            operation_pages: BTreeMap::new(),
            event_pages: BTreeMap::new(),
            ga_holds: BTreeMap::new(),
        })
    }

    pub fn table(&self) -> &RangeTable {
        &self.table
    }

    pub fn page_of_slot(&self, slot: u32) -> Option<&PageSpec> {
        self.table.page_of(slot)
    }

    /// Read-only access to one page's kernel (test and driver inspection).
    pub fn page_kernel(&self, page_index: u32) -> Option<&Kernel> {
        self.pages.get(&page_index).map(|page| &page.kernel)
    }

    /// The fence a command context must carry to be accepted by this page's
    /// kernel right now: the issuer on the direct path, the delegate while
    /// its grant is open, and the grant id itself (a held tombstone) between
    /// the cut and `undelegate_page`.
    pub fn page_fence(&self, page_index: u32) -> Option<ExecutionFence> {
        let page = self.pages.get(&page_index)?;
        Some(self.fence_of(page))
    }

    fn fence_of(&self, page: &Page) -> ExecutionFence {
        let owner = match page.grant {
            None => self.issuer,
            Some(grant_id) => match self.grants.get(&grant_id) {
                Some(grant) if grant.open => grant.delegate,
                _ => grant_id,
            },
        };
        ExecutionFence {
            owner,
            generation: page.epoch,
        }
    }

    pub fn grant(&self, grant_id: KixId) -> Option<GrantState> {
        self.grants.get(&grant_id).copied()
    }

    /// The grant this page is delegated to, if any.
    pub fn grant_of_page(&self, page_index: u32) -> Option<KixId> {
        self.pages.get(&page_index).and_then(|page| page.grant)
    }

    /// Remaining inventory on one page (kernel `remaining()`).
    pub fn remaining(&self, page_index: u32) -> Option<u32> {
        self.pages
            .get(&page_index)
            .map(|page| page.kernel.remaining())
    }

    /// Sum of `remaining()` over all pages.
    pub fn total_remaining(&self) -> u32 {
        self.pages
            .values()
            .map(|page| page.kernel.remaining())
            .sum()
    }

    /// Free show slots inside one GA page's range. `None` for seat pages and
    /// unknown indices.
    pub fn ga_free_slots(&self, page_index: u32) -> Option<&BTreeSet<u32>> {
        self.pages
            .get(&page_index)
            .and_then(|page| page.ga_free.as_ref())
    }

    /// The GA slot hold recorded for an order, if any.
    pub fn slot_hold(&self, order_id: KixId) -> Option<&SlotHold> {
        self.ga_holds.get(&order_id)
    }

    /// The order as the owning page's kernel stores it.
    pub fn order(&self, order_id: KixId) -> Option<&Order> {
        let page_index = *self.order_pages.get(&order_id)?;
        self.pages.get(&page_index)?.kernel.order(order_id)
    }

    /// Routes a show-level reserve to the owning page kernel. Mapping-level
    /// rejections happen before any kernel call and mutate nothing: boundary
    /// and size checks, the cross-page command-conflict check, the
    /// show-scope check, and the closed-grant cut (`GrantClosed`) — the cut
    /// applies only to commands the kernel never stored, so an identical
    /// retry of a pre-cut command still reaches the kernel and returns its
    /// stored first result (`replayed: true`) regardless of the fence.
    /// The command identity is `(show scope, principal, request)` translated
    /// to `(page scope, principal, request)`; a retry of identical bytes is
    /// the kernel's own first-result replay.
    pub fn reserve(
        &mut self,
        ctx: Context,
        request: &DelegatedReserve,
    ) -> Result<AppliedReservation, MappingError> {
        if request.id.scope != self.scope {
            return Err(MappingError::WrongScope);
        }
        let (page_index, selection) = self.route(request.selection)?;
        let key = (request.id.principal, request.id.request);
        let seen = self.routed_commands.get(&key).copied();
        if let Some(existing) = seen
            && existing != page_index
        {
            return Err(MappingError::CommandConflict);
        }
        // The cut gate applies only to commands the kernel has not stored.
        // A stored command goes through so the kernel can return its own
        // first-result replay or CommandConflict — replay precedes the fence
        // check there, which is what preserves pre-cut commitments.
        if seen.is_none()
            && let Some(grant_id) = self.pages[&page_index].grant
            && !self.grants[&grant_id].open
        {
            return Err(MappingError::GrantClosed);
        }
        let page_scope = self.pages[&page_index].scope;
        let applied = self
            .pages
            .get_mut(&page_index)
            .expect("routed page")
            .kernel
            .reserve(
                ctx,
                Reserve {
                    id: CommandId {
                        scope: page_scope,
                        principal: request.id.principal,
                        request: request.id.request,
                    },
                    order_id: request.order_id,
                    expected_business_epoch: request.expected_business_epoch,
                    selection,
                    amount: request.amount,
                    quote_hash: request.quote_hash,
                    policy_hash: request.policy_hash,
                    expires_at_ms: request.expires_at_ms,
                    payment: request.payment,
                },
            )
            .map_err(MappingError::Kernel)?;
        // The kernel stored a command record (Ok covers Held and Rejected);
        // errors stored nothing, so they pin no route.
        self.routed_commands.insert(key, page_index);
        if let ReserveOutcome::Held(order_id) = applied.original {
            self.order_pages.insert(order_id, page_index);
            self.operation_pages.insert(request.payment, page_index);
            let hold = {
                let page = self.pages.get_mut(&page_index).expect("routed page");
                page.orders.insert(order_id);
                if let ShowSelection::GeneralAdmission { count } = request.selection {
                    let free = page.ga_free.as_mut().expect("GA page free set");
                    let mut slots = BTreeSet::new();
                    for _ in 0..count {
                        slots.insert(free.pop_first().expect("remaining >= count"));
                    }
                    Some(SlotHold { page_index, slots })
                } else {
                    None
                }
            };
            if let Some(hold) = hold {
                self.ga_holds.insert(order_id, hold);
            }
        }
        Ok(applied)
    }

    fn route(&self, selection: ShowSelection) -> Result<(u32, Selection), MappingError> {
        match selection {
            ShowSelection::Seats { first, count } => {
                if count > MAX_BUNDLE {
                    return Err(MappingError::BundleTooLarge);
                }
                let page = self.table.page_of(first).ok_or(MappingError::UnknownSlot)?;
                if page.kind != PageKind::Seat {
                    return Err(MappingError::UnknownSlot);
                }
                let end = first
                    .checked_add(u32::from(count))
                    .ok_or(MappingError::CrossPageBundle)?;
                if end > page.end {
                    return Err(MappingError::CrossPageBundle);
                }
                let local = u16::try_from(first - page.start)
                    .map_err(|_| MappingError::InvalidConfiguration)?;
                Ok((
                    page.index,
                    Selection::Seats {
                        first: local,
                        count,
                    },
                ))
            }
            ShowSelection::GeneralAdmission { count } => {
                // Deterministic page choice: the lowest-start GA page that can
                // serve the whole request. Splitting a request across pages
                // would be a partial multi-page effect, which does not exist.
                let page = self
                    .pages
                    .values()
                    .filter(|page| {
                        page.spec.kind == PageKind::Ga && page.kernel.remaining() >= count
                    })
                    .min_by_key(|page| page.spec.start)
                    .ok_or(MappingError::GaSpanningPages)?;
                Ok((page.spec.index, Selection::GeneralAdmission { count }))
            }
        }
    }

    /// Releases an expired held order on its owning page. Releases and fact
    /// recording are not new commitments, so this stays available after a
    /// grant cut under the held tombstone fence; a GA hold's slots return to
    /// the page's free set only when the kernel reports a real release.
    pub fn expire(&mut self, ctx: Context, order_id: KixId) -> Result<bool, MappingError> {
        let page_index = *self
            .order_pages
            .get(&order_id)
            .ok_or(MappingError::UnknownOrder)?;
        let page = self.pages.get_mut(&page_index).expect("order page");
        let released = page
            .kernel
            .expire(ctx, order_id)
            .map_err(MappingError::Kernel)?;
        if released && let Some(hold) = self.ga_holds.remove(&order_id) {
            let free = page.ga_free.as_mut().expect("GA page free set");
            free.extend(hold.slots);
        }
        Ok(released)
    }

    /// Authorizes the first external send for a held order. This is a new
    /// commitment step, so it is refused with `GrantClosed` after the cut,
    /// like every delegated consumption path on the chain.
    pub fn mark_payment_unknown(
        &mut self,
        ctx: Context,
        order_id: KixId,
    ) -> Result<(), MappingError> {
        let page_index = *self
            .order_pages
            .get(&order_id)
            .ok_or(MappingError::UnknownOrder)?;
        if let Some(grant_id) = self.pages[&page_index].grant
            && !self.grants[&grant_id].open
        {
            return Err(MappingError::GrantClosed);
        }
        self.pages
            .get_mut(&page_index)
            .expect("order page")
            .kernel
            .mark_payment_unknown(ctx, order_id)
            .map_err(MappingError::Kernel)
    }

    /// Records a capture observation on the page that owns the bound
    /// operation, or on the page that first recorded the event key (the
    /// conflict path for an unbound operation). Fact recording continues
    /// after a cut: late facts are reconciled under current authority, never
    /// dropped.
    pub fn observe_capture(
        &mut self,
        ctx: Context,
        observation: CaptureObservation,
    ) -> Result<ObservationOutcome, MappingError> {
        let event_key = (
            observation.operation.provider,
            observation.operation.account,
            observation.event_id,
        );
        let page_index = self
            .operation_pages
            .get(&observation.operation)
            .or_else(|| self.event_pages.get(&event_key))
            .copied()
            .ok_or(MappingError::UnknownOperation)?;
        let result = self
            .pages
            .get_mut(&page_index)
            .expect("observation page")
            .kernel
            .observe_capture(ctx, observation)
            .map_err(MappingError::Kernel)?;
        self.event_pages.insert(event_key, page_index);
        Ok(result)
    }

    /// Creates the in-memory grant mirror. The grant id, the delegate and the
    /// issuer must be three distinct identities: the delegated fence owner is
    /// the delegate and the post-cut held owner is the grant id, so a
    /// collision would leave a stale fence valid after the cut.
    pub fn create_grant(&mut self, grant_id: KixId, delegate: KixId) -> Result<(), MappingError> {
        if self.grants.contains_key(&grant_id) {
            return Err(MappingError::GrantExists);
        }
        if grant_id == self.issuer || delegate == self.issuer || delegate == grant_id {
            return Err(MappingError::InvalidConfiguration);
        }
        self.grants.insert(
            grant_id,
            GrantState {
                delegate,
                generation: 1,
                open: true,
            },
        );
        Ok(())
    }

    /// Delegates one page to an open grant: bumps the page's delegation epoch
    /// and moves the fence owner to the grant's delegate. The page must be
    /// undelegated and carry no unresolved reservations (RS-C07b mirror).
    /// Returns the fence delegated commands must now carry.
    pub fn delegate_page(
        &mut self,
        now_ms: u64,
        grant_id: KixId,
        page_index: u32,
    ) -> Result<ExecutionFence, MappingError> {
        let grant = self
            .grants
            .get(&grant_id)
            .ok_or(MappingError::UnknownGrant)?;
        if !grant.open {
            return Err(MappingError::GrantClosed);
        }
        let delegate = grant.delegate;
        let issuer = self.issuer;
        let page = self
            .pages
            .get_mut(&page_index)
            .ok_or(MappingError::UnknownPage)?;
        if page.grant.is_some() {
            return Err(MappingError::PageDelegated);
        }
        if Self::has_unresolved(page) {
            return Err(MappingError::OutstandingReservations);
        }
        // The current fence is the direct path: issuer at the current epoch.
        let ctx = Context {
            fence: ExecutionFence {
                owner: issuer,
                generation: page.epoch,
            },
            now_ms,
            semantics_version: SEMANTICS_VERSION,
        };
        page.epoch += 1;
        let next = ExecutionFence {
            owner: delegate,
            generation: page.epoch,
        };
        page.kernel
            .replace_owner(ctx, next)
            .map_err(MappingError::Kernel)?;
        page.grant = Some(grant_id);
        Ok(next)
    }

    /// The revocation cut: one write on the grant mirror (`open = false`,
    /// `generation += 1`, the `revoke_grant` mirror) plus one fence bump per
    /// delegated page moving the owner to the grant id itself. From that
    /// write on, `reserve` and `mark_payment_unknown` on the grant's pages
    /// are refused with `GrantClosed`, and commands carrying the old delegate
    /// fence fail the kernel's own fence check with `ExecutionFenced`.
    /// Pre-cut stored results still replay; `expire` and `observe_capture`
    /// continue under the held tombstone fence.
    pub fn revoke_grant(&mut self, now_ms: u64, grant_id: KixId) -> Result<(), MappingError> {
        let grant = self
            .grants
            .get(&grant_id)
            .ok_or(MappingError::UnknownGrant)?;
        if !grant.open {
            return Err(MappingError::GrantClosed);
        }
        let delegate = grant.delegate;
        // The current delegated fences must be captured before the grant is
        // closed: the post-cut fence owner is the grant id itself.
        let affected: Vec<(u32, ExecutionFence)> = self
            .pages
            .iter()
            .filter(|(_, page)| page.grant == Some(grant_id))
            .map(|(&index, page)| {
                (
                    index,
                    ExecutionFence {
                        owner: delegate,
                        generation: page.epoch,
                    },
                )
            })
            .collect();
        let grant = self.grants.get_mut(&grant_id).expect("checked grant");
        grant.open = false;
        grant.generation += 1;
        for (index, current) in affected {
            let page = self.pages.get_mut(&index).expect("delegated page");
            page.epoch += 1;
            page.kernel
                .replace_owner(
                    Context {
                        fence: current,
                        now_ms,
                        semantics_version: SEMANTICS_VERSION,
                    },
                    ExecutionFence {
                        owner: grant_id,
                        generation: page.epoch,
                    },
                )
                .map_err(MappingError::Kernel)?;
        }
        Ok(())
    }

    /// Returns one page to the direct path after the cut: the grant must be
    /// closed and the page must be a validated unused remainder — no order in
    /// `Held` or `PaymentUnknown`, mirroring the chain's `reserved == 0`
    /// reclaim condition. Bumps the epoch and restores the issuer owner.
    /// Returns the direct-path fence.
    pub fn undelegate_page(
        &mut self,
        now_ms: u64,
        grant_id: KixId,
        page_index: u32,
    ) -> Result<ExecutionFence, MappingError> {
        let grant = self
            .grants
            .get(&grant_id)
            .ok_or(MappingError::UnknownGrant)?;
        if grant.open {
            return Err(MappingError::GrantOpen);
        }
        let issuer = self.issuer;
        let page = self
            .pages
            .get_mut(&page_index)
            .ok_or(MappingError::UnknownPage)?;
        if page.grant != Some(grant_id) {
            return Err(MappingError::PageNotDelegated);
        }
        if Self::has_unresolved(page) {
            return Err(MappingError::OutstandingReservations);
        }
        // The current fence is the held tombstone: the grant id at the
        // current epoch, set by `revoke_grant`.
        let ctx = Context {
            fence: ExecutionFence {
                owner: grant_id,
                generation: page.epoch,
            },
            now_ms,
            semantics_version: SEMANTICS_VERSION,
        };
        page.epoch += 1;
        let next = ExecutionFence {
            owner: issuer,
            generation: page.epoch,
        };
        page.kernel
            .replace_owner(ctx, next)
            .map_err(MappingError::Kernel)?;
        page.grant = None;
        Ok(next)
    }

    /// Kernel `Held` and `PaymentUnknown` orders are the unresolved
    /// reservations: the open `IssuancePayment` mirror of `reserved > 0`.
    /// Confirmed, expired, return-required and reviewed orders do not block
    /// delegation or reclaim.
    fn has_unresolved(page: &Page) -> bool {
        use kix_kernel_v5::OrderState::{Held, PaymentUnknown};
        page.orders.iter().any(|order_id| {
            page.kernel
                .order(*order_id)
                .is_some_and(|order| matches!(order.state, Held | PaymentUnknown))
        })
    }
}
