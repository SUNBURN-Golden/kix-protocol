"""Fetch once and explicitly delegate one operation to a configured local FSM.

The source supplies command inputs only. All lifecycle checks and first-result
semantics remain with AdmissionMachine and its bound sources.
"""

from admission_fsm import AdmissionMachine
from mock_gates import GateError, _hex32, _ident, _ms, _version
from presentation_source import (
    AuthorizePresentationInput,
    ConsumePresentationInput,
    InvalidPresentationRecord,
    PresentationNotFound,
    PresentationOperation,
    PresentationSource,
    PresentationSourceError,
)


class PresentationAdapter:
    def __init__(self, machine: AdmissionMachine, source: PresentationSource) -> None:
        self._machine = machine
        self._source = source

    def _input(self, presentation_id: str, operation: PresentationOperation) -> dict:
        # Catch source faults only here: FSM exceptions must pass through unchanged.
        try:
            record = self._source.fetch(presentation_id, operation=operation)
        except PresentationSourceError:
            raise
        except Exception as error:
            raise PresentationSourceError("presentation fetch failed") from error
        if record is None:
            raise PresentationNotFound((operation, presentation_id))
        fields = (AuthorizePresentationInput if operation == "authorize_admission"
                  else ConsumePresentationInput).__required_keys__
        if type(record) is not dict or set(record) != fields:
            raise InvalidPresentationRecord("presentation must contain exactly the operation fields")
        try:
            _ident(presentation_id)
            _ident(record["right_id"])
            _version(record["version"])
            _hex32(record["request"], "ADMISSION_REQUEST")
            if operation == "authorize_admission":
                _ident(record["holder_role"])
        except GateError as error:
            raise InvalidPresentationRecord(error.code) from error
        return dict(record)

    @staticmethod
    def _caller(operation_id: str, idempotency_key: str, gate_role: str) -> None:
        try:
            _ident(operation_id)
            _ident(idempotency_key)
            _ident(gate_role)
        except GateError as error:
            raise InvalidPresentationRecord(error.code) from error

    def authorize_admission(
        self, presentation_id: str, *, admission_id: str, idempotency_key: str,
        gate_role: str, expires_ms: int,
    ) -> dict:
        record = self._input(presentation_id, "authorize_admission")
        self._caller(admission_id, idempotency_key, gate_role)
        try:
            _ms(expires_ms, "ADMISSION_WINDOW")
        except GateError as error:
            raise InvalidPresentationRecord(error.code) from error
        return self._machine.authorize_admission(
            admission_id, idempotency_key=idempotency_key, gate_role=gate_role,
            expires_ms=expires_ms, **record,
        )

    def consume(
        self, presentation_id: str, *, consume_id: str, idempotency_key: str,
        gate_role: str,
    ) -> dict:
        record = self._input(presentation_id, "consume")
        self._caller(consume_id, idempotency_key, gate_role)
        return self._machine.consume(
            consume_id, idempotency_key=idempotency_key, gate_role=gate_role, **record,
        )
