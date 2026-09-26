"""Non-production loopback HTTP integration gate for the published local call.

This package is not a production endpoint, a public host, or a live payment,
KYC, venue, or bank adapter. Successful local HTTP calls are not production approval.
An optional process-local readiness journal replays committed receipts after
restart. That journal is not protocol truth and not a production-conformance claim.
"""
