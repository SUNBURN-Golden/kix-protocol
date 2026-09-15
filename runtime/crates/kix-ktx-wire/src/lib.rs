#![forbid(unsafe_code)]
//! Registered KTX replay schemas. These codecs authenticate no external input.
//! The pure kernel remains independent of serde, storage and this crate.

use kix_bcs1::{CodecError, decode_bcs_body, encode_bcs_body};
use kix_kernel::{
    AppliedReservation, CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel,
    KernelError, Limits, MAX_SEATS, ObservationOutcome, ProviderOperation, Rejection, Reserve,
    ReserveOutcome, SEMANTICS_VERSION, Selection,
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};
use serde::de::{Error as _, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer, Serialize};

pub mod registry;
pub use registry::{RegisteredSchema, decode_registered, encode_registered};

/// Persist fixed-width limits, never architecture-dependent `usize` values.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct WireLimits {
    pub commands: u32,
    pub orders: u32,
    pub observations: u32,
}

impl WireLimits {
    fn kernel(self) -> Result<Limits, KernelError> {
        Ok(Limits {
            commands: usize::try_from(self.commands)
                .map_err(|_| KernelError::InvalidConfiguration)?,
            orders: usize::try_from(self.orders).map_err(|_| KernelError::InvalidConfiguration)?,
            observations: usize::try_from(self.observations)
                .map_err(|_| KernelError::InvalidConfiguration)?,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum InventorySpec {
    Seats(Vec<u16>),
    GeneralAdmission(u32),
}

/// A log starts with exactly one immutable genesis; later restarts use it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenesisV1 {
    pub scope: KixId,
    pub fence: ExecutionFence,
    pub business_epoch: u64,
    pub inventory: InventorySpec,
    pub limits: WireLimits,
    pub semantics_version: u16,
}

impl GenesisV1 {
    pub fn kernel(&self) -> Result<Kernel, KernelError> {
        if self.semantics_version != SEMANTICS_VERSION {
            return Err(KernelError::UnsupportedSemantics);
        }
        let inventory = match &self.inventory {
            InventorySpec::Seats(lengths) => Inventory::seats(lengths)?,
            InventorySpec::GeneralAdmission(capacity) => Inventory::general_admission(*capacity)?,
        };
        Kernel::new(
            self.scope,
            self.fence,
            self.business_epoch,
            inventory,
            self.limits.kernel()?,
        )
    }
}

/// Variant order is part of wire schema 1/2/1. Never reorder in place.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Action {
    Reserve(Reserve),
    MarkPaymentUnknown(KixId),
    Expire(KixId),
    CancelScope(u64),
    ReplaceOwner(ExecutionFence),
    ObserveCapture(CaptureObservation),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommandV1 {
    pub ctx: Context,
    pub action: Action,
}

impl CommandV1 {
    /// Apply only at the ordered boundary. This return is not a durable ACK.
    pub fn apply(&self, kernel: &mut Kernel) -> CommandResult {
        match &self.action {
            Action::Reserve(request) => {
                CommandResult::Reserve(kernel.reserve(self.ctx, request.clone()))
            }
            Action::MarkPaymentUnknown(id) => {
                CommandResult::MarkPaymentUnknown(kernel.mark_payment_unknown(self.ctx, *id))
            }
            Action::Expire(id) => CommandResult::Expire(kernel.expire(self.ctx, *id)),
            Action::CancelScope(epoch) => {
                CommandResult::CancelScope(kernel.cancel_scope(self.ctx, *epoch))
            }
            Action::ReplaceOwner(fence) => {
                CommandResult::ReplaceOwner(kernel.replace_owner(self.ctx, *fence))
            }
            Action::ObserveCapture(observation) => {
                CommandResult::ObserveCapture(kernel.observe_capture(self.ctx, observation.clone()))
            }
        }
    }
}

/// Original typed application decision, including deterministic rejections.
/// Durable drivers can preserve this beside the command and compare replay.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CommandResult {
    Reserve(Result<AppliedReservation, KernelError>),
    MarkPaymentUnknown(Result<(), KernelError>),
    Expire(Result<bool, KernelError>),
    CancelScope(Result<(), KernelError>),
    ReplaceOwner(Result<(), KernelError>),
    ObserveCapture(Result<ObservationOutcome, KernelError>),
}

type WireFence = ([u8; 16], u64);
type WireOperation = ([u8; 16], [u8; 16], [u8; 16]);
type WireContext = (WireFence, u64, u16);
type WireCommandId = ([u8; 16], [u8; 16], [u8; 16]);

#[derive(Serialize, Deserialize)]
struct WireGenesis {
    scope: [u8; 16],
    fence: WireFence,
    business_epoch: u64,
    inventory: WireInventory,
    limits: (u32, u32, u32),
    semantics_version: u16,
}

#[derive(Serialize, Deserialize)]
enum WireInventory {
    Seats(BoundedSegments),
    GeneralAdmission(u32),
}

#[derive(Serialize)]
struct BoundedSegments(Vec<u16>);

impl<'de> Deserialize<'de> for BoundedSegments {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct SegmentsVisitor;
        impl<'de> Visitor<'de> for SegmentsVisitor {
            type Value = BoundedSegments;

            fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                formatter.write_str("at most 4096 fixed-width segment lengths")
            }

            fn visit_seq<A: SeqAccess<'de>>(self, mut seq: A) -> Result<Self::Value, A::Error> {
                let maximum = usize::from(MAX_SEATS);
                if seq.size_hint().is_some_and(|count| count > maximum) {
                    return Err(A::Error::custom("segment count exceeds schema limit"));
                }
                let mut values = Vec::with_capacity(seq.size_hint().unwrap_or(0).min(maximum));
                while let Some(value) = seq.next_element()? {
                    if values.len() == maximum {
                        return Err(A::Error::custom("segment count exceeds schema limit"));
                    }
                    values.push(value);
                }
                Ok(BoundedSegments(values))
            }
        }
        deserializer.deserialize_seq(SegmentsVisitor)
    }
}

