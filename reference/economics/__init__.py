"""Track K stage 6: economics as a reference model with synthetic money (R-10).

This package composes unchanged published layers into one explicit, sequential,
in-memory economics reference session:

- ``reference/v0.3-rc1`` commerce (``kix:commerce:2``) calculation contracts and
  the frozen lifecycle/finance Core;
- ``durable`` stage-5 pure admission decision and five-class budgets;
- ``reference/settlement_f01_f03`` settlement FSM under SET-POLICY-DRAFT-0.4
  (adopted rows L0, W0, R0, S0, T0, B5 REQUESTER, P0);
- ``reference/payment_effects`` four published effect commands;
- ``reference/booking_resale_admission`` resale FSM (``seller_due`` face).

It is an internal Python API only: no wire names, no catalogue entries, no new
protocol error codes. Every rate, cap, TTL and budget is caller-supplied
synthetic fixture input; nothing here defaults a product policy value. Missing
product policy values stay DECISION_REQUIRED · Astra; legal/tax/accounting and
provider-dependent values stay UNDETERMINED with their owners.

All execution flags are false. ``evidenceClass`` is ``SYNTHETIC_REFERENCE``.
This is not production readiness, not bank exactly-once, not chain finality,
not durable fencing and not a storage engine.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVIDENCE_CLASS = 'SYNTHETIC_REFERENCE'
PROVENANCE = 'synthetic'

# Every flag is false. localDurableData is false for the in-memory session;
# the optional stage-5 durable binding carries its own true flag per result.
FLAGS = {
    'protocolTruth': False,
    'productionConformance': False,
    'productionReadiness': False,
    'productionEndpoint': False,
    'fundsExecuted': False,
    'chainWriter': False,
    'fsmDurable': False,
    'localDurableData': False,
}


class EconomicsLocalError(ValueError):
    """A local reference-model refusal. Not a protocol/domain error code."""


def _bootstrap_frozen_paths():
    """Put the composed frozen layer directories on sys.path without copying.

    The directories carry disjoint module names (commerce/assets/common,
    mock_settlement/settlement_fsm, mock_gates/resale_fsm), so one shared
    sys.path is safe inside this package's processes.
    """
    for name in ('reference/v0.3-rc1',
                 'reference/settlement_f01_f03',
                 'reference/booking_resale_admission'):
        path = str(ROOT / name)
        if path not in sys.path:
            sys.path.insert(0, path)


_bootstrap_frozen_paths()

# Submodules import the constants above; define them before this import block.
from reference.economics import authentication  # noqa: E402
from reference.economics import quotes  # noqa: E402
from reference.economics import captures  # noqa: E402
from reference.economics import refunds  # noqa: E402
from reference.economics import payouts  # noqa: E402
from reference.economics import session  # noqa: E402

EconomicsSession = session.EconomicsSession
AssetAuthentication = authentication.AssetAuthentication
PolicyAuthentication = authentication.PolicyAuthentication
CaptureLedger = captures.CaptureLedger
DurableCaptureLedger = captures.DurableCaptureLedger

__all__ = [
    'EVIDENCE_CLASS', 'PROVENANCE', 'FLAGS', 'EconomicsLocalError',
    'EconomicsSession', 'AssetAuthentication', 'PolicyAuthentication',
    'CaptureLedger', 'DurableCaptureLedger',
    'authentication', 'quotes', 'captures', 'refunds', 'payouts', 'session',
]