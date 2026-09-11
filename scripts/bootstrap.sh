#!/usr/bin/env bash
set -euo pipefail
KIX_REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KIX_REPO_ROOT"
python3 -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python 3.12 is required"'
node -e 'if (Number(process.versions.node.split(".")[0]) !== 24) throw Error("Node 24 is required")'
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check --timeout 20 --retries 1 -r requirements-dev.txt
npm --prefix reference/v0.3-rc1/client ci --ignore-scripts --no-audit --no-fund
python3 scripts/install_sui.py
python3 scripts/configure_local.py
source scripts/env.sh
python3 reference/v0.3-rc1/scripts/preflight.py
printf '%s\n' 'Runtime installed. In a new terminal: source scripts/env.sh' 'Build/tests: python scripts/verify_runtime.py' 'Local chain journey: python scripts/run_localnet.py'
