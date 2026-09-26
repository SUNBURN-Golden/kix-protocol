"""Local readiness runtime. Not protocol truth.

Protocol FSMs and the reference Core remain the semantic source. This package
journals their committed results for process restart in a controlled local
file. It is not a production endpoint, a public bind, a storage engine, or a
production-conformance claim.
"""

PROTOCOL_TRUTH = False
PRODUCTION_CONFORMANCE = False
PRODUCTION_ENDPOINT = False
