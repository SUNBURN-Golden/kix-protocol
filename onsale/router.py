"""Read-only GA routing on versioned hints (contract §3 and §6).

The router never writes and never decrements anything: effectiveRemaining is
a routing hint, and the authoritative shard check happens again inside the
AdmissionUnit commit. A shard carrying a valid negative hint (same epoch,
unexpired) is excluded; an expired or wrong-epoch hint is ignored, never a
permanent SOLD verdict. Two candidate strategies are provided for comparison
(capacity-aware and power-of-two choices); which one runs in production is
DECISION_REQUIRED · Astra (contract §10). The RNG is caller-supplied and
seeded by the caller; no wall clock and no global random state are read here.
"""

from __future__ import annotations

from onsale.model import hint_is_valid

STRATEGIES = ('capacity_aware', 'power_of_two')


class RouterError(ValueError):
    pass


class HintRouter:
    def __init__(self, strategy, rng):
        if strategy not in STRATEGIES:
            raise RouterError('strategy must be one of %s' % (STRATEGIES,))
        if not callable(getattr(rng, 'choice', None)) or not callable(getattr(rng, 'sample', None)):
            raise RouterError('rng must be a caller-supplied random.Random-like object')
        self.strategy = strategy
        self.rng = rng

    def candidates(self, observations, *, inventory_epoch, now_ms):
        """Shards with a positive effective hint and no valid negative hint."""
        usable = []
        for observation in observations:
            hint = observation.get('negativeHint')
            if hint is not None and hint_is_valid(hint, now_ms, inventory_epoch):
                continue
            if observation['effectiveRemaining'] > 0:
                usable.append(observation)
        return usable

    def route(self, observations, *, inventory_epoch, now_ms):
        """Return a shardId to attempt, or None when no shard is routable.

        None is a routing observation only: the caller may still present an
        existing token, and the commit-time check remains the authority.
        """
        usable = self.candidates(observations, inventory_epoch=inventory_epoch, now_ms=now_ms)
        if not usable:
            return None
        if self.strategy == 'capacity_aware':
            best = max(item['effectiveRemaining'] for item in usable)
            tied = sorted(
                (item for item in usable if item['effectiveRemaining'] == best),
                key=lambda item: item['shardId'],
            )
            return self.rng.choice(tied)['shardId']
        if len(usable) == 1:
            return usable[0]['shardId']
        first, second = self.rng.sample(usable, 2)
        winner = max(
            (first, second),
            key=lambda item: (item['effectiveRemaining'], item['shardId']),
        )
        return winner['shardId']


__all__ = ['STRATEGIES', 'HintRouter', 'RouterError']
