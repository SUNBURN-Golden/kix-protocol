//! Actual local filesystem/process recovery tests. These establish neither
//! quorum commitment nor survival of host power loss or full-prefix rollback.

use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, MutexGuard};
use std::time::{Duration, Instant};

use kix_journal_local::{JournalError, LocalJournal, LogLimits};
use kix_kernel::{
    AppliedReservation, CaptureObservation, CommandId, Context, ExecutionFence, KernelError,
    ObservationOutcome, OrderState, ProviderOperation, Reserve, ReserveOutcome, SEMANTICS_VERSION,
    Selection,
};
use kix_ktx_wire::{Action, CommandResult, CommandV1, GenesisV1, InventorySpec, WireLimits};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

static DIRECTORY_ID: AtomicU64 = AtomicU64::new(0);
// A concurrent fork/exec can briefly inherit another test's locked file before
// CLOEXEC closes it, interfering with immediate drop/reopen assertions. Keep
// these process fixtures isolated; the explicit child lock test remains real.
static PROCESS_FIXTURE: Mutex<()> = Mutex::new(());

struct TestDirectory {
    directory: PathBuf,
    _fixture: MutexGuard<'static, ()>,
}

impl TestDirectory {
    fn new() -> Self {
        let fixture = PROCESS_FIXTURE.lock().unwrap();
        let directory = std::env::temp_dir().join(format!(
            "kix-journal-local-test-{}-{}",
            std::process::id(),
            DIRECTORY_ID.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&directory).unwrap();
        Self {
            directory,
            _fixture: fixture,
        }
    }

    fn path(&self, name: &str) -> PathBuf {
        self.directory.join(name)
    }
}

impl Drop for TestDirectory {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.directory);
    }
}

// Kill and reap helper processes even if the parent's assertions fail.
struct ChildGuard(Child);

impl Drop for ChildGuard {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}

fn id(value: u8) -> KixId {
    KixId::from_bytes([value; 16])
}

fn fence(generation: u64) -> ExecutionFence {
    ExecutionFence {
        owner: id(90),
        generation,
    }
}

fn context(now_ms: u64) -> Context {
    Context {
        fence: fence(1),
        now_ms,
        semantics_version: SEMANTICS_VERSION,
    }
}

fn limits() -> LogLimits {
    LogLimits {
        max_entries: 100,
        max_bytes: 1_000_000,
    }
}

fn genesis() -> GenesisV1 {
    GenesisV1 {
        scope: id(80),
        fence: fence(1),
        business_epoch: 1,
        inventory: InventorySpec::Seats(vec![70, 10]),
        limits: WireLimits {
            commands: 32,
            orders: 16,
            observations: 32,
        },
        semantics_version: SEMANTICS_VERSION,
    }
}

fn amount() -> AssetAmount {
    AssetAmount::checked(
        AssetId::from_bytes([10; 32]),
        1_000,
        u128::MAX,
        RegistryVersion::new(3).unwrap(),
        Hash32::from_bytes([11; 32]),
    )
    .unwrap()
}

fn reservation(number: u8, first: u16) -> Reserve {
    Reserve {
        id: CommandId {
            scope: id(80),
            principal: id(81),
            request: id(number),
        },
        order_id: id(number),
        expected_business_epoch: 1,
        selection: Selection::Seats { first, count: 2 },
        amount: amount(),
        quote_hash: Hash32::from_bytes([12; 32]),
        policy_hash: Hash32::from_bytes([13; 32]),
        expires_at_ms: 100,
        payment: ProviderOperation {
            provider: id(82),
            account: id(83),
            operation: id(number),
        },
    }
}

fn command(now_ms: u64, action: Action) -> CommandV1 {
    CommandV1 {
        ctx: context(now_ms),
        action,
    }
}

fn capture(request: &Reserve, event: u8) -> CaptureObservation {
    CaptureObservation {
        event_id: id(event),
        operation: request.payment,
        amount: request.amount,
        evidence_hash: Hash32::from_bytes([event; 32]),
    }
}

fn execute(journal: &mut LocalJournal, now_ms: u64, action: Action) -> CommandResult {
    journal.execute(command(now_ms, action)).unwrap().result
}

