#!/usr/bin/env python3
"""Fail if the TypeScript 0.x client drifts from the pinned contract-only OpenAPI."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / 'docs/contracts/openapi/kix-protocol.contract-only.openapi.json'
GATE_PATH = ROOT / 'docs/contracts/openapi/kix-protocol.integration-gate.openapi.json'
SOURCE_PATH = ROOT / 'reference/v0.3-rc1/protocol_contract.json'
GENERATOR = ROOT / 'sdk/generate/generate_client.mjs'
MANIFEST_GENERATOR = ROOT / 'sdk/generate/generate_manifest.mjs'
CATALOGUE_PATH = ROOT / 'sdk/generated/catalogue.ts'
PIN_PATH = ROOT / 'sdk/sdk-pin.json'
PROFILE_PATH = ROOT / 'sdk/compat/profiles/bootstrap-1.profile.json'
MANIFEST_PATH = ROOT / 'sdk/compat/manifests/manifest.bootstrap-1.json'
SIDECAR_PATH = ROOT / 'sdk/compat/manifests/manifest.bootstrap-1.json.sha256'
SOURCE_SHA256 = 'ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e'
SOURCE_BLOB = '619ae21c82ca3df5661bd3831613f15fa65225ff'
NODE = shutil.which('node')


def git_blob_id(data):
    header = b'blob ' + str(len(data)).encode('ascii') + b'\0'
    return hashlib.sha1(header + data).hexdigest()


def require_node():
    if NODE is None:
        print('node is not on PATH', file=sys.stderr)
        return None
    spec = json.loads((ROOT / 'toolchains.json').read_text(encoding='utf-8'))
    major = str(spec['nodeMajor'])
    proc = subprocess.run([NODE, '-p', 'process.versions.node'], cwd=ROOT, text=True, capture_output=True)
    version = proc.stdout.strip()
    if proc.returncode != 0 or not version.startswith(major + '.'):
        print('node %s does not match toolchains.json nodeMajor %s' % (version or proc.stderr.strip(), major), file=sys.stderr)
        return None
    return version


def run_generator(openapi, source, catalogue, pin):
    return subprocess.run(
        [NODE, str(GENERATOR), '--openapi', str(openapi), '--source', str(source), '--out', str(catalogue), '--pin', str(pin)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def regenerate(directory):
    catalogue = directory / 'catalogue.ts'
    pin = directory / 'sdk-pin.json'
    proc = run_generator(OPENAPI_PATH, SOURCE_PATH, catalogue, pin)
    if proc.returncode != 0:
        return proc, None
    manifest = subprocess.run(
        [NODE, str(MANIFEST_GENERATOR), '--out-root', str(directory)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return manifest, catalogue


def source_pin_errors():
    errors = []
    source = SOURCE_PATH.read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        errors.append('protocol_contract.json sha256 drift')
    if git_blob_id(source) != SOURCE_BLOB:
        errors.append('protocol_contract.json git blob drift')
    if not OPENAPI_PATH.is_file() or not GATE_PATH.is_file():
        errors.append('openapi pin file missing')
    return errors


def compare_outputs(directory):
    errors = source_pin_errors()
    proc, catalogue = regenerate(directory)
    if proc.returncode != 0:
        errors.append('generator failed: ' + (proc.stderr or proc.stdout).strip())
        return errors
    expected = {
        CATALOGUE_PATH: catalogue.read_bytes(),
        PIN_PATH: (directory / 'sdk-pin.json').read_bytes(),
        PROFILE_PATH: (directory / 'sdk/compat/profiles/bootstrap-1.profile.json').read_bytes(),
        MANIFEST_PATH: (directory / 'sdk/compat/manifests/manifest.bootstrap-1.json').read_bytes(),
        SIDECAR_PATH: (directory / 'sdk/compat/manifests/manifest.bootstrap-1.json.sha256').read_bytes(),
    }
    for path, actual in expected.items():
        if not path.is_file() or path.read_bytes() != actual:
            errors.append('byte drift: ' + str(path.relative_to(ROOT)))
    return errors


def expect_refusal(document, label):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'openapi.json'
        path.write_text(json.dumps(document), encoding='utf-8')
        proc = run_generator(path, SOURCE_PATH, Path(tmp) / 'catalogue.ts', Path(tmp) / 'pin.json')
        if proc.returncode == 0:
            print('self-test: ' + label + ' was accepted', file=sys.stderr)
            return 1
    return 0


def self_test():
    if require_node() is None:
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        errors = compare_outputs(Path(tmp))
        if errors:
            print('self-test: canonical outputs failed comparison', file=sys.stderr)
            for item in errors:
                print('- ' + item, file=sys.stderr)
            return 1
    document = json.loads(OPENAPI_PATH.read_text(encoding='utf-8'))
    broken = json.loads(json.dumps(document))
    broken['components']['schemas']['abort_effect'].pop('additionalProperties')
    if expect_refusal(broken, 'dropped additionalProperties'):
        return 1
    broken = json.loads(json.dumps(document))
    del broken['components']['schemas']['capture']
    if expect_refusal(broken, 'missing command'):
        return 1
    broken = json.loads(json.dumps(document))
    broken['servers'] = [{'url': 'https://example.invalid'}]
    if expect_refusal(broken, 'servers entry'):
        return 1
    broken = json.loads(json.dumps(document))
    broken['x-kix-live-http-server'] = True
    if expect_refusal(broken, 'live flag'):
        return 1
    broken = json.loads(json.dumps(document))
    broken['x-kix-source']['sha256'] = '0' * 64
    if expect_refusal(broken, 'source sha256 drift'):
        return 1
    print('self-test: pass')
    return 0


def write_outputs():
    if require_node() is None:
        return 1
    proc = run_generator(OPENAPI_PATH, SOURCE_PATH, CATALOGUE_PATH, PIN_PATH)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return proc.returncode
    manifest = subprocess.run([NODE, str(MANIFEST_GENERATOR)], cwd=ROOT, text=True, capture_output=True)
    if manifest.returncode != 0:
        print(manifest.stderr, file=sys.stderr)
        return manifest.returncode
    print('wrote sdk client, pin, and BOOTSTRAP manifest')
    return 0


def main(argv):
    if '--self-test' in argv:
        return self_test()
    if '--write' in argv:
        return write_outputs()
    version = require_node()
    if version is None:
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        errors = compare_outputs(Path(tmp))
    if errors:
        print('sdk client pin failed:', file=sys.stderr)
        for item in errors:
            print('- ' + item, file=sys.stderr)
        return 1
    print('sdk client pin ok: commands=40 node=%s sourceSha256=%s' % (version, SOURCE_SHA256))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