#[derive(Serialize, Deserialize)]
struct WireAmount {
    asset_id: [u8; 32],
    atoms: u128,
    registry_version: u32,
    registry_hash: [u8; 32],
}

#[derive(Serialize, Deserialize)]
struct WireReserve {
    id: WireCommandId,
    order_id: [u8; 16],
    expected_business_epoch: u64,
    selection: WireSelection,
    amount: WireAmount,
    quote_hash: [u8; 32],
    policy_hash: [u8; 32],
    expires_at_ms: u64,
    payment: WireOperation,
}

#[derive(Serialize, Deserialize)]
enum WireSelection {
    Seats { first: u16, count: u16 },
    GeneralAdmission { count: u32 },
}

#[derive(Serialize, Deserialize)]
struct WireObservation {
    event_id: [u8; 16],
    operation: WireOperation,
    amount: WireAmount,
    evidence_hash: [u8; 32],
}

#[derive(Serialize, Deserialize)]
enum WireAction {
    Reserve(WireReserve),
    MarkPaymentUnknown([u8; 16]),
    Expire([u8; 16]),
    CancelScope(u64),
    ReplaceOwner(WireFence),
    ObserveCapture(WireObservation),
}

#[derive(Serialize, Deserialize)]
struct WireCommand {
    ctx: WireContext,
    action: WireAction,
}

#[derive(Serialize, Deserialize)]
enum WireReserveOutcome {
    Held([u8; 16]),
    Rejected(u8),
}

#[derive(Serialize, Deserialize)]
enum WireResult {
    Reserve(Result<(WireReserveOutcome, bool), u8>),
    MarkPaymentUnknown(Result<(), u8>),
    Expire(Result<bool, u8>),
    CancelScope(Result<(), u8>),
    ReplaceOwner(Result<(), u8>),
    ObserveCapture(Result<u8, u8>),
}

fn fence_to_wire(value: ExecutionFence) -> WireFence {
    (*value.owner.as_bytes(), value.generation)
}
fn fence_from_wire(value: WireFence) -> ExecutionFence {
    ExecutionFence {
        owner: KixId::from_bytes(value.0),
        generation: value.1,
    }
}
fn operation_to_wire(value: ProviderOperation) -> WireOperation {
    (
        *value.provider.as_bytes(),
        *value.account.as_bytes(),
        *value.operation.as_bytes(),
    )
}
fn operation_from_wire(value: WireOperation) -> ProviderOperation {
    ProviderOperation {
        provider: KixId::from_bytes(value.0),
        account: KixId::from_bytes(value.1),
        operation: KixId::from_bytes(value.2),
    }
}