fn assert_reopens_identically(path: &Path, journal: LocalJournal) -> LocalJournal {
    let expected = journal.kernel().unwrap().clone();
    let genesis = journal.genesis().clone();
    let entries = journal.entry_count();
    drop(journal);
    let reopened = LocalJournal::open(path, limits()).unwrap();
    assert_eq!(reopened.kernel().unwrap(), &expected);
    assert_eq!(reopened.genesis(), &genesis);
    assert_eq!(reopened.entry_count(), entries);
    reopened
}

#[test]
fn complete_kernel_replays_from_genesis_and_ordered_commands() {
    let directory = TestDirectory::new();
    let path = directory.path("journal");
    let mut journal = LocalJournal::create(&path, genesis(), limits()).unwrap();
    let request = reservation(1, 63); // Spans bitmap words, within one segment.
    let first = execute(&mut journal, 1, Action::Reserve(request.clone()));
    assert_eq!(
        first,
        CommandResult::Reserve(Ok(AppliedReservation {
            original: ReserveOutcome::Held(id(1)),
            replayed: false,
        }))
    );
    assert_eq!(
        execute(&mut journal, 2, Action::MarkPaymentUnknown(id(1))),
        CommandResult::MarkPaymentUnknown(Ok(()))
    );
    let observation = capture(&request, 20);
    assert_eq!(
        execute(&mut journal, 3, Action::ObserveCapture(observation)),
        CommandResult::ObserveCapture(Ok(ObservationOutcome::PaymentConfirmed))
    );
    execute(&mut journal, 4, Action::ReplaceOwner(fence(2)));
    let mut journal = assert_reopens_identically(&path, journal);
    let mut retry = command(5, Action::Reserve(request));
    retry.ctx.fence = fence(2);
    assert_eq!(
        journal.execute(retry).unwrap().result,
        CommandResult::Reserve(Ok(AppliedReservation {
            original: ReserveOutcome::Held(id(1)),
            replayed: true,
        }))
    );
    assert_eq!(journal.kernel().unwrap().remaining(), 78);
    assert_eq!(journal.kernel().unwrap().order_count(), 1);
    assert_reopens_identically(&path, journal);
}

#[test]
fn unknown_payment_survives_restart_and_expiry_without_releasing_inventory() {
    let directory = TestDirectory::new();
    let path = directory.path("journal");
    let mut journal = LocalJournal::create(&path, genesis(), limits()).unwrap();
    execute(&mut journal, 1, Action::Reserve(reservation(1, 0)));
    execute(&mut journal, 2, Action::MarkPaymentUnknown(id(1)));
    let mut journal = assert_reopens_identically(&path, journal);
    assert_eq!(
        execute(&mut journal, 101, Action::Expire(id(1))),
        CommandResult::Expire(Ok(false))
    );
    assert_eq!(journal.kernel().unwrap().remaining(), 78);
    assert_eq!(
        journal.kernel().unwrap().order(id(1)).unwrap().state,
        OrderState::PaymentUnknown
    );
    assert_reopens_identically(&path, journal);
}

#[test]
fn replayed_late_capture_preserves_the_new_buyers_inventory() {
    let directory = TestDirectory::new();
    let path = directory.path("journal");
    let mut journal = LocalJournal::create(&path, genesis(), limits()).unwrap();
    let old_request = reservation(1, 0);
    execute(&mut journal, 1, Action::Reserve(old_request.clone()));
    assert_eq!(
        execute(&mut journal, 100, Action::Expire(id(1))),
        CommandResult::Expire(Ok(true))
    );
    let mut new_request = reservation(2, 0);
    new_request.expires_at_ms = 200;
    execute(&mut journal, 101, Action::Reserve(new_request));
    let mut journal = assert_reopens_identically(&path, journal);
    assert_eq!(
        execute(
            &mut journal,
            102,
            Action::ObserveCapture(capture(&old_request, 20))
        ),
        CommandResult::ObserveCapture(Ok(ObservationOutcome::ReturnRequired))
    );
    let journal = assert_reopens_identically(&path, journal);
    let old = journal.kernel().unwrap().order(id(1)).unwrap();
    let new = journal.kernel().unwrap().order(id(2)).unwrap();
    assert_eq!(old.state, OrderState::ReturnRequired);
    assert!(!old.inventory_owned);
    assert_eq!(old.captured, Some(amount()));
    assert_eq!(new.state, OrderState::Held);
    assert!(new.inventory_owned);
    assert_eq!(journal.kernel().unwrap().remaining(), 78);
}

