mod common;

use common::{ctx, ctx_for, id, page, reserve, show};
use kix_delegated_exec::{DelegatedShow, MappingError, PageKind, RangeTable};
use kix_kernel_v5::{ExecutionFence, KernelError, OrderState, ReserveOutcome};

fn show_two_pages() -> DelegatedShow {
    show(
        RangeTable::new(&[
            page(0, 0, 4_096, PageKind::Seat),
            page(1, 4_096, 7_000, PageKind::Seat),
        ])
        .unwrap(),
    )
}

fn grant(show: &mut DelegatedShow, grant: u8, delegate: u8) -> ExecutionFence {
    show.create_grant(id(grant), id(delegate)).unwrap();
    show.delegate_page(1, id(grant), 0).unwrap()
}

#[test]
fn identical_retries_replay_the_stored_first_result() {
    let mut show = show_two_pages();
    let held = show.reserve(ctx(1), &reserve(1, 0, 2)).unwrap();
    assert_eq!(held.original, ReserveOutcome::Held(id(1)));
    assert!(!held.replayed);
    let replay = show.reserve(ctx(2), &reserve(1, 0, 2)).unwrap();
    assert_eq!(replay.original, held.original);
    assert!(replay.replayed);
    assert_eq!(show.remaining(0), Some(4_094));
}

#[test]
fn same_request_identity_with_a_different_payload_conflicts() {
    let mut show = show_two_pages();
    show.reserve(ctx(1), &reserve(1, 0, 2)).unwrap();
    // Same (principal, request), different slot on the same page: the
    // kernel's own payload comparison rejects it.
    let different_payload = reserve(1, 0, 3);
    assert_eq!(
        show.reserve(ctx(2), &different_payload),
        Err(MappingError::Kernel(KernelError::CommandConflict))
    );
    // Same (principal, request) routed to a different page: the map rejects
    // it before any kernel sees a command under a stolen identity.
    let different_page = reserve(1, 4_096, 1);
    assert_eq!(
        show.reserve(ctx(3), &different_page),
        Err(MappingError::CommandConflict)
    );
    assert_eq!(show.remaining(0), Some(4_094));
    assert_eq!(show.remaining(1), Some(2_904));
}

#[test]
fn delegation_moves_the_execution_fence_to_the_delegate() {
    let mut show = show_two_pages();
    let delegated = grant(&mut show, 50, 60);
    assert_eq!(
        delegated,
        ExecutionFence {
            owner: id(60),
            generation: 2
        }
    );
    assert_eq!(show.page_fence(0), Some(delegated));
    assert_eq!(show.grant_of_page(0), Some(id(50)));

    // The direct path no longer commands the delegated page.
    assert_eq!(
        show.reserve(ctx(10), &reserve(1, 0, 1)),
        Err(MappingError::Kernel(KernelError::ExecutionFenced))
    );
    // The delegate's fence does.
    let held = show
        .reserve(ctx_for(11, delegated), &reserve(1, 0, 1))
        .unwrap();
    assert_eq!(held.original, ReserveOutcome::Held(id(1)));
    // Page 1 is untouched by page 0's delegation.
    show.reserve(ctx(12), &reserve(2, 4_096, 1)).unwrap();
}

#[test]
fn delegation_requires_an_open_grant_an_undelegated_page_and_no_reservations() {
    let mut show = show_two_pages();
    assert_eq!(
        show.delegate_page(1, id(50), 0),
        Err(MappingError::UnknownGrant)
    );
    // A held order is an unresolved reservation: the page is not delegatable.
    show.reserve(ctx(1), &reserve(1, 0, 1)).unwrap();
    show.create_grant(id(50), id(60)).unwrap();
    assert_eq!(
        show.delegate_page(2, id(50), 0),
        Err(MappingError::OutstandingReservations)
    );
    // After the reservation expires the page becomes delegatable.
    assert!(show.expire(ctx(100), id(1)).unwrap());
    show.delegate_page(101, id(50), 0).unwrap();
    assert_eq!(
        show.delegate_page(102, id(50), 0),
        Err(MappingError::PageDelegated)
    );
    // A closed grant cannot take a page.
    show.revoke_grant(103, id(50)).unwrap();
    assert_eq!(
        show.delegate_page(104, id(50), 1),
        Err(MappingError::GrantClosed)
    );
}