impl From<AssetAmount> for WireAmount {
    fn from(value: AssetAmount) -> Self {
        Self {
            asset_id: *value.asset_id().as_bytes(),
            atoms: value.atoms(),
            registry_version: value.registry_version().get(),
            registry_hash: *value.registry_hash().as_bytes(),
        }
    }
}

impl TryFrom<WireAmount> for AssetAmount {
    type Error = CodecError;
    fn try_from(value: WireAmount) -> Result<Self, Self::Error> {
        // This preserves a previously validated claim; it does not authenticate
        // the registry or authorize this maximum for fresh external inputs.
        AssetAmount::checked(
            AssetId::from_bytes(value.asset_id),
            value.atoms,
            u128::MAX,
            RegistryVersion::new(value.registry_version).map_err(|_| CodecError::BodyDecode)?,
            Hash32::from_bytes(value.registry_hash),
        )
        .map_err(|_| CodecError::BodyDecode)
    }
}

impl From<&Reserve> for WireReserve {
    fn from(value: &Reserve) -> Self {
        Self {
            id: (
                *value.id.scope.as_bytes(),
                *value.id.principal.as_bytes(),
                *value.id.request.as_bytes(),
            ),
            order_id: *value.order_id.as_bytes(),
            expected_business_epoch: value.expected_business_epoch,
            selection: match value.selection {
                Selection::Seats { first, count } => WireSelection::Seats { first, count },
                Selection::GeneralAdmission { count } => WireSelection::GeneralAdmission { count },
            },
            amount: value.amount.into(),
            quote_hash: *value.quote_hash.as_bytes(),
            policy_hash: *value.policy_hash.as_bytes(),
            expires_at_ms: value.expires_at_ms,
            payment: operation_to_wire(value.payment),
        }
    }
}

impl TryFrom<WireReserve> for Reserve {
    type Error = CodecError;
    fn try_from(value: WireReserve) -> Result<Self, Self::Error> {
        Ok(Self {
            id: CommandId {
                scope: KixId::from_bytes(value.id.0),
                principal: KixId::from_bytes(value.id.1),
                request: KixId::from_bytes(value.id.2),
            },
            order_id: KixId::from_bytes(value.order_id),
            expected_business_epoch: value.expected_business_epoch,
            selection: match value.selection {
                WireSelection::Seats { first, count } => Selection::Seats { first, count },
                WireSelection::GeneralAdmission { count } => Selection::GeneralAdmission { count },
            },
            amount: value.amount.try_into()?,
            quote_hash: Hash32::from_bytes(value.quote_hash),
            policy_hash: Hash32::from_bytes(value.policy_hash),
            expires_at_ms: value.expires_at_ms,
            payment: operation_from_wire(value.payment),
        })
    }
}

impl GenesisV1 {
    fn encode_wire(&self) -> Result<Vec<u8>, CodecError> {
        // Validate before cloning/serializing a potentially large segment list.
        self.kernel().map_err(|_| CodecError::BodyEncode)?;
        let inventory = match &self.inventory {
            InventorySpec::Seats(lengths) => WireInventory::Seats(BoundedSegments(lengths.clone())),
            InventorySpec::GeneralAdmission(capacity) => WireInventory::GeneralAdmission(*capacity),
        };
        encode_bcs_body(&WireGenesis {
            scope: *self.scope.as_bytes(),
            fence: fence_to_wire(self.fence),
            business_epoch: self.business_epoch,
            inventory,
            limits: (
                self.limits.commands,
                self.limits.orders,
                self.limits.observations,
            ),
            semantics_version: self.semantics_version,
        })
    }

    fn decode_wire(bytes: &[u8]) -> Result<Self, CodecError> {
        // The outer body bound precedes BCS decoding. BoundedSegments also
        // rejects excessive declared counts before reserving element storage.
        let value: WireGenesis = decode_bcs_body(bytes)?;
        let inventory = match value.inventory {
            WireInventory::Seats(lengths) => InventorySpec::Seats(lengths.0),
            WireInventory::GeneralAdmission(capacity) => InventorySpec::GeneralAdmission(capacity),
        };
        let genesis = Self {
            scope: KixId::from_bytes(value.scope),
            fence: fence_from_wire(value.fence),
            business_epoch: value.business_epoch,
            inventory,
            limits: WireLimits {
                commands: value.limits.0,
                orders: value.limits.1,
                observations: value.limits.2,
            },
            semantics_version: value.semantics_version,
        };
        genesis.kernel().map_err(|_| CodecError::BodyDecode)?;
        Ok(genesis)
    }
}

