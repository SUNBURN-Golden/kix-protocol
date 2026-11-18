import json, os, pathlib, shlex, subprocess, sys, time
folder = pathlib.Path('validation/2026-11-13-plan-commerce-receipt-goldens')
name, *command = sys.argv[1:]
start = time.monotonic()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CARGO_NET_OFFLINE='true')
with (folder / (name + '.log')).open('w') as output:
    output.write('$ ' + shlex.join(command) + '\n')
    output.flush()
    result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, env=env)
    output.write('\nEXIT: %d\n' % result.returncode)
record = {'log': name + '.log', 'command': shlex.join(command), 'exit': result.returncode, 'elapsed_seconds': round(time.monotonic()-start, 2)}
with (folder / 'commands.jsonl').open('a') as output:
    output.write(json.dumps(record) + '\n')
print(json.dumps(record), flush=True)
print('\n'.join((folder / (name + '.log')).read_text().splitlines()[-12:]), flush=True)
sys.exit(result.returncode)
