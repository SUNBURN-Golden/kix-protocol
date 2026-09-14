"""S06.1 checked asset inputs and the explicit one-way legacy KRW seam.

RegistryContext is caller-approved fixture/configuration, NOT an authenticated
registry, token oracle, credential, observation or execution authorization. Its
version, source, domain and full asset specs are immutable input bindings. A
future store must persist AssetAmount.to_record(), or persist the same trusted
context alongside the compact {assetId, atoms} wire value; that compact value
alone does not identify a registry revision. Full records include a CE1 digest
of the entire approved config, so unchanged header labels cannot hide changes
to unrelated approved assets. This digest conveys no external authenticity.

Counters are separate runtime types, never int aliases or money. Their decimal
string wire format is exact across JSON runtimes. These new counters do not
change the legacy Core's seconds-based fixture clock or integer commands.
LegacyKRWAdapter only exports one checked KRW field; it cannot dispatch, sign,
authenticate a source, turn a calculation into evidence, or authorize execution.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import ClassVar

from assets import Amount, AssetSpec, KRW, MAX_ATOMS
from canonical_encoding import digest, machine_id
from common import require


_UINT = re.compile(r"(?:0|[1-9][0-9]*)\Z")
EXECUTION_AMOUNT_SCHEMA = "kix:execution-amount:1"
REGISTRY_CONTEXT_HASH_DOMAIN = "kix:asset-registry-context:1"
LEGACY_CORE_DOMAIN = "kix:fixture:lifecycle:0.3"
LEGACY_KRW_LIMIT = 10**12
# Asset metadata and execution capacity are different checks. The approved KRW
# asset supports u128 atoms; the old Core accepts only <= 10**12 KRW per field.
LEGACY_KRW_SPEC = KRW


def _decimal_wire(value, maximum, code):
    require(type(value) is str and len(value) <= len(str(maximum))
            and _UINT.fullmatch(value), code)
    result = int(value)
    require(result <= maximum, code)
    return result


@dataclass(frozen=True, slots=True)
class _UnsignedCounter:
    value: int
    MAX: ClassVar[int]
    MIN: ClassVar[int] = 0
    BITS: ClassVar[int]

    def __post_init__(self):
        require(type(self.value) is int and self.MIN <= self.value <= self.MAX,
                "INVALID_" + type(self).__name__.upper())

    def to_wire(self):
        return str(self.value)

    @classmethod
    def from_wire(cls, value):
        return cls(_decimal_wire(value, cls.MAX, "INVALID_" + cls.__name__.upper() + "_WIRE"))


class TimestampMs(_UnsignedCounter):
    """Nonnegative Unix milliseconds, signed-64 storage range; not seconds."""
    __slots__ = ()
    BITS = 64
    MAX = 2**63 - 1


class Sequence(_UnsignedCounter):
    """Unsigned-64 event sequence; zero is the pre-event position."""
    __slots__ = ()
    BITS = 64
    MAX = 2**64 - 1


class Version(_UnsignedCounter):
    """Unsigned-32 optimistic version; zero is an uninitialized version."""
    __slots__ = ()
    BITS = 32
    MAX = 2**32 - 1


class Quantity(_UnsignedCounter):
    """Unsigned-32 count of units; zero does not mean a monetary zero."""
    __slots__ = ()
    BITS = 32
    MAX = 2**32 - 1


class Generation(_UnsignedCounter):
    """Unsigned-64 issuance/claim generation, including initial zero."""
    __slots__ = ()
    BITS = 64
    MAX = 2**64 - 1


class AdmissionEpoch(_UnsignedCounter):
    """Unsigned-64 admission revocation epoch; independent of generation."""
    __slots__ = ()
    BITS = 64
    MAX = 2**64 - 1


class DurationSeconds(_UnsignedCounter):
    """Unsigned-32 duration in seconds, never an absolute timestamp."""
    __slots__ = ()
    BITS = 32
    MAX = 2**32 - 1


class BasisPoints(_UnsignedCounter):
    """Rate in basis points, stored in 16 bits and bounded to 100 percent."""
    __slots__ = ()
    BITS = 16
    MAX = 10000


@dataclass(frozen=True, slots=True)
class RegistryContext:
    """Immutable, caller-approved config; constructing it grants no authority.

    Do not deserialize untrusted request metadata into this class and regard it
    as approval. Supply a separately selected fixture/config context to every
    parser. An actual authenticated registry/version policy remains future work.
    """
    asset_registry_version: Version
    source: str
    domain: str
    approved_assets: tuple[AssetSpec, ...]

    def __post_init__(self):
        require(type(self.asset_registry_version) is Version
                and self.asset_registry_version.value > 0,
                "INVALID_ASSET_REGISTRY_VERSION")
        machine_id(self.source)
        machine_id(self.domain)
        require(type(self.approved_assets) is tuple and bool(self.approved_assets),
                "APPROVED_ASSET_CONFIG_REQUIRED")
        ids = set()
        references = {}
        for spec in self.approved_assets:
            require(type(spec) is AssetSpec, "INVALID_APPROVED_ASSET")
            key = (spec.namespace, spec.reference)
            require(key not in references or references[key] == spec,
                    "APPROVED_ASSET_METADATA_CONFLICT")
            require(spec.asset_id not in ids, "DUPLICATE_APPROVED_ASSET")
            references[key] = spec
            ids.add(spec.asset_id)
        # A registry is a set of bindings: caller iteration order is not identity.
        object.__setattr__(self, "approved_assets",
                           tuple(sorted(self.approved_assets, key=lambda spec: spec.asset_id)))

    def resolve(self, asset_id):
        machine_id(asset_id)
        for spec in self.approved_assets:
            if spec.asset_id == asset_id:
                return spec
        require(False, "ASSET_NOT_APPROVED_IN_CONTEXT")

    def to_dict(self):
        """Audit/config export, never a parser for caller self-authorization."""
        return dict(assetRegistryVersion=self.asset_registry_version.to_wire(),
                    source=self.source, domain=self.domain,
                    assets=[spec.to_dict() for spec in self.approved_assets])

    @property
    def registry_hash(self):
        """Pin the complete sorted config; this digest is not an approval proof."""
        return digest(REGISTRY_CONTEXT_HASH_DOMAIN, self.to_dict())


@dataclass(frozen=True, slots=True)
class AssetAmount:
    """Money bound to a full approved spec and immutable registry context.

    No implicit number conversion exists. The compact wire value must be parsed
    with an explicit trusted RegistryContext; storage records also pin the full
    metadata, version, source, domain and complete approved-set digest, rejecting
    any different context even when only an unrelated asset binding changes.
    """
    asset_id: str
    atoms: int
    registry: RegistryContext

    def __post_init__(self):
        require(type(self.registry) is RegistryContext, "REGISTRY_CONTEXT_REQUIRED")
        spec = self.registry.resolve(self.asset_id)
        require(type(self.atoms) is int and 0 <= self.atoms <= spec.max_atoms,
                "INVALID_ASSET_AMOUNT")

    @property
    def asset(self):
        return self.registry.resolve(self.asset_id)

    def to_dict(self):
        return dict(assetId=self.asset_id, atoms=str(self.atoms))

    @classmethod
    def from_dict(cls, value, *, registry):
        require(type(registry) is RegistryContext, "REGISTRY_CONTEXT_REQUIRED")
        require(type(value) is dict and set(value) == {"assetId", "atoms"},
                "INVALID_EXECUTION_AMOUNT_WIRE")
        atoms = _decimal_wire(value["atoms"], MAX_ATOMS, "INVALID_EXECUTION_ATOMS_WIRE")
        return cls(value["assetId"], atoms, registry)

    @classmethod
    def from_amount(cls, value, *, registry):
        """Explicitly bind calculation money to config; this authorizes nothing."""
        require(type(value) is Amount, "CALCULATION_AMOUNT_REQUIRED")
        require(type(registry) is RegistryContext, "REGISTRY_CONTEXT_REQUIRED")
        require(registry.resolve(value.asset.asset_id) == value.asset,
                "APPROVED_ASSET_SPEC_MISMATCH")
        return cls(value.asset.asset_id, value.atoms, registry)

    def to_record(self):
        return dict(schemaVersion=EXECUTION_AMOUNT_SCHEMA,
                    assetRegistryVersion=self.registry.asset_registry_version.to_wire(),
                    source=self.registry.source, domain=self.registry.domain,
                    registryHash=self.registry.registry_hash,
                    asset=self.asset.to_dict(), amount=self.to_dict())

    @classmethod
    def from_record(cls, value, *, registry):
        require(type(registry) is RegistryContext, "REGISTRY_CONTEXT_REQUIRED")
        require(type(value) is dict and set(value) == {
            "schemaVersion", "assetRegistryVersion", "source", "domain", "registryHash", "asset", "amount"},
                "INVALID_EXECUTION_AMOUNT_RECORD")
        require(value["schemaVersion"] == EXECUTION_AMOUNT_SCHEMA,
                "UNSUPPORTED_EXECUTION_AMOUNT_SCHEMA")
        require(Version.from_wire(value["assetRegistryVersion"]) == registry.asset_registry_version,
                "ASSET_REGISTRY_VERSION_MISMATCH")
        require(value["source"] == registry.source, "ASSET_REGISTRY_SOURCE_MISMATCH")
        require(value["domain"] == registry.domain, "ASSET_REGISTRY_DOMAIN_MISMATCH")
        require(type(value["registryHash"]) is str and value["registryHash"] == registry.registry_hash,
                "ASSET_REGISTRY_CONFIG_MISMATCH")
        result = cls.from_dict(value["amount"], registry=registry)
        require(AssetSpec.from_dict(value["asset"]) == result.asset,
                "APPROVED_ASSET_SPEC_MISMATCH")
        return result


@dataclass(frozen=True, slots=True)
class LegacyKRWAdapter:
    """Opt-in, one-way primitive export for the unchanged legacy Core.

    The caller pins an approved configuration when constructing this adapter.
    Its enabled flag is an explicit compatibility choice, not a credential.
    No source envelope, actor, signature, execution receipt or observation is
    synthesized. Core.execute must still apply every original command, role,
    source, state and policy check. There is deliberately no reverse adapter.
    """
    approved_registry: RegistryContext
    enabled: bool = False

    def __post_init__(self):
        require(self.enabled is True, "LEGACY_KRW_ADAPTER_REQUIRES_OPT_IN")
        require(type(self.approved_registry) is RegistryContext, "REGISTRY_CONTEXT_REQUIRED")
        require(self.approved_registry.domain == LEGACY_CORE_DOMAIN,
                "LEGACY_KRW_DOMAIN_MISMATCH")
        require(self.approved_registry.resolve(LEGACY_KRW_SPEC.asset_id) == LEGACY_KRW_SPEC,
                "LEGACY_KRW_SPEC_NOT_APPROVED")

    def to_legacy_krw(self, amount):
        require(type(amount) is AssetAmount, "CHECKED_ASSET_AMOUNT_REQUIRED")
        require(amount.registry == self.approved_registry, "LEGACY_REGISTRY_CONTEXT_MISMATCH")
        require(amount.asset_id == LEGACY_KRW_SPEC.asset_id and amount.asset == LEGACY_KRW_SPEC,
                "LEGACY_KRW_ASSET_MISMATCH")
        require(0 <= amount.atoms <= LEGACY_KRW_LIMIT, "LEGACY_KRW_AMOUNT_OVERFLOW")
        return amount.atoms