impl CommandV1 {
    fn encode_wire(&self) -> Result<Vec<u8>, CodecError> {
        if self.ctx.semantics_version != SEMANTICS_VERSION {
            return Err(CodecError::BodyEncode);
        }
        let action = match &self.action {
            Action::Reserve(request) => WireAction::Reserve(request.into()),
            Action::MarkPaymentUnknown(id) => WireAction::MarkPaymentUnknown(*id.as_bytes()),
            Action::Expire(id) => WireAction::Expire(*id.as_bytes()),
            Action::CancelScope(epoch) => WireAction::CancelScope(*epoch),
            Action::ReplaceOwner(fence) => WireAction::ReplaceOwner(fence_to_wire(*fence)),
            Action::ObserveCapture(value) => WireAction::ObserveCapture(WireObservation {
                event_id: *value.event_id.as_bytes(),
                operation: operation_to_wire(value.operation),
                amount: value.amount.into(),
                evidence_hash: *value.evidence_hash.as_bytes(),
            }),
        };
        encode_bcs_body(&WireCommand {
            ctx: (
                fence_to_wire(self.ctx.fence),
                self.ctx.now_ms,
                self.ctx.semantics_version,
            ),
            action,
        })
    }

    fn decode_wire(bytes: &[u8]) -> Result<Self, CodecError> {
        let value: WireCommand = decode_bcs_body(bytes)?;
        if value.ctx.2 != SEMANTICS_VERSION {
            return Err(CodecError::BodyDecode);
        }
        let action = match value.action {
            WireAction::Reserve(request) => Action::Reserve(request.try_into()?),
            WireAction::MarkPaymentUnknown(id) => Action::MarkPaymentUnknown(KixId::from_bytes(id)),
            WireAction::Expire(id) => Action::Expire(KixId::from_bytes(id)),
            WireAction::CancelScope(epoch) => Action::CancelScope(epoch),
            WireAction::ReplaceOwner(fence) => Action::ReplaceOwner(fence_from_wire(fence)),
            WireAction::ObserveCapture(value) => Action::ObserveCapture(CaptureObservation {
                event_id: KixId::from_bytes(value.event_id),
                operation: operation_from_wire(value.operation),
                amount: value.amount.try_into()?,
                evidence_hash: Hash32::from_bytes(value.evidence_hash),
            }),
        };
        Ok(Self {
            ctx: Context {
                fence: fence_from_wire(value.ctx.0),
                now_ms: value.ctx.1,
                semantics_version: value.ctx.2,
            },
            action,
        })
    }
}

