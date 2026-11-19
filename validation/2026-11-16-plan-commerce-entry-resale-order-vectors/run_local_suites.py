"""Execute the unchanged workflow reference loop, then applicable local checks.

Every child runs in the foreground through the local command recorder. No
installation, historical evidence overwrite, hosted CI or external call.
"""
from pathlib import Path
import re
import subprocess
import sys

folder = Path(__file__).resolve().parent
workflow = Path('.github/workflows/protocol.yml').read_text()
loop = re.search(r'for suite in ([a-z0-9_ ]+); do', workflow).group(1).split()
assert 'booking_resale_admission' in loop and 'settlement_f01_f03' in loop
commands = [(suite, ['python3.12', '-B', '-m', 'unittest', 'discover',
                     '-s', 'reference/' + suite, '-t', 'reference/' + suite]) for suite in loop]
for script in ('check_openapi_contract', 'check_integration_gate_openapi', 'check_sdk_client'):
    for suffix in ([], ['--self-test']):
        commands.append((script + ('-self-test' if suffix else ''),
                         ['python3.12', '-B', 'scripts/' + script + '.py', *suffix]))
commands += [
    ('offline-limits', ['python3.12', '-B', '-m', 'unittest', 'integration_gate.test_offline_limits']),
    ('architecture', ['python3.12', '-B', 'scripts/verify_runtime_architecture.py']),
    ('architecture-negative', ['python3.12', '-B', 'scripts/test_runtime_architecture.py']),
    ('kernel-tests', ['cargo', 'test', '--manifest-path', 'runtime/Cargo.toml', '-p', 'kix-kernel', '--locked', '--offline']),
    ('kernel-clippy', ['cargo', 'clippy', '--manifest-path', 'runtime/Cargo.toml', '-p', 'kix-kernel', '--all-targets', '--locked', '--offline', '--', '-D', 'warnings']),
    ('runtime-fmt', ['cargo', 'fmt', '--manifest-path', 'runtime/Cargo.toml', '--all', '--', '--check']),
]
failures = []
for name, args in commands:
    result = subprocess.run([sys.executable, '-B', str(folder / 'run_check.py'), name, *args])
    if result.returncode:
        failures.append(name)
print('Local commands:', len(commands), 'failures:', failures, flush=True)
sys.exit(bool(failures))
