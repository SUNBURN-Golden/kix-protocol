"""Separate count/byte/age budgets for new inflow and the service paths.

docs/DEVELOPMENT_PLAN.md §10 separates new inflow from completion, observation,
cancel and recovery. docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md §5 R1
and §7 allow stage 5 to use the names and caller-supplied slots only. Every
number is required from the caller; there is no default, no minimum and no
product meaning. Test fixtures live in test code and are labeled not-product.
"""

from __future__ import annotations

from dataclasses import dataclass

CLASSES = ('inflow', 'completion', 'observation', 'cancel', 'recovery')


class BudgetError(ValueError):
    pass


def _non_negative_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BudgetError('%s must be a non-negative integer supplied by the caller' % label)
    return value


@dataclass(frozen=True)
class ClassLimit:
    count: int
    bytes: int
    age_ms: int

    def __post_init__(self):
        _non_negative_int(self.count, 'count')
        _non_negative_int(self.bytes, 'bytes')
        _non_negative_int(self.age_ms, 'age_ms')

    def document(self):
        return {'age_ms': self.age_ms, 'bytes': self.bytes, 'count': self.count}


class BudgetSpec:
    """One ClassLimit per class. All five are required."""

    def __init__(self, *, inflow, completion, observation, cancel, recovery):
        self._limits = {}
        supplied = {
            'inflow': inflow, 'completion': completion, 'observation': observation,
            'cancel': cancel, 'recovery': recovery,
        }
        for name in CLASSES:
            limit = supplied[name]
            if not isinstance(limit, ClassLimit):
                raise BudgetError('%s needs a ClassLimit' % name)
            self._limits[name] = limit

    def limit(self, budget_class):
        try:
            return self._limits[budget_class]
        except KeyError:
            raise BudgetError('unknown budget class %r' % (budget_class,)) from None

    def document(self):
        return {name: self._limits[name].document() for name in CLASSES}

    def check(self, budget_class, *, used_count, used_bytes, oldest_open_ms,
              now_ms, extra_count=1, extra_bytes=0):
        """Return ('OK', None) or ('CAPACITY', 'count'|'bytes'|'age').

        count and bytes cover entries already retained plus the new entry.
        age is the dwell of the oldest still-open entry of this class against
        the caller-supplied now_ms. No wall clock is read here.
        """
        limit = self.limit(budget_class)
        if used_count + extra_count > limit.count:
            return 'CAPACITY', 'count'
        if used_bytes + extra_bytes > limit.bytes:
            return 'CAPACITY', 'bytes'
        if oldest_open_ms is not None and now_ms - oldest_open_ms > limit.age_ms:
            return 'CAPACITY', 'age'
        return 'OK', None
