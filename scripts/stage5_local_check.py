#!/usr/bin/env python3
"""Run the stage-5 local durable-layer check and write host.json and summary.json.

Needs the local PostgreSQL 17.11 binaries and psycopg (see durable/run.py).
Local and non-production; it adopts nothing and ranks nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from durable.run import main  # noqa: E402


if __name__ == '__main__':
    raise SystemExit(main())
