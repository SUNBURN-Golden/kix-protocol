"""Run one isolated, disposable Sui localnet and the RS-1 rights-scale journey.

Retargeted copy of scripts/run_localnet.py for reference/rights_scale (the
extended-profile public path, 1,024 slots). The 16-slot harness is left
byte-identical; the duplication is deliberate.

Only terminates the subprocess created here. No existing network is reset.
All keys, signed submissions and node state remain in ignored .local folders.
"""
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
PROTO = ROOT / 'reference/rights_scale'
OUTPUT_NAME = 'rights-scale-journey.json'


def main():
    # A failed new attempt must not leave an older success as its apparent result.
    (ROOT / '.local/verification' / OUTPUT_NAME).unlink(missing_ok=True)
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
    run = Path(tempfile.mkdtemp(prefix='rights-scale-', dir=parent))
    tmp = run / 'tmp'
    tmp.mkdir()
    env = dict(os.environ)
    env['PATH'] = str(ROOT / '.local/bin') + os.pathsep + env['PATH']
    env['TMPDIR'] = str(tmp)
    env['RUST_LOG'] = 'off,sui_node=warn'
    env['KIX_SUI_CONFIG'] = str(ROOT / '.local/sui-config/client.yaml')
    env['KIX_LOCAL_RPC'] = 'http://127.0.0.1:9000'
    env['KIX_JOURNEY_DIR'] = str(run / 'journey')
    env['KIX_SCENARIOS'] = str(run / 'journey' / 'scenarios.json')
    subprocess.run([sys.executable, str(ROOT / 'scripts/configure_local.py')], check=True)
    print('Local run: ' + str(run), flush=True)
    network = run / 'network'
    network.mkdir()
    journey = run / 'journey'
    journey.mkdir()
    with (run / 'genesis.log').open('w') as genesis_log:
        subprocess.run(['sui', 'genesis', '--working-dir', str(network), '--committee-size', '1',
            '--with-faucet', '--epoch-duration-ms', '3600000'], env=env, cwd=run,
            stdout=genesis_log, stderr=subprocess.STDOUT, check=True, timeout=120)
    # Sui's local validators otherwise poll every configured OAuth provider,
    # including Slack. This public-path journey does not use zkLogin. An
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
            # Expand the vectors once; driver and comparator consume the same list.
            with (run / 'expand.log').open('w') as expand_log:
                result = subprocess.run([sys.executable, str(PROTO / 'compare_localnet.py'),
                    '--expand', env['KIX_SCENARIOS']], cwd=PROTO, env=env,
                    stdout=expand_log, stderr=subprocess.STDOUT)
            if result.returncode:
                print((run / 'expand.log').read_text()[-4000:])
                raise RuntimeError('SCENARIO_EXPAND_FAILED: ' + str(run))
            with (run / 'journey.log').open('w') as journey_log:
                result = subprocess.run(['node', 'localnet.mjs'], cwd=PROTO / 'client', env=env,
                    stdout=journey_log, stderr=subprocess.STDOUT, timeout=900)
            if result.returncode:
                print((run / 'journey.log').read_text()[-14000:])
                raise RuntimeError('LOCALNET_JOURNEY_FAILED: ' + str(run))
            with (run / 'compare.log').open('w') as compare_log:
                result = subprocess.run([sys.executable, str(PROTO / 'compare_localnet.py'),
                    '--report', str(journey / 'chain-report.json'),
                    '--scenarios', env['KIX_SCENARIOS'],
                    '--out', str(journey / 'journey-result.json')],
                    cwd=PROTO, env=env, stdout=compare_log, stderr=subprocess.STDOUT)
            if result.returncode:
                print((run / 'compare.log').read_text()[-14000:])
                raise RuntimeError('MODEL_COMPARISON_FAILED: ' + str(run))
            receipt = json.loads((journey / 'journey-result.json').read_text())
            if receipt.get('status') != 'PASSED_ACTUAL_LOCALNET':
                raise RuntimeError('MISSING_ACTUAL_CHAIN_SUCCESS_RECEIPT')
            receipt['localCommitteeSize'] = 1
            receipt['networkFaultToleranceTested'] = False
            receipt['zkLoginBackgroundKeyFetchDisabled'] = True
            public_receipts = ROOT / '.local/verification'
            public_receipts.mkdir(parents=True, exist_ok=True)
            (public_receipts / OUTPUT_NAME).write_text(json.dumps(receipt, indent=2) + '\n')
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
