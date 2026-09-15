#![forbid(unsafe_code)]
//! R2-A local persistence/replay harness. NOT a quorum-committed transaction service.
//!
//! Registered genesis and ordered commands are synchronized before application.
//! Results, reservations, dedupe and external intents are reconstructed by the
//! pinned kernel semantics. No provider is called and no production ACK is issued.
//! Corrupt/torn tails are rejected, never silently truncated. A complete-prefix
//! rollback cannot be detected without an independent checkpoint/quorum.

use std::fs::{File, OpenOptions, TryLockError};
use std::io::{self, Read, Seek, SeekFrom, Write};
use std::path::Path;

use kix_bcs1::canonical_hash_bytes;
use kix_kernel::Kernel;
use kix_ktx_wire::{CommandResult, CommandV1, GenesisV1, decode_registered, encode_registered};
use kix_types::Hash32;

const MAGIC: &[u8; 8] = b"KTXLOG1\0";
const FRAME_DOMAIN: &[u8] = b"KTX-LOCAL-FRAME-v1\0";
const FRAME_OVERHEAD: usize = 4 + 8 + 32 + 32;
const MAX_FRAME_PAYLOAD: usize = 16_384;

#[derive(Debug)]
pub enum JournalError {
    Io(io::Error),
    Locked,
    Corrupt(&'static str),
    Wire(String),
    InvalidGenesis,
    InvalidLimits,
    Capacity,
    ClockRegression,
    Poisoned,
}

impl From<io::Error> for JournalError {
    fn from(error: io::Error) -> Self {
        Self::Io(error)
    }
}

impl std::fmt::Display for JournalError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "local journal error: {self:?}")
    }
}

impl std::error::Error for JournalError {}

#[derive(Debug, Clone, Copy)]
pub struct LogLimits {
    pub max_entries: u64,
    pub max_bytes: u64,
}

impl LogLimits {
    fn validate(self) -> Result<(), JournalError> {
        if self.max_entries == 0 || self.max_bytes < 256 {
            return Err(JournalError::InvalidLimits);
        }
        Ok(())
    }
}

/// A local fsync result, explicitly distinct from ADR-0001's quorum ACK.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalReceipt {
    pub sequence: u64,
    pub entry_hash: Hash32,
    pub result: CommandResult,
}

pub struct LocalJournal {
    file: File,
    genesis: GenesisV1,
    kernel: Kernel,
    limits: LogLimits,
    sequence: u64,
    previous: Hash32,
    length: u64,
    admitted_time: u64,
    poisoned: bool,
}

fn lock(file: &File) -> Result<(), JournalError> {
    match file.try_lock() {
        Ok(()) => Ok(()),
        Err(TryLockError::WouldBlock) => Err(JournalError::Locked),
        Err(TryLockError::Error(error)) => Err(JournalError::Io(error)),
    }
}

fn digest(bytes: &[u8]) -> Hash32 {
    let mut domain_bytes = Vec::with_capacity(FRAME_DOMAIN.len() + bytes.len());
    domain_bytes.extend_from_slice(FRAME_DOMAIN);
    domain_bytes.extend_from_slice(bytes);
    canonical_hash_bytes(&domain_bytes)
}

fn frame(
    sequence: u64,
    previous: Hash32,
    payload: &[u8],
) -> Result<(Vec<u8>, Hash32), JournalError> {
    if payload.is_empty() || payload.len() > MAX_FRAME_PAYLOAD {
        return Err(JournalError::Corrupt("invalid frame payload length"));
    }
    let mut bytes = Vec::with_capacity(FRAME_OVERHEAD + payload.len());
    bytes.extend_from_slice(&(payload.len() as u32).to_le_bytes());
    bytes.extend_from_slice(&sequence.to_le_bytes());
    bytes.extend_from_slice(previous.as_bytes());
    bytes.extend_from_slice(payload);
    let hash = digest(&bytes);
    bytes.extend_from_slice(hash.as_bytes());
    Ok((bytes, hash))
}

