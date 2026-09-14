"""Test-only process-kill injector. Never part of the recovery decision API."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'reference/v0.3-rc1'))
from mock_provider import MockProvider
from paid_driver import main

point = sys.argv[1]
assert point in ('before','after')
submit = MockProvider.submit


def killed(self, *args, **kwargs):
    if point == 'after':
        submit(self, *args, **kwargs)
    os._exit(91)


with patch.object(MockProvider, 'submit', killed):
    raise SystemExit(main())
