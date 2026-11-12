"""Fail-closed synthetic asset and policy authentication.

Hash binding (quoteHash / planHash / proposalHash) is calculation integrity,
not source authentication (kix-kernel README, "Hard boundaries": hash equality
is not source authentication). This registry is the local adapter-side
authentication step: an asset or policy document must be explicitly registered
by the caller before any economics operation may use it, and the presented
document must equal the registered one exactly. Nothing is inferred, defaulted
or fetched from an external service; registration is a fixture act, not a
production credential check.

Policy kinds are local registry vocabulary, not protocol commands:

- ``QUOTE_PRICING`` binds an opaque caller pricing document to a ``policyRef``.
  The reference model binds the reference; it does not interpret pricing
  semantics (product policy values stay UNDETERMINED / DECISION_REQUIRED).
- ``PRIMARY_FEE_BPS`` is the adopted settlement policy shape, validated by the
  unchanged settlement layer's own policy validator at registration.
- ``RESALE_SPLIT_BPS`` carries the caller's organizer/platform basis points for
  the resale face split (BRA option A mock boundary; no policy numbers here).
- ``REFUND_FROZEN_LINE_PRICE`` binds commerce's fixed frozen-line-price full
  reversal policy name; it carries no values.
"""
import copy

from assets import AssetSpec
from common import Rejected, ident
from mock_settlement import _policy as _settlement_policy

from reference.economics import EconomicsLocalError

POLICY_KINDS = {
    'QUOTE_PRICING': frozenset({'document'}),
    'PRIMARY_FEE_BPS': frozenset({'kind', 'fee_bps', 'residual_payee', 'fee_payee'}),
    'RESALE_SPLIT_BPS': frozenset({'organizer_bps', 'platform_bps'}),
    'REFUND_FROZEN_LINE_PRICE': frozenset(),
}


def _bps(value, label):
    if type(value) is not int or not 0 <= value <= 10000:
        raise EconomicsLocalError('POLICY_BPS_INVALID:' + label)
    return value


def _validate_policy(kind, document):
    """Exact-field, fail-closed validation of one caller policy document."""
    if kind not in POLICY_KINDS:
        raise EconomicsLocalError('POLICY_KIND_UNKNOWN')
    if type(document) is not dict or set(document) != set(POLICY_KINDS[kind]):
        raise EconomicsLocalError('POLICY_FIELDS_INVALID')
    if kind == 'QUOTE_PRICING':
        if type(document['document']) is not dict:
            raise EconomicsLocalError('POLICY_DOCUMENT_INVALID')
    elif kind == 'PRIMARY_FEE_BPS':
        # The settlement layer's own validator is the authority for this shape.
        try:
            _settlement_policy(document)
        except Exception as error:
            raise EconomicsLocalError('POLICY_SETTLEMENT_INVALID:' + str(error)) from None
    elif kind == 'RESALE_SPLIT_BPS':
        organizer = _bps(document['organizer_bps'], 'organizer_bps')
        platform = _bps(document['platform_bps'], 'platform_bps')
        if organizer + platform > 10000:
            raise EconomicsLocalError('POLICY_SPLIT_EXCEEDS_BASIS')
    return copy.deepcopy(document)


class AssetAuthentication:
    """One explicit registry of authenticated synthetic asset identities."""

    def __init__(self):
        self._assets = {}

    def register(self, asset):
        """Register one exact AssetSpec wire document; equal re-registration is
        idempotent, a different document under the same identity is refused."""
        try:
            spec = AssetSpec.from_dict(asset)
        except (Rejected, ValueError, TypeError, KeyError):
            raise EconomicsLocalError('ASSET_WIRE_INVALID') from None
        existing = self._assets.get(spec.asset_id)
        if existing is not None:
            if existing != spec:
                raise EconomicsLocalError('ASSET_BINDING_CONFLICT')
            return existing.to_dict()
        self._assets[spec.asset_id] = spec
        return spec.to_dict()

    def authenticate(self, asset):
        """Fail closed: an unregistered or altered asset is never usable."""
        try:
            spec = AssetSpec.from_dict(asset)
        except (Rejected, ValueError, TypeError, KeyError):
            raise EconomicsLocalError('ASSET_NOT_AUTHENTICATED') from None
        registered = self._assets.get(spec.asset_id)
        if registered is None or registered != spec:
            raise EconomicsLocalError('ASSET_NOT_AUTHENTICATED')
        return spec

    def view(self):
        return [spec.to_dict() for _, spec in sorted(self._assets.items())]


class PolicyAuthentication:
    """One explicit registry of authenticated caller policy documents."""

    def __init__(self):
        self._policies = {}

    def register(self, policy_ref, kind, document):
        ref = self._ident(policy_ref)
        frozen = _validate_policy(kind, document)
        existing = self._policies.get(ref)
        if existing is not None:
            if existing != (kind, frozen):
                raise EconomicsLocalError('POLICY_BINDING_CONFLICT')
            return copy.deepcopy(frozen)
        self._policies[ref] = (kind, frozen)
        return copy.deepcopy(frozen)

    def authenticate(self, policy_ref, kind):
        ref = self._ident(policy_ref)
        entry = self._policies.get(ref)
        if entry is None:
            raise EconomicsLocalError('POLICY_NOT_AUTHENTICATED')
        if entry[0] != kind:
            raise EconomicsLocalError('POLICY_KIND_MISMATCH')
        return copy.deepcopy(entry[1])

    def view(self):
        return {ref: {'kind': kind, 'document': copy.deepcopy(document)}
                for ref, (kind, document) in sorted(self._policies.items())}

    @staticmethod
    def _ident(value):
        try:
            return ident(value)
        except Rejected:
            raise EconomicsLocalError('POLICY_REF_INVALID') from None