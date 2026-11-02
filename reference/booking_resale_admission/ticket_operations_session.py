"""Sequential synthetic resale/admission sessions over one private local graph."""

from admission_fixture import _validate_setup
from admission_fsm import AdmissionMachine
from admission_session import AdmissionSession
from presentation_source import PresentationSource
from reservation_fsm import ReservationMachine
from resale_fsm import ResaleMachine
from resale_offer_source import ResaleOfferSource
from resale_session import ResaleSession
# admission_fixture installs the existing sibling settlement reference path.
from settlement_fsm import SettlementMachine


class TicketOperationsSession:
    def __init__(self, *, setup: list, offer_source: ResaleOfferSource,
                 presentation_source: PresentationSource) -> None:
        """Execute caller-supplied allowlisted setup through public FSM methods.

        No clock, policy, issuance or settlement defaults are supplied. Structural
        validation precedes construction; domain setup failures propagate unchanged.
        Sessions are published only after setup succeeds. Discarding a failed
        private construction does not provide cross-machine rollback.
        """
        _validate_setup(setup)
        book = SettlementMachine()
        tickets = ReservationMachine(settlement_source=book)
        resale = ResaleMachine(ticket_source=tickets, settlement_source=book)
        admission = AdmissionMachine(ticket_source=tickets, ownership_source=resale,
                                     settlement_source=book)
        machines = {"settlement": book, "reservation": tickets,
                    "resale": resale, "admission": admission}
        for entry in setup:
            # _validate_setup enforces admission_fixture._SETUP's exact allowlist.
            method = getattr(machines[entry["machine"]], entry["operation"])
            method(entry["subject_id"], idempotency_key=entry["idempotency_key"], **entry["body"])
        self.resale = ResaleSession(resale, offer_source)
        self.admission = AdmissionSession(admission, presentation_source)
