#![allow(dead_code)]

use kix_kernel_v5::{
    ActorKind, Authority, ClosureEvaluation, ConditionEvidence, Context, ExecutionFence, Inventory,
    Kernel, Limits, ProviderOperation, Reserve, Terminate,
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

pub fn id(n: u8) -> KixId {
    KixId::from_bytes([n; 16])
}

pub fn fence() -> ExecutionFence {
    ExecutionFence {
        owner: id(1),
        generation: 1,
    }
}

pub fn ctx(now_ms: u64) -> Context {
    Context {
        fence: fence(),
        now_ms,
        semantics_version: kix_kernel_v5::SEMANTICS_VERSION,
    }
}

pub fn limits() -> Limits {
    Limits {
        commands: 1_024,
        orders: 1_024,
        observations: 1_024,
    }
}

pub fn amount(atoms: u128) -> AssetAmount {
    AssetAmount::checked(
        AssetId::from_bytes([7; 32]),
        atoms,
        u128::MAX,
        RegistryVersion::new(1).unwrap(),
        Hash32::from_bytes([8; 32]),
    )
    .unwrap()
}

pub fn engine() -> Kernel {
    Kernel::new(
        id(9),
        fence(),
        1,
        Inventory::seats(&[70, 10]).unwrap(),
        limits(),
    )
    .unwrap()
}

pub fn reserve(n: u8, first: u16, count: u16) -> Reserve {
    Reserve {
        id: kix_kernel_v5::CommandId {
            scope: id(9),
            principal: id(2),
            request: id(n),
        },
        order_id: id(n),
        expected_business_epoch: 1,
        selection: kix_kernel_v5::Selection::Seats { first, count },
        amount: amount(10_000),
        quote_hash: Hash32::from_bytes([3; 32]),
        policy_hash: Hash32::from_bytes([4; 32]),
        expires_at_ms: 100,
        payment: ProviderOperation {
            provider: id(20),
            account: id(21),
            operation: id(n),
        },
    }
}

pub fn observation(request: &Reserve, event: u8) -> kix_kernel_v5::CaptureObservation {
    kix_kernel_v5::CaptureObservation {
        event_id: id(event),
        operation: request.payment,
        amount: request.amount,
        evidence_hash: Hash32::from_bytes([event; 32]),
    }
}

pub fn closure(holds: [bool; 5]) -> ClosureEvaluation {
    ClosureEvaluation {
        c: std::array::from_fn(|index| ConditionEvidence {
            holds: holds[index],
            evidence_hash: Hash32::from_bytes([index as u8; 32]),
        }),
    }
}

pub fn human(principal: u8) -> Authority {
    Authority {
        authority_id: id(30),
        generation: 1,
        actor: ActorKind::Human,
        principal: id(principal),
    }
}

pub fn terminate_for(kernel: &Kernel, decision: u8, order: u8) -> Terminate {
    let order_id = id(order);
    Terminate {
        decision_id: id(decision),
        order_id,
        evaluated: kernel.operation_snapshot(order_id).expect("known order"),
        evaluation: closure([true; 5]),
        authority: human(40),
        rule_hash: Hash32::from_bytes([6; 32]),
    }
}

/// Reserve and authorize one send so the order is on the absence path.
pub fn open_unknown(kernel: &mut Kernel) -> Reserve {
    let request = reserve(3, 1, 1);
    kernel.reserve(ctx(1), request.clone()).unwrap();
    kernel
        .mark_payment_unknown(ctx(2), request.order_id)
        .unwrap();
    request
}
