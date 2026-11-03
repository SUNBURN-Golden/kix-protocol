"""Sequential synthetic booking/resale/admission sessions over one local graph."""

from admission_fixture import _validate_setup
from admission_fsm import AdmissionMachine
from admission_session import AdmissionSession
from booking_session import BookingSession
from presentation_source import PresentationSource
from reservation_fsm import ReservationMachine
from resale_fsm import ResaleMachine
from resale_offer_source import ResaleOfferSource
from resale_payment_source import ResalePaymentSource
from resale_session import ResaleSession
# admission_fixture installs the existing sibling settlement reference path.
from settlement_fsm import SettlementMachine


class TicketSettlementSession:
    """Explicit existing settlement operations on the shared ticket graph."""

    def __init__(self, machine: SettlementMachine) -> None:
        self._machine = machine

    def initiate(self, settlement_id, *, idempotency_key, trade_id, gross,
                 debtor_role, policy, currency):
        return self._machine.initiate(
            settlement_id, idempotency_key=idempotency_key, trade_id=trade_id,
            gross=gross, debtor_role=debtor_role, policy=policy, currency=currency)

    def authorize(self, settlement_id, *, idempotency_key):
        return self._machine.authorize(settlement_id, idempotency_key=idempotency_key)

    def capture(self, settlement_id, *, idempotency_key):
        return self._machine.capture(settlement_id, idempotency_key=idempotency_key)

    def commit(self, settlement_id, *, idempotency_key, movement_id, gross, amount,
               fee, tax, held, adjustment, adjustment_reason):
        return self._machine.commit(
            settlement_id, idempotency_key=idempotency_key, movement_id=movement_id,
            gross=gross, amount=amount, fee=fee, tax=tax, held=held,
            adjustment=adjustment, adjustment_reason=adjustment_reason)

    def view(self, settlement_id):
        return self._machine.view(settlement_id)


class TicketOperationsSession:
    def __init__(self, *, setup: list, offer_source: ResaleOfferSource,
                 presentation_source: PresentationSource,
                 payment_source: ResalePaymentSource | None = None) -> None:
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
        self.settlement = TicketSettlementSession(book)
        self.booking = BookingSession(tickets)
        self.resale = ResaleSession(resale, offer_source, payment_source=payment_source)
        self.admission = AdmissionSession(admission, presentation_source)
