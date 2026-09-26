"""Shared transport limits for the non-production integration gate."""

LOOPBACK_HOST = '127.0.0.1'
LOCAL_CALL_PATH = '/x-kix-contract-only/local-call'
HEALTH_PATH = '/health'
READY_PATH = '/ready'
GENERIC_OPERATION_ID = 'invokeLocalCall'
LIVE_HTTP_SERVER_MODE = 'non-production-local-integration'
MAX_BODY_BYTES = 65536
DEFAULT_TIMEOUT_SECONDS = 5.0
HEADER_LIMIT_BYTES = 8192
MAX_IN_FLIGHT = 8
MAX_JOURNAL_RECORDS = 4096
MAX_JOURNAL_BYTES = 8 * 1024 * 1024
TRACE_HEADER = 'X-Request-Id'
CORRELATION_HEADER = 'X-Correlation-Id'
COMMAND_COUNT = 40
PROTOCOL_CONTRACT = 'reference/v0.3-rc1/protocol_contract.json'
CONTRACT_ONLY_OPENAPI = 'docs/contracts/openapi/kix-protocol.contract-only.openapi.json'
INTEGRATION_GATE_OPENAPI = 'docs/contracts/openapi/kix-protocol.integration-gate.openapi.json'
