# S05 local evidence

Base: PR #4 `f2a370dd55c29d7b3403e3872489bd965e38411e`.

- `python-default.log` and `python-system.log`: 142 tests passed in each runtime, including 19 new S05 checks. The source working directories are really removed and restore subprocesses are killed before/after installation. Chain inputs in unit tests are synthetic.
- `paid-archive.json`: two working-directory-loss traces with separate filesystem device IDs, archived original requests, independent live mock-provider observations and reconstructed obligations. Before-call restore stays held with no money execution permission. After-call cancellation retains 114,000 KRW recoverable and 120,000 KRW unpaid refund.
- `manifest.json`: exact source and evidence hashes plus runtime versions. Reproduce with `python scripts/verify_paid_archive.py --report .local/verification/paid-archive.json`.

No real money or private wallet material is included. The archive and provider used in these tests live in disposable `/dev/shm` directories; this proves survival of the original working-directory deletion, not host restart, power-loss durability or rollback resistance of the archive itself. Actual Sui + mock-money archive journeys and existing ZK gates are evaluated separately by the matching GitHub Actions run.
