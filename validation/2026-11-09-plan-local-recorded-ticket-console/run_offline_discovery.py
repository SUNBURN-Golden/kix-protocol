"""Protocol BRA discovery equivalent, partial: exclude the one socket test.

The builder's supervisor forbids network actions. This runner is evidence only;
it does not change repository CI discovery or label the excluded test a pass.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'reference/booking_resale_admission'
EXCLUDED = ('test_admission_fsm.AdmissionFsmTests.'
            'test_loopback_rejects_fsm_names_and_matches_published_admit')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


if __name__ == '__main__':
    found = list(cases(unittest.defaultTestLoader.discover(str(HERE), top_level_dir=str(HERE))))
    excluded = [case for case in found if case.id() == EXCLUDED]
    if len(excluded) != 1:
        raise SystemExit('Expected exactly one known loopback exclusion')
    print('PARTIAL discovery; excluded (not run): ' + EXCLUDED, flush=True)
    result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(
        case for case in found if case.id() != EXCLUDED))
    raise SystemExit(0 if result.wasSuccessful() else 1)
