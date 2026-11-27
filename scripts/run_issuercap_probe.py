"""Run one isolated, disposable Sui localnet and the RS-1 IssuerCap probe.

Retargeted copy of scripts/run_localnet_rights_scale.py for the
rs-1-issuercap-probe node: same one-validator localnet, same driver
(reference/rights_scale/client/localnet.mjs), but the scenario list is reduced
to the smallest matrix case and model comparison is skipped — the deliverable
is the driver's `probes` block, extracted verbatim into a receipt. The probe
outcome is recorded, not asserted: whichever serialization behavior the chain
shows is what gets reported.

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
OUTPUT_NAME = 'issuercap-probe.json'
# Smallest expanded scenario: 15 seated slots, 4-slot pages, 2 shards. The
# probe block runs after the scenario loop regardless; this keeps the run
# short while exercising the same publish/claim/seal path.
PROBE_SCENARIO = 'matrix_15_0_p4_s2'


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
    run = Path(tempfile.mkdtemp(prefix='issuercap-probe-', dir=parent))
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
    # including Slack. This probe does not use zkLogin. An empty provider map
    # prevents creating those background network tasks.
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
            # Expand the shared vectors once, then keep only the smallest matrix
            # case. The driver still runs its full probe block afterwards.
            expanded = run / 'expanded.json'
            with (run / 'expand.log').open('w') as expand_log:
                result = subprocess.run([sys.executable, str(PROTO / 'compare_localnet.py'),
                    '--expand', str(expanded)], cwd=PROTO, env=env,
                    stdout=expand_log, stderr=subprocess.STDOUT)
            if result.returncode:
                print((run / 'expand.log').read_text()[-4000:])
                raise RuntimeError('SCENARIO_EXPAND_FAILED: ' + str(run))
            scenarios = [s for s in json.loads(expanded.read_text())['scenarios']
                         if s['name'] == PROBE_SCENARIO]
            if len(scenarios) != 1:
                raise RuntimeError('PROBE_SCENARIO_NOT_FOUND: ' + PROBE_SCENARIO)
            Path(env['KIX_SCENARIOS']).write_text(json.dumps({'scenarios': scenarios}, indent=2) + '\n')
            with (run / 'journey.log').open('w') as journey_log:
                result = subprocess.run(['node', 'localnet.mjs'], cwd=PROTO / 'client', env=env,
                    stdout=journey_log, stderr=subprocess.STDOUT, timeout=900)
            if result.returncode:
                print((run / 'journey.log').read_text()[-14000:])
                raise RuntimeError('LOCALNET_JOURNEY_FAILED: ' + str(run))
            report = json.loads((journey / 'chain-report.json').read_text())
            probes = report.get('probes')
            issuer_cap = (probes or {}).get('issuerCap')
            if not isinstance(issuer_cap, dict) or 'a' not in issuer_cap or 'b' not in issuer_cap:
                raise RuntimeError('ISSUERCAP_PROBE_BLOCK_MISSING: ' + str(journey / 'chain-report.json'))
            receipt = {
                'chain': report.get('chain'),
                'packageId': report.get('packageId'),
                'actors': report.get('actors'),
                'scenariosRun': [s['name'] for s in report.get('scenarios', [])],
                'probes': probes,
                'measurements': report.get('measurements'),
                'status': 'PASSED_ACTUAL_LOCALNET',
                'authority': 'SUI_MOVE',
                'kixServicesCalled': 0,
                'ownGas': True,
                'zk': False,
                'localCommitteeSize': 1,
                'networkFaultToleranceTested': False,
                'zkLoginBackgroundKeyFetchDisabled': True,
                'limitation': ('Localnet probe only. One validator, exploratory; the recorded '
                               'concurrency outcome is observed behavior, not a performance or '
                               'production claim. RPC is trusted; no private path, no delegation.'),
            }
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
