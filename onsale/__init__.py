"""On-sale admission control: waiting room and GA routing on the stage-5 local backend.

Node k-onsale-admission-control. Contract: runtime/ONSALE_ADMISSION_CONTROL.md
(revision ONSALE-STAGE5-LOCAL-0.1). Backend: the adopted local, non-production
PostgreSQL 17.11 (Debian 17.11-0+deb13u1), single process, single writer,
default off (docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md §6). The
stage-5 durable/ layer is composed unchanged; this package adds no protocol
command, no public endpoint and no inventory authority of its own. It is not
protocol truth, not a production endpoint, not a replication or storage
engine, and not a production-conformance claim.
"""

from durable import PINNED_POSTGRES

PROTOCOL_TRUTH = False
PRODUCTION_CONFORMANCE = False
PRODUCTION_READINESS = False
PRODUCTION_ENDPOINT = False
FUNDS_EXECUTED = False
CHAIN_WRITER = False
DELEGATED_EXECUTION = False

# Provenance label: everything in this package is a local fixture.
LOCAL_ONSALE_FIXTURE_ONLY = True

REVISION = 'ONSALE-STAGE5-LOCAL-0.1'

__all__ = [
    'PINNED_POSTGRES', 'PROTOCOL_TRUTH', 'PRODUCTION_CONFORMANCE',
    'PRODUCTION_READINESS', 'PRODUCTION_ENDPOINT', 'FUNDS_EXECUTED',
    'CHAIN_WRITER', 'DELEGATED_EXECUTION', 'LOCAL_ONSALE_FIXTURE_ONLY',
    'REVISION',
]
