"""Run the unchanged protocol workflow's stdlib document block in the foreground."""
from pathlib import Path
import shlex
import subprocess
import sys

folder = Path(__file__).resolve().parent
workflow = Path('.github/workflows/protocol.yml').read_text()
block = workflow.split('      - name: Stdlib offline document checks\n', 1)[1]
block = block.split('        run: |\n', 1)[1].split('      - uses:', 1)[0]
commands = [line.strip() for line in block.splitlines() if line.strip().startswith('python3 ')]
assert commands, 'workflow document checks missing'
failures = []
for index, command in enumerate(commands):
    args = shlex.split(command)
    args[:1] = ['python3.12', '-B']
    label = 'document-%02d-%s' % (index + 1, Path(args[2]).stem)
    if '--self-test' in args:
        label += '-self-test'
    result = subprocess.run([sys.executable, '-B', str(folder / 'run_check.py'), label, *args])
    if result.returncode:
        failures.append(command)
print('Document commands:', len(commands), 'failures:', failures, flush=True)
sys.exit(bool(failures))
