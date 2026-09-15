use kix_bcs1::{CodecError, KixBcsSchema, canonical_hash, decode_bcs_body};
use kix_kernel::{
    AppliedReservation, CaptureObservation, CommandId, Context, ExecutionFence, KernelError,
    ObservationOutcome, ProviderOperation, Rejection, Reserve, ReserveOutcome, Selection,
};
use kix_ktx_wire::{
    Action, CommandResult, CommandV1, GenesisV1, InventorySpec, WireLimits, decode_registered,
    encode_registered,
    registry::{self, RegisteredSchema, RegistryError},
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

// Independently constructed with Python struct.pack and hashlib from the field
// specification, not copied from the encoder under test.
const GENESIS_HEX: &str = "4b495831010001000100440101010101010101010101010101010102020202020202020202020202020202070000000000000003000000000000000002410004001000000008000000200000000100";
const GENESIS_HASH: &str = "2e3d2dd7b032ca8b351e8c36f604ce4228b38691598f5cd279f03fc5c6fd4986";
const COMMAND_HEX: &str = concat!(
    "4b495831010002000100bc020202020202020202020202020202020207000000000000006400000000000000010000",
    "010101010101010101010101010101010303030303030303030303030303030304040404040404040404040404040404",
    "050505050505050505050505050505050300000000000000003f000200",
    "0606060606060606060606060606060606060606060606060606060606060606100f0e0d0c0b0a09080706050403020109000000",
    "07070707070707070707070707070707070707070707070707070707070707070808080808080808080808080808080808080808080808080808080808080808",
    "09090909090909090909090909090909090909090909090909090909090909098813000000000000",
    "0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c"
);
const COMMAND_HASH: &str = "9ebb8eef9ce9a4e0a7187716ad308e46c5b986904a9079bb991c3bcb49d259b7";
const RESULT_HEX: &str = "4b495831010003000100140000000505050505050505050505050505050500";
const RESULT_HASH: &str = "1ae46454186abdfda06fd8d1696d32ea8b8ce41992e687682e4dbd25dbc95ef7";

fn id(byte: u8) -> KixId {
    KixId::from_bytes([byte; 16])
}
fn hash(byte: u8) -> Hash32 {
    Hash32::from_bytes([byte; 32])
}
fn unhex(value: &str) -> Vec<u8> {
    value
        .as_bytes()
        .as_chunks::<2>()
        .0
        .iter()
        .map(|pair| u8::from_str_radix(std::str::from_utf8(pair).unwrap(), 16).unwrap())
        .collect()
}
fn amount(atoms: u128) -> AssetAmount {
    AssetAmount::checked(
        AssetId::from_bytes([6; 32]),
        atoms,
        u128::MAX,
        RegistryVersion::new(9).unwrap(),
        hash(7),
    )
    .unwrap()
}
fn genesis() -> GenesisV1 {
    GenesisV1 {
        scope: id(1),
        fence: ExecutionFence {
            owner: id(2),
            generation: 7,
        },
        business_epoch: 3,
        inventory: InventorySpec::Seats(vec![65, 4]),
        limits: WireLimits {
            commands: 16,
            orders: 8,
            observations: 32,
        },
        semantics_version: 1,
    }
}
fn command() -> CommandV1 {
    CommandV1 {
        ctx: Context {
            fence: genesis().fence,
            now_ms: 100,
            semantics_version: 1,
        },
        action: Action::Reserve(Reserve {
            id: CommandId {
                scope: id(1),
                principal: id(3),
                request: id(4),
            },
            order_id: id(5),
            expected_business_epoch: 3,
            selection: Selection::Seats {
                first: 63,
                count: 2,
            },
            amount: amount(0x0102_0304_0506_0708_090a_0b0c_0d0e_0f10),
            quote_hash: hash(8),
            policy_hash: hash(9),
            expires_at_ms: 5_000,
            payment: ProviderOperation {
                provider: id(10),
                account: id(11),
                operation: id(12),
            },
        }),
    }
}
fn round_trip<T: RegisteredSchema + std::fmt::Debug + PartialEq>(value: &T) {
    assert_eq!(
        &decode_registered::<T>(&encode_registered(value).unwrap()).unwrap(),
        value
    );
}

#[test]
fn independently_calculated_genesis_command_and_result_vectors() {
    let initial = genesis();
    assert_eq!(encode_registered(&initial).unwrap(), unhex(GENESIS_HEX));
    assert_eq!(canonical_hash(&initial).unwrap().to_string(), GENESIS_HASH);
    round_trip(&initial);
    let input = command();
    assert_eq!(encode_registered(&input).unwrap(), unhex(COMMAND_HEX));
    assert_eq!(canonical_hash(&input).unwrap().to_string(), COMMAND_HASH);
    round_trip(&input);
    let result = input.apply(&mut initial.kernel().unwrap());
    assert_eq!(encode_registered(&result).unwrap(), unhex(RESULT_HEX));
    assert_eq!(canonical_hash(&result).unwrap().to_string(), RESULT_HASH);
    round_trip(&result);
}

#[test]
fn registry_is_bound_to_the_actual_schema_types_and_rejects_collisions() {
    assert_eq!(registry::validate_registry(registry::REGISTRY), Ok(()));
    assert_eq!(GenesisV1::DOMAIN_ID, registry::GENESIS_V1.domain_id);
    assert_eq!(GenesisV1::SCHEMA_ID, registry::GENESIS_V1.schema_id);
    assert_eq!(
        GenesisV1::SCHEMA_VERSION,
        registry::GENESIS_V1.schema_version
    );
    assert_eq!(
        GenesisV1::MAX_BODY_BYTES,
        registry::GENESIS_V1.max_body_bytes
    );
    assert_eq!(CommandV1::REGISTRATION, registry::COMMAND_V1);
    assert_eq!(CommandResult::REGISTRATION, registry::RESULT_V1);
    assert_eq!(
        registry::validate_registry(&[registry::GENESIS_V1, registry::GENESIS_V1]),
        Err(RegistryError::DuplicateIdentity)
    );
    for field in 0..3 {
        let mut invalid = registry::GENESIS_V1;
        match field {
            0 => invalid.domain_id = 0,
            1 => invalid.schema_id = 0,
            _ => invalid.schema_version = 0,
        }
        assert_eq!(
            registry::validate_registry(&[invalid]),
            Err(RegistryError::ZeroIdentity)
        );
    }
    let mut reserved = registry::GENESIS_V1;
    reserved.domain_id = u16::MAX;
    reserved.schema_id = u16::MAX;
    assert_eq!(
        registry::validate_registry(&[reserved]),
        Err(RegistryError::ReservedIdentity)
    );
    let mut unbounded = registry::GENESIS_V1;
    unbounded.max_body_bytes = 0;
    assert_eq!(
        registry::validate_registry(&[unbounded]),
        Err(RegistryError::InvalidBodyLimit)
    );
}

#[test]
fn every_action_preserves_context_and_fixed_width_payloads() {
    let original = command();
    let Action::Reserve(reserve) = &original.action else {
        unreachable!()
    };
    let actions = [
        original.action.clone(),
        Action::MarkPaymentUnknown(id(5)),
        Action::Expire(id(5)),
        Action::CancelScope(u64::MAX),
        Action::ReplaceOwner(ExecutionFence {
            owner: id(13),
            generation: u64::MAX,
        }),
        Action::ObserveCapture(CaptureObservation {
            event_id: id(14),
            operation: reserve.payment,
            amount: amount(u128::MAX),
            evidence_hash: hash(15),
        }),
    ];
    for action in actions {
        round_trip(&CommandV1 {
            ctx: original.ctx,
            action,
        });
    }
    for atoms in [0, (1_u128 << 63) - 1, 1_u128 << 63, 1_u128 << 64, u128::MAX] {
        let mut input = original.clone();
        let Action::Reserve(value) = &mut input.action else {
            unreachable!()
        };
        value.amount = amount(atoms);
        value.selection = Selection::GeneralAdmission { count: u32::MAX };
        round_trip(&input);
    }
}

#[test]
fn all_deterministic_error_and_result_codes_round_trip() {
    let errors = [
        KernelError::InvalidConfiguration,
        KernelError::UnsupportedSemantics,
        KernelError::ExecutionFenced,
        KernelError::ClockRegression,
        KernelError::WrongScope,
        KernelError::CommandConflict,
        KernelError::Capacity,
        KernelError::UnknownOrder,
        KernelError::InvalidTransition,
        KernelError::UnknownOperation,
    ];
    for error in errors {
        for value in [
            CommandResult::Reserve(Err(error)),
            CommandResult::MarkPaymentUnknown(Err(error)),
            CommandResult::Expire(Err(error)),
            CommandResult::CancelScope(Err(error)),
            CommandResult::ReplaceOwner(Err(error)),
            CommandResult::ObserveCapture(Err(error)),
        ] {
            round_trip(&value);
        }
    }
    for reason in [
        Rejection::InvalidRequest,
        Rejection::BusinessFenced,
        Rejection::Unavailable,
        Rejection::OrderExists,
        Rejection::OperationAlreadyBound,
        Rejection::OperationQuarantined,
    ] {
        round_trip(&CommandResult::Reserve(Ok(AppliedReservation {
            original: ReserveOutcome::Rejected(reason),
            replayed: true,
        })));
    }
    for outcome in [
        ObservationOutcome::PaymentConfirmed,
        ObservationOutcome::ReturnRequired,
        ObservationOutcome::Review,
        ObservationOutcome::DuplicateEffect,
        ObservationOutcome::Conflict,
    ] {
        round_trip(&CommandResult::ObserveCapture(Ok(outcome)));
    }
    for result in [
        CommandResult::MarkPaymentUnknown(Ok(())),
        CommandResult::CancelScope(Ok(())),
        CommandResult::ReplaceOwner(Ok(())),
        CommandResult::Expire(Ok(true)),
        CommandResult::Expire(Ok(false)),
    ] {
        round_trip(&result);
    }
}

fn malformed<T: RegisteredSchema>(bytes: &[u8]) {
    for end in 0..bytes.len() {
        assert!(
            decode_registered::<T>(&bytes[..end]).is_err(),
            "accepted truncation {end}"
        );
    }
    for offset in [0, 4, 6, 8] {
        let mut bad = bytes.to_vec();
        bad[offset] ^= 0x80;
        assert!(decode_registered::<T>(&bad).is_err());
    }
    let mut trailing = bytes.to_vec();
    trailing.push(0);
    assert!(decode_registered::<T>(&trailing).is_err());
    assert_eq!(
        decode_registered::<T>(&vec![0; T::MAX_BODY_BYTES + 33]).err(),
        Some(CodecError::EnvelopeTooLarge)
    );
    assert!(T::decode_body(&vec![0; T::MAX_BODY_BYTES + 1]).is_err());
}

#[test]
fn truncations_wrong_identity_trailing_and_physical_size_are_rejected() {
    malformed::<GenesisV1>(&unhex(GENESIS_HEX));
    malformed::<CommandV1>(&unhex(COMMAND_HEX));
    malformed::<CommandResult>(&unhex(RESULT_HEX));
    assert!(decode_registered::<CommandV1>(&unhex(GENESIS_HEX)).is_err());
    assert!(decode_registered::<GenesisV1>(br#"{\"schema\":\"kix:commerce:2\"}"#).is_err());
}

#[test]
fn noncanonical_lengths_unknown_tags_and_invalid_registry_are_rejected() {
    let original = unhex(GENESIS_HEX);
    let mut nonminimal = original[..10].to_vec();
    nonminimal.extend([0xc4, 0]);
    nonminimal.extend_from_slice(&original[11..]);
    assert!(decode_registered::<GenesisV1>(&nonminimal).is_err());
    let mut overflow = original[..10].to_vec();
    overflow.extend([0xff, 0xff, 0xff, 0xff, 0x10]);
    assert!(decode_registered::<GenesisV1>(&overflow).is_err());
    let mut inner = original[11..].to_vec();
    inner.push(0);
    assert!(GenesisV1::decode_body(&inner).is_err());
    // Context is 34 bytes, then the action variant tag.
    let mut invalid_tag = unhex(COMMAND_HEX);
    invalid_tag[12 + 34] = 6;
    assert!(decode_registered::<CommandV1>(&invalid_tag).is_err());
    let mut zero_registry = unhex(COMMAND_HEX);
    zero_registry[12 + 160..12 + 164].fill(0);
    assert!(decode_registered::<CommandV1>(&zero_registry).is_err());
    // Invalid enum and stable code values must fail, never reinterpret.
    assert!(CommandResult::decode_body(&[6]).is_err());
    assert!(CommandResult::decode_body(&[1, 1, 10]).is_err());
    assert!(CommandResult::decode_body(&[5, 0, 5]).is_err());
    assert!(CommandResult::decode_body(&[0, 0, 1, 6, 0]).is_err());
    assert!(decode_bcs_body::<bool>(&[2]).is_err());
}

#[test]
fn genesis_validates_layout_limits_and_semantics_without_accepting_preoccupied_state() {
    let mut input = genesis();
    input.inventory = InventorySpec::Seats(vec![1; 4096]);
    round_trip(&input);
    input.inventory = InventorySpec::Seats(vec![1; 4097]);
    assert!(encode_registered(&input).is_err());
    input.inventory = InventorySpec::Seats(vec![0]);
    assert!(encode_registered(&input).is_err());
    input.inventory = InventorySpec::GeneralAdmission(u32::MAX);
    input.limits.commands = u32::MAX;
    round_trip(&input);
    input.limits.orders = 0;
    assert!(encode_registered(&input).is_err());
    let mut bad_genesis = unhex(GENESIS_HEX);
    let end = bad_genesis.len();
    bad_genesis[end - 2] = 2;
    assert!(decode_registered::<GenesisV1>(&bad_genesis).is_err());
    let mut bad_command = command();
    bad_command.ctx.semantics_version = 2;
    assert!(encode_registered(&bad_command).is_err());
    let mut bad_wire = unhex(COMMAND_HEX);
    bad_wire[12 + 32] = 2;
    assert!(decode_registered::<CommandV1>(&bad_wire).is_err());
    // Replace the genesis segment count with 4097 or 2^31-1. The bounded
    // sequence visitor rejects the declaration before reserving that capacity.
    let raw = unhex(GENESIS_HEX);
    for declared_length in [&[0x81, 0x20][..], &[0xff, 0xff, 0xff, 0xff, 0x07][..]] {
        let mut body = raw[11..11 + 49].to_vec();
        body.extend_from_slice(declared_length);
        body.extend_from_slice(&raw[11 + 50..]);
        assert!(GenesisV1::decode_body(&body).is_err());
    }
}

#[test]
fn wire_replay_retains_unbound_operation_quarantine_and_recorded_rejection() {
    let purchase = command();
    let Action::Reserve(request) = &purchase.action else {
        unreachable!()
    };
    let unknown_operation = ProviderOperation {
        operation: id(30),
        ..request.payment
    };
    let fact = CaptureObservation {
        event_id: id(31),
        operation: request.payment,
        amount: request.amount,
        evidence_hash: hash(32),
    };
    let conflict = CaptureObservation {
        operation: unknown_operation,
        evidence_hash: hash(33),
        ..fact.clone()
    };
    let mut attempted_rebind = request.clone();
    attempted_rebind.id.request = id(34);
    attempted_rebind.order_id = id(35);
    attempted_rebind.payment = unknown_operation;
    attempted_rebind.selection = Selection::Seats { first: 0, count: 1 };
    let inputs = [
        purchase.clone(),
        CommandV1 {
            ctx: purchase.ctx,
            action: Action::ObserveCapture(fact),
        },
        CommandV1 {
            ctx: purchase.ctx,
            action: Action::ObserveCapture(conflict),
        },
        CommandV1 {
            ctx: purchase.ctx,
            action: Action::Reserve(attempted_rebind),
        },
    ];
    let mut live = genesis().kernel().unwrap();
    let mut replay = decode_registered::<GenesisV1>(&unhex(GENESIS_HEX))
        .unwrap()
        .kernel()
        .unwrap();
    for input in &inputs {
        let expected = input.apply(&mut live);
        let recovered = decode_registered::<CommandV1>(&encode_registered(input).unwrap()).unwrap();
        assert_eq!(recovered.apply(&mut replay), expected);
    }
    assert_eq!(live, replay);
    assert_eq!(replay.conflicts().len(), 1);
    assert_eq!(
        inputs.last().unwrap().apply(&mut replay),
        CommandResult::Reserve(Ok(AppliedReservation {
            original: ReserveOutcome::Rejected(Rejection::OperationQuarantined),
            replayed: true,
        }))
    );
}

#[test]
fn ordered_wire_replay_recovers_original_result_intent_owner_and_late_capture() {
    let initial = genesis();
    let purchase = command();
    let Action::Reserve(request) = &purchase.action else {
        unreachable!()
    };
    let replacement = ExecutionFence {
        owner: id(20),
        generation: 8,
    };
    let current = Context {
        fence: replacement,
        now_ms: 200,
        semantics_version: 1,
    };
    let inputs = [
        purchase.clone(),
        CommandV1 {
            ctx: purchase.ctx,
            action: Action::ReplaceOwner(replacement),
        },
        CommandV1 {
            ctx: current,
            action: Action::MarkPaymentUnknown(request.order_id),
        },
        CommandV1 {
            ctx: current,
            action: Action::CancelScope(4),
        },
        CommandV1 {
            ctx: current,
            action: Action::ObserveCapture(CaptureObservation {
                event_id: id(21),
                operation: request.payment,
                amount: request.amount,
                evidence_hash: hash(22),
            }),
        },
    ];
    let mut live = initial.kernel().unwrap();
    let expected: Vec<_> = inputs.iter().map(|input| input.apply(&mut live)).collect();
    let decoded = decode_registered::<GenesisV1>(&encode_registered(&initial).unwrap()).unwrap();
    let mut replay = decoded.kernel().unwrap();
    for (input, expected) in inputs.iter().zip(expected) {
        let recovered = decode_registered::<CommandV1>(&encode_registered(input).unwrap()).unwrap();
        let decision = recovered.apply(&mut replay);
        assert_eq!(
            decision,
            decode_registered::<CommandResult>(&encode_registered(&expected).unwrap()).unwrap()
        );
    }
    assert_eq!(live, replay);
    let order = replay.order(request.order_id).unwrap();
    assert_eq!(order.request.payment, request.payment);
    assert_eq!(order.submitted_under, purchase.ctx.fence);
    assert_eq!(order.state, kix_kernel::OrderState::ReturnRequired);
    assert_eq!(replay.remaining(), 69);
    assert_eq!(
        purchase.apply(&mut replay),
        CommandResult::Reserve(Ok(AppliedReservation {
            original: ReserveOutcome::Held(request.order_id),
            replayed: true,
        }))
    );
}
