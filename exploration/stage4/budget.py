"""Shared exploration fixtures. These numbers are not product policy."""

CPU_CORES = (0, 1)
TOTAL_RAM_CAP_BYTES = 512 * 1024 * 1024
TOTAL_DISK_CAP_BYTES = 256 * 1024 * 1024
FDB_PORT = 4501
FDB_MEMORY = '384MiB'
FDB_STORAGE_MEMORY = '96MiB'
FDB_CACHE_MEMORY = '64MiB'
FDB_VERSION = '7.3.77'
FDB_API_VERSION = 730
POSTGRES_SHARED_BUFFERS = '64MB'

# Same admission fixtures for every candidate. Not approved limits.
DEFAULT_BUDGET = {
    'max_entries': 32,
    'max_bytes': 1_000_000,
    'observation_budget': 8,
}
SATURATION_BUDGET = {
    'max_entries': 3,
    'max_bytes': 1_000_000,
    'observation_budget': 8,
}

SETTINGS = {
    'warmup_calls': 2,
    'repeats': 1,
    'arrival_rate_per_s': 0,
    'concurrency': 1,
    'p99_method': 'nearest_rank_ceil',
    'rate_zero_means': 'scheduled_latency_equals_service_time',
    'label': 'exploration_data',
}

AMOUNT_FIXTURE = '10001'
U128_MAX = (1 << 128) - 1
SHOW_ID = 'synthetic-show'
LOCKED_BLOBS = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}