#[test]
fn conflict_quarantine_original_evidence_and_send_rejection_survive_replay() {
    let directory = TestDirectory::new();
    let path = directory.path("journal");
    let mut journal = LocalJournal::create(&path, genesis(), limits()).unwrap();
    let first = reservation(1, 0);
    let second = reservation(2, 2);
    execute(&mut journal, 1, Action::Reserve(first.clone()));
    execute(&mut journal, 2, Action::Reserve(second.clone()));
    let original = capture(&first, 20);
    execute(&mut journal, 3, Action::ObserveCapture(original.clone()));
    let conflict = capture(&second, 20);
    assert_eq!(
        execute(&mut journal, 4, Action::ObserveCapture(conflict.clone())),
        CommandResult::ObserveCapture(Ok(ObservationOutcome::Conflict))
    );
    let mut journal = assert_reopens_identically(&path, journal);
    for number in [1, 2] {
        assert!(
            journal
                .kernel()
                .unwrap()
                .order(id(number))
                .unwrap()
                .review_required
        );
    }
    assert_eq!(journal.kernel().unwrap().conflicts(), &[conflict]);
    assert_eq!(
        execute(&mut journal, 5, Action::MarkPaymentUnknown(id(2))),
        CommandResult::MarkPaymentUnknown(Err(KernelError::InvalidTransition))
    );
    assert_eq!(
        execute(&mut journal, 6, Action::ObserveCapture(original)),
        CommandResult::ObserveCapture(Ok(ObservationOutcome::PaymentConfirmed))
    );
    // The original historical result remains available without clearing review.
    assert!(
        journal
            .kernel()
            .unwrap()
            .order(id(1))
            .unwrap()
            .review_required
    );
    assert_reopens_identically(&path, journal);
}

#[test]
fn a_second_process_cannot_open_the_active_writer_file() {
    let directory = TestDirectory::new();
    let path = directory.path("journal");
    let journal = LocalJournal::create(&path, genesis(), limits()).unwrap();
    let status = Command::new(std::env::current_exe().unwrap())
        .args(["--exact", "child_assert_writer_locked", "--ignored"])
        .env("KIX_JOURNAL_TEST_PATH", &path)
        .stdout(Stdio::null())
        .status()
        .unwrap();
    assert!(status.success());
    drop(journal);
    LocalJournal::open(&path, limits()).unwrap();
}

#[test]
#[ignore = "subprocess helper; invoked by a_second_process_cannot_open_the_active_writer_file"]
fn child_assert_writer_locked() {
    let path = PathBuf::from(std::env::var_os("KIX_JOURNAL_TEST_PATH").unwrap());
    assert!(matches!(
        LocalJournal::open(&path, limits()),
        Err(JournalError::Locked)
    ));
}

#[test]
fn process_killed_after_local_fsync_before_response_replays_the_original_result() {
    let directory = TestDirectory::new();
    let path = directory.path("journal");
    let marker = directory.path("fsynced-test-notification");
    let mut child = ChildGuard(
        Command::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "child_append_then_wait_before_response",
                "--ignored",
            ])
            .env("KIX_JOURNAL_TEST_PATH", &path)
            .env("KIX_JOURNAL_TEST_MARKER", &marker)
            .stdout(Stdio::null())
            .spawn()
            .unwrap(),
    );
    let deadline = Instant::now() + Duration::from_secs(10);
    while !marker.exists() {
        assert!(
            Instant::now() < deadline,
            "child failed to reach local fsync boundary"
        );
        assert!(
            child.0.try_wait().unwrap().is_none(),
            "child exited before notification"
        );
        std::thread::sleep(Duration::from_millis(10));
    }
    // Notification is test synchronization, not a transaction response. The
    // helper holds its journal and has not returned a result to a client.
    assert!(matches!(
        LocalJournal::open(&path, limits()),
        Err(JournalError::Locked)
    ));
    child.0.kill().unwrap();
    assert!(!child.0.wait().unwrap().success());
    let mut journal = LocalJournal::open(&path, limits()).unwrap();
    assert_eq!(journal.entry_count(), 1);
    assert_eq!(journal.kernel().unwrap().remaining(), 78);
    assert_eq!(
        execute(&mut journal, 2, Action::Reserve(reservation(1, 0))),
        CommandResult::Reserve(Ok(AppliedReservation {
            original: ReserveOutcome::Held(id(1)),
            replayed: true,
        }))
    );
    assert_eq!(journal.kernel().unwrap().remaining(), 78);
    assert_eq!(journal.kernel().unwrap().order_count(), 1);
    assert_reopens_identically(&path, journal);
}

