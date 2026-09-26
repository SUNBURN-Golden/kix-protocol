"""Run the non-production loopback integration gate."""
from __future__ import annotations

import sys

from integration_gate.server import main

if __name__ == '__main__':
    sys.exit(main())
