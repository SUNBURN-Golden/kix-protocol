"""Create a checkout-local Sui config with an empty keystore; never print keys."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config_dir = root / '.local' / 'sui-config'
config_dir.mkdir(parents=True, exist_ok=True)
keystore = config_dir / 'sui.keystore'
if not keystore.exists():
    keystore.write_text('[]\n')
    keystore.chmod(0o600)
config = config_dir / 'client.yaml'
if not config.exists():
    config.write_text(json.dumps({
        'keystore': {'File': str(keystore)},
        'envs': [{'alias': 'localnet', 'rpc': 'http://127.0.0.1:9000', 'ws': None, 'basic_auth': None}],
        'active_env': 'localnet', 'active_address': None,
    }, indent=2) + '\n')
    config.chmod(0o600)
print('Checkout-local Sui configuration ready; no wallet was generated.')
