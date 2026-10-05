"""Test adapter for the current local wrapper, not a backend adoption."""

from readiness.boundary import FsmBoundary
from readiness.store import ReadinessFault, ReadinessStore


class LocalReadinessAdapter:
    fault_error = ReadinessFault

    @staticmethod
    def open_boundary(directory):
        return FsmBoundary(directory)

    @staticmethod
    def open_store(directory):
        return ReadinessStore.open(directory)