#[test]
#[ignore = "subprocess helper; killed after fsync by the parent recovery test"]
fn child_append_then_wait_before_response() {
    let path = PathBuf::from(std::env::var_os("KIX_JOURNAL_TEST_PATH").unwrap());
    let marker = PathBuf::from(std::env::var_os("KIX_JOURNAL_TEST_MARKER").unwrap());
    let mut journal = LocalJournal::create(&path, genesis(), limits()).unwrap();
    let _unreturned_receipt = journal
        .execute(command(1, Action::Reserve(reservation(1, 0))))
        .unwrap();
    fs::write(marker, b"local fsync finished; no client response").unwrap();
    loop {
        std::thread::park();
    }
}

fn populated_bytes(directory: &TestDirectory) -> Vec<u8> {
    let path = directory.path("source");
    let mut journal = LocalJournal::create(&path, genesis(), limits()).unwrap();
    execute(&mut journal, 1, Action::Reserve(reservation(1, 0)));
    execute(&mut journal, 2, Action::MarkPaymentUnknown(id(1)));
    drop(journal);
    fs::read(path).unwrap()
}

// Tests parse only framing boundaries, independently of application codecs.
fn frame_ranges(bytes: &[u8]) -> Vec<std::ops::Range<usize>> {
    let mut ranges = Vec::new();
    let mut offset = 8;
    while offset < bytes.len() {
        let length = u32::from_le_bytes(bytes[offset..offset + 4].try_into().unwrap()) as usize;
        let end = offset + 76 + length;
        assert!(end <= bytes.len());
        ranges.push(offset..end);
        offset = end;
    }
    ranges
}

fn assert_rejected_without_repair(path: &Path, bytes: &[u8]) {
    fs::write(path, bytes).unwrap();
    assert!(matches!(
        LocalJournal::open(path, limits()),
        Err(JournalError::Corrupt(_))
    ));
    assert_eq!(
        fs::read(path).unwrap(),
        bytes,
        "open must never silently repair a corrupt tail"
    );
}

#[test]
fn every_partial_last_frame_is_rejected_without_silent_truncation() {
    let directory = TestDirectory::new();
    let bytes = populated_bytes(&directory);
    let last = frame_ranges(&bytes).pop().unwrap();
    let path = directory.path("damaged");
    for end in last.start + 1..last.end {
        assert_rejected_without_repair(&path, &bytes[..end]);
    }
    // A complete valid prefix is inherently indistinguishable from an older
    // valid log without an independent checkpoint. Do not claim rollback proof.
    fs::write(&path, &bytes[..last.start]).unwrap();
    assert_eq!(
        LocalJournal::open(&path, limits()).unwrap().entry_count(),
        1
    );
}

#[test]
fn corrupted_payload_checksum_sequence_and_previous_hash_are_rejected() {
    let directory = TestDirectory::new();
    let bytes = populated_bytes(&directory);
    let range = frame_ranges(&bytes)[1].clone();
    let path = directory.path("damaged");
    for index in [
        0,
        range.start + 4,
        range.start + 12,
        range.start + 44,
        range.end - 1,
    ] {
        let mut corrupted = bytes.clone();
        corrupted[index] ^= 1;
        assert_rejected_without_repair(&path, &corrupted);
    }
}

