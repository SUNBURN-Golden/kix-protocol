"""Run explicit local checks sequentially; no retry, golden update or publication.

Use PYTHONPATH=. command prefixes for full reference-suite discovery.
Do not invoke this ledger writer concurrently.
"""
import json,os,subprocess,sys,time
from pathlib import Path
v=Path('validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec')
env=os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='.:reference/booking_resale_admission',CARGO_NET_OFFLINE='true')
for command in sys.argv[1:]:
    entries=json.loads((v/'commands.json').read_text()) if (v/'commands.json').exists() else []
    log=v/f'{len(entries)+1:02d}.log'
    start=time.monotonic()
    with log.open('w') as out:
        result=subprocess.run(command,shell=True,env=env,stdout=out,stderr=subprocess.STDOUT)
    entry=dict(command=command,exit_code=result.returncode,seconds=round(time.monotonic()-start,2),log=str(log))
    entries.append(entry); (v/'commands.json').write_text(json.dumps(entries,indent=2)+'\n')
    print(json.dumps(entry),flush=True)
    if result.returncode: print(log.read_text()[-4500:],flush=True)
