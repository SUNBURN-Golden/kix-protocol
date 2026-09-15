//! Closed registration list for the KTX entry points. The list and trait
//! implementations share the same constants; a second identity declaration
//! cannot drift from a manually maintained documentation-only table.

use crate::{CommandResult, CommandV1, GenesisV1};
use kix_bcs1::{CodecError, KixBcsSchema, canonical_bytes, decode_canonical};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Registration {
    pub name: &'static str,
    pub domain_id: u16,
    pub schema_id: u16,
    pub schema_version: u16,
    pub max_body_bytes: usize,
    /// Normative field order and variant tag references are versioned with code.
    pub layout: &'static str,
}

pub const GENESIS_V1: Registration = Registration {
    name: "KtxGenesisV1",
    domain_id: 1,
    schema_id: 1,
    schema_version: 1,
    max_body_bytes: 8_320,
    layout: "scope:id16;fence:(owner:id16,generation:u64);business_epoch:u64;inventory:enum[0=Seats(vec<u16>,max4096,total<=4096),1=GA(u32)];limits:(commands:u32,orders:u32,observations:u32);semantics_version:u16",
};

pub const COMMAND_V1: Registration = Registration {
    name: "KtxCommandV1",
    domain_id: 1,
    schema_id: 2,
    schema_version: 1,
    max_body_bytes: 512,
    layout: "context:(fence:(owner:id16,generation:u64),now_ms:u64,semantics_version:u16);action:enum[0=Reserve,1=MarkPaymentUnknown(id16),2=Expire(id16),3=CancelScope(u64),4=ReplaceOwner(fence),5=ObserveCapture];Reserve and ObserveCapture layouts in README.md",
};

pub const RESULT_V1: Registration = Registration {
    name: "KtxCommandResultV1",
    domain_id: 1,
    schema_id: 3,
    schema_version: 1,
    max_body_bytes: 128,
    layout: "action:enum[0=Reserve,1=MarkPaymentUnknown,2=Expire,3=CancelScope,4=ReplaceOwner,5=ObserveCapture];Result:enum[0=Ok(action-result),1=Err(stable_error:u8)];stable result/error codes in README.md",
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RegistryError {
    ZeroIdentity,
    ReservedIdentity,
    DuplicateIdentity,
    InvalidBodyLimit,
}

pub fn validate_registry(entries: &[Registration]) -> Result<(), RegistryError> {
    for (index, entry) in entries.iter().enumerate() {
        if entry.domain_id == 0 || entry.schema_id == 0 || entry.schema_version == 0 {
            return Err(RegistryError::ZeroIdentity);
        }
        if entry.domain_id == u16::MAX && entry.schema_id == u16::MAX {
            return Err(RegistryError::ReservedIdentity);
        }
        if entry.max_body_bytes == 0 || entry.max_body_bytes > u32::MAX as usize {
            return Err(RegistryError::InvalidBodyLimit);
        }
        if entries[..index].iter().any(|prior| {
            (prior.domain_id, prior.schema_id, prior.schema_version)
                == (entry.domain_id, entry.schema_id, entry.schema_version)
        }) {
            return Err(RegistryError::DuplicateIdentity);
        }
    }
    Ok(())
}

mod sealed {
    pub trait Sealed {}
}

/// Only this module can register a schema accepted by KTX production-shaped
/// entry points. The generic kix-bcs1 codec remains available for test schemas.
///
/// ```compile_fail
/// use kix_bcs1::{CodecError, KixBcsSchema};
/// use kix_ktx_wire::registry::{Registration, RegisteredSchema, GENESIS_V1};
/// struct Foreign;
/// impl KixBcsSchema for Foreign {
///     const DOMAIN_ID: u16 = 1;
///     const SCHEMA_ID: u16 = 1;
///     const SCHEMA_VERSION: u16 = 1;
///     const MAX_BODY_BYTES: usize = 1;
///     fn encode_body(&self) -> Result<Vec<u8>, CodecError> { Ok(vec![]) }
///     fn decode_body(_: &[u8]) -> Result<Self, CodecError> { Ok(Self) }
/// }
/// // The private sealed trait prevents registering a competing identity here.
/// impl RegisteredSchema for Foreign {
///     const REGISTRATION: Registration = GENESIS_V1;
/// }
/// ```
pub trait RegisteredSchema: KixBcsSchema + sealed::Sealed {
    const REGISTRATION: Registration;
}

pub fn encode_registered<T: RegisteredSchema>(value: &T) -> Result<Vec<u8>, CodecError> {
    canonical_bytes(value)
}

pub fn decode_registered<T: RegisteredSchema>(bytes: &[u8]) -> Result<T, CodecError> {
    decode_canonical(bytes)
}

macro_rules! register_schemas {
    ($(($ty:ty, $registration:ident)),+ $(,)?) => {
        pub const REGISTRY: &[Registration] = &[$($registration),+];
        $(
        impl sealed::Sealed for $ty {}
        impl RegisteredSchema for $ty {
            const REGISTRATION: Registration = $registration;
        }
        impl KixBcsSchema for $ty {
            const DOMAIN_ID: u16 = $registration.domain_id;
            const SCHEMA_ID: u16 = $registration.schema_id;
            const SCHEMA_VERSION: u16 = $registration.schema_version;
            const MAX_BODY_BYTES: usize = $registration.max_body_bytes;
            fn encode_body(&self) -> Result<Vec<u8>, CodecError> {
                let bytes = self.encode_wire()?;
                if bytes.len() > Self::MAX_BODY_BYTES {
                    return Err(CodecError::BodyTooLarge);
                }
                Ok(bytes)
            }
            fn decode_body(bytes: &[u8]) -> Result<Self, CodecError> {
                if bytes.len() > Self::MAX_BODY_BYTES {
                    return Err(CodecError::BodyTooLarge);
                }
                Self::decode_wire(bytes)
            }
        }
        )+
    };
}

register_schemas!(
    (GenesisV1, GENESIS_V1),
    (CommandV1, COMMAND_V1),
    (CommandResult, RESULT_V1),
);