#[test]
fn reordered_and_duplicated_frames_are_rejected() {
    let directory = TestDirectory::new();
    let bytes = populated_bytes(&directory);
    let ranges = frame_ranges(&bytes);
    let path = directory.path("damaged");
    let mut reordered = bytes[..ranges[1].start].to_vec();
    reordered.extend_from_slice(&bytes[ranges[2].clone()]);
    reordered.extend_from_slice(&bytes[ranges[1].clone()]);
    assert_rejected_without_repair(&path, &reordered);
    let mut duplicated = bytes.clone();
    duplicated.extend_from_slice(&bytes[ranges[2].clone()]);
    assert_rejected_without_repair(&path, &duplicated);
}

#[test]
fn empty_and_oversized_declared_frames_are_rejected_before_payload_allocation() {
    let directory = TestDirectory::new();
    let bytes = populated_bytes(&directory);
    let offset = frame_ranges(&bytes)[1].start;
    let path = directory.path("damaged");
    for length in [0_u32, 16_385, u32::MAX] {
        let mut malformed = bytes.clone();
        malformed[offset..offset + 4].copy_from_slice(&length.to_le_bytes());
        assert_rejected_without_repair(&path, &malformed);
    }
}

#[test]
fn exhausted_entry_budget_does_not_modify_state_or_file() {
    let directory = TestDirectory::new();
    let path = directory.path("journal");
    let mut journal = LocalJournal::create(
        &path,
        genesis(),
        LogLimits {
            max_entries: 1,
            ..limits()
        },
    )
    .unwrap();
    execute(&mut journal, 1, Action::Reserve(reservation(1, 0)));
    let state = journal.kernel().unwrap().clone();
    let bytes = fs::read(&path).unwrap();
    assert!(matches!(
        journal.execute(command(2, Action::Reserve(reservation(2, 2)))),
        Err(JournalError::Capacity)
    ));
    assert_eq!(journal.kernel().unwrap(), &state);
    assert_eq!(journal.entry_count(), 1);
    assert_eq!(fs::read(&path).unwrap(), bytes);
    assert_reopens_identically(&path, journal);
}

#[test]
fn exhausted_byte_budget_does_not_modify_state_or_file() {
    let directory = TestDirectory::new();
    let source = populated_bytes(&directory);
    let ranges = frame_ranges(&source);
    let path = directory.path("journal");
    let budget = LogLimits {
        max_bytes: ranges[1].end as u64,
        ..limits()
    };
    let mut journal = LocalJournal::create(&path, genesis(), budget).unwrap();
    execute(&mut journal, 1, Action::Reserve(reservation(1, 0)));
    let state = journal.kernel().unwrap().clone();
    let bytes = fs::read(&path).unwrap();
    assert_eq!(bytes.len() as u64, budget.max_bytes);
    assert!(matches!(
        journal.execute(command(2, Action::MarkPaymentUnknown(id(1)))),
        Err(JournalError::Capacity)
    ));
    assert_eq!(journal.kernel().unwrap(), &state);
    assert_eq!(journal.entry_count(), 1);
    assert_eq!(fs::read(&path).unwrap(), bytes);
    drop(journal);
    assert!(matches!(
        LocalJournal::open(
            &path,
            LogLimits {
                max_bytes: budget.max_bytes - 1,
                ..limits()
            }
        ),
        Err(JournalError::Capacity)
    ));
    LocalJournal::open(&path, budget).unwrap();
}

#[test]
fn ordered_driver_time_survives_rejected_kernel_command_and_restart() {
    let directory = TestDirectory::new();
    let path = directory.path("journal");
    let mut journal = LocalJournal::create(&path, genesis(), limits()).unwrap();
    assert_eq!(
        execute(&mut journal, 500, Action::Expire(id(99))),
        CommandResult::Expire(Err(KernelError::UnknownOrder))
    );
    let mut journal = assert_reopens_identically(&path, journal);
    let state = journal.kernel().unwrap().clone();
    let bytes = fs::read(&path).unwrap();
    assert!(matches!(
        journal.execute(command(300, Action::Reserve(reservation(1, 0)))),
        Err(JournalError::ClockRegression)
    ));
    assert_eq!(journal.kernel().unwrap(), &state);
    assert_eq!(fs::read(&path).unwrap(), bytes);
}