fn read_frame(
    file: &mut File,
    remaining: u64,
    sequence: u64,
    previous: Hash32,
) -> Result<(Vec<u8>, Hash32, u64), JournalError> {
    if remaining < FRAME_OVERHEAD as u64 {
        return Err(JournalError::Corrupt("partial frame header"));
    }
    let mut header = [0_u8; 44];
    file.read_exact(&mut header)?;
    let length = u32::from_le_bytes(header[..4].try_into().unwrap()) as usize;
    if length == 0 || length > MAX_FRAME_PAYLOAD {
        return Err(JournalError::Corrupt("unbounded or empty payload"));
    }
    let total = (FRAME_OVERHEAD + length) as u64;
    if total > remaining {
        return Err(JournalError::Corrupt("partial frame payload"));
    }
    if u64::from_le_bytes(header[4..12].try_into().unwrap()) != sequence
        || &header[12..44] != previous.as_bytes()
    {
        return Err(JournalError::Corrupt("sequence or previous hash mismatch"));
    }
    let mut authenticated = Vec::with_capacity(header.len() + length);
    authenticated.extend_from_slice(&header);
    authenticated.resize(header.len() + length, 0);
    file.read_exact(&mut authenticated[header.len()..])?;
    let mut stored_hash = [0_u8; 32];
    file.read_exact(&mut stored_hash)?;
    let hash = digest(&authenticated);
    if hash.as_bytes() != &stored_hash {
        return Err(JournalError::Corrupt("frame checksum mismatch"));
    }
    Ok((authenticated[header.len()..].to_vec(), hash, total))
}

impl LocalJournal {
    /// Parent directory must already exist. Never overwrites an existing log.
    pub fn create(
        path: &Path,
        genesis: GenesisV1,
        limits: LogLimits,
    ) -> Result<Self, JournalError> {
        limits.validate()?;
        let kernel = genesis.kernel().map_err(|_| JournalError::InvalidGenesis)?;
        let payload =
            encode_registered(&genesis).map_err(|e| JournalError::Wire(format!("{e:?}")))?;
        let (bytes, previous) = frame(0, Hash32::from_bytes([0; 32]), &payload)?;
        let length = (MAGIC.len() + bytes.len()) as u64;
        if length > limits.max_bytes {
            return Err(JournalError::Capacity);
        }
        let mut file = OpenOptions::new()
            .read(true)
            .write(true)
            .create_new(true)
            .open(path)?;
        lock(&file)?;
        file.write_all(MAGIC)?;
        file.write_all(&bytes)?;
        file.sync_all()?;
        // Make creation of the directory entry durable, not only file contents.
        let parent = path
            .parent()
            .filter(|p| !p.as_os_str().is_empty())
            .unwrap_or(Path::new("."));
        File::open(parent)?.sync_all()?;
        Ok(Self {
            file,
            genesis,
            kernel,
            limits,
            sequence: 0,
            previous,
            length,
            admitted_time: 0,
            poisoned: false,
        })
    }

    /// Streaming replay with bounded frame allocation; no silent tail repair.
    pub fn open(path: &Path, limits: LogLimits) -> Result<Self, JournalError> {
        limits.validate()?;
        let mut file = OpenOptions::new().read(true).write(true).open(path)?;
        lock(&file)?;
        let length = file.metadata()?.len();
        if length > limits.max_bytes {
            return Err(JournalError::Capacity);
        }
        if length < (MAGIC.len() + FRAME_OVERHEAD) as u64 {
            return Err(JournalError::Corrupt("missing genesis"));
        }
        let mut magic = [0; 8];
        file.read_exact(&mut magic)?;
        if &magic != MAGIC {
            return Err(JournalError::Corrupt("log format mismatch"));
        }
        let (payload, mut previous, used) =
            read_frame(&mut file, length - 8, 0, Hash32::from_bytes([0; 32]))?;
        let genesis: GenesisV1 =
            decode_registered(&payload).map_err(|e| JournalError::Wire(format!("{e:?}")))?;
        let mut kernel = genesis.kernel().map_err(|_| JournalError::InvalidGenesis)?;
        let mut offset = 8 + used;
        let mut sequence = 0_u64;
        let mut admitted_time = 0;
        while offset < length {
            sequence = sequence.checked_add(1).ok_or(JournalError::Capacity)?;
            if sequence > limits.max_entries {
                return Err(JournalError::Capacity);
            }
            let (payload, hash, used) = read_frame(&mut file, length - offset, sequence, previous)?;
            let command: CommandV1 =
                decode_registered(&payload).map_err(|e| JournalError::Wire(format!("{e:?}")))?;
            if command.ctx.now_ms < admitted_time {
                return Err(JournalError::Corrupt("regressed ordered input time"));
            }
            admitted_time = command.ctx.now_ms;
            command.apply(&mut kernel);
            previous = hash;
            offset += used;
        }
        file.seek(SeekFrom::End(0))?;
        // A prior writer may have died after a complete write but before fsync.
        // Adopt that unacknowledged command only after resynchronizing storage.
        file.sync_all()?;
        let parent = path
            .parent()
            .filter(|p| !p.as_os_str().is_empty())
            .unwrap_or(Path::new("."));
        File::open(parent)?.sync_all()?;
        Ok(Self {
            file,
            genesis,
            kernel,
            limits,
            sequence,
            previous,
            length,
            admitted_time,
            poisoned: false,
        })
    }

