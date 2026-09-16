#!/usr/bin/env python3
"""Verify checked-in CE1 bytes/hashes and independent Python/TypeScript commerce.

Requires the repository-pinned Node 24 runtime; no npm install is needed.
This gate reads frozen expectations and never regenerates them.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'reference/v0.3-rc1'
sys.path.insert(0, str(REFERENCE))

from canonical_encoding import UNICODE_TABLE_SHA256, UNICODE_VERSION, VERSION
from commerce import SCHEMA
from test_canonical_encoding import FIXTURE, verify_golden_vectors


def run(node='node'):
    version = subprocess.run([node, '--version'], check=True, capture_output=True,
                             text=True, timeout=10).stdout.strip()
    if not version.startswith('v24.'):
        raise RuntimeError('Node 24 is required by toolchains.json; got ' + version)
    python_counts = verify_golden_vectors()
    result = subprocess.run([node, str(REFERENCE / 'client/verify_canonical.ts'), str(FIXTURE)],
                            check=True, capture_output=True, text=True, timeout=60)
    typescript = json.loads(result.stdout)
    if typescript.get('result') != 'PASS':
        raise AssertionError(typescript)
    return dict(format='kix-canonical-validation-v1', result='PASS',
                encodingVersion=VERSION, commerceSchema=SCHEMA,
                unicodeVersion=UNICODE_VERSION, unicodeTableSha256=UNICODE_TABLE_SHA256,
                fixtureSha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                pythonVersion=sys.version.split()[0], nodeVersion=version,
                python=python_counts, typescript=typescript,
                evidenceClass='CALCULATION_ONLY',
                actualPGCalls=0, actualChainCalls=0, ledgerMutations=0,
                limitations=['Fixtures validate CE1 and bounded calculation parity.',
                             'No signature, external payment evidence, execution permission or persistence is established.'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True)
    parser.add_argument('--node', default='node')
    args = parser.parse_args()
    result = run(args.node)
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n',
                      encoding='utf-8')
    print(json.dumps(dict(result='PASS', report=str(target),
                          encodingVersion=VERSION, commerceSchema=SCHEMA), sort_keys=True))


if __name__ == '__main__':
    main()
