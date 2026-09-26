#!/usr/bin/env python3
"""Fail if the integration-gate OpenAPI document drifts from the published contract."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration_gate.openapi_doc import main

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
