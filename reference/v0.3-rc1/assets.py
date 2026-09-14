"""Exact asset amounts for new protocol contracts; no FX or legacy-ledger migration.

The fixture hash uses common.digest, not a production cross-language signing
standard. Callers must supply a fully qualified asset reference (including chain,
network and token type where relevant); ticker symbols are not asset identities.
"""
from dataclasses import dataclass
import re
import unicodedata

from common import digest, require


MAX_ATOMS = 2**128 - 1
_UINT = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_NAMESPACE = re.compile(r"[a-z][a-z0-9-]{0,62}\Z")


def _wire_integer(value, code):
    require(type(value) is str and len(value) <= 39 and _UINT.fullmatch(value), code)
    return int(value)


@dataclass(frozen=True)
class AssetSpec:
    namespace: str
    reference: str
    decimals: int
    max_atoms: int

    def __post_init__(self):
        require(type(self.namespace) is str and _NAMESPACE.fullmatch(self.namespace),
                "INVALID_ASSET_NAMESPACE")
        require(type(self.reference) is str and 0 < len(self.reference) <= 256,
                "INVALID_ASSET_REFERENCE")
        require(unicodedata.normalize("NFC", self.reference) == self.reference,
                "ASSET_REFERENCE_MUST_BE_NFC")
        require(all(not c.isspace() and not unicodedata.category(c).startswith("C")
                    for c in self.reference), "INVALID_ASSET_REFERENCE")
        require(len(self.reference.encode("utf-8")) <= 512, "INVALID_ASSET_REFERENCE")
        require(type(self.decimals) is int and 0 <= self.decimals <= 38,
                "INVALID_ASSET_DECIMALS")
        require(type(self.max_atoms) is int and 0 < self.max_atoms <= MAX_ATOMS,
                "INVALID_ASSET_LIMIT")

    @property
    def asset_id(self):
        return "asset-" + digest(["kix:asset:v1", self.to_dict()])

    def to_dict(self):
        return {"namespace": self.namespace, "reference": self.reference,
                "decimals": self.decimals, "maxAtoms": str(self.max_atoms)}

    @classmethod
    def from_dict(cls, value):
        require(type(value) is dict and
                set(value) == {"namespace", "reference", "decimals", "maxAtoms"},
                "INVALID_ASSET_WIRE")
        return cls(value["namespace"], value["reference"], value["decimals"],
                   _wire_integer(value["maxAtoms"], "INVALID_ASSET_LIMIT_WIRE"))


@dataclass(frozen=True)
class Amount:
    asset: AssetSpec
    atoms: int

    def __post_init__(self):
        require(type(self.asset) is AssetSpec, "INVALID_AMOUNT_ASSET")
        require(type(self.atoms) is int and 0 <= self.atoms <= self.asset.max_atoms,
                "INVALID_ASSET_AMOUNT")

    def _same_asset(self, other):
        require(type(other) is Amount, "INVALID_AMOUNT_OPERAND")
        require(self.asset == other.asset, "ASSET_MISMATCH")

    def add(self, other):
        self._same_asset(other)
        require(self.atoms <= self.asset.max_atoms - other.atoms, "ASSET_AMOUNT_OVERFLOW")
        return Amount(self.asset, self.atoms + other.atoms)

    def sub(self, other):
        self._same_asset(other)
        require(self.atoms >= other.atoms, "ASSET_AMOUNT_UNDERFLOW")
        return Amount(self.asset, self.atoms - other.atoms)

    def __add__(self, other):
        return self.add(other)

    def __sub__(self, other):
        return self.sub(other)

    def to_dict(self):
        return {"asset": self.asset.to_dict(), "atoms": str(self.atoms)}

    @classmethod
    def from_dict(cls, value):
        require(type(value) is dict and set(value) == {"asset", "atoms"},
                "INVALID_AMOUNT_WIRE")
        return cls(AssetSpec.from_dict(value["asset"]),
                   _wire_integer(value["atoms"], "INVALID_AMOUNT_ATOMS_WIRE"))

    @classmethod
    def from_decimal(cls, asset, text):
        return from_decimal(asset, text)

    def decimal_string(self):
        """Exact minimal decimal representation; never a floating-point value."""
        if self.asset.decimals == 0:
            return str(self.atoms)
        scale = 10**self.asset.decimals
        whole, fraction = divmod(self.atoms, scale)
        if not fraction:
            return str(whole)
        return str(whole) + "." + str(fraction).zfill(self.asset.decimals).rstrip("0")


def from_decimal(asset, text):
    """Parse unsigned plain decimal text with no rounding or exponent notation.

    Fractional trailing zeroes are accepted within the declared precision. Extra
    fractional digits are rejected even when zero; callers cannot infer rounding.
    """
    require(type(asset) is AssetSpec, "INVALID_AMOUNT_ASSET")
    require(type(text) is str and 0 < len(text) <= 80 and _DECIMAL.fullmatch(text),
            "INVALID_DECIMAL_AMOUNT")
    whole, separator, fraction = text.partition(".")
    require(len(fraction) <= asset.decimals, "ASSET_PRECISION_EXCEEDED")
    atoms = int(whole) * 10**asset.decimals
    if separator:
        atoms += int(fraction) * 10**(asset.decimals - len(fraction))
    return Amount(asset, atoms)


class AssetRegistry:
    """Explicit metadata consistency check; not an authority or token oracle.

    Asset IDs bind the precision and limit. A registry additionally prevents the
    same qualified reference from silently being reinterpreted with new metadata.
    Production adapters still need an approved registry and versioning policy.
    """
    def __init__(self):
        self._specs = {}

    def register(self, asset):
        require(type(asset) is AssetSpec, "INVALID_REGISTRY_ASSET")
        key = (asset.namespace, asset.reference)
        existing = self._specs.get(key)
        require(existing is None or existing == asset, "ASSET_METADATA_CONFLICT")
        self._specs[key] = asset
        return asset

    def get(self, namespace, reference):
        require(type(namespace) is str and type(reference) is str,
                "INVALID_REGISTRY_REFERENCE")
        require((namespace, reference) in self._specs, "ASSET_NOT_REGISTERED")
        return self._specs[(namespace, reference)]


KRW = AssetSpec("fiat", "KRW", 0, MAX_ATOMS)
