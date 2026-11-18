"""Track K stage 5: durable transactions on the adopted local backend.

Backend: local, non-production PostgreSQL 17.11 (Debian 17.11-0+deb13u1), single
process, single writer, default off (docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md §6).
This package is not protocol truth, not a production endpoint, not a replication
or storage engine, and not a production-conformance claim.
"""

PROTOCOL_TRUTH = False
PRODUCTION_CONFORMANCE = False
PRODUCTION_READINESS = False
PRODUCTION_ENDPOINT = False
FUNDS_EXECUTED = False
CHAIN_WRITER = False
FSM_DURABLE = False

PINNED_POSTGRES = 'PostgreSQL 17.11 (Debian 17.11-0+deb13u1)'
