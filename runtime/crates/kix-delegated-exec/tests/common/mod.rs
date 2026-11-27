#![allow(dead_code)]

use kix_delegated_exec::{
    DelegatedReserve, DelegatedShow, PageKind, PageSpec, RangeTable, ShowSelection,
};
use kix_kernel_v5::{Context, ExecutionFence, Limits, ProviderOperation, SEMANTICS_VERSION};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

pub fn id(n: u8) -> KixId {
    KixId::from_bytes([n; 16])
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

/// Issuer authority `id(1)` at delegation epoch 1: every page's starting fence.
pub fn ctx(now_ms: u64) -> Context {
    Context {
        fence: ExecutionFence {
            owner: id(1),
            generation: 1,
        },
        now_ms,
        semantics_version: SEMANTICS_VERSION,
    }
}

pub fn ctx_for(now_ms: u64, fence: ExecutionFence) -> Context {
    Context {
        fence,
        now_ms,
        semantics_version: SEMANTICS_VERSION,
    }
}

pub fn page(index: u32, start: u32, end: u32, kind: PageKind) -> PageSpec {
    PageSpec {
        index,
        start,
        end,
        kind,
    }
}

/// Show scope `id(9)`, issuer authority `id(1)`, page scopes `id(100 + index)`.
pub fn show(table: RangeTable) -> DelegatedShow {
    DelegatedShow::new(id(9), id(1), table, 1, limits(), |index| {
        KixId::from_bytes([index as u8 + 100; 16])
    })
    .unwrap()
}

pub fn reserve(n: u8, first: u32, count: u16) -> DelegatedReserve {
    DelegatedReserve {
        id: kix_kernel_v5::CommandId {
            scope: id(9),
            principal: id(2),
            request: id(n),
        },
        order_id: id(n),
        expected_business_epoch: 1,
        selection: ShowSelection::Seats { first, count },
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

pub fn ga_reserve(n: u8, count: u32) -> DelegatedReserve {
    DelegatedReserve {
        id: kix_kernel_v5::CommandId {
            scope: id(9),
            principal: id(2),
            request: id(n),
        },
        order_id: id(n),
        expected_business_epoch: 1,
        selection: ShowSelection::GeneralAdmission { count },
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
