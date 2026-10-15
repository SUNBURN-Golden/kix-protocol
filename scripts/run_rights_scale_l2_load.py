"""RS-4 L2: run one isolated, disposable Sui localnet under the 16,384-slot
load workload.

Same disposable-localnet discipline as scripts/run_rights_scale_l1_load.py —
whose helpers this runner imports unchanged: a fresh one-validator genesis per
run, only the subprocess started here is terminated, no existing network is
reset, all keys stay in ignored .local folders. The workload is expanded
deterministically from reference/rights_scale/load_plan.py --stage l2, executed
by client/load-l1.mjs against the published package (real chain transactions,
real Groth16 proofs — setup:zk artifacts required), then reduced by
reference/rights_scale/summarize_load.py.

The private path is contract-capped at 2^ZK_DEPTH = 1,024 seats
(`claim_zk` asserts seated+ga <= 2^ZK_DEPTH): the L2 private leg runs the
1,024-slot workload plus a probe.zk_capacity prefix that proves the cap on
auxiliary shows. Public and delegated run full 16,384-seat shows.

Usage:
    python3 scripts/run_rights_scale_l2_load.py <output-dir> [--shield-count N]

Writes <output-dir>/{host.json,manifest.json,load-scenarios.json,
load-report.json,receipt.json,public/,private/,delegated/} and the receipt
.local/verification/rights-scale-l2-load.json. Everything produced is
exploration data from a one-validator localnet: no SLO, no throughput or
production claims.
"""
import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from run_rights_scale_l1_load import (  # noqa: E402
    ROOT, PROTO, git, host_facts, wait_ready)

OUTPUT_NAME = 'rights-scale-l2-load.json'
EPOCH_DURATION_MS = 43_200_000  # 12h: the multi-hour L2 run must stay far from rotation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('out', help='validation output directory (fresh; must not exist '
                                    'or be empty)')
    parser.add_argument('--shield-count', type=int, default=None,
                        help='override zk.shield_count (default: generator default, 1024)')
    parser.add_argument('--driver-timeout', type=int, default=18000)
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
    run = Path(tempfile.mkdtemp(prefix='rights-scale-l2-load-', dir=parent))
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
                  '--stage', 'l2', '--expand', env['KIX_LOAD_SCENARIOS']]
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
        'record': 'kix-rs4-l2-load', 'version': 'kix-rs4-l2-load-v1',
        'packageId': report.get('packageId'), 'chain': report.get('chain'),
        'scenarioFingerprint': report.get('scenarioFingerprint'),
        'settings': report.get('settings'), 'requested': report.get('requested'),
        'artifacts': report.get('manifest'),
        'files': {f: hashlib.sha256((out / f).read_bytes()).hexdigest() for f in files},
        'status': status,
        'explorationData': True,
        'nonClaims': ['no SLO', 'not product TPS', 'no production readiness',
                      'no durability or fault-tolerance claims',
                      'fixture values are test values, not protocol values',
                      'private path not measured at 16,384 seats: contract-capped '
                      'at 2^ZK_DEPTH = 1,024 by claim_zk; boundary probed, '
                      'deeper circuit/fixture out of scope'],
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
