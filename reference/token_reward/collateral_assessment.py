"""Local synthetic assessment of the existing TK-12 collateral calculation."""

from reward_fixture import FixtureError, exact_fields, validate_json
from token_reward_model import PROVENANCE, collateral_recognized


OPERATION = "collateral_recognized"
NOTICE = (
    "Synthetic calculation only. No collateral adequacy, eligibility, loan or "
    "legal approval is determined. Asset selection and collateral ratios remain "
    "UNDETERMINED — Astra/User; legal enforceability remains "
    "UNDETERMINED — User/legal. No custody or F04 connection."
)


def assessment_output(**fields):
    """Use the same scope notice on results, rejections and cancellations."""
    return {"operation": OPERATION, "provenance": PROVENANCE,
            "evidence_class": "CALCULATION_ONLY", "notice": NOTICE, **fields}


def dispatch_request(request):
    """Validate the local envelope, then call the unchanged model exactly once.

    FixtureError denotes malformed local input. TokenRewardError (including its
    code and check precedence) comes directly from the model. No item fields or
    amounts are normalized, defaulted or removed here.
    """
    validate_json(request)
    exact_fields(request, {"operation", "arguments"}, "request")
    if type(request["operation"]) is not str or request["operation"] != OPERATION:
        raise FixtureError("unsupported assessment operation")
    arguments = request["arguments"]
    exact_fields(arguments, {"liability_krw", "collateral_items"}, "arguments")
    return assessment_output(result=collateral_recognized(**arguments))
