"""Track K stage 7: authenticated, consistent export over the stage-5 local source.

Contract: runtime/AUTHENTICATED_EXPORT.md §§1-5 and ADR-0001 §9. Source: the
adopted local, non-production PostgreSQL 17.11 (Debian 17.11-0+deb13u1) of
stage 5 (docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md §6), composed
unchanged through durable/. This package is a local fixture boundary: it is
not protocol truth, not a production endpoint, not a registered manifest wire
schema, not a replication or storage engine, and not a production-conformance
claim. The signing scheme, trust root/registry and anti-rollback policy are
DECISION_REQUIRED · Astra; only the caller-keyed fixture HMAC boundary is
implemented here (onsale/tokens.py precedent). No Arrow/Parquet materialization
and no Polars/DuckDB semantics audit happen in this node.
"""

from durable import PINNED_POSTGRES

PROTOCOL_TRUTH = False
PRODUCTION_CONFORMANCE = False
PRODUCTION_READINESS = False
PRODUCTION_ENDPOINT = False
FUNDS_EXECUTED = False
CHAIN_WRITER = False
FSM_DURABLE = False

# Provenance label: everything in this package is a local fixture.
LOCAL_EXPORT_FIXTURE_ONLY = True

# Local fixture document labels, not registered wire names. A production
# manifest wire schema is DECISION_REQUIRED · Astra (contract §3 preamble).
EXPORT_SCHEMA_VERSION = 'kix-export-manifest-local/1'
SOURCE_SCHEMA_VERSION = 'durable-schema/1'
TYPE_MAPPING_VERSION = 'kix-local-export-types/1'

# Local fixture scope labels (not product policy values).
EXECUTION_PROFILE = 'local-fixture'
AUTHORITY_SCOPE = 'kix-local-stage5'
AUTHORITY_PLACEMENT_VERSION = 'adr-0001-local/1'
SHARD_ID = 'local-single'
CURSOR_KIND = 'table-keyset/1'
BOUNDARY_SEMANTICS = 'startExclusive-endInclusive'
ISOLATION_LEVEL = 'SERIALIZABLE READ ONLY'
CUT_DECISION_BOUNDARY = (
    'single-shard local snapshot; no cross-shard coordinator exists '
    '(BACKEND_ADOPTION_PROPOSAL_20261009.md §6); no global-atomicity claim'
)

FULL_SNAPSHOT = 'FULL_SNAPSHOT'
INCREMENTAL = 'INCREMENTAL'
MODES = (FULL_SNAPSHOT, INCREMENTAL)

__all__ = [
    'PINNED_POSTGRES', 'PROTOCOL_TRUTH', 'PRODUCTION_CONFORMANCE',
    'PRODUCTION_READINESS', 'PRODUCTION_ENDPOINT', 'FUNDS_EXECUTED',
    'CHAIN_WRITER', 'FSM_DURABLE', 'LOCAL_EXPORT_FIXTURE_ONLY',
    'EXPORT_SCHEMA_VERSION', 'SOURCE_SCHEMA_VERSION', 'TYPE_MAPPING_VERSION',
    'EXECUTION_PROFILE', 'AUTHORITY_SCOPE', 'AUTHORITY_PLACEMENT_VERSION',
    'SHARD_ID', 'CURSOR_KIND', 'BOUNDARY_SEMANTICS', 'ISOLATION_LEVEL',
    'CUT_DECISION_BOUNDARY',
    'FULL_SNAPSHOT', 'INCREMENTAL', 'MODES',
]
