#!/usr/bin/env python3
"""Run the stage-4 local exploration and write raw samples.

The comparison answers belong in docs/DEVELOPMENT_PLAN.md §9.
This script does not rank candidates and does not adopt a backend.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exploration.stage4.run import main  # noqa: E402


if __name__ == '__main__':
    raise SystemExit(main())
