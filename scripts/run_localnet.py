"""Run one isolated, disposable Sui localnet and the public/private journey.

Only terminates the subprocess created here. No existing network is reset.
All keys, signed submissions and node state remain in ignored .local folders.
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'reference/v0.3-rc1'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--private', action='store_true', help='Requires client/setup-zk.mjs artifacts')
    parser.add_argument('--scale', action='store_true', help='Public rights-scale functional localnet acceptance')
    parser.add_argument('--paid', action='store_true', help='Actual public Sui resale with independent mock PG/bank')
    args = parser.parse_args()
    if sum((args.private, args.paid, args.scale)) > 1:
        raise SystemExit('Choose one of private, paid or scale.')
    output_name = 'scale-localnet.json' if args.scale else 'paid-journey.json' if args.paid else 'private-journey.json' if args.private else 'public-journey.json'
    # A failed new attempt must not leave an older success as its apparent result.
    (ROOT / '.local/verification' / output_name).unlink(missing_ok=True)
    if args.private and not (PROTO / 'zk/artifacts/manifest.json').exists():
        raise SystemExit('Run npm --prefix reference/v0.3-rc1/client run setup:zk first.')
    for port in (9000, 9123):
        with socket.socket() as test:
            # A preceding localnet can leave TIME_WAIT connections after its
            # process has exited. Reuse permits those, not an active listener.
            test.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                test.bind(('127.0.0.1', port))
            except OSError:
                raise SystemExit(f'Port {port} is in use. This runner will not stop another process.')
    parent = ROOT / '.local/localnet'
    parent.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='private-' if args.private else 'public-', dir=parent))
    tmp = run / 'tmp'
    tmp.mkdir()
    env = dict(os.environ)
    env['PATH'] = str(ROOT / '.local/bin') + os.pathsep + env['PATH']
    env['TMPDIR'] = str(tmp)
    env['RUST_LOG'] = 'off,sui_node=warn'
    env['KIX_SUI_CONFIG'] = str(ROOT / '.local/sui-config/client.yaml')
    env['KIX_LOCAL_RPC'] = 'http://127.0.0.1:9000'
    env['KIX_JOURNEY_DIR'] = str(run / 'journey')
    env['KIX_PRIVATE'] = '1' if args.private else '0'
    env['KIX_PAID'] = '1' if args.paid else '0'
    env['KIX_PYTHON'] = env.get('KIX_PYTHON', '/usr/bin/python3' if args.paid else sys.executable)
    if args.scale:
        env['KIX_SCALE_OUTPUT'] = str(run / 'scale-result.json')
    if args.paid:
        # Ubuntu 24.04 system Python is the bounded integration runtime. Fail
        # before creating a chain if a different environment is selected.
        subprocess.run([env['KIX_PYTHON'], '-c',
            'import sys,sqlite3; assert sys.version_info[:2]==(3,12) and sqlite3.sqlite_version=="3.45.1", '
            '"Paid fixture requires Python 3.12 / SQLite 3.45.1"; '
            'print("Paid fixture runtime:",sys.version.split()[0],sqlite3.sqlite_version)'], check=True, env=env)
    subprocess.run([sys.executable, str(ROOT / 'scripts/configure_local.py')], check=True)
    print('Local run: ' + str(run), flush=True)
    network = run / 'network'
    network.mkdir()
    with (run / 'genesis.log').open('w') as genesis_log:
        subprocess.run(['sui', 'genesis', '--working-dir', str(network), '--committee-size', '1',
            '--with-faucet', '--epoch-duration-ms', '3600000'], env=env, cwd=run,
            stdout=genesis_log, stderr=subprocess.STDOUT, check=True, timeout=120)
    # Sui's local validators otherwise poll every configured OAuth provider,
    # including Slack. This Ed25519 + Groth16 test does not use zkLogin. An
    # empty provider map prevents creating those background network tasks.
    # See upstream sui-node/src/lib.rs::start_jwk_updater at our pinned commit.
    network_file = network / 'network.yaml'
    configuration = yaml.safe_load(network_file.read_text())
    validators = configuration.get('validator_configs')
    if not isinstance(validators, list) or len(validators) != 1:
        raise RuntimeError('UNRECOGNIZED_LOCAL_VALIDATOR_CONFIGURATION')
    for validator in validators:
        validator['zklogin-oauth-providers'] = {}
    network_file.write_text(yaml.safe_dump(configuration, sort_keys=False))
    if any(v.get('zklogin-oauth-providers') != {} for v in yaml.safe_load(network_file.read_text())['validator_configs']):
        raise RuntimeError('JWK_BACKGROUND_FETCH_NOT_DISABLED')
    with (run / 'node.log').open('w') as log:
        node = subprocess.Popen(['sui', 'start', '--network.config', str(network),
            '--with-faucet=127.0.0.1:9123'],
            cwd=run, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
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
                        break
                except (OSError, ValueError):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError('LOCALNET_READY_TIMEOUT: inspect ' + str(run / 'node.log'))
                time.sleep(0.5)
            print('Local chain ready: ' + chain, flush=True)
            with (run / 'journey.log').open('w') as journey_log:
                journey = ROOT / 'reference/rights-scale-v1/localnet.mjs' if args.scale else PROTO / 'client/localnet.mjs'
                result = subprocess.run(['node', str(journey)], cwd=PROTO / 'client', env=env,
                    stdout=journey_log, stderr=subprocess.STDOUT, timeout=600)
            if result.returncode:
                print((run / 'journey.log').read_text()[-14000:])
                raise RuntimeError('LOCALNET_JOURNEY_FAILED: ' + str(run))
            receipt_path = run / 'scale-result.json' if args.scale else run / 'journey/journey-result.json'
            receipt = json.loads(receipt_path.read_text())
            if args.scale:
                if receipt.get('mode') != 'LOCALNET_FUNCTIONAL' or [c.get('capacity') for c in receipt.get('cases', [])] != [1024, 16384, 65536]:
                    raise RuntimeError('MISSING_SCALE_CHAIN_SUCCESS_RECEIPT')
            elif receipt.get('status') != 'PASSED_ACTUAL_LOCALNET':
                raise RuntimeError('MISSING_ACTUAL_CHAIN_SUCCESS_RECEIPT')
            receipt['localCommitteeSize'] = 1
            receipt['networkFaultToleranceTested'] = False
            receipt['zkLoginBackgroundKeyFetchDisabled'] = True
            public_receipts = ROOT / '.local/verification'
            public_receipts.mkdir(parents=True, exist_ok=True)
            if args.paid and receipt.get('paidIntegration', {}).get('status') != 'PASSED_ACTUAL_SUI_MOCK_MONEY':
                raise RuntimeError('MISSING_PAID_INTEGRATION_RECEIPT')
            (public_receipts / output_name).write_text(
                json.dumps(receipt, indent=2) + '\n')
            print(json.dumps(receipt, indent=2), flush=True)
        finally:
            node.terminate()
            try:
                node.wait(timeout=20)
            except subprocess.TimeoutExpired:
                node.kill()
                node.wait()


if __name__ == '__main__':
    main()

