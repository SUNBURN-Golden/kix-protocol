"""RS-4 L1: run one isolated, disposable Sui localnet under the 1,024-slot load workload.

Same disposable-localnet discipline as scripts/run_localnet_rights_scale_private.py:
a fresh one-validator genesis per run, only the subprocess started here is
terminated, no existing network is reset, all keys stay in ignored .local
folders. The workload is expanded deterministically from
reference/rights_scale/load_plan.py, executed by client/load-l1.mjs against the
published package (real chain transactions, real Groth16 proofs — setup:zk
artifacts required), then reduced by reference/rights_scale/summarize_load.py.

Usage:
    python3 scripts/run_rights_scale_l1_load.py <output-dir> [--shield-count N]

Writes <output-dir>/{host.json,manifest.json,load-scenarios.json,load-report.json,
receipt.json,public/,private/,delegated/} and the receipt
.local/verification/rights-scale-l1-load.json. Everything produced is
exploration data from a one-validator localnet: no SLO, no throughput or
production claims.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'reference/rights_scale'
OUTPUT_NAME = 'rights-scale-l1-load.json'
LOCKED = (
    'runtime/crates/kix-kernel/src/lib.rs',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs',
)


def git(*args):
    result = subprocess.run(['git', '-C', str(ROOT)] + list(args),
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


EPOCH_DURATION_MS = 21_600_000  # 6h: a 1,024-proof run must not be cut by epoch rotation


def host_facts():
    facts = {
        'machine': platform.machine(), 'system': platform.system(),
        'release': platform.release(), 'python': platform.python_version(),
        'cpu_count': os.cpu_count(),
        'exploration_data': True,
        'network': 'localnet-only (one validator, committee size 1)',
        'git_head': git('rev-parse', 'HEAD'),
        'git_origin_main': git('rev-parse', 'origin/main'),
        'git_branch': git('rev-parse', '--abbrev-ref', 'HEAD'),
    }
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):
                facts['cpu_model'] = line.split(':', 1)[1].strip()
                break
    except OSError:
        facts['cpu_model'] = None
    for path in LOCKED:
        facts['locked_blob:' + path] = git('hash-object', str(ROOT / path))
    for name, cmd in (('sui', ['sui', '--version']), ('node', ['node', '--version']),
                      ('npm', ['npm', '--version'])):
        try:
            facts[name + '_version'] = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            facts[name + '_version'] = None
    toolchains = ROOT / 'toolchains.json'
    if toolchains.exists():
        facts['toolchains'] = json.loads(toolchains.read_text())
    try:
        meminfo = Path('/proc/meminfo').read_text()
        facts['mem_total_bytes'] = int(meminfo.split('MemTotal:')[1].split()[0]) * 1024
    except (OSError, IndexError, ValueError):
        facts['mem_total_bytes'] = None
    return facts


def wait_ready(env, node, run):
    deadline = time.monotonic() + 120
    while True:
        if node.poll() is not None:
            raise RuntimeError('LOCALNET_START_FAILED: inspect ' + str(run / 'node.log'))
        try:
            req = urllib.request.Request(env['KIX_LOCAL_RPC'], data=json.dumps({
                'jsonrpc': '2.0', 'id': 1, 'method': 'sui_getChainIdentifier', 'params': [],
            }).encode(), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=2) as response:
                chain = json.load(response).get('result')
            with socket.create_connection(('127.0.0.1', 9123), timeout=2):
                pass
            if chain:
                return chain
        except (OSError, ValueError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError('LOCALNET_READY_TIMEOUT: inspect ' + str(run / 'node.log'))
        time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('out', help='validation output directory (fresh; must not exist '
                                    'or be empty)')
    parser.add_argument('--shield-count', type=int, default=None,
                        help='override zk.shield_count (default: generator default, 1024)')
    parser.add_argument('--driver-timeout', type=int, default=7200)
    args = parser.parse_args()

    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit('Output directory is not empty: ' + str(out))
    out.mkdir(parents=True, exist_ok=True)

    # The pinned sui CLI lives in .local/bin. Record that binary, not "not found".
    os.environ['PATH'] = str(ROOT / '.local/bin') + os.pathsep + os.environ.get('PATH', '')

    # Host facts first: a failed run still records where it ran.
    facts = host_facts()
    facts['resource_budget'] = {
        'driver_timeout_s': args.driver_timeout, 'committee_size': 1,
        'epoch_duration_ms': EPOCH_DURATION_MS,
        'request': 'builder machine only; no external endpoints, no spend',
    }
    (out / 'host.json').write_text(json.dumps(facts, indent=1) + '\n')

    if not (PROTO / 'zk/artifacts/manifest.json').exists():
        raise SystemExit('Run npm --prefix reference/rights_scale/client run setup:zk first.')
    for port in (9000, 9123):
        with socket.socket() as test:
            # A preceding localnet can leave TIME_WAIT connections after its
            # process has exited. Reuse permits those, not an active listener.
            test.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                test.bind(('127.0.0.1', port))
            except OSError:
                raise SystemExit(f'Port {port} is in use. This runner will not stop another process.')

    (ROOT / '.local/verification' / OUTPUT_NAME).unlink(missing_ok=True)
    parent = ROOT / '.local/localnet'
    parent.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='rights-scale-l1-load-', dir=parent))
    tmp = run / 'tmp'
    tmp.mkdir()
    env = dict(os.environ)
    env['PATH'] = os.environ['PATH']
    env['TMPDIR'] = str(tmp)
    env['RUST_LOG'] = 'off,sui_node=warn'
    env['KIX_SUI_CONFIG'] = str(ROOT / '.local/sui-config/client.yaml')
    env['KIX_LOCAL_RPC'] = 'http://127.0.0.1:9000'
    env['KIX_JOURNEY_DIR'] = str(run / 'journey')
    env['KIX_LOAD_SCENARIOS'] = str(run / 'journey' / 'load-scenarios.json')
    subprocess.run([sys.executable, str(ROOT / 'scripts/configure_local.py')], check=True)
    print('Local run: ' + str(run), flush=True)
    network = run / 'network'
    network.mkdir()
    journey = run / 'journey'
    journey.mkdir()

    # Deterministic workload expansion — the single source of what runs.
    expand_cmd = [sys.executable, str(PROTO / 'load_plan.py'),
                  '--expand', env['KIX_LOAD_SCENARIOS']]
    if args.shield_count is not None:
        expand_cmd += ['--shield-count', str(args.shield_count)]
    with (run / 'expand.log').open('w') as expand_log:
        result = subprocess.run(expand_cmd, cwd=PROTO, env=env,
                                stdout=expand_log, stderr=subprocess.STDOUT)
    if result.returncode:
        print((run / 'expand.log').read_text()[-4000:])
        raise RuntimeError('SCENARIO_EXPAND_FAILED: ' + str(run))
    shutil.copy(env['KIX_LOAD_SCENARIOS'], out / 'load-scenarios.json')
    print((run / 'expand.log').read_text().strip(), flush=True)

    with (run / 'genesis.log').open('w') as genesis_log:
        subprocess.run(['sui', 'genesis', '--working-dir', str(network), '--committee-size', '1',
            '--with-faucet', '--epoch-duration-ms', str(EPOCH_DURATION_MS)], env=env, cwd=run,
            stdout=genesis_log, stderr=subprocess.STDOUT, check=True, timeout=120)
    # Sui's local validators otherwise poll every configured OAuth provider,
    # including Slack. An empty provider map prevents creating those background
    # network tasks. See upstream sui-node/src/lib.rs::start_jwk_updater.
    network_file = network / 'network.yaml'
    configuration = yaml.safe_load(network_file.read_text())
    validators = configuration.get('validator_configs')
    if not isinstance(validators, list) or len(validators) != 1:
        raise RuntimeError('UNRECOGNIZED_LOCAL_VALIDATOR_CONFIGURATION')
    for validator in validators:
        validator['zklogin-oauth-providers'] = {}
    network_file.write_text(yaml.safe_dump(configuration, sort_keys=False))
    if any(v.get('zklogin-oauth-providers') != {}
           for v in yaml.safe_load(network_file.read_text())['validator_configs']):
        raise RuntimeError('JWK_BACKGROUND_FETCH_NOT_DISABLED')

    status = 'FAILED_MEASUREMENT'

    def preserve_and_summarize():
        """Copy a partial report and reduce it. A failed run still leaves raw samples."""
        report_path = journey / 'load-report.json'
        if report_path.exists() and not (out / 'load-report.json').exists():
            shutil.copy(report_path, out / 'load-report.json')
        if not report_path.exists() or (out / 'receipt.json').exists():
            return None
        with (run / 'summarize.log').open('w') as summarize_log:
            result = subprocess.run([sys.executable, str(PROTO / 'summarize_load.py'),
                '--report', str(report_path),
                '--scenarios', env['KIX_LOAD_SCENARIOS'],
                '--out', str(out)],
                cwd=PROTO, env=env, stdout=summarize_log, stderr=subprocess.STDOUT)
        text = (run / 'summarize.log').read_text()
        print(text[-4000:], flush=True)
        return result.returncode

    try:
        with (run / 'node.log').open('w') as log:
            node = subprocess.Popen(['sui', 'start', '--network.config', str(network),
                '--with-faucet=127.0.0.1:9123'],
                cwd=run, env=env, stdout=log, stderr=subprocess.STDOUT)
            try:
                chain = wait_ready(env, node, run)
                print('Local chain ready: ' + chain, flush=True)
                with (run / 'journey.log').open('w', buffering=1) as journey_log:
                    result = subprocess.run(['node', 'load-l1.mjs'], cwd=PROTO / 'client',
                        env=env, stdout=journey_log, stderr=subprocess.STDOUT,
                        timeout=args.driver_timeout)
                if result.returncode:
                    print((run / 'journey.log').read_text()[-14000:])
                code = preserve_and_summarize()
                if result.returncode:
                    raise RuntimeError('LOCALNET_LOAD_DRIVER_FAILED: ' + str(run))
                if code:
                    raise RuntimeError('LOAD_SUMMARIZE_FAILED: ' + str(run))
            finally:
                node.terminate()
                try:
                    node.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    node.kill()
                    node.wait()
    except Exception:
        # Preserve whatever the driver managed to write before the failure.
        if not (out / 'receipt.json').exists():
            preserve_and_summarize()
        raise

    receipt = json.loads((out / 'receipt.json').read_text())
    status = receipt.get('status')
    receipt['localCommitteeSize'] = 1
    receipt['networkFaultToleranceTested'] = False
    receipt['zkLoginBackgroundKeyFetchDisabled'] = True
    receipt['runDir'] = str(run.relative_to(ROOT))
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=1) + '\n')

    # Manifest: provenance for the record directory.
    files = sorted(str(p.relative_to(out)) for p in out.rglob('*') if p.is_file())
    report = json.loads((out / 'load-report.json').read_text())
    manifest = {
        'record': 'kix-rs4-l1-load', 'version': 'kix-rs4-l1-load-v1',
        'packageId': report.get('packageId'), 'chain': report.get('chain'),
        'scenarioFingerprint': report.get('scenarioFingerprint'),
        'settings': report.get('settings'), 'requested': report.get('requested'),
        'artifacts': report.get('manifest'),
        'files': {f: hashlib.sha256((out / f).read_bytes()).hexdigest() for f in files},
        'status': status,
        'explorationData': True,
        'nonClaims': ['no SLO', 'not product TPS', 'no production readiness',
                      'no durability or fault-tolerance claims',
                      'fixture values are test values, not protocol values'],
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')

    public_receipts = ROOT / '.local/verification'
    public_receipts.mkdir(parents=True, exist_ok=True)
    (public_receipts / OUTPUT_NAME).write_text(json.dumps(receipt, indent=2) + '\n')
    print('receipt: ' + str(public_receipts / OUTPUT_NAME), flush=True)
    print('record: ' + str(out), flush=True)
    if status != 'PASSED_MEASUREMENT':
        raise SystemExit('LOAD_MEASUREMENT_DID_NOT_PASS: ' + str(status))


if __name__ == '__main__':
    main()