    /// Appends and fsyncs BEFORE apply. A write/sync error poisons the handle:
    /// callers must recover the file before querying state or sending more work.
    /// A complete command may survive without its response; replay must handle it.
    pub fn execute(&mut self, command: CommandV1) -> Result<LocalReceipt, JournalError> {
        self.ready()?;
        if command.ctx.now_ms < self.admitted_time {
            return Err(JournalError::ClockRegression);
        }
        let payload =
            encode_registered(&command).map_err(|e| JournalError::Wire(format!("{e:?}")))?;
        let sequence = self.sequence.checked_add(1).ok_or(JournalError::Capacity)?;
        if sequence > self.limits.max_entries {
            return Err(JournalError::Capacity);
        }
        let (bytes, hash) = frame(sequence, self.previous, &payload)?;
        let length = self
            .length
            .checked_add(bytes.len() as u64)
            .ok_or(JournalError::Capacity)?;
        if length > self.limits.max_bytes {
            return Err(JournalError::Capacity);
        }
        // Keep it poisoned if I/O fails or apply panics after durable append.
        self.poisoned = true;
        self.file.write_all(&bytes)?;
        self.file.sync_all()?;
        let result = command.apply(&mut self.kernel);
        self.sequence = sequence;
        self.previous = hash;
        self.length = length;
        self.admitted_time = command.ctx.now_ms;
        self.poisoned = false;
        Ok(LocalReceipt {
            sequence,
            entry_hash: hash,
            result,
        })
    }

    fn ready(&self) -> Result<(), JournalError> {
        if self.poisoned {
            Err(JournalError::Poisoned)
        } else {
            Ok(())
        }
    }

    pub fn kernel(&self) -> Result<&Kernel, JournalError> {
        self.ready()?;
        Ok(&self.kernel)
    }

    pub fn genesis(&self) -> &GenesisV1 {
        &self.genesis
    }
    pub fn entry_count(&self) -> u64 {
        self.sequence
    }
}

#[cfg(all(test, target_os = "linux"))]
mod tests {
    use super::*;
    use kix_kernel::{Context, ExecutionFence, SEMANTICS_VERSION};
    use kix_ktx_wire::{Action, InventorySpec, WireLimits};
    use kix_types::KixId;

    #[test]
    fn failed_storage_write_poisons_queries_and_subsequent_commands() {
        let directory = std::env::temp_dir().join(format!(
            "ktx-io-error-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&directory).unwrap();
        let path = directory.join("journal");
        let fence = ExecutionFence {
            owner: KixId::from_bytes([1; 16]),
            generation: 1,
        };
        let genesis = GenesisV1 {
            scope: KixId::from_bytes([2; 16]),
            fence,
            business_epoch: 1,
            inventory: InventorySpec::GeneralAdmission(10),
            limits: WireLimits {
                commands: 100,
                orders: 100,
                observations: 100,
            },
            semantics_version: SEMANTICS_VERSION,
        };
        let limits = LogLimits {
            max_entries: 100,
            max_bytes: 100_000,
        };
        let mut journal = LocalJournal::create(&path, genesis, limits).unwrap();
        let original = std::fs::read(&path).unwrap();
        // Test-only descriptor substitution produces ENOSPC without filling disk.
        journal.file = OpenOptions::new().write(true).open("/dev/full").unwrap();
        let command = CommandV1 {
            ctx: Context {
                fence,
                now_ms: 1,
                semantics_version: SEMANTICS_VERSION,
            },
            action: Action::CancelScope(2),
        };
        assert!(matches!(
            journal.execute(command.clone()),
            Err(JournalError::Io(_))
        ));
        assert!(matches!(journal.kernel(), Err(JournalError::Poisoned)));
        assert!(matches!(
            journal.execute(command),
            Err(JournalError::Poisoned)
        ));
        assert_eq!(std::fs::read(&path).unwrap(), original);
        drop(journal);
        let recovered = LocalJournal::open(&path, limits).unwrap();
        assert_eq!(recovered.entry_count(), 0);
        assert_eq!(recovered.kernel().unwrap().remaining(), 10);
        drop(recovered);
        std::fs::remove_dir_all(directory).unwrap();
    }
}
