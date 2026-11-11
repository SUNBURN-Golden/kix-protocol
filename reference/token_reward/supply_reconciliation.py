"""Local synthetic supply calculations over the unchanged reference model."""

from reward_fixture import FixtureError, exact_fields, validate_json
from token_reward_model import PROVENANCE, reconcile_supply, supply_report


OPERATIONS = frozenset({"supply_report", "reconcile_supply"})
NOTICE = (
    "Synthetic inputs and results only. No mint, allocation, burn, chain query "
    "or payout control occurs. stop_payout is a reported model flag, not an "
    "executed action. Supply policy and operational responses remain "
    "UNDETERMINED — Astra/User."
)


def supply_output(operation, **fields):
    """Retain calculation scope on both results and diagnostics."""
    return {"operation": operation, "provenance": PROVENANCE,
            "evidence_class": "CALCULATION_ONLY", "notice": NOTICE, **fields}


def dispatch_request(request):
    """Validate only the JSON envelope; preserve model results and exceptions.

    Nested inputs are forwarded without repair, normalization or defaults.
    In particular reconciliation receives the caller's report itself.
    """
    validate_json(request)
    exact_fields(request, {"operation", "arguments"}, "request")
    operation = request["operation"]
    if type(operation) is not str or operation not in OPERATIONS:
        raise FixtureError("unsupported supply operation")
    arguments = request["arguments"]
    if operation == "supply_report":
        exact_fields(arguments, {"events"}, "arguments")
        result = supply_report(arguments["events"])
    else:
        exact_fields(arguments, {"offchain", "chain_supply"}, "arguments")
        result = reconcile_supply(arguments["offchain"], arguments["chain_supply"])
    return supply_output(operation, result=result)