#[test]
fn the_cut_refuses_new_commitments_but_replays_stored_results() {
    let mut show = show_two_pages();
    let delegated = grant(&mut show, 50, 60);
    // A pre-cut command commits under the delegate fence.
    show.reserve(ctx_for(10, delegated), &reserve(1, 0, 1))
        .unwrap();
    show.revoke_grant(20, id(50)).unwrap();
    assert!(!show.grant(id(50)).unwrap().open);
    assert_eq!(show.grant(id(50)).unwrap().generation, 2);

    // New commands are refused at the map before any kernel call, whatever
    // fence the caller carries.
    for fence in [delegated, show.page_fence(0).unwrap()] {
        assert_eq!(
            show.reserve(ctx_for(21, fence), &reserve(2, 1, 1)),
            Err(MappingError::GrantClosed)
        );
    }
    // The old delegate fence also fails the kernel's own fence check for
    // anything that reaches it; new sends cannot be authorized.
    assert_eq!(
        show.mark_payment_unknown(ctx_for(22, show.page_fence(0).unwrap()), id(1)),
        Err(MappingError::GrantClosed)
    );
    // An identical retry of the pre-cut command still replays its stored
    // first result even under the stale direct fence: the kernel checks the
    // command record before the fence.
    let replay = show.reserve(ctx(23), &reserve(1, 0, 1)).unwrap();
    assert_eq!(replay.original, ReserveOutcome::Held(id(1)));
    assert!(replay.replayed);
    // Releases continue under the held tombstone fence: pre-cut obligations
    // are preserved, not executable.
    assert!(
        show.expire(ctx_for(100, show.page_fence(0).unwrap()), id(1))
            .unwrap()
    );
    assert_eq!(show.order(id(1)).unwrap().state, OrderState::Expired);
}

#[test]
fn the_cut_is_per_grant_and_undelegation_restores_the_direct_path() {
    let mut show = show_two_pages();
    show.create_grant(id(50), id(60)).unwrap();
    show.create_grant(id(51), id(61)).unwrap();
    show.delegate_page(10, id(50), 0).unwrap();
    let second = show.delegate_page(10, id(51), 1).unwrap();
    show.revoke_grant(20, id(50)).unwrap();

    // Page 1's grant is unaffected by page 0's cut.
    show.reserve(ctx_for(21, second), &reserve(1, 4_096, 1))
        .unwrap();
    assert_eq!(
        show.reserve(ctx_for(22, second), &reserve(2, 0, 1)),
        Err(MappingError::GrantClosed)
    );

    // Undelegating page 0 requires the closed grant it was delegated to.
    // An open grant answers GrantOpen; once grant 51 is cut too, page 0 —
    // delegated to grant 50 — answers PageNotDelegated for it.
    assert_eq!(
        show.undelegate_page(22, id(51), 0),
        Err(MappingError::GrantOpen)
    );
    show.revoke_grant(22, id(51)).unwrap();
    assert_eq!(
        show.undelegate_page(23, id(51), 0),
        Err(MappingError::PageNotDelegated)
    );
    let restored = show.undelegate_page(23, id(50), 0).unwrap();
    assert_eq!(
        restored,
        ExecutionFence {
            owner: id(1),
            generation: 4
        }
    );
    assert_eq!(show.grant_of_page(0), None);
    // The direct path works again; every older fence is dead.
    show.reserve(ctx_for(24, restored), &reserve(3, 0, 1))
        .unwrap();
    assert_eq!(
        show.reserve(ctx_for(25, second), &reserve(4, 1, 1)),
        Err(MappingError::Kernel(KernelError::ExecutionFenced))
    );
}

#[test]
fn undelegation_requires_a_closed_grant_and_a_validated_unused_remainder() {
    let mut show = show_two_pages();
    let delegated = grant(&mut show, 50, 60);
    // An open grant cannot be undelegated.
    assert_eq!(
        show.undelegate_page(10, id(50), 0),
        Err(MappingError::GrantOpen)
    );
    // A reservation committed pre-cut strands the reclaim: the remainder is
    // not validated-unused while it is unresolved.
    show.reserve(ctx_for(10, delegated), &reserve(1, 0, 1))
        .unwrap();
    show.mark_payment_unknown(ctx_for(11, delegated), id(1))
        .unwrap();
    show.revoke_grant(20, id(50)).unwrap();
    assert_eq!(
        show.undelegate_page(21, id(50), 0),
        Err(MappingError::OutstandingReservations)
    );
}

#[test]
fn grant_identity_collisions_are_invalid_configuration() {
    let mut show = show_two_pages();
    // grant id, delegate and issuer (id(1)) must be three distinct
    // identities, or a stale fence would survive the cut.
    for (grant, delegate) in [(1, 60), (50, 1), (50, 50)] {
        assert_eq!(
            show.create_grant(id(grant), id(delegate)),
            Err(MappingError::InvalidConfiguration)
        );
    }
    show.create_grant(id(50), id(60)).unwrap();
    assert_eq!(
        show.create_grant(id(50), id(61)),
        Err(MappingError::GrantExists)
    );
}
