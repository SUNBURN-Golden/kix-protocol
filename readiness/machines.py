"""Public FSM restore targets wrapped by the local readiness boundary.

The set matches ReadinessStore.FSM_MACHINES. Adding a machine here without
the store allow-list, or the reverse, fails at import.
"""

from __future__ import annotations

import sys
from pathlib import Path

from readiness.ai_delegation_wrap import AiDelegationWrap
from readiness.store import FSM_MACHINES

ROOT = Path(__file__).resolve().parents[1]
_PATHS = (
    ROOT / 'reference' / 'settlement_f01_f03',
    ROOT / 'reference' / 'booking_resale_admission',
    ROOT / 'reference' / 'credit_advance_f04',
)
for _path in _PATHS:
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)

from admission_fsm import AdmissionMachine  # noqa: E402
from credit_fsm import CreditMachine  # noqa: E402
from reservation_fsm import ReservationMachine  # noqa: E402
from resale_fsm import ResaleMachine  # noqa: E402
from settlement_fsm import SettlementMachine  # noqa: E402

MACHINES = ('settlement', 'reservation', 'resale', 'credit', 'admission', 'ai_delegation')
RESTORE = {
    'settlement': SettlementMachine.restore,
    'reservation': ReservationMachine.restore,
    'resale': ResaleMachine.restore,
    'credit': CreditMachine.restore,
    'admission': AdmissionMachine.restore,
    'ai_delegation': AiDelegationWrap.restore,
}

if set(MACHINES) != FSM_MACHINES or set(RESTORE) != FSM_MACHINES:
    raise RuntimeError('MACHINE_SET')
