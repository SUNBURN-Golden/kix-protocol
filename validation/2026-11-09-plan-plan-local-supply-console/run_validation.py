import json, os, pathlib, subprocess, sys
root = pathlib.Path('validation/2026-11-09-plan-plan-local-supply-console')
ledger_path = root/'commands.json'
ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
command = sys.argv[1:]
index = len(ledger)+1
process = subprocess.run(command, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':'reference/token_reward'}, timeout=900)
name = f'{index:02d}'
(root/f'{name}.stdout.txt').write_bytes(process.stdout)
(root/f'{name}.stderr.txt').write_bytes(process.stderr)
ledger.append({'command': command,'environment':{'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':'reference/token_reward'},'exit_status':process.returncode,'stdout':f'{name}.stdout.txt','stderr':f'{name}.stderr.txt'})
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
print('Command:', ' '.join(command), '\nExit:', process.returncode)
print((process.stdout+process.stderr).decode('utf-8',errors='backslashreplace')[-9000:])
