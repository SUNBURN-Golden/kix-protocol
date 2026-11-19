"""Run every discovered booking test except the one prohibited socket test.

This is explicitly an offline subset, never evidence of full-suite success.
"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
BLOCKED = "test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit"


def prohibit_sockets(event, args):
    if event in {"socket.__new__", "socket.bind", "socket.connect", "socket.getaddrinfo"}:
        raise AssertionError("Sockets prohibited in this offline node: " + event)


def flatten(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten(test)
        else:
            yield test


def main():
    sys.addaudithook(prohibit_sockets)
    sys.path.insert(0, str(ROOT))
    directory = str(ROOT / "reference/booking_resale_admission")
    discovered = list(flatten(unittest.defaultTestLoader.discover(directory, top_level_dir=directory)))
    excluded = [test for test in discovered if test.id() == BLOCKED]
    if len(excluded) != 1:
        raise AssertionError(f"Expected exactly one blocked test, found {len(excluded)}")
    print("BLOCKED (socket test, not executed): " + BLOCKED, flush=True)
    selected = unittest.TestSuite(test for test in discovered if test.id() != BLOCKED)
    result = unittest.TextTestRunner().run(selected)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