fn error_code(value: KernelError) -> u8 {
    match value {
        KernelError::InvalidConfiguration => 0,
        KernelError::UnsupportedSemantics => 1,
        KernelError::ExecutionFenced => 2,
        KernelError::ClockRegression => 3,
        KernelError::WrongScope => 4,
        KernelError::CommandConflict => 5,
        KernelError::Capacity => 6,
        KernelError::UnknownOrder => 7,
        KernelError::InvalidTransition => 8,
        KernelError::UnknownOperation => 9,
    }
}
fn decode_error(value: u8) -> Result<KernelError, CodecError> {
    match value {
        0 => Ok(KernelError::InvalidConfiguration),
        1 => Ok(KernelError::UnsupportedSemantics),
        2 => Ok(KernelError::ExecutionFenced),
        3 => Ok(KernelError::ClockRegression),
        4 => Ok(KernelError::WrongScope),
        5 => Ok(KernelError::CommandConflict),
        6 => Ok(KernelError::Capacity),
        7 => Ok(KernelError::UnknownOrder),
        8 => Ok(KernelError::InvalidTransition),
        9 => Ok(KernelError::UnknownOperation),
        _ => Err(CodecError::BodyDecode),
    }
}
fn decode_result<T>(value: Result<T, u8>) -> Result<Result<T, KernelError>, CodecError> {
    Ok(match value {
        Ok(value) => Ok(value),
        Err(code) => Err(decode_error(code)?),
    })
}
fn rejection_code(value: Rejection) -> u8 {
    match value {
        Rejection::InvalidRequest => 0,
        Rejection::BusinessFenced => 1,
        Rejection::Unavailable => 2,
        Rejection::OrderExists => 3,
        Rejection::OperationAlreadyBound => 4,
        Rejection::OperationQuarantined => 5,
    }
}
fn decode_rejection(value: u8) -> Result<Rejection, CodecError> {
    match value {
        0 => Ok(Rejection::InvalidRequest),
        1 => Ok(Rejection::BusinessFenced),
        2 => Ok(Rejection::Unavailable),
        3 => Ok(Rejection::OrderExists),
        4 => Ok(Rejection::OperationAlreadyBound),
        5 => Ok(Rejection::OperationQuarantined),
        _ => Err(CodecError::BodyDecode),
    }
}
fn observation_code(value: ObservationOutcome) -> u8 {
    match value {
        ObservationOutcome::PaymentConfirmed => 0,
        ObservationOutcome::ReturnRequired => 1,
        ObservationOutcome::Review => 2,
        ObservationOutcome::DuplicateEffect => 3,
        ObservationOutcome::Conflict => 4,
    }
}
fn decode_observation(value: u8) -> Result<ObservationOutcome, CodecError> {
    match value {
        0 => Ok(ObservationOutcome::PaymentConfirmed),
        1 => Ok(ObservationOutcome::ReturnRequired),
        2 => Ok(ObservationOutcome::Review),
        3 => Ok(ObservationOutcome::DuplicateEffect),
        4 => Ok(ObservationOutcome::Conflict),
        _ => Err(CodecError::BodyDecode),
    }
}

impl CommandResult {
    fn encode_wire(&self) -> Result<Vec<u8>, CodecError> {
        let wire = match self {
            Self::Reserve(result) => WireResult::Reserve(
                result
                    .map(|value| {
                        let original = match value.original {
                            ReserveOutcome::Held(id) => WireReserveOutcome::Held(*id.as_bytes()),
                            ReserveOutcome::Rejected(reason) => {
                                WireReserveOutcome::Rejected(rejection_code(reason))
                            }
                        };
                        (original, value.replayed)
                    })
                    .map_err(error_code),
            ),
            Self::MarkPaymentUnknown(result) => {
                WireResult::MarkPaymentUnknown(result.map_err(error_code))
            }
            Self::Expire(result) => WireResult::Expire(result.map_err(error_code)),
            Self::CancelScope(result) => WireResult::CancelScope(result.map_err(error_code)),
            Self::ReplaceOwner(result) => WireResult::ReplaceOwner(result.map_err(error_code)),
            Self::ObserveCapture(result) => {
                WireResult::ObserveCapture(result.map(observation_code).map_err(error_code))
            }
        };
        encode_bcs_body(&wire)
    }

    fn decode_wire(bytes: &[u8]) -> Result<Self, CodecError> {
        let wire: WireResult = decode_bcs_body(bytes)?;
        Ok(match wire {
            WireResult::Reserve(result) => Self::Reserve(match decode_result(result)? {
                Ok((original, replayed)) => Ok(AppliedReservation {
                    original: match original {
                        WireReserveOutcome::Held(id) => ReserveOutcome::Held(KixId::from_bytes(id)),
                        WireReserveOutcome::Rejected(reason) => {
                            ReserveOutcome::Rejected(decode_rejection(reason)?)
                        }
                    },
                    replayed,
                }),
                Err(error) => Err(error),
            }),
            WireResult::MarkPaymentUnknown(result) => {
                Self::MarkPaymentUnknown(decode_result(result)?)
            }
            WireResult::Expire(result) => Self::Expire(decode_result(result)?),
            WireResult::CancelScope(result) => Self::CancelScope(decode_result(result)?),
            WireResult::ReplaceOwner(result) => Self::ReplaceOwner(decode_result(result)?),
            WireResult::ObserveCapture(result) => {
                Self::ObserveCapture(match decode_result(result)? {
                    Ok(value) => Ok(decode_observation(value)?),
                    Err(error) => Err(error),
                })
            }
        })
    }
}
