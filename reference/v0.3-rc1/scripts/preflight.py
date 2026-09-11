"""Read-only dependency check; never installs tools or changes network policy."""
import json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
tools={n:shutil.which(n) for n in ['python3','node','sui','cargo','rustc']}
node=root/'client/node_modules'
packages={n:(node/n).exists() for n in ['@mysten/sui','snarkjs','circom2','circomlib','circomlibjs']}
versions={}
for n in ['python3','node','sui']:
 if tools[n]:
  r=subprocess.run([tools[n],'--version'],capture_output=True,text=True,timeout=10)
  versions[n]=(r.stdout+r.stderr).strip()
ready=bool(tools['sui']) and all(packages.values())
report={'status':'READY_FOR_BUILD' if ready else 'BLOCKED_MISSING_RUNTIME','tools':tools,'packages':packages,'versions':versions,
        'moveCompiled':False,'chainExecuted':False,'proofGenerated':False,
        'note':'This probe only checks prerequisites; READY is not a passing chain test.'}
print(json.dumps(report,indent=2))
sys.exit(0 if ready else 3)
